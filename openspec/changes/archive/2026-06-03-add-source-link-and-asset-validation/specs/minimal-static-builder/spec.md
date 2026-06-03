## ADDED Requirements

### Requirement: Source content links in artifact index
The minimal builder SHALL include valid source content links in the generated link index.

#### Scenario: Content link exported
- **WHEN** a source Markdown page links to another valid source Markdown page
- **THEN** `data/links.json` MUST include a link entry from the source page quantum to the target page quantum with kind `content`

#### Scenario: Build stops on broken source links
- **WHEN** source validation fails because of a broken content link or missing local asset
- **THEN** the builder MUST stop before writing a successful artifact
