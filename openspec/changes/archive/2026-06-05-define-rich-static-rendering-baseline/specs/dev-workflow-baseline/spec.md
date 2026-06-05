## ADDED Requirements

### Requirement: Rich rendering verification
Changes that affect rich static rendering SHALL include representative contract and e2e verification.

#### Scenario: Rich rendering contracts changed
- **WHEN** a change modifies Markdown rendering, math rendering, code block rendering, callouts, footnotes, heading anchors, page table of contents, or rich render support resources
- **THEN** verification MUST include contract tests for generated HTML, link/asset rewriting, artifact validation, and static read-path behavior

#### Scenario: Rich rendering e2e fixture
- **WHEN** rich static rendering behavior changes
- **THEN** verification MUST include a representative fixture that renders at least one root page and one nested page through `artifact/site/`

#### Scenario: Rich rendering Docker coverage
- **WHEN** rich static rendering introduces parser, highlighter, math, or renderer dependencies
- **THEN** verification MUST include the Docker Compose reference workflow or explicitly document any Docker workflow gap

### Requirement: Rich rendering documentation
Changes that introduce or modify rich static rendering SHALL update the documentation surfaces authors, learners, contributors, and agents use.

#### Scenario: Rich rendering role docs updated
- **WHEN** rich rendering changes author-facing syntax or student-facing rendered behavior
- **THEN** documentation tasks MUST update separate English and Spanish role documentation for contributors/collaborators, professors, students, and agents or explicitly track any deferred role-language page

#### Scenario: Rich rendering foundation and rendered docs updated
- **WHEN** the accepted rich rendering baseline changes
- **THEN** documentation tasks MUST update the rendering execution plan or other relevant foundation docs and keep the live rendered docs tree aligned
