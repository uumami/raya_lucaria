## ADDED Requirements

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
