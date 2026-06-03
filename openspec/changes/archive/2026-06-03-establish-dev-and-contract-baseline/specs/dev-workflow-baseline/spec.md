## ADDED Requirements

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
