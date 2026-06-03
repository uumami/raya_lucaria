## ADDED Requirements

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
