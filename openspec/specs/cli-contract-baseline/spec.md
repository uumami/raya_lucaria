# cli-contract-baseline Specification

## Purpose
Defines the first `raya` CLI package, command surface, diagnostics, and baseline workflows for humans and coding agents.
## Requirements
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

### Requirement: Build command
The CLI SHALL provide `raya build <course>` to produce a static course artifact from an explicit source course path.

#### Scenario: Build explicit course path
- **WHEN** a user runs `raya build examples/courses/minimal`
- **THEN** the CLI MUST validate the source course, build the configured artifact output, report files read and outputs written, and exit successfully

#### Scenario: Build failure exits nonzero
- **WHEN** `raya build <course>` encounters source validation errors or artifact generation errors
- **THEN** the CLI MUST exit nonzero and print actionable diagnostics tied to concrete files, fields, or output paths

#### Scenario: Build has no hidden global state
- **WHEN** a user passes an explicit course path to `raya build`
- **THEN** build inputs MUST derive from that path and documented configuration files

### Requirement: Artifacts inspect command
The CLI SHALL provide `raya artifacts inspect <artifact>` to validate a built course artifact from an explicit artifact path.

#### Scenario: Inspect explicit artifact path
- **WHEN** a user runs `raya artifacts inspect <artifact>` against a valid artifact directory
- **THEN** the CLI MUST validate the artifact contract, report files read, and exit successfully

#### Scenario: Inspect failure exits nonzero
- **WHEN** `raya artifacts inspect <artifact>` finds missing paths, malformed manifest data, or invalid indexes
- **THEN** the CLI MUST exit nonzero and print actionable diagnostics tied to concrete artifact files or fields

#### Scenario: Inspect has no hidden global state
- **WHEN** a user passes an explicit artifact path to `raya artifacts inspect`
- **THEN** inspection inputs MUST derive from that artifact path and its manifest

### Requirement: Course init command
The CLI SHALL provide `raya course init <path>` to create a valid minimal source course from an explicit target path.

#### Scenario: Init explicit course path
- **WHEN** a user runs `raya course init <path>`
- **THEN** the CLI MUST create the baseline source-course files, report outputs written, and exit successfully

#### Scenario: Init failure exits nonzero
- **WHEN** `raya course init <path>` cannot safely create the course source
- **THEN** the CLI MUST exit nonzero and print actionable diagnostics tied to concrete files or directories

#### Scenario: Init has no hidden global state
- **WHEN** a user passes an explicit target path to `raya course init`
- **THEN** initialization inputs MUST derive from that path and explicit command flags

### Requirement: Run command
The CLI SHALL provide `raya run <course> <target>` for explicit local execution of one accepted code or notebook target.

#### Scenario: Run explicit target
- **WHEN** a user runs `raya run <course> <target>` for a valid executable target
- **THEN** the CLI MUST resolve the course, validate source/runtime metadata, run the selected target according to policy, report files read and outputs written, and exit successfully when execution succeeds

#### Scenario: Run target failure exits nonzero
- **WHEN** local execution fails before or during target execution
- **THEN** the CLI MUST exit nonzero and print actionable diagnostics tied to concrete files, fields, commands, or generated output paths

#### Scenario: Run dry-run
- **WHEN** a user runs `raya run <course> <target> --dry-run`
- **THEN** the CLI MUST print the resolved execution plan and exit successfully without executing the target

#### Scenario: Run refresh
- **WHEN** a user runs `raya run <course> <target> --refresh`
- **THEN** the CLI MUST request cache refresh behavior for cache policy targets

#### Scenario: Run docker
- **WHEN** a user runs `raya run <course> <target> --docker`
- **THEN** the CLI MUST request Docker plus `uv` execution through the selected runtime profile

#### Scenario: Build remains separate
- **WHEN** a user runs `raya build <course>`
- **THEN** the CLI MUST NOT execute scripts, notebooks, Docker commands, kernels, or cache refreshes

### Requirement: Outputs command
The CLI SHALL provide `raya outputs` subcommands for non-executing exploration and freezing of execution outputs.

#### Scenario: Outputs list command
- **WHEN** a user runs `raya outputs list <course>`
- **THEN** the CLI MUST report target IDs, policies, generated result status, reviewed output status, frozen validation status, and relevant file paths without executing targets

#### Scenario: Outputs freeze command
- **WHEN** a user runs `raya outputs freeze <course> <target>` for a current successful generated result
- **THEN** the CLI MUST write reviewed source support under colocated `_reviewed/`, report outputs written, and exit successfully without running the target

#### Scenario: Outputs command failure exits nonzero
- **WHEN** output listing or freezing finds stale reviewed output, missing generated results, failed generated results, malformed metadata, or missing files
- **THEN** the CLI MUST exit nonzero and print actionable diagnostics tied to concrete files, fields, commands, or target IDs

#### Scenario: Outputs commands do not execute
- **WHEN** a user runs any `raya outputs` command
- **THEN** the CLI MUST NOT execute scripts, notebooks, kernels, `uv`, Docker, package installers, or cache refreshes
