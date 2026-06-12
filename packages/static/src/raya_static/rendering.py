from __future__ import annotations

import html
import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.footnote import footnote_plugin
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from raya_schema import ValidationReport

from raya_static.math_renderer import MathItem, MathRenderer


INDEX_MARKER = "<!-- raya:index -->"
RENDER_STYLESHEET_PATH = "_raya/render/rich.css"
_INDEX_PLACEHOLDER = "RAYA_INDEX_PLACEHOLDER"

_CALLOUT_MARKER_RE = re.compile(
    r"^\s{0,3}>\s*\[!(NOTE|TIP|WARNING|CAUTION)\]\s*$",
    re.IGNORECASE,
)
_BLOCKQUOTE_LINE_RE = re.compile(r"^\s{0,3}>\s?(.*)$")
_FOOTNOTE_REF_RE = re.compile(r"(?<!\\)\[\^([^\]\s]+)\]")
_FOOTNOTE_DEF_RE = re.compile(r"^\[\^([^\]\s]+)\]:", re.MULTILINE)
_FENCE_RE = re.compile(r"^\s{0,3}(```+|~~~+)")
_SLUG_UNSAFE_RE = re.compile(r"[^a-z0-9 -]")
_SLUG_SPACE_RE = re.compile(r"\s+")
_LANGUAGE_RE = re.compile(r"^[A-Za-z0-9_+.#-]+")


@dataclass(frozen=True)
class _Heading:
    level: int
    title: str
    anchor: str


@dataclass(frozen=True)
class _Callout:
    kind: str
    body: str


class RichMarkdownRenderer:
    def __init__(
        self,
        resolve_href: Callable[[str], str],
        *,
        source_path: Path,
        report: ValidationReport,
        math_renderer: MathRenderer,
    ) -> None:
        self._resolve_href = resolve_href
        self._source_path = source_path
        self._report = report
        self._math_renderer = math_renderer
        self._md = MarkdownIt("commonmark", {"html": False})
        self._md.enable("table")
        self._md.use(footnote_plugin)
        self._md.use(dollarmath_plugin)
        self._default_image_renderer = self._md.renderer.rules.get("image")
        self._md.renderer.rules["heading_open"] = self._render_heading_open
        self._md.renderer.rules["link_open"] = self._render_link_open
        self._md.renderer.rules["image"] = self._render_image
        self._md.renderer.rules["fence"] = self._render_fence
        self._md.renderer.rules["math_inline"] = self._render_math
        self._md.renderer.rules["math_block"] = self._render_math

    def render(self, body: str, generated_index: str = "") -> str:
        prepared_body, callouts = _extract_callouts(body)
        env = _new_env(self._resolve_href, collect_headings=True)
        marker_used = INDEX_MARKER in prepared_body
        if marker_used:
            prepared_body = prepared_body.replace(INDEX_MARKER, _INDEX_PLACEHOLDER)
        page_tokens = self._md.parse(prepared_body, env)
        callout_fragments: dict[str, tuple[_Callout, list[Token], dict]] = {}
        for placeholder, callout in callouts.items():
            callout_env = _new_env(self._resolve_href, collect_headings=False)
            callout_tokens = self._md.parse(callout.body, callout_env)
            callout_fragments[placeholder] = (callout, callout_tokens, callout_env)

        math_items = _collect_math_items(
            page_tokens,
            source_path=self._source_path,
            counter=0,
        )
        counter = len(math_items)
        for _, callout_tokens, _ in callout_fragments.values():
            new_items = _collect_math_items(
                callout_tokens,
                source_path=self._source_path,
                counter=counter,
            )
            math_items.extend(new_items)
            counter += len(new_items)

        math_result = self._math_renderer.render_many(math_items, report=self._report)
        if not self._report.ok:
            return ""
        env["raya_math_html_by_id"] = math_result.html_by_id
        for _, _, callout_env in callout_fragments.values():
            callout_env["raya_math_html_by_id"] = math_result.html_by_id

        html_fragment = self._md.renderer.render(page_tokens, self._md.options, env)

        if marker_used:
            html_fragment = html_fragment.replace(
                f"<p>{_INDEX_PLACEHOLDER}</p>",
                generated_index,
            )
        else:
            if generated_index:
                html_fragment = html_fragment.rstrip() + "\n" + generated_index + "\n"

        rendered_callouts = {
            placeholder: self._render_callout(
                callout,
                self._md.renderer.render(callout_tokens, self._md.options, callout_env),
            )
            for placeholder, (
                callout,
                callout_tokens,
                callout_env,
            ) in callout_fragments.items()
        }
        html_fragment = self._replace_callout_placeholders(
            html_fragment,
            rendered_callouts,
        )
        toc = _render_page_toc(env["raya_headings"])
        if toc:
            return toc + "\n" + html_fragment
        return html_fragment

    def _replace_callout_placeholders(
        self,
        html_fragment: str,
        callouts: dict[str, str],
    ) -> str:
        for placeholder, callout_html in callouts.items():
            html_fragment = html_fragment.replace(f"<p>{placeholder}</p>", callout_html)
        return html_fragment

    def _render_callout(self, callout: _Callout, inner_html: str) -> str:
        label = _callout_label(callout.kind)
        inner = inner_html.strip()
        body = inner if inner else "<p></p>"
        return "\n".join(
            [
                (
                    f'<aside class="raya-callout raya-callout-{html.escape(callout.kind)}" '
                    f'role="note" aria-label="{html.escape(label)}">'
                ),
                f'<p class="raya-callout-title">{html.escape(label)}</p>',
                '<div class="raya-callout-body">',
                body,
                "</div>",
                "</aside>",
            ]
        )

    def _render_heading_open(
        self,
        tokens: list[Token],
        idx: int,
        options: dict,
        env: dict,
    ) -> str:
        token = tokens[idx]
        level = int(token.tag[1:])
        title = _heading_title(tokens, idx)
        anchor = _unique_anchor(title, env["raya_anchor_counts"])
        token.attrSet("id", anchor)
        if env.get("raya_collect_headings") and level > 1:
            env["raya_headings"].append(
                _Heading(level=level, title=title, anchor=anchor)
            )
        return self._md.renderer.renderToken(tokens, idx, options, env)

    def _render_link_open(
        self,
        tokens: list[Token],
        idx: int,
        options: dict,
        env: dict,
    ) -> str:
        href = tokens[idx].attrGet("href")
        if href:
            tokens[idx].attrSet("href", self._resolve_href(href))
        return self._md.renderer.renderToken(tokens, idx, options, env)

    def _render_image(
        self,
        tokens: list[Token],
        idx: int,
        options: dict,
        env: dict,
    ) -> str:
        src = tokens[idx].attrGet("src")
        if src:
            tokens[idx].attrSet("src", self._resolve_href(src))
        if self._default_image_renderer is not None:
            return self._default_image_renderer(tokens, idx, options, env)
        return self._md.renderer.renderToken(tokens, idx, options, env)

    def _render_fence(
        self,
        tokens: list[Token],
        idx: int,
        options: dict,
        env: dict,
    ) -> str:
        token = tokens[idx]
        language = _language_from_info(token.info)
        code_html = _highlight_code(token.content, language)
        data_language = (
            f' data-language="{html.escape(language, quote=True)}"' if language else ""
        )
        code_class = (
            f' class="language-{html.escape(language, quote=True)}"' if language else ""
        )
        label = (
            f'<div class="raya-code-label">{html.escape(language)}</div>'
            if language
            else ""
        )
        return (
            f'<div class="raya-code-block"{data_language}>'
            f"{label}"
            f'<pre class="highlight"><code{code_class}>{code_html}</code></pre>'
            "</div>\n"
        )

    def _render_math(
        self,
        tokens: list[Token],
        idx: int,
        options: dict,
        env: dict,
    ) -> str:
        token = tokens[idx]
        item_id = token.meta.get("raya_math_id")
        if isinstance(item_id, str):
            html_by_id = env.get("raya_math_html_by_id", {})
            rendered = html_by_id.get(item_id)
            if isinstance(rendered, str):
                return rendered
        self._report.add_error(
            "Math rendering failed",
            path=self._source_path,
            field="math",
            next_action=(
                "Check the MathJax renderer contract. "
                "No rendered HTML was available for this math token."
            ),
        )
        return ""


def render_markdown_body(
    body: str,
    *,
    generated_index: str,
    resolve_href: Callable[[str], str],
    source_path: Path,
    report: ValidationReport,
    math_renderer: MathRenderer,
) -> str:
    return RichMarkdownRenderer(
        resolve_href,
        source_path=source_path,
        report=report,
        math_renderer=math_renderer,
    ).render(body, generated_index)


def missing_footnote_definitions(body: str) -> list[str]:
    text = _without_fenced_blocks(body)
    refs = set(_FOOTNOTE_REF_RE.findall(text))
    defs = set(_FOOTNOTE_DEF_RE.findall(text))
    return sorted(ref for ref in refs - defs if ref)


def rich_render_css() -> str:
    base = """
* {
  box-sizing: border-box;
}
body {
  background: #f7f8fa;
  color: #24292f;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.6;
  margin: 0;
  overflow-wrap: anywhere;
}
a {
  color: #0969da;
}
img {
  height: auto;
  max-width: 100%;
}
.raya-skip-link {
  background: #ffffff;
  border: 1px solid #d8dee4;
  left: 1rem;
  padding: 0.5rem 0.75rem;
  position: absolute;
  top: -4rem;
  z-index: 10;
}
.raya-skip-link:focus {
  top: 1rem;
}
.raya-site-header {
  background: #ffffff;
  border-bottom: 1px solid #d8dee4;
}
.raya-site-header-inner,
.raya-main,
.raya-page-footer,
.raya-inspection-main {
  margin: 0 auto;
  max-width: 76rem;
  padding: 1rem;
}
.raya-course-title {
  font-size: 0.875rem;
  font-weight: 700;
  margin: 0 0 0.75rem;
}
.raya-course-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 0.75rem;
}
.raya-course-nav a {
  border-bottom: 2px solid transparent;
  text-decoration: none;
}
.raya-course-nav a[aria-current="page"] {
  border-bottom-color: #1a7f37;
  color: #1a7f37;
  font-weight: 700;
}
nav[aria-label="Breadcrumbs"] {
  color: #57606a;
  font-size: 0.875rem;
  margin-top: 0.75rem;
}
.raya-main {
  align-items: start;
  display: grid;
  gap: 1.5rem;
  grid-template-columns: minmax(0, 1fr) minmax(16rem, 22rem);
}
.raya-article,
.raya-support-stack,
.raya-inspection-main {
  background: #ffffff;
  border: 1px solid #d8dee4;
  min-width: 0;
}
.raya-article,
.raya-inspection-main {
  padding: 1.25rem;
}
.raya-article > :first-child,
.raya-inspection-main > :first-child {
  margin-top: 0;
}
.raya-support-stack {
  display: grid;
  gap: 1rem;
  padding: 1rem;
}
.raya-page-footer {
  color: #57606a;
}
.raya-page-footer nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}
.raya-page-toc {
  border: 1px solid #d8dee4;
  margin: 1rem 0 1.5rem;
  padding: 0.75rem 1rem;
}
.raya-page-toc-title {
  font-weight: 700;
  margin: 0 0 0.5rem;
}
.raya-page-toc ol {
  margin: 0;
  padding-left: 1.25rem;
}
.raya-page-toc-level-3,
.raya-page-toc-level-4,
.raya-page-toc-level-5,
.raya-page-toc-level-6 {
  margin-left: 1rem;
}
.raya-code-block {
  margin: 1rem 0;
}
.raya-code-label {
  background: #24292f;
  color: #ffffff;
  display: inline-block;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 0.8125rem;
  padding: 0.25rem 0.5rem;
}
.raya-code-block pre {
  margin: 0;
  overflow-x: auto;
  padding: 0.85rem 1rem;
}
.raya-callout {
  border-left: 0.25rem solid #6e7781;
  margin: 1rem 0;
  padding: 0.75rem 1rem;
}
.raya-callout-title {
  font-weight: 700;
  margin: 0 0 0.35rem;
}
.raya-callout-body > :first-child {
  margin-top: 0;
}
.raya-callout-body > :last-child {
  margin-bottom: 0;
}
.raya-callout-note {
  border-left-color: #0969da;
}
.raya-callout-tip {
  border-left-color: #1a7f37;
}
.raya-callout-warning,
.raya-callout-caution {
  border-left-color: #bf8700;
}
.math.inline {
  white-space: nowrap;
}
.math.block {
  display: block;
  overflow-x: auto;
  padding: 0.5rem 0;
}
.raya-reference-panel {
  min-width: 0;
  margin: 0;
}
.raya-reference-panel ul {
  list-style: none;
  margin: 0;
  padding: 0;
}
.raya-reference-item {
  margin: 0 0 1rem;
}
.raya-reference-status {
  color: #57606a;
  font-size: 0.875rem;
}
.raya-reference-preview {
  background: #f6f8fa;
  max-width: 100%;
  overflow-x: auto;
  padding: 0.75rem;
  white-space: pre-wrap;
}
.raya-reviewed-output-panel,
.raya-inspection-panel {
  min-width: 0;
  margin: 0;
}
.raya-reviewed-output-panel ul {
  list-style: none;
  margin: 0;
  padding: 0;
}
.raya-reviewed-output-status {
  color: #57606a;
  font-size: 0.875rem;
}
.raya-reviewed-output-excerpt {
  background: #f6f8fa;
  max-width: 100%;
  overflow-x: auto;
  padding: 0.75rem;
  white-space: pre-wrap;
}
@media (max-width: 720px) {
  .raya-site-header-inner,
  .raya-main,
  .raya-page-footer,
  .raya-inspection-main {
    padding: 0.75rem;
  }
  .raya-main {
    display: block;
  }
  .raya-support-stack {
    margin-top: 1rem;
  }
  .raya-course-nav {
    display: grid;
  }
}
""".strip()
    return base + "\n" + HtmlFormatter().get_style_defs(".highlight") + "\n"


def _new_env(
    resolve_href: Callable[[str], str],
    *,
    collect_headings: bool,
) -> dict:
    return {
        "raya_resolve_href": resolve_href,
        "raya_anchor_counts": {},
        "raya_headings": [],
        "raya_collect_headings": collect_headings,
    }


def _walk_tokens(tokens: list[Token]) -> Iterator[Token]:
    for token in tokens:
        yield token
        if token.children:
            yield from _walk_tokens(token.children)


def _collect_math_items(
    tokens: list[Token],
    *,
    source_path: Path,
    counter: int,
) -> list[MathItem]:
    items: list[MathItem] = []
    for token in _walk_tokens(tokens):
        if token.type in {"math_inline", "math_block"}:
            item_id = f"math-{counter}"
            token.meta["raya_math_id"] = item_id
            items.append(
                MathItem(
                    id=item_id,
                    tex=token.content.strip(),
                    display=token.type == "math_block",
                    source_path=source_path,
                )
            )
            counter += 1
    return items


def _extract_callouts(body: str) -> tuple[str, dict[str, _Callout]]:
    lines = body.splitlines()
    output: list[str] = []
    callouts: dict[str, _Callout] = {}
    idx = 0
    while idx < len(lines):
        marker = _CALLOUT_MARKER_RE.match(lines[idx])
        if marker is None:
            output.append(lines[idx])
            idx += 1
            continue

        kind = marker.group(1).lower()
        idx += 1
        callout_lines: list[str] = []
        while idx < len(lines):
            quote_line = _BLOCKQUOTE_LINE_RE.match(lines[idx])
            if quote_line is None:
                break
            callout_lines.append(quote_line.group(1))
            idx += 1

        placeholder = f"RAYA_CALLOUT_{len(callouts)}"
        callouts[placeholder] = _Callout(kind=kind, body="\n".join(callout_lines))
        output.extend(["", placeholder, ""])

    trailing_newline = "\n" if body.endswith("\n") else ""
    return "\n".join(output) + trailing_newline, callouts


def _heading_title(tokens: list[Token], idx: int) -> str:
    if idx + 1 < len(tokens) and tokens[idx + 1].type == "inline":
        return tokens[idx + 1].content.strip()
    return "section"


def _unique_anchor(title: str, counts: dict[str, int]) -> str:
    base = _slugify(title)
    count = counts.get(base, 0)
    counts[base] = count + 1
    if count:
        return f"{base}-{count + 1}"
    return base


def _slugify(text: str) -> str:
    value = text.strip().lower()
    value = _SLUG_UNSAFE_RE.sub("", value)
    value = _SLUG_SPACE_RE.sub("-", value).strip("-")
    return value or "section"


def _render_page_toc(headings: list[_Heading]) -> str:
    if len(headings) < 2:
        return ""
    items = []
    for heading in headings:
        label = html.escape(heading.title)
        anchor = html.escape(f"#{heading.anchor}", quote=True)
        items.append(
            f'<li class="raya-page-toc-level-{heading.level}"><a href="{anchor}">{label}</a></li>'
        )
    return "\n".join(
        [
            '<nav class="raya-page-toc" aria-label="Page contents">',
            '<p class="raya-page-toc-title">On This Page</p>',
            "<ol>",
            "\n".join(items),
            "</ol>",
            "</nav>",
        ]
    )


def _language_from_info(info: str) -> str:
    first = info.strip().split(maxsplit=1)[0] if info.strip() else ""
    first = first.lstrip(".")
    match = _LANGUAGE_RE.match(first)
    return match.group(0).lower() if match else ""


def _highlight_code(code: str, language: str) -> str:
    if not language:
        return html.escape(code)
    try:
        lexer = get_lexer_by_name(language)
    except ClassNotFound:
        return html.escape(code)
    return highlight(code, lexer, HtmlFormatter(nowrap=True))


def _callout_label(kind: str) -> str:
    return {
        "note": "Note",
        "tip": "Tip",
        "warning": "Warning",
        "caution": "Caution",
    }[kind]


def _without_fenced_blocks(body: str) -> str:
    output: list[str] = []
    in_fence = False
    fence_marker = ""
    for line in body.splitlines():
        match = _FENCE_RE.match(line)
        if match is not None:
            marker = match.group(1)
            marker_kind = marker[0]
            if not in_fence:
                in_fence = True
                fence_marker = marker_kind
            elif marker_kind == fence_marker:
                in_fence = False
                fence_marker = ""
            output.append("")
            continue
        output.append("" if in_fence else line)
    return "\n".join(output)
