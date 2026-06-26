# Graph Canvas Legend Design

## Goal

Make graph colors understandable at the point of use by adding a compact,
canvas-adjacent group legend to the static Graph workspace.

## Context

The historical `main` branch graph kept a visible legend near the graph canvas.
That idea is worth salvaging, but its Cytoscape/CDN implementation is not part
of the reset. The current reset renderer already owns the static SVG graph,
local graph script, group colors, group filters, collapsible graph side panels,
and skin-driven graph color tokens.

The current group controls live inside the left Pages panel. When that panel is
collapsed, focused readers gain canvas space but lose the visible color key.
This makes the graph harder to read exactly when the canvas is being
prioritized.

## Design

Add a non-authoritative graph legend strip inside the map panel, above the SVG
canvas and below the orientation band. The legend lists each generated graph
group with the same swatch color used by graph nodes and the existing group
filter buttons. Each item is a real button using the existing
`data-raya-graph-group-filter` attribute so the current local graph script can
continue to control group visibility without a second state model.

The Pages panel keeps its existing group controls for scan/filter workflows.
The new map-panel legend is a duplicate control surface over the same transient
local UI state, not a second data source. It must not persist state, fetch data,
infer progress, expose source paths, or imply recommendation/ranking/mastery.

## UX Requirements

- The legend appears in the graph map panel first viewport on desktop.
- The legend remains visible when the Pages panel is collapsed.
- Legend swatches use the same generated group color tokens as graph nodes.
- Legend controls use the existing group filter behavior and `aria-pressed`
  state.
- The legend layout is compact and wraps instead of forcing horizontal
  overflow.
- The legend uses current skin tokens and existing graph button styling.

## Implementation Notes

- Reuse the current group button generation pattern in
  `packages/static/src/raya_static/builder.py`.
- Generate a second group-control block with a map-panel specific wrapper class.
- Do not add external graph libraries, CDN requests, storage, fetch, or runtime
  graph data loading.
- Keep tests focused on rendered HTML, first-viewport visibility, collapsed
  panel behavior, local-only requests, and no horizontal overflow.

## Testing

- Contract test: the generated graph HTML contains a map-panel legend with one
  button per graph group, matching group filter attributes and no external
  renderer dependency.
- Browser test: at desktop size, collapse the Pages panel and verify the legend
  remains visible above the canvas, buttons fit without horizontal overflow,
  and clicking a legend button updates its `aria-pressed` state through the
  existing local graph script.

## Non-Goals

- No Cytoscape migration.
- No persistent graph state.
- No new graph data contract.
- No graph analytics, progress, ranking, recommendations, or mastery semantics.
