## ADDED Requirements

### Requirement: Build-time MathJax rendering
Glintstone SHALL pre-render supported TeX/LaTeX math during `raya build` into
the generated static artifact.

#### Scenario: Inline math is typeset
- **WHEN** a page contains supported inline math
- **THEN** generated HTML MUST contain MathJax-rendered output rather than only raw TeX text

#### Scenario: Display math is typeset
- **WHEN** a page contains supported display math
- **THEN** generated HTML MUST contain MathJax-rendered display output with local support CSS

#### Scenario: Broken math fails build
- **WHEN** MathJax reports a conversion error for source math
- **THEN** build MUST fail with a diagnostic naming the source file and math expression context

#### Scenario: Preview and deployment use one artifact
- **WHEN** preview serves a course after build
- **THEN** it MUST serve the same pre-rendered math files that static deployment serves

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
