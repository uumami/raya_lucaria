## MODIFIED Requirements

### Requirement: Static reference rendering
Glintstone SHALL render code and notebook references as compact static resource surfaces with deployment-neutral links while keeping complete metadata in manifest-declared artifact data.

#### Scenario: Static code reference renders
- **WHEN** a rendered page references a validated code file
- **THEN** the generated page MUST include a compact resource entry with a deployment-neutral link and MAY include a safe source excerpt without executing the file

#### Scenario: Static notebook reference renders
- **WHEN** a rendered page references a validated notebook file
- **THEN** the generated page MUST include a compact resource entry with a deployment-neutral link and MAY include a static notebook outline or source-cell preview without executing the notebook

#### Scenario: Verbose reference data remains out of default page flow
- **WHEN** reference metadata includes source paths, artifact paths, browser paths, hashes, execution policy, runtime profile, cache keys, or reviewed-output linkage
- **THEN** default rendered pages MUST NOT dump those raw fields into the main reading flow and MUST leave complete data in manifest-declared artifact surfaces

#### Scenario: Static site serves references
- **WHEN** `artifact/site/` is served directly
- **THEN** referenced code and notebook files MUST be downloadable through relative URLs under the static read path

#### Scenario: Inspection can show full reference metadata
- **WHEN** a generated inspection surface includes reference details
- **THEN** it MUST derive those details from manifest-declared reference data rather than scraping the compact rendered panel
