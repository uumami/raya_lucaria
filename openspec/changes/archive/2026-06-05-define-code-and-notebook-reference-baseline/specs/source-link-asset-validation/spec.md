## ADDED Requirements

### Requirement: Local code reference validation
Source course validation SHALL validate local Markdown references to supported code files separately from content links and asset references.

#### Scenario: Valid colocated code reference
- **WHEN** a Markdown page links to an existing `.py` file under its own or accepted ancestor `code/` directory
- **THEN** validation MUST pass that reference and read the code file

#### Scenario: Missing code reference
- **WHEN** a Markdown page links to a missing `.py` file that would be a code reference
- **THEN** validation MUST fail with a diagnostic naming the source file and code target

#### Scenario: Code reference outside support root
- **WHEN** a Markdown page links to a `.py` file outside accepted `code/` support directories
- **THEN** validation MUST fail with an actionable diagnostic

### Requirement: Local notebook reference validation
Source course validation SHALL validate local Markdown references to supported notebook files separately from content links and asset references.

#### Scenario: Valid colocated notebook reference
- **WHEN** a Markdown page links to an existing readable `.ipynb` file under its own or accepted ancestor `notebooks/` directory
- **THEN** validation MUST pass that reference and read the notebook file

#### Scenario: Missing notebook reference
- **WHEN** a Markdown page links to a missing `.ipynb` file that would be a notebook reference
- **THEN** validation MUST fail with a diagnostic naming the source file and notebook target

#### Scenario: Unreadable notebook reference
- **WHEN** a Markdown page links to an `.ipynb` file that is not readable notebook JSON
- **THEN** validation MUST fail with an actionable diagnostic

### Requirement: Reference boundary diagnostics
Code and notebook reference validation SHALL preserve source privacy and produce diagnostics useful to humans and coding agents.

#### Scenario: Private support path blocked
- **WHEN** a Markdown page links to code or notebook material under `_official/`, `_drafts/`, `drafts/`, `_partials/`, or another private support path
- **THEN** validation MUST fail and explain that rendered pages cannot link directly into private support paths

#### Scenario: Cross-quantum support reference blocked
- **WHEN** a Markdown page links to another quantum's `code/` or `notebooks/` directory and cross-quantum support references are not accepted
- **THEN** validation MUST fail with a diagnostic explaining the ownership boundary

#### Scenario: External reference ignored
- **WHEN** a Markdown page links to an external code repository, external notebook URL, `mailto:`, `tel:`, or fragment-only target
- **THEN** validation MUST NOT require that target to exist locally or copy it into the artifact
