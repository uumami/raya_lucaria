## ADDED Requirements

### Requirement: Unified source tree verification
Changes that affect the authored source root, support-directory conventions, official learning-object colocation, or colocated assets SHALL include focused contract and e2e verification.

#### Scenario: Unified source contract changed
- **WHEN** a change modifies `source: course`, unsupported source-root fields, `_official/`, `_assets/`, support path classification, or source-root behavior
- **THEN** verification MUST include contract tests for configuration resolution, source validation, support directory privacy, official object discovery, asset validation, and representative artifact generation

#### Scenario: Unified source static behavior changed
- **WHEN** a change modifies how unified source content renders, exports study seed data, copies assets, or creates browser-facing links
- **THEN** verification MUST include a representative static-read-path e2e fixture that exercises rendered pages, generated indexes, official object export, and colocated asset URLs

### Requirement: Unified source documentation
Changes that introduce or modify the unified authored source tree SHALL update the documentation surfaces that authors, learners, contributors, and agents use to understand course structure.

#### Scenario: Unified source role docs updated
- **WHEN** `source: course`, colocated `_official/`, colocated `_assets/`, or support-directory privacy changes
- **THEN** documentation tasks MUST update separate English and Spanish role documentation for contributors/collaborators, professors, students, and agents or explicitly track any deferred role-language page

#### Scenario: Unified source foundation docs updated
- **WHEN** the canonical source-course tree changes
- **THEN** documentation tasks MUST update the foundation course contract, system overview, documentation surface map, and OpenSpec config guidance as needed
