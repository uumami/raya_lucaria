## MODIFIED Requirements

### Requirement: Course init command
The system SHALL provide a CLI workflow for creating a minimal source course tree from an explicit target path.

#### Scenario: Initialize new course
- **WHEN** a user runs `raya course init <path>` against a missing or empty directory
- **THEN** the command MUST create `raya.yaml`, `content/0_index.md`, `assets/`, `official/cards/`, `official/quizzes/`, and `official/prompts/`

## ADDED Requirements

### Requirement: Initialized ordered scaffold
Course init SHALL create starter source content that follows the blessed ordered source convention without defining course canon by accident.

#### Scenario: Root index metadata created
- **WHEN** `raya course init <path>` creates starter content
- **THEN** `content/0_index.md` MUST include minimal frontmatter needed for a published root index and starter prose labeled as replaceable scaffold

#### Scenario: Scaffold uses canonical prefix style
- **WHEN** `raya course init <path>` creates ordered starter files or directories beyond the root index
- **THEN** those entries MUST use the canonical unpadded prefix style such as `1_` and `2_`
