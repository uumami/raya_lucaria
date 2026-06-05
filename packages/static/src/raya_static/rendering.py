from __future__ import annotations

import html
import re
from collections.abc import Callable
from dataclasses import dataclass

from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.footnote import footnote_plugin
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound


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
    def __init__(self, resolve_href: Callable[[str], str]) -> None:
        self._resolve_href = resolve_href
        self._md = MarkdownIt("commonmark", {"html": False})
        self._md.enable("table")
        self._md.use(footnote_plugin)
        self._md.use(dollarmath_plugin)
        self._default_image_renderer = self._md.renderer.rules.get("image")
        self._md.renderer.rules["heading_open"] = self._render_heading_open
        self._md.renderer.rules["link_open"] = self._render_link_open
        self._md.renderer.rules["image"] = self._render_image
        self._md.renderer.rules["fence"] = self._render_fence

    def render(self, body: str, generated_index: str = "") -> str:
        prepared_body, callouts = _extract_callouts(body)
        env = _new_env(self._resolve_href, collect_headings=True)
        marker_used = INDEX_MARKER in prepared_body
        if marker_used:
            prepared_body = prepared_body.replace(INDEX_MARKER, _INDEX_PLACEHOLDER)
        html_fragment = self._md.render(prepared_body, env)

        if marker_used:
            html_fragment = html_fragment.replace(
                f"<p>{_INDEX_PLACEHOLDER}</p>",
                generated_index,
            )
        else:
            if generated_index:
                html_fragment = html_fragment.rstrip() + "\n" + generated_index + "\n"

        html_fragment = self._replace_callout_placeholders(html_fragment, callouts)
        toc = _render_page_toc(env["raya_headings"])
        if toc:
            return toc + "\n" + html_fragment
        return html_fragment

    def _replace_callout_placeholders(
        self,
        html_fragment: str,
        callouts: dict[str, _Callout],
    ) -> str:
        for placeholder, callout in callouts.items():
            callout_html = self._render_callout(callout)
            html_fragment = html_fragment.replace(f"<p>{placeholder}</p>", callout_html)
        return html_fragment

    def _render_callout(self, callout: _Callout) -> str:
        label = _callout_label(callout.kind)
        inner_env = _new_env(self._resolve_href, collect_headings=False)
        inner = self._md.render(callout.body, inner_env).strip()
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


def render_markdown_body(
    body: str,
    *,
    generated_index: str,
    resolve_href: Callable[[str], str],
) -> str:
    return RichMarkdownRenderer(resolve_href).render(body, generated_index)


def missing_footnote_definitions(body: str) -> list[str]:
    text = _without_fenced_blocks(body)
    refs = set(_FOOTNOTE_REF_RE.findall(text))
    defs = set(_FOOTNOTE_DEF_RE.findall(text))
    return sorted(ref for ref in refs - defs if ref)


def rich_render_css() -> str:
    base = """
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
