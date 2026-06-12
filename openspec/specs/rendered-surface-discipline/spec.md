# rendered-surface-discipline Specification

## Purpose
Defines the display boundary between readable student pages, compact support panels, static inspection surfaces, and machine-readable artifact data.
## Requirements
### Requirement: Rendered surface tiers
Glintstone SHALL classify generated rendered surfaces by audience and authority so normal pages remain readable while artifact data remains complete.

#### Scenario: Student-default surface
- **WHEN** Glintstone renders an ordinary course page
- **THEN** the generated page MUST prioritize authored learning content, navigation, generated indexes, stable links, local assets, and compact study/resource cues without dumping internal artifact metadata into the normal page flow

#### Scenario: Support-panel surface
- **WHEN** a rendered page has generated resource, code/notebook, runtime, execution, cache, official-object, or reviewed-output context useful to readers
- **THEN** Glintstone MUST expose only a compact status, label, summary, and deployment-neutral link by default unless a more detailed view is explicitly opened

#### Scenario: Inspection surface
- **WHEN** professors, contributors, or agents need to inspect detailed generated metadata
- **THEN** Glintstone MAY generate static inspection pages or equivalent static surfaces from manifest-declared artifact data without requiring a backend or treating those pages as course canon

#### Scenario: Machine-only surface
- **WHEN** agents, future services, launchers, graph tools, or execution tools need full generated data
- **THEN** they MUST read `manifest.json`, manifest-declared `data/*.json`, and copied artifact files rather than scraping normal rendered HTML as authority

### Requirement: Default pages avoid internal metadata leakage
Default rendered pages SHALL NOT expose verbose build, runtime, execution, cache, reference, freshness, hash, or copied-file internals unless those details are necessary student-facing content.

#### Scenario: Normal page hides verbose internals
- **WHEN** a course page has reference data, runtime profiles, execution policies, cache keys, reviewed-output freshness data, source hashes, artifact paths, or copied browser paths
- **THEN** the default rendered page MUST NOT dump those raw fields into the main reading flow

#### Scenario: Useful status remains visible
- **WHEN** generated metadata affects reader trust or available resources
- **THEN** the rendered page MUST still expose compact labels such as `not executed`, `reviewed`, `current`, resource kind, target label, or view/download links when relevant

#### Scenario: Machine data remains complete
- **WHEN** default pages hide verbose internals
- **THEN** the generated artifact MUST continue to emit the complete accepted manifest-declared data needed for inspection, agents, and future dynamic domains

### Requirement: Static inspection remains passive
Inspection surfaces SHALL be static views over generated artifact data and SHALL NOT execute code, notebooks, kernels, runtime profiles, package managers, Docker, cache refreshes, or output freezing.

#### Scenario: Inspection served statically
- **WHEN** an inspection or gallery page is served from `artifact/site/`
- **THEN** it MUST work as static files with deployment-neutral links and no backend dependency

#### Scenario: Inspection does not execute
- **WHEN** a user opens an inspection surface, default page, gallery page, copied referenced file, or copied reviewed file
- **THEN** Glintstone MUST NOT execute scripts, notebooks, kernels, `uv`, Docker, package installers, cache refreshes, or `raya outputs freeze`

### Requirement: Fixture gallery surface
The repository SHALL provide a static examples/gallery surface for quickly opening representative rendered fixtures without making fixture content canonical pedagogy.

#### Scenario: Gallery lists fixture artifacts
- **WHEN** repository examples are built for preview or e2e verification
- **THEN** the gallery MUST link to representative fixture `artifact/site/` entrypoints with labels describing the behavior each fixture demonstrates

#### Scenario: Gallery labels fixture authority
- **WHEN** a contributor opens the examples/gallery surface
- **THEN** the page MUST identify entries as fixture material and point readers to foundation docs and accepted specs for authority

#### Scenario: Gallery works through static read path
- **WHEN** the examples/gallery surface is served from local static hosting
- **THEN** links to fixture pages, referenced files, reviewed files, and rendered support resources MUST work through deployment-neutral static paths

### Requirement: Student-default visual readability
Student-default rendered pages SHALL be visually organized for sustained reading and review before additional pedagogy surfaces are added.

#### Scenario: Reading flow remains primary
- **WHEN** Glintstone renders a normal course page
- **THEN** authored content, page title, navigation, generated indexes, and compact study/resource cues MUST be easier to find than fixture labels, inspection links, or internal implementation details

#### Scenario: Compact panels do not dominate
- **WHEN** a page includes support panels for references, reviewed output, runtime metadata, cache metadata, or official objects
- **THEN** those panels MUST remain visually secondary to the authored learning content while preserving required status and deployment-neutral links

#### Scenario: No visual overlap
- **WHEN** representative student-default pages are rendered at desktop and mobile-sized viewports
- **THEN** navigation, headings, content, support panels, and footer or inspection links MUST NOT overlap or obscure each other

### Requirement: Preview surface discoverability
Rendered artifacts SHALL expose preview and inspection affordances for reviewers without turning audit surfaces into the student reading flow.

#### Scenario: Inspection reachable from preview workflow
- **WHEN** a contributor or professor starts the accepted preview workflow for an artifact with inspection output
- **THEN** the workflow MUST expose the inspection URL through CLI output, gallery links, or another reviewer-facing surface outside the main reading flow

#### Scenario: Student page not inspection-first
- **WHEN** a student-default page is opened directly
- **THEN** inspection details MUST NOT be placed above authored content or primary navigation

#### Scenario: Machine authority preserved
- **WHEN** preview and inspection affordances are added
- **THEN** agents and future services MUST continue to read `manifest.json`, manifest-declared `data/*.json`, and copied files rather than treating screenshots or rendered HTML as authority
