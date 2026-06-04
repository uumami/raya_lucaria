## ADDED Requirements

### Requirement: Ordered content verification
Changes that affect ordered content, generated indexes, stable references, or static navigation SHALL include focused contract and e2e verification.

#### Scenario: Ordered content contracts changed
- **WHEN** a change modifies ordered source conventions, page metadata, generated index behavior, stable `raya:` links, or navigation artifact data
- **THEN** verification MUST include contract tests for source validation, metadata parsing, stable reference resolution, generated navigation data, and generated index data

#### Scenario: Rendered index behavior changed
- **WHEN** a change modifies generated local indexes, master indexes, breadcrumbs, previous/next links, or stable rendered links
- **THEN** verification MUST include a representative static-read-path e2e fixture that renders those behaviors from source content

### Requirement: Ordered content documentation
Changes that introduce or modify the ordered authoring model SHALL update role documentation for affected audiences.

#### Scenario: Role docs updated
- **WHEN** ordered content, generated indexes, stable IDs, or authoring metadata change
- **THEN** documentation tasks MUST update separate English and Spanish role documentation for contributors/collaborators, professors, students, and agents or explicitly track any deferred role-language page

#### Scenario: Documentation includes source and rendered views
- **WHEN** role documentation explains ordered content behavior
- **THEN** it MUST show both the source-tree authoring model and the rendered student-facing result so readers do not confuse filename mechanics with student navigation labels
