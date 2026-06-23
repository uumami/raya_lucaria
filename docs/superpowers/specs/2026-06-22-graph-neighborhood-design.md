# Graph Neighborhood Design

## Context

The current static Course graph already renders from embedded artifact graph data,
supports local fuzzy search, group filter chips, map/radial/list layouts, and a
selected-page detail panel. Legacy `main` made graph exploration feel clearer by
surfacing neighborhoods and group-oriented graph context. The reset renderer
should keep the current static architecture and add the missing feedback where a
reader asks: "what is connected to this page?"

## Goal

Make selected-page neighborhoods visible and scannable on the static graph page
without changing graph schemas, adding external libraries, or persisting graph
state.

## Requirements

- Use only the embedded graph payload already written into `_raya/graph/index.html`.
- Preserve current group chips, search, layouts, fit/reset, expand, URL page focus,
  list navigation, and double-click page navigation.
- Add a selected-neighborhood summary to the detail panel with outgoing,
  incoming, and connected-page counts.
- Mark nodes and list rows connected to the selected page with a distinct
  `is-neighbor` state while keeping the selected page and search match states.
- Add a legend item for "Connected page" so the visual state is named.
- Keep all graph UI state non-persistent. Do not use fetch/XHR, CDN resources,
  browser-side graph computation beyond the embedded payload, localStorage,
  recommendations, progress, mastery, or inferred relationships.

## Design

The builder adds static placeholders and legend markup:

- a legend swatch with `data-raya-graph-legend="neighbor"`;
- a paragraph in the detail panel with
  `class="raya-graph-detail-neighborhood"` and
  `data-raya-graph-detail-neighborhood`.

The existing graph script computes selected-page relationships from the embedded
`edges` and `backlinks` arrays it already uses for the detail lists. On each
render it derives:

- outgoing edge count;
- incoming edge count;
- unique connected page count, excluding the selected page itself.

When no page is selected, the detail panel remains hidden and the neighborhood
summary is empty. When a page is selected, the summary reads:

```text
Neighborhood: 3 outgoing link(s), 1 incoming link(s), 4 connected page(s).
```

SVG nodes and list rows get `is-neighbor` when their node id is connected to the
selected page. Existing `is-selected`, `is-match`, and muted-node behavior stays
intact.

## Accessibility And UX

The summary is real text in the selected-page detail panel, not only color. The
legend names the visual state. The list state mirrors the graph state so readers
in list layout or keyboard navigation still see which pages are connected.

The wording is structural: "outgoing", "incoming", and "connected page(s)".
It does not imply recommendations, next steps, progress, or mastery.

## Testing

Contract tests must assert the graph surface includes the new legend and detail
summary placeholder.

Browser tests must assert that loading the graph with
`?page=authoring-matrix`:

- opens the selected-page detail panel;
- shows the expected neighborhood summary;
- marks expected connected list rows as `is-neighbor`;
- marks the selected list row as `is-active`;
- preserves no external requests after page load.

## Out Of Scope

- New graph layouts or physics.
- Schema changes to `data/graph.json`.
- Merging prerequisites and content links into new relationship taxonomies.
- Runtime persistence of selected page, group filters, search, or layout.
