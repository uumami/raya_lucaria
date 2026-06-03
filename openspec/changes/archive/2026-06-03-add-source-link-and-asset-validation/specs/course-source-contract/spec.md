## ADDED Requirements

### Requirement: Source links and assets validate before build
The source course contract SHALL require local content links and local asset references to validate before build.

#### Scenario: Broken local source reference
- **WHEN** course validation scans Markdown content and finds a broken local `.md` link or missing local asset reference
- **THEN** validation MUST fail before the course can build successfully

#### Scenario: External source reference
- **WHEN** course validation scans Markdown content and finds an external URL or fragment-only link
- **THEN** validation MUST NOT require that link to exist as a local source file
