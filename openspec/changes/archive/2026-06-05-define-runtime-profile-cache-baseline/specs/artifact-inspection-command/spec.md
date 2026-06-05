## ADDED Requirements

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
