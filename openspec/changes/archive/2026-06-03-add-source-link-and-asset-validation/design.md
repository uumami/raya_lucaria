## Context

The current course validator checks config, content existence, Markdown/frontmatter readability, duplicate IDs, and official learning-object scope. It does not yet verify local Markdown links or asset references. The minimal builder can render Markdown links and generate navigation links, but it does not export source content links into `data/links.json`.

This change strengthens the static-first baseline without adding a UI, backend, or graph package.

## Goals / Non-Goals

**Goals:**

- Validate local Markdown links that target `.md` files under `content/`.
- Validate local asset links that target files under `assets/`.
- Ignore external URLs and in-page fragments.
- Keep diagnostics concrete and source-file-oriented.
- Include valid source content links in generated link indexes.
- Keep all tests isolated in temporary course directories.

**Non-Goals:**

- No wikilink syntax yet.
- No heading-anchor validation.
- No static HTML link crawler.
- No graph UI or backlink UI.
- No cross-course link resolution.
- No citation or bibliography validation.

## Decisions

### Decision: classify by target extension and source root

Markdown links ending in `.md` are treated as source content links. Other relative links are treated as asset references unless they are fragments or unsupported schemes.

Rationale: this matches the current minimal Markdown authoring surface and keeps the validation behavior simple.

Alternative considered: infer all non-MD links as rendered HTML routes. That would blur source validation with renderer behavior.

### Decision: validation stays in `packages/schema`

The link and asset checks are part of course source contract validation.

Rationale: broken local links and missing assets are source contract problems, not builder-specific rendering concerns.

### Decision: builder exports source content links only after validation

The builder already runs validation first. It can safely include source content links in `data/links.json` once validation guarantees targets exist.

Rationale: this gives Primeval Current useful seed data without implementing graph behavior.

## Risks / Trade-offs

- Simple Markdown regex may miss advanced Markdown edge cases -> acceptable for the baseline; richer parsing can come later.
- Asset classification by extension/root may need refinement -> tests cover the current explicit behavior.
- Fragment-only and external links are not deeply checked -> future proposals can add heading anchors and external link policies.

## Migration Plan

1. Add shared link extraction/classification helpers where practical.
2. Extend course validation for local content links and local assets.
3. Extend builder `data/links.json` generation with content links.
4. Add tests and update docs.

Rollback is simple during reset: remove the validation helpers, builder link-index changes, tests, docs, and change specs before archive.
