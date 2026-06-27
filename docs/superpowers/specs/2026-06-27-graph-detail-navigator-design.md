# Graph Detail Navigator Design

## Context

The reset graph has already absorbed the useful old-main graph ideas in a
contract-safe way: local SVG rendering, fuzzy search, layout controls, visible
relationship types, group filters, minimap, page focus, graph state, panel
collapse, and selected-page inspection. The remaining ergonomic problem is that
the selected-page inspector can become long after adding sections, study
objects, key objects, relationship overview, relationship walkthrough, reading
path, and explicit link lists.

The old graph kept the map primary with compact status and hover feedback. This
slice adapts that principle by making selected-page detail faster to scan and
navigate without changing graph data, adding persistence, or importing the old
browser graph stack.

## Goal

Add a compact page-local navigator at the top of the selected-page graph detail
panel so learners can jump directly to Summary, Relationships, Study, Sequence,
and Links sections.

## Requirements

- Render a `data-raya-graph-detail-nav` region inside the selected-page detail
  panel.
- The navigator is hidden while no page is selected and visible when a selected
  page detail is open.
- Buttons are native `button type="button"` controls.
- Buttons jump within the selected-page detail panel without changing URL,
  storage, graph data, filters, selection, page focus, or learner state.
- Buttons disable when their target section has no visible content for the
  current selected page.
- Button labels expose the section names: `Summary`, `Relationships`, `Study`,
  `Sequence`, and `Links`.
- The selected detail target receives temporary focus after a button click so
  keyboard users land where they jumped.
- The graph inspector collapse behavior must remain intact: hidden panel bodies
  are not keyboard reachable while collapsed.
- No `localStorage`, `sessionStorage`, cookies, `fetch`, XHR, external assets,
  browser-side MathJax, or new artifact data contract.

## Design

The builder emits a static detail navigator immediately after the selected-page
header. Each button points to a semantic section key through
`data-raya-graph-detail-nav-target`.

The graph script owns visibility and enabled state. On each `renderDetail()`,
it computes whether each target is available:

- `summary`: selected page title/summary/meta area is always available;
- `relationships`: relationship overview, relationship chips, walkthrough, or
  explicit link counts are visible;
- `study`: page sections, study objects, or key objects are visible;
- `sequence`: reading path section is visible;
- `links`: outgoing or incoming link list section is visible.

Clicking a button calls a local helper that scrolls the corresponding section
into view and focuses it with `tabindex="-1"` when necessary. This focus is
transient DOM focus only and does not write state.

## Styling

Use the existing graph detail token vocabulary: small pill-like buttons, local
skin colors, visible focus rings, horizontal wrapping on desktop, and compact
stacking on narrow widths. Disabled buttons remain visible but muted so learners
understand that the section exists as a detail category but has no content for
the selected page.

## Testing

Add browser-driven coverage on the render fixture graph:

- graph detail HTML includes the navigator and five native buttons;
- opening a selected page shows the navigator;
- clicking `Relationships` focuses the relationship section and does not change
  URL or storage;
- buttons for available sections are enabled for `reader-ux`;
- collapsing the inspector still removes navigator buttons from tab order;
- graph resources still contain no `fetch`, XHR, `localStorage`, or
  `sessionStorage`.

## Non-Goals

- No accordion behavior in this slice.
- No persisted inspector tab state.
- No new graph data fields.
- No change to graph selection, filters, layout, search, minimap, page focus, or
  generated URL semantics.

## Self-Review

- No placeholders remain.
- Scope is one graph-inspector ergonomics slice.
- The design improves UX while preserving current reset renderer constraints.
