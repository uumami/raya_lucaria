## ADDED Requirements

### Requirement: Official learning object families
The source course contract SHALL support official cards, quizzes, prompts, examples, assignments, exams, projects, and tasks as course-owned learning objects.

#### Scenario: Recognize official object family
- **WHEN** validation scans official learning-object source
- **THEN** it MUST classify supported objects by family and preserve their official authority domain

### Requirement: Structured official objects
Official learning objects SHALL be structured enough to validate, index, export, and attach to learning quanta.

#### Scenario: Required object identity and scope
- **WHEN** an official learning object is validated
- **THEN** it MUST have a stable object identity, object type, learning-quantum scope, and content payload appropriate to its type

#### Scenario: Duplicate object identity
- **WHEN** two official learning objects declare the same stable ID in the same course
- **THEN** validation MUST fail and identify the duplicates

### Requirement: Retrieval practice hooks
Official cards, quizzes, and prompts SHALL expose retrieval-practice hooks without requiring personal study state.

#### Scenario: Official retrieval seed
- **WHEN** an official card, quiz, or prompt is indexed
- **THEN** the generated data MUST make it available as a retrieval-practice seed for the static artifact and future Rennala features

### Requirement: Authority labeling
Official learning objects SHALL be distinguishable from personal, shared, generated, and accepted material.

#### Scenario: Official label preserved
- **WHEN** an official learning object is indexed into artifact data
- **THEN** the object MUST retain an official authority label

#### Scenario: Generated object not official
- **WHEN** an agent-generated object is represented in future workflows
- **THEN** it MUST NOT be treated as official unless accepted through review

### Requirement: No personal review state in official source
The official learning-object baseline SHALL NOT require private review queues, spaced repetition history, confidence ratings, or mastery maps.

#### Scenario: Official cards without review history
- **WHEN** an official card validates
- **THEN** validation MUST NOT require user-specific review state

### Requirement: Study growth compatibility
Official learning-object indexes SHALL be compatible with future personal study contracts.

#### Scenario: Future review queue reference
- **WHEN** an official learning object is indexed
- **THEN** the index MUST include enough stable identity and scope information for a future review queue to reference it
