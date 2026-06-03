# static-render-resource-resolution Specification

## Purpose
Defines browser-facing static resource resolution for generated artifacts, including `site/_raya/` assets and deployment-neutral rendered URLs.
## Requirements
### Requirement: Browser-facing static resource namespace
Generated static artifacts SHALL use `site/_raya/` as the browser-facing namespace for framework-managed static resources.

#### Scenario: Local asset resource namespace
- **WHEN** a source course asset is referenced from rendered Markdown content
- **THEN** the generated static site MUST make that asset available under `site/_raya/assets/`

#### Scenario: Reserved generated namespace
- **WHEN** the builder writes files under `site/_raya/`
- **THEN** those files MUST be treated as generated artifact resources rather than canonical course source truth

### Requirement: Deployment-neutral asset URLs
Rendered HTML SHALL reference browser-facing local assets with relative URLs that do not depend on a domain, deployment root, backend route, or CDN.

#### Scenario: Nested page asset URL
- **WHEN** a nested generated HTML page references a local source asset
- **THEN** the rendered asset URL MUST be relative from that HTML page to the asset under `site/_raya/assets/`

#### Scenario: Root page asset URL
- **WHEN** a root generated HTML page references a local source asset
- **THEN** the rendered asset URL MUST be relative from that HTML page to the asset under `site/_raya/assets/`

### Requirement: Browser and machine artifact surfaces remain separate
Generated artifacts SHALL distinguish browser-facing static resources from machine-readable artifact data.

#### Scenario: Browser static resources
- **WHEN** `artifact/site/` is served as the static read path
- **THEN** rendered pages and browser-facing local assets MUST be usable from files under `artifact/site/`

#### Scenario: Machine-readable data remains manifest-centered
- **WHEN** an artifact is inspected or read by a future dynamic installation
- **THEN** machine-readable data MUST remain discoverable through `manifest.json` and manifest-declared `data/*.json` paths rather than rendered HTML

### Requirement: Future render capabilities use the static resource namespace
Future browser-facing renderer capabilities SHALL use the `site/_raya/` namespace when they need generated browser resources.

#### Scenario: Future math or component assets
- **WHEN** a later proposal adds math rendering, syntax highlighting, public browser data, or interactive component assets
- **THEN** those browser-facing resources MUST fit under `site/_raya/` or explicitly update the static resource contract

### Requirement: Representative static render e2e fixture
The repository SHALL include representative fixture content for static render e2e tests when browser-facing static resource behavior is changed.

#### Scenario: Fixture content covers framework overview
- **WHEN** the static render e2e fixture is added
- **THEN** it MUST include a concise page about the Raya Lucaria framework, its static path, and its domain concepts while clearly labeling the content as fixture material

#### Scenario: Fixture content covers render resources
- **WHEN** the static render e2e fixture is built
- **THEN** it MUST exercise at least one root page, one nested page, one local content link, one local asset link, and ignored external or fragment links

#### Scenario: Fixture does not become foundation truth
- **WHEN** contributors inspect the fixture content
- **THEN** it MUST point to `docs/foundation/` as the authority surface rather than defining architecture or pedagogy by example

### Requirement: Rendered documentation uses the static read path
Rendered documentation and documentation fixtures SHALL use the same deployment-neutral static read-path rules as generated course artifacts.

#### Scenario: Documentation asset URLs
- **WHEN** rendered documentation references local documentation assets
- **THEN** the generated URLs MUST be relative and MUST resolve through the rendered static read path without a backend, deployment root, CDN, or configured host

#### Scenario: Documentation render fixture separation
- **WHEN** rendered documentation is used as fixture content for Glintstone coverage
- **THEN** it MUST be labeled as documentation or fixture material and MUST remain separate from class/course examples and official course canon

#### Scenario: Rendered role documentation language pages
- **WHEN** rendered documentation or a documentation fixture includes contributor/collaborator, professor, student, or agent guidance
- **THEN** English and Spanish guidance MUST render as separate role-directory pages while preserving English technical identifiers

### Requirement: Rendered documentation does not become artifact authority
Rendered documentation SHALL remain explanatory guidance and MUST NOT replace machine-readable artifact surfaces.

#### Scenario: Dynamic installation reads course truth
- **WHEN** a future dynamic installation needs artifact data
- **THEN** it MUST continue reading through `manifest.json` and manifest-declared `data/*.json` paths rather than treating rendered documentation HTML as authority
