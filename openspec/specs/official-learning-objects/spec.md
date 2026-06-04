# official-learning-objects Specification

## Purpose
Defines official course-owned learning object families, authority labels, source validation, and artifact export without personal study state.
## Requirements
### Requirement: Official learning object families
The source course contract SHALL support official cards, quizzes, prompts, examples, assignments, exams, projects, and tasks as course-owned learning objects from source-root and quantum-colocated `_official/` locations inside the authored source tree.

#### Scenario: Recognize colocated official object family
- **WHEN** validation scans `_official/cards/1_rate_of_change.yaml` under a rendered learning quantum
- **THEN** it MUST classify the object as an official card and preserve its official authority domain

#### Scenario: Recognize source-root official object family
- **WHEN** validation scans `course/_official/cards/1_course_card.yaml`
- **THEN** it MUST classify the object as an official card and preserve its official authority domain

### Requirement: Structured official objects
Official learning objects SHALL be structured enough to validate, index, export, and attach to learning quanta.

#### Scenario: Required object identity and content
- **WHEN** an official learning object is validated
- **THEN** it MUST have a stable object identity, object type, official authority label, and content payload appropriate to its type

#### Scenario: Scope inferred for colocated object
- **WHEN** an official learning object lives under a rendered quantum's `_official/` directory and omits `scope.quantum`
- **THEN** validation MUST infer `scope.quantum` from the nearest rendered directory landing page

#### Scenario: Explicit colocated scope must match
- **WHEN** a colocated official learning object declares `scope.quantum`
- **THEN** validation MUST require that scope to match the nearest rendered quantum

#### Scenario: Course-level official object requires scope
- **WHEN** an official learning object lives under source-root `_official/`
- **THEN** validation MUST require explicit `scope.quantum`

#### Scenario: Duplicate object identity
- **WHEN** two official learning objects declare the same stable ID in the same course across source-root or quantum-colocated official-object locations
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

### Requirement: Colocated official source
Official learning objects SHOULD be authored under `_official/` beside the learning quantum they support, and validation SHALL treat that source as canonical for new courses.

#### Scenario: Colocated object exports source path
- **WHEN** a colocated official object is exported into artifact data
- **THEN** generated official data MUST include its resolved learning-quantum scope and source path without exposing order prefixes as object identity

#### Scenario: Colocated object contributes study counts
- **WHEN** a colocated official card, quiz, or prompt scopes to a rendered quantum
- **THEN** generated local and master indexes MUST include that object in official study-object counts for the quantum and its ancestors

#### Scenario: Private official source does not render
- **WHEN** `_official/` contains YAML or JSON official objects
- **THEN** the static builder MUST NOT render those files as public pages

