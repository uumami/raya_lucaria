## MODIFIED Requirements

### Requirement: Artifact data indexes
The minimal builder SHALL generate manifest-declared page, quanta, link, navigation, generated index, and official learning-object indexes.

#### Scenario: Generated indexes validate
- **WHEN** the generated artifact is inspected
- **THEN** `manifest.json`, `data/pages.json`, `data/quanta.json`, `data/links.json`, `data/navigation.json`, `data/indices.json`, and `data/official.json` MUST validate against the baseline artifact schemas

## ADDED Requirements

### Requirement: Ordered navigation rendering
The minimal builder SHALL render static navigation from the resolved ordered content tree.

#### Scenario: Ordered pages render clean URLs
- **WHEN** a source page such as `content/1_foundations/2_derivatives.md` is built
- **THEN** the rendered static page MUST use a clean URL derived from stripped path segments and MUST NOT expose order prefixes as URL identity

#### Scenario: Breadcrumb and sequence navigation render
- **WHEN** a rendered page has resolved parent, previous, or next entries
- **THEN** the static page MUST expose usable breadcrumb and previous/next navigation without requiring a backend or client-side router

### Requirement: Generated index rendering
The minimal builder SHALL render generated local and master index sections from resolved source metadata and official study-object scopes.

#### Scenario: Local index rendered
- **WHEN** a section landing page has rendered child pages
- **THEN** the static section page MUST include generated child index entries with labels, titles, summaries, and links in resolved order

#### Scenario: Master index rendered
- **WHEN** the root course index is built
- **THEN** the static root page MUST include generated master index entries for main ordered sections and appendices

#### Scenario: Study counts rendered without personal state
- **WHEN** official cards, quizzes, or prompts are scoped to rendered quanta
- **THEN** generated index data MUST expose official study-object counts for rendered quanta and MUST NOT include private review history, confidence ratings, personal mastery state, or spaced repetition history

### Requirement: Stable reference rendering
The minimal builder SHALL render validated `raya:` stable source references as static links to current generated page URLs.

#### Scenario: Stable content link rendered
- **WHEN** source Markdown links to a valid `raya:` page ID
- **THEN** the generated HTML MUST link to the current static URL for that page using a deployment-neutral relative path

#### Scenario: Stable alias link rendered
- **WHEN** source Markdown links to a valid alias declared by a rendered page
- **THEN** the generated HTML MUST link to the current static URL for the page that owns the alias
