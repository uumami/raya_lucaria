# runtime-profile-cache-baseline Specification

## Purpose
Defines the metadata-only runtime and cache baseline for future execution: where runtime profiles live, which execution policies are accepted, how cache keys are derived, and how validation, build, and artifact inspection remain non-executing.

## Requirements
### Requirement: Runtime profile source
Raya Lucaria SHALL define runtime profiles as source support metadata outside the ordered learning tree.

#### Scenario: Runtime profile file location
- **WHEN** a course declares runtime profiles
- **THEN** the profile file MUST live under `runtime/profiles.yaml` beside the configured `course/` source tree

#### Scenario: Runtime support does not render
- **WHEN** validation or build scans `runtime/`
- **THEN** files under `runtime/` MUST NOT become rendered pages, generated index entries, navigation entries, official learning objects, or source assets

#### Scenario: Runtime files stay source support
- **WHEN** a course contains `pyproject.toml`, `uv.lock`, Docker files, or `runtime/profiles.yaml`
- **THEN** validation MUST treat them as execution support files rather than learning quanta

### Requirement: Runtime profile fields
Runtime profiles SHALL provide minimal, portable metadata for future execution managers.

#### Scenario: Default uv profile
- **WHEN** `runtime/profiles.yaml` declares a profile with `manager: uv`
- **THEN** validation MUST accept profile metadata for Python version or constraint, project file path, lockfile path, and optional Docker Compose service metadata

#### Scenario: Unsupported manager
- **WHEN** a profile declares a manager other than `uv`
- **THEN** validation MUST fail unless a future accepted adapter contract supports that manager

#### Scenario: Missing declared project file
- **WHEN** a profile declares a project file path that does not exist under the course root
- **THEN** validation MUST fail with an actionable diagnostic naming the profile and missing path

#### Scenario: Missing declared lockfile
- **WHEN** a `uv` profile requires a lockfile path that does not exist under the course root
- **THEN** validation MUST fail or warn according to the accepted profile strictness and name the profile and missing lockfile

### Requirement: Execution policy metadata
Raya Lucaria SHALL model executable intent with explicit policies before any execution engine exists.

#### Scenario: Allowed policy values
- **WHEN** source metadata declares an execution policy
- **THEN** validation MUST accept only `never`, `manual`, `cache`, `always`, and `frozen`

#### Scenario: Default policy is never
- **WHEN** executable source support has no explicit policy
- **THEN** generated execution metadata MUST record policy `never` and status `not-executed`

#### Scenario: Unsafe always policy is explicit
- **WHEN** source metadata declares policy `always`
- **THEN** validation MUST require an explicit target-level declaration and MUST NOT infer `always` from a profile default

#### Scenario: Frozen output remains metadata only
- **WHEN** source metadata declares policy `frozen`
- **THEN** Phase 3 validation MUST record the policy but MUST NOT trust, execute, refresh, or publish output content without a later accepted frozen-output contract

### Requirement: Cache key metadata
Raya Lucaria SHALL generate cache-key metadata from declared inputs without running executable targets.

#### Scenario: Cache key inputs
- **WHEN** an executable target has runtime metadata
- **THEN** generated cache metadata MUST include hashes or identifiers for source file content, declared input files, runtime profile metadata, lockfile content when present, execution policy, and relevant Raya or Glintstone schema versions

#### Scenario: Cache key is not execution proof
- **WHEN** a cache key is generated
- **THEN** artifact metadata MUST distinguish the cache key from an executed result, trusted output, or refreshed cache entry

#### Scenario: Declared input path validation
- **WHEN** runtime metadata declares input files for a cache key
- **THEN** validation MUST require those paths to stay under the authored course root and fail with an actionable diagnostic for missing or escaping paths

### Requirement: Runtime metadata does not execute
Runtime profile and cache metadata handling SHALL NOT execute scripts, notebook cells, kernels, package managers, Docker commands, or runtime commands.

#### Scenario: Validation does not create environments
- **WHEN** validation checks runtime profiles
- **THEN** it MUST NOT create virtual environments, install packages, call `uv`, call Docker, or start kernels

#### Scenario: Build does not refresh cache
- **WHEN** Glintstone builds runtime and cache metadata
- **THEN** it MUST NOT execute targets, refresh cache entries, trust notebook outputs, or write generated execution outputs

#### Scenario: Artifact inspection does not execute
- **WHEN** artifact inspection validates runtime, execution, or cache metadata
- **THEN** it MUST NOT execute targets, resolve package environments, call Docker, call `uv`, or refresh cache entries
