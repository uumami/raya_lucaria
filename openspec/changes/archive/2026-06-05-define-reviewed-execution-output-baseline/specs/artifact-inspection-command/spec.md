## ADDED Requirements

### Requirement: Inspect reviewed execution outputs
Artifact inspection SHALL validate manifest-declared reviewed output metadata and copied reviewed files without executing targets.

#### Scenario: Reviewed output data validates
- **WHEN** artifact inspection finds manifest-declared reviewed output data
- **THEN** it MUST validate that data against the accepted reviewed output schema

#### Scenario: Reviewed output files exist
- **WHEN** reviewed output data declares artifact-level or browser-facing files
- **THEN** artifact inspection MUST verify those files exist under the artifact root or static read path as declared

#### Scenario: Inspection does not validate by execution
- **WHEN** artifact inspection validates reviewed output metadata
- **THEN** it MUST NOT run scripts, notebooks, kernels, `uv`, Docker, package installers, or cache refreshes
