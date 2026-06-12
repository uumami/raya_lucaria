from __future__ import annotations

import json
import hashlib
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from raya_schema import ValidationReport, validate_course
from raya_schema.content import resolve_course_content
from raya_schema.course import resolve_course_source_root
from raya_schema.reviewed import (
    REVIEWED_MANIFEST_NAME,
    cache_entries_by_reference,
    collect_source_references,
    discover_reviewed_outputs,
    freshness_for_reference,
    reviewed_outputs_by_reference,
)
from raya_schema.runtime import load_runtime_model

from raya_cli.execution import (
    EXECUTION_RESULTS_PATH,
    ResolvedExecutionTarget,
    _load_config,
    _merge_report,
    _resolve_target,
)


def list_course_outputs(course_path: str | Path) -> ValidationReport:
    context = _course_output_context(course_path, context="outputs")
    report = context["report"]
    if not report.ok:
        return report

    course_id = context["course_id"]
    artifact_dir = context["artifact_dir"]
    references = context["references"]
    runtime_model = context["runtime_model"]
    reviewed_outputs = context["reviewed_outputs"]
    generated_results = _generated_results(artifact_dir / EXECUTION_RESULTS_PATH, report)
    current_reviewed = reviewed_outputs_by_reference(reviewed_outputs)

    if generated_results is None:
        report.add_info(
            "Generated execution results are not available",
            path=artifact_dir / EXECUTION_RESULTS_PATH,
            next_action="Run an explicit target with raya run before freezing generated output",
        )
        generated_results = []

    generated_by_reference = _latest_results_by_reference(generated_results, references, runtime_model)
    for reference in references:
        runtime_target = runtime_model.target_for_source(reference.source_path)
        target_label = runtime_target.id if runtime_target is not None else reference.id
        generated = generated_by_reference.get(reference.id)
        generated_status = _generated_status(generated, artifact_dir)
        reviewed = current_reviewed.get(reference.id)
        reviewed_status = "current" if reviewed is not None else "missing"
        frozen_status = (
            "valid"
            if reference.execution_policy == "frozen" and reviewed is not None
            else "missing"
            if reference.execution_policy == "frozen"
            else "not-frozen"
        )
        details = [
            f"target={target_label}",
            f"policy={reference.execution_policy}",
            f"generated={generated_status}",
            f"reviewed={reviewed_status}",
            f"frozen={frozen_status}",
        ]
        if generated is not None and isinstance(generated.get("output_path"), str):
            details.append(f"generated_path={generated['output_path']}")
        if reviewed is not None:
            details.append(f"reviewed_path={reviewed.manifest_rel_path}")
        report.add_info(
            "Execution output status",
            path=reference.source_path,
            field=target_label,
            next_action="; ".join(details),
        )

    if report.ok:
        report.add_info(
            "Output listing passed",
            path=Path(course_path).resolve(),
            next_action=f"Read {EXECUTION_RESULTS_PATH.as_posix()} or _reviewed/ for details",
        )
    return report


def freeze_course_output(course_path: str | Path, target: str) -> ValidationReport:
    context = _course_output_context(course_path, context="outputs")
    report = context["report"]
    if not report.ok:
        return report

    root = context["root"]
    course_id = context["course_id"]
    source_dir = context["source_dir"]
    artifact_dir = context["artifact_dir"]
    references = context["references"]
    runtime_model = context["runtime_model"]
    cache_entries = context["cache_entries"]

    resolved = _resolve_target(
        target,
        references=references,
        runtime_model=runtime_model,
        cache_entries=cache_entries,
        course_root=root,
        source_dir=source_dir,
    )
    if resolved is None:
        report.add_error(
            "Output target was not found",
            path=root,
            field=target,
            next_action="Use a validated reference ID, runtime target ID, or source path",
        )
        return report

    results = _generated_results(artifact_dir / EXECUTION_RESULTS_PATH, report)
    if results is None:
        report.add_error(
            "Generated execution result is missing",
            path=artifact_dir / EXECUTION_RESULTS_PATH,
            field=target,
            next_action=f"Run raya run {root} {target} before freezing reviewed output",
        )
        return report
    result = _latest_result_for_target(results, resolved, root)
    if result is None:
        report.add_error(
            "Generated execution result is missing",
            path=artifact_dir / EXECUTION_RESULTS_PATH,
            field=target,
            next_action=f"Run raya run {root} {target} before freezing reviewed output",
        )
        return report
    if result.get("status") not in {"succeeded", "cached"}:
        report.add_error(
            "Generated execution result is not successful",
            path=artifact_dir / EXECUTION_RESULTS_PATH,
            field=target,
            next_action="Fix the target and rerun it successfully before freezing",
        )
        return report

    output_path_value = result.get("output_path")
    if not isinstance(output_path_value, str):
        report.add_error(
            "Generated execution result has no output file",
            path=artifact_dir / EXECUTION_RESULTS_PATH,
            field=target,
            next_action="Rerun the target so the generated output file is recorded",
        )
        return report
    generated_output = (artifact_dir / output_path_value).resolve()
    try:
        generated_output.relative_to(artifact_dir.resolve())
    except ValueError:
        report.add_error(
            "Generated execution output path escapes artifact root",
            path=artifact_dir / EXECUTION_RESULTS_PATH,
            field="output_path",
            next_action="Remove malformed generated execution results and rerun the target",
        )
        return report
    if not generated_output.is_file():
        report.add_error(
            "Generated execution output file is missing",
            path=generated_output,
            field=target,
            next_action="Rerun the target before freezing reviewed output",
        )
        return report

    freshness = freshness_for_reference(
        course_root=root,
        reference=resolved.reference,
        runtime_model=runtime_model,
        cache_entry=resolved.cache_entry,
    )
    if not _generated_result_is_current(result, freshness, resolved):
        report.add_error(
            "Generated execution result is stale",
            path=artifact_dir / EXECUTION_RESULTS_PATH,
            field=target,
            next_action="Rerun the explicit target before freezing reviewed output",
        )
        return report

    review_id = (
        resolved.runtime_target.id if resolved.runtime_target is not None else resolved.reference.id
    )
    reviewed_dir = (
        (source_dir / resolved.reference.page_source_path).parent
        / "_reviewed"
        / "execution"
        / _safe_name(review_id)
    )
    reviewed_dir.mkdir(parents=True, exist_ok=True)
    report.wrote_output(reviewed_dir)
    output_name = "stdout.txt" if resolved.reference.kind == "code" else generated_output.name
    reviewed_file = reviewed_dir / output_name
    shutil.copy2(generated_output, reviewed_file)
    report.wrote_output(reviewed_file)

    reviewed_file_sha = _file_sha256(reviewed_file)
    manifest = _reviewed_manifest(
        review_id=review_id,
        resolved=resolved,
        freshness=freshness,
        output_name=output_name,
        output_kind="stdout" if resolved.reference.kind == "code" else "notebook",
        output_sha256=reviewed_file_sha,
    )
    manifest_path = reviewed_dir / REVIEWED_MANIFEST_NAME
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )
    report.wrote_output(manifest_path)

    verification_report = ValidationReport(context="outputs")
    discover_reviewed_outputs(
        course_id=course_id,
        course_root=root,
        source_dir=source_dir,
        runtime_model=runtime_model,
        references=references,
        report=verification_report,
        require_frozen=False,
    )
    _merge_report(report, verification_report)
    if report.ok:
        report.add_info(
            "Reviewed output frozen",
            path=manifest_path,
            field=target,
            next_action="Review and commit the _reviewed/ files before treating them as course truth",
        )
    return report


def _course_output_context(course_path: str | Path, *, context: str) -> dict[str, Any]:
    root = Path(course_path).resolve()
    report = ValidationReport(context=context)

    validation_report = validate_course(root)
    validation_report.context = context
    _merge_report(report, validation_report)
    if not validation_report.ok:
        return {"report": report}

    config = _load_config(root / "raya.yaml", report)
    if config is None:
        return {"report": report}
    course_id = str(config.get("course_id", "unknown-course"))
    source_dir = resolve_course_source_root(root=root, config=config, report=report)
    if source_dir is None:
        return {"report": report}
    runtime_model = load_runtime_model(root, report)
    content_model = resolve_course_content(
        course_root=root,
        content_dir=source_dir,
        course_id=course_id,
        config=config,
        report=report,
    )
    if not report.ok:
        return {"report": report}
    references = collect_source_references(
        course_id=course_id,
        content_model=content_model,
        course_root=root,
        source_dir=source_dir,
        runtime_model=runtime_model,
        report=report,
    )
    cache_entries = cache_entries_by_reference(course_id, references, runtime_model)
    reviewed_outputs = discover_reviewed_outputs(
        course_id=course_id,
        course_root=root,
        source_dir=source_dir,
        runtime_model=runtime_model,
        references=references,
        report=report,
        require_frozen=False,
    )
    artifact_dir = (root / str(config.get("artifact", "artifact"))).resolve()
    return {
        "report": report,
        "root": root,
        "course_id": course_id,
        "source_dir": source_dir,
        "runtime_model": runtime_model,
        "references": references,
        "cache_entries": cache_entries,
        "reviewed_outputs": reviewed_outputs,
        "artifact_dir": artifact_dir,
    }


def _generated_results(path: Path, report: ValidationReport) -> list[dict[str, Any]] | None:
    if not path.exists():
        return None
    report.read_file(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        report.add_error(
            f"Could not read generated execution results: {exc}",
            path=path,
            next_action="Remove malformed generated results and rerun the target",
        )
        return None
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        report.add_error(
            "Generated execution results are malformed",
            path=path,
            next_action="Rerun the explicit target to regenerate execution-results.json",
        )
        return None
    return [item for item in data["results"] if isinstance(item, dict)]


def _latest_results_by_reference(
    results: list[dict[str, Any]],
    references: list[Any],
    runtime_model: Any,
) -> dict[str, dict[str, Any]]:
    by_reference: dict[str, dict[str, Any]] = {}
    for reference in references:
        by_reference[reference.id] = (
            _latest_result_for_reference(results, reference, runtime_model) or {}
        )
    return {key: value for key, value in by_reference.items() if value}


def _latest_result_for_target(
    results: list[dict[str, Any]],
    resolved: ResolvedExecutionTarget,
    course_root: Path,
) -> dict[str, Any] | None:
    runtime_id = resolved.runtime_target.id if resolved.runtime_target is not None else None
    source_root_rel = resolved.reference.source_path.relative_to(course_root).as_posix()
    matches = [
        result
        for result in results
        if result.get("target_id") == resolved.reference.id
        or result.get("reference_id") == resolved.reference.id
        or (runtime_id is not None and result.get("runtime_target_id") == runtime_id)
        or result.get("source_path") == source_root_rel
    ]
    return matches[-1] if matches else None


def _latest_result_for_reference(
    results: list[dict[str, Any]],
    reference: Any,
    runtime_model: Any,
) -> dict[str, Any] | None:
    runtime_target = runtime_model.target_for_source(reference.source_path)
    runtime_id = runtime_target.id if runtime_target is not None else None
    matches = [
        result
        for result in results
        if result.get("target_id") == reference.id
        or result.get("reference_id") == reference.id
        or (runtime_id is not None and result.get("runtime_target_id") == runtime_id)
    ]
    return matches[-1] if matches else None


def _generated_status(result: dict[str, Any] | None, artifact_dir: Path) -> str:
    if result is None:
        return "missing"
    status = str(result.get("status") or "unknown")
    output_path = result.get("output_path")
    if isinstance(output_path, str) and not (artifact_dir / output_path).is_file():
        return f"{status}:missing-file"
    return status


def _generated_result_is_current(
    result: dict[str, Any],
    freshness: dict[str, Any],
    resolved: ResolvedExecutionTarget,
) -> bool:
    for field_name in (
        "source_sha256",
        "input_hashes",
        "runtime_profile_sha256",
        "lockfile_sha256",
        "review_key",
    ):
        expected = freshness.get(field_name)
        if result.get(field_name) != expected:
            return False
    if resolved.cache_entry is not None:
        expected_cache_key = resolved.cache_entry.get("cache_key")
        if isinstance(expected_cache_key, str) and result.get("cache_key") != expected_cache_key:
            return False
    return True


def _reviewed_manifest(
    *,
    review_id: str,
    resolved: ResolvedExecutionTarget,
    freshness: dict[str, Any],
    output_name: str,
    output_kind: str,
    output_sha256: str,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": review_id,
        "target_id": resolved.reference.id,
        "reference_id": resolved.reference.id,
        "source_path": freshness["source_path"],
        "kind": resolved.reference.kind,
        "policy": resolved.policy,
        "source_sha256": freshness["source_sha256"],
        "input_hashes": freshness["input_hashes"],
        "review_key": freshness["review_key"],
        "reviewed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "outputs": [
            {
                "path": output_name,
                "kind": output_kind,
                "sha256": output_sha256,
            }
        ],
    }
    if resolved.runtime_target is not None:
        data["runtime_target_id"] = resolved.runtime_target.id
    for field_name in (
        "profile",
        "runtime_profile_sha256",
        "lockfile_sha256",
        "cache_key",
    ):
        value = freshness.get(field_name)
        if value is not None:
            data[field_name] = value
    return data


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "target"


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()
