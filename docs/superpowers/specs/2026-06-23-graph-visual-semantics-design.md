# Graph Visual Semantics Design

## Context

The legacy `main` graph used Cytoscape to make the graph visually legible:
chapter colors, node size by degree, hover neighborhood emphasis, and concise
status text. The reset renderer already has a static Course graph surface with
embedded artifact data, local JavaScript, fuzzy search, deterministic layouts,
group filters, selected-page details, selected neighborhoods, and no external
graph dependency.

This slice adapts the remaining useful visual semantics without copying the old
runtime model.

## Approaches Considered

### A. Reintroduce a graph library

This would recover drag, zoom, force layouts, and animated hover behavior faster.
It is rejected because it would add an external graph runtime or a vendored graph
engine before the reset contracts require one.

### B. Add visual semantics to the existing SVG graph

This keeps the current static graph architecture, uses only embedded graph data,
and improves readability with group color, degree emphasis, hover status, and
clearer layout copy. This is the selected approach.

### C. Build a separate graph inspection page

This would keep the current Course graph unchanged and put richer diagnostics in
`_raya/inspect/`. It is useful later for agents, but it does not improve the
student-facing graph experience enough for this UX loop.

## Selected Design

The Course graph keeps its current page, payload, and script architecture. The
builder will add static affordance placeholders:

- a status line slot for transient hover context;
- a graph instruction paragraph that names click and double-click behavior;
- group filter buttons with stable group color custom properties.

The local graph script will derive visual semantics from the already embedded
payload:

- group color comes from each node's `group` and the ordered `groups` array;
- degree comes from current generated edges;
- node radius increases modestly with degree so more connected pages are easier
  to spot;
- hovering or focusing a graph/list node sets transient inspected-page state;
- inspected connected nodes and edges receive CSS classes;
- the status line explains the inspected page's group, outgoing link count,
  incoming link count, and connected page count.

Selection remains click-based and continues to drive the detail panel. Hover
inspection is transient only and must not navigate, persist, fetch, or imply
recommendations. Double-click navigation remains available for graph nodes.

## Data Flow

The graph page already embeds `nodes`, `edges`, `groups`, and `backlinks` in
`#raya-graph-data`. The new behavior reads those arrays in the existing
`graph.py` script. It does not change artifact data schemas or fetch graph data
at runtime.

Group color is a deterministic CSS-variable palette derived in the browser from
the group order:

- `--raya-graph-group-1` through `--raya-graph-group-8`;
- fallback to `--raya-color-accent` when a group is missing.

Degree size is bounded so layout remains stable:

- base radius `14`;
- selected radius remains prominent;
- non-selected degree radius is `14 + min(8, sqrt(degree) * 2)`.

## Accessibility And Interaction

SVG node links remain real anchors. The graph script will add accessible names
through each link's existing text and `aria-label` describing the page and link
counts. List rows remain normal links. Hover and focus inspection must be
mirrored so keyboard users can inspect graph/list items without a mouse.

The graph status line remains `aria-live="polite"` and may update with transient
inspection text. The selected detail panel remains the persistent selected-page
summary.

## Boundaries

This slice must not add:

- Cytoscape, D3, Mermaid, CDN resources, fetch/XHR, service workers, or browser
  graph-data storage;
- graph drag, zoom, force physics, or persisted layout preferences;
- inferred related pages, recommendations, mastery, analytics, or progress;
- source-contract, artifact-contract, or schema changes.

## Tests

Contract tests should assert:

- group color semantics are emitted in graph markup or CSS resources;
- graph script contains bounded degree-radius and inspected-node behavior;
- no legacy graph dependency strings are introduced.

Browser tests should verify:

- hovering a graph node updates the graph status with inspected-page context;
- focusing a list row can mark the same page as inspected;
- inspected connected nodes and active edges receive CSS classes;
- selected-node behavior and URL-focused neighborhood behavior still work;
- no external requests happen after graph interactions.

Docs should state that graph color and size are structural readability cues,
not course authority, progress, recommendations, or mastery.
