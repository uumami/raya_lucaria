## ADDED Requirements

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
