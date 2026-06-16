from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

from raya_schema.references import reference_kind_for_path


MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
FENCE_OPEN_RE = re.compile(
    r"^(?P<prefix>(?: {0,3}(?:[-+*]|\d+[.)])\s+)? {0,3})"
    r"(?P<marker>`{3,}|~{3,})(?P<info>.*)$"
)
FENCE_CLOSE_RE = re.compile(r"^(?P<indent> *)(?P<marker>`{3,}|~{3,})[ \t]*$")


@dataclass(frozen=True)
class MarkdownLink:
    label: str
    target: str
    start: int
    end: int
    line: int
    column: int


@dataclass(frozen=True)
class MarkdownSourceLine:
    text: str
    start: int
    number: int


@dataclass(frozen=True)
class AssetReference:
    kind: str
    target_path: Path
    output_path: str | None = None
    asset_root: Path | None = None
    blocked_segment: str | None = None


@dataclass(frozen=True)
class _FenceState:
    marker: str
    close_indent_max: int


def iter_unfenced_markdown_lines(text: str) -> list[MarkdownSourceLine]:
    lines: list[MarkdownSourceLine] = []
    cursor = 0
    line_number = 1
    fence_state: _FenceState | None = None

    for raw_line in text.splitlines(keepends=True):
        fence_line = raw_line.rstrip("\r\n")
        if fence_state is not None:
            if _is_closing_fence(fence_line, fence_state):
                fence_state = None
            cursor += len(raw_line)
            line_number += 1
            continue

        opener = _fence_opener(fence_line)
        if opener is not None:
            fence_state = opener
            cursor += len(raw_line)
            line_number += 1
            continue

        lines.append(
            MarkdownSourceLine(
                text=raw_line,
                start=cursor,
                number=line_number,
            )
        )
        cursor += len(raw_line)
        line_number += 1

    return lines


def extract_markdown_links(text: str) -> list[MarkdownLink]:
    links: list[MarkdownLink] = []
    for source_line in iter_unfenced_markdown_lines(text):
        line_text = source_line.text.rstrip("\n")
        for match in MARKDOWN_LINK_RE.finditer(line_text):
            absolute_start = source_line.start + match.start()
            absolute_end = source_line.start + match.end()
            links.append(
                MarkdownLink(
                    label=match.group(1),
                    target=match.group(2).strip(),
                    start=absolute_start,
                    end=absolute_end,
                    line=source_line.number,
                    column=match.start() + 1,
                )
            )
    return links


def classify_markdown_target(target: str) -> str:
    if target.strip().startswith("raya:"):
        return "stable"
    if _is_non_local_target(target):
        return "ignored"

    path = markdown_link_path(target)
    if not path:
        return "ignored"
    if path.lower().endswith(".md"):
        return "content"
    reference_kind = reference_kind_for_path(path)
    if reference_kind is not None:
        return reference_kind
    return "asset"


def markdown_link_path(target: str) -> str:
    path = _target_without_optional_title(target.strip())
    path = path.split("#", 1)[0]
    path = path.split("?", 1)[0]
    return unquote(path.strip())


def markdown_link_fragment(target: str) -> str:
    if "#" not in target:
        return ""
    fragment = target.split("#", 1)[1].strip()
    return f"#{fragment}" if fragment else ""


def stable_markdown_id(target: str) -> str:
    stripped = _target_without_optional_title(target.strip())
    if not stripped.startswith("raya:"):
        return ""
    value = stripped[len("raya:") :]
    value = value.split("#", 1)[0]
    value = value.split("?", 1)[0]
    return unquote(value.strip())


def resolve_local_markdown_target(
    *,
    source_path: Path,
    course_root: Path,
    target_path: str,
) -> Path:
    target = Path(target_path)
    if target.is_absolute():
        return (course_root / target.as_posix().lstrip("/")).resolve()
    return (source_path.parent / target).resolve()


def resolve_course_asset_reference(
    *,
    source_path: Path,
    course_root: Path,
    source_dir: Path,
    target_path: str,
) -> AssetReference:
    target = resolve_local_markdown_target(
        source_path=source_path,
        course_root=course_root,
        target_path=target_path,
    )

    if path_is_under(target, source_dir):
        blocked_segment = _blocked_source_support_segment(target, source_dir)
        if blocked_segment is not None:
            return AssetReference(
                kind="blocked",
                target_path=target,
                blocked_segment=blocked_segment,
            )
        for asset_root in _colocated_asset_roots(source_path, source_dir):
            if path_is_under(target, asset_root):
                return AssetReference(
                    kind="colocated",
                    target_path=target,
                    output_path=colocated_asset_output_path(source_dir, target),
                    asset_root=asset_root,
                )
        return AssetReference(kind="outside", target_path=target)

    return AssetReference(kind="outside", target_path=target)


def colocated_asset_output_path(source_dir: Path, target_path: Path) -> str:
    rel_parts = target_path.relative_to(source_dir).parts
    output_parts = ["_source"]
    for part in rel_parts:
        output_parts.append("_local" if part == "_assets" else part)
    return Path(*output_parts).as_posix()


def path_is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _colocated_asset_roots(source_path: Path, source_dir: Path) -> list[Path]:
    roots: list[Path] = []
    current = source_path.parent.resolve()
    source_root = source_dir.resolve()
    while True:
        try:
            current.relative_to(source_root)
        except ValueError:
            break
        roots.append(current / "_assets")
        if current == source_root:
            break
        current = current.parent
    return roots


def _blocked_source_support_segment(target_path: Path, source_dir: Path) -> str | None:
    try:
        rel_parts = target_path.resolve().relative_to(source_dir.resolve()).parts
    except ValueError:
        return None
    for part in rel_parts[:-1]:
        if part == "_assets":
            continue
        if part in {"drafts", "runtime"} or part.startswith("_"):
            return part
    return None


def _is_non_local_target(target: str) -> bool:
    stripped = target.strip()
    if stripped.startswith("#"):
        return True
    parsed = urlsplit(stripped)
    return bool(parsed.scheme or parsed.netloc)


def _target_without_optional_title(target: str) -> str:
    if target.startswith("<") and ">" in target:
        return target[1 : target.find(">")]
    return target


def _fence_opener(line: str) -> _FenceState | None:
    match = FENCE_OPEN_RE.match(_line_without_blockquote_prefix(line))
    if match is None:
        return None
    marker = match.group("marker")
    info = match.group("info")
    if marker.startswith("`") and "`" in info:
        return None
    return _FenceState(
        marker=marker,
        close_indent_max=len(match.group("prefix")) + 3,
    )


def _is_closing_fence(line: str, fence_state: _FenceState) -> bool:
    match = FENCE_CLOSE_RE.match(_line_without_blockquote_prefix(line))
    if match is None:
        return False
    if len(match.group("indent")) > fence_state.close_indent_max:
        return False
    marker = match.group("marker")
    return marker[0] == fence_state.marker[0] and len(marker) >= len(fence_state.marker)


def _line_without_blockquote_prefix(line: str) -> str:
    value = line
    while True:
        match = re.match(r"^ {0,3}>\s?", value)
        if match is None:
            return value
        value = value[match.end() :]
