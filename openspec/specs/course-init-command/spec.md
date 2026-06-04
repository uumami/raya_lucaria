# course-init-command Specification

## Purpose
Defines the CLI workflow for creating replaceable source course scaffolds without overwriting existing work or defining course canon by accident.
## Requirements
### Requirement: Course init command
The system SHALL provide a CLI workflow for creating a minimal source course tree from an explicit target path.

#### Scenario: Initialize new course
- **WHEN** a user runs `raya course init <path>` against a missing or empty directory
- **THEN** the command MUST create `raya.yaml`, `course/0_index.md`, `course/_official/`, `course/_assets/`, and the generated-output target directory convention without requiring separate top-level `content/`, `official/`, or `assets/` source roots

### Requirement: Initialized course validates
Initialized courses SHALL satisfy the baseline source course contract.

#### Scenario: Validate initialized course
- **WHEN** `raya validate <path>` runs after `raya course init <path>`
- **THEN** validation MUST exit successfully and report the generated course files read

### Requirement: Initialized course builds and inspects
Initialized courses SHALL work with the baseline build and artifact inspection loop.

#### Scenario: Build and inspect initialized course
- **WHEN** a user runs `raya build <path>` and then `raya artifacts inspect <path>/artifact` after course init
- **THEN** the artifact MUST build and inspect successfully

### Requirement: Safe target handling
Course init SHALL NOT overwrite existing non-empty directories by default.

#### Scenario: Non-empty target refused
- **WHEN** a user runs `raya course init <path>` against a directory containing existing files
- **THEN** the command MUST fail nonzero with an actionable diagnostic

### Requirement: Minimal scaffold language
Course init SHALL keep generated starter content minimal and replaceable.

#### Scenario: Generated content is scaffold
- **WHEN** initialized content is inspected
- **THEN** starter text MUST be labeled as replaceable scaffold and MUST NOT define required pedagogy, architecture, or official course canon

### Requirement: Initialized ordered scaffold
Course init SHALL create starter source content that follows the blessed ordered source convention without defining course canon by accident.

#### Scenario: Root index metadata created
- **WHEN** `raya course init <path>` creates starter content
- **THEN** `course/0_index.md` MUST include minimal frontmatter needed for a published root index and starter prose labeled as replaceable scaffold

#### Scenario: Scaffold uses canonical prefix style
- **WHEN** `raya course init <path>` creates ordered starter files or directories beyond the root index
- **THEN** those entries MUST use the canonical unpadded prefix style such as `1_` and `2_`

#### Scenario: Scaffold uses source field
- **WHEN** `raya course init <path>` creates `raya.yaml`
- **THEN** the configuration MUST use `source: course` as the canonical authored source root

#### Scenario: Scaffold support dirs remain private
- **WHEN** initialized support directories such as `course/_official/` or `course/_assets/` are inspected
- **THEN** they MUST be clearly private source support directories and MUST NOT define rendered navigation by their existence

