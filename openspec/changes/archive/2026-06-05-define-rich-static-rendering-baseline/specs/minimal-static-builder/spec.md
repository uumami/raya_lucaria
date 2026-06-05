## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Rich render fixture builds
The minimal builder SHALL build a representative rich rendering fixture that exercises the accepted static rendering baseline.

#### Scenario: Rich render fixture output
- **WHEN** `raya build` runs against the representative rich rendering fixture
- **THEN** the generated HTML MUST contain examples of headings, lists, links, code blocks, math, tables, callouts, footnotes, heading anchors, and a page table of contents

#### Scenario: Rich render fixture remains fixture material
- **WHEN** contributors inspect rich rendering fixture source or output
- **THEN** it MUST be labeled as fixture material and MUST point to `docs/foundation/` for authority
