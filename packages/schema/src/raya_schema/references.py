from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote


REFERENCE_EXTENSIONS = {
    ".py": "code",
    ".ipynb": "notebook",
}
REFERENCE_FORMATS = {
    "code": "python",
    "notebook": "ipynb",
}
PRIVATE_REFERENCE_SEGMENTS = {
    "_assets",
    "_official",
    "_reviewed",
    "_drafts",
    "_partials",
    "drafts",
    "runtime",
}


@dataclass(frozen=True)
class ReferenceResolution:
    kind: str
    target_path: Path
    status: str
    output_path: str | None = None
    support_root: Path | None = None
    blocked_segment: str | None = None


@dataclass(frozen=True)
class SourceReference:
    id: str
    page_id: str
    page_source_path: str
    label: str
    target: str
    kind: str
    format: str
    source_path: Path
    source_rel_path: str
    output_path: str
    artifact_path: str
    browser_path: str
    sha256: str
    execution_status: str = "not-executed"
    execution_policy: str = "never"
    runtime_profile: str | None = None
    cache_key: str | None = None

    def to_index_item(self) -> dict[str, object]:
        execution: dict[str, object] = {
            "status": self.execution_status,
            "policy": self.execution_policy,
        }
        if self.runtime_profile is not None:
            execution["profile"] = self.runtime_profile
        if self.cache_key is not None:
            execution["cache_key"] = self.cache_key
        return {
            "id": self.id,
            "page_id": self.page_id,
            "page_source_path": self.page_source_path,
            "label": self.label,
            "target": self.target,
            "kind": self.kind,
            "format": self.format,
            "source_path": self.source_rel_path,
            "artifact_path": self.artifact_path,
            "browser_path": self.browser_path,
            "sha256": self.sha256,
            "execution": execution,
        }


def reference_kind_for_path(path: str | Path) -> str | None:
    suffix = Path(str(path)).suffix.lower()
    return REFERENCE_EXTENSIONS.get(suffix)


def reference_format(kind: str) -> str:
    return REFERENCE_FORMATS.get(kind, kind)


def reference_output_path(source_dir: Path, target_path: Path) -> str:
    rel_parts = target_path.resolve().relative_to(source_dir.resolve()).parts
    return Path("_source", *rel_parts).as_posix()


def source_reference_id(course_id: str, page_id: str, output_path: str) -> str:
    digest = hashlib.sha256(
        f"{course_id}\0{page_id}\0{output_path}".encode("utf-8")
    ).hexdigest()[:12]
    return f"{page_id}:{digest}"


def resolve_course_reference(
    *,
    source_path: Path,
    course_root: Path,
    source_dir: Path,
    target_path: str,
    kind: str,
) -> ReferenceResolution:
    target = _resolve_local_target(
        source_path=source_path,
        course_root=course_root,
        target_path=target_path,
    )
    if kind not in REFERENCE_FORMATS or reference_kind_for_path(target) != kind:
        return ReferenceResolution(kind=kind, target_path=target, status="unsupported")
    if not _path_is_under(target, source_dir):
        return ReferenceResolution(kind=kind, target_path=target, status="outside")

    blocked_segment = _blocked_reference_segment(target, source_dir)
    if blocked_segment is not None:
        return ReferenceResolution(
            kind=kind,
            target_path=target,
            status="blocked",
            blocked_segment=blocked_segment,
        )

    target_owner = _owner_dir_for_path(target, source_dir)
    allowed_owners = _allowed_owner_dirs(source_path, source_dir)
    if target_owner.resolve() in {owner.resolve() for owner in allowed_owners}:
        return ReferenceResolution(
            kind=kind,
            target_path=target,
            status="referenced",
            output_path=reference_output_path(source_dir, target),
            support_root=target_owner,
        )

    return ReferenceResolution(kind=kind, target_path=target, status="cross_owner")


def notebook_validation_error(path: Path) -> str | None:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return f"Notebook is not readable JSON: {exc}"
    if not isinstance(loaded, dict):
        return "Notebook JSON must be an object"
    if not isinstance(loaded.get("cells"), list):
        return "Notebook JSON must contain a cells list"
    if "nbformat" not in loaded:
        return "Notebook JSON must contain nbformat"
    return None


def _allowed_owner_dirs(
    source_path: Path,
    source_dir: Path,
) -> list[Path]:
    roots: list[Path] = []
    current = _owner_dir_for_path(source_path, source_dir).resolve()
    source_root = source_dir.resolve()
    while True:
        try:
            current.relative_to(source_root)
        except ValueError:
            break
        roots.append(current)
        if current == source_root:
            break
        current = current.parent
    return roots


def _owner_dir_for_path(path: Path, source_dir: Path) -> Path:
    source_root = source_dir.resolve()
    current = path.resolve().parent
    while True:
        try:
            current.relative_to(source_root)
        except ValueError:
            return source_root
        if _has_normalized_zero_index(current):
            return current
        if current == source_root:
            return source_root
        current = current.parent


def _has_normalized_zero_index(directory: Path) -> bool:
    if not directory.is_dir():
        return False
    for child in directory.iterdir():
        if (
            child.is_file()
            and child.suffix == ".md"
            and child.stem.startswith("0")
            and child.stem.strip("0") == "_index"
        ):
            return True
    return False


def _blocked_reference_segment(target_path: Path, source_dir: Path) -> str | None:
    try:
        rel_parts = target_path.resolve().relative_to(source_dir.resolve()).parts
    except ValueError:
        return None
    for part in rel_parts[:-1]:
        if part in PRIVATE_REFERENCE_SEGMENTS or part.startswith("_"):
            return part
    return None


def _resolve_local_target(
    *,
    source_path: Path,
    course_root: Path,
    target_path: str,
) -> Path:
    target = Path(unquote(target_path))
    if target.is_absolute():
        return (course_root / target.as_posix().lstrip("/")).resolve()
    return (source_path.parent / target).resolve()


def _path_is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True
