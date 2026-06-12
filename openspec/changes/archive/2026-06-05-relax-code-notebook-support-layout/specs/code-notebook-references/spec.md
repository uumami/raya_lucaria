## MODIFIED Requirements

### Requirement: Code and notebook source support
Raya Lucaria SHALL define linked code and notebook files as authored source support material classified by extension and owned by learning quanta without rendering those files as course pages.

#### Scenario: Supported linked extensions
- **WHEN** a rendered Markdown page links to a local `.py` or `.ipynb` file under its own learning quantum or accepted ancestor quantum
- **THEN** validation MUST treat the target as source support material classified by extension rather than by folder name

#### Scenario: Optional source folders
- **WHEN** a learning quantum contains ordinary folders such as `code/`, `notebooks/`, `scripts/`, `helpers/`, or `labs/`
- **THEN** validation MUST NOT require or reserve any of those folder names for code/notebook reference support

#### Scenario: Source support does not render
- **WHEN** validation and build scan linked or unlinked `.py` or `.ipynb` files under the authored source root
- **THEN** those files MUST NOT become rendered navigation entries, generated index entries, or page quanta

#### Scenario: Code is not an asset, official object, or reviewed output
- **WHEN** a course contains runnable code or notebooks
- **THEN** source guidance and validation MUST keep them distinct from `_assets/`, `_official/`, and `_reviewed/`

### Requirement: Code and notebook reference validation
Raya Lucaria SHALL validate local Markdown references to supported code and notebook files before build using extension, readable target checks, privacy checks, and ownership boundaries.

#### Scenario: Valid script reference
- **WHEN** a rendered Markdown page links to an existing `.py` file under its own learning quantum or accepted ancestor quantum
- **THEN** validation MUST pass the reference and classify it as a code reference

#### Scenario: Valid notebook reference
- **WHEN** a rendered Markdown page links to an existing readable `.ipynb` file under its own learning quantum or accepted ancestor quantum
- **THEN** validation MUST pass the reference and classify it as a notebook reference

#### Scenario: Missing support file
- **WHEN** a rendered Markdown page links to a missing code or notebook support file
- **THEN** validation MUST fail with an actionable diagnostic naming the source page and target

#### Scenario: Unsupported support path
- **WHEN** a rendered Markdown page links to code or notebook material under `_official/`, `_reviewed/`, `_drafts/`, `drafts/`, `_partials/`, `_assets/`, runtime support, or outside the authored source tree
- **THEN** validation MUST fail unless a future accepted contract explicitly allows that reference type

#### Scenario: Cross-quantum support reference
- **WHEN** a rendered Markdown page links to a `.py` or `.ipynb` target owned by a sibling or unrelated learning quantum
- **THEN** validation MUST fail unless a future accepted shared-support contract explicitly allows that reference type

### Requirement: Code and notebook artifact references
Glintstone SHALL expose referenced code and notebook files through generated artifact surfaces without treating rendered HTML as the authority.

#### Scenario: Reference data generated
- **WHEN** a course contains validated code or notebook references
- **THEN** the generated artifact MUST include manifest-declared reference data with page ID, source path, kind, format or language, hash, artifact path, browser path, and no-execution status

#### Scenario: Referenced files copied
- **WHEN** a code or notebook file is referenced by rendered content and validation accepts that reference
- **THEN** the builder MUST copy it to artifact-level file storage and browser-facing static file storage

#### Scenario: Unlinked support files are not copied
- **WHEN** a course contains `.py` or `.ipynb` files that no rendered Markdown page links to
- **THEN** the builder MUST NOT copy those files into reference artifact storage or list them in generated reference data

#### Scenario: Reference data remains machine authority
- **WHEN** agents, launchers, graph tools, or future execution managers need code and notebook reference metadata
- **THEN** they MUST read manifest-declared reference data rather than scraping rendered HTML
