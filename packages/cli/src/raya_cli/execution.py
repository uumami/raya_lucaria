from __future__ import annotations

import hashlib
import json
import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from raya_schema import ValidationReport, validate_course
from raya_schema.content import ContentModel, resolve_course_content
from raya_schema.course import resolve_course_source_root
from raya_schema.links import classify_markdown_target, extract_markdown_links, markdown_link_path
from raya_schema.references import (
    SourceReference,
    notebook_validation_error,
    reference_format,
    resolve_course_reference,
    source_reference_id,
)
from raya_schema.runtime import (
    RuntimeModel,
    RuntimeProfile,
    RuntimeTarget,
    cache_index,
    load_runtime_model,
    reference_execution_metadata,
)
from raya_schema.yaml_io import load_yaml_file
from raya_static import build_course


SOURCE_SCHEMA_VERSION = "0.1"
EXECUTION_RESULTS_PATH = Path("data") / "execution-results.json"


@dataclass(frozen=True)
class ResolvedExecutionTarget:
    reference: SourceReference
    runtime_target: RuntimeTarget | None
    cache_entry: dict[str, Any] | None

    @property
    def policy(self) -> str:
        return self.reference.execution_policy

    @property
    def profile_name(self) -> str | None:
        return self.reference.runtime_profile


@dataclass(frozen=True)
class ExecutionPaths:
    output_dir: Path
    output_path: Path
    log_path: Path
    stdout_path: Path
    stderr_path: Path
    cache_result_path: Path | None


def run_course_target(
    course_path: str | Path,
    target: str,
    *,
    dry_run: bool = False,
    refresh: bool = False,
    docker: bool = False,
) -> ValidationReport:
    root = Path(course_path).resolve()
    report = ValidationReport(context="run")

    validation_report = validate_course(root)
    validation_report.context = "run"
    _merge_report(report, validation_report)
    if not validation_report.ok:
        return report

    config = _load_config(root / "raya.yaml", report)
    if config is None:
        return report
    course_id = str(config.get("course_id", "unknown-course"))
    source_dir = resolve_course_source_root(root=root, config=config, report=report)
    if source_dir is None:
        return report

    runtime_model = load_runtime_model(root, report)
    content_model = resolve_course_content(
        course_root=root,
        content_dir=source_dir,
        course_id=course_id,
        config=config,
        report=report,
    )
    if not report.ok:
        return report

    references = _collect_source_references(
        course_id=course_id,
        content_model=content_model,
        course_root=root,
        source_dir=source_dir,
        runtime_model=runtime_model,
        report=report,
    )
    cache_entries = _cache_entries_by_reference(course_id, references, runtime_model)
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
            "Local execution target was not found",
            path=root,
            field=target,
            next_action=(
                "Use a validated reference ID, runtime target ID, or "
                "course-root-relative referenced source path"
            ),
        )
        return report

    if resolved.policy == "never":
        report.add_error(
            "Execution policy refuses local execution",
            path=resolved.reference.source_path,
            field="policy",
            next_action="Change the target policy to manual, cache, or always before running it",
        )
        return report
    if resolved.policy == "frozen":
        report.add_error(
            "Frozen execution policy is not accepted for local runs yet",
            path=resolved.reference.source_path,
            field="policy",
            next_action="Wait for a frozen-output trust contract or use a different policy",
        )
        return report
    if resolved.policy not in {"manual", "cache", "always"}:
        report.add_error(
            "Unsupported local execution policy",
            path=resolved.reference.source_path,
            field="policy",
            next_action="Use manual, cache, or always for explicit local execution",
        )
        return report

    profile = runtime_model.profile_for(resolved.profile_name)
    if profile is None:
        report.add_error(
            "Execution target does not resolve to a runtime profile",
            path=resolved.reference.source_path,
            field="profile",
            next_action="Declare a runtime profile in runtime/profiles.yaml and reference it",
        )
        return report
    if docker and profile.docker_compose_service is None:
        report.add_error(
            "Docker execution requires profile Docker metadata",
            path=runtime_model.source_path or root / "runtime" / "profiles.yaml",
            field=f"profiles.{profile.name}.docker.compose_service",
            next_action="Add docker.compose_service to the runtime profile or omit --docker",
        )
        return report

    artifact_dir = (root / str(config.get("artifact", "artifact"))).resolve()
    paths = _execution_paths(artifact_dir, resolved)
    cache_decision = _cache_decision(artifact_dir, resolved, paths, refresh=refresh)
    command = _command_for_target(
        root=root,
        source_dir=source_dir,
        profile=profile,
        target=resolved,
        paths=paths,
        docker=docker,
    )

    if dry_run:
        report.add_info(
            "Local execution dry run",
            path=resolved.reference.source_path,
            next_action=(
                f"target={resolved.reference.id}; policy={resolved.policy}; "
                f"profile={profile.name}; cache={cache_decision}; command={shlex.join(command)}"
            ),
        )
        if docker:
            report.add_info(
                "Docker command shape resolved",
                path=runtime_model.source_path or root,
                next_action=shlex.join(command),
            )
        return report

    if cache_decision == "hit" and paths.cache_result_path is not None:
        cached_result = _load_json(paths.cache_result_path)
        if isinstance(cached_result, dict):
            result = dict(cached_result)
            result["status"] = "cached"
            _write_execution_result_index(course_id, artifact_dir, result, report)
            report.add_info(
                "Local execution cache hit reused",
                path=paths.cache_result_path,
                next_action=f"Use --refresh to rerun {resolved.reference.id}",
            )
            return report

    _ensure_static_artifact(root, artifact_dir, report)
    if not report.ok:
        return report
    if not docker and shutil.which("uv") is None:
        report.add_error(
            "uv is unavailable",
            path=root,
            next_action="Install uv, put it on PATH, or use --docker with a profile service",
        )
        return report
    if docker and shutil.which("docker") is None:
        report.add_error(
            "Docker is unavailable",
            path=root,
            next_action="Install Docker Compose or omit --docker for local uv execution",
        )
        return report

    _prepare_output_dirs(paths, report)
    started_at = _utc_now()
    completed = subprocess.run(
        command,
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    ended_at = _utc_now()
    _write_text(paths.stdout_path, completed.stdout, report)
    _write_text(paths.stderr_path, completed.stderr, report)
    _write_text(paths.log_path, _combined_log(command, started_at, ended_at, completed), report)
    output_path = _write_execution_output(resolved, paths, completed, report)

    status = "succeeded" if completed.returncode == 0 else "failed"
    if resolved.reference.kind == "notebook" and completed.returncode == 0 and not output_path.exists():
        status = "failed"
        report.add_error(
            "Notebook execution completed without writing an output notebook",
            path=output_path,
            next_action="Check Jupyter nbconvert output settings and runtime profile",
        )
    result = _result_record(
        root=root,
        artifact_dir=artifact_dir,
        target=resolved,
        profile=profile,
        paths=paths,
        command=command,
        status=status,
        exit_code=completed.returncode,
        started_at=started_at,
        ended_at=ended_at,
        output_path=output_path if output_path.exists() else None,
    )
    _write_execution_result_index(course_id, artifact_dir, result, report)
    if resolved.policy == "cache" and status == "succeeded" and paths.cache_result_path is not None:
        _write_json(paths.cache_result_path, result, report)

    if completed.returncode != 0:
        if resolved.reference.kind == "notebook" and _looks_like_missing_jupyter(completed):
            report.add_error(
                "Notebook execution tooling is unavailable",
                path=resolved.reference.source_path,
                next_action="Install Jupyter notebook execution tooling in the selected uv profile",
            )
        report.add_error(
            "Local execution target failed",
            path=resolved.reference.source_path,
            field="exit_code",
            next_action=f"Read {paths.log_path.relative_to(artifact_dir).as_posix()}",
        )
        return report
    if status != "succeeded":
        return report

    report.add_info(
        "Local execution target passed",
        path=resolved.reference.source_path,
        next_action=f"Inspect {EXECUTION_RESULTS_PATH.as_posix()} in the artifact",
    )
    return report


def _load_config(path: Path, report: ValidationReport) -> dict[str, Any] | None:
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


def _collect_source_references(
    *,
    course_id: str,
    content_model: ContentModel,
    course_root: Path,
    source_dir: Path,
    runtime_model: RuntimeModel,
    report: ValidationReport,
) -> list[SourceReference]:
    references: list[SourceReference] = []
    seen: set[tuple[str, Path]] = set()
    for page in content_model.pages:
        for link in extract_markdown_links(page.body):
            kind = classify_markdown_target(link.target)
            if kind not in {"code", "notebook"}:
                continue
            resolved = resolve_course_reference(
                source_path=page.source_path,
                course_root=course_root,
                source_dir=source_dir,
                target_path=markdown_link_path(link.target),
                kind=kind,
            )
            if (
                resolved.status != "referenced"
                or resolved.output_path is None
                or not resolved.target_path.is_file()
            ):
                continue
            if kind == "notebook" and notebook_validation_error(resolved.target_path):
                continue
            key = (page.id, resolved.target_path.resolve())
            if key in seen:
                continue
            seen.add(key)
            source_rel_path = resolved.target_path.relative_to(source_dir).as_posix()
            execution = reference_execution_metadata(
                reference_source_path=resolved.target_path,
                model=runtime_model,
            )
            references.append(
                SourceReference(
                    id=source_reference_id(course_id, page.id, resolved.output_path),
                    page_id=page.id,
                    page_source_path=page.rel_path,
                    label=link.label,
                    target=link.target,
                    kind=kind,
                    format=reference_format(kind),
                    source_path=resolved.target_path,
                    source_rel_path=source_rel_path,
                    output_path=resolved.output_path,
                    artifact_path=(Path("files") / resolved.output_path).as_posix(),
                    browser_path=(Path("_raya") / "files" / resolved.output_path).as_posix(),
                    sha256=_file_sha256(resolved.target_path),
                    execution_policy=execution["policy"],
                    runtime_profile=execution.get("profile"),
                )
            )
            report.read_file(resolved.target_path)
    return references


def _cache_entries_by_reference(
    course_id: str,
    references: list[SourceReference],
    runtime_model: RuntimeModel,
) -> dict[str, dict[str, Any]]:
    data = cache_index(
        course_id,
        references,
        runtime_model,
        schema_version=SOURCE_SCHEMA_VERSION,
    )
    entries: dict[str, dict[str, Any]] = {}
    for item in data.get("entries", []):
        if isinstance(item, dict):
            reference_id = item.get("reference_id") or item.get("target_id")
            if isinstance(reference_id, str):
                entries[reference_id] = item
    return entries


def _resolve_target(
    selected: str,
    *,
    references: list[SourceReference],
    runtime_model: RuntimeModel,
    cache_entries: dict[str, dict[str, Any]],
    course_root: Path,
    source_dir: Path,
) -> ResolvedExecutionTarget | None:
    normalized = _normalize_selector(selected)
    for reference in references:
        runtime_target = runtime_model.target_for_source(reference.source_path)
        root_rel = reference.source_path.relative_to(course_root).as_posix()
        accepted_selectors = {
            reference.id,
            reference.source_rel_path,
            root_rel,
            f"./{root_rel}",
            str(Path(reference.source_rel_path)),
            str(Path(root_rel)),
        }
        if runtime_target is not None:
            accepted_selectors.add(runtime_target.id)
            accepted_selectors.add(runtime_target.source_rel_path)
        if normalized in {_normalize_selector(item) for item in accepted_selectors}:
            return ResolvedExecutionTarget(
                reference=reference,
                runtime_target=runtime_target,
                cache_entry=cache_entries.get(reference.id),
            )

    selected_path = Path(selected)
    if selected_path.is_absolute():
        try:
            absolute = selected_path.resolve().relative_to(source_dir.resolve())
        except ValueError:
            return None
        return _resolve_target(
            absolute.as_posix(),
            references=references,
            runtime_model=runtime_model,
            cache_entries=cache_entries,
            course_root=course_root,
            source_dir=source_dir,
        )
    return None


def _cache_decision(
    artifact_dir: Path,
    target: ResolvedExecutionTarget,
    paths: ExecutionPaths,
    *,
    refresh: bool,
) -> str:
    if target.policy != "cache":
        return "not-applicable"
    if target.cache_entry is None or paths.cache_result_path is None:
        return "miss"
    if refresh:
        return "refresh"
    if _valid_cache_record(paths.cache_result_path, artifact_dir, target.cache_entry):
        return "hit"
    return "miss"


def _valid_cache_record(
    cache_result_path: Path,
    artifact_dir: Path,
    cache_entry: dict[str, Any],
) -> bool:
    data = _load_json(cache_result_path)
    if not isinstance(data, dict):
        return False
    if data.get("cache_key") != cache_entry.get("cache_key"):
        return False
    if data.get("status") != "succeeded":
        return False
    for field_name in ("output_path", "log_path", "stdout_path", "stderr_path"):
        value = data.get(field_name)
        if isinstance(value, str) and not (artifact_dir / value).is_file():
            return False
    return True


def _command_for_target(
    *,
    root: Path,
    source_dir: Path,
    profile: RuntimeProfile,
    target: ResolvedExecutionTarget,
    paths: ExecutionPaths,
    docker: bool,
) -> list[str]:
    source_root_rel = target.reference.source_path.relative_to(root).as_posix()
    if docker:
        service = profile.docker_compose_service or ""
        return [
            "docker",
            "compose",
            "run",
            "--rm",
            service,
            *_uv_args(
                profile,
                source_root_rel=source_root_rel,
                source_dir=source_dir,
                kind=target.reference.kind,
                output_path=paths.output_path,
                output_dir=paths.output_dir,
                docker=True,
            ),
        ]
    return _uv_args(
        profile,
        source_root_rel=source_root_rel,
        source_dir=source_dir,
        kind=target.reference.kind,
        output_path=paths.output_path,
        output_dir=paths.output_dir,
        docker=False,
    )


def _uv_args(
    profile: RuntimeProfile,
    *,
    source_root_rel: str,
    source_dir: Path,
    kind: str,
    output_path: Path,
    output_dir: Path,
    docker: bool,
) -> list[str]:
    args = ["uv", "run"]
    if profile.project_path is not None:
        project_value = "." if docker else str(profile.project_path.parent)
        args.extend(["--project", project_value])
    if profile.lockfile_path is not None:
        args.append("--locked")
    if kind == "code":
        args.extend(["python", source_root_rel])
        return args

    output_dir_value = output_dir.relative_to(output_dir.parents[2]).as_posix() if docker else str(output_dir)
    args.extend(
        [
            "python",
            "-m",
            "jupyter",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            source_root_rel,
            "--output",
            output_path.name,
            "--output-dir",
            output_dir_value,
        ]
    )
    return args


def _ensure_static_artifact(root: Path, artifact_dir: Path, report: ValidationReport) -> None:
    if (artifact_dir / "manifest.json").exists():
        return
    build_report = build_course(root)
    _merge_report(report, build_report)


def _execution_paths(
    artifact_dir: Path,
    target: ResolvedExecutionTarget,
) -> ExecutionPaths:
    safe = _safe_name(target.reference.id)
    output_dir = artifact_dir / "execution" / "outputs" / safe
    output_name = (
        f"{safe}.ipynb" if target.reference.kind == "notebook" else "stdout.txt"
    )
    cache_key = target.cache_entry.get("cache_key") if target.cache_entry else None
    cache_result_path = (
        artifact_dir / "cache" / "results" / f"{cache_key}.json"
        if isinstance(cache_key, str)
        else None
    )
    return ExecutionPaths(
        output_dir=output_dir,
        output_path=output_dir / output_name,
        log_path=artifact_dir / "logs" / f"{safe}.log",
        stdout_path=artifact_dir / "logs" / f"{safe}.stdout.log",
        stderr_path=artifact_dir / "logs" / f"{safe}.stderr.log",
        cache_result_path=cache_result_path,
    )


def _prepare_output_dirs(paths: ExecutionPaths, report: ValidationReport) -> None:
    for directory in (
        paths.output_dir,
        paths.log_path.parent,
        paths.cache_result_path.parent if paths.cache_result_path else None,
    ):
        if directory is None:
            continue
        directory.mkdir(parents=True, exist_ok=True)
        report.wrote_output(directory)


def _write_execution_output(
    target: ResolvedExecutionTarget,
    paths: ExecutionPaths,
    completed: subprocess.CompletedProcess[str],
    report: ValidationReport,
) -> Path:
    if target.reference.kind == "notebook":
        if paths.output_path.exists():
            report.wrote_output(paths.output_path)
        return paths.output_path
    _write_text(paths.output_path, completed.stdout, report)
    return paths.output_path


def _result_record(
    *,
    root: Path,
    artifact_dir: Path,
    target: ResolvedExecutionTarget,
    profile: RuntimeProfile,
    paths: ExecutionPaths,
    command: list[str],
    status: str,
    exit_code: int,
    started_at: str,
    ended_at: str,
    output_path: Path | None,
) -> dict[str, Any]:
    source_path = target.reference.source_path.relative_to(root).as_posix()
    record: dict[str, Any] = {
        "id": _result_id(target.reference.id, started_at),
        "target_id": target.reference.id,
        "reference_id": target.reference.id,
        "source_path": source_path,
        "kind": target.reference.kind,
        "policy": target.policy,
        "profile": profile.name,
        "status": status,
        "exit_code": exit_code,
        "started_at": started_at,
        "ended_at": ended_at,
        "command": command,
        "log_path": paths.log_path.relative_to(artifact_dir).as_posix(),
        "stdout_path": paths.stdout_path.relative_to(artifact_dir).as_posix(),
        "stderr_path": paths.stderr_path.relative_to(artifact_dir).as_posix(),
    }
    if target.runtime_target is not None:
        record["runtime_target_id"] = target.runtime_target.id
    if output_path is not None:
        record["output_path"] = output_path.relative_to(artifact_dir).as_posix()
    if target.cache_entry is not None:
        cache_key = target.cache_entry.get("cache_key")
        if isinstance(cache_key, str):
            record["cache_key"] = cache_key
        if paths.cache_result_path is not None:
            record["cache_result_path"] = paths.cache_result_path.relative_to(
                artifact_dir
            ).as_posix()
    return record


def _write_execution_result_index(
    course_id: str,
    artifact_dir: Path,
    result: dict[str, Any],
    report: ValidationReport,
) -> None:
    path = artifact_dir / EXECUTION_RESULTS_PATH
    existing = _load_json(path)
    if not isinstance(existing, dict):
        existing = {"course_id": course_id, "results": []}
    results = existing.get("results")
    if not isinstance(results, list):
        results = []
    target_id = result.get("target_id")
    filtered = [
        item
        for item in results
        if not (isinstance(item, dict) and item.get("target_id") == target_id)
    ]
    filtered.append(result)
    data = {"course_id": course_id, "results": filtered}
    _write_json(path, data, report)
    _declare_execution_results(artifact_dir, report)


def _declare_execution_results(artifact_dir: Path, report: ValidationReport) -> None:
    manifest_path = artifact_dir / "manifest.json"
    manifest = _load_json(manifest_path)
    if not isinstance(manifest, dict):
        return
    data = manifest.get("data")
    if not isinstance(data, dict):
        data = {}
        manifest["data"] = data
    if data.get("execution_results") == EXECUTION_RESULTS_PATH.as_posix():
        return
    data["execution_results"] = EXECUTION_RESULTS_PATH.as_posix()
    _write_json(manifest_path, manifest, report)


def _write_text(path: Path, text: str, report: ValidationReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    report.wrote_output(path)


def _write_json(path: Path, data: dict[str, Any], report: ValidationReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report.wrote_output(path)


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _combined_log(
    command: list[str],
    started_at: str,
    ended_at: str,
    completed: subprocess.CompletedProcess[str],
) -> str:
    return "\n".join(
        [
            f"command: {shlex.join(command)}",
            f"started_at: {started_at}",
            f"ended_at: {ended_at}",
            f"exit_code: {completed.returncode}",
            "",
            "stdout:",
            completed.stdout,
            "",
            "stderr:",
            completed.stderr,
            "",
        ]
    )


def _looks_like_missing_jupyter(completed: subprocess.CompletedProcess[str]) -> bool:
    text = f"{completed.stdout}\n{completed.stderr}".lower()
    return "no module named jupyter" in text or "jupyter" in text and "not found" in text


def _normalize_selector(value: str) -> str:
    cleaned = value.strip().replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "target"


def _result_id(target_id: str, started_at: str) -> str:
    digest = hashlib.sha256(f"{target_id}\0{started_at}".encode("utf-8")).hexdigest()[:16]
    return f"execution:{digest}"


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _merge_report(target: ValidationReport, source: ValidationReport) -> None:
    for path in source.files_read:
        target.read_file(path)
    for path in source.outputs_written:
        target.wrote_output(path)
    target.diagnostics.extend(source.diagnostics)
