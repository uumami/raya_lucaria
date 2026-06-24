# Graph Cluster Layout Design

## Context

The reset graph workspace now has local embedded graph data, fuzzy search,
group filters, collapsible list and inspector panels, selected-page details,
neighborhood focus, viewport controls, and deterministic `Connections`, `Map`,
`Radial`, and `List` layouts. Legacy `main` had a Cytoscape force layout that
was useful because it made chapter or topic clusters feel visible, but its
implementation relied on a browser graph library, CDN loading, animated random
layout, and runtime interaction patterns that do not fit the reset renderer.

The next useful transfer is the cluster-reading affordance, not the legacy
engine. Students should be able to ask "what areas of the course sit near each
other?" without losing static parity, deterministic screenshots, local-only
resources, or explicit graph data boundaries.

## Goal

Add a deterministic `Cluster` graph layout that arranges visible pages around
their generated course groups. It should preserve all current graph controls and
make group neighborhoods easier to scan than `Connections` or `Map` for larger
courses.

## Approach Options

### Option A: Port the legacy force layout

This would most closely mimic the old graph, but it would require a graph
engine or a hand-written physics simulation. It would also introduce animation,
randomness, or difficult screenshot behavior. This does not fit the reset
static renderer.

### Option B: Add a deterministic cluster layout

Compute one group center per visible course group, place group centers on a
stable ring, and place pages in each group on smaller deterministic rings around
their group center. This keeps the useful "cluster" mental model while using
only embedded nodes, generated groups, and local SVG. This is the recommended
approach.

### Option C: Strengthen hover spotlight only

Hover spotlight would improve graph scanning, but it does not add the missing
group-cluster view. It should be a later slice after a cluster layout exists.

## User Experience

The graph layout selector adds `Cluster` after `Connections`:

- `Connections` remains the default relationship-flow layout.
- `Cluster` groups pages by generated course group.
- `Map` keeps the existing group-column layout.
- `Radial` keeps the all-around overview.
- `List` hides the SVG for text-first browsing.

In `Cluster` mode, pages in the same generated group sit near each other. The
group centers form a deterministic ring, ordered by generated group order and
title. Pages within each group form a smaller ring ordered by course order,
then title, then ID. A single-node group sits at its group center. The layout is
stable across rebuilds, local preview, static deployment, and render-debug
screenshots.

The layout is a reading view only. It must not imply learner state, personal
guidance, ranking, importance, mastery, completion, or recommendation.

## Layout Algorithm

The algorithm runs inside the existing local graph script:

1. Split active nodes by `node.group || ""`.
2. Sort group IDs by generated group order, then group title.
3. Place group centers around the canvas center on a ring that fits within the
   existing fixed SVG viewBox.
4. For each group:
   - sort nodes with the existing course-order comparator;
   - if the group has one node, place it at the group center;
   - otherwise, place nodes around a smaller ring centered on the group center;
   - clamp the per-group ring radius so node hit targets stay inside the
     viewBox.
5. Return positions through the existing `positionsFor(activeNodes, mode)`
   contract.

No schema changes are required. The layout uses existing payload fields:
`group`, `order`, `title`, `nav_title`, and `id`.

## Architecture

The builder emits one new static layout option. `graph.py` adds a group sorting
helper and a `mode === "cluster"` branch in `positionsFor`. The existing SVG
renderer, edges, status, search, group filters, selected-node state,
neighborhood focus, panel collapse, viewport controls, and local accessibility
resources remain unchanged.

`Cluster` must not add Cytoscape, D3, Mermaid, workers, `fetch`, storage, URL
state, cookies, generated graph mutation, or external requests.

## Testing

Contract tests should assert:

- the graph HTML includes `Cluster` in the layout selector;
- graph help describes `Cluster` without forbidden learner-state language;
- the graph script includes the cluster layout branch and helper names;
- no external graph library or forbidden runtime token is introduced.

Browser tests should verify:

- selecting `Cluster` changes `data-raya-graph-layout` to `cluster`;
- at least two pages in the same group are closer to each other than pages in
  different groups in the render fixture with added crowded pages;
- all node centers remain at least one hit-target radius inside the SVG
  viewBox;
- `Cluster` still works after returning from `List`;
- no extra browser requests occur after page load.

## Documentation

Update the learning renderer contract and English/Spanish agent guides to name
`Cluster` as a deterministic generated-group layout. Documentation must keep
the same boundary language: positions are structural reading cues over explicit
generated data, not learner state or personal guidance.
