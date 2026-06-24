# Graph URL State Debug Design

## Context

The current static graph has already absorbed most useful old-main graph UX in a
framework-compatible way: fuzzy search, group chips, multiple deterministic
layouts, selected-page details, relationship-kind filters, hover/focus
inspection, viewport controls, expanded mode, and local SVG rendering without
Cytoscape or CDN requests.

Independent review found the next valuable gap is reproducibility. Old main was
directly manipulable and visually responsive, but a graph view was still hard to
share or debug without redoing every interaction by hand. The current graph
reads only `?page=<page-id>` on load. Search, layout, hidden groups, hidden edge
kinds, selected-neighborhood focus, expanded mode, and panel state are all
transient JavaScript state with no URL representation and no compact state
readout.

## Goal

Make the graph workspace easier for students and agents to reproduce, inspect,
and debug while preserving static/local constraints.

## Design

Add a small "Graph state" readout inside the existing inspector body. It shows
only public, structural UI state:

- selected page stable ID, or `none`;
- current search query, or `none`;
- current layout;
- visible node and visible edge counts;
- hidden group count;
- hidden edge-kind count;
- whether neighborhood focus is active;
- the current share URL.

The share URL is the current page URL after normalization. It is a regular
static URL and does not require a copy button in this slice. Users and agents can
select it from the readout or browser address bar.

The graph script parses these URL parameters on load:

- `page=<page-id>` selects a page when it exists;
- `q=<query>` initializes graph search;
- `layout=<connections|topology|cluster|map|radial|list>` initializes layout;
- `groups=<comma-separated group ids>` means visible groups; omitted means all;
- `edges=<comma-separated edge kinds>` means visible edge kinds; omitted means all;
- `neighborhood=1` enables selected-neighborhood focus only when a selected page
  exists;
- `expanded=1` starts expanded graph workspace;
- `list=0` starts the list panel collapsed;
- `inspector=0` starts the inspector panel collapsed.

As controls change, the graph script updates the browser URL with
`history.replaceState`. It must not write `localStorage`, `sessionStorage`,
cookies, IndexedDB, or fetch anything. URL updates are transient browser history
state over the already loaded static page.

The URL should omit default values to stay readable. Defaults are all groups,
all edge kinds, no query, default `connections` layout, no selected page, no
neighborhood focus, compact graph workspace, and both panels expanded.

## Boundaries

This slice does not add a backend, graph database, copied old-main Cytoscape
runtime, force animation, persistent state, graph ranking, progress, mastery,
recommendations, or a new graph data contract. It does not expose private source
paths, artifact internals, `_official/`, `_assets/`, `_reviewed/`, answer
content, cache keys, or source hashes.

The readout is a debugging and orientation aid. It must not describe hidden
groups, hidden edges, or selected pages as importance, recommendation,
completion, or learner state.

## Testing

Add contract coverage for the new static graph readout markup and URL-state
script tokens while preserving the existing no-fetch, no-storage, no-Cytoscape,
deterministic-script checks.

Add browser coverage that opens a graph URL with `page`, `q`, and `layout`,
asserts those states initialize correctly, toggles an edge kind and a group, and
verifies the URL/readout update without storage or external requests.

Run focused graph tests first, then the render-debug, host, and Docker gates
before committing implementation.
