## ADDED Requirements

### Requirement: Runtime policies drive local execution
Runtime profile and cache metadata SHALL determine whether local execution runs, reuses, or refuses an explicitly selected target.

#### Scenario: Manual policy executes explicit target
- **WHEN** a target policy is `manual` and the user explicitly selects that target with `raya run`
- **THEN** local execution MUST run the target through the selected profile

#### Scenario: Cache policy uses current cache key
- **WHEN** a target policy is `cache`
- **THEN** local execution MUST compare the current cache key with generated cache result metadata before deciding to reuse or run

#### Scenario: Always policy remains explicit
- **WHEN** a target policy is `always`
- **THEN** local execution MUST run only when the target is explicitly selected

#### Scenario: Never policy blocks local execution
- **WHEN** a target policy is `never`
- **THEN** local execution MUST refuse to run the target

#### Scenario: Frozen policy deferred
- **WHEN** a target policy is `frozen`
- **THEN** local execution MUST refuse to run or trust frozen output until a future accepted frozen-output contract exists

### Requirement: Runtime profile command construction
Runtime profile metadata SHALL be used to construct local and Docker execution command shapes.

#### Scenario: Local uv command shape
- **WHEN** local execution runs a script target under a `uv` profile
- **THEN** the command shape MUST use the profile project and lockfile metadata from the course root

#### Scenario: Docker uv command shape
- **WHEN** Docker execution is requested under a profile with Docker Compose service metadata
- **THEN** the command shape MUST include the declared Compose service and execute through the same `uv` profile semantics inside the container
