# Graph Workspace Polish Design

## Context

The current static graph surface is contractually allowed to expose generated graph data as a reader-facing discovery workspace. It may show generated page metadata, explicit incoming/outgoing links, local search and filters, hover/focus inspection text, keyboard inspection parity, local viewport controls, and a non-persistent expanded workspace mode.

The legacy `main` graph page is useful as product inspiration but not as architecture. Its CDN Cytoscape dependency, force layout, and browser graph library do not fit the current reset contract. The current renderer must stay local, static, SVG-based, and deployment-neutral.

## Goal

Make `_raya/graph/index.html` feel like a modern, learnable graph workspace rather than a plain control strip above a canvas. The page should prioritize the graph on desktop, keep details and lists scannable, and let learners collapse secondary panels when they need space.

## Current Problems

- Controls, legend, details, graph, and list are stacked in one long column, so desktop space is underused.
- Expanded graph mode only increases canvas height; it does not create a materially better workspace.
- The selected-page detail panel sits above the graph, interrupting inspection flow instead of acting as a side inspector.
- The page list is useful but competes with the graph; it needs a collapsible sidebar role.
- Learners need clear static orientation without fake progress, recommendations, or personal state.

## Proposed Shape

Use a graph workspace shell:

- Top workspace header and compact controls remain above the workspace.
- A central graph stage owns the largest region on desktop.
- A right inspector panel holds selected-page details and hover/focus inspection status.
- A left page list panel holds the generated page list and group filters.
- Legend/help become compact support panels instead of taking prime vertical space.
- Panel visibility is non-persistent state controlled by explicit buttons.
- Mobile remains single-column, with panels stacked and usable.

## Contract Boundaries

Safe now:

- Local SVG graph rendering.
- Local JavaScript only.
- Non-persistent panel toggles.
- Search/filter/layout/zoom/reset controls.
- Public generated page metadata in details and list.
- Explicit incoming/outgoing graph relationships only.
- Hover/focus inspection status and keyboard parity.
- Browser tests for no external requests and no horizontal overflow.

Out of scope:

- Cytoscape or other graph libraries.
- Browser-side MathJax or external renderer/CDN requests.
- Runtime graph fetching.
- LocalStorage/sessionStorage for graph state.
- Progress, recommendations, mastery, adaptive study, ranking, or learner analytics.
- Drag physics or persisted graph positions.

## Test Strategy

- Extend graph e2e coverage so desktop verifies the three-zone workspace and panel collapse behavior.
- Verify graph panels hide their focusable contents when collapsed.
- Verify expanded mode gives the canvas materially more width/height and uses the workspace class/state.
- Keep existing graph checks for local static resources, no fetch/storage, no external requests, search, fuzzy search, selected details, incoming/outgoing lists, viewport controls, and focused `?page=...` handoff.
- Add contract assertions for the new structural markers so renderer output remains intentional.
