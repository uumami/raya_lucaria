# documentation-surface-baseline Specification

## Purpose
Define documentation as a current truth surface for contributors, professors, students, and agents, including role-scoped English and Spanish guides, source-readable Markdown, rendered documentation fixtures, and spec-purpose hygiene.
## Requirements
### Requirement: Documentation is a current truth surface
Raya Lucaria SHALL treat current documentation as an explicit truth surface below foundation decisions and accepted specs, and separate from examples, generated artifacts, and historical material.

#### Scenario: Documentation listed in truth hierarchy
- **WHEN** the foundation truth-surface map is read
- **THEN** it MUST identify documentation as explanatory current guidance rather than fixture content or historical reference

#### Scenario: Documentation cannot override foundation
- **WHEN** documentation conflicts with `docs/foundation/` or accepted OpenSpec specs
- **THEN** the lower documentation surface MUST be treated as wrong until a new accepted decision updates the foundation or specs

### Requirement: Role-scoped documentation impact
Changes SHALL identify whether they affect contributor/collaborator, professor, student, or agent documentation.

#### Scenario: Change affects an audience
- **WHEN** a proposal changes behavior, contracts, commands, rendering, deployment, pedagogy, authority boundaries, or user-facing workflows
- **THEN** it MUST state which documentation audiences are affected and include documentation tasks for those audiences

#### Scenario: Change does not need documentation
- **WHEN** a proposal has no documentation impact for contributors, professors, students, or agents
- **THEN** it MUST state that no audience-facing documentation update is needed

### Requirement: Separate English and Spanish role documentation directories
Role documentation for contributors/collaborators, professors, students, and agents SHALL be available as separate English and Spanish role directories with `index.md` entry pages while preserving English technical identifiers.

#### Scenario: Role documentation is created or updated
- **WHEN** documentation is created or updated for contributors, professors, students, or agents
- **THEN** it MUST provide separate English and Spanish role directories with index pages or explicitly defer the missing language version in a tracked task

#### Scenario: Languages are not mixed in one role page
- **WHEN** role documentation is written in English or Spanish
- **THEN** the English and Spanish versions MUST be separate role directories rather than mixed-language sections in the same page

#### Scenario: Technical identifiers remain stable
- **WHEN** Spanish documentation describes packages, commands, schemas, file paths, or canonical domain names
- **THEN** it MUST preserve the English identifier and may explain it in Spanish near the identifier

### Requirement: Documentation remains separate from examples and course content
Documentation SHALL remain distinct from course/class material and repository examples.

#### Scenario: Docs explain current behavior
- **WHEN** documentation is added or updated
- **THEN** it MUST explain current accepted behavior or workflow and MUST NOT define course pedagogy, official course canon, or architecture by example

#### Scenario: Examples remain fixtures
- **WHEN** examples or fixtures are used to support documentation or tests
- **THEN** they MUST be labeled as fixtures or documentation examples and MUST NOT become authoritative user guidance by accident

### Requirement: Documentation source remains readable without rendering
Documentation source SHALL remain useful as plain files without requiring a backend, hosted service, or rendered site.

#### Scenario: Markdown docs are inspected directly
- **WHEN** a contributor, professor, student, or agent reads documentation source from the repository
- **THEN** the relevant documentation MUST be understandable without first running a renderer or dynamic service

### Requirement: Known missing work documentation
Documentation surfaces SHALL include a current known-missing-work inventory for deferred capabilities and intentional gaps.

#### Scenario: Deferred work is documented
- **WHEN** a contributor, professor, student, or agent needs to understand whether a capability is current behavior
- **THEN** current documentation MUST identify major deferred capabilities and intentional gaps without requiring readers to infer them from archived changes or old plans

#### Scenario: Deferred work is not current behavior
- **WHEN** known missing work is listed in current documentation
- **THEN** the listing MUST state that deferred work becomes current only through an accepted OpenSpec change, implementation, tests, and documentation

#### Scenario: Preview proposal remains parked
- **WHEN** current guidance describes the repository hygiene baseline
- **THEN** it MUST keep the parked preview proposal separate from the hygiene implementation scope

### Requirement: Current guidance consistency
Current guidance surfaces SHALL agree on canonical verification commands and accepted source layout.

#### Scenario: Canonical commands are consistent
- **WHEN** `README.md`, `AGENTS.md`, role guides, foundation docs, rendered docs, or `openspec/config.yaml` describe repository verification
- **THEN** they MUST point to the canonical host and Docker check scripts or explicitly explain a narrower focused command

#### Scenario: Source layout guidance is consistent
- **WHEN** current guidance describes course source layout, local assets, official support, reviewed output, runtime metadata, or code and notebook references
- **THEN** it MUST match accepted foundation and OpenSpec contracts, including extension-based `.py` and `.ipynb` reference ownership rather than required `code/` or `notebooks/` roots

#### Scenario: Role guidance is aligned
- **WHEN** contributor or agent guidance changes for repository verification, generated output handling, deferred work, or source layout
- **THEN** the English and Spanish role directories MUST be updated together or the deferred language page MUST be tracked explicitly in OpenSpec tasks

### Requirement: Rendered documentation is labeled and portable
Rendered documentation or documentation fixtures SHALL preserve the static-first and authority-boundary rules.

#### Scenario: Documentation is rendered by Glintstone
- **WHEN** documentation is rendered into a static artifact or exercised through a documentation fixture
- **THEN** it MUST be labeled as documentation or fixture material and MUST remain separate from class/course examples

#### Scenario: Rendered documentation stays portable
- **WHEN** rendered documentation is served from its static read path
- **THEN** it MUST not require a backend, configured host, CDN, identity provider, or client-side router

#### Scenario: Current docs render through ordered source
- **WHEN** the live repository documentation under `docs/` is validated or built
- **THEN** `docs/raya.yaml` MUST define a docs course whose ordered render source includes current foundation and role documentation without making generated artifact output authoritative

#### Scenario: Render source preserves readable doc paths
- **WHEN** the live docs render source references current documentation
- **THEN** readable repository paths such as `docs/foundation/` and `docs/guides/` MUST remain the human-facing documentation paths

### Requirement: Spec purpose hygiene
Accepted current specs SHALL have meaningful purpose text.

#### Scenario: Current specs are inspected
- **WHEN** current specs under `openspec/specs/` are reviewed or validated
- **THEN** they MUST NOT contain `Purpose` sections that remain `TBD` placeholders

#### Scenario: Change is archived
- **WHEN** a change creates or updates a current spec through archive
- **THEN** the resulting current spec MUST have a concise purpose describing what the capability covers
