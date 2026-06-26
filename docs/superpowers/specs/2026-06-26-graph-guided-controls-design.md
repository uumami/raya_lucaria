# Graph Guided Controls Design

## Context

The legacy `main` graph page had a compact `Controles del grafo` disclosure that
made the graph easier to learn: search, layout, fit/reset, expansion, chapters,
and interaction were explained directly near the graph. That implementation used
Cytoscape and CDN loading, so it cannot be ported directly.

The current reset branch already has a stronger static graph: local SVG,
generated graph data embedded at build time, grouped controls, relationship
filters, orientation band, graph focus mode, URL-addressable graph state,
search spotlight, selected-page inspection, and no runtime fetches or external
renderer dependencies. The remaining UX gap is learnability. The current help
is structurally present but long and placed after the inspector and legend,
which makes it easy to miss during first use.

## Design

Add a compact graph guide strip inside the graph map panel, between the
orientation band and the SVG canvas. It should explain the most useful actions
in short scan-friendly cards:

- `Find`: search titles, stable IDs, tags, groups, and status; use arrow keys
  in results and Enter to open the active result.
- `Choose a view`: `Connections` reads course link flow, `Topology` follows
  explicit relationships, `Cluster` groups by course group, and alternate
  layouts are just visual views.
- `Inspect`: hover/focus previews a page; click once selects; double-click or
  Enter opens the page.
- `Move`: pan/zoom/fit change only the SVG viewport; `Fit selection` frames the
  selected page and visible relationship context.
- `Filter`: group and relationship filters hide visible marks only; they do not
  delete pages, mutate authored graph data, or become learner progress.

The guide is static HTML generated with the graph page. It is not a tutorial
engine, does not persist state, and does not add JavaScript. The existing longer
`Graph controls` details block remains in the inspector as the complete
reference.

## Constraints

- No `fetch`, `XMLHttpRequest`, external scripts, Cytoscape, CDN requests, or
  browser-side renderer calls.
- No `localStorage` or `sessionStorage`.
- No learner progress, mastery, ranking, recommendation, or personalization
  language.
- Keep the current graph controls, graph data payload, URL state, orientation
  band, inspector, legend, and graph behavior intact.
- Keep the guide compact enough to stay above the canvas on desktop.
- Keep mobile layout readable without horizontal overflow.

## Testing

Contract tests should assert that the graph page contains the new guide strip,
all five guide cards, and the no-storage/no-fetch constraints still hold.

Browser tests should assert that the guide is visible above the canvas on a
desktop graph page, remains compact, has all guide card labels, does not create
horizontal overflow, and does not trigger external requests.

Render-debug verification should continue to pass because the change affects
visible generated graph/static resources.

## Out of Scope

This does not change graph algorithms, layouts, SVG rendering, graph URL state,
panel collapse behavior, course schemas, or role documentation. Broader
visual restyling and theme preview controls remain separate UX fusion loops.
