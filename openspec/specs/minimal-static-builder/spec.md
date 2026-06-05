# minimal-static-builder Specification

## Purpose
Defines the first Glintstone static builder behavior for readable HTML, navigation, artifact data indexes, assets, and deployment-neutral output.
## Requirements
### Requirement: Glintstone static builder package
The repository SHALL provide a minimal Glintstone builder implementation under the plain package path `packages/static`.

#### Scenario: Builder package exists
- **WHEN** dependencies are synced through Docker or local `uv`
- **THEN** the static builder package MUST be importable by the CLI without requiring a backend, JavaScript framework, or hosted service

### Requirement: Source course build
The minimal builder SHALL build a validated source course into the artifact output directory declared by `raya.yaml`.

#### Scenario: Build canonical source fixture
- **WHEN** `raya build examples/courses/minimal` runs against a fixture using `source: course`
- **THEN** it MUST create the configured artifact directory with `site/`, `manifest.json`, `data/`, and `assets/`

#### Scenario: Validation before build
- **WHEN** source course validation fails
- **THEN** the builder MUST stop before writing a successful artifact and report validation diagnostics

### Requirement: Static HTML output
The minimal builder SHALL render readable static HTML pages from source Markdown content, including the accepted rich static rendering baseline.

#### Scenario: Render content pages
- **WHEN** a course contains Markdown files under the configured authored source root
- **THEN** the generated `site/` directory MUST contain corresponding `.html` pages with escaped readable content, document titles, navigation links, rich static Markdown structures, and no backend dependency

#### Scenario: Static internal links
- **WHEN** generated pages link to other generated pages
- **THEN** links MUST use static relative HTML paths rather than requiring a router or dynamic service

#### Scenario: Rich page shell preserves generated surfaces
- **WHEN** a rich-rendered page also has breadcrumbs, previous/next links, generated local indexes, master indexes, stable links, local assets, or official study counts
- **THEN** the builder MUST preserve those existing generated surfaces while rendering the richer page body

### Requirement: Artifact data indexes
The minimal builder SHALL generate manifest-declared page, quanta, link, navigation, generated index, and official learning-object indexes.

#### Scenario: Generated indexes validate
- **WHEN** the generated artifact is inspected
- **THEN** `manifest.json`, `data/pages.json`, `data/quanta.json`, `data/links.json`, `data/navigation.json`, `data/indices.json`, and `data/official.json` MUST validate against the baseline artifact schemas

### Requirement: Official study seed export
The minimal builder SHALL export official learning objects from source-root and quantum-colocated `_official/` locations as static study seed data while preserving authority and scope.

#### Scenario: Colocated official objects indexed
- **WHEN** source official cards, quizzes, or prompts exist under `_official/`
- **THEN** `data/official.json` MUST include them with stable IDs, object types, official authority labels, inferred or explicit learning-quantum scope, source paths, and content payloads

#### Scenario: Personal state excluded
- **WHEN** official learning objects are exported
- **THEN** generated artifact data MUST NOT include private review history, confidence ratings, personal mastery state, or spaced repetition history

### Requirement: Asset copying
The minimal builder SHALL copy local course assets into the artifact assets directory when source assets exist.

#### Scenario: Copy colocated assets
- **WHEN** a source course contains referenced files under `_assets/` inside the authored source tree
- **THEN** the generated artifact MUST copy those files into artifact assets and browser-facing static assets without rendering the `_assets/` directory as course pages

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

#### Scenario: Referenced colocated asset copied for static site
- **WHEN** a source Markdown page references an existing colocated `_assets/` file
- **THEN** the generated artifact MUST contain that asset under `site/_raya/assets/` with a collision-safe path and a deployment-neutral rendered URL

#### Scenario: Existing artifact asset copy preserved
- **WHEN** a source course contains referenced colocated `_assets/`
- **THEN** the generated artifact MUST continue to expose copied assets under artifact-level `assets/`

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

### Requirement: Ordered navigation rendering
The minimal builder SHALL render static navigation from the resolved ordered content tree.

#### Scenario: Ordered pages render clean URLs
- **WHEN** a source page such as `course/1_foundations/2_derivatives.md` is built
- **THEN** the rendered static page MUST use a clean URL derived from stripped path segments and MUST NOT expose order prefixes as URL identity

#### Scenario: Breadcrumb and sequence navigation render
- **WHEN** a rendered page has resolved parent, previous, or next entries
- **THEN** the static page MUST expose usable breadcrumb and previous/next navigation without requiring a backend or client-side router

### Requirement: Generated index rendering
The minimal builder SHALL render generated local and master index sections from resolved source metadata and official study-object scopes.

#### Scenario: Local index rendered
- **WHEN** a section landing page has rendered child pages
- **THEN** the static section page MUST include generated child index entries with labels, titles, summaries, and links in resolved order

#### Scenario: Master index rendered
- **WHEN** the root course index is built
- **THEN** the static root page MUST include generated master index entries for main ordered sections and appendices

#### Scenario: Study counts rendered without personal state
- **WHEN** official cards, quizzes, or prompts are scoped to rendered quanta
- **THEN** generated index data MUST expose official study-object counts for rendered quanta and MUST NOT include private review history, confidence ratings, personal mastery state, or spaced repetition history

### Requirement: Stable reference rendering
The minimal builder SHALL render validated `raya:` stable source references as static links to current generated page URLs.

#### Scenario: Stable content link rendered
- **WHEN** source Markdown links to a valid `raya:` page ID
- **THEN** the generated HTML MUST link to the current static URL for that page using a deployment-neutral relative path

#### Scenario: Stable alias link rendered
- **WHEN** source Markdown links to a valid alias declared by a rendered page
- **THEN** the generated HTML MUST link to the current static URL for the page that owns the alias

### Requirement: Rich render fixture builds
The minimal builder SHALL build a representative rich rendering fixture that exercises the accepted static rendering baseline.

#### Scenario: Rich render fixture output
- **WHEN** `raya build` runs against the representative rich rendering fixture
- **THEN** the generated HTML MUST contain examples of headings, lists, links, code blocks, math, tables, callouts, footnotes, heading anchors, and a page table of contents

#### Scenario: Rich render fixture remains fixture material
- **WHEN** contributors inspect rich rendering fixture source or output
- **THEN** it MUST be labeled as fixture material and MUST point to `docs/foundation/` for authority

