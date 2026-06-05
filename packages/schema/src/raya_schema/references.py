from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote


REFERENCE_SUPPORT_DIRS = {"code", "notebooks"}
REFERENCE_EXTENSIONS = {
    ".py": "code",
    ".ipynb": "notebook",
}
REFERENCE_FORMATS = {
    "code": "python",
    "notebook": "ipynb",
}
REFERENCE_DIR_BY_KIND = {
    "code": "code",
    "notebook": "notebooks",
}
PRIVATE_REFERENCE_SEGMENTS = {
    "_assets",
    "_official",
    "_drafts",
    "_partials",
    "drafts",
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
    if kind not in REFERENCE_DIR_BY_KIND:
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

    for support_root in _allowed_support_roots(source_path, source_dir, kind):
        if _path_is_under(target, support_root):
            return ReferenceResolution(
                kind=kind,
                target_path=target,
                status="referenced",
                output_path=reference_output_path(source_dir, target),
                support_root=support_root,
            )

    if _target_uses_reference_dir(target, source_dir, kind):
        return ReferenceResolution(kind=kind, target_path=target, status="cross_owner")
    return ReferenceResolution(kind=kind, target_path=target, status="outside_support")


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


def _allowed_support_roots(
    source_path: Path,
    source_dir: Path,
    kind: str,
) -> list[Path]:
    support_dir_name = REFERENCE_DIR_BY_KIND[kind]
    roots: list[Path] = []
    current = source_path.parent.resolve()
    source_root = source_dir.resolve()
    while True:
        try:
            current.relative_to(source_root)
        except ValueError:
            break
        roots.append(current / support_dir_name)
        if current == source_root:
            break
        current = current.parent
    return roots


def _target_uses_reference_dir(target_path: Path, source_dir: Path, kind: str) -> bool:
    try:
        rel_parts = target_path.resolve().relative_to(source_dir.resolve()).parts
    except ValueError:
        return False
    support_dir_name = REFERENCE_DIR_BY_KIND[kind]
    return support_dir_name in rel_parts[:-1]


def _blocked_reference_segment(target_path: Path, source_dir: Path) -> str | None:
    try:
        rel_parts = target_path.resolve().relative_to(source_dir.resolve()).parts
    except ValueError:
        return None
    for part in rel_parts[:-1]:
        if part in PRIVATE_REFERENCE_SEGMENTS or (
            part.startswith("_") and part not in REFERENCE_SUPPORT_DIRS
        ):
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
