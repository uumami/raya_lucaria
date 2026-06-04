# source-link-asset-validation Specification

## Purpose
Defines validation for local Markdown content links and local asset references before build, while ignoring external and fragment-only links.
## Requirements
### Requirement: Local content link validation
Source course validation SHALL validate local Markdown links that target course content files.

#### Scenario: Valid content link
- **WHEN** a Markdown content file links to another existing `.md` file under the configured authored source root
- **THEN** validation MUST pass that link and treat it as a valid source content link

#### Scenario: Broken content link
- **WHEN** a Markdown content file links to a missing `.md` file under the configured authored source root
- **THEN** validation MUST fail with a diagnostic naming the source file and link target

### Requirement: Local asset reference validation
Source course validation SHALL validate local asset references in Markdown content against the page's own `_assets/` directory or an ancestor `_assets/` support directory inside the authored source tree.

#### Scenario: Valid colocated asset reference
- **WHEN** a Markdown page links to an existing file under its own or an ancestor `_assets/` directory
- **THEN** validation MUST pass that reference and read the asset file

#### Scenario: Missing asset reference
- **WHEN** a Markdown page links to a missing local asset file
- **THEN** validation MUST fail with a diagnostic naming the source file and asset target

#### Scenario: Support object is not an asset
- **WHEN** a Markdown page links to a file under `_official/`, `_drafts/`, or `_partials/`
- **THEN** validation MUST fail unless a future accepted contract explicitly allows that reference type

### Requirement: Non-local link handling
Source course validation SHALL NOT require external URLs or fragment-only links to resolve as local files.

#### Scenario: External and fragment links ignored
- **WHEN** a Markdown content file contains `https://`, `mailto:`, `tel:`, or `#fragment` links
- **THEN** validation MUST NOT fail because those targets are not present as local files

### Requirement: Actionable link diagnostics
Link and asset validation SHALL produce diagnostics useful to humans and coding agents.

#### Scenario: Link diagnostic details
- **WHEN** validation finds a broken local link or missing local asset
- **THEN** the diagnostic MUST include the source file, link target field, and a concrete next action

### Requirement: Stable content reference validation
Source course validation SHALL validate `raya:` stable content references against rendered page IDs and aliases.

#### Scenario: Valid stable reference
- **WHEN** a Markdown content file links to `raya:derivatives-rates` and a rendered page declares `id: derivatives-rates`
- **THEN** validation MUST pass that reference and treat it as a valid source content link

#### Scenario: Valid alias reference
- **WHEN** a Markdown content file links to a `raya:` value declared in a rendered page's aliases
- **THEN** validation MUST pass that reference and resolve it to the page that owns the alias

#### Scenario: Broken stable reference
- **WHEN** a Markdown content file links to a `raya:` value that no rendered page ID or alias declares
- **THEN** validation MUST fail with a diagnostic naming the source file and missing stable reference

#### Scenario: Stable reference diagnostic
- **WHEN** validation reports a broken `raya:` reference
- **THEN** the diagnostic MUST explain that `raya:` links target stable frontmatter IDs or aliases rather than source paths or order prefixes

### Requirement: Durable link guidance
Source course validation SHALL preserve normal Markdown link support while guiding authors toward stable references for durable course links.

#### Scenario: Normal Markdown content link remains valid
- **WHEN** a Markdown content file links to another existing `.md` file under the configured authored source root
- **THEN** validation MUST continue to pass that local path link according to the local content link validation contract

#### Scenario: Fragile path link warning
- **WHEN** a local Markdown path link targets rendered course content that has a stable page ID
- **THEN** validation MUST report non-failing guidance that a `raya:` reference is more durable for links that must survive renumbering or moves

### Requirement: Colocated asset support
Colocated `_assets/` directories SHALL provide source-local files for rendered pages without becoming rendered navigation entries.

#### Scenario: Colocated asset copied for static read path
- **WHEN** a rendered page references an existing colocated `_assets/` file
- **THEN** the builder MUST copy that asset into the generated artifact and rewrite the rendered link to a deployment-neutral relative URL

#### Scenario: Colocated asset directory is private
- **WHEN** validation scans Markdown or other files under `_assets/`
- **THEN** those files MUST NOT be rendered as course pages or included in generated indexes

