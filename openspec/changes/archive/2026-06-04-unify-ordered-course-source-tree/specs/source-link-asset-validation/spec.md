## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Colocated asset support
Colocated `_assets/` directories SHALL provide source-local files for rendered pages without becoming rendered navigation entries.

#### Scenario: Colocated asset copied for static read path
- **WHEN** a rendered page references an existing colocated `_assets/` file
- **THEN** the builder MUST copy that asset into the generated artifact and rewrite the rendered link to a deployment-neutral relative URL

#### Scenario: Colocated asset directory is private
- **WHEN** validation scans Markdown or other files under `_assets/`
- **THEN** those files MUST NOT be rendered as course pages or included in generated indexes
