## ADDED Requirements

### Requirement: Code and notebook reference artifact surfaces
Artifacts SHALL expose referenced code and notebook files through manifest-centered generated surfaces without making rendered HTML authoritative.

#### Scenario: Reference manifest data declared
- **WHEN** a build generates code or notebook reference data
- **THEN** `manifest.json` MUST declare the reference data path

#### Scenario: Artifact file storage present
- **WHEN** a build copies referenced code or notebook files
- **THEN** artifact-level file storage MUST preserve those generated copies for inspection and future local tooling

#### Scenario: Browser file storage present
- **WHEN** a build copies referenced code or notebook files for static pages
- **THEN** browser-facing copies MUST live under the artifact static read path and use deployment-neutral URLs

#### Scenario: Rendered HTML remains non-authoritative for references
- **WHEN** future agents, graph tools, launchers, or execution managers need reference metadata
- **THEN** they MUST read manifest-declared reference data rather than rendered HTML
