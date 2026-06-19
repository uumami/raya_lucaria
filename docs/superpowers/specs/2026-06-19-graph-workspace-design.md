# Graph Workspace Design

## Context

The legacy `main` branch had a richer graph page: fuzzy search, multiple layouts,
chapter filters, neighborhood highlighting, a status line, tooltips, and an
expand control. It depended on Cytoscape from a CDN and old path/chapter data, so
the implementation cannot be copied into the reset renderer.

The reset branch already has a local static graph surface under `_raya/graph/`.
It reads embedded manifest-derived graph data, renders an SVG map or list view,
uses local JavaScript, and avoids external requests. The next useful slice is to
make that graph feel like an actual learning workspace while preserving the
static artifact contract.

## Decision

Adapt the legacy graph UX into the reset renderer with three local-only features:

- fuzzy search over page title, navigation title, stable ID, status, group title,
  and hierarchy label;
- selected-node details with outgoing links, incoming links, status, group, and a
  clear action;
- an expanded graph workspace mode that gives the graph more vertical room
  without using fullscreen APIs or storing state.

This slice keeps the current SVG renderer. It does not add Cytoscape, Pagefind,
fetch, XHR, CDN assets, localStorage graph state, service workers, inferred
recommendations, progress, or browser-side math rendering.

## Behavior

The graph page will:

- keep the existing map, radial, and list layout modes;
- add `Expand graph` / `Compact graph` controls that toggle a local
  `data-raya-graph-expanded` attribute and keep the page static-file-safe;
- improve search so typo-tolerant matches such as `matrx` still find `Matrix`;
- preserve visible neighbors of matching nodes so search remains contextual;
- let users select a node from the SVG or list without immediately navigating;
- show a detail panel for the selected page with page link, status, group,
  outgoing links, incoming links, and an explicit clear button;
- keep normal page navigation available through links in the detail panel and
  graph list;
- reset search, group filters, selected node, expanded mode, and layout through
  the existing reset control.

Selection is non-persistent UI state. Search and expanded mode are also
non-persistent UI state.

## Out Of Scope

This slice does not implement pan/zoom, dragging, force-directed layout,
object-level graph nodes, wikilinks, cross-course graph, graph recommendations,
personal progress overlays, graph-aware tutors, or persisted graph preferences.

## Testing

Contract tests should require the new graph detail panel, expanded control,
script tokens, and no external graph dependencies. Browser tests should verify:

- fuzzy search finds a deliberately misspelled query and keeps at least one
  matching node visible;
- selecting a graph node populates the detail panel without navigating away;
- incoming and outgoing lists render when graph data has those links;
- `Expand graph` toggles graph workspace state and increases graph area;
- reset clears selected node, search, filters, expanded mode, and layout;
- no external requests occur during graph interactions;
- desktop and mobile graph pages have no horizontal overflow.

Role docs should describe graph search/detail as generated course structure, not
personal progress or recommendations.
