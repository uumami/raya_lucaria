# minimal-static-builder Specification

## Purpose
TBD - created by archiving change add-minimal-static-artifact-builder. Update Purpose after archive.
## Requirements
### Requirement: Glintstone static builder package
The repository SHALL provide a minimal Glintstone builder implementation under the plain package path `packages/static`.

#### Scenario: Builder package exists
- **WHEN** dependencies are synced through Docker or local `uv`
- **THEN** the static builder package MUST be importable by the CLI without requiring a backend, JavaScript framework, or hosted service

### Requirement: Source course build
The minimal builder SHALL build a validated source course into the artifact output directory declared by `raya.yaml`.

#### Scenario: Build minimal fixture
- **WHEN** `raya build examples/courses/minimal` runs against the minimal fixture
- **THEN** it MUST create the configured artifact directory with `site/`, `manifest.json`, `data/`, and `assets/`

#### Scenario: Validation before build
- **WHEN** source course validation fails
- **THEN** the builder MUST stop before writing a successful artifact and report validation diagnostics

### Requirement: Static HTML output
The minimal builder SHALL render readable static HTML pages from source Markdown content.

#### Scenario: Render content pages
- **WHEN** a course contains Markdown files under the configured content directory
- **THEN** the generated `site/` directory MUST contain corresponding `.html` pages with escaped readable content, document titles, navigation links, and no backend dependency

#### Scenario: Static internal links
- **WHEN** generated pages link to other generated pages
- **THEN** links MUST use static relative HTML paths rather than requiring a router or dynamic service

### Requirement: Artifact data indexes
The minimal builder SHALL generate manifest-declared page, quanta, link, and official learning-object indexes.

#### Scenario: Generated indexes validate
- **WHEN** the generated artifact is inspected
- **THEN** `manifest.json`, `data/pages.json`, `data/quanta.json`, `data/links.json`, and `data/official.json` MUST validate against the baseline artifact schemas

### Requirement: Official study seed export
The minimal builder SHALL export official learning objects as static study seed data while preserving authority and scope.

#### Scenario: Official objects indexed
- **WHEN** source official cards, quizzes, or prompts exist
- **THEN** `data/official.json` MUST include them with stable IDs, object types, official authority labels, learning-quantum scope, and content payloads

#### Scenario: Personal state excluded
- **WHEN** official learning objects are exported
- **THEN** generated artifact data MUST NOT include private review history, confidence ratings, personal mastery state, or spaced repetition history

### Requirement: Asset copying
The minimal builder SHALL copy local course assets into the artifact assets directory when source assets exist.

#### Scenario: Copy local assets
- **WHEN** a source course contains files under the configured or default assets directory
- **THEN** the generated artifact MUST copy those files under `assets/` without treating them as canonical source truth

### Requirement: Deterministic rebuild surface
The minimal builder SHALL make generated artifacts rebuildable from source course truth.

#### Scenario: Rebuild replaces generated output
- **WHEN** `raya build <course>` runs again for the same source course
- **THEN** the builder MUST replace stale generated `site/`, `data/`, `manifest.json`, and copied assets output for that artifact directory

### Requirement: Source content links in artifact index
The minimal builder SHALL include valid source content links in the generated link index.

#### Scenario: Content link exported
- **WHEN** a source Markdown page links to another valid source Markdown page
- **THEN** `data/links.json` MUST include a link entry from the source page quantum to the target page quantum with kind `content`

#### Scenario: Build stops on broken source links
- **WHEN** source validation fails because of a broken content link or missing local asset
- **THEN** the builder MUST stop before writing a successful artifact

### Requirement: Static read-path asset copying
The minimal builder SHALL copy browser-facing local course assets into the generated static read path.

#### Scenario: Referenced asset copied for static site
- **WHEN** a source Markdown page references an existing local asset
- **THEN** the generated artifact MUST contain that asset under `site/_raya/assets/` with its source asset relative path preserved

#### Scenario: Existing artifact asset copy preserved
- **WHEN** a source course contains files under the configured or default assets directory
- **THEN** the generated artifact MUST continue to copy those files under artifact-level `assets/`

### Requirement: Rendered local asset URLs
The minimal builder SHALL rewrite rendered local asset references to deployment-neutral relative URLs.

#### Scenario: Root page rendered asset URL
- **WHEN** a root content page links to a local source asset
- **THEN** the generated HTML link MUST point to the copied asset under `_raya/assets/` using a relative URL

#### Scenario: Nested page rendered asset URL
- **WHEN** a nested content page links to a local source asset
- **THEN** the generated HTML link MUST point to the copied asset under `site/_raya/assets/` using a relative URL from the nested page

#### Scenario: External links are not rewritten
- **WHEN** a Markdown page links to an external URL, `mailto:`, `tel:`, or fragment-only target
- **THEN** the rendered link target MUST NOT be rewritten as a local asset URL

### Requirement: Build output remains deployment-neutral
The minimal builder SHALL avoid deployment-root assumptions in generated browser URLs.

#### Scenario: No absolute deployment root for local resources
- **WHEN** generated HTML references another generated page or local asset
- **THEN** the generated URL MUST be relative and MUST NOT require an absolute `/` root, configured host, backend route, or CDN

