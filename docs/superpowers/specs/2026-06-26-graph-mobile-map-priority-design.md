# Graph Mobile Map Priority Design

## Goal

Graph workspaces should show the graph map before dense page and inspector panels on tablet and mobile widths.

## Problem

The desktop graph uses a three-column workspace: pages, map, inspector. When that grid collapses to one column below the desktop breakpoint, source order puts the pages panel before the map. On small screens this pushes the map and canvas thousands of pixels down the page, so a learner who opens the graph sees controls and list content instead of the graph.

## Design

- Keep the current generated HTML, graph data, SVG runtime, URL state, filters, and panel collapse behavior.
- At the existing single-column graph breakpoint, reorder panels visually with CSS:
  - graph map first;
  - pages panel second;
  - inspector third.
- Keep desktop behavior unchanged.
- Do not add storage, new URL state, browser-side graph libraries, or runtime layout persistence.
- Keep all page-list and inspector content accessible after the map.

## Testing

Add a browser e2e regression that opens `_raya/graph/index.html?page=reader-ux` at desktop, tablet, and mobile widths. It should prove:

- desktop still keeps the pages panel before the map;
- tablet and mobile place the map panel before the pages and inspector panels;
- the map begins in the initial viewport on tablet and mobile;
- the selected graph state remains active;
- no local or session storage is used.

## Out of Scope

- Reducing toolbar height.
- Changing graph controls.
- Changing graph panel collapse JavaScript.
- Changing generated graph data or relationship semantics.
