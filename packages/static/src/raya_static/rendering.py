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
from raya_schema.wikilinks import render_wikilinks_as_markdown

from raya_static.math_renderer import MathItem, MathRenderer
from raya_static.numbered_objects import (
    NumberedObjectRenderContext,
    NumberedObjectRenderItem,
    expand_shorthand_references,
)
from raya_static.proofs import StaticEnvironmentRenderContext, StaticEnvironmentRenderItem
from raya_static.shell_geometry import apply_rail_geometry_tokens


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
_INSPECTABLE_IMAGE_EXTENSIONS = {
    ".apng",
    ".avif",
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".svg",
    ".webp",
}


@dataclass(frozen=True)
class _Heading:
    level: int
    title: str
    anchor: str


@dataclass(frozen=True)
class _Callout:
    kind: str
    body: str


def _is_inspectable_local_image_src(src: str) -> bool:
    lowered = src.lower().split("#", 1)[0].split("?", 1)[0]
    if lowered.startswith(("http://", "https://", "//", "data:", "mailto:", "tel:")):
        return False
    return "_raya/assets/" in lowered and any(
        lowered.endswith(extension) for extension in _INSPECTABLE_IMAGE_EXTENSIONS
    )


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
        resolve_wikilink: Callable[[str], str | None] | None = None,
    ) -> None:
        self._resolve_href = resolve_href
        self._source_path = source_path
        self._report = report
        self._math_renderer = math_renderer
        self._resolve_wikilink = resolve_wikilink
        self._md = MarkdownIt("commonmark", {"html": False})
        self._md.enable("table")
        self._md.use(footnote_plugin)
        self._md.use(dollarmath_plugin)
        self._default_image_renderer = self._md.renderer.rules.get("image")
        self._md.renderer.rules["heading_open"] = self._render_heading_open
        self._md.renderer.rules["link_open"] = self._render_link_open
        self._md.renderer.rules["link_close"] = self._render_link_close
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
        body = self._render_wikilinks(body)
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
            callout_tokens = self._md.parse(
                self._render_wikilinks(callout.body),
                callout_env,
            )
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
                object_body = self._render_wikilinks(object_body)
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
                proof_body = self._render_wikilinks(proof_body)
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

    def _render_wikilinks(self, body: str) -> str:
        if self._resolve_wikilink is None:
            return body
        return render_wikilinks_as_markdown(
            body,
            resolve_target=self._resolve_wikilink,
        )

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
        env["raya_link_depth"] = int(env.get("raya_link_depth", 0)) + 1
        href = tokens[idx].attrGet("href")
        if href:
            tokens[idx].attrSet("href", self._resolve_href(href))
        return self._md.renderer.renderToken(tokens, idx, options, env)

    def _render_link_close(
        self,
        tokens: list[Token],
        idx: int,
        options: dict,
        env: dict,
    ) -> str:
        rendered = self._md.renderer.renderToken(tokens, idx, options, env)
        env["raya_link_depth"] = max(0, int(env.get("raya_link_depth", 0)) - 1)
        return rendered

    def _render_image(
        self,
        tokens: list[Token],
        idx: int,
        options: dict,
        env: dict,
    ) -> str:
        src = tokens[idx].attrGet("src")
        if src:
            src = self._resolve_href(src)
            tokens[idx].attrSet("src", src)
        if self._default_image_renderer is not None:
            image_html = self._default_image_renderer(tokens, idx, options, env)
        else:
            image_html = self._md.renderer.renderToken(tokens, idx, options, env)
        if (
            not src
            or env.get("raya_link_depth", 0)
            or not _is_inspectable_local_image_src(src)
        ):
            return image_html
        alt = tokens[idx].content.strip() or "Local image asset"
        escaped_alt = html.escape(alt, quote=True)
        escaped_src = html.escape(src, quote=True)
        return (
            '<span class="raya-local-asset-image" data-raya-local-asset-image>'
            f"{image_html}"
            '<button class="raya-local-asset-inspect" type="button" '
            'data-raya-asset-inspect aria-haspopup="dialog" '
            f'data-raya-asset-src="{escaped_src}" '
            f'data-raya-asset-alt="{escaped_alt}" '
            f'aria-label="Inspect image: {escaped_alt}">'
            "Inspect"
            "</button>"
            "</span>"
        )

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
    resolve_wikilink: Callable[[str], str | None] | None = None,
) -> str:
    return RichMarkdownRenderer(
        resolve_href,
        source_path=source_path,
        report=report,
        math_renderer=math_renderer,
        resolve_wikilink=resolve_wikilink,
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
.raya-local-asset-image {
  display: inline-grid;
  gap: 0.35rem;
  justify-items: start;
  max-width: 100%;
}
.raya-local-asset-inspect {
  background: color-mix(in srgb, var(--raya-color-accent-soft) 72%, var(--raya-color-surface));
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  cursor: pointer;
  font: inherit;
  font-size: 0.78rem;
  font-weight: 850;
  line-height: 1.1;
  padding: 0.28rem 0.5rem;
}
.raya-local-asset-inspect:hover,
.raya-local-asset-inspect:focus-visible {
  background: var(--raya-color-accent);
  color: var(--raya-color-page);
}
.raya-asset-inspector[hidden] {
  display: none;
}
.raya-asset-inspector {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-text) 62%, transparent);
  display: grid;
  inset: 0;
  justify-items: center;
  padding: 1.25rem;
  position: fixed;
  z-index: 80;
}
.raya-asset-inspector-panel {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.5rem;
  box-shadow: 0 1rem 2.5rem color-mix(in srgb, var(--raya-color-text) 28%, transparent);
  display: grid;
  gap: 0.75rem;
  max-height: min(88vh, 56rem);
  max-width: min(92vw, 68rem);
  overflow: auto;
  padding: 0.85rem;
  width: 100%;
}
.raya-asset-inspector-header {
  align-items: center;
  border-bottom: 1px solid var(--raya-color-border);
  display: flex;
  gap: 0.75rem;
  justify-content: space-between;
  padding-bottom: 0.65rem;
}
.raya-asset-inspector-header h2 {
  font-size: 1rem;
  line-height: 1.2;
  margin: 0;
}
.raya-asset-inspector-close {
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  cursor: pointer;
  font: inherit;
  font-size: 0.82rem;
  font-weight: 850;
  padding: 0.35rem 0.55rem;
}
.raya-asset-inspector-close:hover,
.raya-asset-inspector-close:focus-visible {
  background: var(--raya-color-accent);
  color: var(--raya-color-page);
}
.raya-asset-inspector-figure {
  display: grid;
  justify-items: center;
  margin: 0;
  min-height: 0;
}
.raya-asset-inspector-figure img {
  max-height: 68vh;
  object-fit: contain;
  width: auto;
}
.raya-asset-inspector-actions {
  margin: 0;
}
.raya-visually-hidden {
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  height: 1px;
  overflow: hidden;
  position: absolute;
  white-space: nowrap;
  width: 1px;
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
.raya-mobile-course-map-open.raya-command {
  display: none;
}
.raya-top-command-bar {
  background: var(--raya-color-text);
  backdrop-filter: blur(18px);
  border-bottom: 1px solid color-mix(in srgb, var(--raya-color-text) 72%, var(--raya-color-accent));
  color: var(--raya-color-surface);
  gap: 0.55rem;
  position: sticky;
  top: 0;
  z-index: 5;
}
.raya-discovery-command-bar {
  box-shadow: 0 0.75rem 2rem color-mix(in srgb, var(--raya-color-text) 18%, transparent);
}
.raya-discovery-command-bar .raya-command[aria-current="page"] {
  background: var(--raya-color-surface);
  border-color: var(--raya-color-accent);
  box-shadow: inset 0 -0.18rem 0 var(--raya-color-accent), 0 0 0 1px var(--raya-color-accent);
  color: var(--raya-color-text);
}
.raya-discovery-command-bar .raya-command[aria-current="page"] .raya-command-icon {
  color: inherit;
}
.raya-discovery-command-bar .raya-course-tools {
  min-width: 0;
  overflow-x: auto;
  overflow-y: hidden;
}
.raya-discovery-command-bar .raya-command {
  flex: 0 0 auto;
  overflow-wrap: normal;
  white-space: nowrap;
}
.raya-discovery-command-bar .raya-command-label {
  overflow-wrap: normal;
  white-space: nowrap;
}
@media (max-width: 1100px) {
  .raya-discovery-command-bar .raya-command-label {
    clip: rect(0 0 0 0);
    height: 1px;
    overflow: hidden;
    position: absolute;
    width: 1px;
  }
}
.raya-top-command-bar-inner,
.raya-learning-shell,
.raya-page-footer,
.raya-inspection-main {
  margin: 0 auto;
  max-width: 110rem;
  padding: var(--raya-space-page);
}
.raya-top-command-bar-inner,
.raya-learning-shell {
  max-width: 128rem;
}
.raya-top-command-bar-inner {
  align-items: center;
  display: flex;
  gap: 0.55rem;
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
  align-items: center;
  background: var(--raya-color-accent-soft);
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 58%, var(--raya-color-border));
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  display: inline-flex;
  gap: 0.32rem;
  font-size: 0.75rem;
  font-weight: 800;
  line-height: 1;
  max-width: min(18rem, 38vw);
  min-height: 1.9rem;
  min-width: 0;
  padding: 0.35rem 0.5rem;
  text-decoration: none;
}
.raya-reading-context-section {
  flex: 0 1 auto;
}
.raya-reading-context-section-kicker {
  flex: 0 0 auto;
  text-transform: uppercase;
}
.raya-reading-context-section-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  gap: 0.4rem;
  justify-content: flex-end;
  min-width: 0;
}
.raya-command-group {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-surface) 82%, var(--raya-color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 76%, transparent);
  border-radius: 0.55rem;
  display: flex;
  flex: 0 1 auto;
  flex-wrap: nowrap;
  gap: 0.3rem;
  min-width: 0;
  padding: 0.2rem;
}
.raya-command-group-discovery {
  flex: 1 1 auto;
}
.raya-command-group-layout,
.raya-command-group-comfort {
  flex: 0 0 auto;
}
.raya-command-search-form {
  align-items: center;
  flex: 0 1 14rem;
  display: flex;
  gap: 0.35rem;
  min-width: 10rem;
}
.raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-search-form + .raya-command-search {
  display: none;
}
.raya-command-search-input {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  box-sizing: border-box;
  color: var(--raya-color-text);
  flex: 1 1 auto;
  font: inherit;
  height: 2.5rem;
  line-height: 1.2;
  min-width: 0;
  padding: 0.45rem 0.6rem;
}
.raya-command-search-submit {
  align-items: center;
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  box-sizing: border-box;
  color: var(--raya-color-text);
  cursor: pointer;
  display: inline-flex;
  flex: 0 0 auto;
  font: inherit;
  font-weight: 800;
  justify-content: center;
  line-height: 1.2;
  height: 2.5rem;
  min-height: 2.5rem;
  min-width: 3rem;
  padding: 0.45rem 0.65rem;
  white-space: nowrap;
}
.raya-command-search-submit span {
  white-space: nowrap;
}
.raya-command-search-input:focus-visible,
.raya-command-search-submit:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 2px;
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
  min-height: 2.35rem;
  min-width: 2.75rem;
  padding: 0.45rem 0.65rem;
  text-decoration: none;
}
.raya-command::before {
  content: none;
  display: none;
}
.raya-command-icon {
  background: color-mix(in srgb, var(--raya-color-accent) 16%, transparent);
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 56%, transparent);
  border-radius: 0.3rem;
  box-sizing: border-box;
  color: currentColor;
  fill: none;
  flex: 0 0 auto;
  height: 1.5rem;
  padding: 0.18rem;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
  width: 1.5rem;
}
.raya-command-icon-text {
  fill: currentColor;
  font-family: var(--raya-font-heading), var(--raya-font-body), -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 0.5rem;
  font-weight: 900;
  letter-spacing: 0;
  stroke: none;
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
.raya-graph-page {
  padding-top: 0.35rem;
}
.raya-graph-header {
  align-items: baseline;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 1rem;
  max-width: none;
}
.raya-graph-header h1 {
  margin: 0;
}
.raya-graph-header p {
  color: var(--raya-color-muted);
  flex: 1 1 24rem;
  font-size: 0.95rem;
  margin: 0;
}
.raya-graph-controls.raya-graph-toolbar,
.raya-graph-instructions {
  margin-bottom: 0.35rem;
}
.raya-graph-instructions {
  color: var(--raya-color-muted);
  font-size: 0.88rem;
  line-height: 1.35;
}
.raya-graph-orientation {
  background: color-mix(
    in srgb,
    var(--raya-color-surface) 88%,
    var(--raya-color-accent) 12%
  );
  border: 1px solid var(--raya-color-border);
  border-radius: 0.5rem;
  display: grid;
  font-size: 0.84rem;
  gap: 0.22rem 0.6rem;
  margin-bottom: 0.35rem;
  padding: 0.28rem 0.46rem;
}
.raya-graph-status {
  margin: 0 0 0.45rem;
  pointer-events: none;
}
.raya-graph-arrangement-status {
  background: color-mix(in srgb, var(--raya-color-warning-soft) 70%, var(--raya-color-surface));
  border: 1px solid color-mix(in srgb, var(--raya-color-warning) 44%, var(--raya-color-border));
  border-left: 0.25rem solid var(--raya-color-warning);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  font-size: 0.86rem;
  font-weight: 750;
  margin: 0 0 0.65rem;
  padding: 0.5rem 0.65rem;
}
.raya-graph-arrangement-status[hidden] {
  display: none;
}
.raya-graph-orientation-main {
  align-items: baseline;
  display: flex;
  flex-wrap: wrap;
  gap: 0.16rem 0.65rem;
  justify-content: space-between;
}
.raya-graph-orientation-counts,
.raya-graph-orientation-selection {
  margin: 0;
}
.raya-graph-orientation-meta {
  display: grid;
  gap: 0.14rem 0.45rem;
  grid-template-columns: repeat(auto-fit, minmax(5.75rem, 1fr));
  margin: 0;
}
.raya-graph-orientation-meta div {
  min-width: 0;
}
.raya-graph-orientation-meta dt {
  color: var(--raya-color-muted);
  font-size: 0.68rem;
  font-weight: 700;
  line-height: 1.1;
  text-transform: uppercase;
}
.raya-graph-orientation-meta dd {
  line-height: 1.15;
  margin: 0.02rem 0 0;
  overflow-wrap: anywhere;
}
.raya-graph-orientation-actions {
  display: flex;
  flex-wrap: nowrap;
  gap: 0.24rem;
  margin: 0;
  overflow-x: auto;
  scrollbar-gutter: stable;
}
.raya-graph-orientation-actions > * {
  flex: 0 0 auto;
  white-space: nowrap;
}
.raya-graph-reading-keys {
  display: grid;
  gap: 0.28rem;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin: 0 0 0.24rem;
}
.raya-graph-reading-keys article {
  align-items: baseline;
  background: color-mix(in srgb, var(--raya-color-surface) 88%, transparent);
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 84%, transparent);
  border-radius: 0.375rem;
  display: flex;
  gap: 0.22rem;
  min-width: 0;
  padding: 0.26rem 0.36rem;
}
.raya-graph-reading-keys h2 {
  color: var(--raya-color-heading);
  flex: 0 0 auto;
  font-size: 0.68rem;
  letter-spacing: 0;
  margin: 0;
}
.raya-graph-reading-keys p {
  color: var(--raya-color-muted);
  font-size: 0.65rem;
  line-height: 1.18;
  margin: 0;
  min-width: 0;
}
@media (max-width: 900px) {
  .raya-graph-reading-keys {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 520px) {
  .raya-graph-reading-keys {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
.raya-discovery-overview {
  background: color-mix(
    in srgb,
    var(--raya-color-surface) 88%,
    var(--raya-color-accent) 12%
  );
  border: 1px solid var(--raya-color-border);
  border-radius: 0.5rem;
  display: grid;
  gap: 0.45rem 0.65rem;
  margin: 0 0 0.65rem;
  padding: 0.55rem 0.65rem;
}
.raya-discovery-overview-main {
  display: grid;
  gap: 0.18rem;
}
.raya-discovery-overview-main h2 {
  font-size: 0.95rem;
  margin: 0;
}
.raya-discovery-overview-main p {
  color: var(--raya-color-muted);
  font-size: 0.82rem;
  line-height: 1.32;
  margin: 0;
}
.raya-discovery-overview-meta {
  display: grid;
  gap: 0.25rem 0.55rem;
  grid-template-columns: repeat(auto-fit, minmax(7rem, 1fr));
  margin: 0;
}
.raya-discovery-overview-meta div {
  min-width: 0;
}
.raya-discovery-overview-meta dt {
  color: var(--raya-color-muted);
  font-size: 0.64rem;
  font-weight: 800;
  line-height: 1.1;
  text-transform: uppercase;
}
.raya-discovery-overview-meta dd {
  font-size: 0.86rem;
  line-height: 1.18;
  margin: 0.03rem 0 0;
  overflow-wrap: anywhere;
}
.raya-discovery-overview-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}
.raya-discovery-overview-actions a {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-surface) 82%, var(--raya-color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 84%, var(--raya-color-accent));
  border-radius: 0.45rem;
  color: var(--raya-color-text);
  display: inline-flex;
  font-size: 0.82rem;
  font-weight: 800;
  min-height: 1.85rem;
  padding: 0.25rem 0.5rem;
  text-decoration: none;
}
.raya-discovery-overview-actions a:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
.raya-discovery-workspace-shell {
  align-items: start;
  display: grid;
  gap: 0.75rem;
  grid-template-columns: minmax(13rem, 16rem) minmax(0, 1fr);
  margin-top: var(--raya-space-block);
  min-width: 0;
}
.raya-discovery-course-rail {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.5rem;
  min-width: 0;
  padding: 0.75rem;
  position: sticky;
  top: calc(var(--raya-topbar-height, 4rem) + 1rem);
}
.raya-discovery-course-tab {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-surface) 86%, var(--raya-color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 82%, var(--raya-color-accent));
  border-radius: 0.45rem;
  color: var(--raya-color-text);
  display: inline-flex;
  font: inherit;
  font-weight: 800;
  justify-content: center;
  margin-bottom: 0.65rem;
  min-height: 2.5rem;
  padding: 0.45rem 0.55rem;
  width: 100%;
}
.raya-discovery-course-tab:focus-visible,
.raya-discovery-workspace-link:focus-visible,
.raya-discovery-course-page-link:focus-visible,
.raya-discovery-course-identity a:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
.raya-discovery-course-rail-body {
  display: grid;
  gap: 0.75rem;
  min-width: 0;
}
.raya-discovery-course-identity {
  display: grid;
  gap: 0.35rem;
  min-width: 0;
}
.raya-discovery-course-identity h2 {
  font-size: 0.95rem;
  line-height: 1.2;
  margin: 0;
  overflow-wrap: anywhere;
}
.raya-discovery-course-identity a {
  color: var(--raya-color-link);
  font-size: 0.86rem;
  font-weight: 800;
}
.raya-discovery-workspace-links {
  display: grid;
  gap: 0.35rem;
}
.raya-discovery-workspace-link {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-surface) 92%, var(--raya-color-accent-soft));
  border: 1px solid var(--raya-color-border);
  border-radius: 0.45rem;
  color: var(--raya-color-text);
  display: grid;
  gap: 0.2rem;
  grid-template-columns: minmax(0, 1fr) auto;
  min-height: 2.35rem;
  padding: 0.45rem 0.55rem;
  text-decoration: none;
}
.raya-discovery-workspace-link[data-raya-current-workspace-link="true"] {
  background: color-mix(in srgb, var(--raya-color-accent-soft) 78%, var(--raya-color-surface));
  border-color: color-mix(in srgb, var(--raya-color-accent) 52%, var(--raya-color-border));
  box-shadow: inset 0.22rem 0 0 var(--raya-color-accent);
}
.raya-discovery-workspace-link span {
  font-size: 0.88rem;
  font-weight: 850;
  overflow-wrap: anywhere;
}
.raya-discovery-workspace-link em {
  color: var(--raya-color-muted);
  font-size: 0.68rem;
  font-style: normal;
  font-weight: 800;
  text-transform: uppercase;
}
.raya-discovery-course-pages {
  border-top: 1px solid var(--raya-color-border);
  display: grid;
  gap: 0.45rem;
  min-width: 0;
  padding-top: 0.65rem;
}
.raya-discovery-rail-page-focus {
  background: color-mix(in srgb, var(--raya-color-surface) 86%, var(--raya-color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 82%, var(--raya-color-accent));
  border-radius: 0.45rem;
  display: grid;
  gap: 0.35rem;
  min-width: 0;
  padding: 0.55rem;
}
.raya-discovery-rail-page-focus[hidden] {
  display: none;
}
.raya-discovery-rail-page-focus h3 {
  color: var(--raya-color-muted);
  font-size: 0.7rem;
  letter-spacing: 0;
  line-height: 1.1;
  margin: 0;
  text-transform: uppercase;
}
.raya-discovery-rail-page-focus p {
  font-size: 0.82rem;
  font-weight: 800;
  line-height: 1.25;
  margin: 0;
  overflow-wrap: anywhere;
}
.raya-discovery-rail-page-handoffs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}
.raya-discovery-rail-page-handoffs a {
  border: 1px solid var(--raya-color-border);
  border-radius: 999px;
  color: var(--raya-color-link);
  font-size: 0.72rem;
  font-weight: 800;
  padding: 0.16rem 0.38rem;
  text-decoration: none;
}
.raya-discovery-course-pages h3 {
  color: var(--raya-color-muted);
  font-size: 0.74rem;
  letter-spacing: 0;
  line-height: 1.1;
  margin: 0;
  text-transform: uppercase;
}
.raya-discovery-course-pages ol {
  display: grid;
  gap: 0.2rem;
  list-style: none;
  margin: 0;
  max-height: min(42rem, calc(100vh - 22rem));
  overflow: auto;
  padding: 0;
}
.raya-discovery-course-page-link {
  align-items: baseline;
  border-radius: 0.35rem;
  color: var(--raya-color-text);
  display: grid;
  gap: 0.35rem;
  grid-template-columns: 2.8rem minmax(0, 1fr);
  padding: 0.35rem 0.4rem;
  text-decoration: none;
}
.raya-discovery-course-page-link:hover {
  background: color-mix(in srgb, var(--raya-color-surface) 82%, var(--raya-color-accent-soft));
}
.raya-discovery-course-page-link[data-raya-rail-page-focus="true"] {
  background: color-mix(in srgb, var(--raya-color-accent-soft) 72%, var(--raya-color-surface));
  box-shadow: inset 0.2rem 0 0 var(--raya-color-accent);
}
.raya-discovery-course-page-link span {
  color: var(--raya-color-muted);
  font-size: 0.72rem;
  font-weight: 800;
}
.raya-discovery-course-page-link strong {
  font-size: 0.82rem;
  line-height: 1.25;
  min-width: 0;
  overflow-wrap: anywhere;
}
[data-raya-discovery-rail-state="collapsed"] .raya-discovery-workspace-shell {
  grid-template-columns: minmax(4.5rem, 5.25rem) minmax(0, 1fr);
}
[data-raya-discovery-rail-state="collapsed"] .raya-discovery-course-rail {
  align-items: center;
  display: flex;
  justify-content: center;
}
[data-raya-discovery-rail-state="collapsed"] .raya-discovery-course-rail-body {
  display: none;
}
[data-raya-discovery-rail-state="collapsed"] .raya-discovery-course-tab {
  display: inline-flex;
  margin-bottom: 0;
  writing-mode: vertical-rl;
}
.raya-discovery-quick-guide {
  background: color-mix(in srgb, var(--raya-color-surface) 90%, var(--raya-color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 82%, var(--raya-color-accent));
  border-radius: 0.5rem;
  display: grid;
  gap: 0.55rem;
  margin: 0 0 0.75rem;
  padding: 0.45rem 0.65rem;
}
.raya-discovery-quick-guide summary {
  color: var(--raya-color-text);
  cursor: pointer;
  font-size: 0.92rem;
  font-weight: 800;
  line-height: 1.25;
  margin: 0;
}
.raya-discovery-quick-guide summary:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
.raya-discovery-guide-cards {
  display: grid;
  gap: 0.65rem;
  grid-template-columns: repeat(auto-fit, minmax(min(12rem, 100%), 1fr));
  margin-top: 0.55rem;
}
.raya-discovery-guide-card {
  background: color-mix(in srgb, var(--raya-color-surface) 88%, var(--raya-color-page));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 84%, transparent);
  border-radius: 0.45rem;
  display: grid;
  gap: 0.2rem;
  min-width: 0;
  padding: 0.65rem;
}
.raya-discovery-guide-card h3 {
  color: var(--raya-color-text);
  font-size: 0.9rem;
  margin: 0;
}
.raya-discovery-guide-card p {
  color: var(--raya-color-muted);
  font-size: 0.86rem;
  line-height: 1.35;
  margin: 0;
  overflow-wrap: anywhere;
}
.raya-graph-workspace {
  align-items: start;
  display: grid;
  gap: 0.75rem;
  grid-template-columns: minmax(16rem, 22rem) minmax(34rem, 1fr) minmax(18rem, 24rem);
  margin-top: 0.35rem;
}
.raya-discovery-workspace-shell > .raya-graph-workspace,
.raya-discovery-workspace-shell > .raya-search-workspace,
.raya-discovery-workspace-shell > .raya-practice-workspace,
.raya-discovery-workspace-shell > .raya-tasks-workspace,
.raya-discovery-workspace-shell > .raya-schedule-workspace {
  margin-top: 0;
  min-width: 0;
  width: 100%;
}
.raya-discovery-workspace-shell > .raya-graph-workspace {
  grid-template-columns: minmax(12rem, 15rem) minmax(28rem, 1fr) minmax(13rem, 16.25rem);
}
.raya-discovery-workspace-shell > .raya-search-workspace,
.raya-discovery-workspace-shell > .raya-practice-workspace,
.raya-discovery-workspace-shell > .raya-tasks-workspace,
.raya-discovery-workspace-shell > .raya-schedule-workspace {
  grid-template-columns: minmax(12rem, 15rem) minmax(0, 1fr) minmax(12rem, 15rem);
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
.raya-discovery-page-focus {
  background: color-mix(in srgb, var(--raya-color-accent) 10%, var(--raya-color-surface));
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 35%, var(--raya-color-border));
  border-radius: 0.55rem;
  color: var(--raya-color-text);
  font-size: 0.9rem;
  line-height: 1.45;
  margin: 0.65rem 0 0;
  padding: 0.6rem 0.7rem;
}
.raya-discovery-page-focus[hidden] {
  display: none;
}
.raya-discovery-focus-strip {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-surface) 88%, var(--raya-color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 82%, var(--raya-color-accent));
  border-radius: 0.5rem;
  display: flex;
  gap: 0.55rem;
  justify-content: space-between;
  margin: 0 0 0.85rem;
  min-width: 0;
  padding: 0.58rem 0.7rem;
}
.raya-discovery-focus-strip[hidden] {
  display: none;
}
.raya-discovery-focus-copy {
  flex: 1 1 auto;
  min-width: 0;
}
.raya-discovery-focus-kicker {
  color: var(--raya-color-muted);
  font-size: 0.72rem;
  font-weight: 900;
  letter-spacing: 0;
  margin: 0 0 0.15rem;
}
.raya-discovery-focus-strip h2 {
  font-size: 1rem;
  margin: 0;
  overflow-wrap: anywhere;
}
.raya-discovery-focus-actions {
  align-items: center;
  display: flex;
  flex-wrap: nowrap;
  gap: 0.45rem;
  justify-content: flex-end;
  max-width: 100%;
  min-width: 0;
  overflow-x: auto;
  padding-bottom: 0.1rem;
}
.raya-discovery-focus-actions a {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.35rem;
  color: var(--raya-color-text);
  font-size: 0.82rem;
  font-weight: 800;
  flex: 0 0 auto;
  line-height: 1.15;
  min-height: 2rem;
  padding: 0.42rem 0.55rem;
  text-decoration: none;
}
.raya-discovery-focus-actions a[aria-current="page"] {
  background: var(--raya-color-accent);
  border-color: var(--raya-color-accent);
  color: var(--raya-color-accent-contrast);
}
.raya-discovery-focus-actions a:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
.raya-graph-page .raya-discovery-focus-strip {
  align-items: start;
  display: grid;
  gap: 0.35rem;
  grid-template-columns: minmax(0, 1fr);
  margin-bottom: 0.35rem;
  padding: 0.38rem 0.5rem;
}
.raya-graph-page .raya-discovery-focus-strip[hidden] {
  display: none;
}
.raya-graph-page .raya-discovery-workspace-shell {
  margin-top: 0.35rem;
}
.raya-graph-page .raya-discovery-focus-copy {
  align-items: baseline;
  display: flex;
  gap: 0.45rem;
}
.raya-graph-page .raya-discovery-focus-kicker {
  flex: 0 0 auto;
  font-size: 0.66rem;
  line-height: 1;
  margin: 0;
}
.raya-graph-page .raya-discovery-focus-strip h2 {
  font-size: 0.9rem;
  line-height: 1.1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.raya-graph-page .raya-discovery-focus-actions {
  justify-content: flex-start;
}
.raya-graph-page .raya-discovery-focus-actions a {
  font-size: 0.74rem;
  min-height: 1.55rem;
  padding: 0.22rem 0.38rem;
}
.raya-discovery-context-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0.75rem 0 0;
}
.raya-discovery-context-actions[hidden] {
  display: none;
}
.raya-discovery-context-actions a {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-surface) 82%, var(--raya-color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 84%, var(--raya-color-accent));
  border-radius: 0.45rem;
  color: var(--raya-color-text);
  display: inline-flex;
  font-size: 0.9rem;
  font-weight: 800;
  min-height: 2.25rem;
  padding: 0.35rem 0.65rem;
  text-decoration: none;
}
.raya-discovery-context-actions a:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
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
  position: relative;
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
.raya-graph-panel-rail-summary {
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  color: var(--raya-color-muted);
  display: none;
  font-size: 0.72rem;
  font-weight: 800;
  line-height: 1.2;
  margin: 0;
  max-width: 4.75rem;
  overflow: hidden;
  text-align: center;
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
[data-raya-graph-list-state="collapsed"] [data-raya-graph-panel-rail-summary="list"],
[data-raya-graph-inspector-state="collapsed"] [data-raya-graph-panel-rail-summary="inspector"] {
  display: -webkit-box;
}
[data-raya-graph-list-state="collapsed"] .raya-graph-list-panel h2,
[data-raya-graph-inspector-state="collapsed"] .raya-graph-inspector-panel h2 {
  writing-mode: vertical-rl;
}
[data-raya-graph-expanded="true"] .raya-graph-workspace {
  grid-template-columns: minmax(4.5rem, 5.5rem) minmax(40rem, 1fr) minmax(4.5rem, 5.5rem);
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
.raya-graph-toolbar {
  align-items: stretch;
  background: color-mix(in srgb, var(--raya-color-surface) 92%, var(--raya-color-accent-soft));
  border: 1px solid var(--raya-color-border);
  border-radius: 0.5rem;
  gap: 0.25rem;
  padding: 0.25rem;
}
.raya-graph-toolbar-group {
  align-items: center;
  border-right: 1px solid var(--raya-color-border);
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.28rem;
  padding-right: 0.42rem;
}
.raya-graph-toolbar-label {
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  color: var(--raya-color-text-muted);
  flex: 0 0 auto;
  font-size: 0.7rem;
  font-weight: 800;
  height: 1px;
  letter-spacing: 0;
  line-height: 1.2;
  overflow: hidden;
  position: absolute;
  text-transform: uppercase;
  white-space: nowrap;
  width: 1px;
}
.raya-graph-toolbar-group:last-child {
  border-right: 0;
  padding-right: 0;
}
.raya-graph-toolbar-primary {
  align-items: center;
  flex: 1 1 28rem;
}
.raya-graph-toolbar-primary input {
  flex: 1 1 12rem;
  min-width: min(12rem, 100%);
}
.raya-graph-toolbar-viewport,
.raya-graph-toolbar-state {
  flex: 0 1 auto;
}
.raya-graph-active-state {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-accent-soft) 70%, var(--raya-color-surface));
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 38%, var(--raya-color-border));
  border-radius: 999px;
  color: var(--raya-color-text);
  display: inline-flex;
  font-size: 0.74rem;
  font-weight: 800;
  line-height: 1.15;
  min-height: 1.9rem;
  max-width: min(26rem, 100%);
  overflow-wrap: anywhere;
  padding: 0.28rem 0.55rem;
}
.raya-graph-toolbar-pan [data-raya-graph-pan] {
  align-items: center;
  aspect-ratio: 1;
  display: inline-flex;
  font-weight: 800;
  inline-size: 2.125rem;
  justify-content: center;
  padding: 0;
}
.raya-graph-shortcut-hints {
  align-items: center;
  display: inline-flex;
  flex: 0 1 auto;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin: 0;
  min-width: 0;
}
.raya-graph-shortcut-hint {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-surface) 82%, var(--raya-color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 35%, var(--raya-color-border));
  border-radius: 999px;
  color: var(--raya-color-muted);
  display: inline-flex;
  font-size: 0.72rem;
  font-weight: 800;
  gap: 0.3rem;
  line-height: 1.1;
  min-height: 1.7rem;
  padding: 0.18rem 0.48rem;
}
.raya-graph-shortcut-hint kbd {
  background: var(--raya-color-text);
  border: 1px solid color-mix(in srgb, var(--raya-color-text) 78%, var(--raya-color-surface));
  border-radius: 0.25rem;
  color: var(--raya-color-surface);
  font: inherit;
  font-size: 0.68rem;
  line-height: 1;
  min-width: 1.2rem;
  padding: 0.16rem 0.25rem;
  text-align: center;
}
.raya-search-control-panel .raya-search-controls,
.raya-practice-control-panel .raya-practice-controls {
  align-items: stretch;
  display: grid;
  gap: var(--raya-space-card-gap);
}
.raya-discovery-control-group {
  background: color-mix(in srgb, var(--raya-color-surface) 92%, var(--raya-color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 82%, var(--raya-color-accent));
  border-radius: 0.5rem;
  display: grid;
  gap: var(--raya-space-card-gap);
  margin: 0;
  min-inline-size: 0;
  padding: var(--raya-space-card-gap) var(--raya-space-card-padding);
}
.raya-discovery-control-group legend {
  color: var(--raya-color-text-muted);
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0;
  line-height: 1.2;
  padding: 0 0.25rem;
  text-transform: uppercase;
}
.raya-discovery-control-state {
  border-top: 1px solid var(--raya-color-border);
  display: grid;
  gap: var(--raya-space-card-gap);
  margin-top: var(--raya-space-card-gap);
  padding-top: var(--raya-space-card-gap);
}
.raya-discovery-control-state .raya-discovery-summary,
.raya-discovery-control-state .raya-discovery-page-focus {
  margin: 0;
}
.raya-discovery-results-jump {
  display: none;
  margin: 0.75rem 0 0;
}
.raya-discovery-results-jump a {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-surface) 82%, var(--raya-color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 84%, var(--raya-color-accent));
  border-radius: 0.45rem;
  color: var(--raya-color-text);
  display: inline-flex;
  font-size: 0.9rem;
  font-weight: 800;
  justify-content: center;
  min-height: var(--raya-space-card-action-min-height);
  padding: var(--raya-space-chip-padding-block) var(--raya-space-chip-padding-inline);
  text-decoration: none;
  width: 100%;
}
.raya-discovery-results-jump a:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
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
  min-height: var(--raya-space-card-action-min-height);
  padding: var(--raya-space-chip-padding-block) var(--raya-space-chip-padding-inline);
}
.raya-graph-controls button:disabled {
  cursor: not-allowed;
  opacity: 0.52;
}
.raya-graph-controls input,
.raya-graph-controls select,
.raya-graph-controls button,
.raya-graph-chip {
  line-height: 1.1;
  min-height: 1.9rem;
  padding: 0.18rem 0.45rem;
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
  gap: var(--raya-space-inline);
}
.raya-search-results {
  display: grid;
  gap: var(--raya-space-card-gap);
  list-style: none;
  padding-left: 0;
}
.raya-search-results li {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  padding: var(--raya-space-card-padding);
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
  gap: var(--raya-space-inline);
  margin: var(--raya-space-card-gap) 0 0;
}
.raya-search-result-sections {
  background: color-mix(in srgb, var(--raya-color-surface) 90%, var(--raya-color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 80%, var(--raya-color-accent));
  border-radius: 0.375rem;
  margin: var(--raya-space-card-gap) 0 0;
  padding: var(--raya-space-card-gap) var(--raya-space-card-padding);
}
.raya-search-result-sections[hidden] {
  display: none;
}
.raya-search-result-sections h3 {
  font-size: 0.85rem;
  margin: 0 0 0.45rem;
  text-transform: uppercase;
}
.raya-search-result-section-list {
  display: grid;
  gap: var(--raya-space-inline);
  list-style: none;
  margin: 0;
  padding: 0;
}
.raya-search-result-section {
  border-left: 0.2rem solid var(--raya-color-accent);
  display: grid;
  gap: 0.15rem;
  padding-left: 0.55rem;
}
.raya-search-result-section[hidden] {
  display: none;
}
.raya-search-result-section a {
  font-weight: 800;
}
.raya-search-result-section span {
  color: var(--raya-color-muted);
  font-size: 0.84rem;
  line-height: 1.35;
}
.raya-search-result-open,
.raya-search-result-graph,
.raya-search-result-practice,
.raya-search-result-tasks,
.raya-search-result-schedule {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-surface) 88%, var(--raya-color-accent-soft));
  border: 1px solid var(--raya-color-border);
  border-radius: 0.35rem;
  color: var(--raya-color-link);
  display: inline-flex;
  font-weight: 700;
  min-height: var(--raya-space-card-action-min-height);
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
  gap: var(--raya-space-card-gap);
}
.raya-practice-group {
  display: grid;
  gap: var(--raya-space-card-gap);
}
.raya-practice-group h2 {
  border-bottom: 1px solid var(--raya-color-border);
  margin-bottom: 0;
  padding-bottom: 0.35rem;
}
.raya-practice-grid {
  display: grid;
  gap: var(--raya-space-card-gap);
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 22rem), 1fr));
}
.raya-practice-object {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.5rem;
  box-shadow: inset 0.25rem 0 0 var(--raya-color-accent);
  padding: var(--raya-space-card-padding);
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
  gap: var(--raya-space-inline);
}
.raya-practice-kind,
.raya-practice-authority {
  border: 1px solid var(--raya-color-border);
  border-radius: 999px;
  color: var(--raya-color-muted);
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0;
  padding: var(--raya-space-chip-padding-block) var(--raya-space-chip-padding-inline);
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
  margin: var(--raya-space-card-gap) 0 0;
}
.raya-practice-open,
.raya-practice-graph {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-surface) 88%, var(--raya-color-accent-soft));
  border: 1px solid var(--raya-color-border);
  border-radius: 0.35rem;
  display: inline-flex;
  font-weight: 700;
  min-height: var(--raya-space-card-action-min-height);
  padding: 0.25rem 0.65rem;
}
.raya-tasks-page {
  margin: 0 auto;
  max-width: 118rem;
  padding: var(--raya-space-page);
}
.raya-tasks-header {
  margin-bottom: var(--raya-space-block);
  max-width: 72rem;
}
.raya-tasks-workspace {
  align-items: start;
  display: grid;
  gap: var(--raya-space-block);
  grid-template-columns: minmax(16rem, 22rem) minmax(28rem, 1fr) minmax(17rem, 23rem);
  margin-top: var(--raya-space-block);
}
.raya-tasks-control-panel,
.raya-tasks-results-panel,
.raya-tasks-context-panel {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.5rem;
  min-width: 0;
  padding: 0.9rem;
}
.raya-tasks-control-panel,
.raya-tasks-context-panel {
  position: sticky;
  top: calc(var(--raya-topbar-height, 4rem) + 1rem);
}
.raya-tasks-control-panel h2,
.raya-tasks-context-panel h2 {
  font-size: 1rem;
  margin: 0 0 0.75rem;
}
.raya-tasks-context-panel [data-raya-tasks-context-title] {
  font-weight: 800;
  line-height: 1.35;
  margin: 0;
}
.raya-tasks-controls {
  align-items: stretch;
  display: grid;
  gap: var(--raya-space-card-gap);
}
.raya-tasks-controls input,
.raya-tasks-controls select,
.raya-tasks-controls button,
.raya-task-chip {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  font: inherit;
  min-height: var(--raya-space-card-action-min-height);
  min-width: 0;
  padding: var(--raya-space-chip-padding-block) var(--raya-space-chip-padding-inline);
}
.raya-task-filters {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: var(--raya-space-inline);
}
.raya-task-chip[aria-pressed="true"] {
  border-color: var(--raya-color-accent);
  box-shadow: inset 0 -0.2rem 0 var(--raya-color-accent);
}
.raya-tasks-status,
.raya-tasks-empty,
.raya-task-meta,
.raya-task-preview {
  color: var(--raya-color-muted);
  font-size: 0.875rem;
}
.raya-tasks-results {
  display: grid;
  gap: var(--raya-space-card-gap);
}
.raya-tasks-empty[hidden],
.raya-task-object[hidden] {
  display: none;
}
.raya-task-object {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.5rem;
  box-shadow: inset 0.25rem 0 0 var(--raya-color-success);
  padding: var(--raya-space-card-padding);
  transition: border-color 120ms ease, box-shadow 120ms ease, transform 120ms ease;
}
.raya-task-object[data-raya-task-active="true"] {
  border-color: var(--raya-color-accent);
  box-shadow:
    inset 0.25rem 0 0 var(--raya-color-success),
    0 0 0 3px color-mix(in srgb, var(--raya-color-accent) 24%, transparent);
  transform: translateY(-1px);
}
.raya-task-object-header,
.raya-task-actions,
.raya-task-tags {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: var(--raya-space-inline);
}
.raya-task-kind,
.raya-task-authority,
.raya-task-tag {
  border: 1px solid var(--raya-color-border);
  border-radius: 999px;
  color: var(--raya-color-muted);
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0;
  padding: var(--raya-space-chip-padding-block) var(--raya-space-chip-padding-inline);
}
.raya-task-kind {
  background: color-mix(in srgb, var(--raya-color-success) 14%, transparent);
  color: var(--raya-color-text);
  text-transform: uppercase;
}
.raya-task-tag {
  background: color-mix(in srgb, var(--raya-color-accent-soft) 70%, transparent);
}
.raya-task-object h3 {
  font-size: clamp(1.05rem, 1rem + 0.2vw, 1.25rem);
  margin: 0.65rem 0 0.4rem;
}
.raya-task-object[data-raya-task-active="true"] h3 {
  color: var(--raya-color-success);
}
.raya-task-actions {
  margin: var(--raya-space-card-gap) 0 0;
}
.raya-task-open,
.raya-task-graph {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-surface) 88%, var(--raya-color-accent-soft));
  border: 1px solid var(--raya-color-border);
  border-radius: 0.35rem;
  display: inline-flex;
  font-weight: 700;
  min-height: var(--raya-space-card-action-min-height);
  padding: 0.25rem 0.65rem;
}
.raya-schedule-page {
  margin: 0 auto;
  max-width: 118rem;
  padding: var(--raya-space-page);
}
.raya-schedule-header {
  margin-bottom: var(--raya-space-block);
  max-width: 72rem;
}
.raya-schedule-workspace {
  align-items: start;
  display: grid;
  gap: var(--raya-space-block);
  grid-template-columns: minmax(16rem, 22rem) minmax(28rem, 1fr) minmax(17rem, 23rem);
  margin-top: var(--raya-space-block);
}
.raya-schedule-control-panel,
.raya-schedule-results-panel,
.raya-schedule-context-panel {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.5rem;
  min-width: 0;
  padding: 0.9rem;
}
.raya-schedule-control-panel,
.raya-schedule-context-panel {
  position: sticky;
  top: calc(var(--raya-topbar-height, 4rem) + 1rem);
}
.raya-schedule-control-panel h2,
.raya-schedule-context-panel h2 {
  font-size: 1rem;
  margin: 0 0 0.75rem;
}
.raya-schedule-context-panel [data-raya-schedule-context-title] {
  font-weight: 800;
  line-height: 1.35;
  margin: 0;
}
.raya-schedule-controls {
  align-items: stretch;
  display: grid;
  gap: var(--raya-space-card-gap);
}
.raya-schedule-controls input,
.raya-schedule-controls button,
.raya-schedule-chip {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  font: inherit;
  min-height: var(--raya-space-card-action-min-height);
  min-width: 0;
  padding: var(--raya-space-chip-padding-block) var(--raya-space-chip-padding-inline);
}
.raya-schedule-filters {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: var(--raya-space-inline);
}
.raya-schedule-chip[aria-pressed="true"] {
  border-color: var(--raya-color-accent);
  box-shadow: inset 0 -0.2rem 0 var(--raya-color-accent);
}
.raya-schedule-status,
.raya-schedule-empty,
.raya-schedule-meta,
.raya-schedule-preview {
  color: var(--raya-color-muted);
  font-size: 0.875rem;
}
.raya-schedule-results {
  display: grid;
  gap: var(--raya-space-card-gap);
}
.raya-schedule-empty[hidden],
.raya-schedule-item[hidden] {
  display: none;
}
.raya-schedule-item {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.5rem;
  box-shadow: inset 0.25rem 0 0 var(--raya-color-accent);
  padding: var(--raya-space-card-padding);
  transition: border-color 120ms ease, box-shadow 120ms ease, transform 120ms ease;
}
.raya-schedule-item[data-raya-schedule-active="true"] {
  border-color: var(--raya-color-accent);
  box-shadow:
    inset 0.25rem 0 0 var(--raya-color-accent),
    0 0 0 3px color-mix(in srgb, var(--raya-color-accent) 24%, transparent);
  transform: translateY(-1px);
}
.raya-schedule-item-header,
.raya-schedule-actions,
.raya-schedule-tags {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: var(--raya-space-inline);
}
.raya-schedule-date,
.raya-schedule-kind,
.raya-schedule-tag {
  border: 1px solid var(--raya-color-border);
  border-radius: 999px;
  color: var(--raya-color-muted);
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0;
  padding: var(--raya-space-chip-padding-block) var(--raya-space-chip-padding-inline);
}
.raya-schedule-date {
  background: color-mix(in srgb, var(--raya-color-accent) 14%, transparent);
  color: var(--raya-color-text);
}
.raya-schedule-kind {
  text-transform: uppercase;
}
.raya-schedule-tag {
  background: color-mix(in srgb, var(--raya-color-accent-soft) 70%, transparent);
}
.raya-schedule-item h3 {
  font-size: clamp(1.05rem, 1rem + 0.2vw, 1.25rem);
  margin: 0.65rem 0 0.4rem;
}
.raya-schedule-item[data-raya-schedule-active="true"] h3 {
  color: var(--raya-color-success);
}
.raya-schedule-actions {
  margin: var(--raya-space-card-gap) 0 0;
}
.raya-schedule-open,
.raya-schedule-graph {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-surface) 88%, var(--raya-color-accent-soft));
  border: 1px solid var(--raya-color-border);
  border-radius: 0.35rem;
  display: inline-flex;
  font-weight: 700;
  min-height: var(--raya-space-card-action-min-height);
  padding: 0.25rem 0.65rem;
}
.raya-discovery-header {
  border-bottom: 1px solid color-mix(in srgb, var(--raya-color-border) 70%, transparent);
  display: grid;
  gap: 0.45rem;
  margin-bottom: 1rem;
  max-width: 78rem;
  padding-bottom: 0.85rem;
}
.raya-discovery-header h1 {
  font-size: 2rem;
  line-height: 1.12;
  margin: 0;
}
.raya-discovery-header p {
  color: var(--raya-color-muted);
  margin: 0;
  max-width: 58rem;
}
.raya-search-workspace,
.raya-practice-workspace,
.raya-tasks-workspace,
.raya-schedule-workspace {
  gap: 1rem;
  grid-template-columns: minmax(17rem, 22rem) minmax(34rem, 1fr) minmax(18rem, 24rem);
}
.raya-discovery-panel-header {
  align-items: center;
  display: flex;
  gap: 0.75rem;
  justify-content: space-between;
  margin-bottom: 0.8rem;
}
.raya-discovery-panel-header h2 {
  margin: 0;
}
.raya-discovery-panel-rail-summary {
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  color: var(--raya-color-muted);
  display: none;
  font-size: 0.72rem;
  font-weight: 800;
  line-height: 1.2;
  margin: 0;
  max-width: 4.75rem;
  overflow: hidden;
  text-align: center;
}
.raya-discovery-panel-header button {
  background: color-mix(in srgb, var(--raya-color-surface) 82%, var(--raya-color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 84%, var(--raya-color-accent));
  border-radius: 0.45rem;
  color: var(--raya-color-text);
  font: inherit;
  font-size: 0.85rem;
  font-weight: 800;
  min-height: 2.25rem;
  padding: 0.35rem 0.6rem;
}
.raya-discovery-panel-header button:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
.raya-discovery-panel-body[aria-hidden="true"] {
  display: none;
}
[data-raya-discovery-controls-state="collapsed"] .raya-search-workspace,
[data-raya-discovery-controls-state="collapsed"] .raya-practice-workspace,
[data-raya-discovery-controls-state="collapsed"] .raya-tasks-workspace,
[data-raya-discovery-controls-state="collapsed"] .raya-schedule-workspace {
  grid-template-columns: minmax(4.5rem, 5.75rem) minmax(36rem, 1fr) minmax(18rem, 24rem);
}
[data-raya-discovery-context-state="collapsed"] .raya-search-workspace,
[data-raya-discovery-context-state="collapsed"] .raya-practice-workspace,
[data-raya-discovery-context-state="collapsed"] .raya-tasks-workspace,
[data-raya-discovery-context-state="collapsed"] .raya-schedule-workspace {
  grid-template-columns: minmax(17rem, 22rem) minmax(36rem, 1fr) minmax(4.5rem, 5.75rem);
}
[data-raya-discovery-controls-state="collapsed"][data-raya-discovery-context-state="collapsed"] .raya-search-workspace,
[data-raya-discovery-controls-state="collapsed"][data-raya-discovery-context-state="collapsed"] .raya-practice-workspace,
[data-raya-discovery-controls-state="collapsed"][data-raya-discovery-context-state="collapsed"] .raya-tasks-workspace,
[data-raya-discovery-controls-state="collapsed"][data-raya-discovery-context-state="collapsed"] .raya-schedule-workspace {
  grid-template-columns: minmax(4.5rem, 5.75rem) minmax(42rem, 1fr) minmax(4.5rem, 5.75rem);
}
[data-raya-discovery-controls-state="collapsed"] .raya-search-control-panel,
[data-raya-discovery-controls-state="collapsed"] .raya-practice-control-panel,
[data-raya-discovery-controls-state="collapsed"] .raya-tasks-control-panel,
[data-raya-discovery-controls-state="collapsed"] .raya-schedule-control-panel,
[data-raya-discovery-context-state="collapsed"] .raya-search-context-panel,
[data-raya-discovery-context-state="collapsed"] .raya-practice-context-panel,
[data-raya-discovery-context-state="collapsed"] .raya-tasks-context-panel,
[data-raya-discovery-context-state="collapsed"] .raya-schedule-context-panel {
  align-items: center;
  display: flex;
  flex-direction: column;
}
[data-raya-discovery-controls-state="collapsed"] .raya-search-control-panel .raya-discovery-panel-header,
[data-raya-discovery-controls-state="collapsed"] .raya-practice-control-panel .raya-discovery-panel-header,
[data-raya-discovery-controls-state="collapsed"] .raya-tasks-control-panel .raya-discovery-panel-header,
[data-raya-discovery-controls-state="collapsed"] .raya-schedule-control-panel .raya-discovery-panel-header,
[data-raya-discovery-context-state="collapsed"] .raya-search-context-panel .raya-discovery-panel-header,
[data-raya-discovery-context-state="collapsed"] .raya-practice-context-panel .raya-discovery-panel-header,
[data-raya-discovery-context-state="collapsed"] .raya-tasks-context-panel .raya-discovery-panel-header,
[data-raya-discovery-context-state="collapsed"] .raya-schedule-context-panel .raya-discovery-panel-header {
  flex-direction: column;
}
[data-raya-discovery-controls-state="collapsed"] [data-raya-discovery-panel-rail-summary="controls"],
[data-raya-discovery-context-state="collapsed"] [data-raya-discovery-panel-rail-summary="context"] {
  display: -webkit-box;
}
[data-raya-discovery-controls-state="collapsed"] .raya-search-control-panel h2,
[data-raya-discovery-controls-state="collapsed"] .raya-practice-control-panel h2,
[data-raya-discovery-controls-state="collapsed"] .raya-tasks-control-panel h2,
[data-raya-discovery-controls-state="collapsed"] .raya-schedule-control-panel h2,
[data-raya-discovery-context-state="collapsed"] .raya-search-context-panel h2,
[data-raya-discovery-context-state="collapsed"] .raya-practice-context-panel h2,
[data-raya-discovery-context-state="collapsed"] .raya-tasks-context-panel h2,
[data-raya-discovery-context-state="collapsed"] .raya-schedule-context-panel h2 {
  writing-mode: vertical-rl;
}
.raya-search-control-panel,
.raya-search-context-panel,
.raya-practice-control-panel,
.raya-practice-context-panel,
.raya-tasks-control-panel,
.raya-tasks-context-panel,
.raya-schedule-control-panel,
.raya-schedule-context-panel,
.raya-graph-list-panel,
.raya-graph-inspector-panel {
  background: color-mix(in srgb, var(--raya-color-surface) 86%, var(--raya-color-page));
  border-color: color-mix(in srgb, var(--raya-color-border) 68%, var(--raya-color-page));
  box-shadow: 0 0.5rem 1.25rem rgba(31, 35, 40, 0.035);
  padding: 1rem;
}
.raya-search-results-panel,
.raya-practice-results-panel,
.raya-tasks-results-panel,
.raya-schedule-results-panel {
  background: var(--raya-color-surface);
  border-color: color-mix(in srgb, var(--raya-color-border) 84%, var(--raya-color-page));
  box-shadow: 0 1rem 2.5rem rgba(31, 35, 40, 0.06);
  padding: 1rem;
}
.raya-graph-map-panel {
  background: var(--raya-color-surface);
  border-color: color-mix(in srgb, var(--raya-color-border) 84%, var(--raya-color-page));
  box-shadow: 0 1rem 2.5rem rgba(31, 35, 40, 0.06);
  overflow-x: clip;
  padding: 0.75rem;
}
.raya-search-control-panel h2,
.raya-search-context-panel h2,
.raya-practice-control-panel h2,
.raya-practice-context-panel h2,
.raya-tasks-control-panel h2,
.raya-tasks-context-panel h2,
.raya-schedule-control-panel h2,
.raya-schedule-context-panel h2,
.raya-graph-panel-header h2 {
  color: var(--raya-color-text);
  font-size: 0.95rem;
  letter-spacing: 0;
}
.raya-search-context-panel [data-raya-search-context-title],
.raya-practice-context-panel [data-raya-practice-context-title],
.raya-tasks-context-panel [data-raya-tasks-context-title],
.raya-schedule-context-panel [data-raya-schedule-context-title] {
  color: var(--raya-color-text);
  font-weight: 800;
}
.raya-search-results li,
.raya-practice-object,
.raya-task-object,
.raya-schedule-item {
  border-color: color-mix(in srgb, var(--raya-color-border) 82%, var(--raya-color-page));
  border-radius: 0.5rem;
}
.raya-search-results li,
.raya-practice-object,
.raya-task-object,
.raya-schedule-item,
.raya-graph-list li {
  scroll-margin-top: calc(var(--raya-topbar-height, 4rem) + 1rem);
}
.raya-search-results-panel,
.raya-practice-results-panel,
.raya-tasks-results-panel,
.raya-schedule-results-panel {
  scroll-margin-top: calc(var(--raya-topbar-height, 4rem) + 1rem);
}
.raya-search-results li[data-raya-search-active="true"],
.raya-practice-object[data-raya-practice-active="true"],
.raya-task-object[data-raya-task-active="true"],
.raya-schedule-item[data-raya-schedule-active="true"] {
  border-color: var(--raya-color-accent);
}
.raya-search-result-open,
.raya-search-result-graph,
.raya-search-result-practice,
.raya-search-result-tasks,
.raya-search-result-schedule,
.raya-practice-open,
.raya-practice-graph,
.raya-task-open,
.raya-task-graph,
.raya-schedule-open,
.raya-schedule-graph,
.raya-graph-detail-actions a,
.raya-graph-panel-header button {
  background: color-mix(in srgb, var(--raya-color-surface) 82%, var(--raya-color-accent-soft));
  border-color: color-mix(in srgb, var(--raya-color-border) 84%, var(--raya-color-accent));
  border-radius: 0.45rem;
}
.raya-graph-toolbar,
.raya-graph-legend,
.raya-graph-canvas-legend {
  background: color-mix(in srgb, var(--raya-color-surface) 88%, var(--raya-color-page));
  border-color: color-mix(in srgb, var(--raya-color-border) 76%, var(--raya-color-page));
  box-shadow: 0 0.5rem 1.25rem rgba(31, 35, 40, 0.035);
}
.raya-graph-canvas-legend {
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 82%, var(--raya-color-page));
  border-radius: 0.55rem;
  display: grid;
  gap: 0.45rem;
  margin: 0.55rem 0;
  padding: 0.55rem;
}
.raya-graph-canvas-legend h2 {
  color: var(--raya-color-muted);
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  margin: 0;
  text-transform: uppercase;
}
.raya-graph-canvas-legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}
.raya-graph-canvas-legend .raya-graph-chip {
  min-height: 2rem;
  padding: 0.2rem 0.55rem;
}
@media (max-width: 720px) {
  .raya-graph-canvas-legend-items {
    flex-wrap: nowrap;
    overflow-x: auto;
    padding-bottom: 0.15rem;
  }
  .raya-graph-canvas-legend .raya-graph-chip {
    flex: 0 0 auto;
  }
}
.raya-graph-edge-kind-filters {
  align-items: center;
}
.raya-graph-edge-kind-filters > span {
  color: var(--raya-color-muted);
  font-size: 0.85rem;
  font-weight: 800;
}
.raya-graph-edge-kind-filter[aria-pressed="false"],
[data-raya-graph-edge-kind-filter][aria-pressed="false"] {
  background: var(--raya-color-surface);
  border-color: var(--raya-color-border);
  color: var(--raya-color-muted);
  opacity: 0.72;
}
.raya-graph-list {
  list-style: none;
  padding-left: 0;
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
.raya-graph-inspection-preview {
  background: color-mix(in srgb, var(--raya-color-surface) 90%, var(--raya-color-accent-soft));
  border: 1px solid var(--raya-color-border);
  border-radius: 0.5rem;
  bottom: 1rem;
  box-shadow: 0 0.85rem 1.65rem color-mix(in srgb, var(--raya-color-text) 14%, transparent);
  inline-size: min(32rem, calc(100% - 2rem));
  left: auto;
  margin: 0;
  padding: 0.8rem 0.9rem;
  pointer-events: none;
  position: absolute;
  right: 1rem;
  top: auto;
  z-index: 5;
}
.raya-graph-inspection-preview[hidden] {
  display: none;
}
.raya-graph-inspection-preview-header {
  align-items: baseline;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.75rem;
  justify-content: space-between;
}
.raya-graph-inspection-preview h2 {
  font-size: 1rem;
  margin: 0;
}
.raya-graph-inspection-preview p {
  margin: 0.4rem 0 0;
}
.raya-graph-inspection-preview [data-raya-graph-inspection-preview-meta],
.raya-graph-inspection-preview-counts {
  color: var(--raya-color-muted);
  font-size: 0.875rem;
  font-weight: 700;
}
.raya-graph-inspection-preview-actions {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  pointer-events: auto;
}
.raya-graph-relationship-preview {
  background: color-mix(in srgb, var(--raya-color-surface) 90%, var(--raya-color-accent-soft));
  border: 1px solid var(--raya-color-accent);
  border-radius: 0.5rem;
  box-shadow: 0 0.75rem 1.4rem color-mix(in srgb, var(--raya-color-text) 12%, transparent);
  margin: 0.65rem 0;
  padding: 0.8rem 0.9rem;
}
.raya-graph-relationship-preview[hidden] {
  display: none;
}
.raya-graph-relationship-preview h2,
.raya-graph-relationship-preview p {
  margin: 0;
}
.raya-graph-relationship-preview h2 {
  font-size: 1rem;
  margin-block-end: 0.35rem;
}
.raya-graph-relationship-preview-kicker {
  color: var(--raya-color-muted);
  font-size: 0.78rem;
  font-weight: 800;
  text-transform: uppercase;
}
.raya-graph-relationship-preview-actions {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-block-start: 0.65rem;
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
.raya-graph-legend-edge-navigation {
  background: var(--raya-color-border);
}
.raya-graph-legend-edge-content {
  background: repeating-linear-gradient(
    90deg,
    var(--raya-color-border) 0 0.35rem,
    transparent 0.35rem 0.6rem
  );
}
.raya-graph-legend-edge-prerequisite {
  background: repeating-linear-gradient(
    90deg,
    var(--raya-color-border) 0 0.55rem,
    transparent 0.55rem 0.85rem
  );
  height: 0.22rem;
}
.raya-graph-legend-edge-parent {
  background: repeating-linear-gradient(
    90deg,
    var(--raya-color-border) 0 0.14rem,
    transparent 0.14rem 0.38rem
  );
  opacity: 0.72;
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
.raya-graph-guide {
  background: color-mix(in srgb, var(--raya-color-surface) 86%, transparent);
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 82%, transparent);
  border-radius: 0.375rem;
  margin: 0 0 0.58rem;
  padding: 0.42rem 0.5rem;
}
.raya-graph-guide > summary {
  align-items: center;
  color: var(--raya-color-heading);
  cursor: pointer;
  display: flex;
  font-size: 0.78rem;
  font-weight: 850;
  letter-spacing: 0;
  line-height: 1.25;
  margin: 0;
  min-height: 2rem;
}
.raya-graph-guide > summary:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
.raya-graph-guide-cards {
  display: grid;
  gap: 0.38rem;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  margin-top: 0.42rem;
}
.raya-graph-guide-card {
  background: color-mix(in srgb, var(--raya-color-surface) 86%, transparent);
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 82%, transparent);
  border-radius: 0.375rem;
  min-width: 0;
  padding: 0.42rem 0.48rem;
}
.raya-graph-guide-card h3 {
  color: var(--raya-color-heading);
  font-size: 0.72rem;
  letter-spacing: 0;
  margin: 0 0 0.16rem;
}
.raya-graph-guide-card p {
  color: var(--raya-color-muted);
  font-size: 0.68rem;
  line-height: 1.24;
  margin: 0;
}
.raya-graph-guide-mobile {
  display: none;
}
@media (max-width: 900px) {
  .raya-graph-guide-cards {
    grid-template-columns: repeat(auto-fit, minmax(8.5rem, 1fr));
  }
  .raya-graph-guide-desktop {
    display: none;
  }
  .raya-graph-guide-mobile {
    display: inline;
  }
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
.raya-graph-detail-nav {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin: 0.65rem 0 0.8rem;
}
.raya-graph-detail-nav-button {
  border-radius: 999px !important;
  font-size: 0.82rem !important;
  font-weight: 800;
  min-height: 1.9rem !important;
  padding: 0.25rem 0.6rem !important;
}
.raya-graph-detail-nav-button:disabled {
  color: var(--raya-color-muted);
  cursor: default;
  opacity: 0.56;
}
.raya-graph-detail-nav-button:focus-visible,
[data-raya-graph-detail-jump-target]:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
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
.raya-graph-state {
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  margin: 0 0 1rem;
  padding: 0.75rem;
}
.raya-graph-state summary {
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 800;
  margin: 0 0 0.5rem;
}
.raya-graph-state:not([open]) summary {
  margin-bottom: 0;
}
.raya-graph-state summary:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
.raya-graph-state dl {
  display: grid;
  gap: 0.35rem;
  margin: 0;
}
.raya-graph-state div {
  display: grid;
  gap: 0.35rem;
  grid-template-columns: minmax(5.5rem, 0.42fr) minmax(0, 1fr);
}
.raya-graph-state dt {
  color: var(--raya-color-muted);
  font-size: 0.82rem;
  font-weight: 700;
}
.raya-graph-state dd {
  margin: 0;
  min-width: 0;
}
.raya-graph-state code {
  display: block;
  max-width: 100%;
  overflow-wrap: anywhere;
}
.raya-graph-share-url {
  align-items: start;
  display: grid;
  gap: 0.45rem;
}
.raya-graph-share-url button {
  justify-self: start;
  min-height: 2rem;
}
.raya-graph-share-url span {
  color: var(--raya-color-muted);
  font-size: 0.82rem;
  min-height: 1.1rem;
}
.raya-graph-detail-focus-node {
  margin-left: 0.4rem;
}
.raya-graph-detail-meta,
.raya-graph-detail-summary,
.raya-graph-detail-study-counts,
.raya-graph-detail-section-kind,
.raya-graph-detail-edge-kind {
  color: var(--raya-color-muted);
  font-size: 0.875rem;
}
.raya-graph-detail-sections {
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  margin: 0.75rem 0;
  padding: 0.65rem;
}
.raya-graph-detail-sections h3 {
  font-size: 0.95rem;
  margin: 0 0 0.45rem;
}
.raya-graph-detail-sections ol {
  display: grid;
  gap: 0.35rem;
  margin: 0;
  padding-left: 1.25rem;
}
.raya-graph-detail-sections li {
  min-width: 0;
}
.raya-graph-detail-sections a {
  display: inline-block;
  max-width: 100%;
  overflow-wrap: anywhere;
  padding-block: 0.12rem;
}
.raya-graph-detail-section-kind {
  display: block;
}
.raya-graph-detail-study-objects {
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  margin: 0.75rem 0;
  padding: 0.65rem;
}
.raya-graph-detail-study-objects h3 {
  font-size: 0.95rem;
  margin: 0 0 0.45rem;
}
.raya-graph-detail-study-objects ul {
  display: grid;
  gap: 0.55rem;
  list-style: none;
  margin: 0;
  padding: 0;
}
.raya-graph-detail-study-objects li {
  border-left: 0.2rem solid var(--raya-color-accent);
  display: grid;
  gap: 0.18rem;
  padding-left: 0.55rem;
}
.raya-graph-detail-study-object-meta,
.raya-graph-detail-study-object-preview {
  color: var(--raya-color-muted);
  font-size: 0.85rem;
}
.raya-graph-detail-key-objects {
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  margin: 0.75rem 0;
  padding: 0.65rem;
}
.raya-graph-detail-key-objects h3 {
  font-size: 0.95rem;
  margin: 0 0 0.45rem;
}
.raya-graph-detail-key-objects ol {
  display: grid;
  gap: 0.35rem;
  margin: 0;
  padding-left: 1.25rem;
}
.raya-graph-detail-key-objects li {
  min-width: 0;
}
.raya-graph-detail-key-objects a {
  display: inline-block;
  max-width: 100%;
  overflow-wrap: anywhere;
  padding-block: 0.12rem;
}
.raya-graph-detail-relationship-overview {
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  margin: 0.75rem 0;
  padding: 0.65rem;
}
.raya-graph-detail-relationship-overview h3 {
  font-size: 0.95rem;
  margin: 0 0 0.35rem;
}
.raya-graph-detail-relationship-overview p {
  color: var(--raya-color-muted);
  font-size: 0.85rem;
  margin: 0 0 0.55rem;
}
.raya-graph-relationship-overview-grid {
  display: grid;
  gap: 0.45rem;
  grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr));
}
.raya-graph-relationship-overview-card {
  background: color-mix(in srgb, var(--raya-color-surface) 90%, var(--raya-color-accent-soft));
  border: 1px solid var(--raya-color-border);
  border-left: 0.25rem solid var(--raya-color-accent);
  border-radius: 0.35rem;
  color: var(--raya-color-text);
  cursor: pointer;
  display: grid;
  font: inherit;
  gap: 0.22rem;
  min-height: 4.25rem;
  padding: 0.55rem 0.6rem;
  text-align: left;
}
.raya-graph-relationship-overview-card[aria-pressed="true"] {
  background: var(--raya-color-text);
  border-color: var(--raya-color-text);
  color: var(--raya-color-surface);
}
.raya-graph-relationship-overview-card.is-hidden-by-filter {
  background: color-mix(in srgb, var(--raya-color-surface) 82%, var(--raya-color-muted));
  border-color: color-mix(in srgb, var(--raya-color-border) 72%, var(--raya-color-muted));
  color: var(--raya-color-muted);
}
.raya-graph-relationship-overview-card:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 2px;
}
.raya-graph-relationship-overview-title {
  font-weight: 800;
}
.raya-graph-relationship-overview-count {
  font-size: 0.82rem;
  font-weight: 800;
}
.raya-graph-relationship-overview-meaning {
  color: var(--raya-color-muted);
  font-size: 0.8rem;
  line-height: 1.35;
}
.raya-graph-relationship-overview-card[aria-pressed="true"] .raya-graph-relationship-overview-meaning {
  color: color-mix(in srgb, var(--raya-color-surface) 78%, var(--raya-color-accent-soft));
}
.raya-graph-detail-relationship-chips {
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  margin: 0.75rem 0;
  padding: 0.65rem;
}
.raya-graph-detail-relationship-chips h3 {
  font-size: 0.95rem;
  margin: 0 0 0.45rem;
}
.raya-graph-relationship-focus-bar {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: space-between;
  margin: 0 0 0.55rem;
}
.raya-graph-relationship-focus-bar p {
  color: var(--raya-color-muted);
  font-size: 0.85rem;
  margin: 0;
}
.raya-graph-relationship-focus-reset {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  cursor: pointer;
  font: inherit;
  font-size: 0.82rem;
  font-weight: 700;
  min-height: 1.85rem;
  padding: 0.25rem 0.55rem;
  white-space: nowrap;
}
.raya-graph-relationship-focus-reset:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 2px;
}
.raya-graph-detail-relationship-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}
.raya-graph-detail-relationship-chip {
  align-items: center;
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 999px;
  color: var(--raya-color-text);
  cursor: pointer;
  display: inline-flex;
  font: inherit;
  font-size: 0.82rem;
  font-weight: 700;
  gap: 0.35rem;
  line-height: 1.2;
  min-height: 1.8rem;
  padding: 0.25rem 0.55rem;
}
.raya-graph-detail-relationship-chip[aria-pressed="true"] {
  background: var(--raya-color-text);
  border-color: var(--raya-color-text);
  color: var(--raya-color-surface);
}
.raya-graph-detail-relationship-chip.is-hidden-by-filter {
  background: color-mix(in srgb, var(--raya-color-surface) 78%, var(--raya-color-muted));
  border-color: color-mix(in srgb, var(--raya-color-border) 72%, var(--raya-color-muted));
  color: var(--raya-color-muted);
}
.raya-graph-detail-relationship-chip:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 2px;
}
.raya-graph-relationship-walkthrough {
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  margin: 0.75rem 0;
  padding: 0.65rem;
}
.raya-graph-relationship-walkthrough h3 {
  font-size: 0.95rem;
  margin: 0 0 0.55rem;
}
.raya-graph-relationship-focus-status {
  color: var(--raya-color-muted);
  font-size: 0.85rem;
  margin: -0.15rem 0 0.55rem;
}
.raya-graph-relationship-walkthrough-list {
  display: grid;
  gap: 0.55rem;
}
.raya-graph-relationship-walkthrough-card {
  background: color-mix(in srgb, var(--raya-color-surface) 92%, var(--raya-color-accent-soft));
  border: 1px solid var(--raya-color-border);
  border-left: 0.25rem solid var(--raya-color-accent);
  border-radius: 0.35rem;
  display: grid;
  gap: 0.35rem;
  padding: 0.6rem 0.65rem;
}
.raya-graph-relationship-walkthrough-card h4 {
  font-size: 0.92rem;
  margin: 0;
}
.raya-graph-relationship-walkthrough-card p {
  color: var(--raya-color-muted);
  font-size: 0.85rem;
  margin: 0;
}
.raya-graph-relationship-walkthrough-card ul {
  display: grid;
  gap: 0.35rem;
  list-style: none;
  margin: 0.1rem 0 0;
  padding: 0;
}
.raya-graph-relationship-walkthrough-card li {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  justify-content: space-between;
}
.raya-graph-detail-reading-path {
  background: color-mix(in srgb, var(--raya-color-surface) 88%, var(--raya-color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 80%, var(--raya-color-accent));
  border-radius: 0.55rem;
  display: grid;
  gap: 0.55rem;
  margin: 0.8rem 0;
  padding: 0.75rem;
}
.raya-graph-detail-reading-path h3 {
  font-size: 0.98rem;
  margin: 0;
}
.raya-graph-detail-reading-path-summary {
  color: var(--raya-color-muted);
  font-size: 0.86rem;
  margin: 0;
}
.raya-graph-detail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0;
}
.raya-graph-detail-actions a,
.raya-graph-detail-secondary-actions button {
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
.raya-graph-detail-primary-actions {
  align-items: stretch;
}
.raya-graph-detail-actions .raya-graph-detail-open-primary {
  background: var(--raya-color-accent);
  border-color: var(--raya-color-accent);
  color: var(--raya-color-accent-contrast);
  font-weight: 800;
  justify-content: center;
  min-width: min(100%, 14rem);
}
.raya-graph-detail-actions .raya-graph-detail-open-primary:focus-visible,
.raya-graph-detail-actions .raya-graph-detail-open-primary:hover {
  filter: brightness(0.96);
}
.raya-graph-detail-actions a[hidden],
.raya-graph-detail-actions button[hidden] {
  display: none;
}
.raya-graph-detail-sequence {
  display: grid;
  gap: 0.5rem;
  grid-template-columns: repeat(auto-fit, minmax(9.5rem, 1fr));
  margin: 0;
}
.raya-graph-detail-sequence a {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-left: 0.25rem solid var(--raya-color-border);
  border-radius: 0.4rem;
  color: var(--raya-color-link);
  font-weight: 750;
  line-height: 1.35;
  min-height: 3rem;
  padding: 0.45rem 0.55rem;
}
.raya-graph-detail-sequence a[hidden] {
  display: none;
}
[data-raya-graph-detail-current] {
  border-left-color: var(--raya-color-accent) !important;
  color: var(--raya-color-text) !important;
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
.raya-graph-empty {
  background: color-mix(in srgb, var(--raya-color-warning-soft) 74%, var(--raya-color-surface));
  border: 1px solid var(--raya-color-border);
  border-left: 0.25rem solid var(--raya-color-warning);
  border-radius: 0.375rem;
  display: grid;
  gap: 0.5rem;
  margin: 0.35rem 0;
  padding: 0.7rem;
}
.raya-graph-empty p {
  margin: 0;
}
.raya-graph-empty button {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  font: inherit;
  justify-self: start;
  min-height: 2.25rem;
  padding: 0.35rem 0.65rem;
}
.raya-graph-canvas {
  background:
    radial-gradient(
      circle at 20% 18%,
      color-mix(in srgb, var(--raya-color-accent) 10%, transparent) 0,
      transparent 22rem
    ),
    linear-gradient(
      90deg,
      color-mix(in srgb, var(--raya-color-border) 28%, transparent) 1px,
      transparent 1px
    ),
    linear-gradient(
      0deg,
      color-mix(in srgb, var(--raya-color-border) 22%, transparent) 1px,
      transparent 1px
    ),
    color-mix(in srgb, var(--raya-color-surface) 94%, var(--raya-color-accent-soft));
  background-size: auto, 2.5rem 2.5rem, 2.5rem 2.5rem, auto;
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 82%, var(--raya-color-page));
  border-radius: 0.375rem;
  box-shadow:
    inset 0 1px 0 color-mix(in srgb, var(--raya-color-surface) 74%, white),
    0 1rem 2.25rem color-mix(in srgb, var(--raya-color-text) 7%, transparent);
  cursor: grab;
  display: block;
  flex: 0 0 auto;
  height: clamp(24rem, 50vh, 36rem);
  order: 4;
  width: 100%;
}
.raya-graph-canvas-hint {
  color: var(--raya-color-muted);
  font-size: 0.78rem;
  font-weight: 800;
  line-height: 1.3;
  margin: 0 0 0.45rem;
  order: 1;
}
.raya-graph-status,
.raya-graph-arrangement-status {
  order: 2;
}
.raya-graph-orientation {
  order: 5;
}
.raya-graph-canvas-legend {
  order: 6;
}
.raya-graph-minimap-panel {
  order: 7;
}
.raya-graph-canvas.is-panning {
  cursor: grabbing;
}
.raya-graph-canvas.is-dragging-node,
.raya-graph-canvas.is-dragging-node .raya-graph-node-link {
  cursor: grabbing;
}
.raya-graph-canvas:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
[data-raya-graph-expanded="true"] .raya-graph-canvas {
  height: clamp(42rem, 84vh, 64rem);
}
.raya-graph-canvas[hidden] {
  display: none;
}
.raya-graph-minimap-panel {
  align-items: start;
  display: grid;
  gap: 0.28rem;
  grid-template-columns: minmax(0, 1fr) auto;
  margin: 0.55rem 0 0;
}
.raya-graph-minimap-panel h2 {
  color: var(--raya-color-heading);
  font-size: 0.76rem;
  line-height: 1.2;
  margin: 0;
}
.raya-graph-minimap {
  background: color-mix(in srgb, var(--raya-color-surface) 92%, var(--raya-color-accent-soft));
  border: 1px solid var(--raya-color-border);
  border-radius: 0.35rem;
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--raya-color-surface) 70%, white);
  cursor: crosshair;
  display: block;
  height: 6.5rem;
  max-width: min(13.5rem, 100%);
  width: 13.5rem;
}
.raya-graph-minimap:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
.raya-graph-minimap[aria-disabled="true"] {
  cursor: default;
  opacity: 0.68;
}
.raya-graph-minimap-caption {
  color: var(--raya-color-muted);
  font-size: 0.72rem;
  grid-column: 1 / -1;
  line-height: 1.25;
  margin: 0;
}
.raya-graph-minimap-edge {
  stroke: color-mix(in srgb, var(--raya-color-muted) 55%, transparent);
  stroke-width: 1.2;
}
.raya-graph-minimap-node {
  fill: var(--raya-graph-node-color, var(--raya-color-accent));
  opacity: 0.72;
}
.raya-graph-minimap-viewport {
  fill: color-mix(in srgb, var(--raya-color-accent) 13%, transparent);
  stroke: var(--raya-color-accent);
  stroke-width: 2;
}
.raya-graph-preview-bubble {
  background: color-mix(in srgb, var(--raya-color-surface) 94%, var(--raya-color-accent-soft));
  border: 1px solid var(--raya-color-accent);
  border-radius: 0.5rem;
  box-shadow: 0 1rem 2rem color-mix(in srgb, var(--raya-color-text) 18%, transparent);
  color: var(--raya-color-text);
  inline-size: min(19rem, calc(100% - 2rem));
  left: 1rem;
  padding: 0.85rem 0.95rem;
  pointer-events: none;
  position: absolute;
  top: 1rem;
  transform: translate(var(--raya-graph-preview-x, 0), var(--raya-graph-preview-y, 0));
  z-index: 4;
}
.raya-graph-preview-bubble[hidden] {
  display: none;
}
.raya-graph-preview-bubble h2,
.raya-graph-preview-bubble p {
  margin: 0;
}
.raya-graph-preview-bubble h2 {
  font-size: 1rem;
  line-height: 1.25;
}
.raya-graph-preview-kicker,
.raya-graph-preview-counts {
  color: var(--raya-color-muted);
  font-size: 0.78rem;
}
.raya-graph-preview-bubble h2 + p,
.raya-graph-preview-bubble p + p {
  margin-top: 0.35rem;
}
.raya-graph-edge {
  pointer-events: none;
  stroke: var(--raya-graph-edge-color, var(--raya-color-border));
  stroke-opacity: 0.58;
  stroke-width: 2;
  transition: stroke 140ms ease;
}
.raya-graph-edge-hit {
  cursor: help;
  fill: none;
  pointer-events: stroke;
  stroke: transparent;
  stroke-linecap: round;
  stroke-width: 16;
}
.raya-graph-edge-hit:focus-visible {
  outline: none;
  stroke: color-mix(in srgb, var(--raya-color-accent) 34%, transparent);
}
.raya-graph-arrow-marker path {
  fill: var(--raya-graph-edge-color, var(--raya-color-border));
  opacity: 0.68;
}
.raya-graph-arrow-marker.raya-graph-edge-kind-parent path {
  opacity: 0.44;
}
.raya-graph-arrow-marker.is-active path {
  fill: var(--raya-color-accent);
  opacity: 0.86;
}
.raya-graph-arrow-marker.is-search-context path {
  opacity: 0.82;
}
.raya-graph-arrow-marker.is-search-dimmed path {
  opacity: 0.12;
}
.raya-graph-arrow-marker.is-inspected path {
  fill: var(--raya-graph-edge-color, var(--raya-color-success));
  opacity: 0.94;
}
.raya-graph-arrow-marker.is-focus-route path {
  fill: var(--raya-color-accent);
  opacity: 0.96;
}
.raya-graph-arrow-marker.is-dimmed path {
  opacity: 0.14;
}
.raya-graph-arrow-marker.is-selection-muted path {
  opacity: 0.18;
}
.raya-graph-arrow-marker.is-relationship-focus path {
  opacity: 1;
}
.raya-graph-arrow-marker.is-relationship-muted path {
  opacity: 0.22;
}
.raya-graph-edge-kind-navigation {
  stroke-dasharray: none;
}
.raya-graph-edge-kind-content {
  stroke-dasharray: 7 5;
}
.raya-graph-edge-kind-prerequisite {
  stroke-dasharray: 13 6;
  stroke-width: 2.4;
}
.raya-graph-edge-kind-parent {
  stroke-dasharray: 2 5;
  stroke-opacity: 0.44;
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
.raya-graph-edge.is-edge-inspected {
  stroke: var(--raya-color-accent);
  stroke-opacity: 1;
  stroke-width: 4;
}
.raya-graph-edge.is-focus-route {
  stroke: var(--raya-color-accent);
  stroke-opacity: 0.94;
  stroke-width: 3.6;
}
.raya-graph-edge.is-relationship-focus {
  stroke-opacity: 1;
  stroke-width: 3;
}
.raya-graph-edge.is-relationship-muted {
  stroke-opacity: 0.22;
}
.raya-graph-edge.is-dimmed {
  stroke-opacity: 0.14;
}
.raya-graph-edge.is-selection-muted {
  stroke-opacity: 0.18;
}
.raya-graph-node-link {
  cursor: grab;
}
.raya-graph-node.is-dragging .raya-graph-node-mark {
  fill: color-mix(in srgb, var(--raya-graph-node-color, var(--raya-color-accent)) 60%, var(--raya-color-surface));
  stroke-width: 4;
}
.raya-graph-node-hit {
  fill: #000;
  fill-opacity: 0.001;
  pointer-events: all;
  stroke: transparent;
  stroke-width: 0;
}
.raya-graph-node-mark {
  fill: color-mix(in srgb, var(--raya-graph-node-color, var(--raya-color-accent)) 24%, var(--raya-color-surface));
  pointer-events: none;
  stroke: var(--raya-graph-node-color, var(--raya-color-accent));
  stroke-width: 2;
  transition:
    fill 140ms ease,
    filter 140ms ease,
    stroke 140ms ease;
}
.raya-graph-canvas .raya-graph-node-mark {
  filter: drop-shadow(0 0.18rem 0.18rem color-mix(in srgb, var(--raya-color-text) 8%, transparent));
}
.raya-graph-node.is-inspected .raya-graph-node-mark {
  fill: color-mix(in srgb, var(--raya-graph-node-color, var(--raya-color-accent)) 54%, var(--raya-color-surface));
  stroke-width: 4;
}
.raya-graph-node.is-inspected-neighbor .raya-graph-node-mark {
  fill: color-mix(in srgb, var(--raya-graph-node-color, var(--raya-color-accent)) 38%, var(--raya-color-surface));
  stroke-width: 3;
}
.raya-graph-node.is-focus-origin .raya-graph-node-mark {
  fill: color-mix(in srgb, var(--raya-graph-node-color, var(--raya-color-accent)) 58%, var(--raya-color-surface));
  stroke: var(--raya-color-accent);
  stroke-width: 4.5;
  filter: drop-shadow(0 0 0.38rem color-mix(in srgb, var(--raya-color-accent) 36%, transparent));
}
.raya-graph-node.is-focus-endpoint .raya-graph-node-mark {
  stroke: var(--raya-color-accent);
  stroke-width: 3.4;
}
.raya-graph-node.is-edge-endpoint .raya-graph-node-mark {
  fill: color-mix(in srgb, var(--raya-graph-node-color, var(--raya-color-accent)) 48%, var(--raya-color-surface));
  stroke: var(--raya-color-accent);
  stroke-width: 3.6;
}
.raya-graph-node.is-selected .raya-graph-node-mark {
  fill: var(--raya-color-success);
  stroke: var(--raya-color-success);
  stroke-width: 4.5;
  filter:
    drop-shadow(0 0 0.42rem color-mix(in srgb, var(--raya-color-success) 42%, transparent))
    drop-shadow(0 0.24rem 0.22rem color-mix(in srgb, var(--raya-color-text) 14%, transparent));
}
.raya-graph-node.is-neighbor .raya-graph-node-mark {
  fill: color-mix(in srgb, var(--raya-color-accent-soft) 58%, var(--raya-color-success));
  stroke: var(--raya-color-accent);
  stroke-width: 3;
}
.raya-graph-node.is-match .raya-graph-node-mark {
  stroke-width: 4;
}
.raya-graph-node.is-search-context .raya-graph-node-mark {
  fill: color-mix(in srgb, var(--raya-graph-node-color, var(--raya-color-accent)) 34%, var(--raya-color-surface));
}
.raya-graph-node text {
  fill: var(--raya-color-text);
  font-size: 0.78rem;
  font-weight: 700;
  opacity: 0;
  paint-order: stroke;
  pointer-events: none;
  stroke: color-mix(in srgb, var(--raya-color-surface) 88%, var(--raya-color-page));
  stroke-linejoin: round;
  stroke-width: 3.5px;
  text-anchor: middle;
  transition: opacity 140ms ease;
  visibility: hidden;
}
.raya-graph-node.is-label-visible text,
.raya-graph-node.is-selected text,
.raya-graph-node.is-neighbor text,
.raya-graph-node.is-inspected text,
.raya-graph-node.is-inspected-neighbor text,
.raya-graph-node.is-match text,
.raya-graph-node.is-search-context text,
.raya-graph-node.is-dragging text {
  opacity: 1;
  visibility: visible;
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
  padding-left: 0;
}
.raya-graph-list li {
  border: 1px solid var(--raya-color-border);
  border-left: 4px solid var(--raya-color-accent);
  border-radius: 0.5rem;
  break-inside: avoid;
  display: block;
  margin: 0 0 0.65rem;
  padding: 0.7rem 0.75rem;
}
.raya-graph-list-title-row {
  align-items: flex-start;
  display: flex;
  gap: 0.5rem;
  justify-content: space-between;
}
.raya-graph-list-title-row a {
  font-weight: 850;
  min-width: 0;
}
.raya-graph-list-status {
  border: 1px solid var(--raya-color-border);
  border-radius: 999px;
  color: var(--raya-color-muted);
  flex: 0 0 auto;
  font-size: 0.72rem;
  font-weight: 800;
  line-height: 1;
  padding: 0.25rem 0.45rem;
  text-transform: uppercase;
}
.raya-graph-list-search-role {
  background: color-mix(in srgb, var(--raya-color-accent) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 45%, var(--raya-color-border));
  border-radius: 999px;
  color: var(--raya-color-accent);
  flex: 0 0 auto;
  font-size: 0.72rem;
  font-weight: 850;
  line-height: 1;
  padding: 0.25rem 0.45rem;
}
.raya-graph-list-search-role[hidden] {
  display: none;
}
.raya-graph-list-metrics {
  color: var(--raya-color-muted);
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.65rem;
  font-size: 0.84rem;
  line-height: 1.35;
  margin-top: 0.35rem;
}
.raya-graph-list-summary {
  color: var(--raya-color-muted);
  display: block;
  font-size: 0.9rem;
  line-height: 1.45;
  margin-top: 0.45rem;
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
@media (max-width: 720px) {
  .raya-graph-preview-bubble {
    display: none;
  }
}
.raya-learning-shell {
  display: grid;
  gap: 0.875rem;
  grid-template-areas: "course-map main-article learning-rail";
  grid-template-columns: minmax(13.75rem, 16rem) minmax(0, 1fr) minmax(16rem, 18rem);
  /* grid-template-columns is transitioned (below) for smooth rail/map
     collapse, but that same transition also fires when a responsive
     breakpoint is crossed by a plain viewport resize (media queries are
     just computed-value changes to a transition-aware property). Column
     tracks then animate from a wider band's resolved px values down to
     this band's, and because the viewport itself snaps to its new width
     instantly while the 220ms transition catches up, the *sum* of
     mid-transition track widths can briefly exceed the (already-narrower)
     viewport before settling. overflow-x: clip (not hidden, so it doesn't
     also touch overflow-y or break the rail/map position: sticky, which
     only cares about the vertical axis) contains that transient overshoot
     without affecting the settled layout or any content's own horizontal
     scroll (mjx-container, pre, tables keep their own overflow-x: auto). */
  overflow-x: clip;
}
html[data-raya-shell-ready="true"] .raya-learning-shell {
  transition: grid-template-columns 220ms ease, gap 220ms ease;
}
.raya-course-map {
  align-self: start;
  grid-area: course-map;
  max-height: calc(100vh - 2rem);
  overflow: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
}
html[data-raya-shell-ready="true"] .raya-course-map {
  transition: border-color 180ms ease, box-shadow 180ms ease, max-height 180ms ease, opacity 180ms ease, transform 220ms ease, width 220ms ease;
}
.raya-main-article {
  grid-area: main-article;
  font-size: calc(1rem * var(--raya-reader-text-scale, 1));
  justify-self: stretch;
  max-width: none;
  width: 100%;
}
.raya-learning-rail {
  align-content: start;
  align-self: start;
  grid-area: learning-rail;
  font-size: calc(1rem * var(--raya-reader-text-scale, 1));
  max-height: calc(100vh - 2rem);
  overflow: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
}
html[data-raya-shell-ready="true"] .raya-learning-rail {
  transition: border-color 180ms ease, box-shadow 180ms ease, opacity 180ms ease, transform 220ms ease, width 220ms ease;
}
.raya-course-map,
.raya-learning-rail,
.raya-inspection-main {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  min-width: 0;
}
.raya-main-article {
  background: var(--raya-color-surface);
  border-block: 1px solid color-mix(in srgb, var(--raya-color-border) 42%, transparent);
  border-radius: 0;
  min-width: 0;
}
.raya-course-map,
.raya-learning-rail {
  background: color-mix(in srgb, var(--raya-color-surface) 86%, var(--raya-color-page));
  border-color: color-mix(in srgb, var(--raya-color-border) 62%, var(--raya-color-page));
  box-shadow: 0 0.5rem 1.25rem rgba(31, 35, 40, 0.035);
}
.raya-course-map,
.raya-learning-rail {
  position: sticky;
  top: 1rem;
}
.raya-course-map,
.raya-main-article,
.raya-learning-rail,
.raya-inspection-main {
  padding: var(--raya-space-panel);
}
.raya-region-title,
.raya-rail-title {
  color: var(--raya-color-text);
  font-family: var(--raya-font-heading), var(--raya-font-body), -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 0.875rem;
  font-weight: 700;
  line-height: 1.2;
  margin: 0 0 0.75rem;
}
.raya-course-map-header,
.raya-learning-rail-header {
  align-items: center;
  border-bottom: 1px solid var(--raya-color-border);
  display: flex;
  gap: 0.75rem;
  justify-content: space-between;
  margin-bottom: 0.25rem;
  min-height: 2.9375rem;
  padding-bottom: 0.75rem;
}
.raya-course-map-body {
  display: flex;
  flex-direction: column;
}
.raya-course-map-expand {
  display: none;
}
@media (min-width: __RAYA_STRUCTURAL_PX__px) {
  .raya-course-map-collapse {
    display: inline-flex;
  }
  /* Collapsed-appearance (container geometry, header/body display:none,
     expand chip) lives in ONE place: the
     "rail collapse: appearance (single source)" region below. */
}
@media (max-width: 639px) {
  .raya-course-map-expand,
  .raya-course-map-collapse {
    display: none;
  }
}
.raya-course-map-drawer-chrome {
  grid-column: 1 / -1;
}
.raya-course-map-header .raya-region-title,
.raya-learning-rail-header .raya-region-title {
  hyphens: none;
  margin-bottom: 0;
  min-width: 0;
  overflow-wrap: normal;
  word-break: normal;
}
@media (min-width: __RAYA_APPROVED_PX__px) {
  .raya-course-map-header,
  .raya-learning-rail-header {
    min-height: 3.9375rem;
  }
}
.raya-course-map > .raya-page-position {
  color: var(--raya-color-muted);
  font-size: 0.82rem;
  font-weight: 700;
  line-height: 1.2;
  margin: 0 0 0.35rem;
}
.raya-learning-rail-body {
  display: grid;
  gap: 0;
}
.raya-learning-rail-context-chip {
  display: none;
}
.raya-course-map-collapse,
.raya-course-map-expand,
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
[data-raya-learning-rail="expanded"] .raya-learning-rail[data-raya-learning-rail-transition="expanding"] .raya-learning-rail-header,
.raya-learning-rail[data-raya-learning-rail="expanded"][data-raya-learning-rail-transition="expanding"] .raya-learning-rail-header {
  display: none;
}
[data-raya-learning-rail="expanded"] .raya-learning-rail[data-raya-learning-rail-transition="expanding"] .raya-learning-rail-body,
.raya-learning-rail[data-raya-learning-rail="expanded"][data-raya-learning-rail-transition="expanding"] .raya-learning-rail-body {
  display: grid;
  pointer-events: none;
  visibility: hidden;
}
[data-raya-learning-rail="expanded"] .raya-learning-rail[data-raya-learning-rail-transition="expanding"] .raya-learning-rail-expand,
.raya-learning-rail[data-raya-learning-rail="expanded"][data-raya-learning-rail-transition="expanding"] .raya-learning-rail-expand {
  align-items: center;
  align-self: stretch;
  display: inline-flex;
  font-size: 0;
  gap: 0.55rem;
  justify-content: center;
  min-height: 9rem;
  min-width: 3rem;
  overflow: hidden;
  padding: 0.7rem 0.45rem;
  position: relative;
  width: 100%;
}
[data-raya-learning-rail="expanded"] .raya-learning-rail[data-raya-learning-rail-transition="expanding"] .raya-learning-rail-expand::before,
.raya-learning-rail[data-raya-learning-rail="expanded"][data-raya-learning-rail-transition="expanding"] .raya-learning-rail-expand::before {
  background: var(--raya-color-accent);
  border: 1px solid color-mix(in srgb, var(--raya-color-success) 48%, var(--raya-color-accent));
  border-radius: 999px;
  box-shadow: 0 0 0.65rem color-mix(in srgb, var(--raya-color-accent) 34%, transparent);
  content: "";
  display: block;
  height: 0.65rem;
  width: 0.65rem;
}
[data-raya-learning-rail="expanded"] .raya-learning-rail[data-raya-learning-rail-transition="expanding"] .raya-learning-rail-expand::after,
.raya-learning-rail[data-raya-learning-rail="expanded"][data-raya-learning-rail-transition="expanding"] .raya-learning-rail-expand::after {
  content: "Context";
  font-size: 0.8125rem;
  font-weight: 900;
  line-height: 1;
  text-transform: uppercase;
}
.raya-course-map-collapse:focus-visible,
.raya-course-map-expand:focus-visible,
.raya-learning-rail-collapse:focus-visible,
.raya-learning-rail-expand:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 2px;
}
.raya-course-map-list {
  min-height: 0;
  display: grid;
  gap: 0.15rem;
  overflow: auto;
  overscroll-behavior: contain;
  padding-right: 0.2rem;
  scrollbar-gutter: stable;
}
.raya-course-rail-tools {
  border-bottom: 1px solid color-mix(in srgb, var(--raya-color-border) 72%, transparent);
  display: grid;
  gap: 0.3125rem;
  padding: 0.5rem 0.75rem;
}
.raya-course-rail-search.raya-command-search-form {
  display: flex;
  gap: 0.375rem;
  min-width: 0;
  width: 100%;
}
.raya-course-rail-search .raya-command-search-input,
.raya-course-rail-search .raya-command-search-submit {
  min-height: 2.25rem;
}
.raya-course-rail-command-list {
  display: grid;
  gap: 0.3125rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.raya-course-rail-command {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-surface) 94%, var(--raya-color-page));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 84%, transparent);
  border-radius: 0.4375rem;
  color: var(--raya-color-text);
  display: inline-flex;
  gap: 0.375rem;
  justify-content: flex-start;
  min-height: 1.75rem;
  padding: 0.25rem 0.4375rem;
  text-align: left;
  text-decoration: none;
  width: 100%;
}
.raya-course-rail-command[aria-current="page"],
.raya-course-rail-command[aria-pressed="true"] {
  background: color-mix(in srgb, var(--raya-color-accent-soft) 38%, var(--raya-color-surface));
  border-color: color-mix(in srgb, var(--raya-color-accent) 34%, var(--raya-color-border));
}
.raya-course-rail-command:hover {
  background: color-mix(in srgb, var(--raya-color-accent-soft) 52%, var(--raya-color-surface));
}
.raya-course-rail-command:focus-visible {
  background: color-mix(in srgb, var(--raya-color-accent-soft) 58%, var(--raya-color-surface));
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--raya-color-accent) 26%, transparent);
}
.raya-course-rail-command .raya-command-icon {
  background: color-mix(in srgb, currentColor 12%, transparent);
  border: 1px solid color-mix(in srgb, currentColor 28%, transparent);
  flex: 0 0 auto;
  height: 0.9375rem;
  padding: 0.1rem;
  width: 0.9375rem;
}
.raya-course-rail-command .raya-command-label {
  display: inline;
  font-size: 0.75rem;
  font-weight: 700;
  line-height: 1.2;
  min-width: 0;
  overflow-wrap: anywhere;
}
.raya-course-rail-command.raya-command-search {
  color: var(--raya-color-accent);
}
.raya-course-rail-command.raya-command-graph {
  color: color-mix(in srgb, var(--raya-color-accent) 78%, var(--raya-color-text));
}
.raya-course-rail-command.raya-command-practice {
  color: var(--raya-color-success);
}
.raya-course-rail-command.raya-command-tasks {
  color: var(--raya-color-warning);
}
.raya-course-rail-command.raya-command-schedule {
  color: color-mix(in srgb, var(--raya-color-warning) 56%, var(--raya-color-text));
}
.raya-course-rail-command.raya-command-context {
  color: color-mix(in srgb, var(--raya-color-success) 72%, var(--raya-color-accent));
}
.raya-course-rail-command.raya-text-size-toggle {
  color: var(--raya-color-text);
}
.raya-course-rail-command.raya-font-toggle {
  color: color-mix(in srgb, var(--raya-color-accent) 54%, var(--raya-color-text));
}
.raya-course-map-close {
  background: color-mix(in srgb, var(--raya-color-accent-soft) 72%, var(--raya-color-surface));
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  cursor: pointer;
  font: inherit;
  font-size: 0.78rem;
  font-weight: 800;
  line-height: 1;
  padding: 0.38rem 0.52rem;
}
.raya-course-map-close:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 2px;
}
.raya-course-map-close,
.raya-course-map-drawer-backdrop,
.raya-learning-rail-drawer-backdrop {
  display: none;
}
.raya-course-map-drawer-chrome {
  display: none;
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
.raya-course-map-header-toggle,
.raya-course-map-expand {
  align-items: center;
  height: 2.5rem;
  justify-content: center;
  min-height: 2.5rem;
  min-width: 2.5rem;
  padding: 0;
  width: 2.5rem;
}
.raya-course-map-header-toggle {
  grid-column: 2;
  grid-row: 2 / span 2;
  justify-self: end;
}
.raya-course-map-header-toggle .raya-command-icon {
  background: none;
  border: 0;
  border-radius: 0;
  height: 1rem;
  padding: 0;
  width: 1rem;
}
.raya-course-map-header-toggle .raya-command-label {
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  height: 1px;
  overflow: hidden;
  position: absolute;
  white-space: nowrap;
  width: 1px;
}
html[data-raya-shell-ready="true"] .raya-course-map-toggle,
html[data-raya-shell-ready="true"] .raya-course-map-collapse,
html[data-raya-shell-ready="true"] .raya-course-map-expand,
html[data-raya-shell-ready="true"] .raya-learning-rail-expand {
  transition: background-color 180ms ease, border-color 180ms ease, box-shadow 180ms ease, color 180ms ease;
}
.raya-course-map-toggle:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 2px;
}
.raya-reading-context-ancestors {
  align-items: center;
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.2rem;
  min-width: 0;
}
.raya-reading-context-ancestor-label {
  overflow-wrap: anywhere;
}
.raya-rail-toggle {
  align-items: center;
  background: transparent;
  border: 0;
  border-radius: 0.3rem;
  color: inherit;
  cursor: pointer;
  display: flex;
  font: inherit;
  font-weight: 700;
  justify-content: space-between;
  min-height: 2rem;
  padding: 0.2rem 0;
  text-align: left;
  width: 100%;
}
.raya-rail-toggle::after {
  align-items: center;
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 999px;
  content: "+";
  display: inline-flex;
  font-weight: 700;
  height: 1.35rem;
  justify-content: center;
  margin-left: 0.75rem;
  min-width: 1.35rem;
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
html[data-raya-course-map-scroll-lock="true"],
html[data-raya-course-map-scroll-lock="true"] body,
html[data-raya-learning-rail-scroll-lock="true"],
html[data-raya-learning-rail-scroll-lock="true"] body {
  overflow: hidden;
}
@media (prefers-reduced-motion: reduce) {
  html[data-raya-shell-ready="true"] .raya-learning-shell,
  html[data-raya-shell-ready="true"] .raya-course-map,
  html[data-raya-shell-ready="true"] .raya-learning-rail,
  html[data-raya-shell-ready="true"] .raya-course-map-toggle,
  html[data-raya-shell-ready="true"] .raya-course-map-collapse,
  html[data-raya-shell-ready="true"] .raya-course-map-expand,
  html[data-raya-shell-ready="true"] .raya-learning-rail-expand,
  html[data-raya-shell-ready="true"] .raya-rail-panel-body {
    transition: none;
  }
}
.raya-rail-panel-body-inner {
  min-height: 0;
  min-width: 0;
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
  border-top: 1px solid color-mix(in srgb, var(--raya-color-border) 78%, transparent);
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 2.25rem;
  min-width: 0;
  padding-top: 1.15rem;
  width: 100%;
}
.raya-sequence-card {
  background: color-mix(in srgb, var(--raya-color-surface) 84%, var(--raya-color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 40%, var(--raya-color-border));
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  display: grid;
  gap: 0.4rem;
  min-height: 6rem;
  min-width: 0;
  padding: 1rem;
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
  background: color-mix(in srgb, var(--raya-color-surface) 92%, var(--raya-color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 38%, var(--raya-color-border));
  border-radius: 0.375rem;
  margin-top: 2.25rem;
  min-width: 0;
  padding: 1.05rem;
  width: 100%;
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
  gap: 0.9rem;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));
  min-width: 0;
}
.raya-article-connections-section {
  background: var(--raya-color-surface);
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 82%, var(--raya-color-accent-soft));
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
.raya-connection-preview summary::marker {
  color: var(--raya-color-accent);
}
.raya-connection-preview-meta {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}
.raya-connection-preview-kind,
.raya-connection-preview-direction {
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 42%, var(--raya-color-border));
  border-radius: 999px;
  display: inline-flex;
  font-size: 0.7rem;
  font-weight: 900;
  line-height: 1;
  padding: 0.24rem 0.42rem;
}
.raya-connection-preview-kind {
  background: var(--raya-color-accent);
  color: var(--raya-color-accent-text);
}
.raya-connection-preview-direction {
  background: color-mix(in srgb, var(--raya-color-accent-soft) 76%, var(--raya-color-surface));
  color: var(--raya-color-text);
}
.raya-connection-preview-title {
  display: block;
  margin-top: 0.35rem;
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
.raya-connection-preview-direction-note {
  color: var(--raya-color-muted);
  font-size: 0.84rem;
  line-height: 1.4;
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
.raya-official-practice-actions {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0;
}
.raya-official-practice-open {
  background: var(--raya-color-accent);
  border: 1px solid var(--raya-color-accent);
  border-radius: 999px;
  color: var(--raya-color-surface);
  display: inline-flex;
  font-size: 0.86rem;
  font-weight: 850;
  line-height: 1;
  padding: 0.55rem 0.75rem;
  text-decoration: none;
}
.raya-official-practice-open:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
.raya-official-object {
  --raya-official-accent: var(--raya-color-accent);
  --raya-official-accent-text: var(--raya-color-surface);
  --raya-official-soft: color-mix(in srgb, var(--raya-official-accent) 14%, var(--raya-color-surface));
  background: color-mix(in srgb, var(--raya-color-surface) 88%, var(--raya-official-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 68%, var(--raya-official-accent));
  border-left: 0.35rem solid var(--raya-official-accent);
  border-radius: 0.5rem;
  display: grid;
  gap: 0.75rem;
  padding: 1rem;
  scroll-margin-top: 32rem;
}
.raya-official-card {
  --raya-official-accent: var(--raya-color-success);
  --raya-official-accent-text: var(--raya-color-surface);
}
.raya-official-quiz {
  --raya-official-accent: var(--raya-color-danger);
  --raya-official-accent-text: var(--raya-color-surface);
}
.raya-official-assignment,
.raya-official-task {
  --raya-official-accent: var(--raya-color-warning);
  --raya-official-accent-text: var(--raya-color-surface);
}
.raya-official-exam {
  --raya-official-accent: color-mix(in srgb, var(--raya-color-danger) 78%, var(--raya-color-accent));
  --raya-official-accent-text: var(--raya-color-surface);
}
.raya-official-project,
.raya-official-example {
  --raya-official-accent: color-mix(in srgb, var(--raya-color-success) 72%, var(--raya-color-accent));
  --raya-official-accent-text: var(--raya-color-surface);
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
  background: var(--raya-official-accent);
  color: var(--raya-official-accent-text);
}
.raya-official-authority {
  background: var(--raya-official-soft);
  border: 1px solid color-mix(in srgb, var(--raya-official-accent) 42%, var(--raya-color-border));
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
.raya-official-options > li {
  margin-block: 0.2rem;
}
.raya-official-option {
  background: var(--raya-color-surface);
  border: 1px solid color-mix(in srgb, var(--raya-official-accent) 32%, var(--raya-color-border));
  border-radius: 0.45rem;
  color: var(--raya-color-text);
  cursor: pointer;
  display: block;
  font: inherit;
  font-weight: 700;
  line-height: 1.35;
  padding: 0.6rem 0.75rem;
  text-align: left;
  width: 100%;
}
.raya-official-option:disabled {
  cursor: default;
}
.raya-official-option:focus-visible,
.raya-official-quiz-reset:focus-visible {
  outline: 3px solid var(--raya-official-accent);
  outline-offset: 3px;
}
.raya-official-option[data-raya-official-quiz-result="correct"] {
  background: color-mix(in srgb, var(--raya-color-success) 18%, var(--raya-color-surface));
  border-color: var(--raya-color-success);
}
.raya-official-option[data-raya-official-quiz-result="incorrect"] {
  background: color-mix(in srgb, var(--raya-color-danger) 14%, var(--raya-color-surface));
  border-color: var(--raya-color-danger);
}
.raya-official-quiz-feedback {
  font-weight: 800;
  margin: 0;
}
.raya-official-quiz-reset {
  justify-self: start;
}
.raya-official-reveal {
  background: color-mix(in srgb, var(--raya-official-soft) 56%, var(--raya-color-surface));
  border: 1px solid color-mix(in srgb, var(--raya-official-accent) 30%, var(--raya-color-border));
  border-radius: 0.375rem;
  padding: 0.55rem 0.75rem;
}
.raya-official-reveal summary {
  cursor: pointer;
  font-weight: 800;
}
.raya-official-reveal summary:focus-visible {
  outline: 3px solid var(--raya-official-accent);
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
  padding-top: 0.55rem;
}
.raya-article-connection-title {
  min-width: 0;
}
.raya-article-connection-actions {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin: 0.45rem 0 0;
  min-width: 0;
}
.raya-article-connection-kind,
.raya-article-connection-direction {
  border: 1px solid var(--raya-color-border);
  border-radius: 999px;
  color: var(--raya-color-muted);
  display: inline-flex;
  font-size: 0.72rem;
  font-weight: 800;
  line-height: 1;
  padding: 0.22rem 0.42rem;
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
.raya-reading-flow-grid {
  display: grid;
  gap: 0.5rem;
  min-width: 0;
}
.raya-reading-flow-link {
  background: color-mix(in srgb, var(--raya-color-accent-soft) 60%, var(--raya-color-surface));
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 46%, var(--raya-color-border));
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  display: grid;
  gap: 0.12rem;
  min-width: 0;
  padding: 0.45rem 0.5rem;
  text-decoration: none;
}
.raya-reading-flow-link:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 2px;
}
.raya-reading-flow-link-label {
  color: var(--raya-color-muted);
  font-size: 0.68rem;
  font-weight: 850;
  line-height: 1;
  text-transform: uppercase;
}
.raya-reading-flow-link-title {
  font-size: 0.84rem;
  font-weight: 800;
  line-height: 1.18;
  overflow-wrap: break-word;
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
  gap: 0.28rem;
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
  overflow-wrap: break-word;
}
.raya-course-map-list a {
  border-left: 3px solid transparent;
  display: block;
  min-width: 0;
  overflow-wrap: break-word;
  padding: 0.25rem 0 0.25rem 0.5rem;
  text-decoration: none;
}
.raya-course-map-list a::before {
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
  margin-right: 0.45rem;
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
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-top-command-bar-inner {
    align-items: center;
    flex-wrap: nowrap;
    gap: 0.65rem;
    padding-block: 0.45rem;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context {
    flex: 1 1 24rem;
    flex-wrap: nowrap;
    max-width: min(38rem, 40vw);
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context-course,
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context-page {
    flex: 0 1 auto;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context-section {
    max-width: min(18rem, 22vw);
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-course-tools {
    flex: 0 1 auto;
    flex-wrap: nowrap;
    max-width: calc(100% - 24rem);
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-group {
    align-self: center;
    flex-wrap: nowrap;
    gap: 0.25rem;
    padding: 0.15rem;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-group-discovery {
    flex: 0 1 auto;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-search-form {
    flex: 0 1 12rem;
    min-width: 8.5rem;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-search-input,
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-search-submit {
    height: 2.2rem;
    min-height: 2.2rem;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command {
    gap: 0.25rem;
    min-height: 2.3rem;
    min-width: 2.5rem;
    padding: 0.35rem 0.45rem;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-icon {
    height: 1.25rem;
    padding: 0.14rem;
    width: 1.25rem;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-label {
    clip: rect(0 0 0 0);
    height: 1px;
    overflow: hidden;
    position: absolute;
    white-space: nowrap;
    width: 1px;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-size .raya-command-label,
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-font .raya-command-label {
    clip: auto;
    clip-path: none;
    height: auto;
    overflow: visible;
    position: static;
    white-space: nowrap;
    width: auto;
  }
}
@media (min-width: 1800px) {
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-label {
    clip: auto;
    clip-path: none;
    height: auto;
    overflow: visible;
    position: static;
    white-space: nowrap;
    width: auto;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command {
    gap: 0.38rem;
    min-width: 0;
    padding-inline: 0.55rem;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-group {
    gap: 0.3rem;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-search-form {
    flex-basis: 10rem;
    min-width: 10rem;
  }
}
@media (max-width: 639px) {
  .raya-mobile-course-map-open.raya-command {
    align-items: center;
    background: var(--raya-color-accent-soft);
    border: 1px solid var(--raya-color-border);
    border-radius: 0.375rem;
    box-shadow: 0 0.5rem 1.2rem color-mix(in srgb, var(--raya-color-text) 18%, transparent);
    color: var(--raya-color-text);
    display: inline-flex;
    gap: 0.35rem;
    margin: 0.75rem 0 1rem 0.75rem;
    min-height: 2.35rem;
    padding: 0.42rem 0.6rem;
    position: static;
    z-index: 7;
  }
  .raya-mobile-course-map-open:focus-visible {
    outline: 3px solid var(--raya-color-accent);
    outline-offset: 3px;
  }
  html[data-raya-course-map-drawer="closed"] .raya-course-rail-tools {
    display: none;
  }
  html[data-raya-course-map-drawer="open"] .raya-course-rail-tools {
    display: grid;
  }
  .raya-course-rail-command-list .raya-command-context {
    display: none;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-context {
    display: none;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-course-tools {
    align-items: stretch;
    flex-wrap: wrap;
    justify-content: flex-start;
    overflow-x: visible;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-group {
    flex-wrap: wrap;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-group-discovery {
    flex: 1 1 100%;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-search-form {
    order: -1;
    width: 100%;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-search-input {
    flex: 1 1 auto;
  }
}
@media (min-width: __RAYA_APPROVED_PX__px) {
  /* In-flow token grid (single 894 boundary). Rail tracks are driven by
     CSS custom properties keyed off the html[data-raya-*] state, not by
     four literal grid-template-columns branches: each rail contributes a
     15rem content track plus its own 1.5rem gutter track when expanded,
     and 0 for both when collapsed. column-gap is pinned to 0 so a
     collapsed (0-width) track never leaves a phantom gap behind it — the
     gutter is baked into the *-gap custom property instead, which zeroes
     together with the content track. The article track floor is
     minmax(0, 1fr) here on purpose: the comfortable 42rem floor is only
     safe to reintroduce once the viewport is wide enough (see the
     __RAYA_DESKTOP_PX__ layer below) — reusing it here is the overflow
     trap this layer exists to avoid. */
  html[data-raya-course-map="expanded"] {
    --raya-map-col: 15rem;
    --raya-map-gap: 1.5rem;
  }
  html[data-raya-course-map="collapsed"] {
    --raya-map-col: 0;
    --raya-map-gap: 0;
  }
  html[data-raya-learning-rail="expanded"] {
    --raya-rail-col: 15rem;
    --raya-rail-gap: 1.5rem;
  }
  html[data-raya-learning-rail="collapsed"] {
    --raya-rail-col: 0;
    --raya-rail-gap: 0;
  }
  .raya-learning-shell {
    column-gap: 0;
    grid-template-areas: "course-map . main-article . learning-rail";
    grid-template-columns:
      var(--raya-map-col) var(--raya-map-gap) minmax(0, 1fr)
      var(--raya-rail-gap) var(--raya-rail-col);
  }
  html[data-raya-course-map="collapsed"] .raya-learning-shell {
    padding-left: 3.75rem;
  }
  html[data-raya-learning-rail="collapsed"] .raya-learning-shell {
    padding-right: 3.75rem;
  }
  /* Collapsed header/body display:none lives in the single "rail collapse:
     appearance" region (not band-scoped here — it's width-invariant). */
  [data-raya-learning-rail="collapsed"] .raya-learning-rail[data-raya-learning-rail-transition="collapsing"] .raya-learning-rail-body,
  .raya-learning-rail[data-raya-learning-rail="collapsed"][data-raya-learning-rail-transition="collapsing"] .raya-learning-rail-body {
    display: block;
    pointer-events: none;
    visibility: hidden;
  }
  [data-raya-course-map="expanded"] .raya-course-map[data-raya-course-map-transition="expanding"] .raya-course-map-list,
  .raya-course-map[data-raya-course-map="expanded"][data-raya-course-map-transition="expanding"] .raya-course-map-list {
    display: grid;
    pointer-events: none;
    visibility: hidden;
  }
}
@media (min-width: __RAYA_DESKTOP_PX__px) {
  /* Comfort layer: reintroduce the 42rem article floor only once the
     viewport is wide enough to afford it (15rem map + 1.5rem gap + 42rem
     article + 1.5rem gap + 15rem rail = 75rem = 1200px, which fits under
     the 1280px trigger). Everything else (token columns, gutters, gap
     zeroing, collapsed padding push) is inherited unchanged from the
     __RAYA_APPROVED_PX__ layer above. */
  .raya-learning-shell {
    grid-template-columns:
      var(--raya-map-col) var(--raya-map-gap) minmax(42rem, 1fr)
      var(--raya-rail-gap) var(--raya-rail-col);
  }
  .raya-main-article {
    border: 1px solid color-mix(in srgb, var(--raya-color-border) 58%, transparent);
    border-radius: 0.5rem;
    padding: clamp(1.75rem, 1vw + 1rem, 2rem);
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
.raya-page-brief-path .raya-page-brief-value,
.raya-page-brief-prerequisites .raya-page-brief-value,
.raya-page-brief-connections .raya-page-brief-value,
.raya-page-brief-practice .raya-page-brief-value {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.raya-page-brief-value a {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-accent-soft) 76%, var(--raya-color-surface));
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 54%, var(--raya-color-border));
  border-radius: 999px;
  color: var(--raya-color-text);
  display: inline-flex;
  font-weight: 800;
  line-height: 1.15;
  max-width: 100%;
  min-height: 1.9rem;
  overflow-wrap: anywhere;
  padding: 0.34rem 0.58rem;
  text-decoration: none;
}
.raya-page-brief-value a:hover {
  background: color-mix(in srgb, var(--raya-color-accent-soft) 62%, var(--raya-color-surface));
  border-color: var(--raya-color-accent);
}
.raya-page-brief-value a:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
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
  align-content: start;
  display: grid;
  gap: 0;
}
.raya-rail-panel {
  border-bottom: 1px solid color-mix(in srgb, var(--raya-color-border) 76%, transparent);
  min-width: 0;
  padding: 0.75rem 0;
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
.raya-current-section {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  margin: 0 0 0.75rem;
  padding: 0.65rem 0.75rem;
}
.raya-current-section-label {
  color: var(--raya-color-muted);
  display: block;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0;
  margin-bottom: 0.25rem;
}
.raya-current-section-link {
  color: var(--raya-color-accent);
  font-weight: 700;
  text-decoration-thickness: 0.08em;
  text-underline-offset: 0.16em;
}
.raya-current-section-link:focus-visible {
  outline: 2px solid var(--raya-color-accent);
  outline-offset: 3px;
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
.raya-page-toc-objects {
  border-top: 1px solid var(--raya-color-border);
  margin-top: 0.85rem;
  padding-top: 0.75rem;
}
.raya-page-toc-objects-title {
  color: var(--raya-color-muted);
  font-size: 0.78rem;
  font-weight: 800;
  margin: 0 0 0.45rem;
}
.raya-page-toc-object-list {
  display: grid;
  gap: 0.32rem;
  margin: 0;
  max-height: 11.5rem;
  overflow: auto;
  padding-left: 1.1rem;
}
.raya-page-toc-object-item a {
  display: inline-block;
  line-height: 1.35;
  overflow-wrap: anywhere;
}
.raya-page-toc-object-item a[aria-current="location"] {
  background: color-mix(in srgb, var(--raya-color-accent) 12%, transparent);
  border: 1px solid var(--raya-color-accent);
  border-radius: 0.25rem;
  color: var(--raya-color-text);
  margin-left: -0.2rem;
  padding: 0.08rem 0.2rem;
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
  --raya-numbered-accent: var(--raya-color-accent);
  --raya-numbered-soft: color-mix(in srgb, var(--raya-numbered-accent) 13%, var(--raya-color-surface));
  --raya-numbered-border: color-mix(in srgb, var(--raya-color-border) 72%, var(--raya-numbered-accent));
  border: 1px solid var(--raya-numbered-border);
  margin: 1.25rem 0;
}
.raya-numbered-object--theorem,
.raya-numbered-object--lemma,
.raya-numbered-object--proposition,
.raya-numbered-object--corollary {
  --raya-numbered-accent: var(--raya-color-success);
}
.raya-numbered-object--definition {
  --raya-numbered-accent: var(--raya-color-accent);
}
.raya-numbered-object--problem,
.raya-numbered-object--activity,
.raya-numbered-object--exercise {
  --raya-numbered-accent: var(--raya-color-warning);
}
.raya-numbered-object--example,
.raya-numbered-object--remark {
  --raya-numbered-accent: color-mix(in srgb, var(--raya-color-success) 64%, var(--raya-color-accent));
}
.raya-numbered-object--figure,
.raya-numbered-object--table,
.raya-numbered-object--equation {
  --raya-numbered-accent: var(--raya-color-muted);
}
.raya-numbered-object-heading {
  align-items: baseline;
  background: var(--raya-numbered-soft);
  border-bottom: 1px solid var(--raya-numbered-border);
  display: flex;
  font-family: var(--raya-font-heading), var(--raya-font-body), -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  flex-wrap: wrap;
  gap: 0.35rem 0.5rem;
  margin: 0;
  padding: 0.65rem 0.85rem;
}
.raya-numbered-object-reference {
  color: var(--raya-numbered-accent);
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
  border-left: 0.35rem solid var(--raya-numbered-accent);
}
.raya-numbered-object--banded {
  border-color: var(--raya-numbered-border);
  border-top: 0.35rem solid var(--raya-numbered-accent);
}
.raya-numbered-object--banded .raya-numbered-object-heading {
  background: color-mix(in srgb, var(--raya-numbered-accent) 18%, var(--raya-color-surface));
}
.raya-numbered-object--caption {
  border-color: var(--raya-numbered-border);
}
.raya-numbered-object--caption .raya-numbered-object-heading {
  background: var(--raya-color-surface);
  border-bottom: 0;
  border-top: 1px solid var(--raya-numbered-border);
}
.raya-numbered-object--caption .raya-numbered-object-body {
  background: var(--raya-numbered-soft);
}
.raya-numbered-object--equation {
  border-color: var(--raya-numbered-border);
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
  background: color-mix(in srgb, var(--raya-numbered-accent) 18%, var(--raya-color-surface));
  border-right: 1px solid var(--raya-numbered-border);
  display: grid;
  gap: 0.25rem;
  padding: 0.85rem;
}
.raya-numbered-object-badge-label {
  color: var(--raya-numbered-accent);
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
  .raya-discovery-workspace-shell,
  [data-raya-discovery-rail-state="collapsed"] .raya-discovery-workspace-shell {
    grid-template-columns: minmax(0, 1fr);
  }
  .raya-discovery-course-rail {
    padding: 0.55rem;
    position: static;
  }
  .raya-discovery-course-rail-body {
    gap: 0.5rem;
  }
  .raya-discovery-workspace-links {
    grid-template-columns: repeat(auto-fit, minmax(min(7rem, 100%), 1fr));
  }
  .raya-discovery-workspace-link {
    min-height: 2rem;
    padding: 0.32rem 0.45rem;
  }
  .raya-discovery-workspace-link span {
    font-size: 0.82rem;
  }
  .raya-discovery-course-pages {
    padding-top: 0.45rem;
  }
  .raya-discovery-course-tab,
  [data-raya-discovery-rail-state="collapsed"] .raya-discovery-course-tab {
    display: none;
  }
  [data-raya-discovery-rail-state="collapsed"] .raya-discovery-course-rail {
    display: block;
  }
  [data-raya-discovery-rail-state="collapsed"] .raya-discovery-course-rail-body {
    display: grid;
  }
  .raya-discovery-course-pages ol {
    max-height: 6rem;
    overflow: auto;
  }
  .raya-discovery-course-page-link {
    padding: 0.22rem 0.3rem;
  }
  .raya-discovery-focus-actions {
    justify-content: flex-start;
  }
  .raya-discovery-workspace-shell > .raya-graph-workspace,
  .raya-discovery-workspace-shell > .raya-search-workspace,
  .raya-discovery-workspace-shell > .raya-practice-workspace,
  .raya-discovery-workspace-shell > .raya-tasks-workspace,
  .raya-discovery-workspace-shell > .raya-schedule-workspace {
    grid-template-columns: minmax(0, 1fr);
  }
  .raya-graph-page .raya-discovery-workspace-shell {
    display: flex;
    flex-direction: column;
  }
  .raya-graph-page .raya-discovery-course-rail {
    order: 2;
  }
  .raya-graph-page .raya-graph-legend,
  .raya-graph-page .raya-graph-help {
    order: 3;
  }
  .raya-graph-page .raya-graph-workspace {
    order: 1;
  }
  .raya-graph-workspace,
  [data-raya-graph-list-state="collapsed"] .raya-graph-workspace,
  [data-raya-graph-inspector-state="collapsed"] .raya-graph-workspace,
  [data-raya-graph-list-state="collapsed"][data-raya-graph-inspector-state="collapsed"] .raya-graph-workspace,
  [data-raya-graph-expanded="true"] .raya-graph-workspace {
    grid-template-columns: minmax(0, 1fr);
  }
  .raya-graph-map-panel {
    order: 1;
    max-height: none;
    min-height: 0;
    overflow: visible;
  }
  .raya-graph-instructions {
    display: none;
  }
  .raya-graph-list-panel {
    order: 2;
  }
  .raya-graph-inspector-panel {
    order: 3;
  }
  .raya-search-workspace,
  .raya-practice-workspace,
  .raya-tasks-workspace,
  .raya-schedule-workspace,
  [data-raya-discovery-controls-state="collapsed"] .raya-search-workspace,
  [data-raya-discovery-controls-state="collapsed"] .raya-practice-workspace,
  [data-raya-discovery-controls-state="collapsed"] .raya-tasks-workspace,
  [data-raya-discovery-controls-state="collapsed"] .raya-schedule-workspace,
  [data-raya-discovery-context-state="collapsed"] .raya-search-workspace,
  [data-raya-discovery-context-state="collapsed"] .raya-practice-workspace,
  [data-raya-discovery-context-state="collapsed"] .raya-tasks-workspace,
  [data-raya-discovery-context-state="collapsed"] .raya-schedule-workspace,
  [data-raya-discovery-controls-state="collapsed"][data-raya-discovery-context-state="collapsed"] .raya-search-workspace,
  [data-raya-discovery-controls-state="collapsed"][data-raya-discovery-context-state="collapsed"] .raya-practice-workspace,
  [data-raya-discovery-controls-state="collapsed"][data-raya-discovery-context-state="collapsed"] .raya-tasks-workspace,
  [data-raya-discovery-controls-state="collapsed"][data-raya-discovery-context-state="collapsed"] .raya-schedule-workspace {
    grid-template-columns: minmax(0, 1fr);
  }
  .raya-search-control-panel,
  .raya-search-context-panel,
  .raya-practice-control-panel,
  .raya-practice-context-panel,
  .raya-tasks-control-panel,
  .raya-tasks-context-panel,
  .raya-schedule-control-panel,
  .raya-schedule-context-panel {
    position: static;
  }
  [data-raya-graph-list-state="collapsed"] .raya-graph-list-panel h2,
  [data-raya-graph-inspector-state="collapsed"] .raya-graph-inspector-panel h2 {
    writing-mode: horizontal-tb;
  }
  [data-raya-graph-list-state="collapsed"] .raya-graph-list-panel,
  [data-raya-graph-inspector-state="collapsed"] .raya-graph-inspector-panel {
    align-items: stretch;
    padding: 0.55rem 0.7rem;
  }
  [data-raya-graph-list-state="collapsed"] .raya-graph-list-panel .raya-graph-panel-header,
  [data-raya-graph-inspector-state="collapsed"] .raya-graph-inspector-panel .raya-graph-panel-header {
    flex-direction: row;
    gap: 0.65rem;
    margin-bottom: 0;
  }
  [data-raya-graph-list-state="collapsed"] [data-raya-graph-panel-rail-summary="list"],
  [data-raya-graph-inspector-state="collapsed"] [data-raya-graph-panel-rail-summary="inspector"] {
    flex: 1 1 auto;
    line-clamp: 2;
    max-width: none;
    text-align: left;
  }
  [data-raya-discovery-controls-state="collapsed"] .raya-search-control-panel,
  [data-raya-discovery-controls-state="collapsed"] .raya-practice-control-panel,
  [data-raya-discovery-controls-state="collapsed"] .raya-tasks-control-panel,
  [data-raya-discovery-controls-state="collapsed"] .raya-schedule-control-panel,
  [data-raya-discovery-context-state="collapsed"] .raya-search-context-panel,
  [data-raya-discovery-context-state="collapsed"] .raya-practice-context-panel,
  [data-raya-discovery-context-state="collapsed"] .raya-tasks-context-panel,
  [data-raya-discovery-context-state="collapsed"] .raya-schedule-context-panel {
    align-items: stretch;
    display: block;
  }
  [data-raya-discovery-controls-state="collapsed"] .raya-search-control-panel .raya-discovery-panel-header,
  [data-raya-discovery-controls-state="collapsed"] .raya-practice-control-panel .raya-discovery-panel-header,
  [data-raya-discovery-controls-state="collapsed"] .raya-tasks-control-panel .raya-discovery-panel-header,
  [data-raya-discovery-controls-state="collapsed"] .raya-schedule-control-panel .raya-discovery-panel-header,
  [data-raya-discovery-context-state="collapsed"] .raya-search-context-panel .raya-discovery-panel-header,
  [data-raya-discovery-context-state="collapsed"] .raya-practice-context-panel .raya-discovery-panel-header,
  [data-raya-discovery-context-state="collapsed"] .raya-tasks-context-panel .raya-discovery-panel-header,
  [data-raya-discovery-context-state="collapsed"] .raya-schedule-context-panel .raya-discovery-panel-header {
    flex-direction: row;
  }
  [data-raya-discovery-controls-state="collapsed"] .raya-search-control-panel h2,
  [data-raya-discovery-controls-state="collapsed"] .raya-practice-control-panel h2,
  [data-raya-discovery-controls-state="collapsed"] .raya-tasks-control-panel h2,
  [data-raya-discovery-controls-state="collapsed"] .raya-schedule-control-panel h2,
  [data-raya-discovery-context-state="collapsed"] .raya-search-context-panel h2,
  [data-raya-discovery-context-state="collapsed"] .raya-practice-context-panel h2,
  [data-raya-discovery-context-state="collapsed"] .raya-tasks-context-panel h2,
  [data-raya-discovery-context-state="collapsed"] .raya-schedule-context-panel h2 {
    writing-mode: horizontal-tb;
  }
}
@media (max-width: 519px) {
  .raya-discovery-results-jump {
    display: block;
  }
}
@media (max-width: 639px) {
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
    overflow: auto;
    position: static;
  }
  .raya-course-map,
  .raya-learning-rail {
    max-height: none;
  }
  html[data-raya-course-map-drawer="closed"] .raya-course-map {
    clip: rect(0 0 0 0);
    clip-path: inset(50%);
    height: 1px;
    margin: 0;
    overflow: hidden;
    padding: 0;
    position: absolute;
    white-space: nowrap;
    width: 1px;
  }
  html[data-raya-course-map-drawer="open"] .raya-course-map {
    all: revert;
    background: color-mix(in srgb, var(--raya-color-surface) 86%, var(--raya-color-page));
    border: 1px solid color-mix(in srgb, var(--raya-color-border) 62%, var(--raya-color-page));
    border-radius: 0 0.875rem 0.875rem 0;
    box-sizing: border-box;
    box-shadow: 0 1rem 3rem rgba(0, 0, 0, 0.28);
    color: var(--raya-color-text);
    display: block;
    font-family: var(--raya-font-body), -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 1rem;
    line-height: 1.6;
    left: 0;
    margin: 0;
    max-height: 100vh;
    max-width: calc(100vw - 1rem);
    overflow: auto;
    overscroll-behavior: contain;
    padding: 0;
    position: fixed;
    right: auto;
    scrollbar-gutter: stable;
    top: 0;
    width: min(17.25rem, calc(100vw - 1rem));
    z-index: 80;
  }
  html[data-raya-course-map-drawer="open"] .raya-course-map-header,
  html[data-raya-course-map-drawer="open"] .raya-course-rail-tools,
  html[data-raya-course-map-drawer="open"] .raya-course-map-filter-label,
  html[data-raya-course-map-drawer="open"] .raya-course-map-filter,
  html[data-raya-course-map-drawer="open"] .raya-map-filter-empty,
  html[data-raya-course-map-drawer="open"] .raya-course-map-list {
    margin-left: 0.5rem;
    margin-right: 0.5rem;
  }
  html[data-raya-course-map-drawer="open"] .raya-course-map-header {
    background: color-mix(in srgb, var(--raya-color-surface) 94%, var(--raya-color-page));
    border-bottom: 1px solid color-mix(in srgb, var(--raya-color-border) 70%, transparent);
    display: flex;
    gap: 0.5rem;
    justify-content: space-between;
    margin: 0 0 0.45rem;
    padding: 0.55rem 0.65rem;
    position: sticky;
    top: 0;
    z-index: 2;
  }
  html[data-raya-course-map-drawer="open"] .raya-course-map-header > .raya-region-title,
  html[data-raya-course-map-drawer="open"] .raya-course-map-header > .raya-page-position,
  html[data-raya-course-map-drawer="open"] .raya-course-map-header > .raya-course-map-toggle,
  html[data-raya-course-map-drawer="open"] .raya-course-map-header > .raya-course-map-collapse {
    display: none;
  }
  html[data-raya-course-map-drawer="open"] .raya-course-map-drawer-chrome {
    align-items: center;
    display: grid;
    gap: 0.2rem;
    flex: 1 1 auto;
    grid-template-columns: auto minmax(0, 1fr);
    min-width: 0;
  }
  html[data-raya-course-map-drawer="open"] .raya-course-map-drawer-grip {
    background: color-mix(in srgb, var(--raya-color-accent) 72%, var(--raya-color-text));
    border-radius: 999px;
    display: block;
    height: 2rem;
    grid-row: span 2;
    width: 0.32rem;
  }
  html[data-raya-course-map-drawer="open"] .raya-course-map-drawer-title,
  html[data-raya-course-map-drawer="open"] .raya-course-map-drawer-position {
    margin: 0;
  }
  html[data-raya-course-map-drawer="open"] .raya-course-map-drawer-title {
    font-family: var(--raya-font-heading), var(--raya-font-body), -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 0.95rem;
    font-weight: 900;
    line-height: 1.1;
  }
  html[data-raya-course-map-drawer="open"] .raya-course-map-drawer-position {
    color: var(--raya-color-muted);
    font-size: 0.78rem;
    font-weight: 800;
    line-height: 1.2;
  }
  html[data-raya-course-map-drawer="open"] .raya-course-rail-tools {
    gap: 0.375rem;
    padding: 0.5rem 0.65rem;
  }
  html[data-raya-course-map-drawer="open"] .raya-course-map-filter-label,
  html[data-raya-course-map-drawer="open"] .raya-course-map-filter,
  html[data-raya-course-map-drawer="open"] .raya-map-filter-empty {
    display: none;
  }
  html[data-raya-course-map-drawer="open"] .raya-course-map-list {
    max-height: min(18rem, calc(100vh - 8rem));
  }
  html[data-raya-course-map-drawer="open"] .raya-course-rail-command-list {
    gap: 0.3125rem;
  }
  html[data-raya-course-map-drawer="open"] .raya-course-map-drawer-backdrop {
    background: rgba(0, 0, 0, 0.42);
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
    display: block;
    inset: 0;
    position: fixed;
    z-index: 70;
  }
  html[data-raya-course-map-drawer="closed"] .raya-course-map-drawer-backdrop,
  html[data-raya-course-map-drawer="open"] .raya-course-map-drawer-backdrop[hidden],
  .raya-course-map-drawer-backdrop[hidden] {
    display: none;
  }
  html[data-raya-learning-rail-drawer="open"] .raya-learning-rail {
    all: revert;
    background: color-mix(in srgb, var(--raya-color-surface) 86%, var(--raya-color-page));
    border: 1px solid color-mix(in srgb, var(--raya-color-border) 62%, var(--raya-color-page));
    border-radius: 0.875rem 0 0 0.875rem;
    bottom: 0;
    box-sizing: border-box;
    box-shadow: 0 1rem 3rem rgba(0, 0, 0, 0.28);
    color: var(--raya-color-text);
    display: block;
    font-family: var(--raya-font-body), -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 1rem;
    line-height: 1.6;
    left: auto;
    margin: 0;
    max-height: 100vh;
    max-width: calc(100vw - 1rem);
    overflow: auto;
    overscroll-behavior: contain;
    padding: var(--raya-space-panel);
    position: fixed;
    right: 0;
    scrollbar-gutter: stable;
    top: 0;
    width: min(22rem, calc(100vw - 1rem));
    z-index: 80;
  }
  html[data-raya-learning-rail-drawer="open"] .raya-learning-rail-header {
    background: color-mix(in srgb, var(--raya-color-surface) 94%, var(--raya-color-page));
    border-bottom: 1px solid color-mix(in srgb, var(--raya-color-border) 70%, transparent);
    margin: calc(-1 * var(--raya-space-panel)) calc(-1 * var(--raya-space-panel)) 0.75rem;
    padding: 0.75rem var(--raya-space-panel);
    position: fixed;
    top: calc(-1 * var(--raya-space-panel));
    z-index: 2;
  }
  html[data-raya-learning-rail-drawer="open"] .raya-learning-rail-collapse {
    display: inline-flex;
    justify-content: center;
  }
  html[data-raya-learning-rail-drawer="open"] .raya-learning-rail-drawer-backdrop {
    background: rgba(0, 0, 0, 0.42);
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
    display: block;
    inset: 0;
    position: fixed;
    z-index: 70;
  }
  html[data-raya-learning-rail-drawer="closed"] .raya-learning-rail-drawer-backdrop,
  html[data-raya-learning-rail-drawer="open"] .raya-learning-rail-drawer-backdrop[hidden],
  .raya-learning-rail-drawer-backdrop[hidden] {
    display: none;
  }
  .raya-course-map .raya-course-map-toggle,
  .raya-course-map-collapse,
  .raya-course-map-expand {
    display: none;
  }
  .raya-course-map-close {
    align-items: center;
    display: inline-flex;
    justify-content: center;
    min-height: 2rem;
  }
  .raya-learning-rail-expand {
    display: none;
  }
  .raya-learning-rail-collapse {
    display: none;
  }
  html[data-raya-learning-rail-drawer="open"] .raya-learning-rail-collapse {
    display: inline-flex;
    justify-content: center;
  }
  .raya-learning-rail {
    margin-top: 1rem;
  }
  .raya-graph-canvas {
    height: clamp(18rem, 43vh, 23rem);
  }
  .raya-graph-minimap-panel {
    grid-template-columns: minmax(0, 1fr);
  }
  .raya-graph-minimap {
    width: min(100%, 15rem);
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
@media (min-width: __RAYA_STRUCTURAL_PX__px) and (max-width: __RAYA_APPROVED_MINUS_PX__px) {
  .raya-learning-shell {
    align-items: start;
    gap: 0;
    grid-template-areas: "main-article";
    grid-template-columns: minmax(0, 1fr);
    padding-left: 3.75rem;
    padding-right: 3.75rem;
  }
  .raya-mobile-course-map-open.raya-command {
    display: none;
  }
  html[data-raya-course-map-drawer="closed"] .raya-course-map,
  .raya-course-map {
    clip: auto;
    clip-path: none;
    display: flex;
    flex-direction: column;
    grid-area: auto;
    height: calc(100vh - 1.5rem);
    left: 0.75rem;
    margin: 0;
    max-height: none;
    overflow: auto;
    padding: var(--raya-space-panel);
    position: fixed;
    top: 0.75rem;
    white-space: normal;
    z-index: 44;
  }
  .raya-learning-rail {
    grid-area: auto;
    height: calc(100vh - 1.5rem);
    margin: 0;
    max-height: none;
    overflow: auto;
    position: fixed;
    right: 0.75rem;
    top: 0.75rem;
    z-index: 42;
  }
  .raya-course-map,
  .raya-learning-rail {
    width: min(15rem, calc(100vw - 3rem));
  }
  .raya-course-map-close,
  .raya-course-map-drawer-backdrop,
  html[data-raya-course-map-drawer="open"] .raya-course-map-drawer-backdrop {
    display: none;
  }
  .raya-course-map-drawer-backdrop {
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
  }
  .raya-course-map .raya-course-map-toggle,
  .raya-course-map-collapse,
  .raya-learning-rail-collapse {
    display: inline-flex;
  }
  html[data-raya-course-map-drawer="closed"] .raya-course-rail-tools,
  .raya-course-rail-tools {
    display: grid;
  }
  .raya-course-map-list {
    flex: 1 1 auto;
    max-height: none;
  }
  .raya-course-map,
  .raya-learning-rail {
    height: calc(100vh - 1.5rem);
  }
  .raya-main-article {
    min-width: 0;
  }
  html[data-raya-course-map="expanded"] .raya-learning-shell {
    padding-left: calc(min(15rem, calc(100vw - 3rem)) + 1rem);
  }
  html[data-raya-learning-rail="expanded"] .raya-learning-shell {
    padding-right: calc(min(15rem, calc(100vw - 3rem)) + 1rem);
  }
  html[data-raya-course-map="collapsed"] .raya-learning-shell {
    padding-left: 3.75rem;
  }
  html[data-raya-learning-rail="collapsed"] .raya-learning-shell {
    padding-right: 3.75rem;
  }
  html[data-raya-course-map="collapsed"] .raya-learning-shell {
    grid-template-areas: "main-article";
    grid-template-columns: minmax(0, 1fr);
  }
  html[data-raya-learning-rail="collapsed"] .raya-learning-shell {
    grid-template-areas: "main-article";
    grid-template-columns: minmax(0, 1fr);
  }
  html[data-raya-course-map="collapsed"][data-raya-learning-rail="collapsed"] .raya-learning-shell {
    grid-template-areas: "main-article";
    grid-template-columns: minmax(0, 1fr);
  }
  /* Collapsed header/body display:none, and the expand-chip hover/focus
     glass-highlight, live in the single "rail collapse: appearance" region
     (not band-scoped here — they're width-invariant). */
  html[data-raya-course-map="collapsed"] .raya-course-map[data-raya-course-map-transition="collapsing"] .raya-course-map-list,
  .raya-course-map[data-raya-course-map="collapsed"][data-raya-course-map-transition="collapsing"] .raya-course-map-list,
  html[data-raya-learning-rail="collapsed"] .raya-learning-rail[data-raya-learning-rail-transition="collapsing"] .raya-learning-rail-body,
  .raya-learning-rail[data-raya-learning-rail="collapsed"][data-raya-learning-rail-transition="collapsing"] .raya-learning-rail-body {
    display: none;
  }
  .raya-course-map ol {
    padding-left: 0.75rem;
  }
  .raya-course-map-list a {
    font-size: 0.9375rem;
    line-height: 1.35;
    padding: 0.24rem 0.28rem 0.24rem 0.35rem;
  }
  .raya-course-map-list a::before {
    font-size: 0.64rem;
    margin-right: 0.35rem;
    min-width: 1.3rem;
    padding: 0.18rem 0.3rem;
    transform: translateY(0.05rem);
  }
  html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"]) .raya-learning-shell {
    padding-left: 3.75rem;
    padding-right: 3.75rem;
  }
  html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"]) .raya-course-map {
    align-items: start;
    background: transparent;
    border: 0;
    box-shadow: none;
    box-sizing: border-box;
    display: grid;
    height: auto;
    justify-items: center;
    left: 0.35rem;
    margin: 0;
    max-height: none;
    min-width: 0;
    opacity: 1;
    overflow: visible;
    padding: 0;
    pointer-events: none;
    position: fixed;
    top: 0.75rem;
    transform: none;
    width: 2.75rem;
    z-index: 45;
  }
  html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"]) .raya-learning-rail {
    align-items: start;
    background: transparent;
    border: 0;
    box-shadow: none;
    box-sizing: border-box;
    display: grid;
    height: auto;
    justify-items: center;
    margin: 0;
    max-height: none;
    min-width: 0;
    opacity: 1;
    overflow: visible;
    padding: 0;
    pointer-events: none;
    position: fixed;
    right: 0.35rem;
    top: 0.75rem;
    transform: none;
    width: 2.75rem;
    z-index: 45;
  }
  html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"]) .raya-course-rail-tools,
  html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"]) .raya-course-map-filter-label,
  html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"]) .raya-course-map-filter,
  html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"]) .raya-map-filter-empty,
  html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"]) .raya-course-map-list,
  html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"]) .raya-learning-rail-header,
  html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"]) .raya-learning-rail-body {
    display: none;
  }
  html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"]) .raya-course-map .raya-region-title,
  html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"]) .raya-course-map .raya-page-position {
    clip: rect(0 0 0 0);
    clip-path: inset(50%);
    height: 1px;
    overflow: hidden;
    position: absolute;
    white-space: nowrap;
    width: 1px;
  }
  html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"]) .raya-course-map .raya-course-map-toggle,
  html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"]) .raya-course-map .raya-course-map-expand,
  html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"]) .raya-learning-rail-expand {
    align-items: center;
    background: rgba(255, 255, 255, 0.44);
    backdrop-filter: blur(0.35rem);
    -webkit-backdrop-filter: blur(0.35rem);
    border: 1px solid color-mix(in srgb, var(--raya-color-accent) 30%, transparent);
    border-radius: 0.375rem;
    box-shadow: 0 0.45rem 1rem rgba(31, 35, 40, 0.12);
    box-sizing: border-box;
    color: var(--raya-color-text);
    display: inline-flex;
    font-size: 0;
    height: 2.5rem;
    justify-content: center;
    min-height: 2.5rem;
    min-width: 0;
    opacity: 1;
    padding: 0;
    pointer-events: auto;
    position: relative;
    top: auto;
    width: 2.5rem;
  }
  html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"]) .raya-course-map .raya-course-map-toggle::before,
  html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"]) .raya-course-map .raya-course-map-expand::before,
  html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"]) .raya-learning-rail-expand::before,
  html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"]) .raya-course-map .raya-course-map-toggle::after,
  html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"]) .raya-course-map .raya-course-map-expand::after {
    display: none;
  }
  html[data-raya-shell-prepaint="pending"]:not([data-raya-shell-ready="true"]) .raya-learning-rail-expand::after {
    content: "<";
    display: inline-flex;
    font-size: 1.35rem;
    font-weight: 900;
    justify-content: center;
    line-height: 1;
  }
}
@media (min-width: __RAYA_STRUCTURAL_PX__px) {
  html[data-raya-course-map-drawer="closed"] .raya-course-map,
  .raya-course-map {
    display: flex;
    flex-direction: column;
    padding-inline: 0;
    scrollbar-gutter: stable;
  }
  .raya-learning-rail {
    display: flex;
    flex-direction: column;
    padding-inline: 0;
  }
  .raya-course-map-header,
  .raya-course-map-body > .raya-page-position,
  .raya-course-map-filter-label,
  .raya-course-map-filter,
  .raya-map-filter-empty,
  .raya-course-map-list,
  .raya-learning-rail-header {
    margin-inline: var(--raya-space-panel);
  }
  .raya-course-map-filter {
    width: auto;
  }
  .raya-learning-rail-body {
    flex: 1 1 auto;
    min-height: 0;
    overflow: auto;
    overscroll-behavior: contain;
    padding-inline: var(--raya-space-panel);
  }
  .raya-course-map-body {
    flex: 1 1 auto;
    min-height: 0;
  }
  .raya-course-map-list {
    flex: 1 1 auto;
    /* The rail's chrome (header, tools, page position, filter) is ~398px of
       FIXED height, and the tree is the only flexible item -- so without a
       floor it absorbs the entire squeeze and collapses (measured 5px at a
       520px-tall viewport), making the primary navigation unusable. The
       floor pushes the overflow up to .raya-course-map, which already
       declares overflow:auto and max-height:calc(100vh - 2rem) but never
       reached them because the tree swallowed every pixel first. Tall
       viewports are unaffected: flex grow still sizes the tree above this. */
    min-height: 12rem;
  }
  .raya-course-rail-tools {
    padding: 0.5rem 0;
  }
  .raya-course-rail-command-list {
    min-width: 0;
  }
  .raya-course-rail-command {
    box-sizing: border-box;
    flex-direction: column;
    gap: 0.125rem;
    justify-content: center;
    min-width: 0;
    overflow: hidden;
    padding: 0.25rem 0;
    text-align: center;
  }
  .raya-course-rail-command .raya-command-label {
    hyphens: none;
    overflow-wrap: normal;
    word-break: normal;
  }
  .raya-course-rail-command.raya-font-toggle .raya-command-label {
    font-size: 0.725rem;
  }
  /* --- rail collapse: appearance (single source) --- */
  /* Collapsed = the header and body are fully removed (display:none, which
     also drops them from the a11y tree) and the rail container becomes a
     fixed 2.75rem chip strip holding exactly one visible/interactive
     control: the 2.5rem chevron expand chip (`>` on the left/course-map,
     `<` on the right/learning-rail). One vertical placement (top: 0.75rem)
     applies across the whole >=640 band — no per-band offset. This is the
     only place collapsed-appearance rules for either rail live; do not
     reintroduce band-scoped fragments elsewhere. */
  html[data-raya-course-map="collapsed"] .raya-course-map-header,
  html[data-raya-course-map="collapsed"] .raya-course-map-body,
  html[data-raya-learning-rail="collapsed"] .raya-learning-rail-header,
  html[data-raya-learning-rail="collapsed"] .raya-learning-rail-body {
    display: none;
  }
  html[data-raya-course-map="collapsed"] .raya-course-map,
  html[data-raya-learning-rail="collapsed"] .raya-learning-rail {
    align-items: start;
    background: transparent;
    border: 0;
    box-shadow: none;
    box-sizing: border-box;
    display: grid;
    height: auto;
    justify-items: center;
    margin: 0;
    max-height: none;
    overflow: visible;
    padding: 0;
    pointer-events: none;
    position: fixed;
    top: 0.75rem;
    width: 2.75rem;
    z-index: 45;
  }
  html[data-raya-course-map="collapsed"] .raya-course-map {
    left: 0.35rem;
  }
  html[data-raya-learning-rail="collapsed"] .raya-learning-rail {
    right: 0.35rem;
  }
  html[data-raya-course-map="collapsed"] .raya-course-map-expand,
  html[data-raya-learning-rail="collapsed"] .raya-learning-rail-expand {
    align-items: center;
    background: rgba(255, 255, 255, 0.44);
    backdrop-filter: blur(0.35rem);
    -webkit-backdrop-filter: blur(0.35rem);
    border: 1px solid color-mix(in srgb, var(--raya-color-accent) 30%, transparent);
    border-radius: 0.375rem;
    box-shadow: 0 0.45rem 1rem rgba(31, 35, 40, 0.12);
    display: inline-flex;
    font-size: 0;
    height: 2.5rem;
    justify-content: center;
    min-height: 2.5rem;
    min-width: 2.5rem;
    padding: 0;
    pointer-events: auto;
    width: 2.5rem;
  }
  html[data-raya-course-map="collapsed"] .raya-course-map-expand:hover,
  html[data-raya-course-map="collapsed"] .raya-course-map-expand:focus-visible,
  html[data-raya-learning-rail="collapsed"] .raya-learning-rail-expand:hover,
  html[data-raya-learning-rail="collapsed"] .raya-learning-rail-expand:focus-visible {
    background: rgba(255, 255, 255, 0.72);
    border-color: color-mix(in srgb, var(--raya-color-accent) 44%, var(--raya-color-border));
    box-shadow: 0 0.55rem 1.1rem rgba(31, 35, 40, 0.14);
    color: var(--raya-color-text);
    opacity: 1;
  }
  html[data-raya-course-map="collapsed"] .raya-course-map-expand::after {
    content: ">";
    font-size: 1.35rem;
    font-weight: 900;
    line-height: 1;
  }
  html[data-raya-learning-rail="collapsed"] .raya-learning-rail-expand::after {
    content: "<";
    font-size: 1.35rem;
    font-weight: 900;
    line-height: 1;
  }
  /* --- end rail collapse: appearance --- */
}
@media (min-width: __RAYA_STRUCTURAL_PX__px) and (max-width: __RAYA_APPROVED_MINUS_PX__px) {
  .raya-course-map,
  .raya-learning-rail {
    width: min(15.75rem, calc(100vw - 3rem));
  }
  html[data-raya-course-map="expanded"] .raya-learning-shell {
    padding-left: calc(min(15.75rem, calc(100vw - 3rem)) + 1rem);
  }
  html[data-raya-learning-rail="expanded"] .raya-learning-shell {
    padding-right: calc(min(15.75rem, calc(100vw - 3rem)) + 1rem);
  }
}
@media (min-width: __RAYA_STRUCTURAL_PX__px) and (max-width: 767px) {
  .raya-learning-shell {
    gap: 0.6rem;
    grid-template-areas: "main-article";
    grid-template-columns: minmax(0, 1fr);
    padding: 0.75rem;
  }
  html[data-raya-learning-rail="collapsed"] .raya-learning-shell {
    grid-template-columns: minmax(0, 1fr);
  }
  html[data-raya-learning-rail="expanded"] .raya-learning-shell {
    grid-template-columns: minmax(0, 1fr);
  }
  html[data-raya-course-map="collapsed"] .raya-learning-shell {
    grid-template-columns: minmax(0, 1fr);
  }
  html[data-raya-course-map="collapsed"][data-raya-learning-rail="expanded"] .raya-learning-shell {
    grid-template-columns: minmax(0, 1fr);
  }
  .raya-course-map-close {
    font-size: 0.72rem;
    padding: 0.34rem 0.42rem;
  }
  .raya-course-map-filter {
    min-height: 2rem;
  }
  .raya-course-map-list a {
    font-size: 0.86rem;
    line-height: 1.28;
    padding-inline: 0.22rem;
  }
}
@media (max-width: 380px) {
  html[data-raya-course-map-drawer="open"] .raya-course-map {
    width: min(17.25rem, calc(100vw - 1rem));
  }
}
@media (max-width: 340px) {
  html[data-raya-course-map-drawer="open"] .raya-course-map {
    width: 296px;
  }
}
@media (max-width: 312px) {
  html[data-raya-course-map-drawer="open"] .raya-course-map {
    width: 280px;
  }
}
@media (max-width: 290px) {
  html[data-raya-course-map-drawer="open"] .raya-course-map {
    width: 260px;
  }
}
@media (max-width: 520px) {
  .raya-top-command-bar-inner,
  .raya-learning-shell,
  .raya-page-footer,
  .raya-inspection-main,
  .raya-graph-page,
  .raya-search-page,
  .raya-practice-page,
  .raya-tasks-page,
  .raya-schedule-page {
    padding: 0.75rem;
  }
  .raya-top-command-bar-inner {
    align-items: stretch;
    display: grid;
    gap: 0.5rem;
    padding: 0.4rem 0.75rem;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-top-command-bar-inner {
    gap: 0.35rem;
    padding: 0.3rem 0.65rem;
  }
  .raya-reading-context {
    display: grid;
    gap: 0.4rem;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context {
    align-items: center;
    display: flex;
    flex-wrap: nowrap;
    gap: 0.2rem 0.35rem;
    min-width: 0;
    overflow-x: auto;
    overflow-y: hidden;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context-separator {
    display: none;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context-course,
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context-page {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context-course {
    flex: 0 1 6.5rem;
    max-width: 6.5rem;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context-page {
    flex: 0 1 8.5rem;
    max-width: 8.5rem;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context-section {
    display: none;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context-position {
    flex: 0 0 auto;
    white-space: nowrap;
  }
  .raya-discovery-command-bar .raya-reading-context-course,
  .raya-discovery-command-bar .raya-reading-context-page {
    white-space: nowrap;
  }
  .raya-reading-context-sequence {
    flex-wrap: wrap;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-reading-context-sequence {
    flex: 0 0 auto;
    flex-wrap: nowrap;
  }
  .raya-reading-context-section-label {
    display: none;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-course-tools {
    gap: 0.25rem;
    flex-wrap: wrap;
    justify-content: flex-start;
    overflow-x: visible;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-group {
    gap: 0.2rem;
    padding: 0.1rem;
    width: 100%;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-group-discovery {
    display: grid;
    grid-template-columns: minmax(8.5rem, 1fr) repeat(5, minmax(2.25rem, auto));
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-search-form {
    flex: none;
    min-width: 0;
    width: 100%;
  }
  .raya-main-article {
    padding-top: 0.75rem;
  }
  .raya-main-article > .raya-article-sequence {
    gap: 0.45rem;
    margin-bottom: 0.55rem;
    padding-bottom: 0.45rem;
  }
  .raya-main-article > .raya-breadcrumbs {
    margin-bottom: 0.45rem;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-group-layout,
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-group-comfort {
    flex: 1 1 auto;
    width: auto;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command {
    min-height: 2.25rem;
    min-width: 2.25rem;
    padding: 0.35rem;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-icon {
    height: 1.35rem;
    width: 1.35rem;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-search-input,
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-search-submit {
    height: 2.25rem;
    min-height: 2.25rem;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-map {
    font-size: 0;
  }
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-map .raya-command-icon {
    font-size: 0.75rem;
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
  .raya-graph-toolbar {
    align-items: center;
    contain: layout;
    flex-wrap: nowrap;
    max-width: 100%;
    min-width: 0;
    overflow-x: auto;
    overflow-y: hidden;
    scrollbar-gutter: stable;
  }
  .raya-graph-toolbar-group,
  .raya-graph-pan-controls,
  .raya-graph-shortcut-hints {
    flex: 0 0 auto;
    flex-wrap: nowrap;
  }
  .raya-graph-toolbar-primary {
    min-width: 20rem;
  }
  .raya-graph-toolbar-primary input {
    min-width: 9rem;
  }
  .raya-graph-controls button,
  .raya-graph-controls select,
  .raya-graph-controls input {
    white-space: nowrap;
  }
  .raya-graph-active-state {
    max-width: 12rem;
    white-space: nowrap;
  }
  .raya-graph-toolbar :is(input, select, button):focus-visible {
    outline-offset: -2px;
  }
  .raya-graph-reading-keys {
    display: flex;
    gap: 0.35rem;
    overflow-x: auto;
    padding-bottom: 0.1rem;
    scrollbar-gutter: stable;
  }
  .raya-graph-reading-keys article {
    flex: 0 0 11.25rem;
    min-height: 2.35rem;
    padding: 0.24rem 0.34rem;
  }
  .raya-graph-reading-keys h2 {
    font-size: 0.66rem;
  }
  .raya-graph-reading-keys p {
    display: -webkit-box;
    font-size: 0.62rem;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    overflow: hidden;
  }
  .raya-graph-instructions {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    overflow: hidden;
  }
  .raya-graph-orientation {
    gap: 0.28rem;
    padding: 0.34rem 0.42rem;
  }
  .raya-graph-orientation-main {
    align-items: flex-start;
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-gutter: stable;
  }
  .raya-graph-orientation-counts,
  .raya-graph-orientation-selection {
    flex: 0 0 auto;
    min-width: 0;
    white-space: nowrap;
  }
  .raya-graph-orientation-selection {
    text-align: left;
  }
  .raya-graph-orientation-meta,
  .raya-graph-orientation-actions {
    display: flex;
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-gutter: stable;
  }
  .raya-graph-orientation-meta {
    gap: 0.35rem;
  }
  .raya-graph-orientation-meta div {
    flex: 0 0 7.25rem;
  }
  .raya-graph-orientation-meta dd {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .raya-graph-orientation-actions {
    gap: 0.35rem;
    padding-bottom: 0.05rem;
  }
  .raya-graph-orientation-actions > * {
    flex: 0 0 auto;
    white-space: nowrap;
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
    border-bottom: 1px solid var(--raya-numbered-border);
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
  .raya-graph-minimap-panel,
  .raya-graph-panel-header button,
  .raya-search-controls,
  .raya-search-control-panel,
  .raya-search-context-panel,
  .raya-practice-controls,
  .raya-practice-control-panel,
  .raya-practice-context-panel,
  .raya-tasks-controls,
  .raya-tasks-control-panel,
  .raya-tasks-context-panel,
  .raya-schedule-controls,
  .raya-schedule-control-panel,
  .raya-schedule-context-panel,
  .raya-inspection-sidebar,
  .raya-local-asset-inspect,
  .raya-asset-inspector,
  .raya-code-copy {
    display: none !important;
  }
  .raya-learning-shell,
  .raya-graph-workspace,
  .raya-search-workspace,
  .raya-practice-workspace,
  .raya-tasks-workspace,
  .raya-schedule-workspace {
    display: block !important;
  }
  .raya-graph-page,
  .raya-search-page,
  .raya-practice-page,
  .raya-tasks-page,
  .raya-schedule-page,
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
  .raya-tasks-results a,
  .raya-schedule-results a,
  .raya-graph-list a {
    color: #000 !important;
    text-decoration: underline;
  }
  .raya-main-article a[href^="http"]::after,
  .raya-search-results a[href^="http"]::after,
  .raya-practice-results a[href^="http"]::after,
  .raya-tasks-results a[href^="http"]::after,
  .raya-schedule-results a[href^="http"]::after {
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
    return apply_rail_geometry_tokens(
        base + "\n" + HtmlFormatter().get_style_defs(".highlight") + "\n"
    )


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
