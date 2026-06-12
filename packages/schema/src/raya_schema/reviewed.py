from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from raya_schema.content import ContentModel
from raya_schema.diagnostics import ValidationReport
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
    RuntimeTarget,
    cache_index,
    reference_execution_metadata,
    runtime_profile_sha256,
)
from raya_schema.schema_loader import validator_for
from raya_schema.yaml_io import load_yaml_file


SOURCE_SCHEMA_VERSION = "0.1"
REVIEWED_MANIFEST_NAME = "reviewed.yaml"
REVIEWED_OUTPUTS_DATA_PATH = Path("data") / "reviewed-outputs.json"
REVIEWED_ARTIFACT_DIR = Path("reviewed")
REVIEWED_BROWSER_DIR = Path("_raya") / "reviewed"


@dataclass(frozen=True)
class ReviewedOutputFile:
    path: Path
    rel_path: str
    source_rel_path: str
    kind: str
    sha256: str

    def artifact_path(self, reviewed: ReviewedOutput) -> str:
        return (REVIEWED_ARTIFACT_DIR / _safe_name(reviewed.id) / self.rel_path).as_posix()

    def browser_path(self, reviewed: ReviewedOutput) -> str:
        return (REVIEWED_BROWSER_DIR / _safe_name(reviewed.id) / self.rel_path).as_posix()


@dataclass(frozen=True)
class ReviewedOutput:
    id: str
    target_id: str
    reference_id: str
    runtime_target_id: str | None
    source_path: Path
    source_rel_path: str
    source_root_rel_path: str
    kind: str
    policy: str
    profile: str | None
    status: str
    authority: str
    manifest_path: Path
    manifest_rel_path: str
    owner_dir: Path
    owner_rel_path: str
    reviewed_at: str | None
    source_sha256: str
    input_hashes: tuple[dict[str, str], ...]
    runtime_profile_sha256: str | None
    lockfile_sha256: str | None
    cache_key: str | None
    review_key: str
    files: tuple[ReviewedOutputFile, ...]

    def to_index_item(self) -> dict[str, Any]:
        item: dict[str, Any] = {
            "id": self.id,
            "target_id": self.target_id,
            "reference_id": self.reference_id,
            "source_path": self.source_root_rel_path,
            "source_support_path": self.manifest_rel_path,
            "kind": self.kind,
            "policy": self.policy,
            "status": self.status,
            "authority": self.authority,
            "source_sha256": self.source_sha256,
            "input_hashes": list(self.input_hashes),
            "review_key": self.review_key,
            "files": [
                {
                    "path": reviewed_file.rel_path,
                    "kind": reviewed_file.kind,
                    "sha256": reviewed_file.sha256,
                    "source_path": reviewed_file.source_rel_path,
                    "artifact_path": reviewed_file.artifact_path(self),
                    "browser_path": reviewed_file.browser_path(self),
                }
                for reviewed_file in self.files
            ],
        }
        if self.runtime_target_id is not None:
            item["runtime_target_id"] = self.runtime_target_id
        if self.profile is not None:
            item["profile"] = self.profile
        if self.runtime_profile_sha256 is not None:
            item["runtime_profile_sha256"] = self.runtime_profile_sha256
        if self.lockfile_sha256 is not None:
            item["lockfile_sha256"] = self.lockfile_sha256
        if self.cache_key is not None:
            item["cache_key"] = self.cache_key
        if self.reviewed_at is not None:
            item["reviewed_at"] = self.reviewed_at
        return item


def collect_source_references(
    *,
    course_id: str,
    content_model: ContentModel,
    course_root: Path,
    source_dir: Path,
    runtime_model: RuntimeModel,
    report: ValidationReport,
    artifact_root: Path = Path("files"),
    browser_root: Path = Path("_raya") / "files",
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
                    artifact_path=(artifact_root / resolved.output_path).as_posix(),
                    browser_path=(browser_root / resolved.output_path).as_posix(),
                    sha256=_file_sha256(resolved.target_path),
                    execution_policy=execution["policy"],
                    runtime_profile=execution.get("profile"),
                )
            )
            report.read_file(resolved.target_path)
    return references


def cache_entries_by_reference(
    course_id: str,
    references: list[SourceReference],
    runtime_model: RuntimeModel,
    *,
    schema_version: str = SOURCE_SCHEMA_VERSION,
) -> dict[str, dict[str, Any]]:
    data = cache_index(course_id, references, runtime_model, schema_version=schema_version)
    entries: dict[str, dict[str, Any]] = {}
    for item in data.get("entries", []):
        if isinstance(item, dict):
            reference_id = item.get("reference_id") or item.get("target_id")
            if isinstance(reference_id, str):
                entries[reference_id] = item
    return entries


def reviewed_outputs_index(
    course_id: str,
    outputs: list[ReviewedOutput],
) -> dict[str, Any]:
    return {
        "course_id": course_id,
        "authority": "reviewed-course-support",
        "outputs": [output.to_index_item() for output in outputs],
    }


def reviewed_outputs_by_reference(
    outputs: list[ReviewedOutput],
) -> dict[str, ReviewedOutput]:
    return {output.reference_id: output for output in outputs if output.status == "current"}


def discover_reviewed_outputs(
    *,
    course_id: str,
    course_root: Path,
    source_dir: Path,
    runtime_model: RuntimeModel,
    references: list[SourceReference],
    report: ValidationReport,
    require_frozen: bool = True,
) -> list[ReviewedOutput]:
    by_id = {reference.id: reference for reference in references}
    by_source = {
        reference.source_path.resolve(): reference
        for reference in references
    }
    by_root_rel: dict[str, SourceReference] = {}
    by_runtime_id: dict[str, SourceReference] = {}
    for reference in references:
        by_root_rel[reference.source_path.relative_to(course_root).as_posix()] = reference
        runtime_target = runtime_model.target_for_source(reference.source_path)
        if runtime_target is not None:
            by_runtime_id[runtime_target.id] = reference

    outputs: list[ReviewedOutput] = []
    seen_references: set[str] = set()
    for manifest_path in sorted(source_dir.rglob(REVIEWED_MANIFEST_NAME)):
        owner_dir = _reviewed_owner_dir(source_dir, manifest_path, report)
        if owner_dir is None:
            continue
        data = _load_reviewed_manifest(manifest_path, report)
        if data is None:
            continue
        reference = _manifest_reference(
            data=data,
            manifest_path=manifest_path,
            course_root=course_root,
            by_id=by_id,
            by_source=by_source,
            by_root_rel=by_root_rel,
            by_runtime_id=by_runtime_id,
            report=report,
        )
        if reference is None:
            continue
        if reference.id in seen_references:
            report.add_error(
                "Duplicate reviewed output for target",
                path=manifest_path,
                field=reference.id,
                next_action="Keep one current reviewed output manifest per referenced target",
            )
            continue
        seen_references.add(reference.id)
        allowed_owners = _allowed_review_owner_dirs(reference, source_dir)
        if owner_dir.resolve() not in {path.resolve() for path in allowed_owners}:
            report.add_error(
                "Reviewed output is outside the target ownership boundary",
                path=manifest_path,
                field="source_support_path",
                next_action="Move the manifest under the target quantum's own or ancestor _reviewed/ directory",
            )
            continue
        reviewed = _parse_reviewed_output(
            data=data,
            manifest_path=manifest_path,
            owner_dir=owner_dir,
            course_id=course_id,
            course_root=course_root,
            source_dir=source_dir,
            reference=reference,
            runtime_model=runtime_model,
            report=report,
        )
        if reviewed is not None:
            outputs.append(reviewed)

    if require_frozen:
        current_by_reference = reviewed_outputs_by_reference(outputs)
        for reference in references:
            if reference.execution_policy != "frozen":
                continue
            if reference.id not in current_by_reference:
                report.add_error(
                    "Frozen execution target is missing current reviewed output",
                    path=reference.source_path,
                    field="policy",
                    next_action=(
                        "Run the target under a runnable policy, use raya outputs freeze, "
                        "review the _reviewed/ files, then keep policy: frozen"
                    ),
                )
    return outputs


def validate_reviewed_source_manifest(manifest_path: str | Path) -> ValidationReport:
    path = Path(manifest_path).resolve()
    report = ValidationReport(context="reviewed-output")
    if not path.exists():
        report.add_error(
            "Reviewed output manifest does not exist",
            path=path,
            next_action="Create reviewed.yaml under _reviewed/execution/<target>/",
        )
        return report
    report.read_file(path)
    try:
        data = load_yaml_file(path)
    except Exception as exc:
        report.add_error(
            f"Could not read reviewed output manifest: {exc}",
            path=path,
            next_action="Fix reviewed.yaml syntax",
        )
        return report
    if not isinstance(data, dict):
        report.add_error(
            "Reviewed output manifest must be a mapping",
            path=path,
            next_action="Use key/value metadata in reviewed.yaml",
        )
        return report
    validator = validator_for("reviewed-output-source.schema.json")
    for error in sorted(
        validator.iter_errors(data),
        key=lambda item: (".".join(str(part) for part in item.absolute_path), item.message),
    ):
        report.add_error(
            error.message,
            path=path,
            field=".".join(str(part) for part in error.absolute_path) or None,
            next_action="Update reviewed.yaml to match the reviewed output source contract",
        )
    if report.ok:
        report.add_info("Reviewed output source manifest validation passed", path=path)
    return report


def freshness_for_reference(
    *,
    course_root: Path,
    reference: SourceReference,
    runtime_model: RuntimeModel,
    cache_entry: dict[str, Any] | None,
) -> dict[str, Any]:
    runtime_target = runtime_model.target_for_source(reference.source_path)
    profile_name = runtime_target.profile if runtime_target is not None else reference.runtime_profile
    profile = runtime_model.profile_for(profile_name)
    input_hashes: list[dict[str, str]] = []
    if runtime_target is not None:
        input_hashes = [
            {"path": rel_path, "sha256": _file_sha256(path)}
            for path, rel_path in zip(runtime_target.input_paths, runtime_target.input_rel_paths)
        ]
    freshness: dict[str, Any] = {
        "target_id": reference.id,
        "reference_id": reference.id,
        "source_path": reference.source_path.relative_to(course_root).as_posix(),
        "kind": reference.kind,
        "source_sha256": reference.sha256,
        "input_hashes": input_hashes,
        "schema_version": SOURCE_SCHEMA_VERSION,
    }
    if runtime_target is not None:
        freshness["runtime_target_id"] = runtime_target.id
        freshness["policy"] = runtime_target.policy
    else:
        freshness["policy"] = reference.execution_policy
    if profile_name is not None:
        freshness["profile"] = profile_name
    if profile is not None:
        freshness["runtime_profile_sha256"] = runtime_profile_sha256(profile)
        if profile.lockfile_path is not None and profile.lockfile_path.exists():
            freshness["lockfile_sha256"] = _file_sha256(profile.lockfile_path)
    if cache_entry is not None:
        value = cache_entry.get("cache_key")
        if isinstance(value, str):
            freshness["cache_key"] = value
    freshness["review_key"] = review_key_for_freshness(freshness)
    return freshness


def review_key_for_freshness(freshness: dict[str, Any]) -> str:
    stable = {
        key: value
        for key, value in freshness.items()
        if key not in {"cache_key", "policy", "review_key"}
    }
    encoded = json.dumps(stable, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_reviewed_manifest(
    manifest_path: Path,
    report: ValidationReport,
) -> dict[str, Any] | None:
    manifest_report = validate_reviewed_source_manifest(manifest_path)
    _merge_report(report, manifest_report)
    if not manifest_report.ok:
        return None
    try:
        data = load_yaml_file(manifest_path)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _manifest_reference(
    *,
    data: dict[str, Any],
    manifest_path: Path,
    course_root: Path,
    by_id: dict[str, SourceReference],
    by_source: dict[Path, SourceReference],
    by_root_rel: dict[str, SourceReference],
    by_runtime_id: dict[str, SourceReference],
    report: ValidationReport,
) -> SourceReference | None:
    candidates: list[SourceReference] = []
    for key in ("reference_id", "target_id"):
        value = data.get(key)
        if isinstance(value, str) and value in by_id:
            candidates.append(by_id[value])
    runtime_target_id = data.get("runtime_target_id")
    if isinstance(runtime_target_id, str) and runtime_target_id in by_runtime_id:
        candidates.append(by_runtime_id[runtime_target_id])
    source_value = data.get("source_path")
    if isinstance(source_value, str):
        raw = Path(source_value)
        if raw.is_absolute() or ".." in raw.parts:
            report.add_error(
                "Reviewed output source path must be relative and stay inside course root",
                path=manifest_path,
                field="source_path",
                next_action="Use a course-root-relative referenced source path such as course/1_topic/scripts/task.py",
            )
            return None
        resolved = (course_root / raw).resolve()
        if resolved in by_source:
            candidates.append(by_source[resolved])
        if source_value in by_root_rel:
            candidates.append(by_root_rel[source_value])
    unique = {candidate.id: candidate for candidate in candidates}
    if len(unique) == 1:
        return next(iter(unique.values()))
    if len(unique) > 1:
        report.add_error(
            "Reviewed output manifest identifies multiple targets",
            path=manifest_path,
            next_action="Make target_id, runtime_target_id, and source_path point to the same target",
        )
        return None
    report.add_error(
        "Reviewed output target was not found",
        path=manifest_path,
        field="target_id",
        next_action="Use a validated reference ID, runtime target ID, or current source path",
    )
    return None


def _parse_reviewed_output(
    *,
    data: dict[str, Any],
    manifest_path: Path,
    owner_dir: Path,
    course_id: str,
    course_root: Path,
    source_dir: Path,
    reference: SourceReference,
    runtime_model: RuntimeModel,
    report: ValidationReport,
) -> ReviewedOutput | None:
    manifest_dir = manifest_path.parent
    runtime_target = runtime_model.target_for_source(reference.source_path)
    cache_entries = cache_entries_by_reference(course_id, [reference], runtime_model)
    freshness = freshness_for_reference(
        course_root=course_root,
        reference=reference,
        runtime_model=runtime_model,
        cache_entry=cache_entries.get(reference.id),
    )

    for field_name, expected in (
        ("source_path", freshness["source_path"]),
        ("kind", reference.kind),
        ("source_sha256", freshness["source_sha256"]),
        ("review_key", freshness["review_key"]),
    ):
        value = data.get(field_name)
        if value != expected:
            report.add_error(
                "Stale reviewed output metadata",
                path=manifest_path,
                field=field_name,
                next_action=f"Regenerate reviewed output for {reference.id}; expected {expected}",
            )
            return None
    if data.get("target_id") not in {None, reference.id}:
        report.add_error(
            "Stale reviewed output metadata",
            path=manifest_path,
            field="target_id",
            next_action=f"Update target_id to {reference.id} or freeze the current target",
        )
        return None
    if runtime_target is not None and data.get("runtime_target_id") not in {None, runtime_target.id}:
        report.add_error(
            "Stale reviewed output metadata",
            path=manifest_path,
            field="runtime_target_id",
            next_action=f"Update runtime_target_id to {runtime_target.id} or freeze the current target",
        )
        return None
    for optional_field in ("runtime_profile_sha256", "lockfile_sha256"):
        expected = freshness.get(optional_field)
        value = data.get(optional_field)
        if expected is None:
            if value is not None:
                report.add_error(
                    "Stale reviewed output metadata",
                    path=manifest_path,
                    field=optional_field,
                    next_action=f"Remove {optional_field} or freeze the current target",
                )
                return None
            continue
        if value != expected:
            report.add_error(
                "Stale reviewed output metadata",
                path=manifest_path,
                field=optional_field,
                next_action=f"Regenerate reviewed output for {reference.id}; expected {expected}",
            )
            return None
    if data.get("input_hashes") != freshness["input_hashes"]:
        report.add_error(
            "Stale reviewed output input hashes",
            path=manifest_path,
            field="input_hashes",
            next_action=f"Rerun and freeze {reference.id} after updating declared inputs",
        )
        return None

    output_files = _reviewed_files(
        data=data,
        manifest_path=manifest_path,
        manifest_dir=manifest_dir,
        course_root=course_root,
        report=report,
    )
    if output_files is None:
        return None

    source_root_rel = reference.source_path.relative_to(course_root).as_posix()
    manifest_rel = manifest_path.relative_to(course_root).as_posix()
    try:
        owner_rel = owner_dir.relative_to(source_dir).as_posix()
    except ValueError:
        owner_rel = ""
    reviewed_id = data.get("id")
    if not isinstance(reviewed_id, str) or not reviewed_id:
        reviewed_id = data.get("runtime_target_id") or reference.id
    reviewed_at = data.get("reviewed_at") if isinstance(data.get("reviewed_at"), str) else None
    policy = runtime_target.policy if runtime_target is not None else reference.execution_policy
    return ReviewedOutput(
        id=reviewed_id,
        target_id=reference.id,
        reference_id=reference.id,
        runtime_target_id=runtime_target.id if runtime_target is not None else None,
        source_path=reference.source_path,
        source_rel_path=reference.source_rel_path,
        source_root_rel_path=source_root_rel,
        kind=reference.kind,
        policy=policy,
        profile=freshness.get("profile") if isinstance(freshness.get("profile"), str) else None,
        status="current",
        authority="reviewed-course-support",
        manifest_path=manifest_path,
        manifest_rel_path=manifest_rel,
        owner_dir=owner_dir,
        owner_rel_path=owner_rel,
        reviewed_at=reviewed_at,
        source_sha256=freshness["source_sha256"],
        input_hashes=tuple(freshness["input_hashes"]),
        runtime_profile_sha256=(
            freshness.get("runtime_profile_sha256")
            if isinstance(freshness.get("runtime_profile_sha256"), str)
            else None
        ),
        lockfile_sha256=(
            freshness.get("lockfile_sha256")
            if isinstance(freshness.get("lockfile_sha256"), str)
            else None
        ),
        cache_key=data.get("cache_key") if isinstance(data.get("cache_key"), str) else None,
        review_key=freshness["review_key"],
        files=tuple(output_files),
    )


def _reviewed_files(
    *,
    data: dict[str, Any],
    manifest_path: Path,
    manifest_dir: Path,
    course_root: Path,
    report: ValidationReport,
) -> list[ReviewedOutputFile] | None:
    raw_outputs = data.get("outputs")
    if not isinstance(raw_outputs, list) or not raw_outputs:
        report.add_error(
            "Reviewed output manifest requires output files",
            path=manifest_path,
            field="outputs",
            next_action="Declare at least one reviewed output file",
        )
        return None
    files: list[ReviewedOutputFile] = []
    ok = True
    for index, item in enumerate(raw_outputs):
        field = f"outputs.{index}"
        if not isinstance(item, dict):
            report.add_error(
                "Reviewed output file entry must be a mapping",
                path=manifest_path,
                field=field,
                next_action="Use path, kind, and sha256 fields",
            )
            ok = False
            continue
        path_value = item.get("path")
        kind = item.get("kind")
        sha256 = item.get("sha256")
        if not isinstance(path_value, str) or not path_value:
            report.add_error(
                "Reviewed output file path must be a non-empty string",
                path=manifest_path,
                field=f"{field}.path",
                next_action="Use a manifest-relative output file path",
            )
            ok = False
            continue
        if not isinstance(kind, str) or not kind:
            kind = "output"
        if not isinstance(sha256, str) or not re.fullmatch(r"[a-f0-9]{64}", sha256):
            report.add_error(
                "Reviewed output file sha256 is required",
                path=manifest_path,
                field=f"{field}.sha256",
                next_action="Record the current SHA-256 for the reviewed file",
            )
            ok = False
            continue
        output_path = _safe_reviewed_file_path(
            manifest_dir,
            path_value,
            manifest_path,
            f"{field}.path",
            report,
        )
        if output_path is None:
            ok = False
            continue
        if not output_path.is_file():
            report.add_error(
                "Reviewed output file is missing",
                path=output_path,
                field=f"{field}.path",
                next_action="Restore the reviewed output file or rerun raya outputs freeze",
            )
            ok = False
            continue
        report.read_file(output_path)
        actual = _file_sha256(output_path)
        if actual != sha256:
            report.add_error(
                "Stale reviewed output file hash",
                path=output_path,
                field=f"{field}.sha256",
                next_action=f"Rerun and freeze the target; expected {actual}",
            )
            ok = False
            continue
        files.append(
            ReviewedOutputFile(
                path=output_path,
                rel_path=Path(path_value).as_posix(),
                source_rel_path=output_path.relative_to(course_root).as_posix(),
                kind=kind,
                sha256=sha256,
            )
        )
    return files if ok else None


def _safe_reviewed_file_path(
    manifest_dir: Path,
    value: str,
    manifest_path: Path,
    field: str,
    report: ValidationReport,
) -> Path | None:
    raw = Path(value)
    if raw.is_absolute() or ".." in raw.parts:
        report.add_error(
            "Reviewed output file path must stay under its manifest directory",
            path=manifest_path,
            field=field,
            next_action="Use a relative file path without .. segments",
        )
        return None
    resolved = (manifest_dir / raw).resolve()
    try:
        resolved.relative_to(manifest_dir.resolve())
    except ValueError:
        report.add_error(
            "Reviewed output file path escapes its manifest directory",
            path=manifest_path,
            field=field,
            next_action="Keep reviewed output files beside reviewed.yaml",
        )
        return None
    return resolved


def _reviewed_owner_dir(
    source_dir: Path,
    manifest_path: Path,
    report: ValidationReport,
) -> Path | None:
    try:
        rel = manifest_path.relative_to(source_dir)
    except ValueError:
        return None
    parts = rel.parts
    reviewed_indexes = [index for index, part in enumerate(parts) if part == "_reviewed"]
    if len(reviewed_indexes) != 1:
        report.add_error(
            "Reviewed output manifest must live under one _reviewed directory",
            path=manifest_path,
            next_action="Use <owner>/_reviewed/execution/<target>/reviewed.yaml",
        )
        return None
    index = reviewed_indexes[0]
    if len(parts) != index + 4 or parts[index + 1] != "execution":
        report.add_error(
            "Reviewed output manifest has unsupported path shape",
            path=manifest_path,
            next_action="Use <owner>/_reviewed/execution/<target>/reviewed.yaml",
        )
        return None
    owner_parts = parts[:index]
    return (source_dir / Path(*owner_parts)).resolve() if owner_parts else source_dir.resolve()


def _allowed_review_owner_dirs(reference: SourceReference, source_dir: Path) -> list[Path]:
    page_path = (source_dir / reference.page_source_path).resolve()
    roots: list[Path] = []
    current = page_path.parent
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


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "target"


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _merge_report(target: ValidationReport, source: ValidationReport) -> None:
    for path in source.files_read:
        target.read_file(path)
    for path in source.outputs_written:
        target.wrote_output(path)
    target.diagnostics.extend(source.diagnostics)
