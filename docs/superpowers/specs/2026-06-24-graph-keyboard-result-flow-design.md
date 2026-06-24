# Graph Keyboard Result Flow Design

## Context

The current graph workspace already has static fuzzy search, group filters,
deterministic layouts, a visible page list, SVG map inspection, selected-page
details, and workspace panel collapse controls. The legacy `main` graph used a
stronger interactive loop: search changed graph emphasis immediately, and graph
nodes were easy to act on. The reset renderer should keep that usefulness while
remaining static, local, and non-persistent.

Keyboard users can currently tab into visible page links and inspect them, but
there is no fast search-result flow from the search input itself. A learner who
types a query should be able to move through the resulting pages without leaving
the search field, see the same active page in the list, map, and detail panel,
and open the active page intentionally.

## Goals

- While focus is in the graph search input, `ArrowDown` and `ArrowUp` move an
  active cursor through currently visible graph page results.
- The active cursor wraps within the visible result set.
- The active result is reflected in the list with a dedicated active class and
  `aria-current`.
- The active result updates graph inspection and selected-page details so the
  SVG, list, and inspector stay synchronized.
- `Enter` in the search input opens the active visible page only when an active
  result exists.
- Changing the query resets the active cursor to the first visible result.
- Empty result sets clear active state and do not navigate.
- The flow is transient UI state only: no local storage, no fetch/XHR, no graph
  state persistence, and no progress/recommendation language.

## Non-Goals

- No new graph data schema.
- No ranking, adaptive recommendations, learner progress, or personal next-step
  language.
- No external graph library, browser-side fetch, worker, CDN, or storage.
- No change to generated course order, page URLs, or artifact data.
- No shortcut help overlay in this slice.

## Architecture

`packages/static/src/raya_static/graph.py` owns the static graph behavior. Add a
small active-result state around the existing visible list IDs:

- `activeResultId` stores the transient active page ID.
- `currentVisibleListIds()` reads currently visible list item IDs from the DOM.
- `setActiveResult(nodeId, options)` synchronizes list classes, `aria-current`,
  inspection, selected-page details, and optional scroll/focus behavior.
- `moveActiveResult(delta)` advances within currently visible list IDs and wraps.

The search input handles keyboard movement directly because the learner's
current task starts there. `ArrowDown` and `ArrowUp` prevent page scrolling and
move the active result. `Enter` opens the active result URL only when an active
visible result exists. Query changes reset `activeResultId`, run the normal
render, and then activate the first visible result if present.

List links should remain normal anchors. The active result class is only a
transient visual cue and should not replace selected-page styling.

## Testing

Use TDD against the existing graph browser fixture:

- Contract test confirms the generated graph script exposes the active-result
  helpers/classes.
- Browser test searches `matrix`, presses `ArrowDown` in the search input, and
  verifies the first visible result becomes active in the list and selected in
  the detail panel.
- Browser test presses `ArrowDown` again and verifies the active result changes.
- Browser test presses `ArrowUp` and verifies wrap/backward movement.
- Browser test presses `Enter` and verifies navigation goes to the active page.
- Browser test searches a no-result query and verifies Enter does not navigate.
- Existing no-fetch/no-storage/static-resource assertions continue to cover the
  reset constraints.

## Documentation

Update the learning renderer contract and EN/ES agent guides to mention
keyboard result flow as a local structural graph navigation aid. Keep wording
clear that it is not ranking, progress, recommendation, or learner state.

## Self-Review

- No placeholders remain.
- Scope is limited to graph keyboard result flow.
- The design preserves static renderer constraints and current graph data
  contracts.
- The behavior is testable through generated script assertions and Playwright.
