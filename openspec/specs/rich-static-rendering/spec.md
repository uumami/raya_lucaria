# rich-static-rendering Specification

## Purpose
Defines Glintstone's rich static Markdown rendering baseline for course pages, including static Markdown structures, code display, math, callouts, footnotes, page-local anchors, generated page tables of contents, safety behavior, and static-first constraints.
## Requirements
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

### Requirement: Static reviewed output panels
Rich static rendering SHALL display current reviewed execution output as compact static page content when a page references a reviewed target.

#### Scenario: Reviewed panel rendered
- **WHEN** a page references a target with current reviewed output
- **THEN** the generated HTML MUST show a reviewed-output panel with clear reviewed status, target label, and deployment-neutral links or excerpts for reviewed files

#### Scenario: Reviewed panel is data-backed
- **WHEN** a reviewed-output panel is rendered
- **THEN** its source metadata MUST come from manifest-declared reviewed output data rather than generated HTML being treated as authority

#### Scenario: Static panel does not execute
- **WHEN** a reviewed-output panel is generated or served
- **THEN** it MUST NOT execute code, notebooks, kernels, runtime profiles, or cache refreshes

### Requirement: Build-time MathJax rendering
Glintstone SHALL pre-render supported TeX/LaTeX math during `raya build` into
the generated static artifact and SHALL fail the build when math would visibly
break a published page.

#### Scenario: Inline math is typeset
- **WHEN** a page contains supported inline math
- **THEN** generated HTML MUST contain MathJax-rendered output rather than only raw TeX text

#### Scenario: Display math is typeset
- **WHEN** a page contains supported display math
- **THEN** generated HTML MUST contain MathJax-rendered display output with local support CSS

#### Scenario: Broken math fails build
- **WHEN** MathJax reports a conversion error for source math
- **THEN** build MUST fail with a diagnostic naming the source file and math expression context

#### Scenario: Malformed inline delimiters fail build
- **WHEN** a page contains malformed inline math delimiters
- **THEN** build MUST fail before publication with a diagnostic naming the source file, source span or nearby context, expression text, and next action

#### Scenario: Malformed display delimiters fail build
- **WHEN** a page contains malformed display math delimiters
- **THEN** build MUST fail before publication with a diagnostic naming the source file, source span or nearby context, expression text, and next action

#### Scenario: Unsupported delimiter nesting fails build
- **WHEN** a page contains unsupported nested math delimiters
- **THEN** build MUST fail before publication with a diagnostic naming the source file, source span or nearby context, expression text, and next action

#### Scenario: Missing local math resources fail build
- **WHEN** generated MathJax output requires local support CSS or assets that are missing from the artifact
- **THEN** build MUST fail before publication with a diagnostic naming the missing local resource and the generated page or source math that requires it

#### Scenario: Raw visible math leakage fails build
- **WHEN** math rendering fails or falls back in a way that would leave raw TeX visibly presented as rendered math
- **THEN** build MUST fail before publication unless the fallback is an explicitly accepted diagnostic-backed unsupported-notation case

#### Scenario: Diagnostics identify repair context
- **WHEN** build fails because math would visibly break a published page
- **THEN** diagnostics MUST name the source file, source span or nearby context, math expression, failure reason, and concrete next action

#### Scenario: Preview and deployment use one artifact
- **WHEN** preview serves a course after build
- **THEN** it MUST serve the same pre-rendered math files that static deployment serves

### Requirement: Accepted math authoring syntax
Glintstone SHALL define the accepted first-baseline math syntax so authors,
contributors, and agents do not guess which TeX/LaTeX forms are supported.

#### Scenario: Inline dollar math accepted
- **WHEN** a page contains supported inline math delimited with `$...$`
- **THEN** build MUST pre-render it with MathJax as inline math

#### Scenario: Display dollar blocks accepted
- **WHEN** a page contains supported display math in `$$` blocks with opening and closing delimiters on their own lines
- **THEN** build MUST pre-render it with MathJax as display math

#### Scenario: Full LaTeX documents rejected
- **WHEN** a page contains arbitrary full LaTeX document structure instead of supported math expressions or environments
- **THEN** build MUST fail with an actionable diagnostic rather than attempting to publish it as supported course math

#### Scenario: Supported MathJax baseline extensions
- **WHEN** a page uses notation supported by the `base`, `ams`, or `newcommand` MathJax TeX extensions
- **THEN** build MUST support common matrices, aligned equations, cases, operators, accents, fractions, sums, products, limits, integrals, Greek symbols, subscripts, and superscripts

#### Scenario: Page-local macros accepted
- **WHEN** a page or expression defines TeX-local macros with `\newcommand` or `\renewcommand`
- **THEN** build MUST render those macros through MathJax without requiring a course-level macro configuration file

#### Scenario: Unknown macros fail
- **WHEN** a page uses an unknown macro or control sequence that is not defined by supported page-local TeX macro syntax
- **THEN** build MUST fail with an actionable diagnostic naming the source file, source span or nearby context, unknown macro or control sequence, and next action

#### Scenario: Course-level macro config deferred
- **WHEN** a course includes a proposed course-level math macro configuration file
- **THEN** this change MUST NOT treat that file as accepted contract unless a later accepted proposal defines it

#### Scenario: Fenced code is not math
- **WHEN** a fenced code block contains `$`, `$$`, TeX commands, or LaTeX-looking text
- **THEN** build MUST render it as code and MUST NOT attempt MathJax conversion for that fenced code content

#### Scenario: Escaped dollar signs remain text
- **WHEN** source Markdown escapes dollar signs intended as text
- **THEN** generated HTML MUST preserve them as text instead of treating them as math delimiters

### Requirement: Math rendering remains static-first
Build-time math rendering SHALL use renderer dependencies only and SHALL NOT
turn course content into executable runtime behavior.

#### Scenario: Renderer dependency is not course execution
- **WHEN** Glintstone invokes MathJax during `raya build`
- **THEN** the renderer MUST NOT execute course scripts, notebooks, kernels, `uv`, Docker execution, package installers, cache refreshes, `raya run`, or `raya outputs freeze`

#### Scenario: Browser-only MathJax is not canonical
- **WHEN** generated pages are opened from `artifact/site/`
- **THEN** the visible math baseline MUST come from pre-rendered artifact files rather than requiring a browser-side MathJax conversion pass

#### Scenario: Unsupported math fallback is diagnostic-backed
- **WHEN** a controlled fallback is accepted for unsupported notation
- **THEN** the generated page MUST preserve visible source TeX and emit an actionable diagnostic instead of silently presenting fallback text as correctly rendered math
