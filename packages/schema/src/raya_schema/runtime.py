from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from raya_schema.diagnostics import ValidationReport
from raya_schema.references import reference_kind_for_path
from raya_schema.yaml_io import load_yaml_file


RUNTIME_PROFILE_PATH = Path("runtime") / "profiles.yaml"
EXECUTION_POLICIES = {"never", "manual", "cache", "always", "frozen"}
CACHE_POLICIES = {"cache", "always", "frozen"}


@dataclass(frozen=True)
class RuntimeProfile:
    name: str
    manager: str
    python: str | None
    project_path: Path | None
    project_rel_path: str | None
    lockfile_path: Path | None
    lockfile_rel_path: str | None
    docker_compose_service: str | None
    source: str
    inferred: bool = False

    def to_index_item(self) -> dict[str, object]:
        item: dict[str, object] = {
            "name": self.name,
            "manager": self.manager,
            "source": self.source,
            "inferred": self.inferred,
        }
        if self.python is not None:
            item["python"] = self.python
        if self.project_rel_path is not None:
            item["project"] = self.project_rel_path
        if self.lockfile_rel_path is not None:
            item["lockfile"] = self.lockfile_rel_path
        if self.docker_compose_service is not None:
            item["docker"] = {"compose_service": self.docker_compose_service}
        return item


@dataclass(frozen=True)
class RuntimeTarget:
    id: str
    source_path: Path
    source_rel_path: str
    kind: str
    policy: str
    profile: str | None
    input_paths: tuple[Path, ...] = ()
    input_rel_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class RuntimeModel:
    profiles: dict[str, RuntimeProfile]
    default_policy: str = "never"
    default_profile: str | None = None
    targets: tuple[RuntimeTarget, ...] = ()
    source_path: Path | None = None

    @property
    def has_runtime_metadata(self) -> bool:
        return bool(self.profiles or self.targets or self.source_path is not None)

    def profile_for(self, name: str | None) -> RuntimeProfile | None:
        if name is None:
            return None
        return self.profiles.get(name)

    def target_for_source(self, source_path: Path) -> RuntimeTarget | None:
        resolved = source_path.resolve()
        for target in self.targets:
            if target.source_path.resolve() == resolved:
                return target
        return None


def load_runtime_model(course_root: Path, report: ValidationReport) -> RuntimeModel:
    root = course_root.resolve()
    profile_path = root / RUNTIME_PROFILE_PATH
    if profile_path.exists():
        return _load_declared_runtime_model(root, profile_path, report)
    return _inferred_runtime_model(root, report)


def runtime_index(course_id: str, model: RuntimeModel) -> dict[str, Any]:
    data: dict[str, Any] = {
        "course_id": course_id,
        "profiles": [profile.to_index_item() for profile in model.profiles.values()],
        "defaults": {"policy": model.default_policy},
    }
    if model.default_profile is not None:
        data["defaults"]["profile"] = model.default_profile
    if model.source_path is not None:
        data["source_path"] = RUNTIME_PROFILE_PATH.as_posix()
    return data


def reference_execution_metadata(
    *,
    reference_source_path: Path,
    model: RuntimeModel,
) -> dict[str, str]:
    target = model.target_for_source(reference_source_path)
    policy = target.policy if target is not None else model.default_policy
    profile = target.profile if target is not None else model.default_profile
    metadata = {
        "status": "not-executed",
        "policy": policy,
    }
    if profile is not None:
        metadata["profile"] = profile
    return metadata


def execution_index(
    course_id: str,
    references: list[Any],
    model: RuntimeModel,
) -> dict[str, Any]:
    targets = []
    for reference in references:
        runtime_target = model.target_for_source(reference.source_path)
        execution = reference_execution_metadata(
            reference_source_path=reference.source_path,
            model=model,
        )
        item: dict[str, Any] = {
            "id": reference.id,
            "reference_id": reference.id,
            "source_path": reference.source_rel_path,
            "kind": reference.kind,
            "policy": execution["policy"],
            "status": "not-executed",
        }
        if "profile" in execution:
            item["profile"] = execution["profile"]
        if runtime_target is not None and runtime_target.input_rel_paths:
            item["inputs"] = list(runtime_target.input_rel_paths)
        targets.append(item)
    return {
        "course_id": course_id,
        "targets": targets,
    }


def cache_index(
    course_id: str,
    references: list[Any],
    model: RuntimeModel,
    *,
    schema_version: str,
) -> dict[str, Any]:
    entries = []
    for reference in references:
        runtime_target = model.target_for_source(reference.source_path)
        if runtime_target is None or runtime_target.policy not in CACHE_POLICIES:
            continue
        profile = model.profile_for(runtime_target.profile)
        input_hashes = [
            {
                "path": rel_path,
                "sha256": _file_sha256(path),
            }
            for path, rel_path in zip(
                runtime_target.input_paths,
                runtime_target.input_rel_paths,
            )
        ]
        entry: dict[str, Any] = {
            "target_id": reference.id,
            "reference_id": reference.id,
            "source_path": reference.source_rel_path,
            "policy": runtime_target.policy,
            "source_sha256": reference.sha256,
            "input_hashes": input_hashes,
            "schema_version": schema_version,
        }
        if runtime_target.profile is not None:
            entry["runtime_profile"] = runtime_target.profile
        if profile is not None:
            entry["runtime_profile_sha256"] = runtime_profile_sha256(profile)
            if profile.lockfile_path is not None and profile.lockfile_path.exists():
                entry["lockfile_sha256"] = _file_sha256(profile.lockfile_path)
        entry["cache_key"] = cache_key_for_entry(entry)
        entries.append(entry)
    return {
        "course_id": course_id,
        "entries": entries,
    }


def runtime_profile_sha256(profile: RuntimeProfile) -> str:
    encoded = json.dumps(profile.to_index_item(), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def cache_key_for_entry(entry: dict[str, Any]) -> str:
    stable = {key: value for key, value in entry.items() if key != "cache_key"}
    encoded = json.dumps(stable, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_declared_runtime_model(
    root: Path,
    profile_path: Path,
    report: ValidationReport,
) -> RuntimeModel:
    report.read_file(profile_path)
    try:
        data = load_yaml_file(profile_path)
    except Exception as exc:
        report.add_error(
            f"Could not read runtime profiles: {exc}",
            path=profile_path,
            next_action="Fix runtime/profiles.yaml syntax",
        )
        return RuntimeModel(profiles={}, source_path=profile_path)
    if not isinstance(data, dict):
        report.add_error(
            "Runtime profiles document must be a mapping",
            path=profile_path,
            next_action="Use profiles: and execution: mappings",
        )
        return RuntimeModel(profiles={}, source_path=profile_path)

    profiles = _parse_profiles(root, profile_path, data.get("profiles"), report)
    default_policy = "never"
    default_profile: str | None = "default" if "default" in profiles else None
    execution = data.get("execution")
    if execution is not None and not isinstance(execution, dict):
        report.add_error(
            "Runtime execution metadata must be a mapping",
            path=profile_path,
            field="execution",
            next_action="Use execution.defaults and execution.references mappings",
        )
        execution = {}
    if isinstance(execution, dict):
        defaults = execution.get("defaults", {})
        if defaults is not None and not isinstance(defaults, dict):
            report.add_error(
                "Runtime execution defaults must be a mapping",
                path=profile_path,
                field="execution.defaults",
                next_action="Use policy and profile fields under execution.defaults",
            )
            defaults = {}
        if isinstance(defaults, dict):
            default_policy = _policy_value(
                defaults.get("policy", default_policy),
                path=profile_path,
                field="execution.defaults.policy",
                report=report,
                allow_always=False,
            )
            default_profile = _profile_value(
                defaults.get("profile", default_profile),
                profiles,
                path=profile_path,
                field="execution.defaults.profile",
                report=report,
            )
        targets = _parse_targets(
            root,
            profile_path,
            execution.get("references", []) if isinstance(execution, dict) else [],
            profiles,
            default_policy,
            default_profile,
            report,
        )
    else:
        targets = ()

    return RuntimeModel(
        profiles=profiles,
        default_policy=default_policy,
        default_profile=default_profile,
        targets=targets,
        source_path=profile_path,
    )


def _parse_profiles(
    root: Path,
    profile_path: Path,
    raw_profiles: Any,
    report: ValidationReport,
) -> dict[str, RuntimeProfile]:
    if not isinstance(raw_profiles, dict) or not raw_profiles:
        report.add_error(
            "Runtime profiles must declare at least one profile",
            path=profile_path,
            field="profiles",
            next_action="Add profiles.default with manager: uv",
        )
        return {}
    profiles: dict[str, RuntimeProfile] = {}
    for name, raw_profile in raw_profiles.items():
        field = f"profiles.{name}"
        if not isinstance(name, str) or not name:
            report.add_error(
                "Runtime profile names must be non-empty strings",
                path=profile_path,
                field="profiles",
                next_action="Use stable profile keys such as default or docker",
            )
            continue
        if not isinstance(raw_profile, dict):
            report.add_error(
                "Runtime profile must be a mapping",
                path=profile_path,
                field=field,
                next_action="Use fields such as manager, python, project, and lockfile",
            )
            continue
        manager = str(raw_profile.get("manager", "uv"))
        if manager != "uv":
            report.add_error(
                "Unsupported runtime manager",
                path=profile_path,
                field=f"{field}.manager",
                next_action="Use manager: uv until a future adapter contract is accepted",
            )
            continue
        python = raw_profile.get("python")
        if python is not None and not isinstance(python, str):
            report.add_error(
                "Runtime profile python field must be a string",
                path=profile_path,
                field=f"{field}.python",
                next_action='Use a value such as "3.10" or ">=3.10"',
            )
            python = None
        project_path, project_rel = _declared_file(
            root,
            profile_path,
            raw_profile.get("project", "pyproject.toml"),
            report,
            field=f"{field}.project",
            missing_message="Missing runtime project file",
        )
        lockfile_path, lockfile_rel = _declared_file(
            root,
            profile_path,
            raw_profile.get("lockfile", "uv.lock"),
            report,
            field=f"{field}.lockfile",
            missing_message="Missing runtime lockfile",
        )
        docker_service = _docker_service(raw_profile.get("docker"), profile_path, field, report)
        profiles[name] = RuntimeProfile(
            name=name,
            manager=manager,
            python=python,
            project_path=project_path,
            project_rel_path=project_rel,
            lockfile_path=lockfile_path,
            lockfile_rel_path=lockfile_rel,
            docker_compose_service=docker_service,
            source=RUNTIME_PROFILE_PATH.as_posix(),
        )
    return profiles


def _parse_targets(
    root: Path,
    profile_path: Path,
    raw_targets: Any,
    profiles: dict[str, RuntimeProfile],
    default_policy: str,
    default_profile: str | None,
    report: ValidationReport,
) -> tuple[RuntimeTarget, ...]:
    if raw_targets in (None, []):
        return ()
    if not isinstance(raw_targets, list):
        report.add_error(
            "Runtime execution references must be a list",
            path=profile_path,
            field="execution.references",
            next_action="Use a list of reference target mappings",
        )
        return ()
    targets: list[RuntimeTarget] = []
    for index, raw_target in enumerate(raw_targets):
        field = f"execution.references.{index}"
        if not isinstance(raw_target, dict):
            report.add_error(
                "Runtime execution reference must be a mapping",
                path=profile_path,
                field=field,
                next_action="Use source, policy, profile, and inputs fields",
            )
            continue
        source_value = raw_target.get("source")
        if not isinstance(source_value, str) or not source_value:
            report.add_error(
                "Runtime execution reference requires a source path",
                path=profile_path,
                field=f"{field}.source",
                next_action="Point source to a referenced .py or .ipynb file",
            )
            continue
        source_path, source_rel = _declared_file(
            root,
            profile_path,
            source_value,
            report,
            field=f"{field}.source",
            missing_message="Missing runtime target source file",
        )
        if source_path is None or source_rel is None:
            continue
        kind = reference_kind_for_path(source_path)
        if kind not in {"code", "notebook"}:
            report.add_error(
                "Runtime execution reference must point to code or notebook source",
                path=profile_path,
                field=f"{field}.source",
                next_action="Use a .py or .ipynb source file already referenced by course content",
            )
            continue
        policy = _policy_value(
            raw_target.get("policy", default_policy),
            path=profile_path,
            field=f"{field}.policy",
            report=report,
            allow_always=True,
        )
        profile = _profile_value(
            raw_target.get("profile", default_profile),
            profiles,
            path=profile_path,
            field=f"{field}.profile",
            report=report,
        )
        input_paths, input_rel_paths = _input_paths(
            root,
            profile_path,
            raw_target.get("inputs", []),
            report,
            field=f"{field}.inputs",
        )
        target_id = raw_target.get("id")
        if not isinstance(target_id, str) or not target_id:
            target_id = _target_id(source_rel)
        targets.append(
            RuntimeTarget(
                id=target_id,
                source_path=source_path,
                source_rel_path=source_rel,
                kind=kind,
                policy=policy,
                profile=profile,
                input_paths=tuple(input_paths),
                input_rel_paths=tuple(input_rel_paths),
            )
        )
    return tuple(targets)


def _inferred_runtime_model(root: Path, report: ValidationReport) -> RuntimeModel:
    project = root / "pyproject.toml"
    lockfile = root / "uv.lock"
    if not project.exists() and not lockfile.exists():
        return RuntimeModel(profiles={})
    project_path = project if project.exists() else None
    lockfile_path = lockfile if lockfile.exists() else None
    if project_path is not None:
        report.read_file(project_path)
    if lockfile_path is not None:
        report.read_file(lockfile_path)
    profile = RuntimeProfile(
        name="default",
        manager="uv",
        python=None,
        project_path=project_path,
        project_rel_path="pyproject.toml" if project_path is not None else None,
        lockfile_path=lockfile_path,
        lockfile_rel_path="uv.lock" if lockfile_path is not None else None,
        docker_compose_service=None,
        source="inferred",
        inferred=True,
    )
    return RuntimeModel(
        profiles={"default": profile},
        default_policy="never",
        default_profile="default",
    )


def _policy_value(
    value: Any,
    *,
    path: Path,
    field: str,
    report: ValidationReport,
    allow_always: bool,
) -> str:
    policy = value if isinstance(value, str) else "never"
    if policy not in EXECUTION_POLICIES:
        report.add_error(
            "Unsupported execution policy",
            path=path,
            field=field,
            next_action="Use never, manual, cache, always, or frozen",
        )
        return "never"
    if policy == "always" and not allow_always:
        report.add_error(
            "Unsafe default execution policy",
            path=path,
            field=field,
            next_action="Declare policy: always only on an explicit execution reference",
        )
        return "never"
    return policy


def _profile_value(
    value: Any,
    profiles: dict[str, RuntimeProfile],
    *,
    path: Path,
    field: str,
    report: ValidationReport,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        report.add_error(
            "Runtime profile reference must be a non-empty string",
            path=path,
            field=field,
            next_action="Reference a profile declared under profiles",
        )
        return None
    if value not in profiles:
        report.add_error(
            "Unknown runtime profile",
            path=path,
            field=field,
            next_action="Declare the profile under profiles or update the reference",
        )
        return None
    return value


def _docker_service(
    value: Any,
    path: Path,
    parent_field: str,
    report: ValidationReport,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        report.add_error(
            "Runtime docker metadata must be a mapping",
            path=path,
            field=f"{parent_field}.docker",
            next_action="Use docker.compose_service to name the reference service",
        )
        return None
    service = value.get("compose_service")
    if service is None:
        return None
    if not isinstance(service, str) or not service:
        report.add_error(
            "Runtime docker compose service must be a non-empty string",
            path=path,
            field=f"{parent_field}.docker.compose_service",
            next_action="Use the Docker Compose service name, such as dev",
        )
        return None
    return service


def _input_paths(
    root: Path,
    profile_path: Path,
    value: Any,
    report: ValidationReport,
    *,
    field: str,
) -> tuple[list[Path], list[str]]:
    if value in (None, []):
        return [], []
    if not isinstance(value, list):
        report.add_error(
            "Runtime cache inputs must be a list",
            path=profile_path,
            field=field,
            next_action="Use a list of course-root-relative input file paths",
        )
        return [], []
    paths: list[Path] = []
    rel_paths: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item:
            report.add_error(
                "Runtime cache input path must be a non-empty string",
                path=profile_path,
                field=f"{field}.{index}",
                next_action="Use a course-root-relative input file path",
            )
            continue
        path, rel_path = _declared_file(
            root,
            profile_path,
            item,
            report,
            field=f"{field}.{index}",
            missing_message="Missing runtime input file",
        )
        if path is not None and rel_path is not None:
            paths.append(path)
            rel_paths.append(rel_path)
    return paths, rel_paths


def _declared_file(
    root: Path,
    profile_path: Path,
    value: Any,
    report: ValidationReport,
    *,
    field: str,
    missing_message: str,
) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not value:
        report.add_error(
            "Runtime file path must be a non-empty string",
            path=profile_path,
            field=field,
            next_action="Use a course-root-relative path",
        )
        return None, None
    raw_path = Path(value)
    if raw_path.is_absolute():
        report.add_error(
            "Runtime path must be relative",
            path=profile_path,
            field=field,
            next_action="Use a course-root-relative path",
        )
        return None, None
    resolved = (root / raw_path).resolve()
    try:
        rel_path = resolved.relative_to(root).as_posix()
    except ValueError:
        report.add_error(
            "Runtime path escapes course root",
            path=profile_path,
            field=field,
            next_action="Keep runtime paths inside the course root",
        )
        return None, None
    if not resolved.is_file():
        report.add_error(
            missing_message,
            path=profile_path,
            field=field,
            next_action=f"Create {rel_path} or update the runtime profile path",
        )
        return resolved, rel_path
    report.read_file(resolved)
    return resolved, rel_path


def _target_id(source_rel_path: str) -> str:
    digest = hashlib.sha256(source_rel_path.encode("utf-8")).hexdigest()[:12]
    return f"runtime:{digest}"


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()
