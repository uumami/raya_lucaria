## ADDED Requirements

### Requirement: Inspectable artifact contract
Course artifacts SHALL be inspectable as standalone build products through their manifest and generated data indexes.

#### Scenario: Artifact inspected without source course
- **WHEN** an artifact directory is inspected after being copied away from its source course
- **THEN** inspection MUST validate the artifact using the artifact root, `manifest.json`, and manifest-declared data indexes rather than source course files

#### Scenario: Required paths inspected
- **WHEN** an artifact is inspected
- **THEN** inspection MUST confirm `site/`, `data/`, `assets/`, `manifest.json`, and manifest-declared data index files exist
