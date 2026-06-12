## ADDED Requirements

### Requirement: Static reviewed output panels
Rich static rendering SHALL display current reviewed execution output as compact static page content when a page references a reviewed target.

#### Scenario: Reviewed panel rendered
- **WHEN** a page references a target with current reviewed output
- **THEN** the generated HTML MUST show a reviewed-output panel with clear reviewed status, target label, and deployment-neutral links or excerpts for reviewed files

#### Scenario: Reviewed panel is data-backed
- **WHEN** a reviewed-output panel is rendered
- **THEN** its source metadata MUST come from manifest-declared reviewed output data rather than generated HTML being treated as authority

#### Scenario: Static panel does not execute
- **WHEN** a reviewed-output panel is generated or served
- **THEN** it MUST NOT execute code, notebooks, kernels, runtime profiles, or cache refreshes
