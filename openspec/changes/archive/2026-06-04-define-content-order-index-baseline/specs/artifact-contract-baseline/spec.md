## MODIFIED Requirements

### Requirement: Generated data indexes
Artifact data SHALL expose pages, quanta, links, navigation, generated indexes, and official learning objects as generated indexes.

#### Scenario: Data indexes present
- **WHEN** artifact data is validated
- **THEN** it MUST include page, quanta, link, navigation, generated index, and official learning-object indexes

#### Scenario: Rebuildable generated data
- **WHEN** generated data differs from source course truth
- **THEN** source course truth MUST be treated as canonical and generated data MUST be rebuildable

### Requirement: Builder-produced artifact validation
Artifacts produced by the minimal Glintstone builder SHALL satisfy the baseline artifact contract.

#### Scenario: Produced artifact shape
- **WHEN** `raya build <course>` completes successfully
- **THEN** the produced artifact MUST contain `site/`, `manifest.json`, `data/pages.json`, `data/quanta.json`, `data/links.json`, `data/navigation.json`, `data/indices.json`, `data/official.json`, and `assets/`

#### Scenario: Produced artifact schemas
- **WHEN** the produced manifest and data indexes are validated
- **THEN** they MUST pass the artifact manifest, pages index, quanta index, links index, navigation index, generated indexes, and official index schema validators

## ADDED Requirements

### Requirement: Navigation artifact data
Artifact data SHALL expose resolved navigation as machine-readable generated data rather than requiring consumers to scrape rendered HTML.

#### Scenario: Navigation data present
- **WHEN** a baseline artifact is produced
- **THEN** `manifest.json` MUST declare a navigation data path and that data MUST describe the resolved order, labels, URLs, parent/child relationships, breadcrumbs, previous links, and next links

#### Scenario: Navigation data is generated
- **WHEN** source order, hierarchy labels, or page metadata changes
- **THEN** navigation artifact data MUST be regenerated from source truth rather than edited as canonical source

### Requirement: Generated index artifact data
Artifact data SHALL expose generated local and master index data as machine-readable generated data.

#### Scenario: Index data present
- **WHEN** a baseline artifact is produced
- **THEN** `manifest.json` MUST declare a generated index data path and that data MUST describe local section indexes, master index entries, appendix entries, summaries, and study-object counts available to the static site

#### Scenario: Index data does not include private material
- **WHEN** generated index data is produced
- **THEN** it MUST NOT include private, draft, partial, or unrendered source content as public index entries
