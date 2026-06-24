# Graph Focus Mode Design

## Context

The current static graph has already adapted most of the useful legacy graph
capabilities without inheriting the old Eleventy/Tailwind/Cytoscape/CDN stack:
local SVG rendering, deterministic layouts, graph search, group and edge
filters, selected-page details, URL-addressable graph state, zoom, pan, Fit,
Fit selection, Reset view, and collapsible list/inspector panels.

The remaining ergonomic gap is desktop focus. The old graph made the canvas feel
primary and easy to scan. The current `Expand graph` button collapses only the
list panel and still reserves a full inspector column, while the toolbar stays
text-heavy. That makes the graph less comfortable on desktop than it should be.

## Goals

- Make `Expand graph` a real graph focus mode on desktop.
- When graph focus mode is enabled, collapse both the Pages list and Inspector
  into narrow accessible rails so the SVG canvas gets the clearest priority.
- Keep each collapsed rail operable: the rail header and expand button remain
  visible, keyboard reachable, and labeled.
- Keep selected-page details, graph filters, search query, visible groups,
  visible edge kinds, neighborhood focus, URL state, and graph data unchanged
  when entering or leaving focus mode.
- Make the graph toolbar denser by replacing the most repetitive visible button
  text with compact glyph-like text while preserving explicit `aria-label`s for
  assistive technology and browser tests.
- Keep mobile and tablet graph layout stacked and readable; focus mode should
  not create hidden or inert side panels in narrow layouts.

## Non-Goals

- No new graph data, graph schema, manifest fields, or source contract changes.
- No persisted graph focus state beyond the existing shareable URL parameter.
- No external icon library, image asset, CDN, Cytoscape, fetch/XHR, worker, or
  runtime graph data load.
- No graph ranking, recommendation, progress, mastery, importance, or personal
  state language.
- No wheel zoom, touch pinch, or kinetic gesture work in this slice.
- No broad course shell or skin redesign.

## Architecture

The implementation stays inside the existing generated static graph surface.

`packages/static/src/raya_static/graph.py` already has:

- `setGraphExpanded(nextExpanded)`;
- `setGraphPanelState(panelName, expanded)`;
- URL state for `expanded`, `list`, and `inspector`;
- focus safety for collapsed panel bodies.

Focus mode should reuse those primitives instead of inventing another state
system. Activating `#graph-expand` should:

- set `data-raya-graph-expanded="true"`;
- collapse the list panel;
- collapse the inspector panel;
- re-render the graph without changing selection, filters, search, or viewport
  more than the existing expanded behavior requires.

Deactivating `#graph-expand` should:

- set `data-raya-graph-expanded="false"`;
- expand both panels;
- preserve selected-page detail and current graph filters.

Direct panel toggles remain valid. If a reader manually reopens a panel while
focus mode is on, the URL/readout should reflect that panel state; focus mode is
not a forced modal.

`packages/static/src/raya_static/rendering.py` should make the expanded
two-rail layout use narrow side columns and a wider center map. It should keep
the existing mobile breakpoint override so graph panels stack normally below
`1280px`.

`packages/static/src/raya_static/builder.py` should keep stable IDs and
`aria-label`s while making visible toolbar labels shorter for dense controls:
for example `+`, `-`, `Reset`, `Fit`, `Fit selected`, `View`, and directional
arrows or compact direction letters. Use ASCII text where practical; do not add
icon dependencies.

## Testing

Use TDD against existing graph contract and browser tests:

- Contract tests confirm the generated toolbar preserves accessible labels and
  includes compact visible control text.
- Browser tests on a desktop viewport select a page, click `Expand graph`, and
  assert:
  - `data-raya-graph-expanded="true"`;
  - list and inspector panel bodies have `aria-hidden="true"`;
  - collapsed panel body controls are not keyboard reachable;
  - the canvas/map panel width increases;
  - selected detail state remains in the graph state readout;
  - search/filter state is not cleared.
- Browser tests click `Expand graph` again and assert both panels are expanded
  and accessible.
- Existing mobile/no-overflow tests continue to prove narrow layouts remain
  stacked and readable.

## Documentation

Update `docs/foundation/20_learning_renderer_contract.md` to describe expanded
graph mode as a non-persistent focus mode that can collapse side panels into
operable rails. Keep it framed as a structural viewport affordance, not
personal progress or recommendation state.

Role docs do not need separate edits in this slice because this is a reader
workspace affordance, not a new authoring or agent workflow.

## Self-Review

- No placeholders remain.
- The design is one focused UX slice: graph focus mode plus compact toolbar
  labels.
- Static contracts, graph payloads, and artifact data remain unchanged.
- Accessibility and no-storage/no-fetch boundaries are explicit.
