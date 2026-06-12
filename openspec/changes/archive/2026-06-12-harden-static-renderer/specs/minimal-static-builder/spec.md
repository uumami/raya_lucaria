## ADDED Requirements

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
