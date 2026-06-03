from __future__ import annotations

from pathlib import Path
from typing import Any

from raya_schema.diagnostics import ValidationReport
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
        "official": validate_official_index,
    }
    for key, validator in validators.items():
        declared_path = data_paths.get(key)
        if not isinstance(declared_path, str):
            continue
        index_path = _manifest_relative_path(root, key, declared_path, report)
        if index_path is None:
            continue
        _merge_report(report, validator(index_path))

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


def validate_official_index(index_path: str | Path) -> ValidationReport:
    return validate_artifact_index(index_path, "official-index.schema.json")


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


def _merge_report(target: ValidationReport, source: ValidationReport) -> None:
    for path in source.files_read:
        target.read_file(path)
    for path in source.outputs_written:
        target.wrote_output(path)
    target.diagnostics.extend(source.diagnostics)
