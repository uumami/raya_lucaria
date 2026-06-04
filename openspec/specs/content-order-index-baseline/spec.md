# content-order-index-baseline Specification

## Purpose
Defines the ordered source authoring model, page metadata baseline, stable `raya:` references, appendix ordering, hierarchy labels, and generated local/master index behavior for rendered course content.
## Requirements
### Requirement: Ordered source entries
Rendered course content SHALL use visible ordered source entries under the configured authored source root.

#### Scenario: Numeric main sequence is resolved
- **WHEN** validation scans sibling rendered entries named `1_limits.md`, `2_derivatives.md`, and `10_applications.md`
- **THEN** it MUST resolve them in numeric order `1`, `2`, `10` rather than lexicographic order

#### Scenario: Padded numeric prefixes normalize
- **WHEN** validation scans a sibling set that consistently uses padded prefixes such as `01_limits.md` and `02_derivatives.md`
- **THEN** it MUST treat those prefixes as normalized order values `1` and `2`

#### Scenario: Duplicate normalized order fails
- **WHEN** sibling rendered entries normalize to the same order value, such as `1_intro.md` and `01_intro.md`
- **THEN** validation MUST fail with an actionable diagnostic naming both entries

#### Scenario: Mixed main prefix style fails
- **WHEN** non-index sibling rendered entries in the same main sequence mix prefix widths, such as `1_limits.md` and `02_derivatives.md`
- **THEN** validation MUST fail and identify the inconsistent ordered entries

### Requirement: Rendered source inclusion
The ordered source contract SHALL define which source files render and which files remain private, partial, official, asset, or draft material.

#### Scenario: Ordered Markdown pages render
- **WHEN** a Markdown file under the authored source root uses a valid numeric or appendix prefix and is not under a private, support, or draft path
- **THEN** it MUST be included in the resolved navigation and rendered static site

#### Scenario: Private paths do not render
- **WHEN** Markdown files live under `_partials/`, `_drafts/`, `drafts/`, `_official/`, `_assets/`, or use another leading underscore support path segment
- **THEN** they MUST NOT be rendered as public course pages or included in generated indexes

#### Scenario: Unordered published content fails
- **WHEN** a Markdown file under an ordered source directory lacks a valid rendered prefix and is not private, support, or draft material
- **THEN** validation MUST fail with a diagnostic that recommends adding an order prefix or moving the file to a private or support path

### Requirement: Section landing pages
Rendered source directories SHALL have a landing index page that provides the manual section text and metadata for the directory quantum.

#### Scenario: Section directory has landing page
- **WHEN** a rendered directory participates in navigation
- **THEN** it MUST contain a normalized zero index page such as `0_index.md` or a consistent padded equivalent such as `00_index.md`

#### Scenario: Missing landing page fails
- **WHEN** a rendered directory lacks a normalized zero index page
- **THEN** validation MUST fail with a diagnostic naming the directory and expected index filename

#### Scenario: Directory metadata comes from landing page
- **WHEN** Glintstone resolves metadata for a rendered directory
- **THEN** it MUST read title, summary, stable identity, and status from the directory landing page rather than requiring a separate directory metadata file

### Requirement: Appendix sequence
Appendix or anexo content SHALL use letter prefixes as a sequence after the main numeric sequence.

#### Scenario: Appendix order resolves after main order
- **WHEN** a sibling set contains `1_foundations/`, `2_practice/`, and `A_reference/`
- **THEN** generated navigation MUST place `A_reference/` after the numeric main sequence

#### Scenario: Multi-letter appendices resolve
- **WHEN** appendices exceed single-letter labels and use `AA_` or `AB_`
- **THEN** validation MUST resolve them after `Z_` in appendix order

#### Scenario: Duplicate appendix label fails
- **WHEN** sibling appendix entries normalize to the same appendix label
- **THEN** validation MUST fail with an actionable diagnostic naming the conflicting entries

### Requirement: Page metadata frontmatter
Rendered pages and section landing pages SHALL expose enough metadata for stable references, generated previews, and future learning systems.

#### Scenario: Published page has stable identity
- **WHEN** validation scans a rendered page that is not draft or private material
- **THEN** the page MUST declare a globally unique frontmatter `id` for the course

#### Scenario: Title and summary are available
- **WHEN** Glintstone resolves a rendered page for navigation or generated indexes
- **THEN** it MUST expose a title and summary from frontmatter or validated Markdown inference

#### Scenario: Metadata fields are accepted
- **WHEN** a rendered page declares `id`, `title`, `nav_title`, `summary`, `status`, `estimated_time`, `tags`, `prerequisites`, or `aliases`
- **THEN** validation MUST parse those fields and preserve supported values in generated page or quantum data

#### Scenario: Alias collision fails
- **WHEN** two rendered pages declare the same `id` or alias in the same course
- **THEN** validation MUST fail and identify both declarations

### Requirement: Hierarchy labels
Course configuration SHALL allow rendered hierarchy labels without making directory metadata the source of order.

#### Scenario: Default hierarchy labels apply
- **WHEN** a course does not configure hierarchy labels
- **THEN** generated navigation MUST use a conservative default hierarchy vocabulary for rendered levels

#### Scenario: Configured labels render
- **WHEN** `raya.yaml` configures hierarchy labels such as Unit and Topic or Chapter and Section
- **THEN** generated navigation and indexes MUST use those labels while preserving source-tree order and containment

### Requirement: Stable source references
Stable source references SHALL target frontmatter IDs rather than order prefixes or source paths.

#### Scenario: Stable link resolves
- **WHEN** Markdown content links to `[Derivatives](raya:derivatives-rates)` and a rendered page declares `id: derivatives-rates`
- **THEN** validation MUST resolve the reference and the static builder MUST render a link to the current generated URL for that page

#### Scenario: Broken stable link fails
- **WHEN** Markdown content links to a `raya:` ID that no rendered page or alias declares
- **THEN** validation MUST fail with a diagnostic naming the source file and missing ID

#### Scenario: Renumbered page keeps stable reference
- **WHEN** a page changes its order prefix but keeps the same frontmatter `id`
- **THEN** `raya:` links, prerequisites, and generated learning-object scopes MUST continue to resolve to that page

### Requirement: Generated local and master indexes
Glintstone SHALL generate local and master indexes from resolved source metadata and study-object scopes without writing generated content back into source files.

#### Scenario: Manual index prose is preserved
- **WHEN** a section landing page contains manual Markdown prose
- **THEN** the rendered section page MUST include that prose before or around generated index sections without modifying the source file

#### Scenario: Index marker controls placement
- **WHEN** a source index page contains `<!-- raya:index -->`
- **THEN** the rendered generated index section MUST appear at that marker location

#### Scenario: Missing marker uses default placement
- **WHEN** a source index page omits `<!-- raya:index -->`
- **THEN** the rendered generated index section MUST be appended after the manual page content in a predictable default location

#### Scenario: Child summaries populate local index
- **WHEN** a section has rendered child pages with titles and summaries
- **THEN** the rendered section index MUST list those children in resolved order with generated labels, titles, summaries, and links

#### Scenario: Root master index includes main and appendix sections
- **WHEN** Glintstone renders the root course index
- **THEN** it MUST generate a master index that includes main ordered sections and appendix sections from the resolved navigation tree

### Requirement: Ordered support object files
Official learning-object files under colocated `_official/` directories SHALL use ordered source names for predictable authoring and export order.

#### Scenario: Ordered official object names validate
- **WHEN** validation scans `_official/cards/1_limit_meaning.yaml` and `_official/cards/2_limit_notation.yaml`
- **THEN** it MUST preserve their source order within the card family without treating the numeric prefixes as object IDs

#### Scenario: Unordered official object name fails
- **WHEN** validation scans a colocated official object file such as `_official/cards/limit_meaning.yaml`
- **THEN** validation MUST fail with an actionable diagnostic recommending an ordered filename such as `1_limit_meaning.yaml`

#### Scenario: Duplicate official object order fails
- **WHEN** two sibling official object files in the same family normalize to the same order value
- **THEN** validation MUST fail with an actionable diagnostic naming the conflicting files

