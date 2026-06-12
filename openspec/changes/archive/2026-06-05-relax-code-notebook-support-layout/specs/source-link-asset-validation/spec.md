## MODIFIED Requirements

### Requirement: Local code reference validation
Source course validation SHALL validate local Markdown references to supported code files by extension and ownership boundary, separately from content links and asset references.

#### Scenario: Valid colocated code reference
- **WHEN** a Markdown page links to an existing `.py` file under its own learning quantum or an accepted ancestor quantum
- **THEN** validation MUST pass that reference and read the code file

#### Scenario: Valid ordinary folder code reference
- **WHEN** a Markdown page links to an existing `.py` file under an ordinary folder such as `scripts/`, `helpers/`, `labs/`, or `code/` inside its own learning quantum or accepted ancestor quantum
- **THEN** validation MUST pass that reference without requiring the folder name to be `code`

#### Scenario: Missing code reference
- **WHEN** a Markdown page links to a missing `.py` file that would be a code reference
- **THEN** validation MUST fail with a diagnostic naming the source file and code target

#### Scenario: Code reference outside ownership boundary
- **WHEN** a Markdown page links to a `.py` file owned by a sibling quantum, unrelated quantum, runtime support path, or path outside the authored source tree
- **THEN** validation MUST fail with an actionable diagnostic explaining the ownership or path boundary

### Requirement: Local notebook reference validation
Source course validation SHALL validate local Markdown references to supported notebook files by extension, readable notebook source, and ownership boundary, separately from content links and asset references.

#### Scenario: Valid colocated notebook reference
- **WHEN** a Markdown page links to an existing readable `.ipynb` file under its own learning quantum or an accepted ancestor quantum
- **THEN** validation MUST pass that reference and read the notebook file

#### Scenario: Valid ordinary folder notebook reference
- **WHEN** a Markdown page links to an existing readable `.ipynb` file under an ordinary folder such as `notebooks/`, `labs/`, `examples/`, or `code/` inside its own learning quantum or accepted ancestor quantum
- **THEN** validation MUST pass that reference without requiring the folder name to be `notebooks`

#### Scenario: Missing notebook reference
- **WHEN** a Markdown page links to a missing `.ipynb` file that would be a notebook reference
- **THEN** validation MUST fail with a diagnostic naming the source file and notebook target

#### Scenario: Unreadable notebook reference
- **WHEN** a Markdown page links to an `.ipynb` file that is not readable notebook JSON
- **THEN** validation MUST fail with an actionable diagnostic

#### Scenario: Notebook reference outside ownership boundary
- **WHEN** a Markdown page links to an `.ipynb` file owned by a sibling quantum, unrelated quantum, runtime support path, or path outside the authored source tree
- **THEN** validation MUST fail with an actionable diagnostic explaining the ownership or path boundary

### Requirement: Reference boundary diagnostics
Code and notebook reference validation SHALL preserve source privacy and produce diagnostics useful to humans and coding agents.

#### Scenario: Private support path blocked
- **WHEN** a Markdown page links to code or notebook material under `_official/`, `_reviewed/`, `_assets/`, `_drafts/`, `drafts/`, `_partials/`, or another private support path
- **THEN** validation MUST fail and explain that rendered pages cannot link directly into private support paths for code/notebook references

#### Scenario: Cross-quantum support reference blocked
- **WHEN** a Markdown page links to another quantum's `.py` or `.ipynb` source support and cross-quantum support references are not accepted
- **THEN** validation MUST fail with a diagnostic explaining the ownership boundary

#### Scenario: External reference ignored
- **WHEN** a Markdown page links to an external code repository, external notebook URL, `mailto:`, `tel:`, or fragment-only target
- **THEN** validation MUST NOT require that target to exist locally or copy it into the artifact
