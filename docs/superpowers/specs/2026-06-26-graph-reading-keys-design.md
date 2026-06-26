---
id: superpowers-graph-reading-keys-design
title: Graph Reading Keys Design
status: accepted
---
# Graph Reading Keys Design

## Context

The current Graph workspace has converged most useful legacy graph behavior:
local search, deterministic layouts, visible relationship filters, group
filters, a legend, panel collapse, preview/inspection, URL state, and local SVG
interaction. A current first-viewport screenshot shows the graph is usable but
dense. The student must combine the toolbar, orientation band, hidden quick
guide, and inspector legend to understand the graph.

The legacy `main` graph had a simpler visible controls-and-legend model. Its
implementation is rejected because it used legacy Eleventy/Tailwind surfaces
and a CDN Cytoscape dependency, but the UX principle remains useful: graph
reading cues should be visible near the graph, not only in a side inspector or
closed help disclosure.

## Goal

Add a compact, always-visible Graph reading keys strip above the SVG canvas so
students can quickly interpret graph marks, relationship direction, selection,
and filters without opening hidden help.

## Design

The Graph page gains a small `Graph reading keys` region immediately after the
Graph header and before the heavier toolbar/workspace controls. This keeps the
cue in the first viewport on desktop and mobile. It contains four compact cards:

- `Pages` explains that circles are course pages and color follows course
  groups.
- `Arrows` explains that arrows point from source page to target page.
- `Selection` explains that clicking once inspects a page and double-clicking
  or pressing Enter opens it.
- `Filters` explains that relationship filters hide visible marks only and do
  not change source data.

The existing detailed `Graph quick guide` remains a native closed disclosure
below the canvas for deeper help. The inspector legend remains available. The
new strip is a first-viewport cue, not a replacement for the detailed guide or
legend.

The strip is static generated HTML and CSS only. It does not add state,
storage, fetches, URL parameters, external resources, graph data fields, or
learner-state semantics. A small graph runtime cleanup fix may prevent stale
inspection previews from reopening after filters hide the previewed graph node.

## Non-Goals

- No graph data/schema changes.
- No browser-side graph library or external request.
- No localStorage/sessionStorage.
- No progress, mastery, ranking, recommendation, personalization, or importance
  wording.
- No replacement of the existing detailed quick guide, inspector legend, or
  relationship walkthrough.
- No mobile-only redesign of the graph workspace in this slice.

## Verification

Contract and browser tests should prove:

- the generated graph HTML includes `data-raya-graph-reading-keys` and four
  named reading-key cards;
- the reading keys appear above the SVG canvas and inside the first viewport on
  desktop and mobile;
- the text avoids learner-state and recommendation language;
- the detailed `Graph quick guide` remains a closed native disclosure with its
  cards hidden until opened;
- the graph page still uses local scripts only and makes no external renderer
  requests.

Run the focused graph e2e test, render-debug gate, and then the normal host and
Docker gates before pushing.
