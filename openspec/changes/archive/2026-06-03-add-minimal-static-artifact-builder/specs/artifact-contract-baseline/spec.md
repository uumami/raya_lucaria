## ADDED Requirements

### Requirement: Builder-produced artifact validation
Artifacts produced by the minimal Glintstone builder SHALL satisfy the baseline artifact contract.

#### Scenario: Produced artifact shape
- **WHEN** `raya build <course>` completes successfully
- **THEN** the produced artifact MUST contain `site/`, `manifest.json`, `data/pages.json`, `data/quanta.json`, `data/links.json`, `data/official.json`, and `assets/`

#### Scenario: Produced artifact schemas
- **WHEN** the produced manifest and data indexes are validated
- **THEN** they MUST pass the artifact manifest, pages index, quanta index, links index, and official index schema validators

### Requirement: Static site output from builder
Builder-produced artifacts SHALL include static HTML that remains useful when served as files.

#### Scenario: Readable file-served pages
- **WHEN** the generated `site/` directory is opened through static hosting or local files
- **THEN** course pages, titles, readable content, and navigation links MUST be available without accounts, network services, or client-side routing
