## ADDED Requirements

### Requirement: Runtime metadata verification
Changes that affect runtime profile, execution policy, or cache metadata behavior SHALL include contract and fixture verification without running executable course code.

#### Scenario: Runtime metadata behavior changed
- **WHEN** a change modifies runtime profile parsing, policy validation, cache-key generation, runtime artifact data, execution-plan artifact data, or cache metadata artifact data
- **THEN** verification MUST include contract tests for valid fixtures, invalid diagnostics, generated data schemas, artifact inspection, and static build preservation

#### Scenario: Docker plus uv metadata fixture
- **WHEN** runtime profile behavior changes
- **THEN** verification MUST include a representative fixture that declares a `uv` profile and Docker Compose service metadata without requiring test code to execute the profile

#### Scenario: Invalid runtime fixtures
- **WHEN** runtime profile validation changes
- **THEN** verification MUST include invalid fixtures or equivalent tests for unsupported managers, missing project files, missing or stale lockfile signals, path escapes, and unsafe execution defaults

### Requirement: Runtime metadata documentation
Changes that introduce or modify runtime profiles, execution policies, or cache metadata SHALL update foundation, rendered documentation, and role guidance.

#### Scenario: Role docs updated
- **WHEN** runtime profile, execution policy, or cache metadata behavior changes author-facing, student-facing, contributor-facing, or agent-facing workflows
- **THEN** separate English and Spanish role pages for contributors/collaborators, professors, students, and agents MUST be updated or explicitly marked as deferred

#### Scenario: Phase plan updated
- **WHEN** the accepted runtime profile or cache metadata baseline changes
- **THEN** `docs/foundation/17_rendering_execution_plan.md` or a more specific foundation document MUST be updated and kept aligned with rendered documentation
