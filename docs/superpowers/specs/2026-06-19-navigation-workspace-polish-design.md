---
id: superpowers-navigation-workspace-polish
title: Navigation Workspace Polish Design
status: accepted-for-autonomous-loop
date: 2026-06-19
---
# Navigation Workspace Polish Design

## Goal

Improve the static reader navigation workspace by adapting the useful legacy
main-branch search and graph affordances into the reset renderer without
carrying over legacy architecture. This slice focuses on two practical reader
needs: finding a page quickly and understanding the graph controls without
guesswork.

## Context

The reset renderer already has local static course search, a static graph page,
an expanded course map, local OpenDyslexic resources, and no browser-side
MathJax conversion. The legacy `main` branch had stronger graph orientation:
visible controls, approximate search, a legend, and a collapsible help section,
but it depended on Cytoscape from a CDN, legacy layouts, and browser state that
cannot define current contracts.

## Design

Search remains a static generated page backed only by embedded page metadata.
It gains the same approximate matching style as the graph page, a clear button,
keyboard movement through visible results, active-result styling, and Enter-to-open
behavior. This makes search usable as a fast command surface without adding a
Pagefind dependency or scraping rendered prose.

The graph page keeps the current local SVG/list implementation. It gains a
static legend that explains node, match, selected, and active-link visual states,
plus a closed `details` help panel for controls and layouts. The help text must
describe source graph structure only: pages, groups, links, prerequisites, and
layout controls. It must not describe recommendations, progress, mastery,
completion, analytics, or personal next steps.

Both surfaces continue to use local CSS and JavaScript from
`artifact/site/_raya/render/`. They must not fetch JSON at runtime, load external
scripts/styles/fonts, persist graph/search state, or depend on browser-side
rendering libraries.

## Files

- `packages/static/src/raya_static/builder.py` renders the extra search button
  and graph legend/help markup.
- `packages/static/src/raya_static/search.py` owns static search interactions.
- `packages/static/src/raya_static/rendering.py` owns token-based styling for
  the new states and help surfaces.
- `tests/contracts/test_static_builder.py` protects generated markup, payload
  boundaries, and forbidden runtime dependencies.
- `tests/e2e/test_preview_static_read_path.py` verifies desktop/mobile browser
  behavior, local requests only, keyboard operation, and no overflow.
- `docs/foundation/20_learning_renderer_contract.md` and role guides document
  the accepted behavior if the implementation changes user-facing workflows.

## Rejected Alternatives

- Use Pagefind or a search index generated from rendered prose. Rejected because
  the current contract limits search to generated metadata.
- Bring back Cytoscape or a force-layout graph library. Rejected because static
  deployment must not use CDN or external renderer requests.
- Store recent searches, selected graph nodes, or layout choices. Rejected
  because graph/search state is not a comfort preference and must not persist.

## Verification

Focused verification must show:

- Search typo queries such as `matrx` still surface the matrix page.
- Arrow keys change the active visible search result and Enter opens it.
- The clear button resets the query and active state.
- Graph HTML contains the legend and closed help panel.
- Browser loads for search and graph use only the local preview origin.
- Search and graph scripts contain no `fetch(`, `XMLHttpRequest`,
  `localStorage`, `sessionStorage`, `https://`, or `http://`.
- The generated surfaces contain no recommendation, progress, mastery, or
  completion language outside authored fixture prose.
