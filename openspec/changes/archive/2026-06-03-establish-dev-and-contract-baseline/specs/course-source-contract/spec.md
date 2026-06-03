## ADDED Requirements

### Requirement: Minimal source course shape
A source course SHALL use `raya.yaml`, `content/`, optional `assets/`, and optional `official/` as the baseline file-tree contract.

#### Scenario: Valid minimal tree
- **WHEN** a course contains `raya.yaml` and a readable `content/` directory
- **THEN** the course source contract validation MUST recognize it as a candidate source course

#### Scenario: Missing content directory
- **WHEN** `raya.yaml` points to a missing content directory
- **THEN** validation MUST fail with an actionable diagnostic

### Requirement: Course configuration
`raya.yaml` SHALL declare stable course identity, human-readable metadata, source locations, and artifact output location.

#### Scenario: Required configuration fields
- **WHEN** `raya.yaml` is validated
- **THEN** it MUST require `course_id`, title, description, language, content directory, and artifact output directory

#### Scenario: Invalid configuration field
- **WHEN** a required configuration field has the wrong type or an invalid value
- **THEN** validation MUST fail and name the field

### Requirement: Content files
Course content SHALL be readable Markdown files under the configured `content/` directory.

#### Scenario: Readable Markdown
- **WHEN** validation scans the configured content directory
- **THEN** it MUST parse readable Markdown files and any supported frontmatter

#### Scenario: Broken frontmatter
- **WHEN** a content file contains unreadable frontmatter
- **THEN** validation MUST fail and identify the file

### Requirement: Learning quanta
Directories and pages SHALL be treated as learning quanta that can define navigation, graph, study, authority, and export scope.

#### Scenario: Path-derived identity
- **WHEN** a page has no explicit quantum metadata
- **THEN** validation MUST derive a candidate quantum identity from `course_id` and content path

#### Scenario: Duplicate explicit quantum identity
- **WHEN** two quanta declare the same explicit stable ID
- **THEN** validation MUST fail and identify both declarations

### Requirement: Minimal fixture course
The repository SHALL include a minimal fixture course that exercises the source course contract without defining pedagogy by accident.

#### Scenario: Fixture validation target
- **WHEN** `raya validate examples/courses/minimal` runs
- **THEN** the fixture MUST validate against the baseline source course contract

#### Scenario: Fixture remains minimal
- **WHEN** examples are added to the minimal fixture
- **THEN** they MUST remain labeled as fixture data and not as required pedagogy or architecture

### Requirement: Legacy source names excluded
The baseline source course contract SHALL NOT require old legacy source directory or configuration names.

#### Scenario: Legacy names are not required
- **WHEN** a course uses `raya.yaml` and `content/`
- **THEN** validation MUST NOT require old legacy names such as previous source directory or configuration filenames
