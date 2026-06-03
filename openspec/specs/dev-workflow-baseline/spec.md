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

