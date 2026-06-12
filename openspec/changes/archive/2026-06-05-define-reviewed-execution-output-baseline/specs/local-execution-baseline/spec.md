## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Generated results can be frozen
Generated local execution results SHALL be eligible for reviewed output freezing only when they are successful and current.

#### Scenario: Successful current result is eligible
- **WHEN** a generated execution result succeeded and matches the current target source, runtime profile, lockfile, declared inputs, and cache key
- **THEN** output freezing MAY use it as the source for reviewed output files and metadata

#### Scenario: Generated-only result is not reviewed
- **WHEN** a generated execution result exists but has not been frozen into reviewed source support
- **THEN** local execution and rendering MUST continue treating it as generated artifact data, not reviewed output
