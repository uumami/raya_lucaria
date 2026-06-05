## ADDED Requirements

### Requirement: Static file namespace for code and notebook references
Browser-facing generated copies of referenced code and notebook files SHALL use the `site/_raya/files/` namespace.

#### Scenario: Referenced file uses static namespace
- **WHEN** the builder copies a referenced code or notebook file for browser download
- **THEN** the copied file MUST live under `artifact/site/_raya/files/`

#### Scenario: Referenced file URL is deployment-neutral
- **WHEN** a rendered page links to a copied code or notebook file
- **THEN** the URL MUST be relative to the generated page and MUST NOT require an absolute deployment root, backend route, CDN, or sibling artifact directory

#### Scenario: Static namespace remains generated output
- **WHEN** `artifact/site/_raya/files/` exists
- **THEN** those files MUST be treated as generated output and MUST NOT become course source truth
