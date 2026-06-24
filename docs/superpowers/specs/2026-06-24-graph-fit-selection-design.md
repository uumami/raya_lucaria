# Graph Fit Selection Design

## Context

The old `main` graph used Cytoscape and a visible `Ajustar` control to help a
reader reframe the graph. The current static graph already replaces that with a
local SVG implementation, deterministic layouts, fuzzy search, group and edge
filters, pan/zoom/reset controls, URL state, page-focused handoffs, and
selected-neighborhood filtering. It intentionally rejects the old CDN
Cytoscape dependency, browser-side data fetching, and layout behavior that is
not generated from embedded artifact data.

The remaining orientation gap is narrower: after a reader selects a page, opens
Graph from `?page=<page-id>`, or follows Search to Graph, the global `Fit`
control resets the whole active graph view. There is no command that frames the
selected page and its directly connected graph context while preserving the
selected page, query, filters, details, and current static graph data.

## Goal

Add a graph viewport command that frames the selected page and its immediate
visible neighborhood. This should make selected-page context easier to inspect
without changing graph authority, visible graph membership, URL state semantics,
or learner state.

## User Experience

The Graph toolbar gains a `Fit selection` button near the existing `Fit`,
`Zoom in`, `Zoom out`, and `Reset view` controls.

When no page is selected, `Fit selection` is disabled. When a page is selected,
the button becomes enabled and sets the SVG `viewBox` around:

- the selected page node,
- visible directly connected page nodes, and
- visible edges connecting that selected neighborhood.

The command only changes the SVG viewport. It does not select a different page,
clear the inspector, clear query text, change filters, toggle selected-neighborhood
focus, persist state, fetch data, or navigate.

The existing global `Fit` behavior remains unchanged: it resets the current
active layout to the full active graph view. `Reset view` also remains a full
view reset.

## Behavior Details

The implementation computes viewport bounds from the most recent rendered SVG
geometry, not from DOM bounding boxes. This keeps tests and behavior stable
across desktop/mobile CSS, browser zoom, and skin changes.

The graph script stores the latest rendered node positions by page ID and
the latest active graph edges. `Fit selection` builds a set from
`neighborsOf(selectedId)`, intersects it with currently rendered node positions,
and computes a padded viewBox around those nodes. If only the selected node is
available, the command frames a small readable region around that node. If the
graph is in `List` layout or there is no selected node, the control is disabled.

Padding must be generous enough that labels, selected rings, and connected edge
segments remain visible. The computed viewBox is clamped or expanded to
avoid zero width/height and should not become larger than the full graph unless
the selected region itself requires it.

When the selected page changes through graph click, list keyboard movement,
URL initialization, or detail linked-page `Focus` buttons, the control state
updates after render. Existing zoom and pan controls continue to operate from
the fitted selection view.

## Boundaries

This is a viewport affordance only. It must not add:

- browser-side MathJax,
- runtime `fetch` or XHR,
- external graph libraries or CDN requests,
- localStorage/sessionStorage graph state,
- progress, mastery, recommendation, ranking, or personal guidance language,
- scraped rendered HTML as graph authority.

Graph data remains the embedded generated payload. Positions remain structural
readability cues over explicit generated graph relationships.

## Documentation Impact

Update the learning renderer contract to name `Fit selection` as a current graph
viewport control and to clarify that it frames selected graph context without
changing graph data, selection, filters, or learner state.

Update English and Spanish agent guides so future graph changes verify:

- selected-page fit control presence,
- disabled state when no selected page or list layout is active,
- viewport changes after selecting a page,
- selected-page details and URL/search/filter state remain intact,
- no storage, fetch, external requests, or progress/recommendation language.

## Testing Strategy

Start with failing tests.

Contract tests should assert:

- the graph HTML contains a `graph-fit-selection` control,
- generated help text explains selection fitting as viewport-only,
- graph JavaScript contains named helpers for selected-neighborhood bounds and
  selected-fit control state,
- forbidden runtime tokens remain absent.

Browser tests should assert:

- selecting a graph page enables `Fit selection`,
- zooming or panning away and then clicking `Fit selection` changes the SVG
  `viewBox` to a smaller selected-neighborhood view,
- the selected node and at least one connected edge are visible inside the
  graph canvas after fitting,
- the selected detail panel, graph query, visible filters, and URL state are
  preserved,
- global `Fit` still restores the full active graph view,
- `Fit selection` is disabled in list layout and before any page is selected.

Focused checks should run the graph contract tests and the relevant graph e2e
test before the canonical gates.

## Non-Goals

This loop does not change graph navigation semantics, add hover tooltips,
replace the current inspector, introduce animated force layouts, import
Cytoscape, or redesign the entire graph workspace. Those can be separate
Superpowers loops if they remain useful after this viewport orientation work.
