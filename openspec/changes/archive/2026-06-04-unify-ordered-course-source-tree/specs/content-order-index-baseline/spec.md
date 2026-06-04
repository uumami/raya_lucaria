## MODIFIED Requirements

### Requirement: Ordered source entries
Rendered course content SHALL use visible ordered source entries under the configured authored source root.

#### Scenario: Numeric main sequence is resolved
- **WHEN** validation scans sibling rendered entries named `1_limits.md`, `2_derivatives.md`, and `10_applications.md`
- **THEN** it MUST resolve them in numeric order `1`, `2`, `10` rather than lexicographic order

#### Scenario: Padded numeric prefixes normalize
- **WHEN** validation scans a sibling set that consistently uses padded prefixes such as `01_limits.md` and `02_derivatives.md`
- **THEN** it MUST treat those prefixes as normalized order values `1` and `2`

#### Scenario: Duplicate normalized order fails
- **WHEN** sibling rendered entries normalize to the same order value, such as `1_intro.md` and `01_intro.md`
- **THEN** validation MUST fail with an actionable diagnostic naming both entries

#### Scenario: Mixed main prefix style fails
- **WHEN** non-index sibling rendered entries in the same main sequence mix prefix widths, such as `1_limits.md` and `02_derivatives.md`
- **THEN** validation MUST fail and identify the inconsistent ordered entries

### Requirement: Rendered source inclusion
The ordered source contract SHALL define which source files render and which files remain private, partial, official, asset, or draft material.

#### Scenario: Ordered Markdown pages render
- **WHEN** a Markdown file under the authored source root uses a valid numeric or appendix prefix and is not under a private, support, or draft path
- **THEN** it MUST be included in the resolved navigation and rendered static site

#### Scenario: Private paths do not render
- **WHEN** Markdown files live under `_partials/`, `_drafts/`, `drafts/`, `_official/`, `_assets/`, or use another leading underscore support path segment
- **THEN** they MUST NOT be rendered as public course pages or included in generated indexes

#### Scenario: Unordered published content fails
- **WHEN** a Markdown file under an ordered source directory lacks a valid rendered prefix and is not private, support, or draft material
- **THEN** validation MUST fail with a diagnostic that recommends adding an order prefix or moving the file to a private or support path

## ADDED Requirements

### Requirement: Ordered support object files
Official learning-object files under colocated `_official/` directories SHALL use ordered source names for predictable authoring and export order.

#### Scenario: Ordered official object names validate
- **WHEN** validation scans `_official/cards/1_limit_meaning.yaml` and `_official/cards/2_limit_notation.yaml`
- **THEN** it MUST preserve their source order within the card family without treating the numeric prefixes as object IDs

#### Scenario: Unordered official object name fails
- **WHEN** validation scans a colocated official object file such as `_official/cards/limit_meaning.yaml`
- **THEN** validation MUST fail with an actionable diagnostic recommending an ordered filename such as `1_limit_meaning.yaml`

#### Scenario: Duplicate official object order fails
- **WHEN** two sibling official object files in the same family normalize to the same order value
- **THEN** validation MUST fail with an actionable diagnostic naming the conflicting files
