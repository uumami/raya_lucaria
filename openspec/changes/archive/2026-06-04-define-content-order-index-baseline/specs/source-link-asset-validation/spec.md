## ADDED Requirements

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
- **WHEN** a Markdown content file links to another existing `.md` file under the configured content directory
- **THEN** validation MUST continue to pass that local path link according to the local content link validation contract

#### Scenario: Fragile path link warning
- **WHEN** a local Markdown path link targets rendered course content that has a stable page ID
- **THEN** validation MUST report non-failing guidance that a `raya:` reference is more durable for links that must survive renumbering or moves
