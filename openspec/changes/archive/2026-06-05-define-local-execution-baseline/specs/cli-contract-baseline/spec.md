## ADDED Requirements

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
