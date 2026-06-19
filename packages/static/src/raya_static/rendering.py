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
from raya_static.numbered_objects import (
    NumberedObjectRenderContext,
    NumberedObjectRenderItem,
    expand_shorthand_references,
)
from raya_static.proofs import StaticEnvironmentRenderContext, StaticEnvironmentRenderItem


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
_DISPLAY_DELIMITER_RE = re.compile(r"(?m)^\s*\$\$\s*$")
_UNESCAPED_DISPLAY_SEQUENCE_RE = re.compile(r"(?<!\\)\$\$")
_UNESCAPED_INLINE_DOLLAR_RE = re.compile(r"(?<!\\)\$(?!\$)")
_LATEX_DOCUMENT_RE = re.compile(
    r"\\(?:documentclass|begin\{document\}|end\{document\})"
)
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


_CalloutFragment = tuple[_Callout, list[Token], dict]
_NumberedObjectFragment = tuple[NumberedObjectRenderItem, list[Token], dict]
_ProofFragment = tuple[StaticEnvironmentRenderItem, list[Token], dict]


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

    def render(
        self,
        body: str,
        generated_index: str = "",
        *,
        numbered_objects: NumberedObjectRenderContext | None = None,
        proofs: StaticEnvironmentRenderContext | None = None,
    ) -> str:
        if numbered_objects is not None:
            body = expand_shorthand_references(
                body,
                context=numbered_objects,
                report=self._report,
                source_path=self._source_path,
            )
            if not self._report.ok:
                return ""
        prepared_body, callouts = _extract_callouts(body)
        env = _new_env(self._resolve_href, collect_headings=True)
        marker_used = INDEX_MARKER in prepared_body
        if marker_used:
            prepared_body = prepared_body.replace(INDEX_MARKER, _INDEX_PLACEHOLDER)
        page_tokens = self._md.parse(prepared_body, env)
        callout_fragments: dict[str, _CalloutFragment] = {}
        for placeholder, callout in callouts.items():
            callout_env = _new_env(self._resolve_href, collect_headings=False)
            callout_tokens = self._md.parse(callout.body, callout_env)
            callout_fragments[placeholder] = (callout, callout_tokens, callout_env)
        numbered_object_fragments: dict[str, _NumberedObjectFragment] = {}
        if numbered_objects is not None:
            for item in numbered_objects.items:
                object_env = _new_env(self._resolve_href, collect_headings=False)
                object_body = expand_shorthand_references(
                    item.source.body,
                    context=numbered_objects,
                    report=self._report,
                    source_path=item.source.source_path,
                )
                if not self._report.ok:
                    return ""
                object_tokens = self._md.parse(object_body, object_env)
                numbered_object_fragments[item.source.placeholder] = (
                    item,
                    object_tokens,
                    object_env,
                )
        proof_fragments: dict[str, _ProofFragment] = {}
        if proofs is not None:
            proof_reference_context = NumberedObjectRenderContext(
                items=[],
                objects_by_id=proofs.objects_by_id,
            )
            for item in proofs.items:
                proof_env = _new_env(self._resolve_href, collect_headings=False)
                proof_body = expand_shorthand_references(
                    item.source.body,
                    context=proof_reference_context,
                    report=self._report,
                    source_path=item.source.source_path,
                )
                if not self._report.ok:
                    return ""
                proof_tokens = self._md.parse(proof_body, proof_env)
                proof_fragments[item.source.placeholder] = (
                    item,
                    proof_tokens,
                    proof_env,
                )

        math_items = _collect_math_items_in_render_order(
            page_tokens,
            callout_fragments,
            numbered_object_fragments,
            proof_fragments,
            source_path=self._source_path,
        )

        math_result = self._math_renderer.render_many(math_items, report=self._report)
        if not self._report.ok:
            return ""
        env["raya_math_html_by_id"] = math_result.html_by_id
        for _, _, callout_env in callout_fragments.values():
            callout_env["raya_math_html_by_id"] = math_result.html_by_id
        for _, _, object_env in numbered_object_fragments.values():
            object_env["raya_math_html_by_id"] = math_result.html_by_id
        for _, _, proof_env in proof_fragments.values():
            proof_env["raya_math_html_by_id"] = math_result.html_by_id

        html_fragment = self._md.renderer.render(page_tokens, self._md.options, env)
        if not self._report.ok:
            return ""

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
        if not self._report.ok:
            return ""
        html_fragment = self._replace_callout_placeholders(
            html_fragment,
            rendered_callouts,
        )
        rendered_numbered_objects = {
            placeholder: _render_numbered_object_html(
                self._md.renderer.render(object_tokens, self._md.options, object_env),
                item=item,
            )
            for placeholder, (
                item,
                object_tokens,
                object_env,
            ) in numbered_object_fragments.items()
        }
        html_fragment = self._replace_numbered_object_placeholders(
            html_fragment,
            rendered_numbered_objects,
        )
        rendered_proofs = {
            placeholder: _render_static_environment_html(
                self._md.renderer.render(proof_tokens, self._md.options, proof_env),
                item=item,
            )
            for placeholder, (
                item,
                proof_tokens,
                proof_env,
            ) in proof_fragments.items()
        }
        html_fragment = self._replace_proof_placeholders(
            html_fragment,
            rendered_proofs,
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

    def _replace_numbered_object_placeholders(
        self,
        html_fragment: str,
        numbered_objects: dict[str, str],
    ) -> str:
        for placeholder, object_html in numbered_objects.items():
            html_fragment = html_fragment.replace(f"<p>{placeholder}</p>", object_html)
        return html_fragment

    def _replace_proof_placeholders(
        self,
        html_fragment: str,
        proofs: dict[str, str],
    ) -> str:
        for placeholder, proof_html in proofs.items():
            html_fragment = html_fragment.replace(f"<p>{placeholder}</p>", proof_html)
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
            field=f"math:{item_id}" if isinstance(item_id, str) else "math",
            next_action=(
                "Check the MathJax renderer contract. "
                "No rendered HTML was available for math near "
                f"`{_math_excerpt(token.content)}`."
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
    numbered_objects: NumberedObjectRenderContext | None = None,
    proofs: StaticEnvironmentRenderContext | None = None,
) -> str:
    return RichMarkdownRenderer(
        resolve_href,
        source_path=source_path,
        report=report,
        math_renderer=math_renderer,
    ).render(
        body,
        generated_index,
        numbered_objects=numbered_objects,
        proofs=proofs,
    )


def missing_footnote_definitions(body: str) -> list[str]:
    text = _without_fenced_blocks(body)
    refs = set(_FOOTNOTE_REF_RE.findall(text))
    defs = set(_FOOTNOTE_DEF_RE.findall(text))
    return sorted(ref for ref in refs - defs if ref)


def has_malformed_display_math_delimiters(body: str) -> bool:
    text = _without_fenced_blocks(body)
    return len(_DISPLAY_DELIMITER_RE.findall(text)) % 2 == 1


def contains_full_latex_document(body: str) -> bool:
    return _LATEX_DOCUMENT_RE.search(_without_fenced_blocks(body)) is not None


def has_unsupported_nested_math_delimiters(body: str) -> bool:
    for line in _without_fenced_blocks(body).splitlines():
        if _UNESCAPED_DISPLAY_SEQUENCE_RE.search(line) is None:
            continue
        line_without_display = _UNESCAPED_DISPLAY_SEQUENCE_RE.sub("", line)
        if _UNESCAPED_INLINE_DOLLAR_RE.search(line_without_display) is not None:
            return True
    return False


def rich_render_css() -> str:
    base = """
* {
  box-sizing: border-box;
}
body {
  background: var(--raya-color-page);
  color: var(--raya-color-text);
  font-family: var(--raya-font-body), -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.6;
  margin: 0;
  overflow-wrap: anywhere;
}
a {
  color: var(--raya-color-accent);
}
img {
  height: auto;
  max-width: 100%;
}
:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
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
.raya-top-command-bar {
  background: var(--raya-color-surface);
  border-bottom: 1px solid var(--raya-color-border);
  position: sticky;
  top: 0;
  z-index: 5;
}
.raya-top-command-bar-inner,
.raya-learning-shell,
.raya-page-footer,
.raya-inspection-main {
  margin: 0 auto;
  max-width: 110rem;
  padding: var(--raya-space-page);
}
.raya-top-command-bar-inner {
  align-items: center;
  display: flex;
  gap: 1rem;
  justify-content: space-between;
}
.raya-course-title {
  font-family: var(--raya-font-heading), var(--raya-font-body), -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 0.875rem;
  font-weight: 700;
  margin: 0;
}
.raya-font-toggle {
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-accent);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  cursor: pointer;
  font: inherit;
  font-weight: 700;
  padding: 0.5rem 0.75rem;
}
.raya-font-toggle:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
.raya-learning-shell {
  display: grid;
  gap: calc(var(--raya-space-block) * 1.1);
  grid-template-areas: "course-map main-article learning-rail";
  grid-template-columns: minmax(4.5rem, 5.5rem) minmax(0, 1fr) minmax(14rem, 18rem);
}
.raya-course-map {
  grid-area: course-map;
  overflow: hidden;
}
.raya-main-article {
  grid-area: main-article;
}
.raya-learning-rail {
  grid-area: learning-rail;
}
.raya-course-map,
.raya-main-article,
.raya-learning-rail,
.raya-inspection-main {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  min-width: 0;
}
.raya-course-map,
.raya-learning-rail {
  position: sticky;
  top: 5rem;
}
.raya-course-map,
.raya-main-article,
.raya-learning-rail,
.raya-inspection-main {
  padding: var(--raya-space-panel);
}
.raya-region-title,
.raya-rail-title {
  font-family: var(--raya-font-heading), var(--raya-font-body), -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 0.875rem;
  font-weight: 700;
  margin: 0 0 0.75rem;
}
.raya-course-map-header {
  display: grid;
  gap: 0.5rem;
}
.raya-course-map-list {
  display: grid;
  gap: 0.15rem;
}
.raya-course-map-toggle {
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  cursor: pointer;
  font: inherit;
  font-weight: 700;
  padding: 0.45rem 0.65rem;
}
.raya-course-map-toggle:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 2px;
}
.raya-article-sequence {
  border-bottom: 1px solid var(--raya-color-border);
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: space-between;
  margin: 0 0 1rem;
  padding: 0 0 0.75rem;
}
.raya-course-map ol,
.raya-learning-rail ul {
  margin: 0;
  padding-left: 1.25rem;
}
.raya-course-map a {
  border-left: 3px solid transparent;
  display: block;
  padding: 0.25rem 0 0.25rem 0.5rem;
  text-decoration: none;
}
.raya-course-map a[aria-current="page"] {
  border-left-color: var(--raya-color-success);
  color: var(--raya-color-success);
  font-weight: 700;
}
@media (min-width: 901px) {
  [data-raya-course-map="expanded"] .raya-learning-shell,
  .raya-learning-shell[data-raya-course-map="expanded"] {
    grid-template-columns: minmax(14rem, 18rem) minmax(0, 1fr) minmax(12rem, 16rem);
  }
  [data-raya-course-map="collapsed"] .raya-course-map-list,
  .raya-course-map[data-raya-course-map="collapsed"] .raya-course-map-list {
    clip: rect(0 0 0 0);
    clip-path: inset(50%);
    height: 1px;
    overflow: hidden;
    position: absolute;
    white-space: nowrap;
    width: 1px;
  }
}
nav[aria-label="Breadcrumbs"] {
  color: var(--raya-color-muted);
  font-size: 0.875rem;
  margin-bottom: 0.75rem;
}
.raya-main-article > :first-child,
.raya-inspection-main > :first-child {
  margin-top: 0;
}
.raya-learning-rail {
  display: grid;
  gap: var(--raya-space-block);
}
.raya-rail-panel {
  border-bottom: 1px solid var(--raya-color-border);
  padding-bottom: var(--raya-space-block);
}
.raya-rail-panel:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}
.raya-status-chip {
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 999px;
  display: inline-block;
  font-size: 0.8125rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
}
.raya-page-footer {
  color: var(--raya-color-muted);
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
  font-family: var(--raya-font-mono), ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 0.8125rem;
  padding: 0.25rem 0.5rem;
}
.raya-code-block pre {
  font-family: var(--raya-font-mono), ui-monospace, SFMono-Regular, Consolas, monospace;
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
.raya-numbered-object {
  border: 1px solid #d8dee4;
  margin: 1.25rem 0;
}
.raya-numbered-object-heading {
  align-items: baseline;
  background: #f6f8fa;
  border-bottom: 1px solid #d8dee4;
  display: flex;
  font-family: var(--raya-font-heading), var(--raya-font-body), -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  flex-wrap: wrap;
  gap: 0.35rem 0.5rem;
  margin: 0;
  padding: 0.65rem 0.85rem;
}
.raya-numbered-object-reference {
  color: var(--raya-color-success);
  font-weight: 700;
}
.raya-numbered-object-title {
  color: var(--raya-color-text);
  font-weight: 700;
}
.raya-numbered-object-body {
  overflow-x: auto;
  padding: 0.85rem;
}
.raya-numbered-object-body > :first-child {
  margin-top: 0;
}
.raya-numbered-object-body > :last-child {
  margin-bottom: 0;
}
.raya-numbered-object--margin {
  border-left: 0.35rem solid #1a7f37;
}
.raya-numbered-object--banded {
  border-color: #d0d7de;
  border-top: 0.35rem solid #0969da;
}
.raya-numbered-object--banded .raya-numbered-object-heading {
  background: #ddf4ff;
}
.raya-numbered-object--caption {
  border-color: #d0d7de;
}
.raya-numbered-object--caption .raya-numbered-object-heading {
  background: #ffffff;
  border-bottom: 0;
  border-top: 1px solid #d8dee4;
}
.raya-numbered-object--caption .raya-numbered-object-body {
  background: #f6f8fa;
}
.raya-numbered-object--equation {
  border-color: #d0d7de;
}
.raya-numbered-object--equation .raya-numbered-object-heading {
  justify-content: center;
}
.raya-numbered-object--equation .raya-numbered-object-body {
  overflow-x: auto;
  text-align: center;
}
.raya-numbered-object--scannable {
  border-left: 0;
}
.raya-numbered-object-layout {
  display: grid;
  gap: 0;
  grid-template-columns: minmax(6rem, auto) 1fr;
}
.raya-numbered-object-badge {
  align-content: start;
  background: #f6f8fa;
  border-right: 1px solid #d8dee4;
  display: grid;
  gap: 0.25rem;
  padding: 0.85rem;
}
.raya-numbered-object-badge-label {
  color: var(--raya-color-success);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}
.raya-numbered-object-badge-number {
  color: var(--raya-color-text);
  font-size: 1.15rem;
  font-weight: 700;
  line-height: 1.2;
}
.raya-numbered-object-content {
  min-width: 0;
}
.raya-proof {
  border-left: 3px solid #57606a;
  margin: 1.25rem 0;
  padding: 0.2rem 0 0.2rem 1rem;
}
.raya-proof-heading {
  color: var(--raya-color-text);
  font-family: var(--raya-font-heading), var(--raya-font-body), -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-weight: 650;
  margin: 0 0 0.55rem;
}
.raya-proof-reference {
  font-style: italic;
}
.raya-proof-title {
  color: var(--raya-color-muted);
  font-weight: 500;
}
.raya-proof-body {
  overflow-x: auto;
}
.raya-proof-body > :first-child {
  margin-top: 0;
}
.raya-proof-body > :last-child {
  margin-bottom: 0;
}
.raya-proof-qed {
  float: right;
  margin-left: 0.75rem;
}
.raya-static-environment {
  border: 1px solid #d8dee4;
  border-left-width: 4px;
  margin: 1.25rem 0;
  overflow: hidden;
}
.raya-static-environment--solution {
  border-left-color: #1a7f37;
}
.raya-static-environment--hint {
  border-left-color: #9a6700;
}
.raya-static-environment--answer {
  border-left-color: #0969da;
}
.raya-static-environment-heading {
  background: #f6f8fa;
  border-bottom: 1px solid #d8dee4;
  font-family: var(--raya-font-heading), var(--raya-font-body), -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-weight: 650;
  margin: 0;
  padding: 0.6rem 0.85rem;
}
.raya-static-environment-reference {
  color: var(--raya-color-text);
}
.raya-static-environment-title {
  color: var(--raya-color-muted);
  font-weight: 500;
}
.raya-static-environment-body {
  overflow-x: auto;
  padding: 0.85rem;
}
.raya-static-environment-body > :first-child {
  margin-top: 0;
}
.raya-static-environment-body > :last-child {
  margin-bottom: 0;
}
.math.inline {
  white-space: nowrap;
}
.math.block {
  display: block;
  overflow-x: auto;
  padding: 0.5rem 0;
}
mjx-container {
  max-width: 100%;
}
mjx-container[display="true"] {
  overflow-x: auto;
  overflow-y: hidden;
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
  color: var(--raya-color-muted);
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
  color: var(--raya-color-muted);
  font-size: 0.875rem;
}
.raya-reviewed-output-excerpt {
  background: #f6f8fa;
  max-width: 100%;
  overflow-x: auto;
  padding: 0.75rem;
  white-space: pre-wrap;
}
@media (max-width: 900px) {
  .raya-learning-shell {
    grid-template-areas:
      "course-map"
      "main-article"
      "learning-rail";
    grid-template-columns: minmax(0, 1fr);
  }
  .raya-course-map,
  .raya-learning-rail {
    margin-bottom: 1rem;
    max-height: 14rem;
    overflow: auto;
    position: static;
  }
  .raya-learning-rail {
    margin-top: 1rem;
  }
}
@media (max-width: 520px) {
  .raya-top-command-bar-inner,
  .raya-learning-shell,
  .raya-page-footer,
  .raya-inspection-main {
    padding: 0.75rem;
  }
  .raya-top-command-bar-inner {
    align-items: stretch;
    display: grid;
  }
  .raya-course-map,
  .raya-main-article,
  .raya-learning-rail,
  .raya-inspection-main {
    border-radius: 0.25rem;
  }
  .raya-numbered-object-heading {
    display: block;
  }
  .raya-numbered-object-title {
    display: block;
  }
  .raya-numbered-object-layout {
    display: block;
  }
  .raya-numbered-object-badge {
    border-bottom: 1px solid #d8dee4;
    border-right: 0;
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


def _collect_math_items_in_render_order(
    page_tokens: list[Token],
    callout_fragments: dict[str, _CalloutFragment],
    numbered_object_fragments: dict[str, _NumberedObjectFragment],
    proof_fragments: dict[str, _ProofFragment],
    *,
    source_path: Path,
) -> list[MathItem]:
    items: list[MathItem] = []
    idx = 0
    while idx < len(page_tokens):
        placeholder = _callout_placeholder_at(page_tokens, idx, callout_fragments)
        if placeholder is not None:
            _, callout_tokens, _ = callout_fragments[placeholder]
            new_items = _collect_math_items(
                callout_tokens,
                source_path=source_path,
                counter=len(items),
            )
            items.extend(new_items)
            idx += 3
            continue
        object_placeholder = _numbered_object_placeholder_at(
            page_tokens,
            idx,
            numbered_object_fragments,
        )
        if object_placeholder is not None:
            _, object_tokens, _ = numbered_object_fragments[object_placeholder]
            new_items = _collect_math_items(
                object_tokens,
                source_path=source_path,
                counter=len(items),
            )
            items.extend(new_items)
            idx += 3
            continue
        proof_placeholder = _proof_placeholder_at(
            page_tokens,
            idx,
            proof_fragments,
        )
        if proof_placeholder is not None:
            _, proof_tokens, _ = proof_fragments[proof_placeholder]
            new_items = _collect_math_items(
                proof_tokens,
                source_path=source_path,
                counter=len(items),
            )
            items.extend(new_items)
            idx += 3
            continue

        new_items = _collect_math_items(
            [page_tokens[idx]],
            source_path=source_path,
            counter=len(items),
        )
        items.extend(new_items)
        idx += 1
    return items


def _callout_placeholder_at(
    tokens: list[Token],
    idx: int,
    callout_fragments: dict[str, _CalloutFragment],
) -> str | None:
    if idx + 2 >= len(tokens):
        return None
    if tokens[idx].type != "paragraph_open":
        return None
    inline = tokens[idx + 1]
    if inline.type != "inline" or inline.content not in callout_fragments:
        return None
    if tokens[idx + 2].type != "paragraph_close":
        return None
    return inline.content


def _numbered_object_placeholder_at(
    tokens: list[Token],
    idx: int,
    numbered_object_fragments: dict[str, _NumberedObjectFragment],
) -> str | None:
    if idx + 2 >= len(tokens):
        return None
    if tokens[idx].type != "paragraph_open":
        return None
    inline = tokens[idx + 1]
    if inline.type != "inline" or inline.content not in numbered_object_fragments:
        return None
    if tokens[idx + 2].type != "paragraph_close":
        return None
    return inline.content


def _proof_placeholder_at(
    tokens: list[Token],
    idx: int,
    proof_fragments: dict[str, _ProofFragment],
) -> str | None:
    if idx + 2 >= len(tokens):
        return None
    if tokens[idx].type != "paragraph_open":
        return None
    inline = tokens[idx + 1]
    if inline.type != "inline" or inline.content not in proof_fragments:
        return None
    if tokens[idx + 2].type != "paragraph_close":
        return None
    return inline.content


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


def _math_excerpt(tex: str) -> str:
    normalized = " ".join(tex.strip().split())
    if len(normalized) <= 80:
        return normalized
    return normalized[:77] + "..."


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


def _render_numbered_object_html(
    rendered_body: str,
    *,
    item: NumberedObjectRenderItem,
) -> str:
    obj = item.object
    escaped_id = html.escape(obj.id, quote=True)
    escaped_family = html.escape(obj.family, quote=True)
    escaped_style = html.escape(obj.style, quote=True)
    escaped_reference = html.escape(obj.reference_text)
    escaped_label = html.escape(obj.label)
    escaped_number = html.escape(obj.number)
    title = obj.title or ""
    body = rendered_body.strip() or "<p></p>"
    title_html = (
        f'<span class="raya-numbered-object-title">{html.escape(title)}</span>'
        if title
        else ""
    )
    opening = (
        f'<section id="raya-object-{escaped_id}" '
        f'class="raya-numbered-object raya-numbered-object--{escaped_style} '
        f'raya-numbered-object--{escaped_family}" '
        f'data-object-id="{escaped_id}">'
    )
    if obj.style == "scannable":
        return "\n".join(
            [
                opening,
                '<div class="raya-numbered-object-layout">',
                '<div class="raya-numbered-object-badge" aria-hidden="true">',
                (
                    f'<span class="raya-numbered-object-badge-label">'
                    f"{escaped_label}</span>"
                ),
                (
                    f'<span class="raya-numbered-object-badge-number">'
                    f"{escaped_number}</span>"
                ),
                "</div>",
                '<div class="raya-numbered-object-content">',
                '<p class="raya-numbered-object-heading">',
                f'<span class="raya-numbered-object-reference">{escaped_reference}</span>'
                + (f" {title_html}" if title_html else ""),
                "</p>",
                '<div class="raya-numbered-object-body">',
                body,
                "</div>",
                "</div>",
                "</div>",
                "</section>",
            ]
        )
    return "\n".join(
        [
            opening,
            '<p class="raya-numbered-object-heading">',
            f'<span class="raya-numbered-object-reference">{escaped_reference}</span>'
            + (f" {title_html}" if title_html else ""),
            "</p>",
            '<div class="raya-numbered-object-body">',
            body,
            "</div>",
            "</section>",
        ]
    )


def _static_environment_reference(item: StaticEnvironmentRenderItem) -> str:
    kind = item.source.kind
    label = {
        "proof": "Proof",
        "solution": "Solution",
        "hint": "Hint",
        "answer": "Answer",
    }[kind]
    if item.target is None:
        return label
    if kind == "hint":
        return f"Hint for {item.target.reference_text}"
    if kind == "answer":
        return f"Answer to {item.target.reference_text}"
    return f"{label} of {item.target.reference_text}"


def _render_static_environment_html(
    rendered_body: str,
    *,
    item: StaticEnvironmentRenderItem,
) -> str:
    env_id = item.source.id
    kind = item.source.kind
    reference = _static_environment_reference(item)
    title = item.source.title or ""
    body = rendered_body.strip() or "<p></p>"
    if kind == "proof":
        id_html = (
            f' id="raya-proof-{html.escape(env_id, quote=True)}"' if env_id else ""
        )
        title_html = (
            f'<span class="raya-proof-title">{html.escape(title)}</span>'
            if title
            else ""
        )
        return "\n".join(
            [
                f'<section{id_html} class="raya-proof">',
                '<p class="raya-proof-heading">',
                f'<span class="raya-proof-reference">{html.escape(reference)}</span>'
                + (f" {title_html}" if title_html else ""),
                "</p>",
                '<div class="raya-proof-body">',
                body,
                '<span class="raya-proof-qed" aria-hidden="true">&#x25A1;</span>',
                "</div>",
                "</section>",
            ]
        )

    escaped_kind = html.escape(kind, quote=True)
    id_html = (
        f' id="raya-static-environment-{html.escape(env_id, quote=True)}"'
        if env_id
        else ""
    )
    title_html = (
        f'<span class="raya-static-environment-title">{html.escape(title)}</span>'
        if title
        else ""
    )
    return "\n".join(
        [
            (
                f'<section{id_html} class="raya-static-environment '
                f'raya-static-environment--{escaped_kind}">'
            ),
            '<p class="raya-static-environment-heading">',
            f'<span class="raya-static-environment-reference">{html.escape(reference)}</span>'
            + (f" {title_html}" if title_html else ""),
            "</p>",
            '<div class="raya-static-environment-body">',
            body,
            "</div>",
            "</section>",
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
