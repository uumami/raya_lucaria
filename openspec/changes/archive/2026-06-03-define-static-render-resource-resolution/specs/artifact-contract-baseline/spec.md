## ADDED Requirements

### Requirement: Self-contained static read resources
The artifact static read path SHALL contain the browser-facing resources needed for generated pages to use local course assets without relying on sibling artifact directories.

#### Scenario: Static site served directly
- **WHEN** the generated `site/` directory is served directly by static hosting
- **THEN** rendered pages MUST resolve local course assets through paths contained under `site/`

#### Scenario: Static site opened locally
- **WHEN** a generated HTML page under `site/` is opened from a local filesystem path
- **THEN** rendered local asset links MUST resolve through relative file paths contained under `site/`

### Requirement: Artifact-level assets remain inspectable
The artifact contract SHALL preserve artifact-level copied assets as inspectable generated output while allowing browser-facing copies under the static read path.

#### Scenario: Artifact assets inspected
- **WHEN** an artifact containing source assets is inspected
- **THEN** inspection MUST continue to recognize the artifact-level `assets/` directory as part of the generated artifact shape
