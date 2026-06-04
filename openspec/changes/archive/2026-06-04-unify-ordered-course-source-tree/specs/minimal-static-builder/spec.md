## MODIFIED Requirements

### Requirement: Source course build
The minimal builder SHALL build a validated source course into the artifact output directory declared by `raya.yaml`.

#### Scenario: Build canonical source fixture
- **WHEN** `raya build examples/courses/minimal` runs against a fixture using `source: course`
- **THEN** it MUST create the configured artifact directory with `site/`, `manifest.json`, `data/`, and `assets/`

#### Scenario: Validation before build
- **WHEN** source course validation fails
- **THEN** the builder MUST stop before writing a successful artifact and report validation diagnostics

### Requirement: Official study seed export
The minimal builder SHALL export official learning objects from source-root and quantum-colocated `_official/` locations as static study seed data while preserving authority and scope.

#### Scenario: Colocated official objects indexed
- **WHEN** source official cards, quizzes, or prompts exist under `_official/`
- **THEN** `data/official.json` MUST include them with stable IDs, object types, official authority labels, inferred or explicit learning-quantum scope, source paths, and content payloads

#### Scenario: Personal state excluded
- **WHEN** official learning objects are exported
- **THEN** generated artifact data MUST NOT include private review history, confidence ratings, personal mastery state, or spaced repetition history

### Requirement: Asset copying
The minimal builder SHALL copy local course assets into the artifact assets directory when source assets exist.

#### Scenario: Copy colocated assets
- **WHEN** a source course contains referenced files under `_assets/` inside the authored source tree
- **THEN** the generated artifact MUST copy those files into artifact assets and browser-facing static assets without rendering the `_assets/` directory as course pages

### Requirement: Static read-path asset copying
The minimal builder SHALL copy browser-facing local course assets into the generated static read path.

#### Scenario: Referenced colocated asset copied for static site
- **WHEN** a source Markdown page references an existing colocated `_assets/` file
- **THEN** the generated artifact MUST contain that asset under `site/_raya/assets/` with a collision-safe path and a deployment-neutral rendered URL

#### Scenario: Existing artifact asset copy preserved
- **WHEN** a source course contains referenced colocated `_assets/`
- **THEN** the generated artifact MUST continue to expose copied assets under artifact-level `assets/`
