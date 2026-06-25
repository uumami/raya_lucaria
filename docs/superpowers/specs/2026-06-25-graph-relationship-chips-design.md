# Graph Relationship Chips Design

## Context

The current graph inspector can show a selected page, direct outgoing links, incoming links, study objects, sequence links, and relationship counts. The information is accurate, but the relationship kinds are only visible as small text beside each linked page. A learner has to scan both lists to understand whether the page is connected by navigation, content reference, prerequisite, or parent structure.

The old `main` branch emphasized graph orientation and relationship affordances, but depended on a browser graph library and older static assumptions. This design keeps the reset framework's local SVG graph and adds a compact static inspector summary.

## Decision

Add a relationship chip strip to the graph inspector for the selected page. The strip summarizes visible direct relationships by kind and direction using the graph data already embedded in the page. It is rendered by the existing local `graph.js` script and does not add a new artifact data contract.

## Behavior

- The inspector includes a `Relationship types` section below the explicit link count.
- Selecting a page renders compact chips for each relationship kind touching the page.
- Chips are grouped by direct relationship kind and direction:
  - outgoing navigation
  - incoming navigation
  - outgoing content
  - incoming content
  - outgoing prerequisite
  - incoming prerequisite
  - outgoing parent
  - incoming parent
- Each chip shows a human label and count, for example `Content out 2` or `Navigation in 1`.
- Chips use the same semantic relationship kind names as the graph edge filters and legend.
- Empty selections hide the chip strip.
- Manual selection, search selection, page-scoped graph entry, reset graph, filters, and layout changes continue through the existing selected-page paths.

## Boundaries

- No new course source syntax.
- No new `data/*.json` schema.
- No browser storage.
- No external requests, graph libraries, CDN assets, or browser-side renderer dependencies.
- No learner-state claims; the chips are structural graph orientation only.

## Testing

Tests should fail before implementation:

- graph HTML includes a relationship chip container for the inspector
- graph script contains the relationship chip rendering path
- selecting `authoring-matrix` shows chips for expected kinds and directions
- the chip total matches the selected page's visible outgoing and incoming relationship count
- reset graph hides or empties the chip strip
- the static graph still makes no external runtime requests

## Non-Goals

- No graph minimap.
- No relationship filtering from the chips.
- No persisted inspector state.
- No graph data model change.
