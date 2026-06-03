from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from jsonschema import ValidationError

from raya_schema.diagnostics import ValidationReport
from raya_schema.links import (
    classify_markdown_target,
    extract_markdown_links,
    markdown_link_path,
    path_is_under,
    resolve_local_markdown_target,
)
from raya_schema.schema_loader import validator_for
from raya_schema.yaml_io import load_yaml_file, parse_frontmatter


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


def validate_course(course_path: str | Path) -> ValidationReport:
    root = Path(course_path).resolve()
    report = ValidationReport(context="course")

    if not root.exists():
        report.add_error(
            "Course path does not exist",
            path=root,
            next_action="Pass an existing course directory",
        )
        return report

    config_path = root / "raya.yaml"
    if not config_path.exists():
        report.add_error(
            "Missing raya.yaml",
            path=config_path,
            next_action="Create a raya.yaml course configuration",
        )
        return report

    config = _load_mapping(config_path, report)
    if config is None:
        return report

    _validate_schema(config, "raya-course.schema.json", config_path, report)

    content_dir_name = config.get("content")
    content_dir = (
        root / str(content_dir_name) if content_dir_name else root / "content"
    ).resolve()
    assets_dir = (root / str(config.get("assets", "assets"))).resolve()
    if not content_dir.exists() or not content_dir.is_dir():
        report.add_error(
            "Configured content directory is missing",
            path=content_dir,
            field="content",
            next_action="Create the content directory or update raya.yaml",
        )
        return report

    markdown_files = sorted(content_dir.rglob("*.md"))
    if not markdown_files:
        report.add_error(
            "Content directory contains no Markdown files",
            path=content_dir,
            next_action="Add at least one Markdown content file",
        )

    explicit_quantum_ids: dict[str, Path] = {}
    scoped_quantum_names: set[str] = set()
    duplicate_quantum_paths: list[tuple[str, Path, Path]] = []

    course_id = str(config.get("course_id", "unknown-course"))
    for md_path in markdown_files:
        report.read_file(md_path)
        rel_path = md_path.relative_to(content_dir).as_posix()
        scoped_quantum_names.add(rel_path)
        scoped_quantum_names.add(f"{course_id}:{rel_path}")

        try:
            frontmatter = parse_frontmatter(md_path)
        except Exception as exc:
            report.add_error(
                f"Unreadable Markdown frontmatter: {exc}",
                path=md_path,
                next_action="Fix frontmatter syntax",
            )
            continue

        _validate_markdown_source_links(
            md_path=md_path,
            body=_markdown_body(md_path),
            course_root=root,
            content_dir=content_dir,
            assets_dir=assets_dir,
            report=report,
        )

        quantum = frontmatter.get("quantum")
        if isinstance(quantum, dict) and quantum.get("id"):
            quantum_id = str(quantum["id"])
            scoped_quantum_names.add(quantum_id)
            if quantum_id in explicit_quantum_ids:
                duplicate_quantum_paths.append(
                    (quantum_id, explicit_quantum_ids[quantum_id], md_path)
                )
            else:
                explicit_quantum_ids[quantum_id] = md_path

    for quantum_id, first, second in duplicate_quantum_paths:
        report.add_error(
            "Duplicate quantum ID",
            path=second,
            field="quantum.id",
            next_action=f"Use a unique quantum ID; first seen in {first}",
        )

    official_dir = root / "official"
    if official_dir.exists():
        _validate_official_objects(
            official_dir=official_dir,
            valid_scopes=scoped_quantum_names,
            report=report,
        )

    if report.ok:
        report.add_info(
            "Course validation passed",
            path=root,
            next_action="Run raya build after a builder exists",
        )
    return report


def _load_mapping(path: Path, report: ValidationReport) -> dict[str, Any] | None:
    report.read_file(path)
    try:
        data = load_yaml_file(path)
    except Exception as exc:
        report.add_error(
            f"Could not read YAML: {exc}",
            path=path,
            next_action="Fix YAML syntax",
        )
        return None
    if not isinstance(data, dict):
        report.add_error(
            "YAML document must be a mapping",
            path=path,
            next_action="Use key/value configuration fields",
        )
        return None
    return data


def _validate_schema(
    data: dict[str, Any],
    schema_name: str,
    path: Path,
    report: ValidationReport,
) -> None:
    validator = validator_for(schema_name)
    for error in sorted(validator.iter_errors(data), key=_schema_error_key):
        report.add_error(
            _schema_error_message(error),
            path=path,
            field=".".join(str(part) for part in error.absolute_path) or None,
            next_action="Update the file to match the schema",
        )


def _validate_official_objects(
    *,
    official_dir: Path,
    valid_scopes: set[str],
    report: ValidationReport,
) -> None:
    object_validator = validator_for("official-learning-object.schema.json")
    seen_ids: dict[str, Path] = {}
    by_type: dict[str, list[Path]] = defaultdict(list)

    for object_path in sorted(
        path
        for path in official_dir.rglob("*")
        if path.suffix.lower() in {".yaml", ".yml", ".json"}
    ):
        data = _load_mapping(object_path, report)
        if data is None:
            continue

        for error in sorted(object_validator.iter_errors(data), key=_schema_error_key):
            report.add_error(
                _schema_error_message(error),
                path=object_path,
                field=".".join(str(part) for part in error.absolute_path) or None,
                next_action="Update the official learning object",
            )

        object_id = data.get("id")
        object_type = data.get("type")
        if isinstance(object_type, str):
            by_type[object_type].append(object_path)
            if object_type not in SUPPORTED_OBJECT_TYPES:
                report.add_error(
                    "Unsupported official learning object type",
                    path=object_path,
                    field="type",
                    next_action="Use a supported official learning object type",
                )

        if isinstance(object_id, str):
            if object_id in seen_ids:
                report.add_error(
                    "Duplicate official learning object ID",
                    path=object_path,
                    field="id",
                    next_action=f"Use a unique object ID; first seen in {seen_ids[object_id]}",
                )
            else:
                seen_ids[object_id] = object_path

        scope = data.get("scope")
        quantum = scope.get("quantum") if isinstance(scope, dict) else None
        if isinstance(quantum, str) and quantum not in valid_scopes:
            report.add_error(
                "Official learning object references an unknown quantum scope",
                path=object_path,
                field="scope.quantum",
                next_action="Point scope.quantum to a content path or explicit quantum ID",
            )

    for object_type, paths in sorted(by_type.items()):
        report.add_info(
            f"Found official {object_type} object(s)",
            path=paths[0] if paths else official_dir,
        )


def _validate_markdown_source_links(
    *,
    md_path: Path,
    body: str,
    course_root: Path,
    content_dir: Path,
    assets_dir: Path,
    report: ValidationReport,
) -> None:
    for link in extract_markdown_links(body):
        kind = classify_markdown_target(link.target)
        if kind == "ignored":
            continue

        target_text = markdown_link_path(link.target)
        target_path = resolve_local_markdown_target(
            source_path=md_path,
            course_root=course_root,
            target_path=target_text,
        )
        field = f"link:{link.target}"
        if kind == "content":
            if not path_is_under(target_path, content_dir) or not target_path.is_file():
                report.add_error(
                    "Broken local content link",
                    path=md_path,
                    field=field,
                    next_action=(
                        f"Create {target_path} or update the link to an existing "
                        f"Markdown file under {content_dir.name}/"
                    ),
                )
            else:
                report.read_file(target_path)
            continue

        if not path_is_under(target_path, assets_dir):
            report.add_error(
                "Local asset reference is outside the assets directory",
                path=md_path,
                field=field,
                next_action=(
                    f"Move the asset under {assets_dir.name}/ or update the link "
                    f"to point under the configured assets directory"
                ),
            )
        elif not target_path.is_file():
            report.add_error(
                "Missing local asset reference",
                path=md_path,
                field=field,
                next_action=(
                    f"Create {target_path} or update the link to an existing "
                    f"asset under {assets_dir.name}/"
                ),
            )
        else:
            report.read_file(target_path)


def _markdown_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return text
    marker = "\n---"
    end = text.find(marker, 4)
    if end == -1:
        return text
    body = text[end + len(marker) :]
    return body[1:] if body.startswith("\n") else body


def _schema_error_key(error: ValidationError) -> tuple[str, str]:
    return (".".join(str(part) for part in error.absolute_path), error.message)


def _schema_error_message(error: ValidationError) -> str:
    return error.message
