# Graph Deeplink Orientation Design

## Goal

Graph links such as `_raya/graph/index.html?page=reader-ux` should open with the graph header, orientation summary, and toolbar reachable in the first viewport while still selecting and fitting the linked page inside the graph canvas.

## Problem

The current graph restores `page` URL state and fits the selected node context, but the initial load can scroll the document down to the canvas or result list on tablet and mobile widths. That hides the graph orientation controls before the learner has a chance to understand where they landed.

## Design

- Keep URL state authoritative: `page`, `q`, layout, filters, and neighborhood state still initialize graph state.
- Keep graph fitting: the selected page remains selected and its graph neighborhood remains fitted in the SVG viewBox.
- Suppress document scrolling during initial URL restoration only.
- Preserve explicit user scrolling behaviors:
  - Fit-selection commands may bring the canvas into view.
  - Orientation “details” may bring the details panel into view.
  - Search result keyboard movement may keep the active list row visible.

## Testing

Add a browser e2e regression that opens the graph directly with `?page=reader-ux` at desktop, tablet, and mobile viewports. It should assert that:

- the selected page is active;
- the graph toolbar or orientation summary intersects the initial viewport;
- the page did not jump deep enough to hide both orientation and toolbar;
- no local or session storage is used for this state.

## Out of Scope

- Redesigning the graph workspace layout.
- Changing graph URL parameters.
- Adding persistence beyond the URL.
- Changing explicit user-initiated scroll actions.
