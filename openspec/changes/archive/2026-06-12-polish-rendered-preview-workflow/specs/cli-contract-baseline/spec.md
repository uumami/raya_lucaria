## ADDED Requirements

### Requirement: Preview command
The CLI SHALL provide `raya preview <course>` to validate, build, and locally serve the generated static course artifact from an explicit course path without executing course code.

#### Scenario: Preview explicit course path
- **WHEN** a user runs `raya preview <course>` against a valid source course
- **THEN** the CLI MUST validate the course, build the configured artifact, serve the generated `artifact/site/` directory through a local static HTTP server, and print the local entrypoint URL

#### Scenario: Preview reports useful URLs
- **WHEN** preview starts for a built artifact
- **THEN** the CLI MUST print the artifact path, the student-default entrypoint URL, and the inspection URL when `_raya/inspect/index.html` exists

#### Scenario: Preview remains static
- **WHEN** a user runs `raya preview <course>`
- **THEN** the CLI MUST NOT execute scripts, notebooks, kernels, `raya run`, `raya outputs freeze`, Docker execution, package installers, cache refreshes, or runtime profiles

#### Scenario: Preview uses explicit networking defaults
- **WHEN** preview serves a generated site
- **THEN** the CLI MUST bind to an explicit local host and port selection and report the resolved address instead of relying on hidden global state

#### Scenario: Preview failure exits nonzero
- **WHEN** preview validation, build, artifact discovery, or static serving setup fails
- **THEN** the CLI MUST exit nonzero and print actionable diagnostics tied to concrete source, artifact, host, or port information

#### Scenario: Preview dry run
- **WHEN** a user runs `raya preview <course> --dry-run`
- **THEN** the CLI MUST report the validation/build/serve plan and resolved artifact paths without starting a server or executing course targets
