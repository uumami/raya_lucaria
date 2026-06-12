## MODIFIED Requirements

### Requirement: Code and notebook reference verification
Changes that affect code or notebook reference behavior SHALL include representative contract and e2e verification.

#### Scenario: Reference behavior changed
- **WHEN** a change modifies code reference validation, notebook reference validation, reference copying, reference data, reference rendering, or static file paths
- **THEN** verification MUST include contract tests for validation, generated HTML, artifact data, artifact inspection, and static-read-path behavior

#### Scenario: Representative reference fixture
- **WHEN** code or notebook reference behavior changes
- **THEN** verification MUST include a representative fixture with at least one root or nested page referencing a script and a notebook through extension-based links that do not depend on mandatory `code/` or `notebooks/` support roots

#### Scenario: Optional folder compatibility fixture
- **WHEN** code or notebook reference behavior changes
- **THEN** verification MUST prove that existing `code/` or `notebooks/` folder names still work as ordinary author organization choices when linked references satisfy the ownership boundary

#### Scenario: Invalid reference fixtures
- **WHEN** code or notebook reference validation changes
- **THEN** verification MUST include invalid fixtures or equivalent tests for missing targets, malformed notebooks, private support paths, cross-quantum references, and path-escaping references

#### Scenario: Unlinked support fixture
- **WHEN** code or notebook reference copying behavior changes
- **THEN** verification MUST prove that unlinked `.py` and `.ipynb` files are not copied into generated reference artifact storage

### Requirement: Code and notebook reference documentation
Changes that introduce or modify code and notebook references SHALL update relevant foundation, rendered documentation, role guidance, and agent guidance.

#### Scenario: Role docs updated
- **WHEN** code or notebook reference behavior changes author-facing or student-facing workflows
- **THEN** separate English and Spanish role pages for contributors/collaborators, professors, students, and agents MUST be updated or explicitly marked as deferred

#### Scenario: Phase plan updated
- **WHEN** the accepted code and notebook reference baseline changes
- **THEN** `docs/foundation/17_rendering_execution_plan.md` or a more specific foundation document MUST be updated and kept aligned with rendered documentation

#### Scenario: Agent and proposal guidance updated
- **WHEN** code or notebook reference source-layout guidance changes
- **THEN** `AGENTS.md` and `openspec/config.yaml` MUST stop requiring special `code/` and `notebooks/` support roots and MUST describe extension-based linked support compactly
