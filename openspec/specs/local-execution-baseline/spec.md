# local-execution-baseline Specification

## Purpose
Defines the explicit local execution baseline for referenced scripts and notebooks: target-scoped `raya run`, runtime profile usage, policy behavior, cache reuse, generated logs/results, and the no-execution guarantees for validation, build, inspection, and static serving.

## Requirements
### Requirement: Explicit local execution command
Raya Lucaria SHALL provide local execution only through an explicit command and explicit target selection.

#### Scenario: Explicit target required
- **WHEN** a user runs local execution
- **THEN** the command MUST require a course path and a specific target identifier or source path

#### Scenario: No implicit course-wide execution
- **WHEN** a course contains multiple executable references
- **THEN** local execution MUST NOT run every target unless a future accepted contract defines an explicit multi-target selector

#### Scenario: Dry run reports execution plan
- **WHEN** a user runs local execution with dry-run mode
- **THEN** the command MUST report the resolved target, policy, profile, command shape, cache decision, and output locations without executing code

### Requirement: Script execution through uv
Local script execution SHALL use the selected `uv` runtime profile rather than the static renderer or hidden interpreter state.

#### Scenario: Script target executes
- **WHEN** a user explicitly runs a valid `.py` target with policy `manual`, `cache`, or `always`
- **THEN** Raya MUST execute the target through the selected `uv` profile, capture stdout, stderr, exit code, and timing metadata, and write generated result metadata

#### Scenario: Missing uv fails clearly
- **WHEN** script execution requires `uv` and `uv` is unavailable
- **THEN** the command MUST fail with an actionable diagnostic and MUST NOT fall back to hidden interpreter state

#### Scenario: Never policy refuses execution
- **WHEN** a target policy is `never`
- **THEN** local execution MUST fail without running the target unless a future accepted override contract exists

### Requirement: Notebook execution through Jupyter tooling
Local notebook execution SHALL use established notebook execution tooling and generated output notebooks.

#### Scenario: Notebook target executes
- **WHEN** a user explicitly runs a valid `.ipynb` target with policy `manual`, `cache`, or `always`
- **THEN** Raya MUST execute the notebook through accepted Jupyter tooling under the selected runtime profile and write a generated output notebook

#### Scenario: Notebook tooling missing
- **WHEN** notebook execution tooling is unavailable
- **THEN** the command MUST fail with an actionable diagnostic and MUST NOT treat notebook source as a plain script

#### Scenario: Source notebook unchanged
- **WHEN** a notebook target executes successfully
- **THEN** the authored source notebook MUST NOT be modified in place

### Requirement: Docker execution wrapper
Local execution SHALL support Docker plus `uv` as an explicit reproducibility wrapper when profile metadata declares a Docker Compose service.

#### Scenario: Docker execution requested
- **WHEN** a user requests Docker execution for a target whose profile declares a Docker Compose service
- **THEN** Raya MUST run the target through the declared service or report the exact command shape in dry-run mode

#### Scenario: Docker metadata missing
- **WHEN** a user requests Docker execution for a target whose profile lacks Docker Compose service metadata
- **THEN** the command MUST fail with an actionable diagnostic

#### Scenario: Docker not default
- **WHEN** a runtime profile declares Docker metadata but the user does not request Docker execution
- **THEN** local execution MUST use the local `uv` path

### Requirement: Cache-aware local execution
Local execution SHALL respect execution policies and cache/reviewed-output metadata when deciding whether to run, reuse, refuse, or validate a target.

#### Scenario: Cache hit reused
- **WHEN** a `cache` policy target has a valid cache entry matching the current cache key
- **THEN** local execution MUST reuse the cached result without running the target

#### Scenario: Refresh reruns cache target
- **WHEN** a user passes refresh for a `cache` policy target
- **THEN** local execution MUST run the target and update generated cache result metadata

#### Scenario: Always reruns explicit target
- **WHEN** a user explicitly runs an `always` policy target
- **THEN** local execution MUST run the target even if previous generated output exists

#### Scenario: Frozen validates explicit target
- **WHEN** a user explicitly runs a `frozen` policy target
- **THEN** local execution MUST validate that current reviewed output exists for the target and MUST NOT execute scripts, notebooks, kernels, `uv`, Docker, package installers, or cache refreshes

### Requirement: Generated results can be frozen
Generated local execution results SHALL be eligible for reviewed output freezing only when they are successful and current.

#### Scenario: Successful current result is eligible
- **WHEN** a generated execution result succeeded and matches the current target source, runtime profile, lockfile, declared inputs, and cache key
- **THEN** output freezing MAY use it as the source for reviewed output files and metadata

#### Scenario: Generated-only result is not reviewed
- **WHEN** a generated execution result exists but has not been frozen into reviewed source support
- **THEN** local execution and rendering MUST continue treating it as generated artifact data, not reviewed output

### Requirement: Generated execution outputs
Local execution SHALL write outputs, logs, cache records, and result metadata as generated artifact data.

#### Scenario: Result metadata written
- **WHEN** local execution completes or fails after starting a target
- **THEN** Raya MUST write generated result metadata including target ID, source path, profile, policy, status, exit code when available, start/end time, output path, log path, and cache key when applicable

#### Scenario: Logs written
- **WHEN** local execution starts a target
- **THEN** Raya MUST write generated logs under the artifact root without modifying authored course source

#### Scenario: Static build remains non-executing
- **WHEN** a user runs `raya build`
- **THEN** static build MUST NOT execute local targets, refresh cache entries, or update execution result logs
