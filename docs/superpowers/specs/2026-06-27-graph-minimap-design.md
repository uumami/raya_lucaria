# Graph Minimap Design

## Goal

Add a compact, passive minimap to the static Graph workspace so learners can stay oriented while zooming, panning, fitting a selected page, or using Graph Focus mode.

## Context

The old `main` branch graph felt more spatial and app-like because its Cytoscape canvas could expand, fit, zoom, and keep users oriented inside a large graph. The current renderer cannot reuse that implementation because it used an external Cytoscape CDN dependency and legacy browser state. The current static SVG graph already has local deterministic layouts, search, filters, pan/zoom buttons, pointer panning, keyboard panning, Fit, Fit selection, Reset view, and Graph Focus. What is missing is a small overview that shows where the current SVG viewport sits inside the full generated graph.

## Design

Render a small local SVG minimap beside the main graph canvas. The minimap is generated in the browser from the already embedded public graph payload and the same rendered node/edge positions used by the main SVG canvas. It shows faint visible graph edges, visible page points, and one viewport rectangle that reflects `graphViewBox` relative to `fullViewBox`.

The minimap is passive in this slice. It does not accept pointer input, does not store state, does not create URL parameters, and does not fetch data. It updates whenever the main graph renders or the visual viewport changes through Fit, Fit selection, Reset view, Zoom, Pan, pointer panning, keyboard panning, layout changes, group filters, relationship filters, search, selected-neighborhood focus, or Graph Focus.

## Scope

In scope:

- Add static minimap markup to the generated Graph page.
- Add CSS that keeps the minimap compact on desktop and mobile and hidden in print with other canvas-only graph surfaces.
- Render minimap nodes/edges from currently active visible graph data.
- Render a viewport rectangle that changes when the graph viewport changes.
- Preserve existing graph state rules: no storage, no external requests, no browser-side renderer dependency, and no new graph semantics.

Out of scope:

- Click-to-pan or drag-to-pan minimap interaction.
- New graph layouts or ranking algorithms.
- New artifact data files or source schema.
- Progress, mastery, recommendation, importance, or personalization language.

## Testing

Use TDD:

1. Add a browser e2e test that opens `_raya/graph/index.html?page=reader-ux`, confirms the minimap is visible, has rendered node marks, edge marks, and a viewport rectangle.
2. In the same test, click Zoom in and Pan right, then assert the viewport rectangle geometry changes while selected page state and storage remain unchanged.
3. Add contract assertions that generated Graph HTML includes the minimap surface and that Graph resources still avoid `fetch`, `XMLHttpRequest`, external renderer/CDN URLs, `localStorage`, and `sessionStorage`.
4. Run the focused e2e and contract tests, then `./scripts/check-render-debug.sh`.

## Review Notes

This slice is aligned with the current learning renderer contract because it is a visual orientation cue over current graph structure and existing viewport controls. It does not require a foundation update unless future work makes the minimap interactive or adds new semantics.
