from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import ValidationError

from raya_schema.diagnostics import ValidationReport
from raya_schema.content import markdown_body, resolve_course_content
from raya_schema.links import (
    classify_markdown_target,
    extract_markdown_links,
    markdown_link_path,
    path_is_under,
    resolve_course_asset_reference,
    resolve_local_markdown_target,
    stable_markdown_id,
)
from raya_schema.official import discover_official_objects
from raya_schema.references import (
    notebook_validation_error,
    reference_format,
    resolve_course_reference,
)
from raya_schema.runtime import load_runtime_model
from raya_schema.schema_loader import validator_for
from raya_schema.yaml_io import load_yaml_file


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

    source_root = resolve_course_source_root(root=root, config=config, report=report)
    if source_root is None:
        return report
    source_dir = source_root
    if not source_dir.exists() or not source_dir.is_dir():
        report.add_error(
            "Configured authored source directory is missing",
            path=source_dir,
            field="source",
            next_action="Create the authored source directory or update raya.yaml",
        )
        return report

    markdown_files = sorted(source_dir.rglob("*.md"))
    if not markdown_files:
        report.add_error(
            "Authored source directory contains no Markdown files",
            path=source_dir,
            next_action="Add at least one rendered Markdown source file",
        )

    course_id = str(config.get("course_id", "unknown-course"))
    content_model = resolve_course_content(
        course_root=root,
        content_dir=source_dir,
        course_id=course_id,
        config=config,
        report=report,
    )
    for page in content_model.pages:
        _validate_markdown_source_links(
            md_path=page.source_path,
            body=page.body,
            course_root=root,
            source_dir=source_dir,
            pages_by_source=content_model.pages_by_source,
            stable_targets=set(content_model.pages_by_id) | set(content_model.pages_by_alias),
            report=report,
        )

    discover_official_objects(
        course_root=root,
        course_id=course_id,
        source_dir=source_dir,
        content_model=content_model,
        report=report,
    )
    load_runtime_model(root, report)

    if report.ok:
        report.add_info(
            "Course validation passed",
            path=root,
            next_action="Run raya build after a builder exists",
        )
    return report


def resolve_course_source_root(
    *,
    root: Path,
    config: dict[str, Any],
    report: ValidationReport,
) -> Path | None:
    config_path = root / "raya.yaml"
    source_value = config.get("source")

    if "content" in config:
        report.add_error(
            "Unsupported course configuration field",
            path=config_path,
            field="content",
            next_action="Use source: course; content: is not part of the new source-course contract",
        )
        return None
    if "assets" in config:
        report.add_error(
            "Unsupported course configuration field",
            path=config_path,
            field="assets",
            next_action="Put source assets under course/_assets/ instead of declaring a root assets directory",
        )
        return None
    for field_name in ("code", "notebooks"):
        if field_name in config:
            report.add_error(
                "Unsupported course configuration field",
                path=config_path,
                field=field_name,
                next_action=(
                    f"Put {field_name}/ support directories under course/ "
                    "beside the quantum they support"
                ),
            )
            return None
    if "runtime" in config:
        report.add_error(
            "Unsupported course configuration field",
            path=config_path,
            field="runtime",
            next_action="Put runtime profiles under runtime/profiles.yaml beside course/",
        )
        return None

    if source_value is not None and not isinstance(source_value, str):
        report.add_error(
            "Course source field must be a string",
            path=config_path,
            field="source",
            next_action="Use a relative path such as source: course",
        )
        return None

    if source_value:
        return (root / source_value).resolve()

    report.add_error(
        "Missing authored source root",
        path=config_path,
        field="source",
        next_action="Add source: course",
    )
    return None


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


def _validate_markdown_source_links(
    *,
    md_path: Path,
    body: str,
    course_root: Path,
    source_dir: Path,
    pages_by_source: dict[Path, Any],
    stable_targets: set[str],
    report: ValidationReport,
) -> None:
    for link in extract_markdown_links(body):
        kind = classify_markdown_target(link.target)
        if kind == "ignored":
            continue
        if kind == "stable":
            stable_id = stable_markdown_id(link.target)
            if stable_id not in stable_targets:
                report.add_error(
                    "Broken stable content reference",
                    path=md_path,
                    field=f"link:{link.target}",
                    next_action=(
                        "Use a raya: link target that matches a rendered page "
                        "frontmatter id or alias"
                    ),
                )
            continue

        target_text = markdown_link_path(link.target)
        target_path = resolve_local_markdown_target(
            source_path=md_path,
            course_root=course_root,
            target_path=target_text,
        )
        field = f"link:{link.target}"
        if kind == "content":
            if target_path.resolve() in pages_by_source:
                report.read_file(target_path)
                report.add_info(
                    "Path content link has a durable raya: alternative",
                    path=md_path,
                    field=field,
                    next_action=(
                        "Use a raya: stable ID link when this reference "
                        "must survive renumbering or moves"
                    ),
                )
            elif not path_is_under(target_path, source_dir) or not target_path.is_file():
                report.add_error(
                    "Broken local content link",
                    path=md_path,
                    field=field,
                    next_action=(
                        f"Create {target_path} or update the link to an existing "
                        f"Markdown file under {source_dir.name}/"
                    ),
                )
            continue

        if kind in {"code", "notebook"}:
            _validate_code_or_notebook_reference(
                md_path=md_path,
                link_target=link.target,
                target_text=target_text,
                kind=kind,
                course_root=course_root,
                source_dir=source_dir,
                report=report,
            )
            continue

        asset_ref = resolve_course_asset_reference(
            source_path=md_path,
            course_root=course_root,
            source_dir=source_dir,
            target_path=target_text,
        )
        if asset_ref.kind == "blocked":
            report.add_error(
                "Local asset reference points to non-asset support material",
                path=md_path,
                field=field,
                next_action=(
                    "Do not link rendered pages directly into _official/, _drafts/, "
                    "_partials/, or other private support paths"
                ),
            )
            continue
        if asset_ref.kind != "colocated":
            report.add_error(
                "Local asset reference is outside supported asset roots",
                path=md_path,
                field=field,
                next_action=(
                    "Move the asset under an own/ancestor _assets/ directory, "
                    "or update the link"
                ),
            )
            continue
        if not asset_ref.target_path.is_file():
            report.add_error(
                "Missing local asset reference",
                path=md_path,
                field=field,
                next_action=(
                    f"Create {asset_ref.target_path} or update the link to an existing "
                    "asset under an own/ancestor _assets/ directory"
                ),
            )
        else:
            report.read_file(asset_ref.target_path)


def _validate_code_or_notebook_reference(
    *,
    md_path: Path,
    link_target: str,
    target_text: str,
    kind: str,
    course_root: Path,
    source_dir: Path,
    report: ValidationReport,
) -> None:
    field = f"link:{link_target}"
    reference = resolve_course_reference(
        source_path=md_path,
        course_root=course_root,
        source_dir=source_dir,
        target_path=target_text,
        kind=kind,
    )
    label = "notebook" if kind == "notebook" else "code"
    support_dir = "notebooks/" if kind == "notebook" else "code/"
    if reference.status == "outside":
        report.add_error(
            f"Local {label} reference escapes the authored source tree",
            path=md_path,
            field=field,
            next_action=(
                f"Move the file under an own/ancestor {support_dir} directory "
                "inside the authored source tree"
            ),
        )
        return
    if reference.status == "blocked":
        report.add_error(
            f"Local {label} reference points to private support material",
            path=md_path,
            field=field,
            next_action=(
                "Do not link rendered pages directly into _official/, _drafts/, "
                "drafts/, _partials/, _assets/, or other private support paths"
            ),
        )
        return
    if reference.status == "cross_owner":
        report.add_error(
            f"Local {label} reference crosses a learning quantum boundary",
            path=md_path,
            field=field,
            next_action=(
                f"Move the file under an own/ancestor {support_dir} directory "
                "or propose an explicit shared-code contract"
            ),
        )
        return
    if reference.status != "referenced":
        report.add_error(
            f"Local {label} reference is outside supported {support_dir} roots",
            path=md_path,
            field=field,
            next_action=(
                f"Move the file under an own/ancestor {support_dir} directory "
                "or update the link"
            ),
        )
        return
    if not reference.target_path.is_file():
        report.add_error(
            f"Missing local {label} reference",
            path=md_path,
            field=field,
            next_action=(
                f"Create {reference.target_path} or update the link to an "
                f"existing {reference_format(kind)} file under {support_dir}"
            ),
        )
        return
    report.read_file(reference.target_path)
    if kind == "notebook":
        error = notebook_validation_error(reference.target_path)
        if error is not None:
            report.add_error(
                "Unreadable notebook reference",
                path=md_path,
                field=field,
                next_action=f"Fix {reference.target_path}: {error}",
            )


def _markdown_body(path: Path) -> str:
    return markdown_body(path)


def _schema_error_key(error: ValidationError) -> tuple[str, str]:
    return (".".join(str(part) for part in error.absolute_path), error.message)


def _schema_error_message(error: ValidationError) -> str:
    return error.message
