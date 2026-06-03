## ADDED Requirements

### Requirement: Documentation impact in change workflow
The development workflow SHALL require documentation impact to be considered for every substantial change.

#### Scenario: Proposal documents documentation impact
- **WHEN** a proposal is created for a change that affects behavior, contracts, commands, rendering, deployment, pedagogy, authority boundaries, or user-facing workflows
- **THEN** the proposal MUST identify affected documentation audiences or explicitly state that no documentation update is needed

#### Scenario: Tasks include documentation work
- **WHEN** a proposal identifies documentation impact
- **THEN** the task list MUST include the smallest appropriate documentation updates and any required documentation checks

### Requirement: Documentation hygiene checks
The development workflow SHALL include focused documentation hygiene checks when a change creates or updates documentation, specs, or rendered documentation fixtures.

#### Scenario: Specs are updated
- **WHEN** a change creates or updates current OpenSpec specs
- **THEN** verification MUST check that current specs do not retain `Purpose: TBD` placeholders

#### Scenario: Documentation fixtures are added
- **WHEN** a change adds rendered documentation or documentation fixtures
- **THEN** verification MUST check that the fixture is labeled as documentation or fixture material and remains separate from class/course examples

#### Scenario: Role documentation is updated
- **WHEN** a change creates or updates documentation for contributors/collaborators, professors, students, or agents
- **THEN** verification MUST check that separate English and Spanish role directories with index pages are present or that any deferred language version is tracked
