## ADDED Requirements

### Requirement: Inspect code and notebook reference artifacts
Artifact inspection SHALL validate manifest-declared code and notebook reference data and copied referenced files.

#### Scenario: Reference data validates
- **WHEN** artifact inspection finds manifest-declared reference data
- **THEN** it MUST validate that data against the accepted reference data schema

#### Scenario: Referenced artifact file exists
- **WHEN** reference data declares an artifact-level file path
- **THEN** artifact inspection MUST verify that the copied file exists under generated artifact file storage

#### Scenario: Referenced browser file exists
- **WHEN** reference data declares a browser-facing file path
- **THEN** artifact inspection MUST verify that the copied file exists under the artifact static read path

#### Scenario: Missing referenced file fails inspection
- **WHEN** manifest-declared reference data points to a missing copied file
- **THEN** artifact inspection MUST fail with an actionable diagnostic
