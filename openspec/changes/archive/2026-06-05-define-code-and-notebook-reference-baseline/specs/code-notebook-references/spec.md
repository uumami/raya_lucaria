## ADDED Requirements

### Requirement: Code and notebook source support
Raya Lucaria SHALL define code and notebook files as authored source support material owned by learning quanta without rendering those files as course pages.

#### Scenario: Supported source directories
- **WHEN** a learning quantum directory contains `code/` or `notebooks/`
- **THEN** validation MUST treat those directories as source support material owned by that quantum

#### Scenario: Support directories do not render
- **WHEN** validation and build scan `code/` or `notebooks/`
- **THEN** files under those directories MUST NOT become rendered navigation entries, generated index entries, or page quanta

#### Scenario: Code is not an asset or official object
- **WHEN** a course contains runnable code or notebooks
- **THEN** source guidance and validation MUST keep them distinct from `_assets/` and `_official/`

### Requirement: Code and notebook reference validation
Raya Lucaria SHALL validate local Markdown references to supported code and notebook files before build.

#### Scenario: Valid script reference
- **WHEN** a rendered Markdown page links to an existing `.py` file under its own or accepted ancestor `code/` directory
- **THEN** validation MUST pass the reference and classify it as a code reference

#### Scenario: Valid notebook reference
- **WHEN** a rendered Markdown page links to an existing readable `.ipynb` file under its own or accepted ancestor `notebooks/` directory
- **THEN** validation MUST pass the reference and classify it as a notebook reference

#### Scenario: Missing support file
- **WHEN** a rendered Markdown page links to a missing code or notebook support file
- **THEN** validation MUST fail with an actionable diagnostic naming the source page and target

#### Scenario: Unsupported support path
- **WHEN** a rendered Markdown page links to code or notebook material under `_official/`, `_drafts/`, `_partials/`, `_assets/`, or outside the authored source tree
- **THEN** validation MUST fail unless a future accepted contract explicitly allows that reference type

### Requirement: Code and notebook artifact references
Glintstone SHALL expose referenced code and notebook files through generated artifact surfaces without treating rendered HTML as the authority.

#### Scenario: Reference data generated
- **WHEN** a course contains validated code or notebook references
- **THEN** the generated artifact MUST include manifest-declared reference data with page ID, source path, kind, format or language, hash, artifact path, browser path, and no-execution status

#### Scenario: Referenced files copied
- **WHEN** a code or notebook file is referenced by rendered content
- **THEN** the builder MUST copy it to artifact-level file storage and browser-facing static file storage

#### Scenario: Reference data remains machine authority
- **WHEN** agents, launchers, graph tools, or future execution managers need code and notebook reference metadata
- **THEN** they MUST read manifest-declared reference data rather than scraping rendered HTML

### Requirement: Static reference rendering
Glintstone SHALL render code and notebook references as static readable surfaces with deployment-neutral links.

#### Scenario: Static code reference renders
- **WHEN** a rendered page references a validated code file
- **THEN** the generated page MUST include a deployment-neutral link and MAY include a safe source excerpt without executing the file

#### Scenario: Static notebook reference renders
- **WHEN** a rendered page references a validated notebook file
- **THEN** the generated page MUST include a deployment-neutral link and MAY include a static notebook outline or source-cell preview without executing the notebook

#### Scenario: Static site serves references
- **WHEN** `artifact/site/` is served directly
- **THEN** referenced code and notebook files MUST be downloadable through relative URLs under the static read path

### Requirement: References do not execute
Code and notebook reference handling SHALL remain static-first and SHALL NOT execute scripts, notebook cells, kernels, or runtime commands.

#### Scenario: Build does not execute script
- **WHEN** a referenced `.py` file contains executable-looking code
- **THEN** validation, build, preview generation, and artifact inspection MUST NOT run that code

#### Scenario: Build does not execute notebook
- **WHEN** a referenced `.ipynb` file contains code cells or output metadata
- **THEN** validation, build, preview generation, and artifact inspection MUST NOT run notebook cells or trust notebook outputs

#### Scenario: Execution remains future work
- **WHEN** code and notebook references are present
- **THEN** the artifact MUST remain useful without `uv`, Docker, kernels, Pyodide, JupyterLite, marimo, remote runners, or `raya run`
