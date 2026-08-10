from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import ValidationError

from raya_schema.content import ContentModel, ContentPage, parse_ordered_name
from raya_schema.diagnostics import ValidationReport
from raya_schema.schema_loader import validator_for
from raya_schema.yaml_io import load_yaml_file


SUPPORTED_OBJECT_TYPES = {
    "assignment",
    "card",
    "exam",
    "example",
    "project",
    "prompt",
    "quiz",
    "task",
}
OFFICIAL_FAMILY_TYPES = {
    "assignments": "assignment",
    "cards": "card",
    "exams": "exam",
    "examples": "example",
    "projects": "project",
    "prompts": "prompt",
    "quizzes": "quiz",
    "tasks": "task",
}
SUPPORTED_OFFICIAL_SUFFIXES = {".yaml", ".yml", ".json"}


@dataclass(frozen=True)
class OfficialSource:
    object_path: Path
    family: str
    source_root_support: bool
    support_dir: Path
    owner_page: ContentPage | None
    source_order: int | None = None


def discover_official_objects(
    *,
    course_root: Path,
    course_id: str,
    source_dir: Path,
    content_model: ContentModel,
    report: ValidationReport,
) -> list[dict[str, Any]]:
    object_validator = validator_for("official-learning-object.schema.json")
    valid_scopes = _valid_quantum_scopes(content_model, course_id)
    seen_ids: dict[str, Path] = {}
    by_type: dict[str, list[Path]] = defaultdict(list)
    objects: list[dict[str, Any]] = []

    for source in _official_sources(
        course_root=course_root,
        source_dir=source_dir,
        content_model=content_model,
        report=report,
    ):
        report.read_file(source.object_path)
        try:
            data = load_yaml_file(source.object_path)
        except Exception as exc:
            report.add_error(
                f"Could not read official learning object: {exc}",
                path=source.object_path,
                next_action="Fix official learning object syntax",
            )
            continue
        if not isinstance(data, dict):
            report.add_error(
                "Official learning object must be a mapping",
                path=source.object_path,
                next_action="Use key/value object fields",
            )
            continue

        resolved_data = _resolve_scope(source, data, report)
        for error in sorted(
            object_validator.iter_errors(resolved_data),
            key=_schema_error_key,
        ):
            report.add_error(
                _schema_error_message(error),
                path=source.object_path,
                field=".".join(str(part) for part in error.absolute_path) or None,
                next_action="Update the official learning object",
            )

        object_id = resolved_data.get("id")
        object_type = resolved_data.get("type")
        expected_type = OFFICIAL_FAMILY_TYPES.get(source.family)
        if expected_type is None:
            report.add_error(
                "Unsupported official learning object family",
                path=source.object_path,
                field=source.family,
                next_action="Use cards, quizzes, prompts, examples, assignments, exams, projects, or tasks",
            )
        elif isinstance(object_type, str) and object_type != expected_type:
            report.add_error(
                "Official learning object type does not match its family",
                path=source.object_path,
                field="type",
                next_action=f"Move the object under {object_type}s/ or set type: {expected_type}",
            )

        if isinstance(object_type, str):
            by_type[object_type].append(source.object_path)
            if object_type not in SUPPORTED_OBJECT_TYPES:
                report.add_error(
                    "Unsupported official learning object type",
                    path=source.object_path,
                    field="type",
                    next_action="Use a supported official learning object type",
                )

        if isinstance(object_id, str):
            if object_id in seen_ids:
                report.add_error(
                    "Duplicate official learning object ID",
                    path=source.object_path,
                    field="id",
                    next_action=f"Use a unique object ID; first seen in {seen_ids[object_id]}",
                )
            else:
                seen_ids[object_id] = source.object_path

        scope = resolved_data.get("scope")
        quantum = scope.get("quantum") if isinstance(scope, dict) else None
        if isinstance(quantum, str) and quantum not in valid_scopes:
            report.add_error(
                "Official learning object references an unknown quantum scope",
                path=source.object_path,
                field="scope.quantum",
                next_action="Point scope.quantum to a rendered page id, alias, or source path",
            )

        exported = {
            "id": resolved_data.get("id"),
            "type": resolved_data.get("type"),
            "authority": resolved_data.get("authority"),
            "scope": resolved_data.get("scope", {}),
            "content": resolved_data.get("content", {}),
            "source_path": source.object_path.relative_to(course_root).as_posix(),
        }
        if source.source_order is not None:
            exported["source_order"] = source.source_order
        if "retrieval" in resolved_data:
            exported["retrieval"] = resolved_data["retrieval"]
        objects.append(exported)

    for object_type, paths in sorted(by_type.items()):
        report.add_info(
            f"Found official {object_type} object(s)",
            path=paths[0] if paths else course_root,
        )
    return objects


def _official_sources(
    *,
    course_root: Path,
    source_dir: Path,
    content_model: ContentModel,
    report: ValidationReport,
) -> list[OfficialSource]:
    sources: list[OfficialSource] = []
    index_pages_by_dir = {
        page.source_path.parent.resolve(): page
        for page in content_model.pages
        if page.is_index
    }

    for support_dir in sorted(
        path for path in source_dir.rglob("_official") if path.is_dir()
    ):
        if _private_owner_path(support_dir, source_dir):
            continue
        owner_page = None
        if support_dir.parent.resolve() != source_dir.resolve():
            owner_page = index_pages_by_dir.get(support_dir.parent.resolve())
        for family_dir in sorted(path for path in support_dir.iterdir() if path.is_dir()):
            if (
                support_dir.parent.resolve() == source_dir.resolve()
                and family_dir.name == "calendar"
            ):
                continue
            family = family_dir.name
            source_order_by_parent: dict[Path, dict[int, Path]] = defaultdict(dict)
            for object_path in sorted(
                path
                for path in family_dir.rglob("*")
                if path.is_file() and path.suffix.lower() in SUPPORTED_OFFICIAL_SUFFIXES
            ):
                ordered = parse_ordered_name(object_path.stem)
                source_order = ordered.order if ordered is not None else None
                if ordered is None or ordered.sequence != "main" or ordered.order <= 0:
                    report.add_error(
                        "Unordered official learning object file",
                        path=object_path,
                        next_action="Use an ordered filename such as 1_limit_meaning.yaml",
                    )
                else:
                    seen_orders = source_order_by_parent[object_path.parent]
                    if ordered.order in seen_orders:
                        report.add_error(
                            "Duplicate official learning object order",
                            path=object_path,
                            field=ordered.raw_prefix,
                            next_action=f"Use a unique order; first seen in {seen_orders[ordered.order]}",
                        )
                    else:
                        seen_orders[ordered.order] = object_path
                sources.append(
                    OfficialSource(
                        object_path=object_path,
                        family=family,
                        source_root_support=support_dir.parent.resolve()
                        == source_dir.resolve(),
                        support_dir=support_dir,
                        owner_page=owner_page,
                        source_order=source_order,
                    )
                )

    return sources


def _resolve_scope(
    source: OfficialSource,
    data: dict[str, Any],
    report: ValidationReport,
) -> dict[str, Any]:
    resolved = dict(data)
    scope = resolved.get("scope")
    quantum = scope.get("quantum") if isinstance(scope, dict) else None

    if source.source_root_support:
        if not isinstance(quantum, str) or not quantum.strip():
            report.add_error(
                "Course-level official learning object requires scope.quantum",
                path=source.object_path,
                field="scope.quantum",
                next_action="Set scope.quantum explicitly for source-root _official/ objects",
            )
        return resolved

    if source.owner_page is None:
        report.add_error(
            "Colocated official learning object has no rendered quantum owner",
            path=source.object_path,
            field="scope.quantum",
            next_action="Add 0_index.md to the support-owning directory",
        )
        return resolved

    if not isinstance(quantum, str) or not quantum.strip():
        resolved["scope"] = {"quantum": source.owner_page.id}
        return resolved
    if quantum != source.owner_page.id:
        report.add_error(
            "Colocated official learning object scope does not match nearest quantum",
            path=source.object_path,
            field="scope.quantum",
            next_action=f"Use scope.quantum: {source.owner_page.id} or move the object beside its target quantum",
        )
    return resolved


def _private_owner_path(support_dir: Path, source_dir: Path) -> bool:
    try:
        owner_parts = support_dir.parent.relative_to(source_dir).parts
    except ValueError:
        return True
    return any(part == "drafts" or part.startswith("_") for part in owner_parts)


def _valid_quantum_scopes(
    content_model: ContentModel,
    course_id: str,
) -> set[str]:
    scopes: set[str] = set()
    for page in content_model.pages:
        scopes.add(page.id)
        scopes.update(page.aliases)
        scopes.add(page.rel_path)
        scopes.add(f"{course_id}:{page.rel_path}")
    return scopes


def _schema_error_key(error: ValidationError) -> tuple[str, str]:
    return (".".join(str(part) for part in error.absolute_path), error.message)


def _schema_error_message(error: ValidationError) -> str:
    if error.absolute_path:
        return error.message
    return f"Official learning object does not match schema: {error.message}"
