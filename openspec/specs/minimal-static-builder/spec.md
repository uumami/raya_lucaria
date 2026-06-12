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

### Requirement: Static code and notebook reference output
The minimal static builder SHALL build validated code and notebook references into portable static artifacts without executing them and SHALL render default page summaries according to rendered-surface discipline.

#### Scenario: Code reference copied and linked
- **WHEN** a rendered page references a validated code file
- **THEN** the builder MUST copy the file to artifact-level file storage, copy it to `site/_raya/files/`, and rewrite the rendered link to a deployment-neutral browser path

#### Scenario: Notebook reference copied and linked
- **WHEN** a rendered page references a validated notebook file
- **THEN** the builder MUST copy the file to artifact-level file storage, copy it to `site/_raya/files/`, and rewrite the rendered link to a deployment-neutral browser path

#### Scenario: Reference panel rendered compactly
- **WHEN** a page has validated code or notebook references
- **THEN** the generated HTML MUST expose those references through a compact static resource panel or equivalent readable surface with kind, label, no-execution status, and deployment-neutral view/download links

#### Scenario: Reference internals stay out of default flow
- **WHEN** a page has validated code or notebook references
- **THEN** the default rendered page MUST NOT dump raw reference JSON, source hashes, artifact storage paths, browser storage paths, runtime profile internals, or cache keys into the main reading flow

#### Scenario: Preview does not execute
- **WHEN** a reference panel or preview is generated for code or notebook files
- **THEN** the builder MUST NOT execute scripts, notebook cells, kernels, or runtime commands

### Requirement: Student-default page shell
The minimal builder SHALL render ordinary course pages as student-default surfaces with readable visual hierarchy and compact generated support rather than exhaustive internal metadata displays.

#### Scenario: Page shell uses student defaults
- **WHEN** a course page is built
- **THEN** the generated HTML MUST prioritize title, authored content, breadcrumbs, navigation, generated indexes, local assets, and compact support panels

#### Scenario: Page shell avoids instructional clutter
- **WHEN** a student-default page is rendered
- **THEN** the generated page MUST avoid visible in-page explanations of internal renderer mechanics, testing behavior, fixture mechanics, keyboard shortcuts, or artifact implementation details unless that text is authored course content

#### Scenario: Page shell has stable layout regions
- **WHEN** a student-default page contains navigation, generated indexes, support panels, or reviewed-output summaries
- **THEN** the generated HTML and CSS MUST keep those regions visually distinct and responsive without overlapping authored content across representative desktop and mobile-sized viewports

#### Scenario: Runtime and execution metadata summarized
- **WHEN** a page has generated runtime, execution, or cache metadata associated with its referenced targets
- **THEN** the default page MUST show at most compact reader-relevant status and MUST keep verbose policy, profile, cache, hash, and path internals in artifact data or inspection surfaces

#### Scenario: Reviewed output summarized
- **WHEN** a page has current reviewed output associated with a referenced target
- **THEN** the default page MUST show a compact reviewed label, target label, and deployment-neutral links or short excerpts without dumping freshness internals into the main reading flow

#### Scenario: Machine data remains inspectable
- **WHEN** compact support panels are rendered
- **THEN** artifact inspection and manifest-declared data MUST continue to expose the complete accepted metadata for tools and audits

### Requirement: Static inspection and examples gallery output
The minimal builder or repository preview workflow SHALL provide static inspection or gallery output for contributors without requiring a dynamic service.

#### Scenario: Inspection pages generated from artifact data
- **WHEN** implementation generates inspection pages for a fixture or artifact
- **THEN** those pages MUST be derived from manifest-declared artifact data and MUST use deployment-neutral links to generated pages, referenced files, assets, and reviewed files

#### Scenario: Inspection pages remain audit surfaces
- **WHEN** an inspection page is generated
- **THEN** it MUST identify itself as an inspection surface and MUST NOT present audit metadata as student-default course canon

#### Scenario: Examples gallery links fixtures
- **WHEN** repository example fixtures are built
- **THEN** the repository MUST provide a static gallery or equivalent page linking to representative fixture entrypoints and naming the behavior each fixture demonstrates

#### Scenario: Examples gallery links inspection pages
- **WHEN** a representative fixture artifact has an inspection page
- **THEN** the examples gallery MUST provide a deployment-neutral link to that inspection page or document why the fixture has no inspection surface

#### Scenario: Gallery does not define pedagogy
- **WHEN** the examples gallery is rendered
- **THEN** it MUST label entries as fixture material and MUST NOT present fixture content as canonical pedagogy or architecture

#### Scenario: Gallery layout remains reviewable
- **WHEN** the examples gallery is served through local static hosting
- **THEN** its fixture labels, entrypoint links, inspection links, and authority notice MUST remain visible without text overlap across representative desktop and mobile-sized viewports

### Requirement: Code and notebook reference indexes
The minimal static builder SHALL generate machine-readable reference data when code or notebook references are present.

#### Scenario: References data emitted
- **WHEN** a build includes validated code or notebook references
- **THEN** the artifact MUST contain `data/references.json` or equivalent manifest-declared data for those references

#### Scenario: No references data omitted or empty
- **WHEN** a build has no code or notebook references
- **THEN** the artifact MUST either omit reference data from the manifest or emit an empty valid reference data file consistently

### Requirement: Static runtime metadata output
The minimal static builder SHALL emit runtime and execution metadata as generated artifact data without executing code or notebooks.

#### Scenario: Runtime profile metadata emitted
- **WHEN** a course declares valid runtime profiles
- **THEN** the builder MUST emit manifest-declared runtime metadata derived from `runtime/profiles.yaml` and related root runtime files

#### Scenario: Execution plan metadata emitted
- **WHEN** a course has code or notebook references with execution policy metadata
- **THEN** the builder MUST emit manifest-declared execution plan metadata with target IDs, policy, runtime profile when declared, and status `not-executed`

#### Scenario: Cache metadata emitted
- **WHEN** executable targets declare policy `cache`, `always`, or `frozen`
- **THEN** the builder MUST emit manifest-declared cache-key metadata without executing targets or refreshing outputs

#### Scenario: Static pages preserved
- **WHEN** runtime metadata is present
- **THEN** generated pages, deployment-neutral links, reference panels, assets, navigation, indexes, and static read paths MUST remain usable without runtime support

### Requirement: Runtime metadata indexes
The minimal static builder SHALL keep runtime, execution-plan, and cache metadata machine-readable and manifest-centered.

#### Scenario: Metadata data files validate
- **WHEN** the builder writes runtime, execution-plan, or cache metadata files
- **THEN** those files MUST pass the accepted artifact data validators during build

#### Scenario: No runtime metadata omitted or empty
- **WHEN** a course has no runtime profiles and no executable policy metadata beyond the Phase 2 default
- **THEN** the artifact MUST either omit runtime/cache metadata from the manifest or emit empty valid metadata files consistently

### Requirement: Local math render resources
The minimal static builder SHALL write MathJax-rendered math support resources
into the generated static read path with deployment-neutral local references.

#### Scenario: Math support CSS emitted locally
- **WHEN** a build includes pre-rendered MathJax output that requires support CSS
- **THEN** the generated artifact MUST include local math support CSS under `site/_raya/render/math/`

#### Scenario: Root page links local math resources
- **WHEN** a root generated page contains pre-rendered math
- **THEN** its HTML MUST link math support resources through relative URLs under `_raya/render/math/`

#### Scenario: Nested page links local math resources
- **WHEN** a nested generated page contains pre-rendered math
- **THEN** its HTML MUST link math support resources through deployment-neutral relative URLs that resolve to `site/_raya/render/math/`

#### Scenario: External renderer assets are not required
- **WHEN** generated pages with math are served from `artifact/site/`
- **THEN** the page MUST NOT require CDN, configured host, backend, Python, Node, or MathJax service requests to display typeset math

### Requirement: Hardened render fixture coverage
The minimal static builder SHALL build representative fixture material that
exercises math-heavy static rendering beside existing image, link, code, and
layout behavior.

#### Scenario: Math-heavy fixture builds
- **WHEN** `raya build` runs against the representative renderer fixture
- **THEN** generated HTML MUST include pre-rendered inline math, display math, local image assets, stable links, nested local links, code blocks, callouts, tables, footnotes, generated indexes, and page table of contents output

#### Scenario: Fixture remains non-canonical
- **WHEN** contributors inspect renderer hardening fixture source or output
- **THEN** the fixture MUST identify itself as fixture material and MUST point to `docs/foundation/` for authority

#### Scenario: Layout remains readable
- **WHEN** representative pages contain math, code, images, tables, callouts, footnotes, generated indexes, support panels, or inspection links
- **THEN** generated HTML and CSS MUST avoid horizontal overflow and incoherent overlap across representative desktop and mobile-sized viewports
