## ADDED Requirements

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
