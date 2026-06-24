from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from raya_schema.content import ContentModel, ContentPage
from raya_schema.links import iter_unfenced_markdown_lines


WIKILINK_RE = re.compile(r"(?<!!)\[\[([^\]\|\n]+)(?:\|([^\]\n]+))?\]\]")
ORDER_PREFIX_RE = re.compile(r"^[0-9]+_")


@dataclass(frozen=True)
class Wikilink:
    target: str
    label: str
    start: int
    end: int
    line: int
    column: int


@dataclass(frozen=True)
class WikilinkResolution:
    target: str
    page: ContentPage | None
    ambiguous: tuple[ContentPage, ...] = ()


class WikilinkResolver:
    def __init__(self, content_model: ContentModel) -> None:
        self._pages_by_exact_reference = {
            **content_model.pages_by_id,
            **content_model.pages_by_alias,
        }
        self._pages_by_key: dict[str, set[ContentPage]] = {}
        for page in content_model.pages:
            for key in _page_resolution_keys(page):
                self._pages_by_key.setdefault(_normalize_key(key), set()).add(page)

    def resolve(self, target: str) -> WikilinkResolution:
        stripped = target.strip()
        exact = self._pages_by_exact_reference.get(stripped)
        if exact is not None:
            return WikilinkResolution(target=stripped, page=exact)

        pages = tuple(
            sorted(
                self._pages_by_key.get(_normalize_key(stripped), set()),
                key=lambda page: page.rel_path,
            )
        )
        if len(pages) == 1:
            return WikilinkResolution(target=stripped, page=pages[0])
        if len(pages) > 1:
            return WikilinkResolution(target=stripped, page=None, ambiguous=pages)
        return WikilinkResolution(target=stripped, page=None)


def build_wikilink_resolver(content_model: ContentModel) -> WikilinkResolver:
    return WikilinkResolver(content_model)


def extract_wikilinks(text: str) -> list[Wikilink]:
    wikilinks: list[Wikilink] = []
    for source_line in iter_unfenced_markdown_lines(text):
        line_text = source_line.text.rstrip("\n")
        searchable_line = _without_inline_code_spans(line_text)
        for match in WIKILINK_RE.finditer(searchable_line):
            target = match.group(1).strip()
            label = (match.group(2) or target).strip()
            if not target:
                continue
            wikilinks.append(
                Wikilink(
                    target=target,
                    label=label,
                    start=source_line.start + match.start(),
                    end=source_line.start + match.end(),
                    line=source_line.number,
                    column=match.start() + 1,
                )
            )
    return wikilinks


def render_wikilinks_as_markdown(
    text: str,
    *,
    resolve_target: Callable[[str], str | None],
) -> str:
    replacements: list[tuple[int, int, str]] = []
    for wikilink in extract_wikilinks(text):
        page_id = resolve_target(wikilink.target)
        if page_id is None:
            continue
        replacements.append(
            (
                wikilink.start,
                wikilink.end,
                f"[{_escape_markdown_label(wikilink.label)}](raya:{page_id})",
            )
        )

    rendered = text
    for start, end, replacement in reversed(replacements):
        rendered = rendered[:start] + replacement + rendered[end:]
    return rendered


def _page_resolution_keys(page: ContentPage) -> set[str]:
    keys = {
        page.id,
        page.title,
        page.nav_title,
        Path(page.rel_path).stem,
        _strip_order_prefix(Path(page.rel_path).stem),
        page.rel_path,
        page.rel_path.removesuffix(".md"),
    }
    keys.update(page.aliases)
    if page.is_index:
        parent = Path(page.rel_path).parent
        if str(parent) != ".":
            keys.add(parent.as_posix())
            keys.add(_strip_order_prefix_from_path(parent))
    keys.add(_strip_order_prefix_from_path(Path(page.rel_path).with_suffix("")))
    return {key.strip() for key in keys if key.strip()}


def _strip_order_prefix_from_path(path: Path) -> str:
    return Path(*(_strip_order_prefix(part) for part in path.parts)).as_posix()


def _strip_order_prefix(value: str) -> str:
    return ORDER_PREFIX_RE.sub("", value)


def _normalize_key(value: str) -> str:
    return " ".join(value.casefold().strip().split())


def _escape_markdown_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("]", "\\]")


def _without_inline_code_spans(line: str) -> str:
    chars = list(line)
    index = 0
    while index < len(chars):
        if chars[index] != "`":
            index += 1
            continue
        marker_end = index
        while marker_end < len(chars) and chars[marker_end] == "`":
            marker_end += 1
        marker = "`" * (marker_end - index)
        close = line.find(marker, marker_end)
        if close == -1:
            index = marker_end
            continue
        close_end = close + len(marker)
        for position in range(index, close_end):
            chars[position] = " "
        index = close_end
    return "".join(chars)
