# Graph Preview Bubble Design

## Context

The old `main` graph used a pointer-local tooltip and hover fading to make graph exploration feel immediate. The current reset branch has the correct architecture: generated static SVG, local JavaScript, deterministic layouts, keyboard support, URL-addressable graph state, a list panel, an inspector panel, no external graph library, no runtime fetches, and no browser storage.

This slice adapts the useful old interaction without importing the old graph stack. The graph keeps the current data model and inspector. Hover or focus on a graph node may also show a compact local preview near the inspected node so students can connect the node, label, relationship counts, and page summary without moving their eyes to the side panel.

## Options Considered

1. **Rebuild the graph around Cytoscape-style interactions.** This would recover old animation and tooltip behavior quickly, but it violates current static renderer constraints by adding a browser graph runtime and a larger interaction surface.
2. **Only improve the existing side inspector.** This is the lowest-risk option, but it does not solve the spatial tracking problem visible in the old branch comparison.
3. **Add a bounded local preview bubble on top of the current SVG graph.** This preserves current contracts and adds the missing immediate feedback. This is the chosen approach.

## Chosen Design

The graph page renders a hidden preview bubble inside the graph map panel. When a visible SVG graph node is hovered or receives keyboard focus, the existing inspection state continues to update and the bubble opens near the node's rendered position. The bubble shows only public generated page metadata already present in the graph payload:

- page title
- group or hierarchy context
- status when authored
- summary or a neutral missing-summary fallback
- outgoing, incoming, and connected-page counts

The bubble hides on pointer leave, blur, Escape, graph reset, layout-list mode, hidden filtered nodes, or graph re-render without an inspected node. It must stay inside the graph map panel bounds and avoid horizontal overflow. On narrow layouts where pointer-local overlays reduce readability, the existing in-flow inspection preview and inspector remain the primary surfaces; the bubble may be visually suppressed by CSS while the same inspection state continues to work.

## Architecture

`packages/static/src/raya_static/builder.py` owns the static bubble markup. `packages/static/src/raya_static/graph.py` owns non-persistent state and positioning because it already owns SVG node rendering, inspection state, viewport math, and event wiring. `packages/static/src/raya_static/rendering.py` owns the styling and responsive suppression.

The bubble is not a new data source. It derives content from the same helper text already used by `renderInspectionPreview()`. Positioning uses `latestRenderedPositions`, the current SVG `viewBox`, and the canvas bounding box to map graph coordinates to screen coordinates. The implementation clamps the bubble within the graph map panel so it cannot create horizontal scroll.

## Accessibility And Learning Constraints

The bubble mirrors existing hover/focus inspection and does not become the only accessible description. SVG graph links keep their existing `aria-label`; the in-flow preview and inspector remain available for screen readers and keyboard users. Focused nodes can trigger the bubble, but the side inspector remains the reliable keyboard detail surface.

The bubble is structural context only. It must not imply progress, mastery, ranking, recommendation, importance, authority, or personalized next steps. It must not read or write browser storage.

## Testing

Tests should prove the behavior before implementation:

- static graph HTML includes a hidden bubble surface near the SVG graph
- graph CSS defines bounded bubble styling and narrow-layout suppression
- graph JavaScript opens, positions, and hides the bubble through existing inspection events
- Playwright verifies a hovered/focused node shows the bubble with the expected public title/summary/counts
- Playwright verifies Escape or pointer leave hides the bubble
- desktop and mobile graph pages keep no horizontal overflow
- existing static parity checks still prove no external renderer requests, no browser-side MathJax dependency, and no graph runtime CDN

## Documentation

Update the learning renderer contract and student role docs in English and Spanish. The docs should describe the bubble as transient graph inspection context over public generated graph data, with the side inspector and page links remaining authoritative for navigation.

