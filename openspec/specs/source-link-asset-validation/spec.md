# source-link-asset-validation Specification

## Purpose
TBD - created by archiving change add-source-link-and-asset-validation. Update Purpose after archive.
## Requirements
### Requirement: Local content link validation
Source course validation SHALL validate local Markdown links that target course content files.

#### Scenario: Valid content link
- **WHEN** a Markdown content file links to another existing `.md` file under the configured content directory
- **THEN** validation MUST pass that link and treat it as a valid source content link

#### Scenario: Broken content link
- **WHEN** a Markdown content file links to a missing `.md` file under the configured content directory
- **THEN** validation MUST fail with a diagnostic naming the source file and link target

### Requirement: Local asset reference validation
Source course validation SHALL validate local asset references in Markdown content.

#### Scenario: Valid asset reference
- **WHEN** a Markdown content file links to an existing file under the configured or default assets directory
- **THEN** validation MUST pass that reference and read the asset file

#### Scenario: Missing asset reference
- **WHEN** a Markdown content file links to a missing local asset file
- **THEN** validation MUST fail with a diagnostic naming the source file and asset target

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

