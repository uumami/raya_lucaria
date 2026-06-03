## ADDED Requirements

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
