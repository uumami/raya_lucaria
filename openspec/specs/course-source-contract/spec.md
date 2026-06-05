# course-source-contract Specification

## Purpose
Defines the baseline source course tree, `raya.yaml` configuration, content rules, learning quanta, fixtures, and validation behavior.
## Requirements
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

### Requirement: Learning quanta
Directories and pages SHALL be treated as learning quanta that can define navigation, graph, study, authority, and export scope.

#### Scenario: Path-derived draft identity
- **WHEN** a draft, private, or non-published page has no explicit quantum metadata
- **THEN** validation MUST derive a candidate quantum identity from `course_id` and content path for diagnostics without treating it as a stable published reference

#### Scenario: Published page stable identity
- **WHEN** a rendered published page or section landing page is validated
- **THEN** it MUST declare a globally unique stable ID through supported frontmatter

#### Scenario: Duplicate explicit quantum identity
- **WHEN** two quanta declare the same explicit stable ID
- **THEN** validation MUST fail and identify both declarations

#### Scenario: Directory quantum from index page
- **WHEN** a rendered source directory participates in navigation
- **THEN** validation MUST treat its normalized zero index page as the metadata and content source for the directory quantum

### Requirement: Minimal fixture course
The repository SHALL include a minimal fixture course that exercises the source course contract without defining pedagogy by accident.

#### Scenario: Fixture validation target
- **WHEN** `raya validate examples/courses/minimal` runs
- **THEN** the fixture MUST validate against the baseline source course contract

#### Scenario: Fixture remains minimal
- **WHEN** examples are added to the minimal fixture
- **THEN** they MUST remain labeled as fixture data and not as required pedagogy or architecture

### Requirement: Old source names excluded
The baseline source course contract SHALL NOT require old source directory or configuration names.

#### Scenario: Old names are not required
- **WHEN** a course uses `raya.yaml`, `source: course`, and `course/`
- **THEN** validation MUST NOT require old names such as previous source directory or configuration filenames

### Requirement: CLI-initialized source course
Courses created by the CLI init workflow SHALL satisfy the baseline source course contract without depending on legacy names or renderer assumptions.

#### Scenario: Initialized source shape
- **WHEN** a course is created by `raya course init <path>`
- **THEN** it MUST use `raya.yaml`, `source: course`, `course/`, private support directory conventions, and generated `artifact/` output according to the current source contract

#### Scenario: Initialized source is not canonical pedagogy
- **WHEN** generated starter content is read
- **THEN** it MUST be clear that the content is replaceable scaffold and not required pedagogy or architecture

### Requirement: Source links and assets validate before build
The source course contract SHALL require local content links and local asset references to validate before build.

#### Scenario: Broken local source reference
- **WHEN** course validation scans Markdown content and finds a broken local `.md` link or missing local asset reference
- **THEN** validation MUST fail before the course can build successfully

#### Scenario: External source reference
- **WHEN** course validation scans Markdown content and finds an external URL or fragment-only link
- **THEN** validation MUST NOT require that link to exist as a local source file

### Requirement: Ordered content tree
Source courses SHALL use ordered source-tree conventions for rendered material while allowing private, draft, official, asset, and partial material to remain unrendered.

#### Scenario: Ordered content entries validated
- **WHEN** validation scans the configured authored source root
- **THEN** it MUST classify rendered numeric entries, rendered appendix entries, section landing pages, private paths, draft paths, `_official/`, `_assets/`, partial paths, and invalid unordered files

#### Scenario: Invalid ordered tree fails
- **WHEN** validation finds duplicate normalized order values, mixed main prefix widths in one sibling set, missing section landing pages, duplicate clean slugs, or unordered published Markdown files
- **THEN** validation MUST fail with actionable diagnostics

### Requirement: Frontmatter metadata baseline
Course content SHALL use supported YAML frontmatter metadata for stable identity and generated index previews.

#### Scenario: Metadata parsed
- **WHEN** validation scans Markdown content with supported YAML frontmatter
- **THEN** it MUST parse supported metadata fields needed for stable identity, title, navigation label, summary, status, estimated time, tags, prerequisites, and aliases

#### Scenario: Broken metadata fails
- **WHEN** a rendered page declares malformed frontmatter or unsupported values for required metadata fields
- **THEN** validation MUST fail and identify the file and field

### Requirement: Configured hierarchy labels
Course configuration SHALL support optional hierarchy labels for rendered navigation without changing source containment or order.

#### Scenario: Hierarchy labels configured
- **WHEN** `raya.yaml` declares hierarchy labels
- **THEN** validation MUST accept those labels and make them available to build and artifact generation

#### Scenario: Hierarchy labels absent
- **WHEN** `raya.yaml` omits hierarchy labels
- **THEN** validation MUST use default labels and MUST NOT require directory-level metadata to infer hierarchy

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

### Requirement: Code and notebook support directories
The source course contract SHALL support `code/` and `notebooks/` directories as authored support material owned by rendered learning quanta.

#### Scenario: Quantum-owned code directory
- **WHEN** a rendered quantum directory contains `code/`
- **THEN** validation MUST treat files under `code/` as source support material for that quantum rather than rendered content

#### Scenario: Quantum-owned notebook directory
- **WHEN** a rendered quantum directory contains `notebooks/`
- **THEN** validation MUST treat files under `notebooks/` as source support material for that quantum rather than rendered content

#### Scenario: Support owner has index page
- **WHEN** `code/` or `notebooks/` is added under a learning quantum directory
- **THEN** that quantum MUST be represented by a normalized zero index page such as `0_index.md`

#### Scenario: Root source code unsupported
- **WHEN** a course declares a root authored `code` or `notebooks` configuration field
- **THEN** validation MUST fail or ignore it according to the source-course contract and tell authors to colocate support material under `course/`

### Requirement: Runtime support beside course source
The source course contract SHALL allow runtime support files beside the ordered authored `course/` tree without making those files course content.

#### Scenario: Runtime directory at course root
- **WHEN** a course includes a root-level `runtime/` directory
- **THEN** validation MUST treat it as private execution support metadata and MUST NOT render it as course content

#### Scenario: Python project files at course root
- **WHEN** a course includes root-level `pyproject.toml` or `uv.lock`
- **THEN** validation MUST treat those files as runtime support for reproducibility rather than course pages, assets, or official learning objects

#### Scenario: Runtime directory inside course source
- **WHEN** an ordered `course/` source tree contains a rendered page link into `runtime/` or another private runtime support path
- **THEN** validation MUST fail unless a future accepted contract explicitly exposes that path

#### Scenario: Runtime profile does not affect source order
- **WHEN** runtime profile metadata changes
- **THEN** source page order, generated navigation, stable page IDs, generated indexes, and official learning-object scope MUST remain derived from the ordered `course/` tree

