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
        header = (
            '<div class="raya-code-header">'
            f"{label}"
            '<button class="raya-code-copy" type="button" '
            'data-raya-copy-code aria-label="Copy code block">Copy</button>'
            "</div>"
        )
        return (
            f'<div class="raya-code-block"{data_language}>'
            f"{header}"
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
html {
  scroll-padding-top: 5.5rem;
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
  background: var(--raya-color-text);
  backdrop-filter: blur(18px);
  border-bottom: 1px solid color-mix(in srgb, var(--raya-color-text) 72%, var(--raya-color-accent));
  color: var(--raya-color-surface);
  position: sticky;
  top: 0;
  z-index: 5;
}
.raya-discovery-command-bar {
  box-shadow: 0 0.75rem 2rem color-mix(in srgb, var(--raya-color-text) 18%, transparent);
}
.raya-top-command-bar-inner,
.raya-learning-shell,
.raya-page-footer,
.raya-inspection-main {
  margin: 0 auto;
  max-width: 110rem;
  padding: var(--raya-space-page);
}
.raya-learning-shell {
  max-width: 116rem;
}
.raya-top-command-bar-inner {
  align-items: center;
  display: flex;
  gap: var(--raya-space-block);
  justify-content: space-between;
  padding-block: 0.75rem;
}
.raya-reading-context {
  align-items: center;
  color: inherit;
  display: flex;
  flex: 1 1 auto;
  flex-wrap: wrap;
  gap: 0.35rem 0.6rem;
  min-width: 0;
}
.raya-reading-context-course,
.raya-reading-context-page {
  color: inherit;
  font-family: var(--raya-font-heading), var(--raya-font-body), -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-weight: 700;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.raya-reading-context-course {
  font-size: 0.75rem;
  opacity: 0.82;
}
.raya-reading-context-page {
  font-size: 0.95rem;
}
.raya-reading-context-position {
  background: color-mix(in srgb, var(--raya-color-accent-soft) 82%, var(--raya-color-text));
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 52%, transparent);
  border-radius: 999px;
  color: var(--raya-color-text);
  display: inline-flex;
  flex: 0 0 auto;
  font-size: 0.75rem;
  font-weight: 800;
  line-height: 1;
  padding: 0.28rem 0.5rem;
}
.raya-reading-context-separator {
  color: var(--raya-color-muted);
  flex: 0 0 auto;
  font-size: 0.82rem;
  font-weight: 700;
}
.raya-reading-context-sequence {
  align-items: center;
  display: inline-flex;
  flex: 0 0 auto;
  gap: 0.35rem;
}
.raya-reading-context-link {
  background: var(--raya-color-accent-soft);
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 58%, var(--raya-color-border));
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  display: inline-flex;
  font-size: 0.75rem;
  font-weight: 800;
  line-height: 1;
  min-height: 1.9rem;
  padding: 0.35rem 0.5rem;
  text-decoration: none;
}
.raya-reading-context-link:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
.raya-reading-context-link:hover {
  background: color-mix(in srgb, var(--raya-color-accent-soft) 72%, var(--raya-color-surface));
}
.raya-course-title {
  color: inherit;
  font-family: var(--raya-font-heading), var(--raya-font-body), -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 0.875rem;
  font-weight: 700;
  margin: 0;
}
.raya-course-tools {
  align-items: center;
  display: flex;
  flex-wrap: nowrap;
  gap: 0.5rem;
  justify-content: flex-end;
  min-width: 0;
}
.raya-command {
  align-items: center;
  background: var(--raya-color-accent-soft);
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 64%, var(--raya-color-border));
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  cursor: pointer;
  display: inline-flex;
  font: inherit;
  font-weight: 700;
  gap: 0.45rem;
  justify-content: center;
  min-height: 2.5rem;
  min-width: 2.75rem;
  padding: 0.45rem 0.65rem;
  text-decoration: none;
}
.raya-command::before {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-accent) 16%, transparent);
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 56%, transparent);
  border-radius: 0.25rem;
  color: var(--raya-color-text);
  display: inline-flex;
  flex: 0 0 auto;
  font-size: 0.75rem;
  font-weight: 800;
  height: 1.5rem;
  justify-content: center;
  line-height: 1;
  min-width: 1.5rem;
  padding: 0 0.2rem;
}
.raya-command-search::before {
  content: "S";
}
.raya-command-home::before {
  content: "C";
}
.raya-command-graph::before {
  content: "G";
}
.raya-command-practice::before {
  content: "P";
}
.raya-command-map::before {
  content: "M";
}
.raya-command-size::before {
  content: "T";
}
.raya-command-font::before {
  content: "Aa";
}
.raya-command:hover {
  background: color-mix(in srgb, var(--raya-color-accent-soft) 72%, var(--raya-color-surface));
}
.raya-command:focus-visible,
.raya-font-toggle:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
.raya-graph-back-link {
  align-items: center;
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  display: inline-flex;
  font-weight: 700;
  min-height: 2.25rem;
  padding: 0.45rem 0.75rem;
  text-decoration: none;
}
.raya-graph-back-link:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
.raya-graph-page,
.raya-search-page,
.raya-practice-page {
  margin: 0 auto;
  max-width: 118rem;
  padding: var(--raya-space-page);
}
.raya-graph-page {
  --raya-graph-group-1: var(--raya-color-accent);
  --raya-graph-group-2: var(--raya-color-success);
  --raya-graph-group-3: color-mix(in srgb, var(--raya-color-accent) 68%, var(--raya-color-success));
  --raya-graph-group-4: color-mix(in srgb, var(--raya-color-success) 70%, var(--raya-color-text));
  --raya-graph-group-5: color-mix(in srgb, var(--raya-color-accent) 58%, var(--raya-color-text));
  --raya-graph-group-6: color-mix(in srgb, var(--raya-color-success) 52%, var(--raya-color-accent-soft));
  --raya-graph-group-7: color-mix(in srgb, var(--raya-color-accent) 44%, var(--raya-color-surface));
  --raya-graph-group-8: color-mix(in srgb, var(--raya-color-success) 44%, var(--raya-color-surface));
}
.raya-graph-header,
.raya-search-header,
.raya-practice-header,
.raya-graph-controls,
.raya-search-controls,
.raya-practice-controls,
.raya-graph-groups,
.raya-graph-status,
.raya-graph-hover-status,
.raya-graph-instructions,
.raya-search-status,
.raya-practice-status,
.raya-graph-canvas,
.raya-graph-list,
.raya-search-results,
.raya-practice-results,
.raya-search-empty,
.raya-practice-empty {
  margin-bottom: var(--raya-space-block);
}
.raya-graph-header,
.raya-search-header,
.raya-practice-header {
  max-width: 72rem;
}
.raya-graph-workspace {
  align-items: stretch;
  display: grid;
  gap: var(--raya-space-block);
  grid-template-columns: minmax(16rem, 22rem) minmax(34rem, 1fr) minmax(18rem, 24rem);
  margin-top: var(--raya-space-block);
}
.raya-graph-list-panel,
.raya-graph-map-panel,
.raya-graph-inspector-panel {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.5rem;
  min-width: 0;
  padding: 0.9rem;
}
.raya-search-workspace,
.raya-practice-workspace {
  align-items: start;
  display: grid;
  gap: var(--raya-space-block);
  grid-template-columns: minmax(16rem, 22rem) minmax(28rem, 1fr) minmax(17rem, 23rem);
  margin-top: var(--raya-space-block);
}
.raya-search-control-panel,
.raya-search-results-panel,
.raya-search-context-panel,
.raya-practice-control-panel,
.raya-practice-results-panel,
.raya-practice-context-panel {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.5rem;
  min-width: 0;
  padding: 0.9rem;
}
.raya-search-control-panel,
.raya-search-context-panel,
.raya-practice-control-panel,
.raya-practice-context-panel {
  position: sticky;
  top: calc(var(--raya-topbar-height, 4rem) + 1rem);
}
.raya-search-control-panel h2,
.raya-search-context-panel h2,
.raya-practice-control-panel h2,
.raya-practice-context-panel h2 {
  font-size: 1rem;
  margin: 0 0 0.75rem;
}
.raya-search-results-panel,
.raya-practice-results-panel {
  display: grid;
  gap: 0.75rem;
}
.raya-discovery-summary,
.raya-discovery-context-meta {
  color: var(--raya-color-muted);
  font-size: 0.9rem;
  margin: 0.65rem 0 0;
}
.raya-search-context-panel [data-raya-search-context-title],
.raya-practice-context-panel [data-raya-practice-context-title] {
  font-weight: 800;
  line-height: 1.35;
  margin: 0;
}
.raya-graph-map-panel {
  display: flex;
  flex-direction: column;
}
.raya-graph-panel-header {
  align-items: center;
  display: flex;
  gap: 0.75rem;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}
.raya-graph-panel-header h2 {
  font-size: 1rem;
  margin: 0;
}
.raya-graph-panel-header button {
  background: color-mix(in srgb, var(--raya-color-surface) 88%, var(--raya-color-accent-soft));
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  font: inherit;
  font-weight: 700;
  min-height: 2.25rem;
  padding: 0.3rem 0.6rem;
}
.raya-graph-panel-body[aria-hidden="true"] {
  display: none;
}
[data-raya-graph-list-state="collapsed"] .raya-graph-workspace {
  grid-template-columns: minmax(4.5rem, 5.5rem) minmax(34rem, 1fr) minmax(18rem, 24rem);
}
[data-raya-graph-inspector-state="collapsed"] .raya-graph-workspace {
  grid-template-columns: minmax(16rem, 22rem) minmax(34rem, 1fr) minmax(4.5rem, 5.5rem);
}
[data-raya-graph-list-state="collapsed"][data-raya-graph-inspector-state="collapsed"] .raya-graph-workspace {
  grid-template-columns: minmax(4.5rem, 5.5rem) minmax(40rem, 1fr) minmax(4.5rem, 5.5rem);
}
[data-raya-graph-list-state="collapsed"] .raya-graph-list-panel,
[data-raya-graph-inspector-state="collapsed"] .raya-graph-inspector-panel {
  align-items: center;
  display: flex;
  flex-direction: column;
}
[data-raya-graph-list-state="collapsed"] .raya-graph-list-panel .raya-graph-panel-header,
[data-raya-graph-inspector-state="collapsed"] .raya-graph-inspector-panel .raya-graph-panel-header {
  flex-direction: column;
}
[data-raya-graph-list-state="collapsed"] .raya-graph-list-panel h2,
[data-raya-graph-inspector-state="collapsed"] .raya-graph-inspector-panel h2 {
  writing-mode: vertical-rl;
}
[data-raya-graph-expanded="true"] .raya-graph-workspace {
  grid-template-columns: minmax(4.5rem, 5.5rem) minmax(40rem, 1fr) minmax(18rem, 24rem);
}
.raya-graph-controls,
.raya-search-controls,
.raya-practice-controls,
.raya-graph-groups {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}
.raya-search-control-panel .raya-search-controls,
.raya-practice-control-panel .raya-practice-controls {
  align-items: stretch;
  display: grid;
  gap: 0.65rem;
}
.raya-graph-controls input,
.raya-search-controls input,
.raya-practice-controls input,
.raya-graph-controls select,
.raya-graph-controls button,
.raya-search-controls button,
.raya-practice-controls button,
.raya-graph-chip,
.raya-practice-chip {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  font: inherit;
  min-height: 2.5rem;
  padding: 0.45rem 0.7rem;
}
.raya-graph-controls button:disabled {
  cursor: not-allowed;
  opacity: 0.52;
}
.raya-search-controls input {
  min-width: 0;
  width: 100%;
}
.raya-practice-controls input {
  min-width: 0;
  width: 100%;
}
.raya-practice-filters {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.raya-search-results {
  display: grid;
  gap: 0.75rem;
  list-style: none;
  padding-left: 0;
}
.raya-search-results li {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  padding: 0.9rem 1rem;
}
.raya-search-results li[data-raya-search-active="true"] {
  border-color: var(--raya-color-accent);
  box-shadow: inset 0.25rem 0 0 var(--raya-color-accent);
}
.raya-search-results li[data-raya-search-active="true"] .raya-search-result-page {
  color: var(--raya-color-success);
  font-weight: 800;
}
.raya-search-results li[hidden],
.raya-search-empty[hidden],
.raya-practice-empty[hidden],
.raya-practice-group[hidden],
.raya-practice-object[hidden] {
  display: none;
}
.raya-search-result-meta,
.raya-search-result-counts,
.raya-search-status,
.raya-practice-status,
.raya-search-empty,
.raya-practice-empty,
.raya-practice-meta {
  color: var(--raya-color-muted);
  font-size: 0.875rem;
}
.raya-search-result-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0.65rem 0 0;
}
.raya-search-result-open,
.raya-search-result-graph,
.raya-search-result-practice {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-surface) 88%, var(--raya-color-accent-soft));
  border: 1px solid var(--raya-color-border);
  border-radius: 0.35rem;
  color: var(--raya-color-link);
  display: inline-flex;
  font-weight: 700;
  min-height: 2.25rem;
  padding: 0.25rem 0.65rem;
}
.raya-graph-chip[aria-pressed="true"] {
  border-color: var(--raya-color-accent);
  box-shadow: inset 0 -0.2rem 0 var(--raya-graph-group-color, var(--raya-color-accent));
}
.raya-practice-chip[aria-pressed="true"] {
  border-color: var(--raya-color-accent);
  box-shadow: inset 0 -0.2rem 0 var(--raya-color-accent);
}
.raya-graph-chip {
  align-items: center;
  display: inline-flex;
  gap: 0.45rem;
}
.raya-practice-results {
  display: grid;
  gap: 1.25rem;
}
.raya-practice-group {
  display: grid;
  gap: 0.75rem;
}
.raya-practice-group h2 {
  border-bottom: 1px solid var(--raya-color-border);
  margin-bottom: 0;
  padding-bottom: 0.35rem;
}
.raya-practice-grid {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 22rem), 1fr));
}
.raya-practice-object {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.5rem;
  box-shadow: inset 0.25rem 0 0 var(--raya-color-accent);
  padding: 1rem;
  transition: border-color 120ms ease, box-shadow 120ms ease, transform 120ms ease;
}
.raya-practice-object[data-raya-practice-active="true"] {
  border-color: var(--raya-color-accent);
  box-shadow:
    inset 0.25rem 0 0 var(--raya-color-accent),
    0 0 0 3px color-mix(in srgb, var(--raya-color-accent) 24%, transparent);
  transform: translateY(-1px);
}
.raya-practice-object-header,
.raya-practice-actions {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.raya-practice-kind,
.raya-practice-authority {
  border: 1px solid var(--raya-color-border);
  border-radius: 999px;
  color: var(--raya-color-muted);
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0;
  padding: 0.15rem 0.5rem;
  text-transform: uppercase;
}
.raya-practice-kind {
  background: color-mix(in srgb, var(--raya-color-accent) 12%, transparent);
  color: var(--raya-color-text);
}
.raya-practice-object h3 {
  font-size: clamp(1.05rem, 1rem + 0.2vw, 1.25rem);
  margin: 0.65rem 0 0.4rem;
}
.raya-practice-object[data-raya-practice-active="true"] h3 {
  color: var(--raya-color-success);
}
.raya-practice-actions {
  margin: 0.75rem 0 0;
}
.raya-practice-open,
.raya-practice-graph {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-surface) 88%, var(--raya-color-accent-soft));
  border: 1px solid var(--raya-color-border);
  border-radius: 0.35rem;
  display: inline-flex;
  font-weight: 700;
  min-height: 2.25rem;
  padding: 0.25rem 0.65rem;
}
.raya-graph-group-swatch {
  background: var(--raya-graph-group-color, var(--raya-color-accent));
  border: 1px solid color-mix(in srgb, var(--raya-color-text) 24%, transparent);
  border-radius: 999px;
  display: inline-block;
  height: 0.85rem;
  width: 0.85rem;
}
.raya-graph-instructions,
.raya-graph-hover-status {
  color: var(--raya-color-muted);
  font-size: 0.9rem;
}
.raya-graph-hover-status {
  border-left: 0.22rem solid var(--raya-color-border);
  min-height: 1.6rem;
  padding-left: 0.65rem;
}
.raya-graph-legend {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-surface) 88%, var(--raya-color-accent-soft));
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem 1rem;
  margin-bottom: var(--raya-space-block);
  padding: 0.7rem 0.85rem;
}
.raya-graph-legend-item {
  align-items: center;
  color: var(--raya-color-muted);
  display: inline-flex;
  font-size: 0.875rem;
  font-weight: 700;
  gap: 0.4rem;
}
.raya-graph-legend-swatch {
  background: var(--raya-color-accent-soft);
  border: 2px solid var(--raya-color-accent);
  border-radius: 999px;
  display: inline-block;
  height: 0.85rem;
  width: 0.85rem;
}
.raya-graph-legend-match {
  border-width: 4px;
}
.raya-graph-legend-selected {
  background: var(--raya-color-success);
  border-color: var(--raya-color-success);
}
.raya-graph-legend-neighbor {
  background: color-mix(in srgb, var(--raya-color-accent-soft) 62%, var(--raya-color-success));
  border-color: var(--raya-color-accent);
}
.raya-graph-legend-line {
  background: var(--raya-color-border);
  display: inline-block;
  height: 0.18rem;
  width: 1.6rem;
}
.raya-graph-legend-edge-color {
  background: linear-gradient(
    90deg,
    var(--raya-graph-group-1),
    var(--raya-graph-group-2)
  );
}
.raya-graph-help {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  margin-bottom: var(--raya-space-block);
  padding: 0.75rem 0.9rem;
}
.raya-graph-help summary {
  cursor: pointer;
  font-weight: 800;
}
.raya-graph-help p {
  margin: 0.65rem 0 0;
}
.raya-graph-detail {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  margin-bottom: var(--raya-space-block);
  padding: 0.9rem 1rem;
}
.raya-graph-detail [hidden] {
  display: none;
}
.raya-graph-detail-header {
  align-items: center;
  display: flex;
  gap: 0.75rem;
  justify-content: space-between;
}
.raya-graph-detail-header h2 {
  font-size: 1rem;
  margin: 0;
}
.raya-graph-detail button {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  font: inherit;
  min-height: 2.25rem;
  padding: 0.35rem 0.65rem;
}
.raya-graph-detail button[aria-pressed="true"] {
  background: var(--raya-color-accent);
  border-color: var(--raya-color-accent);
  color: var(--raya-color-accent-contrast);
}
.raya-graph-detail-focus-node {
  margin-left: 0.4rem;
}
.raya-graph-detail-meta,
.raya-graph-detail-summary,
.raya-graph-detail-study-counts,
.raya-graph-detail-edge-kind {
  color: var(--raya-color-muted);
  font-size: 0.875rem;
}
.raya-graph-detail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0.65rem 0;
}
.raya-graph-detail-actions a {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-surface) 88%, var(--raya-color-accent-soft));
  border: 1px solid var(--raya-color-border);
  border-radius: 0.35rem;
  color: var(--raya-color-link);
  display: inline-flex;
  font-weight: 700;
  min-height: 2.25rem;
  padding: 0.25rem 0.65rem;
}
.raya-graph-detail-actions a[hidden] {
  display: none;
}
.raya-graph-detail-neighborhood {
  border-left: 0.22rem solid var(--raya-color-accent);
  color: var(--raya-color-muted);
  font-size: 0.9rem;
  font-weight: 700;
  margin: 0.65rem 0;
  padding-left: 0.65rem;
}
.raya-graph-detail-links {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.raya-graph-detail-links h3 {
  font-size: 0.95rem;
  margin: 0 0 0.35rem;
}
.raya-graph-detail-links ul {
  margin: 0;
  padding-left: 1.2rem;
}
.raya-graph-pan-controls {
  align-items: center;
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.raya-graph-canvas {
  background: color-mix(in srgb, var(--raya-color-surface) 94%, var(--raya-color-accent-soft));
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  cursor: grab;
  display: block;
  flex: 1 1 auto;
  min-height: 34rem;
  width: 100%;
}
.raya-graph-canvas.is-panning {
  cursor: grabbing;
}
.raya-graph-canvas:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
[data-raya-graph-expanded="true"] .raya-graph-canvas {
  min-height: clamp(34rem, 72vh, 48rem);
}
.raya-graph-canvas[hidden] {
  display: none;
}
.raya-graph-edge {
  stroke: var(--raya-graph-edge-color, var(--raya-color-border));
  stroke-opacity: 0.58;
  stroke-width: 2;
}
.raya-graph-edge.is-active {
  stroke: var(--raya-color-accent);
  stroke-opacity: 0.86;
  stroke-width: 3;
}
.raya-graph-edge.is-search-context {
  stroke-opacity: 0.82;
}
.raya-graph-edge.is-search-dimmed {
  stroke-opacity: 0.12;
}
.raya-graph-edge.is-inspected {
  stroke: var(--raya-graph-edge-color, var(--raya-color-success));
  stroke-opacity: 0.94;
  stroke-width: 3;
}
.raya-graph-edge.is-dimmed {
  stroke-opacity: 0.14;
}
.raya-graph-node-link {
  cursor: pointer;
}
.raya-graph-node-hit {
  fill: transparent;
  pointer-events: all;
  stroke: transparent;
}
.raya-graph-node circle {
  fill: color-mix(in srgb, var(--raya-graph-node-color, var(--raya-color-accent)) 24%, var(--raya-color-surface));
  stroke: var(--raya-graph-node-color, var(--raya-color-accent));
  stroke-width: 2;
}
.raya-graph-node.is-inspected circle {
  fill: color-mix(in srgb, var(--raya-graph-node-color, var(--raya-color-accent)) 54%, var(--raya-color-surface));
  stroke-width: 4;
}
.raya-graph-node.is-inspected-neighbor circle {
  fill: color-mix(in srgb, var(--raya-graph-node-color, var(--raya-color-accent)) 38%, var(--raya-color-surface));
  stroke-width: 3;
}
.raya-graph-node.is-selected circle {
  fill: var(--raya-color-success);
  stroke: var(--raya-color-success);
}
.raya-graph-node.is-neighbor circle {
  fill: color-mix(in srgb, var(--raya-color-accent-soft) 58%, var(--raya-color-success));
  stroke: var(--raya-color-accent);
  stroke-width: 3;
}
.raya-graph-node.is-match circle {
  stroke-width: 4;
}
.raya-graph-node.is-search-context circle {
  fill: color-mix(in srgb, var(--raya-graph-node-color, var(--raya-color-accent)) 34%, var(--raya-color-surface));
}
.raya-graph-node text {
  fill: var(--raya-color-text);
  font-size: 0.78rem;
  font-weight: 700;
  text-anchor: middle;
}
.raya-graph-node.is-muted {
  opacity: 0.28;
}
.raya-graph-node.is-dimmed {
  opacity: 0.16;
}
.raya-graph-node.is-search-dimmed {
  opacity: 0.18;
}
.raya-graph-list {
  columns: 1;
  padding-left: 1.25rem;
}
.raya-graph-list li {
  break-inside: avoid;
  margin-bottom: 0.35rem;
}
.raya-graph-list-summary {
  color: var(--raya-color-muted);
  display: block;
  font-size: 0.85rem;
}
.raya-graph-list li.is-active a {
  color: var(--raya-color-success);
  font-weight: 700;
}
.raya-graph-list li.is-active-result a {
  background: color-mix(in srgb, var(--raya-color-accent) 12%, transparent);
  outline: 2px solid var(--raya-color-accent);
  outline-offset: 2px;
}
.raya-graph-list li.is-neighbor a {
  font-weight: 700;
  text-decoration: underline;
  text-decoration-thickness: 0.1em;
}
.raya-graph-list li.is-inspected a {
  color: var(--raya-color-success);
  font-weight: 800;
}
.raya-graph-list li.is-inspected-neighbor a {
  text-decoration: underline;
  text-decoration-thickness: 0.1em;
}
.raya-graph-list li.is-match a {
  text-decoration: underline;
  text-decoration-thickness: 0.12em;
}
.raya-graph-list li[hidden] {
  display: none;
}
.raya-learning-shell {
  display: grid;
  gap: 0.875rem;
  grid-template-areas: "course-map main-article learning-rail";
  grid-template-columns: minmax(13.75rem, 16rem) minmax(0, 1fr) minmax(16rem, 18rem);
}
html[data-raya-shell-ready="true"] .raya-learning-shell {
  transition: grid-template-columns 180ms ease;
}
.raya-course-map {
  align-self: start;
  grid-area: course-map;
  max-height: calc(100vh - 6rem);
  overflow: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
}
html[data-raya-shell-ready="true"] .raya-course-map {
  transition: max-height 180ms ease, width 180ms ease;
}
.raya-main-article {
  grid-area: main-article;
  font-size: calc(1rem * var(--raya-reader-text-scale, 1));
}
.raya-learning-rail {
  grid-area: learning-rail;
  font-size: calc(1rem * var(--raya-reader-text-scale, 1));
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
.raya-main-article {
  box-shadow: 0 1rem 2.5rem rgba(31, 35, 40, 0.08);
}
.raya-course-map,
.raya-learning-rail {
  background: color-mix(in srgb, var(--raya-color-surface) 86%, var(--raya-color-page));
  border-color: color-mix(in srgb, var(--raya-color-border) 62%, var(--raya-color-page));
  box-shadow: 0 0.75rem 1.75rem rgba(31, 35, 40, 0.06);
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
.raya-learning-rail-header {
  align-items: center;
  border-bottom: 1px solid var(--raya-color-border);
  display: flex;
  gap: 0.75rem;
  justify-content: space-between;
  margin-bottom: 0.25rem;
  padding-bottom: 0.75rem;
}
.raya-learning-rail-header .raya-region-title {
  margin-bottom: 0;
}
.raya-learning-rail-body {
  display: grid;
  gap: 0;
}
.raya-learning-rail-collapse,
.raya-learning-rail-expand {
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  cursor: pointer;
  font: inherit;
  font-size: 0.8125rem;
  font-weight: 700;
  line-height: 1;
  padding: 0.45rem 0.65rem;
  white-space: nowrap;
}
.raya-learning-rail-expand {
  display: none;
}
.raya-learning-rail-collapse:focus-visible,
.raya-learning-rail-expand:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 2px;
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
.raya-rail-toggle {
  align-items: center;
  background: transparent;
  border: 0;
  color: inherit;
  cursor: pointer;
  display: flex;
  font: inherit;
  font-weight: 700;
  justify-content: space-between;
  padding: 0;
  text-align: left;
  width: 100%;
}
.raya-rail-toggle::after {
  content: "+";
  font-weight: 700;
  margin-left: 0.75rem;
}
.raya-rail-toggle[aria-expanded="true"]::after {
  content: "-";
}
.raya-rail-toggle:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
.raya-rail-panel-body {
  display: grid;
  grid-template-rows: 1fr;
  margin-top: 0.5rem;
  opacity: 1;
}
html[data-raya-shell-ready="true"] .raya-rail-panel-body {
  transition: grid-template-rows 220ms ease, opacity 180ms ease, margin-top 220ms ease;
}
@media (prefers-reduced-motion: reduce) {
  html[data-raya-shell-ready="true"] .raya-learning-shell,
  html[data-raya-shell-ready="true"] .raya-course-map,
  html[data-raya-shell-ready="true"] .raya-rail-panel-body {
    transition: none;
  }
}
.raya-rail-panel-body-inner {
  min-height: 0;
  overflow: hidden;
}
.raya-rail-panel[data-raya-rail-panel-state="collapsed"] .raya-rail-panel-body {
  grid-template-rows: 0fr;
  margin-top: 0;
  opacity: 0;
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
.raya-article-sequence-cards {
  border-top: 1px solid var(--raya-color-border);
  display: grid;
  gap: 0.9rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 2rem;
  padding-top: 1rem;
}
.raya-sequence-card {
  background: color-mix(in srgb, var(--raya-color-surface) 88%, var(--raya-color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 70%, var(--raya-color-accent));
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  display: grid;
  gap: 0.35rem;
  min-width: 0;
  padding: 0.9rem 1rem;
  text-decoration: none;
}
.raya-sequence-card:hover {
  border-color: var(--raya-color-accent);
  box-shadow: 0 0.5rem 1.25rem rgba(31, 35, 40, 0.12);
  text-decoration: none;
}
.raya-sequence-card:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
.raya-sequence-card-next {
  text-align: right;
}
.raya-sequence-card-kicker {
  color: var(--raya-color-muted);
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}
.raya-sequence-card-title {
  color: var(--raya-color-text);
  font-family: var(--raya-font-heading), var(--raya-font-body), -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 1.05rem;
  font-weight: 800;
  line-height: 1.25;
  overflow-wrap: anywhere;
}
.raya-sequence-card-meta {
  color: var(--raya-color-muted);
  font-size: 0.85rem;
}
.raya-course-map ol,
.raya-learning-rail ul {
  margin: 0;
  padding-left: 1.25rem;
}
.raya-rail-link-list {
  list-style: none;
  padding-left: 0;
}
.raya-rail-connection-summary {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin: 0 0 0.7rem;
}
.raya-rail-connection-summary span {
  background: color-mix(in srgb, var(--raya-color-accent-soft) 72%, var(--raya-color-surface));
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 42%, var(--raya-color-border));
  border-radius: 999px;
  color: var(--raya-color-text);
  display: inline-flex;
  font-size: 0.75rem;
  gap: 0.25rem;
  line-height: 1;
  padding: 0.32rem 0.5rem;
}
.raya-rail-connection-heading {
  align-items: center;
  display: flex;
  gap: 0.5rem;
  justify-content: space-between;
  margin: 0.75rem 0 0.35rem;
}
.raya-rail-connection-heading h3 {
  margin: 0;
}
.raya-rail-count {
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 999px;
  color: var(--raya-color-text);
  display: inline-flex;
  flex: 0 0 auto;
  font-size: 0.72rem;
  font-weight: 800;
  line-height: 1;
  padding: 0.2rem 0.42rem;
}
.raya-rail-link-row {
  align-items: baseline;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.5rem;
}
.raya-article-connections {
  background: color-mix(in srgb, var(--raya-color-surface) 94%, var(--raya-color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 44%, var(--raya-color-border));
  border-radius: 0.375rem;
  margin-top: 2rem;
  padding: 1rem;
}
.raya-article-connections-header {
  align-items: start;
  display: flex;
  gap: 1rem;
  justify-content: space-between;
}
.raya-article-connections-kicker {
  color: var(--raya-color-muted);
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  margin: 0 0 0.2rem;
  text-transform: uppercase;
}
.raya-article-connections h2,
.raya-article-connections h3 {
  margin: 0;
}
.raya-article-connections-graph,
.raya-article-connection-context {
  background: var(--raya-color-accent-soft);
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 55%, var(--raya-color-border));
  border-radius: 999px;
  color: var(--raya-color-text);
  display: inline-flex;
  font-size: 0.82rem;
  font-weight: 800;
  line-height: 1.1;
  padding: 0.45rem 0.65rem;
  text-decoration: none;
  white-space: nowrap;
}
.raya-article-connections-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin: 1rem 0;
}
.raya-article-connections-summary > span {
  align-items: center;
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 999px;
  display: inline-flex;
  font-size: 0.84rem;
  gap: 0.4rem;
  padding: 0.35rem 0.58rem;
}
.raya-article-connections-count {
  background: var(--raya-color-accent);
  border-radius: 999px;
  color: var(--raya-color-accent-text);
  display: inline-flex;
  font-size: 0.74rem;
  font-weight: 900;
  justify-content: center;
  line-height: 1;
  min-width: 1.35rem;
  padding: 0.25rem 0.38rem;
}
.raya-article-connections-grid {
  display: grid;
  gap: 0.85rem;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));
}
.raya-article-connections-section {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  padding: 0.85rem;
}
.raya-article-connections-section ul {
  display: grid;
  gap: 0.45rem;
  list-style: none;
  margin: 0.65rem 0 0;
  padding: 0;
}
.raya-connection-preview {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  min-width: 0;
}
.raya-connection-preview summary {
  cursor: pointer;
  font-weight: 800;
  line-height: 1.25;
  overflow-wrap: anywhere;
  padding: 0.45rem 0.55rem;
}
.raya-connection-preview summary:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 2px;
}
.raya-connection-preview[open] {
  border-color: color-mix(in srgb, var(--raya-color-accent) 52%, var(--raya-color-border));
}
.raya-connection-preview-body {
  border-top: 1px solid var(--raya-color-border);
  display: grid;
  gap: 0.55rem;
  padding: 0.6rem;
}
.raya-connection-preview-body p {
  margin: 0;
}
.raya-connection-preview-summary {
  color: var(--raya-color-muted);
  font-size: 0.9rem;
  line-height: 1.45;
}
.raya-connection-preview-status {
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 999px;
  color: var(--raya-color-text);
  display: inline-flex;
  font-size: 0.75rem;
  font-weight: 800;
  line-height: 1;
  padding: 0.28rem 0.5rem;
}
.raya-connection-preview-counts,
.raya-connection-preview-actions {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.raya-connection-preview-counts span {
  background: color-mix(in srgb, var(--raya-color-accent-soft) 65%, var(--raya-color-surface));
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 38%, var(--raya-color-border));
  border-radius: 999px;
  display: inline-flex;
  font-size: 0.75rem;
  gap: 0.25rem;
  line-height: 1;
  padding: 0.3rem 0.48rem;
}
.raya-connection-preview-open,
.raya-connection-preview-graph {
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 999px;
  color: var(--raya-color-text);
  display: inline-flex;
  font-size: 0.78rem;
  font-weight: 800;
  line-height: 1;
  padding: 0.35rem 0.52rem;
  text-decoration: none;
}
.raya-connection-preview-open:focus-visible,
.raya-connection-preview-graph:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 2px;
}
.raya-official-practice {
  border-top: 1px solid var(--raya-color-border);
  display: grid;
  gap: 1rem;
  margin-top: 2rem;
  padding-top: 1.5rem;
}
.raya-official-practice > h2 {
  margin-bottom: 0;
}
.raya-official-practice > p {
  color: var(--raya-color-muted);
  margin: 0;
}
.raya-official-object {
  background: color-mix(in srgb, var(--raya-color-surface) 92%, var(--raya-color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 70%, var(--raya-color-accent));
  border-left: 0.35rem solid var(--raya-color-accent);
  border-radius: 0.5rem;
  display: grid;
  gap: 0.75rem;
  padding: 1rem;
  scroll-margin-top: 32rem;
}
.raya-official-object-header {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}
.raya-official-kind,
.raya-official-authority {
  border-radius: 999px;
  display: inline-flex;
  font-size: 0.75rem;
  font-weight: 900;
  letter-spacing: 0;
  line-height: 1;
  padding: 0.35rem 0.55rem;
  text-transform: uppercase;
}
.raya-official-kind {
  background: var(--raya-color-accent);
  color: var(--raya-color-accent-text);
}
.raya-official-authority {
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  color: var(--raya-color-text);
}
.raya-official-prompt {
  font-weight: 800;
  margin: 0;
}
.raya-official-question {
  display: grid;
  gap: 0.65rem;
}
.raya-official-options,
.raya-official-answer-list {
  margin: 0;
  padding-left: 1.35rem;
}
.raya-official-options {
  display: grid;
  gap: 0.3rem;
}
.raya-official-reveal {
  background: color-mix(in srgb, var(--raya-color-accent-soft) 48%, var(--raya-color-surface));
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  padding: 0.55rem 0.75rem;
}
.raya-official-reveal summary {
  cursor: pointer;
  font-weight: 800;
}
.raya-official-reveal summary:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
.raya-official-reveal-body {
  margin-top: 0.55rem;
}
.raya-official-reveal-body > :first-child {
  margin-top: 0;
}
.raya-official-reveal-body > :last-child {
  margin-bottom: 0;
}
.raya-article-connection-item {
  border-top: 1px solid color-mix(in srgb, var(--raya-color-border) 70%, transparent);
  display: block;
  min-width: 0;
  padding-top: 0.45rem;
}
.raya-article-connection-title {
  min-width: 0;
}
.raya-article-connection-context {
  flex: 0 0 auto;
  font-size: 0.75rem;
  padding: 0.32rem 0.5rem;
}
.raya-rail-link-row > a:first-child {
  min-width: 0;
}
.raya-rail-context-link {
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 999px;
  color: var(--raya-color-text);
  display: inline-flex;
  font-size: 0.75rem;
  font-weight: 700;
  line-height: 1;
  padding: 0.2rem 0.45rem;
  text-decoration: none;
}
.raya-rail-context-link:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 2px;
}
.raya-course-map ol {
  list-style: none;
  padding-left: 0;
}
.raya-course-map [data-raya-map-children] {
  border-left: 1px solid var(--raya-color-border);
  margin-left: 0.7rem;
  padding-left: 0.65rem;
}
.raya-course-map-node[hidden],
.raya-course-map [data-raya-map-children][hidden],
.raya-map-filter-empty[hidden] {
  display: none;
}
.raya-course-map-node-row {
  align-items: start;
  display: grid;
  gap: 0.35rem;
  grid-template-columns: 1.25rem minmax(0, 1fr);
}
.raya-course-map-node-toggle,
.raya-course-map-node-spacer {
  aspect-ratio: 1;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 0.25rem;
  color: var(--raya-color-muted);
  display: grid;
  font: inherit;
  min-width: 0;
  padding: 0;
  place-items: center;
  width: 1.25rem;
}
.raya-course-map-node-toggle {
  cursor: pointer;
}
.raya-course-map-node-toggle::before {
  content: ">";
  font-size: 0.8rem;
  line-height: 1;
}
.raya-course-map-node-toggle[aria-expanded="true"]::before {
  content: "v";
}
.raya-course-map-node-toggle:focus-visible,
.raya-course-map-filter:focus-visible {
  outline: 2px solid var(--raya-color-accent);
  outline-offset: 2px;
}
.raya-course-map-filter-label {
  color: var(--raya-color-muted);
  display: block;
  font-size: 0.78rem;
  font-weight: 700;
  margin-bottom: 0.3rem;
}
.raya-course-map-filter {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  font: inherit;
  margin-bottom: 0.65rem;
  min-height: 2.25rem;
  padding: 0.35rem 0.55rem;
  width: 100%;
}
.raya-map-filter-empty {
  color: var(--raya-color-muted);
  font-size: 0.85rem;
  margin: 0 0 0.65rem;
}
.raya-course-map a {
  border-left: 3px solid transparent;
  align-items: center;
  display: flex;
  gap: 0.45rem;
  padding: 0.25rem 0 0.25rem 0.5rem;
  text-decoration: none;
}
.raya-course-map a::before {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-accent-soft) 74%, var(--raya-color-surface));
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 42%, var(--raya-color-border));
  border-radius: 999px;
  color: var(--raya-color-muted);
  content: attr(data-raya-map-index);
  display: inline-flex;
  flex: 0 0 auto;
  font-size: 0.7rem;
  font-weight: 900;
  justify-content: center;
  line-height: 1;
  min-width: 1.45rem;
  padding: 0.22rem 0.35rem;
}
.raya-course-map [data-raya-map-active="ancestor"] > .raya-course-map-node-row a {
  color: var(--raya-color-text);
  font-weight: 700;
}
.raya-course-map a[aria-current="page"] {
  border-left-color: var(--raya-color-success);
  color: var(--raya-color-success);
  font-weight: 700;
}
@media (max-width: 1500px) {
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-label {
    clip: rect(0 0 0 0);
    height: 1px;
    overflow: hidden;
    position: absolute;
    white-space: nowrap;
    width: 1px;
  }
}
@media (min-width: 1280px) {
  [data-raya-course-map="expanded"] .raya-learning-shell,
  .raya-learning-shell[data-raya-course-map="expanded"] {
    grid-template-columns: minmax(13.75rem, 13.75rem) minmax(42rem, 1fr) minmax(15rem, 15rem);
  }
  [data-raya-course-map="expanded"][data-raya-learning-rail="collapsed"] .raya-learning-shell,
  .raya-learning-shell[data-raya-course-map="expanded"][data-raya-learning-rail="collapsed"] {
    grid-template-columns: minmax(12rem, 15rem) minmax(48rem, 1fr) 3.25rem;
  }
  [data-raya-course-map="collapsed"] .raya-learning-shell,
  .raya-learning-shell[data-raya-course-map="collapsed"] {
    grid-template-columns: 4.5rem minmax(48rem, 1fr) minmax(15rem, 15rem);
  }
  [data-raya-course-map="collapsed"][data-raya-learning-rail="collapsed"] .raya-learning-shell,
  .raya-learning-shell[data-raya-course-map="collapsed"][data-raya-learning-rail="collapsed"] {
    grid-template-columns: 4.5rem minmax(48rem, 1fr) 3.25rem;
  }
  [data-raya-learning-rail="collapsed"] .raya-learning-rail,
  .raya-learning-rail[data-raya-learning-rail="collapsed"] {
    align-items: start;
    display: grid;
    justify-items: center;
    padding: 0.5rem;
  }
  [data-raya-learning-rail="collapsed"] .raya-learning-rail-header,
  [data-raya-learning-rail="collapsed"] .raya-learning-rail-body,
  .raya-learning-rail[data-raya-learning-rail="collapsed"] .raya-learning-rail-header,
  .raya-learning-rail[data-raya-learning-rail="collapsed"] .raya-learning-rail-body {
    display: none;
  }
  [data-raya-learning-rail="collapsed"] .raya-learning-rail-expand,
  .raya-learning-rail[data-raya-learning-rail="collapsed"] .raya-learning-rail-expand {
    aspect-ratio: 1;
    display: inline-grid;
    font-size: 0;
    min-width: 0;
    overflow: hidden;
    padding: 0;
    place-items: center;
    width: 100%;
  }
  [data-raya-learning-rail="collapsed"] .raya-learning-rail-expand::after,
  .raya-learning-rail[data-raya-learning-rail="collapsed"] .raya-learning-rail-expand::after {
    content: "Info";
    font-size: 0.8125rem;
  }
  [data-raya-course-map="collapsed"] .raya-course-map,
  .raya-course-map[data-raya-course-map="collapsed"] {
    padding: 0.5rem;
  }
  [data-raya-course-map="collapsed"] .raya-course-map-header,
  .raya-course-map[data-raya-course-map="collapsed"] .raya-course-map-header {
    gap: 0.35rem;
  }
  [data-raya-course-map="collapsed"] .raya-course-map .raya-region-title,
  [data-raya-course-map="collapsed"] .raya-course-map .raya-page-position,
  .raya-course-map[data-raya-course-map="collapsed"] .raya-region-title,
  .raya-course-map[data-raya-course-map="collapsed"] .raya-page-position {
    clip: rect(0 0 0 0);
    clip-path: inset(50%);
    height: 1px;
    overflow: hidden;
    position: absolute;
    white-space: nowrap;
    width: 1px;
  }
  [data-raya-course-map="collapsed"] #raya-course-map .raya-course-map-toggle,
  .raya-course-map[data-raya-course-map="collapsed"] .raya-course-map-toggle {
    aspect-ratio: 1;
    overflow: hidden;
    padding: 0;
    position: relative;
    text-indent: 200%;
    white-space: nowrap;
    width: 100%;
  }
  [data-raya-course-map="collapsed"] #raya-course-map .raya-course-map-toggle::after,
  .raya-course-map[data-raya-course-map="collapsed"] .raya-course-map-toggle::after {
    content: "Map";
    display: grid;
    inset: 0;
    place-items: center;
    position: absolute;
    text-indent: 0;
  }
  [data-raya-course-map="collapsed"] .raya-course-map-list,
  .raya-course-map[data-raya-course-map="collapsed"] .raya-course-map-list {
    gap: 0.35rem;
  }
  [data-raya-course-map="collapsed"] .raya-course-map-filter-label,
  [data-raya-course-map="collapsed"] .raya-course-map-filter,
  [data-raya-course-map="collapsed"] .raya-map-filter-empty,
  .raya-course-map[data-raya-course-map="collapsed"] .raya-course-map-filter-label,
  .raya-course-map[data-raya-course-map="collapsed"] .raya-course-map-filter,
  .raya-course-map[data-raya-course-map="collapsed"] .raya-map-filter-empty {
    display: none;
  }
  [data-raya-course-map="collapsed"] .raya-course-map ol,
  .raya-course-map[data-raya-course-map="collapsed"] ol {
    display: grid;
    gap: 0.35rem;
    list-style: none;
    padding-left: 0;
  }
  [data-raya-course-map="collapsed"] .raya-course-map [data-raya-map-children],
  .raya-course-map[data-raya-course-map="collapsed"] [data-raya-map-children] {
    border-left: 0;
    margin-left: 0;
    padding-left: 0;
  }
  [data-raya-course-map="collapsed"] .raya-course-map [data-raya-map-children][hidden],
  .raya-course-map[data-raya-course-map="collapsed"] [data-raya-map-children][hidden] {
    display: none;
  }
  [data-raya-course-map="collapsed"] .raya-course-map li,
  .raya-course-map[data-raya-course-map="collapsed"] li {
    margin: 0;
  }
  [data-raya-course-map="collapsed"] .raya-course-map-node-row,
  .raya-course-map[data-raya-course-map="collapsed"] .raya-course-map-node-row {
    gap: 0;
    grid-template-columns: minmax(0, 1fr);
  }
  [data-raya-course-map="collapsed"] .raya-course-map-node-toggle,
  [data-raya-course-map="collapsed"] .raya-course-map-node-spacer,
  .raya-course-map[data-raya-course-map="collapsed"] .raya-course-map-node-toggle,
  .raya-course-map[data-raya-course-map="collapsed"] .raya-course-map-node-spacer {
    display: none;
  }
  [data-raya-course-map="collapsed"] .raya-course-map a,
  .raya-course-map[data-raya-course-map="collapsed"] a {
    aspect-ratio: 1;
    border: 1px solid var(--raya-color-border);
    border-left-width: 1px;
    border-radius: 0.375rem;
    color: transparent;
    display: grid;
    overflow: hidden;
    padding: 0;
    place-items: center;
    position: relative;
    text-indent: 200%;
    white-space: nowrap;
    width: 100%;
  }
  [data-raya-course-map="collapsed"] .raya-course-map a::before,
  .raya-course-map[data-raya-course-map="collapsed"] a::before {
    display: none;
  }
  [data-raya-course-map="collapsed"] .raya-course-map a::after,
  .raya-course-map[data-raya-course-map="collapsed"] a::after {
    color: var(--raya-color-accent);
    content: attr(data-raya-map-index);
    display: grid;
    font-weight: 700;
    inset: 0;
    place-items: center;
    position: absolute;
    text-indent: 0;
  }
  [data-raya-course-map="collapsed"] .raya-course-map a[aria-current="page"],
  .raya-course-map[data-raya-course-map="collapsed"] a[aria-current="page"] {
    border-color: var(--raya-color-success);
  }
  [data-raya-course-map="collapsed"] .raya-course-map a[aria-current="page"]::after,
  .raya-course-map[data-raya-course-map="collapsed"] a[aria-current="page"]::after {
    color: var(--raya-color-success);
  }
}
.raya-breadcrumbs {
  color: var(--raya-color-muted);
  font-size: 0.875rem;
  margin-bottom: 0.85rem;
  max-width: 100%;
}
.raya-breadcrumbs-list {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  list-style: none;
  margin: 0;
  min-width: 0;
  padding: 0;
}
.raya-breadcrumbs li {
  min-width: 0;
}
.raya-breadcrumb-home,
.raya-breadcrumb-link,
.raya-breadcrumb-current {
  border-radius: 0.25rem;
  display: inline-block;
  max-width: min(18rem, 70vw);
  overflow: hidden;
  padding: 0.1rem 0.2rem;
  text-overflow: ellipsis;
  vertical-align: bottom;
  white-space: nowrap;
}
.raya-breadcrumb-home,
.raya-breadcrumb-link {
  color: var(--raya-color-link);
  font-weight: 700;
  text-decoration-thickness: 0.08em;
}
.raya-breadcrumb-home:hover,
.raya-breadcrumb-link:hover {
  color: var(--raya-color-success);
}
.raya-breadcrumb-current {
  color: var(--raya-color-text);
  font-weight: 800;
}
.raya-breadcrumb-separator {
  color: var(--raya-color-muted);
  font-weight: 800;
}
.raya-page-brief {
  background: color-mix(in srgb, var(--raya-color-surface) 92%, var(--raya-color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 42%, var(--raya-color-border));
  border-radius: 0.5rem;
  box-shadow: 0 0.75rem 1.75rem rgba(31, 35, 40, 0.08);
  display: grid;
  gap: 0.75rem;
  margin: 0 0 1.35rem;
  padding: 1rem;
}
.raya-page-brief-heading {
  display: grid;
  gap: 0.15rem;
}
.raya-page-brief-kicker {
  color: var(--raya-color-muted);
  font-size: 0.74rem;
  font-weight: 850;
  line-height: 1;
  margin: 0;
  text-transform: uppercase;
}
.raya-page-brief h2 {
  font-size: 1.15rem;
  line-height: 1.2;
  margin: 0;
}
.raya-page-brief-summary {
  color: var(--raya-color-text);
  font-size: 0.98rem;
  margin: 0;
}
.raya-page-brief-facts {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  list-style: none;
  margin: 0;
  padding: 0;
}
.raya-page-brief-fact {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-surface) 82%, var(--raya-color-page));
  border: 1px solid var(--raya-color-border);
  border-radius: 999px;
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  max-width: 100%;
  min-width: 0;
  padding: 0.35rem 0.55rem;
}
.raya-page-brief-label {
  color: var(--raya-color-muted);
  font-size: 0.72rem;
  font-weight: 850;
  line-height: 1;
  text-transform: uppercase;
}
.raya-page-brief-value {
  color: var(--raya-color-text);
  font-size: 0.84rem;
  font-weight: 700;
  line-height: 1.2;
  min-width: 0;
  overflow-wrap: anywhere;
}
.raya-page-brief-value a {
  font-weight: 800;
}
.raya-page-brief-tag {
  display: inline-block;
}
.raya-main-article > :first-child,
.raya-inspection-main > :first-child {
  margin-top: 0;
}
.raya-main-article > * {
  max-width: 68rem;
}
.raya-main-article > .raya-article-sequence,
.raya-main-article > .raya-article-sequence-cards,
.raya-main-article > .raya-article-connections,
.raya-main-article > .raya-breadcrumbs,
.raya-main-article > .raya-page-brief,
.raya-main-article > .raya-numbered-object,
.raya-main-article > table,
.raya-main-article > pre {
  max-width: 100%;
}
.raya-learning-rail {
  display: grid;
  gap: 0;
}
.raya-rail-panel {
  border-bottom: 1px solid var(--raya-color-border);
  padding: 0.875rem 0;
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
.raya-section-landing {
  margin: 2rem 0;
}
.raya-section-card-list {
  display: grid;
  gap: 0.875rem;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));
  list-style: none;
  margin: 1rem 0 0;
  padding: 0;
}
.raya-section-card {
  margin: 0;
}
.raya-section-card-link {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  display: grid;
  gap: 0.45rem;
  min-height: 100%;
  padding: 1rem;
  text-decoration: none;
}
.raya-section-card-link:hover {
  border-color: var(--raya-color-accent);
  color: var(--raya-color-text);
}
.raya-section-card-link:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
.raya-section-card-title {
  color: var(--raya-color-accent);
  font-weight: 800;
  line-height: 1.25;
}
.raya-section-card-summary {
  color: var(--raya-color-muted);
  font-size: 0.95rem;
}
.raya-section-card-meta {
  color: var(--raya-color-muted);
  font-size: 0.8125rem;
  font-weight: 700;
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
.raya-page-toc a[aria-current="location"] {
  color: var(--raya-color-success);
  font-weight: 700;
}
.raya-code-block {
  margin: 1rem 0;
}
.raya-code-header {
  align-items: stretch;
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-bottom: 0;
  display: flex;
  justify-content: space-between;
  min-height: 2.25rem;
}
.raya-code-label {
  align-items: center;
  background: var(--raya-color-text);
  color: var(--raya-color-page);
  display: inline-flex;
  font-family: var(--raya-font-mono), ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 0.8125rem;
  font-weight: 700;
  padding: 0.25rem 0.5rem;
}
.raya-code-copy {
  background: var(--raya-color-accent-soft);
  border: 0;
  border-left: 1px solid var(--raya-color-border);
  color: var(--raya-color-text);
  cursor: pointer;
  font: inherit;
  font-size: 0.8125rem;
  font-weight: 700;
  padding: 0.25rem 0.75rem;
}
.raya-code-copy:hover {
  background: var(--raya-color-accent);
  color: var(--raya-color-page);
}
.raya-code-copy:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 2px;
}
.raya-code-copy[data-raya-copy-state="failed"] {
  background: var(--raya-color-danger);
  color: var(--raya-color-page);
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
.raya-static-environment > summary.raya-static-environment-heading {
  cursor: pointer;
  list-style-position: inside;
}
.raya-static-environment > summary.raya-static-environment-heading:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: -3px;
}
.raya-static-environment:not([open]) > summary.raya-static-environment-heading {
  border-bottom: 0;
}
.raya-static-environment:not([open]) > .raya-static-environment-body {
  display: none;
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
@media (max-width: 1279px) {
  .raya-learning-shell {
    grid-template-areas: "course-map main-article learning-rail";
    grid-template-columns: minmax(13.75rem, 16rem) minmax(0, 1fr) minmax(16rem, 18rem);
  }
  .raya-graph-workspace,
  [data-raya-graph-list-state="collapsed"] .raya-graph-workspace,
  [data-raya-graph-inspector-state="collapsed"] .raya-graph-workspace,
  [data-raya-graph-list-state="collapsed"][data-raya-graph-inspector-state="collapsed"] .raya-graph-workspace,
  [data-raya-graph-expanded="true"] .raya-graph-workspace {
    grid-template-columns: minmax(0, 1fr);
  }
  .raya-search-workspace,
  .raya-practice-workspace {
    grid-template-columns: minmax(0, 1fr);
  }
  .raya-search-control-panel,
  .raya-search-context-panel,
  .raya-practice-control-panel,
  .raya-practice-context-panel {
    position: static;
  }
  [data-raya-graph-list-state="collapsed"] .raya-graph-list-panel h2,
  [data-raya-graph-inspector-state="collapsed"] .raya-graph-inspector-panel h2 {
    writing-mode: horizontal-tb;
  }
}
@media (max-width: 1279px) {
  .raya-learning-shell {
    grid-template-areas:
      "main-article"
      "course-map"
      "learning-rail";
    grid-template-columns: minmax(0, 1fr);
  }
  .raya-course-map,
  .raya-learning-rail {
    margin-bottom: 1rem;
    max-height: 16rem;
    overflow: auto;
    position: static;
  }
  [data-raya-course-map="collapsed"] .raya-course-map {
    max-height: 5.5rem;
  }
  [data-raya-course-map="expanded"] .raya-course-map {
    max-height: 70vh;
  }
  .raya-course-map .raya-course-map-toggle {
    display: none;
  }
  .raya-learning-rail-collapse,
  .raya-learning-rail-expand {
    display: none;
  }
  .raya-learning-rail {
    margin-top: 1rem;
  }
  .raya-graph-canvas {
    min-height: 24rem;
  }
  .raya-graph-detail-links {
    grid-template-columns: 1fr;
  }
  .raya-graph-list {
    columns: 1;
  }
  .raya-article-sequence-cards {
    grid-template-columns: 1fr;
  }
  .raya-sequence-card-next {
    text-align: left;
  }
}
@media (max-width: 520px) {
  .raya-top-command-bar-inner,
  .raya-learning-shell,
  .raya-page-footer,
  .raya-inspection-main,
  .raya-graph-page,
  .raya-search-page,
  .raya-practice-page {
    padding: 0.75rem;
  }
  .raya-top-command-bar-inner {
    align-items: stretch;
    display: grid;
  }
  .raya-reading-context {
    display: grid;
    gap: 0.4rem;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context {
    align-items: center;
    display: flex;
    gap: 0.35rem 0.5rem;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context-separator {
    display: none;
  }
  .raya-reading-context-course,
  .raya-reading-context-page {
    white-space: normal;
  }
  .raya-reading-context-sequence {
    flex-wrap: wrap;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-course-tools {
    flex-wrap: nowrap;
    justify-content: flex-start;
    overflow-x: auto;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command {
    min-width: 2.5rem;
    padding: 0.45rem;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-label {
    clip: rect(0 0 0 0);
    height: 1px;
    overflow: hidden;
    position: absolute;
    white-space: nowrap;
    width: 1px;
  }
  .raya-discovery-command-bar .raya-top-command-bar-inner {
    gap: 0.5rem;
  }
  .raya-discovery-command-bar .raya-reading-context {
    display: flex;
    flex-wrap: nowrap;
  }
  .raya-discovery-command-bar .raya-reading-context-course,
  .raya-discovery-command-bar .raya-reading-context-page {
    white-space: nowrap;
  }
  .raya-discovery-command-bar .raya-course-tools {
    flex-wrap: nowrap;
    justify-content: flex-start;
    overflow-x: auto;
  }
  .raya-discovery-command-bar .raya-command {
    min-width: 2.5rem;
    padding: 0.45rem;
  }
  .raya-discovery-command-bar .raya-command-label {
    clip: rect(0 0 0 0);
    height: 1px;
    overflow: hidden;
    position: absolute;
    white-space: nowrap;
    width: 1px;
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
@media print {
  *,
  *::before,
  *::after {
    box-shadow: none !important;
    text-shadow: none !important;
  }
  html {
    background: #fff !important;
    color: #000 !important;
    font-size: 11pt;
    scroll-padding-top: 0;
  }
  body {
    background: #fff !important;
    color: #000 !important;
    margin: 0;
  }
  .raya-skip-link,
  .raya-top-command-bar,
  .raya-course-map,
  .raya-learning-rail,
  .raya-graph-controls,
  .raya-graph-groups,
  .raya-graph-status,
  .raya-graph-hover-status,
  .raya-graph-instructions,
  .raya-graph-inspector-panel,
  .raya-graph-canvas,
  .raya-graph-panel-header button,
  .raya-search-controls,
  .raya-search-control-panel,
  .raya-search-context-panel,
  .raya-practice-controls,
  .raya-practice-control-panel,
  .raya-practice-context-panel,
  .raya-inspection-sidebar,
  .raya-code-copy {
    display: none !important;
  }
  .raya-learning-shell,
  .raya-graph-workspace,
  .raya-search-workspace,
  .raya-practice-workspace {
    display: block !important;
  }
  .raya-graph-page,
  .raya-search-page,
  .raya-practice-page,
  .raya-graph-list-panel,
  .raya-main-article,
  .raya-inspection-main {
    background: #fff !important;
    border: 0 !important;
    color: #000 !important;
    display: block !important;
    margin: 0 !important;
    max-width: none !important;
    padding: 0 !important;
    width: auto !important;
  }
  .raya-main-article {
    font-size: 11pt;
    line-height: 1.45;
  }
  .raya-main-article a,
  .raya-search-results a,
  .raya-practice-results a,
  .raya-graph-list a {
    color: #000 !important;
    text-decoration: underline;
  }
  .raya-main-article a[href^="http"]::after,
  .raya-search-results a[href^="http"]::after,
  .raya-practice-results a[href^="http"]::after {
    content: " (" attr(href) ")";
    font-size: 0.85em;
    overflow-wrap: anywhere;
  }
  .raya-breadcrumbs,
  .raya-article-sequence,
  .raya-article-sequence-cards,
  .raya-page-brief,
  .raya-article-connections,
  .raya-official-practice,
  .raya-numbered-object,
  .raya-proof,
  .raya-static-environment,
  .raya-callout,
  figure,
  table,
  pre,
  blockquote,
  mjx-container {
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .raya-page-brief,
  .raya-article-connections,
  .raya-official-practice,
  .raya-numbered-object,
  .raya-proof,
  .raya-static-environment,
  .raya-callout {
    background: #fff !important;
    border-color: #888 !important;
  }
  .raya-page-toc {
    border: 1px solid #999;
  }
  .raya-graph-panel-body[aria-hidden="true"] {
    display: block !important;
  }
  [data-raya-graph-list-state="collapsed"] .raya-graph-list-panel h2 {
    writing-mode: horizontal-tb;
  }
  .raya-static-environment:not([open]) > .raya-static-environment-body {
    display: block !important;
  }
  .raya-static-environment:not([open]) > summary.raya-static-environment-heading {
    border-bottom: 1px solid #999;
  }
  .raya-static-environment-heading,
  .raya-numbered-object-heading,
  .raya-proof-heading {
    background: #f7f7f7 !important;
    border-color: #999 !important;
    color: #000 !important;
  }
  table {
    border-collapse: collapse;
    width: 100%;
  }
  th,
  td {
    border-color: #999 !important;
  }
  pre,
  code,
  .highlight {
    background: #fff !important;
    color: #000 !important;
    white-space: pre-wrap;
  }
  pre,
  .math.block,
  .raya-numbered-object-body,
  .raya-proof-body,
  .raya-static-environment-body {
    overflow: visible !important;
  }
  img,
  svg {
    max-width: 100% !important;
  }
  h1,
  h2,
  h3 {
    break-after: avoid;
    page-break-after: avoid;
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
                f'<details{id_html} class="raya-static-environment '
                f'raya-static-environment--{escaped_kind}">'
            ),
            '<summary class="raya-static-environment-heading">',
            f'<span class="raya-static-environment-reference">{html.escape(reference)}</span>'
            + (f" {title_html}" if title_html else ""),
            "</summary>",
            '<div class="raya-static-environment-body">',
            body,
            "</div>",
            "</details>",
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
