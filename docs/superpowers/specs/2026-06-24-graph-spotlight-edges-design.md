---
title: Graph Spotlight Edges Design
status: approved-for-autonomous-superpowers-loop
---
# Graph Spotlight Edges Design

## Context

The current reset renderer already has a static Course Graph workspace with local
search, deterministic layouts, group filters, collapsible list and inspector
panels, selected-page details, and neighborhood focus. The legacy `main` branch
graph used Cytoscape, force layouts, source-chapter edge colors, hover fading,
and a floating tooltip. The transferable part is the visual reading behavior,
not the old stack.

This loop adds a small graph readability pillar: **spotlight edges and hover
context**. It keeps the current SVG renderer, current embedded payload, and
current static constraints.

## Goals

- Color each visible edge from the source page's generated course group.
- Dim graph nodes and edges outside the inspected page neighborhood while a
  page is hovered or keyboard-focused.
- Keep selected-page state separate from transient inspection state.
- Extend the legend and help copy so students and agents can understand the
  visual cues.
- Preserve local static behavior: no fetch, storage, external graph library,
  CDN, browser-side MathJax, or dynamic learner-state language.

## Non-Goals

- No Cytoscape, D3, force simulation, random layout, animation dependency, or
  drag-position state.
- No schema or artifact payload change.
- No inferred recommendations, importance ranking, progress, mastery, or
  personal next-step language.
- No floating tooltip in this loop. The current inspector status region already
  provides accessible hover/focus parity; a tooltip can be reconsidered later if
  it can stay accessible and non-overlapping.

## Design

The graph script will derive edge color from existing node group data. When an
edge is rendered, it will set a CSS custom property on the SVG line:
`--raya-graph-edge-color: var(--raya-graph-group-N)`, where `N` is the source
node's generated group color index. If the source page is missing, the edge
falls back to the default graph border color.

Transient inspection already tracks `inspectedId` and marks inspected nodes,
neighbors, and incident edges. This loop extends that state by marking
non-neighborhood SVG nodes and non-incident SVG edges as `is-dimmed` while
inspection is active. The list already highlights inspected and neighboring
items; it will not be hidden or filtered by this transient state.

Selected-page behavior remains unchanged. Clicking still selects a page and
fills the detail panel; hovering/focus only changes temporary visual emphasis
and the live inspection text.

## Documentation

The foundation renderer contract will name source-group edge colors and
transient spotlight dimming as graph readability cues. English and Spanish
agent guides will ask agents to verify edge colors, spotlight behavior,
keyboard parity, and static constraints.

## Testing

Contract tests will assert that the graph HTML exposes an edge-color legend item
and help copy, and that the local graph script contains the edge-color helper
and `is-dimmed` state.

The browser graph e2e test will focus and hover existing graph nodes, then
verify:

- incident edges become inspected;
- unrelated graph elements receive `is-dimmed`;
- rendered edge lines carry `--raya-graph-edge-color`;
- the live inspection status updates from keyboard focus;
- no external runtime requests are introduced.

Focused tests are enough for implementation. The normal render-debug, host, and
Docker gates remain completion verification.
