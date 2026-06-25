# Page-Scoped Graph Entry Design

## Context

Reader pages already link to the graph with `?page=<page-id>`. The graph currently reads that URL state, selects the page, and exposes its detail panel. The next UX improvement is to make that entry point immediately useful: when a learner arrives from a page, the graph should frame that page and its nearby relationships instead of showing the full-course graph first.

The old `main` branch emphasized graph discoverability, fit/reset controls, and visual orientation, but used Cytoscape from a CDN. This design adapts the orientation principle into the reset renderer's local SVG graph.

## Decision

When graph initialization receives a valid `page` query parameter and the active layout is a graph layout, the local graph script will automatically fit the selected page neighborhood after the first render. This is a viewport-only change. It does not change graph data, filters, selected page, search query, learner state, or persisted preferences.

## Behavior

- `/_raya/graph/index.html?page=<id>` selects `<id>` as today.
- After first render, the SVG `viewBox` frames the selected page and directly connected visible graph context using the same bounds as `Fit selection`.
- The selected page detail panel remains open.
- `#graph-fit-selection` is enabled.
- The graph state readout exposes entry context as `Page focus: <id>` so the user and tests can distinguish page-scoped entry from ordinary manual selection.
- The URL keeps `page=<id>` and does not add a separate viewport parameter.
- Manual `Fit`, `Reset view`, `Reset graph`, layout changes, search, and neighborhood focus continue to work through existing paths.
- If the selected page is invalid, hidden by filters, or the layout is `list`, the graph falls back to existing behavior without errors.

## Boundaries

- No new data indexes or course source syntax.
- No storage.
- No external graph libraries, CDN calls, browser-side fetch, or renderer services.
- No automatic learner guidance claims; this is only graph viewport orientation.

## Testing

Tests should fail before implementation:

- opening the graph with `?page=authoring-matrix` should produce a narrower viewBox than the full graph view
- the selected node and at least one active connected edge should be visible in the viewport
- `Fit selection` should be enabled
- graph state should include `Page focus: authoring-matrix`
- `Reset view` should restore the full graph view while preserving selected page and detail panel
- `Reset graph` should clear page focus and selected details

## Non-Goals

- No persisted viewport.
- No minimap.
- No graph algorithm change.
- No change to page link generation beyond existing `?page=` links.
