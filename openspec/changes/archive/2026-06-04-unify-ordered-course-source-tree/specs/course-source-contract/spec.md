## MODIFIED Requirements

### Requirement: Minimal source course shape
A source course SHALL use `raya.yaml`, `source: course`, one authored `course/` tree, private support directories, and generated artifact output as the baseline file-tree contract.

#### Scenario: Valid canonical tree
- **WHEN** a course contains `raya.yaml` with `source: course` and a readable `course/` directory
- **THEN** course source validation MUST recognize it as the canonical source-course shape

#### Scenario: Content field is unsupported
- **WHEN** a course contains `raya.yaml` with a source `content` field
- **THEN** course source validation MUST fail with an actionable diagnostic telling the author to use `source: course`

#### Scenario: Missing source directory
- **WHEN** `raya.yaml` points `source` to a missing directory
- **THEN** validation MUST fail with an actionable diagnostic

#### Scenario: Root source assets field is unsupported
- **WHEN** a course contains `raya.yaml` with a root authored `assets` field
- **THEN** course source validation MUST fail with an actionable diagnostic telling the author to put source assets under `course/_assets/`

### Requirement: Course configuration
`raya.yaml` SHALL declare stable course identity, human-readable metadata, source locations, and artifact output location.

#### Scenario: Required configuration fields
- **WHEN** `raya.yaml` is validated for a new canonical course
- **THEN** it MUST require `course_id`, title, description, language, authored source root, and artifact output directory

#### Scenario: Invalid configuration field
- **WHEN** a required configuration field has the wrong type or an invalid value
- **THEN** validation MUST fail and name the field

### Requirement: Content files
Course content SHALL be readable Markdown files under the configured authored source root.

#### Scenario: Readable Markdown
- **WHEN** validation scans the configured authored source root
- **THEN** it MUST parse readable Markdown files and any supported frontmatter

#### Scenario: Broken frontmatter
- **WHEN** a content file contains unreadable frontmatter
- **THEN** validation MUST fail and identify the file

### Requirement: CLI-initialized source course
Courses created by the CLI init workflow SHALL satisfy the baseline source course contract without depending on legacy names or renderer assumptions.

#### Scenario: Initialized source shape
- **WHEN** a course is created by `raya course init <path>`
- **THEN** it MUST use `raya.yaml`, `source: course`, `course/`, private support directory conventions, and generated `artifact/` output according to the current source contract

#### Scenario: Initialized source is not canonical pedagogy
- **WHEN** generated starter content is read
- **THEN** it MUST be clear that the content is replaceable scaffold and not required pedagogy or architecture

### Requirement: Ordered content tree
Source courses SHALL use ordered source-tree conventions for rendered material while allowing private, draft, official, asset, and partial material to remain unrendered.

#### Scenario: Ordered content entries validated
- **WHEN** validation scans the configured authored source root
- **THEN** it MUST classify rendered numeric entries, rendered appendix entries, section landing pages, private paths, draft paths, `_official/`, `_assets/`, partial paths, and invalid unordered files

#### Scenario: Invalid ordered tree fails
- **WHEN** validation finds duplicate normalized order values, mixed main prefix widths in one sibling set, missing section landing pages, duplicate clean slugs, or unordered published Markdown files
- **THEN** validation MUST fail with actionable diagnostics

## ADDED Requirements

### Requirement: Unified authored source tree
The authored source tree SHALL organize rendered pages and non-rendered support material under the learning quanta they belong to.

#### Scenario: Support directories do not render
- **WHEN** `_official/`, `_assets/`, `_drafts/`, `drafts/`, or `_partials/` exists under the authored source root
- **THEN** validation MUST treat those directories as source support material and MUST NOT include them in rendered navigation, generated local indexes, or master indexes

#### Scenario: Quantum support uses directory page
- **WHEN** a learning quantum owns `_official/` or `_assets/` support material
- **THEN** that quantum MUST be represented as a rendered directory with a normalized zero index page such as `0_index.md`

#### Scenario: File page remains valid without support
- **WHEN** a rendered file page such as `1_topic.md` has no child support directories
- **THEN** validation MUST continue to accept it as a rendered page
