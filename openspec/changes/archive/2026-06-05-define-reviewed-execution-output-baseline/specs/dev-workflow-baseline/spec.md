## ADDED Requirements

### Requirement: Reviewed output verification
Changes that affect reviewed or frozen execution output SHALL include source, artifact, static-read-path, command, and no-execution verification.

#### Scenario: Reviewed output behavior changed
- **WHEN** reviewed output source, validation, artifact data, freezing, or rendering behavior changes
- **THEN** verification MUST include contract tests for current reviewed output, stale reviewed output, missing reviewed files, generated-to-reviewed freezing, and artifact inspection

#### Scenario: Frozen policy changed
- **WHEN** frozen policy behavior changes
- **THEN** verification MUST include tests proving frozen targets validate reviewed output without executing and fail when reviewed output is missing or stale

#### Scenario: Static reviewed output changed
- **WHEN** reviewed output rendering changes
- **THEN** verification MUST include e2e/static-read-path tests proving reviewed panels and linked reviewed files work from `artifact/site/`

#### Scenario: No-execution regression
- **WHEN** reviewed/frozen output support changes
- **THEN** verification MUST prove `raya validate`, `raya build`, `raya artifacts inspect`, `raya outputs list`, `raya outputs freeze`, and static serving do not execute targets

### Requirement: Reviewed output documentation
Changes that introduce or modify reviewed/frozen execution output SHALL update foundation, rendered documentation, operational docs, and role guidance.

#### Scenario: Role docs updated
- **WHEN** reviewed output behavior changes author-facing, student-facing, contributor-facing, or agent-facing workflows
- **THEN** separate English and Spanish role pages for contributors/collaborators, professors, students, and agents MUST be updated or explicitly marked as deferred

#### Scenario: Phase plan updated
- **WHEN** the accepted reviewed output baseline changes
- **THEN** `docs/foundation/17_rendering_execution_plan.md` or a more specific foundation document MUST be updated and kept aligned with rendered documentation
