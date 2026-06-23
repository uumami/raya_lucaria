# Graph Viewport Controls Design

Date: 2026-06-23

## Purpose

The legacy `main` graph gave readers direct viewport control: fit, reset, layout switching, zoom-like exploration, and a larger graph canvas. The reset renderer already has local static graph data, deterministic SVG/list layouts, selected-page detail, group filters, search, fit, reset, and expanded workspace mode. The missing UX capability is comfortable inspection of dense SVG graphs without bringing back Cytoscape, CDN scripts, persisted state, or runtime graph fetches.

This slice adds static SVG viewport controls to the current Course Graph page.

## Scope

In scope:

- Add visible `Zoom in`, `Zoom out`, and `Reset view` controls to the graph toolbar.
- Apply zoom by changing the SVG `viewBox` around the current visible graph geometry.
- Keep `Fit` as a redraw/refit of the current layout and make `Reset view` return to the full generated viewBox without clearing search, filters, selected page, or layout.
- Preserve existing broad reset behavior through the `graph-reset` control, labeled `Reset graph`, which clears search, filters, selected page, layout, expanded workspace, and viewport.
- Keep all viewport state transient in memory only.
- Update the renderer contract and English/Spanish role docs.
- Add contract and browser tests for controls, no external requests, no storage, no overflow, and reset semantics.

Out of scope:

- Cytoscape, D3, force simulation, graph workers, service workers, or external graph libraries.
- Persisted graph zoom/pan/layout/search state.
- New graph data, inferred relationships, ranking, recommendations, progress, or mastery.
- Browser fetching of `data/graph.json`.

## Behavior

The graph toolbar gains:

- `Zoom in`
- `Zoom out`
- `Reset view`
- `Reset graph`

`Zoom in` and `Zoom out` operate only when the SVG graph is visible. They scale the current `viewBox` around its center, bounded so the graph remains usable and does not become invisible. `Reset view` returns the SVG to the full generated layout viewBox. `Fit` continues to redraw the current layout and also resets the viewBox to the full generated layout. The existing broad reset button keeps its `graph-reset` ID for compatibility, but its visible label becomes `Reset graph` to distinguish it from `Reset view`.

Search, group-filter, layout, and fit changes refit the SVG viewport to the current generated graph view so filtered graph results cannot remain hidden inside an old zoom crop. Viewport buttons are disabled in list layout because the SVG is hidden. Pointer drag, wheel zoom, pinch zoom, and draggable nodes are deferred; they can interfere with link selection, double-click navigation, and mobile page scrolling.

## Accessibility

All new controls are real buttons in the existing graph controls section. They have clear visible text and `aria-label` values. The graph status remains the live region for visible node/edge counts; viewport controls must not report progress or learner state. The controls must fit in the existing compact mobile toolbar without horizontal overflow. The ordered graph list and selected-page detail remain the accessible fallback for readers who do not use precision SVG inspection.

## Static Contract

The viewport controls use only embedded graph data and local JavaScript. They must not write `localStorage`, `sessionStorage`, IndexedDB, URL state, cookies, artifact data, or source files. They must not fetch external resources or generated `data/*.json` at runtime.

## Testing

Contract tests should verify graph HTML includes the new controls and graph JavaScript includes viewport helper names while still excluding external libraries and runtime storage/fetch APIs.

Browser tests should verify:

- Initial graph canvas has a full generated `viewBox`.
- `Zoom in` changes the `viewBox` to a smaller centered region.
- `Zoom out` changes the `viewBox` back toward a larger region.
- Search and group-filter changes reset the viewport to the current full graph view.
- `Fit` restores the current full graph view after zoom.
- `Reset view` restores the initial full viewBox without clearing search text or selected page.
- Viewport controls are disabled in list layout and re-enabled when an SVG layout returns.
- Existing `Reset graph` still clears search, selection, layout, expanded state, group filters, and viewport.
- Controls do not create external requests or horizontal overflow on desktop or mobile.

## Documentation

Update `docs/foundation/20_learning_renderer_contract.md` and role guides to say the graph may provide transient zoom, fit, and reset-view controls for local inspection. Students should understand these controls as comfort/orientation tools. Agents and contributors should verify that viewport state is local and non-persistent.
