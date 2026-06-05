## ADDED Requirements

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
