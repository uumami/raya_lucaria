# Graph Pan Viewport Design

## Context

The legacy `main` graph used Cytoscape for direct spatial exploration:
students could drag and zoom the graph while search and neighborhood cues
remained visible. The reset renderer intentionally removed Cytoscape and all
external graph/runtime dependencies, but the learning value of direct viewport
manipulation still applies. The current static graph has deterministic layouts,
zoom buttons, Fit, and Reset view, but dense graph inspection still requires
button-only zooming and full refits.

## Goals

- Pointer dragging on the SVG graph pans the current `viewBox`.
- The graph canvas can receive keyboard focus.
- Arrow keys pan the focused graph canvas in the four directions.
- Explicit pan buttons provide keyboard and pointer access to the same viewport
  movement.
- Fit redraws/fits the current layout and Reset view restores the current full
  view box.
- Pan, zoom, Fit, and Reset view do not clear search, group filters, selected
  page details, inspected page details, or graph data.
- All pan state is transient browser UI state only.

## Non-Goals

- No persisted graph viewport state.
- No mouse-wheel zoom in this slice.
- No touch gesture inertia or kinetic scrolling.
- No external graph library, CDN, fetch/XHR, worker, or browser-side data load.
- No graph ranking, recommendation, progress, mastery, or importance language.

## Architecture

`packages/static/src/raya_static/graph.py` already stores `fullViewBox` and
`graphViewBox`, and existing zoom/reset controls mutate the SVG `viewBox`.
Pan can use the same state without changing graph data:

- `panGraphView(dxRatio, dyRatio)` shifts the current `graphViewBox` by a
  fraction of its width/height.
- Pointer events on the SVG record the drag start point and starting view box,
  then update the view box based on pointer delta scaled through the SVG client
  rectangle.
- The SVG gets `tabindex="0"` so focused keyboard users can use Arrow keys.
- Four pan buttons call the same `panGraphView` helper.

The implementation should not re-render the graph while panning. It only changes
the SVG `viewBox`, matching the existing viewport-only zoom/reset behavior.

## Testing

Use TDD against the existing graph browser fixture:

- Contract test confirms generated graph controls and graph script expose pan
  controls and pan helpers.
- Browser test focuses the graph canvas and verifies ArrowRight changes the
  `viewBox` x coordinate without changing the current search value or selected
  detail.
- Browser test clicks a pan button and verifies the `viewBox` changes.
- Browser test drags the SVG and verifies the `viewBox` changes.
- Existing assertions continue to cover no fetch, no storage, no external
  graph libraries, no overflow, and static deployment-neutral resources.

## Documentation

Update the learning renderer contract and EN/ES agent guides to identify pan as
a transient graph viewport control. The docs should explicitly keep graph
position as a readability cue, not progress, rank, recommendation, mastery, or
importance.

## Self-Review

- No placeholders remain.
- Scope is limited to graph viewport pan controls.
- The design keeps the current static graph data contract unchanged.
- The behavior is verifiable in Playwright without external services.
