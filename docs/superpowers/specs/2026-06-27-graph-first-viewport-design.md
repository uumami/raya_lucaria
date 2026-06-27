# Graph First Viewport Design

## Purpose

Make the generated Graph workspace behave like a first-screen learning tool. When a student opens `_raya/graph/index.html?page=<page-id>`, the selected graph page and at least one active relationship should be visible in the browser viewport without manual scrolling.

## Current Evidence

Fresh probes of the render fixture show that the graph SVG viewBox frames the selected node, but the surrounding page chrome pushes the SVG and selected node below the browser viewport:

- `1440x900`: selected `reader-ux` node starts near `y=1024`.
- `1024x768`: the SVG canvas itself starts below the viewport.
- `390x844`: selected `reader-ux` node starts near `y=934`.

The foundation contract already requires page-focused graph handoffs to first-paint visible selected graph content and keep the graph canvas height bounded relative to the viewport.

## Design

Adapt the useful old-main pattern of treating the graph as a viewport-sized work surface, but keep the current static framework:

- no Cytoscape or external graph library;
- no runtime fetches;
- no browser storage for graph state;
- no recommendation, progress, ranking, mastery, or personalization semantics.

The current page keeps its command bar, reading keys, toolbar, orientation band, legend, and side panels. The layout changes are CSS-only:

- reduce graph-page vertical padding and top margins;
- make desktop graph workspaces a bounded viewport work area;
- make the map panel use grid rows so the SVG canvas receives the remaining first-viewport height;
- keep orientation and legend compact and scrollable when their contents are wide;
- on mobile/tablet, keep map-first ordering and reduce pre-canvas chrome so the selected node is visible without scroll.

## Tests

Add focused browser coverage to `tests/e2e/test_preview_static_read_path.py`:

- open `/_raya/graph/index.html?page=reader-ux`;
- assert no horizontal overflow;
- assert selected graph node and at least one active edge intersect the browser viewport before any manual scroll;
- assert selected node is still in the SVG viewBox;
- assert canvas height is bounded and useful for desktop/tablet/mobile;
- assert no localStorage or sessionStorage keys are written.

Keep existing render-debug checks as the visual/static parity gate.

## Out of Scope

- New graph semantics.
- New graph data fields.
- Reordering graph details or relationship logic.
- Replacing current graph rendering with old-main Cytoscape.
- Persisted graph viewport or panel state.
