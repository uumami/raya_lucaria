## MODIFIED Requirements

### Requirement: Student-default page shell
The minimal builder SHALL render ordinary course pages as student-default surfaces with readable visual hierarchy and compact generated support rather than exhaustive internal metadata displays.

#### Scenario: Page shell uses student defaults
- **WHEN** a course page is built
- **THEN** the generated HTML MUST prioritize title, authored content, breadcrumbs, navigation, generated indexes, local assets, and compact support panels

#### Scenario: Page shell avoids instructional clutter
- **WHEN** a student-default page is rendered
- **THEN** the generated page MUST avoid visible in-page explanations of internal renderer mechanics, testing behavior, fixture mechanics, keyboard shortcuts, or artifact implementation details unless that text is authored course content

#### Scenario: Page shell has stable layout regions
- **WHEN** a student-default page contains navigation, generated indexes, support panels, or reviewed-output summaries
- **THEN** the generated HTML and CSS MUST keep those regions visually distinct and responsive without overlapping authored content across representative desktop and mobile-sized viewports

#### Scenario: Runtime and execution metadata summarized
- **WHEN** a page has generated runtime, execution, or cache metadata associated with its referenced targets
- **THEN** the default page MUST show at most compact reader-relevant status and MUST keep verbose policy, profile, cache, hash, and path internals in artifact data or inspection surfaces

#### Scenario: Reviewed output summarized
- **WHEN** a page has current reviewed output associated with a referenced target
- **THEN** the default page MUST show a compact reviewed label, target label, and deployment-neutral links or short excerpts without dumping freshness internals into the main reading flow

#### Scenario: Machine data remains inspectable
- **WHEN** compact support panels are rendered
- **THEN** artifact inspection and manifest-declared data MUST continue to expose the complete accepted metadata for tools and audits

### Requirement: Static inspection and examples gallery output
The minimal builder or repository preview workflow SHALL provide static inspection or gallery output for contributors without requiring a dynamic service.

#### Scenario: Inspection pages generated from artifact data
- **WHEN** implementation generates inspection pages for a fixture or artifact
- **THEN** those pages MUST be derived from manifest-declared artifact data and MUST use deployment-neutral links to generated pages, referenced files, assets, and reviewed files

#### Scenario: Inspection pages remain audit surfaces
- **WHEN** an inspection page is generated
- **THEN** it MUST identify itself as an inspection surface and MUST NOT present audit metadata as student-default course canon

#### Scenario: Examples gallery links fixtures
- **WHEN** repository example fixtures are built
- **THEN** the repository MUST provide a static gallery or equivalent page linking to representative fixture entrypoints and naming the behavior each fixture demonstrates

#### Scenario: Examples gallery links inspection pages
- **WHEN** a representative fixture artifact has an inspection page
- **THEN** the examples gallery MUST provide a deployment-neutral link to that inspection page or document why the fixture has no inspection surface

#### Scenario: Gallery does not define pedagogy
- **WHEN** the examples gallery is rendered
- **THEN** it MUST label entries as fixture material and MUST NOT present fixture content as canonical pedagogy or architecture

#### Scenario: Gallery layout remains reviewable
- **WHEN** the examples gallery is served through local static hosting
- **THEN** its fixture labels, entrypoint links, inspection links, and authority notice MUST remain visible without text overlap across representative desktop and mobile-sized viewports
