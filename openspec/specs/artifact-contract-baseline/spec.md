# artifact-contract-baseline Specification

## Purpose
TBD - created by archiving change establish-dev-and-contract-baseline. Update Purpose after archive.
## Requirements
### Requirement: Portable artifact shape
A course artifact SHALL contain a static read path, a manifest, generated data indexes, and copied or referenced local assets.

#### Scenario: Required artifact paths
- **WHEN** a baseline artifact is produced or inspected
- **THEN** it MUST contain `site/`, `manifest.json`, `data/`, and `assets/` according to the artifact contract

### Requirement: Manifest entrypoint
`manifest.json` SHALL be the backend-readable and agent-readable entrypoint for a course artifact.

#### Scenario: Manifest required fields
- **WHEN** an artifact manifest is validated
- **THEN** it MUST include artifact version, course ID, course version or content hash, generated timestamp, source schema version, static site root, and data index locations

#### Scenario: Services read manifest
- **WHEN** a future dynamic service needs artifact data
- **THEN** the artifact contract MUST require it to discover data through `manifest.json` instead of scraping rendered HTML as authority

### Requirement: Generated data indexes
Artifact data SHALL expose pages, quanta, links, and official learning objects as generated indexes.

#### Scenario: Data indexes present
- **WHEN** artifact data is validated
- **THEN** it MUST include page, quanta, link, and official learning-object indexes

#### Scenario: Rebuildable generated data
- **WHEN** generated data differs from source course truth
- **THEN** source course truth MUST be treated as canonical and generated data MUST be rebuildable

### Requirement: Official study seed data
Artifacts SHALL expose official learning objects as study seed data without embedding personal review or mastery state.

#### Scenario: Official index contains study seeds
- **WHEN** official cards, quizzes, or prompts exist in source
- **THEN** artifact data MUST expose them with official authority labels and learning-quantum scope

#### Scenario: Private state excluded
- **WHEN** artifact data is generated
- **THEN** it MUST NOT include private notes, review history, confidence ratings, or personal mastery state

### Requirement: Static usefulness
The baseline artifact contract SHALL preserve a useful static course path without accounts, network services, or dynamic JavaScript-heavy behavior.

#### Scenario: Static site can be served as files
- **WHEN** the artifact `site/` directory is served by static hosting
- **THEN** course pages, navigation, internal links, accessible HTML, and local assets MUST remain usable without a backend

### Requirement: Renderer independence
The artifact contract SHALL NOT depend on a specific static-site generator, JavaScript framework, CSS framework, or search tool.

#### Scenario: Renderer not part of contract
- **WHEN** a builder satisfies the artifact contract
- **THEN** validation MUST NOT require any specific renderer stack as part of the artifact contract

### Requirement: Builder-produced artifact validation
Artifacts produced by the minimal Glintstone builder SHALL satisfy the baseline artifact contract.

#### Scenario: Produced artifact shape
- **WHEN** `raya build <course>` completes successfully
- **THEN** the produced artifact MUST contain `site/`, `manifest.json`, `data/pages.json`, `data/quanta.json`, `data/links.json`, `data/official.json`, and `assets/`

#### Scenario: Produced artifact schemas
- **WHEN** the produced manifest and data indexes are validated
- **THEN** they MUST pass the artifact manifest, pages index, quanta index, links index, and official index schema validators

### Requirement: Static site output from builder
Builder-produced artifacts SHALL include static HTML that remains useful when served as files.

#### Scenario: Readable file-served pages
- **WHEN** the generated `site/` directory is opened through static hosting or local files
- **THEN** course pages, titles, readable content, and navigation links MUST be available without accounts, network services, or client-side routing

### Requirement: Inspectable artifact contract
Course artifacts SHALL be inspectable as standalone build products through their manifest and generated data indexes.

#### Scenario: Artifact inspected without source course
- **WHEN** an artifact directory is inspected after being copied away from its source course
- **THEN** inspection MUST validate the artifact using the artifact root, `manifest.json`, and manifest-declared data indexes rather than source course files

#### Scenario: Required paths inspected
- **WHEN** an artifact is inspected
- **THEN** inspection MUST confirm `site/`, `data/`, `assets/`, `manifest.json`, and manifest-declared data index files exist

### Requirement: Self-contained static read resources
The artifact static read path SHALL contain the browser-facing resources needed for generated pages to use local course assets without relying on sibling artifact directories.

#### Scenario: Static site served directly
- **WHEN** the generated `site/` directory is served directly by static hosting
- **THEN** rendered pages MUST resolve local course assets through paths contained under `site/`

#### Scenario: Static site opened locally
- **WHEN** a generated HTML page under `site/` is opened from a local filesystem path
- **THEN** rendered local asset links MUST resolve through relative file paths contained under `site/`

### Requirement: Artifact-level assets remain inspectable
The artifact contract SHALL preserve artifact-level copied assets as inspectable generated output while allowing browser-facing copies under the static read path.

#### Scenario: Artifact assets inspected
- **WHEN** an artifact containing source assets is inspected
- **THEN** inspection MUST continue to recognize the artifact-level `assets/` directory as part of the generated artifact shape

