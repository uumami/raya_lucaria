# Local Course Search Design

## Context

The old `main` branch exposed search through a Pagefind widget in the sidebar. That was useful for student orientation, but the implementation depended on the old Eleventy/Tailwind build and Pagefind assets. The reset renderer should adapt the capability without importing that stack.

The current branch already has a local command bar, local graph page, local `OpenDyslexic`, and manifest-centered artifact data. A search surface should follow the same pattern as the graph page: generated static HTML, embedded browser input data, local JavaScript, no fetch-path ambiguity, and no external requests.

## Goal

Add a local static course search surface available from normal rendered pages.

The first slice searches generated page metadata only:

- page title;
- navigation title;
- stable ID;
- summary;
- status;
- tags;
- hierarchy label.

This keeps the feature useful without scraping rendered prose, MathJax output, source paths, or artifact internals.

## Design

The builder writes:

- `artifact/site/_raya/search/index.html`;
- `artifact/site/_raya/render/search.js`.

Normal pages add a fourth top command:

- `Search`: a local static link to `_raya/search/index.html`.

The search page embeds a browser payload:

```html
<script type="application/json" id="raya-search-data">...</script>
```

The browser payload is a rendered view input, not a new authority surface. It contains safe page metadata and deployment-neutral page URLs relative to `_raya/search/index.html`.

The search page works without JavaScript by rendering the full page list. With JavaScript enabled, a search input filters the list and updates an `aria-live` status. Matching is case-insensitive and accent-insensitive. Results are links to rendered pages.

## Non-Goals

- No Pagefind dependency.
- No full-text indexing of page body prose in this slice.
- No browser fetch of `artifact/data/pages.json`.
- No source paths, artifact paths, hashes, or cache keys in the student search page.
- No recommendations, mastery, progress, or adaptive ranking.
- No persistent search history.

## Files

- `packages/static/src/raya_static/builder.py`: add search surface generation, search payload, and command-bar link.
- `packages/static/src/raya_static/search.py`: local search JavaScript resource.
- `packages/static/src/raya_static/rendering.py`: search page and command CSS using existing skin tokens.
- `docs/foundation/20_learning_renderer_contract.md`: list local page-metadata search as current static renderer behavior.
- `tests/contracts/test_static_builder.py`: contract tests for generated search surface and local resource constraints.
- `tests/e2e/test_preview_static_read_path.py`: browser tests for preview, filtering, mobile/desktop overflow, and command link.

## Verification

Focused tests should prove:

- search page and `search.js` are written under `artifact/site/_raya/`;
- normal pages link to search using deployment-neutral relative URLs;
- search HTML embeds JSON and does not link to `artifact/data/pages.json`;
- search page contains no `http://`, `https://`, Pagefind, CDN, source paths, or artifact-root paths;
- browser search filters for `matrix` and exposes the expected page result;
- desktop and mobile search views have no horizontal overflow.

Broader verification should run the static builder suite, static-read-path e2e suite, and render-debug gate.
