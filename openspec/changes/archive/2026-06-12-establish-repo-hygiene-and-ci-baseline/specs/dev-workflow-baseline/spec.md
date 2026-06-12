## ADDED Requirements

### Requirement: Canonical repository verification
The development workflow SHALL provide canonical repository verification scripts for host and Docker workflows.

#### Scenario: Host full check runs canonical gate
- **WHEN** a contributor or agent runs `./scripts/check.sh` from the repository root
- **THEN** the command MUST run the repository's full host verification gate, including whitespace checks, hygiene scans, strict OpenSpec validation, and Python/Raya verification through `./scripts/check-python.sh`

#### Scenario: Docker check uses reference container
- **WHEN** a contributor or agent runs `./scripts/check-docker.sh` from the repository root
- **THEN** the command MUST run the accepted Python/Raya verification path through the Docker Compose `dev` service without requiring the caller to copy the underlying command list

#### Scenario: Python verification is centralized
- **WHEN** host, Docker, or CI workflows need Python/Raya validation
- **THEN** they MUST call `./scripts/check-python.sh` or an equivalent repository-owned script rather than maintaining separate duplicated lists of `uv`, `pytest`, `raya validate`, `raya build`, and artifact inspection commands

#### Scenario: Verification output is actionable
- **WHEN** a canonical verification script runs
- **THEN** it MUST print the major command or check being run so failures identify the concrete workflow step that needs attention

### Requirement: Repository hygiene verification
The development workflow SHALL include repository hygiene checks that protect current guidance, source truth, and generated-output boundaries.

#### Scenario: Stale current guidance is scanned
- **WHEN** repository hygiene verification runs
- **THEN** it MUST scan current guidance surfaces for stale renderer assumptions, stale source-layout requirements, command drift, or other current wording that conflicts with accepted foundation or specs

#### Scenario: Generated output pollution is scanned
- **WHEN** repository hygiene verification runs
- **THEN** it MUST fail if generated artifacts, static site output, caches, dependency folders, or local session output appear as tracked source or untracked source that should be ignored

#### Scenario: OpenSpec incomplete markers are scanned
- **WHEN** repository hygiene verification runs
- **THEN** it MUST fail on incomplete markers in current specs or current documentation surfaces that are expected to be accepted guidance

#### Scenario: Fixture labeling is scanned
- **WHEN** repository hygiene verification runs
- **THEN** it MUST verify that repository examples, galleries, rendered documentation fixtures, or similar preview surfaces remain labeled as fixture or documentation material rather than hidden authority

### Requirement: CI verification
The development workflow SHALL provide CI that runs the canonical repository verification scripts.

#### Scenario: CI installs accepted tools
- **WHEN** CI runs for the repository
- **THEN** it MUST install the accepted Python, `uv`, OpenSpec, and Docker Compose tooling needed by the canonical checks or document any platform limitation

#### Scenario: CI calls repository scripts
- **WHEN** CI verifies the repository
- **THEN** it MUST call repository-owned scripts such as `./scripts/check.sh` and `./scripts/check-docker.sh` instead of duplicating their command lists in workflow configuration

#### Scenario: CI documents Docker limits
- **WHEN** CI cannot run the accepted Docker verification path
- **THEN** the workflow or current repository guidance MUST document the limitation and identify the local Docker command contributors should run before archive or merge
