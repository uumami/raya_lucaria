## ADDED Requirements

### Requirement: Static code and notebook reference output
The minimal static builder SHALL build validated code and notebook references into portable static artifacts without executing them.

#### Scenario: Code reference copied and linked
- **WHEN** a rendered page references a validated code file
- **THEN** the builder MUST copy the file to artifact-level file storage, copy it to `site/_raya/files/`, and rewrite the rendered link to a deployment-neutral browser path

#### Scenario: Notebook reference copied and linked
- **WHEN** a rendered page references a validated notebook file
- **THEN** the builder MUST copy the file to artifact-level file storage, copy it to `site/_raya/files/`, and rewrite the rendered link to a deployment-neutral browser path

#### Scenario: Reference panel rendered
- **WHEN** a page has validated code or notebook references
- **THEN** the generated HTML MUST expose those references through a compact static panel or equivalent readable surface

#### Scenario: Preview does not execute
- **WHEN** a reference panel or preview is generated for code or notebook files
- **THEN** the builder MUST NOT execute scripts, notebook cells, kernels, or runtime commands

### Requirement: Code and notebook reference indexes
The minimal static builder SHALL generate machine-readable reference data when code or notebook references are present.

#### Scenario: References data emitted
- **WHEN** a build includes validated code or notebook references
- **THEN** the artifact MUST contain `data/references.json` or equivalent manifest-declared data for those references

#### Scenario: No references data omitted or empty
- **WHEN** a build has no code or notebook references
- **THEN** the artifact MUST either omit reference data from the manifest or emit an empty valid reference data file consistently
