## ADDED Requirements

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
