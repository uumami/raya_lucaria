## Why

Raya Lucaria can initialize, validate, build, and inspect courses, but source validation still misses broken local links and missing local assets. The foundation explicitly calls these out as validation concerns, and catching them before build protects the static course path before richer rendering, graph, or UI work.

## What Changes

- Validate Markdown links in source content.
- Fail validation for broken local `.md` links under the configured `content/` directory.
- Fail validation for broken local asset references under the configured/default `assets/` directory.
- Ignore external URLs, `mailto:`, `tel:`, page fragments, and non-file schemes.
- Keep diagnostics actionable by naming the source Markdown file, field/link, and expected target.
- Include source content links in generated `data/links.json` in addition to navigation/parent links.
- Add fixture/tests for valid source links, broken source links, valid assets, and missing assets.

Minimum requirement: `raya validate <course>` catches broken local content links and asset references before `raya build`, and the builder exports valid content links into the artifact link index.

Growth path: future proposals can add backlinks, wikilinks, heading-anchor validation, cross-course links, bibliography/citation checks, static HTML link crawling, and Primeval Current graph UI.

## Capabilities

### New Capabilities

- `source-link-asset-validation`: validation rules for local Markdown links and local asset references in source course content.

### Modified Capabilities

- `course-source-contract`: require source validation to catch broken local content links and missing local assets.
- `minimal-static-builder`: require generated `data/links.json` to include valid source content links from Markdown.

## Impact

- Updates `packages/schema` course validation helpers.
- Updates `packages/static` link-index generation.
- Adds tests for valid and invalid local content links and asset references.
- Keeps renderer, graph UI, search, backend, identity, deployment, and personal study state out of scope.
