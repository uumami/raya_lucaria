from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

from raya_schema.references import reference_kind_for_path


MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


@dataclass(frozen=True)
class MarkdownLink:
    label: str
    target: str
    start: int
    end: int
    line: int
    column: int


@dataclass(frozen=True)
class AssetReference:
    kind: str
    target_path: Path
    output_path: str | None = None
    asset_root: Path | None = None
    blocked_segment: str | None = None


def extract_markdown_links(text: str) -> list[MarkdownLink]:
    links: list[MarkdownLink] = []
    cursor = 0
    in_fence = False
    for raw_line in text.splitlines(keepends=True):
        stripped = raw_line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            cursor += len(raw_line)
            continue
        if in_fence:
            cursor += len(raw_line)
            continue

        line_text = raw_line.rstrip("\n")
        for match in MARKDOWN_LINK_RE.finditer(line_text):
            absolute_start = cursor + match.start()
            absolute_end = cursor + match.end()
            line = text.count("\n", 0, absolute_start) + 1
            previous_newline = text.rfind("\n", 0, absolute_start)
            column = (
                absolute_start + 1
                if previous_newline == -1
                else absolute_start - previous_newline
            )
            links.append(
                MarkdownLink(
                    label=match.group(1),
                    target=match.group(2).strip(),
                    start=absolute_start,
                    end=absolute_end,
                    line=line,
                    column=column,
                )
            )
        cursor += len(raw_line)
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
    stable_id = unquote(value.strip())
    if stable_id.startswith("ref/"):
        return stable_id
    return stable_id


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
