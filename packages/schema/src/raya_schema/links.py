from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit


MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


@dataclass(frozen=True)
class MarkdownLink:
    label: str
    target: str
    start: int
    end: int
    line: int
    column: int


def extract_markdown_links(text: str) -> list[MarkdownLink]:
    links: list[MarkdownLink] = []
    for match in MARKDOWN_LINK_RE.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        previous_newline = text.rfind("\n", 0, match.start())
        column = (
            match.start() + 1
            if previous_newline == -1
            else match.start() - previous_newline
        )
        links.append(
            MarkdownLink(
                label=match.group(1),
                target=match.group(2).strip(),
                start=match.start(),
                end=match.end(),
                line=line,
                column=column,
            )
        )
    return links


def classify_markdown_target(target: str) -> str:
    if _is_non_local_target(target):
        return "ignored"

    path = markdown_link_path(target)
    if not path:
        return "ignored"
    if path.lower().endswith(".md"):
        return "content"
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


def path_is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


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
