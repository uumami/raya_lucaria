# reviewed-execution-output-baseline Specification

## Purpose
Defines reviewed execution outputs as source-controlled frozen support: how generated results become reviewed source support, how freshness is validated, how artifacts expose reviewed files, and how static rendering distinguishes reviewed output from generated or personal work.

## Requirements
### Requirement: Reviewed output source support
Raya Lucaria SHALL represent reviewed execution outputs as source-controlled, private support material colocated with the learning quantum that owns the executable target.

#### Scenario: Reviewed output directory is private
- **WHEN** a course contains `_reviewed/` under a rendered quantum or accepted ancestor
- **THEN** validation and build MUST treat it as private source support rather than rendered page content, navigation, generated index entries, official objects, or ordinary assets

#### Scenario: Reviewed output manifest exists
- **WHEN** a target has reviewed output
- **THEN** the reviewed source support MUST include a manifest naming the target/reference ID, source path, runtime profile, policy, cache key or equivalent freshness key, reviewed output files, and freshness hashes needed for validation

#### Scenario: Reviewed files stay source support
- **WHEN** reviewed output files are stored under `_reviewed/`
- **THEN** they MUST be treated as reviewed source support and MUST NOT overwrite authored code, notebooks, pages, assets, or official learning objects

### Requirement: Output listing command
The CLI SHALL provide a non-executing output listing command for exploring generated and reviewed execution outputs.

#### Scenario: List outputs
- **WHEN** a user runs `raya outputs list <course>`
- **THEN** the CLI MUST report executable targets, generated result availability, reviewed output availability, frozen status, staleness, and relevant output paths without executing targets

#### Scenario: List missing artifact
- **WHEN** output listing runs before a generated artifact exists
- **THEN** it MUST still report source/runtime/reviewed-output state where available and MUST NOT build or execute implicitly

### Requirement: Freeze generated result
The CLI SHALL provide an explicit freeze command that promotes the latest successful generated execution result into reviewed source support for human source review.

#### Scenario: Freeze successful result
- **WHEN** a user runs `raya outputs freeze <course> <target>` for a target with a successful current generated execution result
- **THEN** the CLI MUST copy the reviewed output files into colocated `_reviewed/` source support, write reviewed output metadata, report outputs written, and exit successfully without executing the target

#### Scenario: Freeze refuses failed result
- **WHEN** the latest generated execution result for a target failed or is missing
- **THEN** the freeze command MUST fail with an actionable diagnostic and MUST NOT create reviewed source support

#### Scenario: Freeze refuses stale result
- **WHEN** a generated execution result does not match the current source, runtime profile, lockfile, cache key, or declared freshness metadata
- **THEN** the freeze command MUST fail and tell the user to rerun the explicit target before freezing

### Requirement: Reviewed output freshness
Reviewed execution outputs SHALL validate against current source, runtime, cache, and reviewed file metadata before they can be treated as current.

#### Scenario: Current reviewed output validates
- **WHEN** a reviewed output manifest matches the current executable target, source hash, runtime profile hash, lockfile hash when present, declared input hashes, cache key, and reviewed file hashes
- **THEN** validation MUST treat the reviewed output as current

#### Scenario: Stale reviewed output fails validation
- **WHEN** reviewed output metadata no longer matches current source, runtime, inputs, lockfile, cache key, or reviewed files
- **THEN** validation MUST fail with an actionable diagnostic naming the stale target and the field or file that changed

#### Scenario: Reviewed output validation does not execute
- **WHEN** validation checks reviewed output freshness
- **THEN** it MUST NOT run scripts, notebooks, kernels, `uv`, Docker, package installers, or cache refreshes

### Requirement: Reviewed output artifact data
Glintstone SHALL expose reviewed execution outputs through manifest-declared artifact data and copied file surfaces.

#### Scenario: Reviewed output data generated
- **WHEN** a course contains current reviewed output
- **THEN** the generated artifact MUST include manifest-declared reviewed output data with target ID, source path, runtime profile, freshness key, reviewed status, output file paths, and browser file paths

#### Scenario: Reviewed files copied
- **WHEN** reviewed output files are declared by current reviewed output metadata
- **THEN** the builder MUST copy them to artifact-level reviewed file storage and browser-facing static reviewed file storage

#### Scenario: Reviewed output remains data-backed
- **WHEN** agents, launchers, graph tools, or future renderers need reviewed output metadata
- **THEN** they MUST read manifest-declared reviewed output data rather than scraping rendered HTML

### Requirement: Static reviewed output visualization
Glintstone SHALL render compact reviewed-output status for referenced targets with current reviewed outputs while keeping rendered HTML non-authoritative.

#### Scenario: Reviewed output panel renders
- **WHEN** a rendered page references a script or notebook target with current reviewed output
- **THEN** the generated page MUST include a compact reviewed-output panel with status, target, profile, freshness label or key, and deployment-neutral links or excerpts for reviewed output files

#### Scenario: No stale reviewed output renders
- **WHEN** reviewed output is stale or invalid
- **THEN** build MUST fail before publishing a static page that presents the stale output as reviewed

#### Scenario: Static serving remains passive
- **WHEN** `artifact/site/` is served directly
- **THEN** reviewed-output panels and linked reviewed files MUST work as static files without execution services

### Requirement: Reviewed output authority
Reviewed execution output SHALL be distinguishable from authored source, generated run results, official learning objects, and personal student work.

#### Scenario: Authority label present
- **WHEN** reviewed output metadata is generated or rendered
- **THEN** it MUST identify the output as reviewed course support rather than generated-only output or personal student work

#### Scenario: Generated results not automatically reviewed
- **WHEN** `raya run` writes a successful generated execution result
- **THEN** that result MUST NOT be treated as reviewed output until an explicit freeze/review source-support step records it
