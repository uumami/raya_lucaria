## ADDED Requirements

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
