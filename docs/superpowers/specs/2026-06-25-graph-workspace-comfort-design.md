---
id: superpowers-graph-workspace-comfort-design
title: Graph Workspace Comfort Design
status: accepted
---
# Graph Workspace Comfort Design

## Context

The legacy `main` branch has useful UX patterns: an app-like shell, collapsible rails, graph search, layout controls, fit/reset, group filters, and hover neighborhood spotlighting. Its implementation is not reusable as architecture because it depends on Eleventy, Tailwind, CDN Cytoscape, CDN fonts/renderers, old source paths, and localStorage-heavy state.

The current `new_rayalucaria` renderer already owns the accepted static graph surface: local SVG graph rendering, generated artifact graph data, search, layout modes, group and edge filters, panel collapse, focus mode, URL state, and no browser-side fetch/CDN behavior. The next improvement should preserve those contracts while making the graph workspace feel less diagnostic and easier for students to use.

## Goal

Make the generated Graph workspace controls clearer and more comfortable without changing graph data, graph semantics, persistence rules, URL state, or static deployment behavior.

## Design

This slice improves the graph toolbar and pan controls only. It does not add a graph library, fetch data at runtime, store graph state, or change layout algorithms.

The Graph workspace will expose clearer student-facing control groups:

- `Find pages` for search and layout.
- `Relationship filters` for edge-kind buttons.
- `Canvas view` for fit, zoom, and viewport reset.
- `Move canvas` for pan buttons.
- `Workspace` for reset and focus mode.

Pan controls will keep their existing `data-raya-graph-pan` attributes and keyboard behavior, but their visible labels will use familiar direction symbols instead of `L`, `R`, `U`, and `D`. Accessible labels remain explicit English phrases such as `Pan graph left`.

The toolbar CSS will be tuned to scan like a compact control surface:

- group labels are visually distinct but not oversized;
- primary search/layout controls get more width on desktop;
- pan buttons use stable square dimensions;
- mobile controls wrap cleanly without horizontal overflow;
- no text becomes dependent on viewport-scaled font sizes.

## Non-Goals

- No Cytoscape, D3, Mermaid, Pagefind, Google Fonts, or CDN resources.
- No browser-side graph data fetching.
- No localStorage/sessionStorage for graph state.
- No change to generated graph data, edge kinds, node IDs, links, or URL parameters.
- No progress, mastery, ranking, recommendation, or personalization wording.

## Verification

Contract tests should assert the generated Graph HTML contains the new group labels, preserved data attributes, preserved local-only scripts, and direction-symbol pan controls with accessible labels.

Browser tests should assert the toolbar remains visible, does not overflow on desktop or mobile, pan controls keep stable square hit targets, and focus mode still collapses the list and inspector into the existing compact graph view.
