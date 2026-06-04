## MODIFIED Requirements

### Requirement: Rendered documentation is labeled and portable
Rendered documentation or documentation fixtures SHALL preserve the static-first and authority-boundary rules.

#### Scenario: Documentation is rendered by Glintstone
- **WHEN** documentation is rendered into a static artifact or exercised through a documentation fixture
- **THEN** it MUST be labeled as documentation or fixture material and MUST remain separate from class/course examples

#### Scenario: Rendered documentation stays portable
- **WHEN** rendered documentation is served from its static read path
- **THEN** it MUST not require a backend, configured host, CDN, identity provider, or client-side router

#### Scenario: Current docs render through ordered source
- **WHEN** the live repository documentation under `docs/` is validated or built
- **THEN** `docs/raya.yaml` MUST define a docs course whose ordered render source includes current foundation and role documentation without making generated artifact output authoritative

#### Scenario: Render source preserves readable doc paths
- **WHEN** the live docs render source references current documentation
- **THEN** readable repository paths such as `docs/foundation/` and `docs/guides/` MUST remain the human-facing documentation paths
