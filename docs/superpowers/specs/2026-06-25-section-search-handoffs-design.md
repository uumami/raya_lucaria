# Section Search Handoffs Design

## Context

The old `main` branch used richer search affordances, including section-like subresults, but depended on renderer assumptions that are no longer accepted here. The current branch already has static reader pages, a static Search workspace, a local SVG Graph workspace, official Practice/Tasks/Schedule workspaces, and URL-only page handoffs.

The missing UX capability is precision: a learner can search a page, but cannot see which public section matched before opening it. Browser verification also needs to prove that Search and related workspace handoffs first-paint useful focused states, not just that links exist in HTML.

## Scope

Add generated section-level search context to the static Search workspace.

- Build section records from already-rendered public article HTML.
- Use existing page heading anchors as section targets.
- Include section title, anchor, public sanitized search text, and a short sanitized snippet.
- Render section links under each page result.
- Let local `search.js` match, count, and reveal section matches for the active query.
- Keep page-level results as the primary unit; section matches are subresults, not separate pages.
- Add browser tests for the Search page and URL-only handoffs into Search, Graph, Practice, Tasks, and Schedule.

## Non-Goals

- No Pagefind, CDN, external search service, browser fetch, workers, storage, or indexed database.
- No browser-side MathJax conversion.
- No private source paths or generated internals in search text.
- No learner progress, recommendation, mastery, reminder, or personal due-state language.
- No graph layout rewrite or pixel-perfect graph testing.

## Data Model

Each search page payload may include:

```json
{
  "sections": [
    {
      "id": "authoring-matrix:matrix-norm-fixture",
      "title": "Matrix norm fixture",
      "url": "../../authoring-matrix/index.html#matrix-norm-fixture",
      "anchor": "matrix-norm-fixture",
      "search_text": "Matrix norm fixture Let I and x...",
      "search_snippet": "Matrix norm fixture Let I and x..."
    }
  ]
}
```

The artifact `data/search-index.json` should mirror the same public section records so agents and future static tools do not scrape rendered HTML. The schema remains static and local; if a page has no section headings, `sections` is an empty list.

## Rendering Behavior

The Search workspace remains a static HTML page with embedded JSON and local JavaScript. Each result keeps its page title, summary, metadata, official-object counts, and workspace actions. Below that, it shows a compact "Section matches" area with public section links.

When the query is empty, section links are available as scan targets. When the query is present, nonmatching section links are hidden and matching links remain visible. If a page matches only through a section, the page result stays visible and the context panel names the number of matching sections.

## Verification

Tests must prove:

- search payload and `data/search-index.json` include sanitized public sections,
- section URLs are deployment-neutral and anchored to rendered pages,
- raw TeX, MathJax internals, code blocks, private folders, artifact paths, and learner-state words do not leak,
- `search.js` has no storage, fetch, worker, external, or browser-side renderer calls,
- browser search for a section term reveals the matching page and section link,
- `_raya/search/index.html?page=<id>` shows the page-focus notice and Clear/Escape reset,
- graph/practice/tasks/schedule URL handoffs first-paint a focused state,
- desktop and mobile layouts do not introduce horizontal overflow.
