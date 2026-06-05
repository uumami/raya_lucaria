## MODIFIED Requirements

### Requirement: Future render capabilities use the static resource namespace
Future browser-facing renderer capabilities SHALL use the `site/_raya/` namespace when they need generated browser resources.

#### Scenario: Future math or component assets
- **WHEN** a later proposal adds math rendering, syntax highlighting, public browser data, or interactive component assets
- **THEN** those browser-facing resources MUST fit under `site/_raya/` or explicitly update the static resource contract

#### Scenario: Rich render support resources
- **WHEN** rich static rendering needs browser-facing support resources such as local math support, style sheets, syntax highlighting assets, or small renderer data files
- **THEN** those resources MUST be generated under `site/_raya/` and referenced by deployment-neutral relative URLs

## ADDED Requirements

### Requirement: Render support resources are generated output
Browser-facing render support resources SHALL be treated as generated artifact resources rather than course source truth.

#### Scenario: Render resources are not source
- **WHEN** the builder writes rich rendering support files under `artifact/site/_raya/`
- **THEN** those files MUST be considered generated output and MUST NOT be edited as canonical course source

#### Scenario: Render resources work from static read path
- **WHEN** `artifact/site/` is served directly
- **THEN** rich rendering support resources MUST resolve without relying on sibling artifact directories, an absolute deployment root, a CDN, or a backend route
