## ADDED Requirements

### Requirement: CLI-initialized source course
Courses created by the CLI init workflow SHALL satisfy the baseline source course contract without depending on legacy names or renderer assumptions.

#### Scenario: Initialized source shape
- **WHEN** a course is created by `raya course init <path>`
- **THEN** it MUST use `raya.yaml`, `content/`, optional `assets/`, and optional `official/` according to the current source contract

#### Scenario: Initialized source is not canonical pedagogy
- **WHEN** generated starter content is read
- **THEN** it MUST be clear that the content is replaceable scaffold and not required pedagogy or architecture
