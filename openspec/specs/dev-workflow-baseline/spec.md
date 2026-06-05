# dev-workflow-baseline Specification

## Purpose
Defines the Docker Compose and `uv` development workflow, local escape hatch, smoke checks, e2e expectations, and provider-neutral baseline.
## Requirements
### Requirement: Docker Compose reference workflow
The repository SHALL provide Docker Compose as the documented reference development workflow for the first contract and CLI implementation.

#### Scenario: Run CLI through Docker
- **WHEN** a contributor follows the documented Docker workflow from the repository root
- **THEN** the workflow MUST run the `raya` CLI without requiring a host Python virtual environment

#### Scenario: Docker workflow is canonical for setup
- **WHEN** Docker and Docker Compose are available
- **THEN** the documented setup MUST prefer Docker Compose over ad hoc host-machine setup

### Requirement: uv Python environment
The first Python packages SHALL use `uv` for dependency resolution, environment creation, and local non-Docker execution.

#### Scenario: Sync Python dependencies
- **WHEN** a contributor runs the documented `uv` setup command
- **THEN** the command MUST create or update a Python environment that can run the `raya` CLI

#### Scenario: Container uses uv
- **WHEN** the Docker development workflow installs Python dependencies
- **THEN** it MUST use `uv` instead of unmanaged `pip install` commands

### Requirement: Local non-Docker escape hatch
The repository SHALL document a local non-Docker workflow for contributors who need to run the first CLI and tests directly on the host.

#### Scenario: Run CLI locally
- **WHEN** a contributor has Python and `uv` installed locally
- **THEN** the documented local workflow MUST run `raya --help` without Docker

### Requirement: External course smoke test
The repository SHALL provide a focused smoke-test workflow for validating a source course outside the framework checkout without creating a permanent second repository.

#### Scenario: Validate temporary external course
- **WHEN** the smoke-test workflow runs from the repository root
- **THEN** it MUST copy the minimal fixture course into a temporary directory outside the repository, validate that external course locally, validate it through Docker Compose with an explicit temporary mount, and clean up the temporary files

### Requirement: Baseline development commands
The development workflow SHALL define commands for checking the foundation docs, syncing dependencies, running the CLI, and running baseline tests.

#### Scenario: Execute baseline checks
- **WHEN** a contributor runs the documented baseline check command set
- **THEN** it MUST include the foundation file listing check, stale renderer assumption check, CLI help, contract tests, and external-course smoke test once implemented

### Requirement: Provider and renderer neutrality
The development workflow SHALL NOT require a hosted service, identity provider, JavaScript framework, or static-site renderer for the baseline contract work.

#### Scenario: No backend needed
- **WHEN** the baseline workflow validates the minimal fixture course
- **THEN** it MUST complete without network services, auth providers, databases, or a frontend build pipeline

### Requirement: Static render e2e workflow
The development workflow SHALL include real e2e or static-read-path tests when a change affects rendered HTML, browser-facing resources, deployment portability, or static site behavior.

#### Scenario: Rendered static site e2e
- **WHEN** a change modifies static rendering or browser-facing generated resources
- **THEN** the verification workflow MUST build a representative fixture and test the generated `artifact/site/` read path rather than only checking source validation or string-level unit behavior

#### Scenario: Docker e2e compatibility
- **WHEN** rendered static site e2e tests are added
- **THEN** they MUST run through the Docker Compose reference workflow or explicitly document any required Docker setup change

#### Scenario: Fixture content remains labeled
- **WHEN** e2e fixture content is created for renderer coverage
- **THEN** it MUST be labeled as fixture material and MUST NOT be treated as canonical pedagogy, architecture, or foundation truth

### Requirement: Documentation impact in change workflow
The development workflow SHALL require documentation impact to be considered for every substantial change.

#### Scenario: Proposal documents documentation impact
- **WHEN** a proposal is created for a change that affects behavior, contracts, commands, rendering, deployment, pedagogy, authority boundaries, or user-facing workflows
- **THEN** the proposal MUST identify affected documentation audiences or explicitly state that no documentation update is needed

#### Scenario: Tasks include documentation work
- **WHEN** a proposal identifies documentation impact
- **THEN** the task list MUST include the smallest appropriate documentation updates and any required documentation checks

### Requirement: Documentation hygiene checks
The development workflow SHALL include focused documentation hygiene checks when a change creates or updates documentation, specs, or rendered documentation fixtures.

#### Scenario: Specs are updated
- **WHEN** a change creates or updates current OpenSpec specs
- **THEN** verification MUST check that current specs do not retain `Purpose: TBD` placeholders

#### Scenario: Documentation fixtures are added
- **WHEN** a change adds rendered documentation or documentation fixtures
- **THEN** verification MUST check that the fixture is labeled as documentation or fixture material and remains separate from class/course examples

#### Scenario: Role documentation is updated
- **WHEN** a change creates or updates documentation for contributors/collaborators, professors, students, or agents
- **THEN** verification MUST check that separate English and Spanish role directories with index pages are present or that any deferred language version is tracked

### Requirement: Ordered content verification
Changes that affect ordered content, generated indexes, stable references, or static navigation SHALL include focused contract and e2e verification.

#### Scenario: Ordered content contracts changed
- **WHEN** a change modifies ordered source conventions, page metadata, generated index behavior, stable `raya:` links, or navigation artifact data
- **THEN** verification MUST include contract tests for source validation, metadata parsing, stable reference resolution, generated navigation data, and generated index data

#### Scenario: Rendered index behavior changed
- **WHEN** a change modifies generated local indexes, master indexes, breadcrumbs, previous/next links, or stable rendered links
- **THEN** verification MUST include a representative static-read-path e2e fixture that renders those behaviors from source content

### Requirement: Ordered content documentation
Changes that introduce or modify the ordered authoring model SHALL update role documentation for affected audiences.

#### Scenario: Role docs updated
- **WHEN** ordered content, generated indexes, stable IDs, or authoring metadata change
- **THEN** documentation tasks MUST update separate English and Spanish role documentation for contributors/collaborators, professors, students, and agents or explicitly track any deferred role-language page

#### Scenario: Documentation includes source and rendered views
- **WHEN** role documentation explains ordered content behavior
- **THEN** it MUST show both the source-tree authoring model and the rendered student-facing result so readers do not confuse filename mechanics with student navigation labels

### Requirement: Unified source tree verification
Changes that affect the authored source root, support-directory conventions, official learning-object colocation, or colocated assets SHALL include focused contract and e2e verification.

#### Scenario: Unified source contract changed
- **WHEN** a change modifies `source: course`, unsupported source-root fields, `_official/`, `_assets/`, support path classification, or source-root behavior
- **THEN** verification MUST include contract tests for configuration resolution, source validation, support directory privacy, official object discovery, asset validation, and representative artifact generation

#### Scenario: Unified source static behavior changed
- **WHEN** a change modifies how unified source content renders, exports study seed data, copies assets, or creates browser-facing links
- **THEN** verification MUST include a representative static-read-path e2e fixture that exercises rendered pages, generated indexes, official object export, and colocated asset URLs

### Requirement: Unified source documentation
Changes that introduce or modify the unified authored source tree SHALL update the documentation surfaces that authors, learners, contributors, and agents use to understand course structure.

#### Scenario: Unified source role docs updated
- **WHEN** `source: course`, colocated `_official/`, colocated `_assets/`, or support-directory privacy changes
- **THEN** documentation tasks MUST update separate English and Spanish role documentation for contributors/collaborators, professors, students, and agents or explicitly track any deferred role-language page

#### Scenario: Unified source foundation docs updated
- **WHEN** the canonical source-course tree changes
- **THEN** documentation tasks MUST update the foundation course contract, system overview, documentation surface map, and OpenSpec config guidance as needed

### Requirement: Rich rendering verification
Changes that affect rich static rendering SHALL include representative contract and e2e verification.

#### Scenario: Rich rendering contracts changed
- **WHEN** a change modifies Markdown rendering, math rendering, code block rendering, callouts, footnotes, heading anchors, page table of contents, or rich render support resources
- **THEN** verification MUST include contract tests for generated HTML, link/asset rewriting, artifact validation, and static read-path behavior

#### Scenario: Rich rendering e2e fixture
- **WHEN** rich static rendering behavior changes
- **THEN** verification MUST include a representative fixture that renders at least one root page and one nested page through `artifact/site/`

#### Scenario: Rich rendering Docker coverage
- **WHEN** rich static rendering introduces parser, highlighter, math, or renderer dependencies
- **THEN** verification MUST include the Docker Compose reference workflow or explicitly document any Docker workflow gap

### Requirement: Rich rendering documentation
Changes that introduce or modify rich static rendering SHALL update the documentation surfaces authors, learners, contributors, and agents use.

#### Scenario: Rich rendering role docs updated
- **WHEN** rich rendering changes author-facing syntax or student-facing rendered behavior
- **THEN** documentation tasks MUST update separate English and Spanish role documentation for contributors/collaborators, professors, students, and agents or explicitly track any deferred role-language page

#### Scenario: Rich rendering foundation and rendered docs updated
- **WHEN** the accepted rich rendering baseline changes
- **THEN** documentation tasks MUST update the rendering execution plan or other relevant foundation docs and keep the live rendered docs tree aligned

