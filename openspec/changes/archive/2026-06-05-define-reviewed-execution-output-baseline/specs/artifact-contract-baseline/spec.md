## ADDED Requirements

### Requirement: Reviewed output artifact surfaces
Course artifacts SHALL expose reviewed execution outputs as manifest-declared data and copied files without making rendered HTML authoritative.

#### Scenario: Reviewed output data declared
- **WHEN** a build includes current reviewed output metadata
- **THEN** `manifest.json` MUST declare the reviewed output data path

#### Scenario: Reviewed artifact file storage present
- **WHEN** a build copies reviewed execution output files
- **THEN** artifact-level reviewed file storage MUST preserve those generated copies for inspection and future local tooling

#### Scenario: Reviewed browser file storage present
- **WHEN** a build copies reviewed execution output files for static pages
- **THEN** browser-facing reviewed copies MUST live under the artifact static read path and use deployment-neutral URLs

#### Scenario: Source reviewed output remains canonical
- **WHEN** reviewed output is copied into an artifact
- **THEN** the source `_reviewed/` metadata and files MUST remain the authority for reviewed output unless a future contract defines another trust surface
