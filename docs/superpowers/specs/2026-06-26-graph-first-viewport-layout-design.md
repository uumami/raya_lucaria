---
id: superpowers-graph-first-viewport-layout-design
title: Graph First-Viewport Layout Design
status: accepted
---
# Graph First-Viewport Layout Design

## Context

The current Course Graph already follows the reset architecture: graph data is
generated at build time, the browser uses a local SVG renderer, scripts are
served from the artifact, and tests reject Cytoscape, runtime fetches, storage,
and external requests. It also has richer reset-safe behavior than the legacy
main graph: fuzzy search, relationship filters, deterministic layouts,
collapsible list and inspector panels, hover/focus previews, keyboard opening,
zoom/pan controls, focus mode, relationship walkthroughs, and local graph
palette tokens.

The remaining UX problem is first-viewport access. On a 1440x950 desktop
viewport, the graph workspace starts around 403px and the SVG canvas starts
around 603px. Students see the command bar, title, full toolbar, instructions,
status, and orientation chrome before they see the visual map. Legacy main
treated the graph as a large viewport workspace; that principle is useful, but
its Cytoscape, Eleventy, Tailwind, CDN, and browser-runtime assumptions are not.

## Goal

Make the current static Course Graph feel graph-first on desktop by bringing
the workspace and SVG canvas into the first viewport while preserving all
current graph behavior and static-renderer constraints.

## Design

Define a first-viewport layout contract for the graph page:

- the graph workspace should start soon after the command bar and compact page
  heading;
- the SVG canvas should be visible without scrolling on desktop;
- the toolbar should remain keyboard-reachable and readable, but it should use
  compact spacing and not dominate the viewport;
- the instructional sentence should be compact and should not add a full block
  of vertical chrome before the map;
- the status and orientation surface should stay in the map panel, but with
  tighter vertical spacing;
- list and inspector collapse, focus mode, search, layout selection,
  relationship filters, graph previews, zoom/pan, graph data, and local skins
  must keep working.

This is a CSS/layout slice. Generated graph payloads, schema, graph algorithms,
and JavaScript state models do not change unless tests reveal a direct layout
bug in existing markup.

## Expected Behavior

On `_raya/graph/` at 1440x950:

- the graph workspace starts above 340px;
- the SVG canvas starts above 520px;
- the SVG canvas has a useful visible height;
- the list panel, map panel, inspector panel, toolbar, and command bar remain
  visible and keyboard-reachable;
- horizontal overflow remains absent.

On mobile and tablet:

- the graph workspace remains single-column;
- controls remain reachable;
- the canvas remains visible and no horizontal overflow is introduced.

## Non-Goals

- No Cytoscape or external graph library.
- No Pagefind, service worker, CDN, remote font, Mermaid runtime, KaTeX runtime,
  or browser-side MathJax.
- No graph data, schema, ranking, recommendation, progress, storage, or
  personalization changes.
- No broad rewrite of graph interactions.
- No change to authored course content or graph payload semantics.

## Verification

Use TDD with a focused Playwright regression that fails against the current
layout because the graph canvas starts too low. After the CSS layout change,
run the focused graph surface test, the graph collapse/focus checks already in
the static-read-path suite, and `./scripts/check-render-debug.sh`. Request an
independent code review before committing.
