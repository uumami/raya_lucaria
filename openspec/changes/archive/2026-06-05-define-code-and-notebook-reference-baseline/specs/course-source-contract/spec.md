## ADDED Requirements

### Requirement: Code and notebook support directories
The source course contract SHALL support `code/` and `notebooks/` directories as authored support material owned by rendered learning quanta.

#### Scenario: Quantum-owned code directory
- **WHEN** a rendered quantum directory contains `code/`
- **THEN** validation MUST treat files under `code/` as source support material for that quantum rather than rendered content

#### Scenario: Quantum-owned notebook directory
- **WHEN** a rendered quantum directory contains `notebooks/`
- **THEN** validation MUST treat files under `notebooks/` as source support material for that quantum rather than rendered content

#### Scenario: Support owner has index page
- **WHEN** `code/` or `notebooks/` is added under a learning quantum directory
- **THEN** that quantum MUST be represented by a normalized zero index page such as `0_index.md`

#### Scenario: Root source code unsupported
- **WHEN** a course declares a root authored `code` or `notebooks` configuration field
- **THEN** validation MUST fail or ignore it according to the source-course contract and tell authors to colocate support material under `course/`
