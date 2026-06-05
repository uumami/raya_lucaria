# artifact-inspection-command Specification

## Purpose
Defines the read-only artifact inspection command and diagnostics used to validate built course artifacts without rebuilding source courses.
## Requirements
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

### Requirement: Inspect runtime and cache metadata
Artifact inspection SHALL validate manifest-declared runtime, execution-plan, and cache metadata without executing targets or resolving environments.

#### Scenario: Runtime metadata validates
- **WHEN** artifact inspection finds manifest-declared runtime profile data
- **THEN** it MUST validate that data against the accepted runtime metadata schema

#### Scenario: Execution plan metadata validates
- **WHEN** artifact inspection finds manifest-declared execution plan data
- **THEN** it MUST validate policy values, target references, runtime profile references, and not-executed status fields against the accepted execution metadata schema

#### Scenario: Cache metadata validates
- **WHEN** artifact inspection finds manifest-declared cache metadata
- **THEN** it MUST validate cache-key records and declared hash fields against the accepted cache metadata schema

#### Scenario: Inspection remains non-executing
- **WHEN** artifact inspection validates runtime, execution, or cache metadata
- **THEN** it MUST NOT call `uv`, Docker, kernels, package installers, remote runners, or executable source files

### Requirement: Inspect local execution results
Artifact inspection SHALL validate generated local execution result metadata and referenced generated files without re-executing targets.

#### Scenario: Result metadata validates
- **WHEN** artifact inspection finds manifest-declared local execution result data
- **THEN** it MUST validate that data against the accepted execution result schema

#### Scenario: Output and log files exist
- **WHEN** execution result metadata declares generated output or log paths
- **THEN** artifact inspection MUST verify those files exist under the artifact root

#### Scenario: Inspection does not re-execute
- **WHEN** artifact inspection validates execution results
- **THEN** it MUST NOT run scripts, notebooks, kernels, `uv`, Docker, package installers, or cache refreshes
