# Graph First-Paint Visibility Design

## Goal

Make the generated Graph workspace immediately useful when opened from a page handoff such as `_raya/graph/index.html?page=reader-ux`. The selected graph node and connected structure must be visible in the first desktop viewport without requiring the learner to scroll past an empty graph canvas.

## Evidence

Independent UX review found that the render fixture graph page contains valid graph data and rendered SVG nodes/edges, but the map panel can become very tall because the graph workspace stretches columns to the height of neighboring panels. The SVG viewBox remains landscape, so the graph content is vertically centered far below the initial visible canvas area.

Local inspection agrees:

- `.raya-graph-workspace` uses `align-items: stretch`.
- `.raya-graph-map-panel` is a flex column.
- `.raya-graph-canvas` has `flex: 1 1 auto` and `min-height: 34rem`.
- The generated graph code renders nodes and selected-page detail correctly; the first-paint defect is layout composition, not graph data.

## Design

Keep the current static SVG graph and local deterministic layouts. Do not introduce Cytoscape, external graph libraries, runtime fetches, persisted graph state, or learner-state wording.

Change the graph workspace layout so desktop panels align to their own content instead of stretching the map panel to neighboring panel height. Give the SVG canvas an explicit, bounded learner-friendly height and aspect ratio. The default graph should show nodes and edges near the top of the graph panel, and expanded graph mode may still use a larger bounded viewport.

The graph page should preserve:

- selected page from `?page=<page-id>`;
- graph/list/inspector composition;
- panel collapse controls;
- zoom, pan, fit, reset, layout, group filter, edge-kind filter, and neighborhood focus behavior;
- no external requests;
- no browser-side MathJax;
- no graph-state storage.

## Acceptance Criteria

1. Opening `_raya/graph/index.html?page=reader-ux` at desktop size shows at least one graph node, at least one graph edge, and the selected page node inside the visible canvas viewport on first paint.
2. The selected page from the `page` query remains selected in the SVG and in the inspector.
3. The graph canvas height is bounded relative to the viewport and does not stretch to the height of side panels.
4. At desktop widths, the graph map panel remains wider than the list and inspector panels.
5. At mobile widths, graph controls and content remain usable with no horizontal overflow.
6. Existing static renderer invariants remain true: local resources only, no fetch/XHR, no external renderer/CDN requests, no persisted graph state, and no learner-state claims.

## Verification

Add a browser e2e test that loads the render fixture graph handoff and measures actual DOM bounding boxes. The test should fail if graph data exists but the selected SVG node or graph edges are outside the visible canvas area.

Run focused graph e2e tests first, then `./scripts/check-render-debug.sh`, `./scripts/check.sh`, and `./scripts/check-docker.sh` before claiming completion.
