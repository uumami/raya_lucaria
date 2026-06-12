# code-notebook-references Specification

## Purpose
Defines the static-first contract for authored code and notebook support files: where they live in course source, how local Markdown links validate, how Glintstone copies and renders them, and how artifacts expose reference metadata without executing scripts or notebook cells.
## Requirements
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

### Requirement: References expose reviewed output status
Code and notebook reference surfaces SHALL expose reviewed output status when current reviewed output exists for a referenced target.

#### Scenario: Referenced script has reviewed output
- **WHEN** a rendered page references a script target with current reviewed output
- **THEN** generated reference metadata MUST associate that reference with reviewed output status and reviewed output artifact paths

#### Scenario: Referenced notebook has reviewed output
- **WHEN** a rendered page references a notebook target with current reviewed output
- **THEN** generated reference metadata MUST associate that reference with reviewed output status and reviewed output artifact paths without mutating the authored source notebook

#### Scenario: Reference preview remains non-executing
- **WHEN** reference metadata includes reviewed output status
- **THEN** validation, build, preview generation, and artifact inspection MUST NOT execute the referenced target

### Requirement: Static reference rendering
Glintstone SHALL render code and notebook references as compact static resource surfaces with deployment-neutral links while keeping complete metadata in manifest-declared artifact data.

#### Scenario: Static code reference renders
- **WHEN** a rendered page references a validated code file
- **THEN** the generated page MUST include a compact resource entry with a deployment-neutral link and MAY include a safe source excerpt without executing the file

#### Scenario: Static notebook reference renders
- **WHEN** a rendered page references a validated notebook file
- **THEN** the generated page MUST include a compact resource entry with a deployment-neutral link and MAY include a static notebook outline or source-cell preview without executing the notebook

#### Scenario: Verbose reference data remains out of default page flow
- **WHEN** reference metadata includes source paths, artifact paths, browser paths, hashes, execution policy, runtime profile, cache keys, or reviewed-output linkage
- **THEN** default rendered pages MUST NOT dump those raw fields into the main reading flow and MUST leave complete data in manifest-declared artifact surfaces

#### Scenario: Static site serves references
- **WHEN** `artifact/site/` is served directly
- **THEN** referenced code and notebook files MUST be downloadable through relative URLs under the static read path

#### Scenario: Inspection can show full reference metadata
- **WHEN** a generated inspection surface includes reference details
- **THEN** it MUST derive those details from manifest-declared reference data rather than scraping the compact rendered panel

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

### Requirement: Reference execution metadata hooks
Code and notebook references SHALL expose execution policy and runtime profile metadata hooks while preserving static Phase 2 behavior.

#### Scenario: Reference default policy
- **WHEN** a referenced code or notebook file has no explicit execution metadata
- **THEN** generated reference or execution metadata MUST record policy `never` and status `not-executed`

#### Scenario: Reference profile binding
- **WHEN** a referenced code or notebook file declares a runtime profile binding through accepted metadata
- **THEN** validation MUST require the named runtime profile to exist and MUST NOT execute the referenced file

#### Scenario: Reference cache metadata
- **WHEN** a referenced code or notebook file declares policy `cache`
- **THEN** generated cache metadata MUST include a cache key for the reference without executing the target or refreshing cached output

#### Scenario: Reference always policy
- **WHEN** a referenced code or notebook file declares policy `always`
- **THEN** validation MUST require the declaration to be target-specific and generated metadata MUST still record status `not-executed` in Phase 3

### Requirement: References as executable targets
Code and notebook references SHALL become executable targets only when selected through the accepted local execution command.

#### Scenario: Referenced script selected
- **WHEN** a user selects a validated `.py` reference with `raya run`
- **THEN** local execution MUST resolve the reference metadata and execute the source script according to its policy and profile

#### Scenario: Referenced notebook selected
- **WHEN** a user selects a validated `.ipynb` reference with `raya run`
- **THEN** local execution MUST resolve the reference metadata and execute a generated copy or output notebook without mutating the authored source notebook

#### Scenario: Static preview not execution
- **WHEN** a page renders a code or notebook preview
- **THEN** the preview MUST NOT be treated as evidence that the target has executed

#### Scenario: Missing reference target refuses execution
- **WHEN** a user selects a code or notebook target that does not match a validated reference or accepted source path
- **THEN** local execution MUST fail with an actionable diagnostic
