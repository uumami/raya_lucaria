## ADDED Requirements

### Requirement: Runtime support beside course source
The source course contract SHALL allow runtime support files beside the ordered authored `course/` tree without making those files course content.

#### Scenario: Runtime directory at course root
- **WHEN** a course includes a root-level `runtime/` directory
- **THEN** validation MUST treat it as private execution support metadata and MUST NOT render it as course content

#### Scenario: Python project files at course root
- **WHEN** a course includes root-level `pyproject.toml` or `uv.lock`
- **THEN** validation MUST treat those files as runtime support for reproducibility rather than course pages, assets, or official learning objects

#### Scenario: Runtime directory inside course source
- **WHEN** an ordered `course/` source tree contains a rendered page link into `runtime/` or another private runtime support path
- **THEN** validation MUST fail unless a future accepted contract explicitly exposes that path

#### Scenario: Runtime profile does not affect source order
- **WHEN** runtime profile metadata changes
- **THEN** source page order, generated navigation, stable page IDs, generated indexes, and official learning-object scope MUST remain derived from the ordered `course/` tree
