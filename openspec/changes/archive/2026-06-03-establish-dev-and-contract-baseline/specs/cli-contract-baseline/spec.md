## ADDED Requirements

### Requirement: Python CLI package
The first operational CLI SHALL be a Python package managed through the repository's `uv` workflow.

#### Scenario: CLI entrypoint exists
- **WHEN** dependencies are synced through Docker or local `uv`
- **THEN** the `raya` command MUST be available in the configured environment

### Requirement: Help command
The CLI SHALL provide `raya --help` as the first discoverable command surface.

#### Scenario: Print help
- **WHEN** a user runs `raya --help`
- **THEN** the CLI MUST print available commands and exit successfully

### Requirement: Doctor command
The CLI SHALL provide `raya doctor` to report detected context, environment status, and actionable setup diagnostics.

#### Scenario: Framework repository context
- **WHEN** `raya doctor` runs from the framework repository
- **THEN** it MUST identify the framework context and report relevant files or directories it inspected

#### Scenario: Unknown context
- **WHEN** `raya doctor` runs outside a recognized framework, course, or installation context
- **THEN** it MUST report an unknown context with concrete next actions instead of guessing

### Requirement: Validate command
The CLI SHALL provide `raya validate <course>` to validate source course contracts before any build step.

#### Scenario: Valid minimal fixture
- **WHEN** `raya validate examples/courses/minimal` runs against a valid fixture
- **THEN** it MUST exit successfully and report the course files inspected

#### Scenario: Invalid source course
- **WHEN** `raya validate <course>` finds contract violations
- **THEN** it MUST exit nonzero and print actionable diagnostics tied to concrete files or fields

### Requirement: Stable diagnostics and exits
CLI commands SHALL use predictable exit codes and diagnostics suitable for humans and coding agents.

#### Scenario: Failure exits nonzero
- **WHEN** a CLI command fails validation or setup checks
- **THEN** it MUST exit with a nonzero status

#### Scenario: Diagnostics name files
- **WHEN** a CLI command reads source files or writes outputs
- **THEN** diagnostics MUST identify the relevant files read and outputs written

### Requirement: No hidden global state
The baseline CLI SHALL NOT depend on hidden global state for course validation.

#### Scenario: Validate explicit course path
- **WHEN** a user passes an explicit course path to `raya validate`
- **THEN** validation MUST derive its inputs from that path and documented configuration files
