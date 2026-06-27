# Graph Page Sections Design

## Context

The static Graph workspace is becoming the main orientation surface for course structure. It already shows selected-page metadata, study objects, key objects, relationship summaries, relationship walkthroughs, and reading-path links. Search already indexes public section anchors for rendered pages, including ordinary headings, numbered objects, and proofs.

Old `main` exposed stronger jump/navigation affordances through anchored pages and heading links. The current graph detail panel does not yet give students a compact way to jump into ordinary public sections on the selected page. That makes graph exploration good for page-level navigation but weaker for learning workflows that ask, "where in this page is the relevant explanation?"

## Decision

Add a `Page sections` block to the selected-page graph detail panel. It will list public section anchors already derived from rendered article HTML and search records. Each item links to the rendered page URL plus section anchor.

The graph node payload will include a new `sections` array. Each section item contains only:

- `id`;
- `anchor`;
- `kind`;
- `title`;
- `url`.

`kind` is copied only when it is already present in the public section record. This allows the client to distinguish ordinary headings from numbered objects and proofs without exposing source paths or private support surfaces. Search-only text fields such as `search_text` and `search_snippet` do not need to move into the graph payload.

The client renders at most a bounded list of public sections for the selected page. Ordinary headings should appear first in page order, and numbered objects/proofs remain available either in this section list or in the existing `Key objects` block.

## User Experience

When a graph page is selected, the inspector shows:

1. selected page title and summary;
2. compact public section jumps;
3. existing study/key object and relationship context.

This lets a student move from graph-level structure to a specific rendered explanation, theorem, proof, or heading without opening Search first. Links are normal static anchors, so they work in local preview and static deployment.

## Constraints

- No browser-side MathJax.
- No runtime fetch/XHR for graph data.
- No external renderer, CDN, script, CSS, graph library, or font request.
- No `localStorage` or `sessionStorage` writes for graph state.
- No source paths, `_official`, `_reviewed`, `_assets`, artifact paths, cache keys, raw TeX, MathJax internals, answer-only support content, progress, mastery, recommendation, ranking, or personalization language in the graph payload or rendered section list.
- No new source-course contract or graph-data semantics.

## Testing

Add tests before implementation:

- Contract test: graph JSON nodes include `sections`, each item has only the allowed public keys, section URLs are deployment-neutral rendered anchors, and private/search-only fields are absent.
- Contract test: graph HTML includes the static `Page sections` detail block hooks.
- Browser e2e test: selecting the render fixture page with public sections shows a visible `Page sections` list, a section link points to the rendered page anchor, search/filter state is not cleared, URL state is not mutated by rendering, and browser storage remains empty.

## Documentation Impact

Update the foundation renderer contract only if the current wording is too implicit. It already permits graph selected-page details to show generated public section/object anchor jump links, so role docs can remain unchanged unless tests reveal the control needs learner-facing explanation.
