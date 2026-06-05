## ADDED Requirements

### Requirement: Rich Markdown page rendering
Glintstone SHALL render a defined rich static Markdown baseline for course pages without requiring a backend, external hosted service, or executable runtime.

#### Scenario: Common block structures render
- **WHEN** a rendered source page contains headings, paragraphs, unordered lists, ordered lists, blockquotes, thematic breaks, emphasis, strong text, inline code, local links, stable `raya:` links, and local assets
- **THEN** the generated HTML MUST preserve the readable structure and MUST continue to resolve local links, stable links, and local assets through Raya link and asset rules

#### Scenario: Tables render
- **WHEN** a rendered source page contains a valid Markdown pipe table
- **THEN** the generated HTML MUST include a semantic table with header and body cells

#### Scenario: Unsupported raw HTML is safe
- **WHEN** a rendered source page contains raw HTML or potentially unsafe markup
- **THEN** the generated HTML MUST either escape it or sanitize it so scripts and event handlers do not execute by default

### Requirement: Static code block rendering
Glintstone SHALL render fenced code blocks as static readable code without executing them.

#### Scenario: Language code block renders
- **WHEN** a rendered source page contains a fenced code block with a declared language
- **THEN** the generated HTML MUST include escaped code, a language label or machine-readable language marker, and syntax highlighting when the language is supported

#### Scenario: Unknown language remains readable
- **WHEN** a rendered source page contains a fenced code block with an unknown language
- **THEN** the generated HTML MUST render escaped code without failing the build

#### Scenario: Code block does not execute
- **WHEN** a rendered source page contains executable-looking code
- **THEN** the build MUST NOT run that code as part of rich static rendering

### Requirement: Static math rendering
Glintstone SHALL support inline and display math in static course pages without requiring network-hosted resources.

#### Scenario: Inline math renders
- **WHEN** a rendered source page contains inline math
- **THEN** the generated HTML MUST preserve the TeX source and render a browser-usable inline math element

#### Scenario: Display math renders
- **WHEN** a rendered source page contains display math
- **THEN** the generated HTML MUST preserve the TeX source and render a browser-usable display math element

#### Scenario: Math support is local
- **WHEN** math rendering requires browser-facing support resources
- **THEN** those resources MUST be generated under `site/_raya/` and MUST NOT depend on a CDN or configured host

### Requirement: Callout rendering
Glintstone SHALL render GitHub-style blockquote callout syntax for `[!NOTE]`, `[!TIP]`, `[!WARNING]`, and `[!CAUTION]` as semantic static callout blocks.

#### Scenario: Note callout renders
- **WHEN** a rendered source page contains an accepted note callout
- **THEN** the generated HTML MUST render a distinguishable callout with a semantic label and readable body

#### Scenario: Warning callout renders
- **WHEN** a rendered source page contains an accepted warning or caution callout
- **THEN** the generated HTML MUST render a distinguishable warning callout with a semantic label and readable body

### Requirement: Footnote rendering
Glintstone SHALL render footnotes for static course pages while keeping bibliography and citation systems out of this baseline.

#### Scenario: Footnote reference renders
- **WHEN** a rendered source page contains a footnote reference and matching footnote definition
- **THEN** the generated HTML MUST link the reference to a rendered footnote entry on the same page

#### Scenario: Missing footnote definition fails or warns
- **WHEN** a rendered source page contains a footnote reference without a matching definition
- **THEN** validation or build MUST produce an actionable diagnostic naming the source page and footnote label

### Requirement: Heading anchors and page table of contents
Glintstone SHALL generate page-local heading anchors and a page table of contents from rendered headings.

#### Scenario: Heading anchors render
- **WHEN** a rendered source page contains section headings below the page title
- **THEN** the generated HTML MUST include page-local anchor IDs for those headings without treating them as durable course identity

#### Scenario: Duplicate heading anchors are unique
- **WHEN** a rendered source page contains duplicate heading text
- **THEN** generated heading anchor IDs MUST remain unique within that page

#### Scenario: Page table of contents renders
- **WHEN** a rendered source page contains at least two headings below the page title
- **THEN** the generated HTML MUST include a page table of contents linking to generated page-local heading anchors

### Requirement: Rich rendering remains static-first
Rich static rendering SHALL not introduce execution, accounts, backend services, client-side routing, or hosted-service requirements.

#### Scenario: Static page remains file-servable
- **WHEN** a rich-rendered page is served directly from `artifact/site/`
- **THEN** its rich content, navigation, links, local assets, and generated render resources MUST work without a backend

#### Scenario: Execution is deferred
- **WHEN** source content includes code, math, or rich formatting
- **THEN** the build MUST NOT require `uv`, Docker, Jupyter, Pyodide, notebook kernels, or a runtime profile to render the static page
