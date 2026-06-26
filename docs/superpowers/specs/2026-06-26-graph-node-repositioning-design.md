---
id: superpowers-graph-node-repositioning-design
title: Graph Node Repositioning Design
status: accepted
---
# Graph Node Repositioning Design

## Context

The legacy `main` branch graph allowed direct node dragging through Cytoscape.
The current static SVG Graph workspace already has local node repositioning for
mouse users, but `docs/foundation/20_learning_renderer_contract.md` only names
pointer drag panning. That leaves a useful legacy-inspired affordance present
in code and browser tests but not accepted by the current authority surfaces.

## Goal

Accept node repositioning as a constrained graph readability affordance:
students may temporarily move visible SVG graph nodes to untangle a local view,
without changing graph data, course order, URL state, storage, filters,
selection, or authored relationships.

## Design

Node repositioning remains local display state in the Graph workspace only. It
is allowed when all of these are true:

- the graph is in an SVG layout, not `List`;
- the interaction starts from a visible graph node;
- the pointer is a mouse pointer or equivalent desktop mouse event;
- the dragged position is constrained inside the current SVG graph bounds;
- connected visible edge geometry updates while the node moves.

The behavior does not persist. `Reset graph` clears manual node positions.
`Fit`, `Fit selection`, zoom, and pan may change the viewBox but must not clear
manual node positions. Search may preserve a manual node position when the node
remains visible and clamps it into the active view if needed. Touch pointer
events must not start node repositioning so touch users keep normal page and
canvas behavior.

Node repositioning is not a layout editor, authoring tool, recommendation,
ranking, progress signal, mastery signal, or course-data mutation. It is the
same kind of transient visual aid as pan and zoom.

## Verification

Existing browser coverage should remain the behavioral source of truth:

- mouse drag changes a visible node position;
- connected visible edge geometry updates;
- URL and browser storage do not change;
- `Fit` preserves manual position;
- search keeps the moved node inside the active graph view;
- `Reset graph` restores generated layout position;
- touch pointerdown does not start node repositioning.

This loop adds contract/documentation assertions so the accepted behavior and
constraints cannot silently drift away from the implementation.
