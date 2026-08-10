from __future__ import annotations

from datetime import date, time
from pathlib import Path
from typing import Any

from raya_schema.diagnostics import ValidationReport
from raya_schema.numbered_objects import validate_numbered_objects_index
from raya_schema.schema_loader import validator_for
from raya_schema.yaml_io import load_yaml_file


def inspect_artifact(artifact_path: str | Path) -> ValidationReport:
    path = Path(artifact_path).resolve()
    root = path.parent if path.is_file() and path.name == "manifest.json" else path
    report = ValidationReport(context="artifact")

    if not root.exists():
        report.add_error(
            "Artifact path does not exist",
            path=root,
            next_action="Pass an existing artifact directory",
        )
        return report
    if not root.is_dir():
        report.add_error(
            "Artifact path must be a directory or manifest.json",
            path=root,
            next_action="Pass an artifact directory or its manifest.json",
        )
        return report

    manifest_path = root / "manifest.json"
    for required_path, description in (
        (manifest_path, "Artifact manifest is missing"),
        (root / "site", "Artifact site directory is missing"),
        (root / "data", "Artifact data directory is missing"),
        (root / "assets", "Artifact assets directory is missing"),
    ):
        if not required_path.exists():
            report.add_error(
                description,
                path=required_path,
                next_action="Rebuild the artifact or inspect a complete artifact directory",
            )

    manifest_report = validate_artifact_manifest(manifest_path)
    _merge_report(report, manifest_report)
    if not manifest_report.ok:
        return report

    try:
        manifest = load_yaml_file(manifest_path)
    except Exception:
        return report
    if not isinstance(manifest, dict):
        return report

    data_paths = manifest.get("data")
    if not isinstance(data_paths, dict):
        return report

    validators = {
        "pages": validate_pages_index,
        "quanta": validate_quanta_index,
        "links": validate_links_index,
        "graph": validate_graph_index,
        "navigation": validate_navigation_index,
        "indices": validate_indices_index,
        "official": validate_official_index,
        "calendar": validate_calendar_index,
        "tasks": validate_tasks_index,
        "search_index": validate_search_index,
        "references": validate_references_index,
        "reviewed_outputs": validate_reviewed_outputs_index,
        "numbered_objects": validate_numbered_objects_index,
        "runtime": validate_runtime_index,
        "execution": validate_execution_index,
        "execution_results": validate_execution_results_index,
        "cache": validate_cache_index,
    }
    for key, validator in validators.items():
        declared_path = data_paths.get(key)
        if not isinstance(declared_path, str):
            continue
        index_path = _manifest_relative_path(root, key, declared_path, report)
        if index_path is None:
            continue
        validation_report = validator(index_path)
        _merge_report(report, validation_report)
        if key == "references" and validation_report.ok:
            _validate_reference_files(root, index_path, report)
        if key == "reviewed_outputs" and validation_report.ok:
            _validate_reviewed_output_files(root, index_path, report)
        if key in {"runtime", "execution", "cache"} and validation_report.ok:
            _validate_metadata_paths(key, index_path, report)
        if key == "execution_results" and validation_report.ok:
            _validate_execution_result_files(root, index_path, report)

    if report.ok:
        report.add_info(
            "Artifact inspection passed",
            path=root,
            next_action="Artifact can be served as static files or read through manifest.json",
        )
    return report


def validate_artifact_manifest(manifest_path: str | Path) -> ValidationReport:
    path = Path(manifest_path).resolve()
    report = ValidationReport(context="artifact")

    if not path.exists():
        report.add_error(
            "Artifact manifest does not exist",
            path=path,
            next_action="Create manifest.json in the artifact root",
        )
        return report

    report.read_file(path)
    try:
        data = load_yaml_file(path)
    except Exception as exc:
        report.add_error(
            f"Could not read manifest: {exc}",
            path=path,
            next_action="Fix manifest JSON/YAML syntax",
        )
        return report

    if not isinstance(data, dict):
        report.add_error(
            "Artifact manifest must be an object",
            path=path,
            next_action="Use key/value manifest fields",
        )
        return report

    validator = validator_for("artifact-manifest.schema.json")
    for error in sorted(
        validator.iter_errors(data),
        key=lambda item: (".".join(str(part) for part in item.absolute_path), item.message),
    ):
        report.add_error(
            error.message,
            path=path,
            field=".".join(str(part) for part in error.absolute_path) or None,
            next_action="Update manifest.json to match the artifact contract",
        )

    if report.ok:
        report.add_info(
            "Artifact manifest validation passed",
            path=path,
        )
    return report


def validate_pages_index(index_path: str | Path) -> ValidationReport:
    return validate_artifact_index(index_path, "pages-index.schema.json")


def validate_quanta_index(index_path: str | Path) -> ValidationReport:
    return validate_artifact_index(index_path, "quanta-index.schema.json")


def validate_links_index(index_path: str | Path) -> ValidationReport:
    return validate_artifact_index(index_path, "links-index.schema.json")


def validate_graph_index(index_path: str | Path) -> ValidationReport:
    return validate_artifact_index(index_path, "graph-index.schema.json")


def validate_navigation_index(index_path: str | Path) -> ValidationReport:
    return validate_artifact_index(index_path, "navigation-index.schema.json")


def validate_indices_index(index_path: str | Path) -> ValidationReport:
    return validate_artifact_index(index_path, "indices-index.schema.json")


def validate_official_index(index_path: str | Path) -> ValidationReport:
    return validate_artifact_index(index_path, "official-index.schema.json")


def validate_tasks_index(index_path: str | Path) -> ValidationReport:
    return validate_artifact_index(index_path, "tasks-index.schema.json")


def validate_search_index(index_path: str | Path) -> ValidationReport:
    return validate_artifact_index(index_path, "search-index.schema.json")


def validate_references_index(index_path: str | Path) -> ValidationReport:
    return validate_artifact_index(index_path, "references-index.schema.json")


def validate_reviewed_outputs_index(index_path: str | Path) -> ValidationReport:
    return validate_artifact_index(index_path, "reviewed-outputs.schema.json")


def validate_runtime_index(index_path: str | Path) -> ValidationReport:
    return validate_artifact_index(index_path, "runtime-index.schema.json")


def validate_execution_index(index_path: str | Path) -> ValidationReport:
    return validate_artifact_index(index_path, "execution-index.schema.json")


def validate_execution_results_index(index_path: str | Path) -> ValidationReport:
    return validate_artifact_index(index_path, "execution-results.schema.json")


def validate_cache_index(index_path: str | Path) -> ValidationReport:
    return validate_artifact_index(index_path, "cache-index.schema.json")


def validate_calendar_index(index_path: str | Path) -> ValidationReport:
    report = validate_artifact_index(index_path, "calendar-index.schema.json")
    if not report.ok:
        return report

    path = Path(index_path).resolve()
    data = load_yaml_file(path)
    if not isinstance(data, dict):
        return report
    _validate_calendar_index_semantics(data, path, report)
    return report


def _validate_calendar_index_semantics(
    data: dict[str, Any],
    path: Path,
    report: ValidationReport,
) -> None:
    events = data.get("events")
    if not isinstance(events, list):
        return
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            continue
        date_value = event.get("date")
        if isinstance(date_value, str):
            try:
                date.fromisoformat(date_value)
            except ValueError:
                report.add_error(
                    "Calendar event date must be a valid ISO civil date",
                    path=path,
                    field=f"events.{index}.date",
                    next_action="Use a valid date such as 2026-08-10",
                )

        start_time = _calendar_index_time(
            event.get("start_time"),
            index=index,
            field="start_time",
            path=path,
            report=report,
        )
        end_time = _calendar_index_time(
            event.get("end_time"),
            index=index,
            field="end_time",
            path=path,
            report=report,
        )
        if event.get("end_time") is not None and event.get("start_time") is None:
            report.add_error(
                "Calendar event end_time requires start_time",
                path=path,
                field=f"events.{index}.end_time",
                next_action="Set start_time before setting end_time",
            )
        if start_time is not None and end_time is not None and end_time <= start_time:
            report.add_error(
                "Calendar event end_time must be later than start_time",
                path=path,
                field=f"events.{index}.end_time",
                next_action="Set end_time later than start_time on the same date",
            )


def _calendar_index_time(
    value: Any,
    *,
    index: int,
    field: str,
    path: Path,
    report: ValidationReport,
) -> time | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    try:
        return time.fromisoformat(value)
    except ValueError:
        report.add_error(
            "Calendar event time must be a valid local 24-hour time",
            path=path,
            field=f"events.{index}.{field}",
            next_action="Use a time such as 16:00",
        )
        return None


def validate_artifact_index(index_path: str | Path, schema_name: str) -> ValidationReport:
    path = Path(index_path).resolve()
    report = ValidationReport(context="artifact")

    if not path.exists():
        report.add_error(
            "Artifact data index does not exist",
            path=path,
            next_action="Create the generated data index or update manifest.json",
        )
        return report

    report.read_file(path)
    try:
        data = load_yaml_file(path)
    except Exception as exc:
        report.add_error(
            f"Could not read artifact data index: {exc}",
            path=path,
            next_action="Fix generated data syntax",
        )
        return report

    if not isinstance(data, dict):
        report.add_error(
            "Artifact data index must be an object",
            path=path,
            next_action="Use key/value index fields",
        )
        return report

    validator = validator_for(schema_name)
    for error in sorted(
        validator.iter_errors(data),
        key=lambda item: (".".join(str(part) for part in item.absolute_path), item.message),
    ):
        report.add_error(
            error.message,
            path=path,
            field=".".join(str(part) for part in error.absolute_path) or None,
            next_action=f"Update data index to match {schema_name}",
        )

    if report.ok:
        report.add_info(
            "Artifact data index validation passed",
            path=path,
        )
    return report


def _manifest_relative_path(
    artifact_root: Path,
    key: str,
    declared_path: str,
    report: ValidationReport,
) -> Path | None:
    raw_path = Path(declared_path)
    if raw_path.is_absolute():
        report.add_error(
            "Manifest data path must be relative",
            path=artifact_root / "manifest.json",
            field=f"data.{key}",
            next_action="Use artifact-relative data paths",
        )
        return None

    resolved = (artifact_root / raw_path).resolve()
    try:
        resolved.relative_to(artifact_root)
    except ValueError:
        report.add_error(
            "Manifest data path escapes artifact root",
            path=artifact_root / "manifest.json",
            field=f"data.{key}",
            next_action="Keep manifest data paths inside the artifact directory",
        )
        return None
    return resolved


def _validate_reference_files(
    artifact_root: Path,
    index_path: Path,
    report: ValidationReport,
) -> None:
    try:
        data = load_yaml_file(index_path)
    except Exception:
        return
    if not isinstance(data, dict):
        return
    references = data.get("references")
    if not isinstance(references, list):
        return
    for index, item in enumerate(references):
        if not isinstance(item, dict):
            continue
        artifact_path = item.get("artifact_path")
        if isinstance(artifact_path, str):
            _validate_manifest_relative_file(
                artifact_root,
                artifact_path,
                report,
                field=f"references.{index}.artifact_path",
            )
        browser_path = item.get("browser_path")
        if isinstance(browser_path, str):
            _validate_manifest_relative_file(
                artifact_root / "site",
                browser_path,
                report,
                field=f"references.{index}.browser_path",
            )


def _validate_reviewed_output_files(
    artifact_root: Path,
    index_path: Path,
    report: ValidationReport,
) -> None:
    try:
        data = load_yaml_file(index_path)
    except Exception:
        return
    if not isinstance(data, dict):
        return
    outputs = data.get("outputs")
    if not isinstance(outputs, list):
        return
    for output_index, item in enumerate(outputs):
        if not isinstance(item, dict):
            continue
        source_path = item.get("source_path")
        if isinstance(source_path, str):
            _validate_relative_metadata_path(
                source_path,
                report,
                path=index_path,
                field=f"outputs.{output_index}.source_path",
            )
        files = item.get("files")
        if not isinstance(files, list):
            continue
        for file_index, file_item in enumerate(files):
            if not isinstance(file_item, dict):
                continue
            artifact_path = file_item.get("artifact_path")
            if isinstance(artifact_path, str):
                _validate_manifest_relative_file(
                    artifact_root,
                    artifact_path,
                    report,
                    field=f"outputs.{output_index}.files.{file_index}.artifact_path",
                )
            browser_path = file_item.get("browser_path")
            if isinstance(browser_path, str):
                _validate_manifest_relative_file(
                    artifact_root / "site",
                    browser_path,
                    report,
                    field=f"outputs.{output_index}.files.{file_index}.browser_path",
                )


def _validate_metadata_paths(
    key: str,
    index_path: Path,
    report: ValidationReport,
) -> None:
    try:
        data = load_yaml_file(index_path)
    except Exception:
        return
    if not isinstance(data, dict):
        return
    if key == "runtime":
        for index, profile in enumerate(data.get("profiles", [])):
            if not isinstance(profile, dict):
                continue
            for field_name in ("project", "lockfile"):
                value = profile.get(field_name)
                if isinstance(value, str):
                    _validate_relative_metadata_path(
                        value,
                        report,
                        path=index_path,
                        field=f"profiles.{index}.{field_name}",
                    )
        return
    if key == "execution":
        for index, target in enumerate(data.get("targets", [])):
            if not isinstance(target, dict):
                continue
            source_path = target.get("source_path")
            if isinstance(source_path, str):
                _validate_relative_metadata_path(
                    source_path,
                    report,
                    path=index_path,
                    field=f"targets.{index}.source_path",
                )
            inputs = target.get("inputs")
            if isinstance(inputs, list):
                for input_index, input_path in enumerate(inputs):
                    if isinstance(input_path, str):
                        _validate_relative_metadata_path(
                            input_path,
                            report,
                            path=index_path,
                            field=f"targets.{index}.inputs.{input_index}",
                        )
        return
    if key == "cache":
        for index, entry in enumerate(data.get("entries", [])):
            if not isinstance(entry, dict):
                continue
            source_path = entry.get("source_path")
            if isinstance(source_path, str):
                _validate_relative_metadata_path(
                    source_path,
                    report,
                    path=index_path,
                    field=f"entries.{index}.source_path",
                )
            input_hashes = entry.get("input_hashes")
            if isinstance(input_hashes, list):
                for input_index, item in enumerate(input_hashes):
                    if not isinstance(item, dict):
                        continue
                    input_path = item.get("path")
                    if isinstance(input_path, str):
                        _validate_relative_metadata_path(
                            input_path,
                            report,
                            path=index_path,
                            field=f"entries.{index}.input_hashes.{input_index}.path",
                        )


def _validate_execution_result_files(
    artifact_root: Path,
    index_path: Path,
    report: ValidationReport,
) -> None:
    try:
        data = load_yaml_file(index_path)
    except Exception:
        return
    if not isinstance(data, dict):
        return
    results = data.get("results")
    if not isinstance(results, list):
        return
    for index, item in enumerate(results):
        if not isinstance(item, dict):
            continue
        source_path = item.get("source_path")
        if isinstance(source_path, str):
            _validate_relative_metadata_path(
                source_path,
                report,
                path=index_path,
                field=f"results.{index}.source_path",
            )
        for field_name in (
            "output_path",
            "log_path",
            "stdout_path",
            "stderr_path",
            "cache_result_path",
        ):
            declared_path = item.get(field_name)
            if isinstance(declared_path, str):
                _validate_manifest_relative_file(
                    artifact_root,
                    declared_path,
                    report,
                    field=f"results.{index}.{field_name}",
                )


def _validate_relative_metadata_path(
    declared_path: str,
    report: ValidationReport,
    *,
    path: Path,
    field: str,
) -> None:
    raw_path = Path(declared_path)
    if raw_path.is_absolute() or ".." in raw_path.parts:
        report.add_error(
            "Runtime metadata path must be relative and stay inside course source",
            path=path,
            field=field,
            next_action="Use a generated relative path without .. segments",
        )


def _validate_manifest_relative_file(
    root: Path,
    declared_path: str,
    report: ValidationReport,
    *,
    field: str,
) -> None:
    path = Path(declared_path)
    if path.is_absolute():
        report.add_error(
            "Reference file path must be relative",
            path=root,
            field=field,
            next_action="Use a generated artifact-relative reference path",
        )
        return
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        report.add_error(
            "Reference file path escapes artifact root",
            path=root,
            field=field,
            next_action="Keep reference file paths inside generated artifact output",
        )
        return
    if not resolved.is_file():
        report.add_error(
            "Referenced artifact file is missing",
            path=resolved,
            field=field,
            next_action="Rebuild the artifact so referenced files are copied",
        )


def _merge_report(target: ValidationReport, source: ValidationReport) -> None:
    for path in source.files_read:
        target.read_file(path)
    for path in source.outputs_written:
        target.wrote_output(path)
    target.diagnostics.extend(source.diagnostics)
