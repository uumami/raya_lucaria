# Graph Topology Layout Design

## Context

The legacy `main` graph used a Cytoscape force layout. That implementation does
not fit the reset renderer because it relied on a browser graph library, runtime
animation, random layout behavior, and old Eleventy surfaces. The useful UX idea
is still valid: students could see relationship-shaped neighborhoods, not only
course-order columns or generated course groups.

The current graph already has deterministic `Connections`, `Cluster`, `Map`,
`Radial`, and `List` layouts. `Cluster` groups pages by generated course group.
It does not answer the old-main question "which pages are close because they are
linked?"

## Goal

Add a dependency-free `Topology` graph layout that places visible pages by
explicit generated graph relationships. It should recover the old-main natural
cluster reading affordance while preserving current static renderer contracts:
local embedded data only, deterministic output, no runtime graph library, no
browser-side fetch, no persisted graph state, and no learner-state language.

## Approach Options

### Option A: Port Cytoscape force layout

This would recreate old-main behavior most closely, but it would reintroduce a
large browser graph dependency, runtime physics, animation timing, and harder
static parity checks. It is rejected.

### Option B: Add a deterministic force-inspired layout

Run a small deterministic local layout pass over the already visible nodes and
visible explicit edges. Initial positions come from course order on a ring. Each
iteration applies bounded pairwise repulsion, edge attraction, and center pull.
The result is stable across builds and browser runs because there is no random
seed, no timer, and no animation. This is the selected approach.

### Option C: Rename the existing `Cluster` layout

This would be misleading. `Cluster` is generated-group clustering. `Topology`
is relationship clustering. Both are useful and should remain separate.

## User Experience

The graph layout selector adds `Topology` after `Connections`:

- `Connections` remains the default flow layout.
- `Topology` groups pages by explicit link structure.
- `Cluster` groups pages by generated course group.
- `Map`, `Radial`, and `List` keep their current behavior.

In `Topology`, pages connected by explicit `navigation`, `content`,
`prerequisite`, or visible `parent` edges are pulled closer together. Pages that
are not connected repel each other enough to keep labels readable. Hidden groups
and hidden edge kinds are excluded before the topology layout runs, so the
layout reflects the currently visible graph. Search and neighborhood focus keep
their current visible-node behavior.

The layout is a structural readability cue over generated graph data. It must
not imply importance, ranking, recommendation, mastery, or learner state.

## Layout Algorithm

The algorithm runs inside `packages/static/src/raya_static/graph.py` as local
JavaScript:

1. Start with visible nodes sorted by current course-order comparator.
2. Place them on a deterministic ring inside the existing fixed SVG viewBox.
3. Build the active edge list from the same visible edge-kind filtered edges
   used for rendering.
4. Run a fixed small number of synchronous iterations:
   - apply pairwise repulsion between all visible nodes;
   - apply attraction along active edges;
   - apply a weak pull toward the canvas center;
   - clamp every position inside the safe canvas bounds.
5. Return positions through the existing `positionsFor(activeNodes, mode)`
   contract.

The algorithm must be deterministic and bounded. It must not use `Math.random`,
`requestAnimationFrame`, timers, workers, external libraries, runtime fetches,
or storage.

## Architecture

No schema or artifact data change is required. The builder emits one new layout
option in the graph selector and updates the static help text. The graph script
adds a `topology` branch that receives the already visible active edges from
the render path. Existing rendering, arrows, edge-kind filters, group filters,
search, selected-page detail, neighborhood focus, pan/zoom, expanded mode, and
list layout remain unchanged.

## Tests

Contract tests should prove:

- graph HTML includes `<option value="topology">Topology</option>`;
- graph help explains that `Topology` groups by explicit relationships;
- graph JavaScript contains topology layout helpers;
- forbidden runtime tokens such as `Math.random`, `requestAnimationFrame`,
  `fetch(`, `localStorage`, and external graph library names are absent.

Browser tests should prove:

- selecting `Topology` sets `data-raya-graph-layout="topology"`;
- rendered node positions remain inside the SVG viewBox;
- a content-linked pair in the render fixture is closer in `Topology` than an
  unrelated pair;
- hiding the `content` edge kind and returning to `Topology` changes the
  topology positions, proving visible edge filters affect the layout;
- no extra browser requests occur after page load.

## Documentation

Update the learning renderer contract and English/Spanish agent guide pages to
name `Topology` as a deterministic static layout over explicit graph
relationships. Documentation must state that it is a readability cue only, not
importance, ranking, recommendation, mastery, or learner state.
