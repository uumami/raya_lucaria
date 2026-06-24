# Graph Edge Kind Filters Design

## Context

The current static graph already distinguishes edge kinds visually:
navigation links, content references, prerequisite metadata, and parent links.
Recent work also added direction arrows, so the graph now communicates both kind
and direction. The remaining usability gap is that dense pages can still show all
relationship types at once. Students and agents cannot quickly isolate "only
prerequisites" or "only content references" without scanning every line pattern.

Old `main` used a richer graph workspace with explicit controls and filter-like
affordances. The current branch must keep the local static renderer, generated
HTML/JS/CSS, and no external graph dependency.

## Decision

Add local edge-kind filter chips to the graph workspace.

The filters are rendered as static toolbar buttons generated from the current
known edge kinds. The graph script keeps a transient `hiddenEdgeKinds` set in
memory only. Toggling a chip hides or restores matching graph edges and their
arrow markers. Nodes remain visible when their group and search state allow
them, because edge-kind filtering is a relationship lens rather than a page
filter.

## Behavior

- The graph page includes a button group labelled `Edge filters`.
- The default state shows all edge kinds.
- Each chip has `aria-pressed="true"` when that edge kind is visible.
- Toggling a chip updates only the visible SVG edges and marker definitions.
- The graph list and selected-page inspector remain page-based and do not hide
  pages only because an edge kind is hidden.
- Status text reports how many visible graph edges remain and, when relevant,
  how many edge kinds are hidden.
- Reset graph restores all edge kinds.
- List layout keeps the SVG hidden; edge-kind chips still show their current
  state and reset still restores them.

## Constraints

- Do not modify `data/graph.json`.
- Do not add a graph library, fetch, worker, CDN, storage, ranking, or adaptive
  behavior.
- Do not persist filter state.
- Do not remove or rename existing edge kind classes.
- Do not use adaptive-study status language.
- Preserve search, group filters, panel collapse, expand, viewport controls,
  arrows, and edge-kind styling.

## Test Strategy

- Contract tests assert that graph HTML contains edge-filter buttons for the
  known edge kinds and that graph JS contains transient edge-kind filter logic
  without storage.
- Browser tests toggle a kind off and verify matching SVG edges disappear while
  page nodes remain visible.
- Browser tests verify status text mentions hidden edge kind count, arrow
  markers still match visible edges, and reset graph restores the hidden kind.
- Existing render-debug and archive gates cover browser/static parity,
  screenshot artifacts, overflow checks, raw math leakage, and external renderer
  request checks.
