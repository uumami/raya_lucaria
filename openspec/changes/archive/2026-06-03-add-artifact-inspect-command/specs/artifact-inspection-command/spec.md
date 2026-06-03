## ADDED Requirements

### Requirement: Artifact inspection command
The system SHALL provide a read-only artifact inspection workflow for validating a built course artifact as a portable unit.

#### Scenario: Inspect generated artifact
- **WHEN** a valid artifact directory produced by `raya build <course>` is inspected
- **THEN** inspection MUST validate the artifact manifest, required artifact paths, and manifest-declared data indexes without requiring source course files

### Requirement: Manifest-centered inspection
Artifact inspection SHALL use `manifest.json` as the entrypoint for generated data validation.

#### Scenario: Follow manifest data paths
- **WHEN** `manifest.json` declares pages, quanta, links, and official data index paths
- **THEN** inspection MUST validate those indexes relative to the artifact root

### Requirement: Read-only behavior
Artifact inspection SHALL NOT modify the artifact being inspected.

#### Scenario: Inspect without writes
- **WHEN** artifact inspection completes successfully or fails
- **THEN** diagnostics MUST report files read and MUST NOT report generated outputs written by inspection

### Requirement: Required artifact path checks
Artifact inspection SHALL validate the baseline artifact path shape before reporting success.

#### Scenario: Missing required path
- **WHEN** a required artifact path such as `site/`, `data/`, `assets/`, or `manifest.json` is missing
- **THEN** inspection MUST fail with an actionable diagnostic tied to the missing path

### Requirement: Stable inspection diagnostics
Artifact inspection SHALL use predictable diagnostics suitable for humans and coding agents.

#### Scenario: Inspection failure
- **WHEN** artifact inspection finds malformed JSON, invalid schema data, or missing manifest-declared indexes
- **THEN** it MUST fail with nonzero CLI exit behavior and diagnostics naming concrete files or fields
