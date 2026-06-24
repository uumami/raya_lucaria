# Static Wikilink Resolution Design

## Goal

Bring the useful `main`-branch wikilink authoring pattern into the current static renderer without adopting the old Eleventy/Pagefind/Cytoscape stack.

## Design

Authors may write `[[target]]` or `[[target|label]]` in Markdown body text outside fenced code. The target resolves at validate/build time to exactly one rendered page by stable page ID, alias, page title, nav title, ordered filename stem, stripped filename stem, or source-relative path without `.md`. The rendered output is an ordinary local `<a>` link, and the resolved page contributes a normal explicit `content` edge to `links.json` and `graph.json`.

Resolution is static and course-local. Missing or ambiguous targets fail validation with actionable diagnostics. The browser does not resolve wikilinks, fetch link data, store graph state, or load an external graph/search renderer.

## Scope

In scope:

- Resolve `[[target]]` and `[[target|label]]` outside fenced code.
- Render wikilinks as deployment-neutral local links.
- Add resolved wikilinks as explicit content graph edges.
- Fail missing and ambiguous wikilinks before build succeeds.
- Document the feature in foundation and role docs.

Out of scope:

- Cross-course wikilinks.
- Browser-side wikilink resolution.
- Full-text search.
- Graph editing.
- Inferred related pages or recommendations.
