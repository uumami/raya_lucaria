# Graph Mobile Overflow Design

## Goal

Keep the mobile graph command strip horizontally scrollable inside its own toolbar without creating document-level horizontal scrolling.

## Context

The old `main` graph UX uses dense controls and graph search/filter affordances. The current reset renderer already adapts those ideas with a dependency-free static SVG graph, compact mobile toolbar, URL-backed graph state, no local storage, and no external rendering dependency.

Fresh mobile inspection at `390x844` showed `document.documentElement.scrollWidth` growing far beyond the viewport while the graph toolbar was internally scrollable. That makes the page feel rough on phones and contradicts the current visual/layout test pattern that reader-facing pages should not create body-level horizontal overflow.

## Design

On mobile widths, the graph toolbar remains a single horizontal command strip. The toolbar itself may scroll horizontally, but the page root must stay viewport-width. The fix should constrain the toolbar within the graph page grid/flex context and prevent its wide flex contents from contributing to document intrinsic width.

The behavior is intentionally local:

- No new JavaScript state.
- No local storage or session storage.
- No URL contract change.
- No graph data or layout algorithm change.
- No browser-side renderer dependency.
- No external assets or CDN requests.

## Acceptance Criteria

- At `390x844`, `document.documentElement.scrollWidth - window.innerWidth <= 1`.
- The graph toolbar still has internal horizontal overflow so late controls remain reachable.
- The mobile toolbar stays compact enough for the map to remain near the first viewport.
- Existing graph deep-link, map-priority, toolbar, and render-debug checks remain green.

