## MODIFIED Requirements

### Requirement: Static code and notebook reference output
The minimal static builder SHALL build validated code and notebook references into portable static artifacts without executing them and SHALL render default page summaries according to rendered-surface discipline.

#### Scenario: Code reference copied and linked
- **WHEN** a rendered page references a validated code file
- **THEN** the builder MUST copy the file to artifact-level file storage, copy it to `site/_raya/files/`, and rewrite the rendered link to a deployment-neutral browser path

#### Scenario: Notebook reference copied and linked
- **WHEN** a rendered page references a validated notebook file
- **THEN** the builder MUST copy the file to artifact-level file storage, copy it to `site/_raya/files/`, and rewrite the rendered link to a deployment-neutral browser path

#### Scenario: Reference panel rendered compactly
- **WHEN** a page has validated code or notebook references
- **THEN** the generated HTML MUST expose those references through a compact static resource panel or equivalent readable surface with kind, label, no-execution status, and deployment-neutral view/download links

#### Scenario: Reference internals stay out of default flow
- **WHEN** a page has validated code or notebook references
- **THEN** the default rendered page MUST NOT dump raw reference JSON, source hashes, artifact storage paths, browser storage paths, runtime profile internals, or cache keys into the main reading flow

#### Scenario: Preview does not execute
- **WHEN** a reference panel or preview is generated for code or notebook files
- **THEN** the builder MUST NOT execute scripts, notebook cells, kernels, or runtime commands

## ADDED Requirements

### Requirement: Student-default page shell
The minimal builder SHALL render ordinary course pages as student-default surfaces with compact generated support rather than exhaustive internal metadata displays.

#### Scenario: Page shell uses student defaults
- **WHEN** a course page is built
- **THEN** the generated HTML MUST prioritize title, authored content, breadcrumbs, navigation, generated indexes, local assets, and compact support panels

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

#### Scenario: Examples gallery links fixtures
- **WHEN** repository example fixtures are built
- **THEN** the repository MUST provide a static gallery or equivalent page linking to representative fixture entrypoints and naming the behavior each fixture demonstrates

#### Scenario: Gallery does not define pedagogy
- **WHEN** the examples gallery is rendered
- **THEN** it MUST label entries as fixture material and MUST NOT present fixture content as canonical pedagogy or architecture
