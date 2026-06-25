# Graph Relationship Chip Focus Design

The current graph detail panel already explains the selected page's explicit
relationships through summary chips and walkthrough cards. The chips are useful
orientation cues, but they are inert. This loop turns them into lightweight
local controls so a reader can focus one relationship family without changing
the graph data model or adding learner state.

## Goal

Make selected-page relationship chips in the graph detail panel act as
transient local focus controls for the existing relationship walkthrough.

## Behavior

- Relationship chips render as buttons when a graph page is selected.
- Each chip keeps the existing visible label, such as `Content out 3`.
- Activating a chip marks that chip pressed and shows only matching
  walkthrough cards with the same relationship kind and direction.
- Activating the same chip again clears the focus and restores all walkthrough
  cards.
- Activating another chip switches the focus to that chip.
- The active chip state is volatile DOM state only. It must not write
  `localStorage`, `sessionStorage`, cookies, URL parameters, graph data, or
  artifact data.
- Reset graph, clear selected page, selecting another page, and search-driven
  selection changes clear the active relationship focus.
- Normal page links and existing `Focus` buttons inside walkthrough cards keep
  working.

## Static Constraints

The feature uses only the embedded graph payload and existing generated markup.
It must not add `fetch`, `XMLHttpRequest`, CDN resources, browser-side graph
libraries, backend calls, or schema changes. Relationship groups continue to be
computed from explicit generated edges only.

## Accessibility

Chips use native buttons with `aria-pressed`. The relationship walkthrough
section exposes a polite local status line describing the current focus, such
as `Showing Content out relationships.`. Hidden non-matching cards use the
native `hidden` attribute so they leave the tab order. Keyboard activation uses
normal button behavior.

## Files

- `packages/static/src/raya_static/graph.py` renders chip buttons, tracks the
  active chip key, filters walkthrough cards, and clears focus when graph
  selection changes.
- `packages/static/src/raya_static/rendering.py` styles chip buttons, pressed
  state, focus state, and the relationship focus status.
- `packages/static/src/raya_static/builder.py` may add a status placeholder to
  the graph detail surface if needed.
- `tests/e2e/test_preview_static_read_path.py` proves button semantics,
  filtering, reset behavior, no storage, no URL mutation, no external
  requests, and existing focus links.
- `docs/foundation/20_learning_renderer_contract.md` and role docs describe
  chips as structural local focus controls, not recommendations or progress.

## Tests

Focused e2e tests should prove:

- relationship chips are buttons with `aria-pressed="false"` by default;
- clicking `Content out 3` hides non-matching cards and keeps only the matching
  walkthrough card visible;
- clicking it again restores all cards;
- clicking a different chip switches the active group;
- reset/clear selection removes the active chip state and hides detail UI;
- existing walkthrough page links and node `Focus` buttons remain usable;
- no storage keys are written and the URL does not gain a new relationship
  parameter;
- graph static-resource constraints remain unchanged.
