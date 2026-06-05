## ADDED Requirements

### Requirement: Local execution verification
Changes that affect local execution SHALL include host, Docker, cache, notebook, and no-execution regression verification.

#### Scenario: Script execution behavior changed
- **WHEN** local script execution behavior changes
- **THEN** verification MUST include contract or CLI tests proving explicit target execution, logs, outputs, exit codes, and nonzero failure diagnostics

#### Scenario: Notebook execution behavior changed
- **WHEN** local notebook execution behavior changes
- **THEN** verification MUST include tests proving generated output notebooks are produced without mutating authored source notebooks

#### Scenario: Cache behavior changed
- **WHEN** cache reuse or refresh behavior changes
- **THEN** verification MUST include tests for cache hit reuse, refresh rerun, stale cache diagnostics, and hidden no-execution paths

#### Scenario: Docker execution behavior changed
- **WHEN** Docker execution behavior changes
- **THEN** verification MUST include a representative Docker Compose plus `uv` workflow or document the exact environment gap

#### Scenario: Static no-execution regression
- **WHEN** local execution support changes
- **THEN** verification MUST prove `raya validate`, `raya build`, `raya artifacts inspect`, and static serving do not execute targets

### Requirement: Local execution documentation
Changes that introduce or modify local execution SHALL update foundation, rendered documentation, operational docs, and role guidance.

#### Scenario: Role docs updated
- **WHEN** local execution behavior changes author-facing, student-facing, contributor-facing, or agent-facing workflows
- **THEN** separate English and Spanish role pages for contributors/collaborators, professors, students, and agents MUST be updated or explicitly marked as deferred

#### Scenario: Phase plan updated
- **WHEN** the accepted local execution baseline changes
- **THEN** `docs/foundation/17_rendering_execution_plan.md` or a more specific foundation document MUST be updated and kept aligned with rendered documentation
