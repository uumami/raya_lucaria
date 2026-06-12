## ADDED Requirements

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
- **WHEN** a page uses notation supported by the `base`, `ams`, `newcommand`, or `noundefined` MathJax TeX extensions
- **THEN** build MUST support common matrices, aligned equations, cases, operators, accents, fractions, sums, products, limits, integrals, Greek symbols, subscripts, and superscripts

#### Scenario: Page-local macros accepted
- **WHEN** a page or expression defines TeX-local macros with `\newcommand` or `\renewcommand`
- **THEN** build MUST render those macros through MathJax without requiring a course-level macro configuration file

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
