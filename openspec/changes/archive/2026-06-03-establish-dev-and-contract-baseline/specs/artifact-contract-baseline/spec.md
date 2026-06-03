## ADDED Requirements

### Requirement: Portable artifact shape
A course artifact SHALL contain a static read path, a manifest, generated data indexes, and copied or referenced local assets.

#### Scenario: Required artifact paths
- **WHEN** a baseline artifact is produced or inspected
- **THEN** it MUST contain `site/`, `manifest.json`, `data/`, and `assets/` according to the artifact contract

### Requirement: Manifest entrypoint
`manifest.json` SHALL be the backend-readable and agent-readable entrypoint for a course artifact.

#### Scenario: Manifest required fields
- **WHEN** an artifact manifest is validated
- **THEN** it MUST include artifact version, course ID, course version or content hash, generated timestamp, source schema version, static site root, and data index locations

#### Scenario: Services read manifest
- **WHEN** a future dynamic service needs artifact data
- **THEN** the artifact contract MUST require it to discover data through `manifest.json` instead of scraping rendered HTML as authority

### Requirement: Generated data indexes
Artifact data SHALL expose pages, quanta, links, and official learning objects as generated indexes.

#### Scenario: Data indexes present
- **WHEN** artifact data is validated
- **THEN** it MUST include page, quanta, link, and official learning-object indexes

#### Scenario: Rebuildable generated data
- **WHEN** generated data differs from source course truth
- **THEN** source course truth MUST be treated as canonical and generated data MUST be rebuildable

### Requirement: Official study seed data
Artifacts SHALL expose official learning objects as study seed data without embedding personal review or mastery state.

#### Scenario: Official index contains study seeds
- **WHEN** official cards, quizzes, or prompts exist in source
- **THEN** artifact data MUST expose them with official authority labels and learning-quantum scope

#### Scenario: Private state excluded
- **WHEN** artifact data is generated
- **THEN** it MUST NOT include private notes, review history, confidence ratings, or personal mastery state

### Requirement: Static usefulness
The baseline artifact contract SHALL preserve a useful static course path without accounts, network services, or dynamic JavaScript-heavy behavior.

#### Scenario: Static site can be served as files
- **WHEN** the artifact `site/` directory is served by static hosting
- **THEN** course pages, navigation, internal links, accessible HTML, and local assets MUST remain usable without a backend

### Requirement: Renderer independence
The artifact contract SHALL NOT depend on a specific static-site generator, JavaScript framework, CSS framework, or search tool.

#### Scenario: Renderer not part of contract
- **WHEN** a builder satisfies the artifact contract
- **THEN** validation MUST NOT require any specific renderer stack as part of the artifact contract
