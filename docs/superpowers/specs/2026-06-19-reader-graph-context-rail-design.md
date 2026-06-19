# Reader Graph Context Rail Design

## Context

The local graph page now gives a full static overview of course links and backlinks. The old `main` graph also made neighborhood context easy to inspect on hover, which is useful for learning orientation. The reset renderer should bring a small part of that usefulness into normal reading pages without turning the page into a graph UI, recommendation engine, or inspection surface.

Current foundation constraints are strict:

- normal pages are reader-facing views;
- machine truth remains in manifest-declared `data/*.json`;
- right rail may show compact page context from accepted artifact data;
- the renderer must not infer goals, related practice, progress, mastery, or recommendations from prose;
- no browser-side renderer dependencies, CDN requests, or dynamic state.

## Goal

Add a compact collapsible right-rail panel called `Linked pages` on normal course pages. It shows explicit graph relationships for the current page:

- `From this page`: authored content links from the current page to other pages;
- `Links here`: authored content links from other pages to the current page;
- `Prerequisites`: explicit prerequisite relationships already accepted in source metadata.

The panel is a reading aid. It does not say “recommended,” “practice,” “progress,” “mastery,” or “you should.”

## Non-Goals

- Do not infer relationships from headings, tags, prose, numbered objects, or summaries.
- Do not create a related-practice index.
- Do not add personal progress, study state, analytics, adaptive review, or spaced repetition.
- Do not add browser fetches or external graph libraries.
- Do not duplicate verbose graph internals in normal pages.

## Data Source

The panel uses the same generated link graph as `artifact/data/graph.json`.

The builder will compute `links_index` and `graph_index` before rendering pages. This is safe because `_links_index(...)` depends only on resolved course content, page reference maps, source paths, and source Markdown bodies. It does not depend on rendered page HTML, MathJax, numbered objects, references, reviewed outputs, or artifact writes.

The artifact-level `data/graph.json` remains the machine authority. The rail receives a small in-memory projection for the current page during rendering.

## Panel Rules

For a current page:

- `From this page` includes outgoing `content` edges only.
- `Links here` includes incoming `content` edges only.
- `Prerequisites` remains the existing prerequisite rail behavior and is not duplicated in `Linked pages`.
- Parent/navigation edges are not shown in this panel because the course map and sequence rail already cover structure.
- The current page is never listed as a linked target.
- Duplicate links are deduplicated by edge kind and page ID through the existing links index.
- Missing targets are omitted silently, matching current prerequisite rendering.

If a page has no outgoing or incoming content links, no `Linked pages` panel is rendered.

## UX

The panel appears in the right learning rail after `Prerequisites` and before `Page contents`. It is collapsed by default like most contextual panels. It uses the existing rail panel component and shell behavior:

- semantic `<section>`;
- real toggle button;
- `aria-expanded`;
- `aria-hidden`;
- `inert` when collapsed;
- no localStorage persistence;
- no hover-triggered layout movement.

Each list item has a small relationship label so readers can distinguish outgoing and incoming links without needing graph terminology:

- `From this page`
- `Links here`

The full graph page remains available from the top command bar.

## Foundation Update

`docs/foundation/20_learning_renderer_contract.md` should be updated to list explicit graph link context as current right-rail behavior. The wording must preserve the non-goal that related practice indexes require accepted source/artifact data and must not be inferred from prose.

## Tests

Contract tests:

- Build a temporary course where page A links to page B and page B links to page C.
- Assert page B renders a `raya-page-linked-pages` rail panel.
- Assert the panel contains `From this page` for page B’s outgoing content link.
- Assert the panel contains `Links here` for page A’s incoming content link.
- Assert it does not include navigation/parent relationships.
- Assert visible text does not contain `recommended`, `practice`, `progress`, or `mastery`.
- Assert `docs/foundation/20_learning_renderer_contract.md` documents explicit graph link context.

E2E/browser tests:

- Open a rendered page with the linked-pages panel.
- Verify it is collapsed by default with `aria-hidden="true"` and `inert`.
- Expand it by click and verify links become focusable.
- Verify no horizontal overflow at representative desktop/mobile viewports.

Verification:

- `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_reader_page_shows_explicit_graph_context -q`
- `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_context_panel_collapses_without_focus_leaks -q`
- `./scripts/check-render-debug.sh`

## Risks

- Moving graph generation earlier must not make rendered pages depend on generated artifact files.
- The panel text must not imply recommendations or personal learning state.
- The panel must not duplicate course-map structure or overwhelm the reader rail.
- The full graph page remains the right place for exploratory graph visualization.
