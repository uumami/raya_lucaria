# Graph Connections Layout Design

## Context

The reset static Course graph already has local SVG rendering, embedded graph
data, search, group filters, selected-page details, neighborhood focus,
collapsible panels, and no external requests. Legacy `main` had a stronger graph
experience through Cytoscape layout choices such as force, hierarchy, circular,
and grid. The useful UX idea is that students can switch between different
mental models of the same graph. The implementation mechanism is not portable:
`main` loaded Cytoscape from a CDN, animated a force layout in the browser, and
navigated on node click. The reset renderer must keep local static resources,
deployment-neutral links, explicit graph data, and no runtime data fetching.

The current reset `map` layout is deterministic, but it is grouped by page group
columns rather than by link direction. For larger courses, students need a
layout that answers "what flows into what?" without requiring a force engine or
external graph library.

## Goal

Add a deterministic `Connections` graph layout that arranges visible pages by
normalized explicit graph relationships and course order. It should become the
default layout for the graph workspace while preserving the existing `Map`,
`Radial`, and `List` modes as alternatives.

## Approach Options

### Option A: Use a browser force simulation

This would most closely resemble legacy `main`, but it would add significant
runtime complexity and likely require either a new graph engine or a
hand-rolled physics loop. It would also make screenshot/debug output less
deterministic. This is not appropriate for the reset static renderer.

### Option B: Replace `map` with link-aware columns

This keeps the UI small but removes the current group-column view. Group columns
are still useful when students want chapter/unit structure rather than link
flow, so replacing them would lose a current capability.

### Option C: Add `Connections` as the default layout

Add a new `connections` layout option and make it selected by default. It uses
only current embedded nodes and normalized layout edges. It places root or
low-incoming pages in the first column, follows explicit relationship flow to
later columns, uses course order as a stable tie-breaker, and falls back to
group/order placement for cycles or disconnected pages. Existing `Map`,
`Radial`, and `List` remain available. This is the best fit: it transfers the
useful hierarchy concept from legacy `main` while respecting reset constraints.

## User Experience

The graph layout selector shows:

- `Connections` as the selected default;
- `Map` for the existing group-column layout;
- `Radial` for an all-around overview;
- `List` for non-SVG browsing.

In `Connections` mode, the SVG arranges pages left-to-right by relationship
depth. A course root or page with no incoming visible edges starts on the left.
Pages reached by explicit outgoing links move rightward. Pages in the same
column are ordered by current course order and title. The layout remains stable
across page reloads, screenshots, and static deployments.

The mode works with current controls:

- Search still expands matches to connected context before layout.
- Group filters remove hidden groups before layout.
- Neighborhood focus narrows the visible set before layout.
- Selected, neighbor, match, hover/focus inspection, and edge states stay
  unchanged.
- Fit, zoom, reset view, and graph expansion continue to operate on the SVG
  `viewBox`.
- Reset returns to `Connections`, clears search/filters/selection, and restores
  the full graph.

## Layout Algorithm

The algorithm runs entirely in local JavaScript over already-visible graph
nodes and edges:

1. Build the active node ID set.
2. Normalize layout edges from the current active edge set:
   - ignore `parent` edges for geometry;
   - keep forward `navigation`, `content`, and `prerequisite` edges when the
     source page order is less than or equal to target page order;
   - invert backward `content` and `prerequisite` edges so a page linking back
     to supporting material can still appear after that material;
   - drop duplicate normalized edges.
3. Compute incoming and outgoing adjacency for normalized layout edges.
4. Choose roots as nodes with no incoming normalized edges. If every active node has
   incoming edges, use the lowest-order visible node as the root.
5. Walk outgoing edges from roots, assigning the smallest discovered depth.
6. Repeat a bounded relaxation pass over normalized edges so a node may move right
   when it is reached from a deeper predecessor.
7. Any unassigned node receives depth `0` when disconnected or one more than the
   shallowest incoming assigned predecessor when possible.
8. Render columns by depth. Within a column, sort by `order`, then title, then
   ID.

This is intentionally not a topological truth claim. It is a deterministic
reading layout over explicit graph edges. Cycles, backlinks, parent links, and
navigation links may exist; normalized edge direction, bounded passes, and
course order keep output predictable.

## Architecture

No schema changes are required. The builder emits a new static `<option>` in the
graph layout selector. The local graph script adds one layout branch inside
`positionsFor(activeNodes, mode)` and a helper that computes connection depths
from the existing `edges` array.

`connections` uses the same SVG primitives, hit targets, node sizing,
inspection classes, and viewBox controls as `map` and `radial`. It must not
write URL parameters, storage, cookies, generated files, or runtime network
requests. It must not import Cytoscape, D3, Mermaid, workers, or any external
renderer.

## Testing

Contract tests should assert that the graph HTML includes `Connections`,
`Map`, `Radial`, and `List` layout options and that the local graph script
contains normalized layout-edge and connection-depth helpers without adding
forbidden runtime tokens.

Browser tests should open the render fixture graph and verify:

- the default layout is `connections`;
- the graph root has a smaller SVG `x` position than a connected child;
- selecting `Map`, `Radial`, and `List` still updates layout state correctly;
- Reset returns layout to `connections`;
- `Connections` works after search, group filters, and neighborhood focus;
- no external requests occur after page load;
- desktop and mobile have no horizontal overflow.

## Documentation

Update the learning renderer contract and English/Spanish agent guides to treat
`Connections` as the default deterministic relationship layout. The docs should
state that graph layout is a readability cue over explicit generated graph data,
not a recommendation, progress, ranking, or mastery signal.
