## ADDED Requirements

### Requirement: Rich render artifact surfaces
Artifacts SHALL preserve rich rendering outputs as generated static resources and optional manifest-declared machine data without making rendered HTML the authority surface.

#### Scenario: Rich render resources present
- **WHEN** rich static rendering produces browser-facing support resources
- **THEN** those resources MUST be contained under the artifact static read path and MUST remain usable when `artifact/site/` is served directly

#### Scenario: Render support data declared
- **WHEN** rich static rendering produces machine-readable support data
- **THEN** `manifest.json` MUST declare the data path and artifact inspection MUST validate the declared file

#### Scenario: Rendered HTML remains non-authoritative
- **WHEN** future dynamic services or agents need course structure, navigation, indexes, links, or official learning objects
- **THEN** they MUST continue reading manifest-declared data rather than treating rich rendered HTML as canonical source truth
