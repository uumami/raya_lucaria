## ADDED Requirements

### Requirement: Rendered surface verification
Changes that affect rendered surface discipline SHALL include contract and static-read-path verification for both visible reader content and hidden machine-only internals.

#### Scenario: Default page visibility tested
- **WHEN** rendered-surface behavior changes
- **THEN** verification MUST prove representative default pages show authored content, navigation, generated indexes, compact resource/status labels, and deployment-neutral links

#### Scenario: Metadata leakage tested
- **WHEN** rendered-surface behavior changes
- **THEN** verification MUST prove representative default pages do not dump raw JSON, source hashes, cache keys, artifact storage paths, browser storage paths, or verbose runtime/execution internals into the main reading flow

#### Scenario: Machine data preservation tested
- **WHEN** rendered-surface behavior changes
- **THEN** verification MUST prove manifest-declared artifact data and artifact inspection still expose the complete accepted metadata

#### Scenario: Static inspection tested
- **WHEN** inspection surfaces are generated or changed
- **THEN** verification MUST prove those surfaces work from the static read path without executing targets or requiring a backend

### Requirement: Examples gallery verification
Changes that add or modify repository example preview surfaces SHALL include fixture labeling, build, and static-read-path checks.

#### Scenario: Gallery builds with fixtures
- **WHEN** the examples/gallery surface changes
- **THEN** verification MUST build the representative fixtures and prove the gallery links to their generated static entrypoints

#### Scenario: Gallery labels examples as fixtures
- **WHEN** the examples/gallery surface is rendered
- **THEN** verification MUST prove it labels entries as fixture material and points to foundation docs or accepted specs for authority

#### Scenario: Gallery static links work
- **WHEN** the gallery is served through local static hosting or static-read-path tests
- **THEN** links to fixture pages, support resources, referenced files, and reviewed files MUST resolve without backend routes or absolute deployment-root assumptions

### Requirement: Rendered surface documentation
Changes that introduce or modify rendered-surface discipline SHALL update foundation, rendered documentation, role guidance, and agent/proposal guidance.

#### Scenario: Role docs updated
- **WHEN** rendered-surface behavior changes author-facing, student-facing, contributor-facing, professor-facing, or agent-facing workflows
- **THEN** separate English and Spanish role pages for contributors/collaborators, professors, students, and agents MUST be updated or explicitly marked as deferred

#### Scenario: Foundation docs updated
- **WHEN** rendered-surface discipline changes the relationship between artifact data and rendered pages
- **THEN** `docs/foundation/06_artifact_contract.md`, `docs/foundation/15_system_overview.md`, `docs/foundation/16_documentation_surfaces.md`, or `docs/foundation/17_rendering_execution_plan.md` MUST be updated as appropriate

#### Scenario: Agent and proposal guidance updated
- **WHEN** rendered-surface discipline becomes an accepted baseline
- **THEN** `AGENTS.md` and `openspec/config.yaml` MUST tell future agents and proposals to keep normal pages focused and use manifest-declared data or inspection surfaces for verbose internals
