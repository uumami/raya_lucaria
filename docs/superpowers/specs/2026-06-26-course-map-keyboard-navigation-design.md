# Course Map Keyboard Navigation Design

## Context

The current learning shell renders a static hierarchical course map with local
section controls, filter, scan mode, desktop collapse, and mobile drawer
behavior. The map is structurally useful, but keyboard users still have to tab
through every map target and toggle. That makes large courses feel rough even
when the map is visually compact.

Foundation contract `docs/foundation/20_learning_renderer_contract.md` allows
volatile local course-map controls, filtering, current-path expansion, scan
mode, drawer behavior, and non-persistent UI state. This change stays inside
that boundary: it adds local keyboard movement over already rendered map links
and toggles without browser storage, runtime fetches, new data files, or
learner-state semantics.

## Design

Course-map keyboard navigation applies only when focus is already inside the
rendered map list. It does not intercept global previous/next page shortcuts
when the reader is focused in the article, command bar, learning rail, or an
editable control.

Visible course-map links form the movement set. Hidden nodes from collapsed
sections, filtered results, desktop collapsed map state, or closed mobile
drawers are skipped. The map keeps real anchors as navigation targets and real
buttons as section toggles; no custom ARIA tree role is introduced because the
existing DOM is a navigation landmark with links and buttons.

Keyboard behavior:

- `ArrowDown` focuses the next visible map link.
- `ArrowUp` focuses the previous visible map link.
- `Home` focuses the first visible map link.
- `End` focuses the last visible map link.
- `ArrowRight` expands the focused node when it has children and is collapsed;
  when already expanded, it focuses the first visible child link.
- `ArrowLeft` collapses the focused node when it has expanded children; when it
  has no expanded children, it focuses the nearest visible parent link.

The behavior respects scan mode. Expanding a node with `ArrowRight` while scan
mode is active uses the same sibling-collapse path as pointer toggles, so scan
mode remains a narrow branch-reading workflow. Filtering remains local and
non-persistent; arrow movement operates over the filtered visible links.

## Implementation Notes

The shell script should add focused helper functions near existing course-map
helpers:

- visible-link collection for `#raya-course-map-list`.
- node/link lookup for the focused map item.
- parent and first-child link helpers.
- one keydown handler attached to `#raya-course-map`.

The handler must avoid editable targets, modifier-key chords, and targets
outside the map list. It must not use `localStorage`, `sessionStorage`,
`fetch`, `XMLHttpRequest`, external libraries, or browser-side renderer
requests.

## Testing

Contract coverage should confirm the generated local shell resource contains
the keyboard navigation helpers and still avoids storage/fetch APIs.

Browser coverage should use the existing nested minimal-course fixture and
verify:

- `ArrowDown`, `ArrowUp`, `Home`, and `End` move focus among visible map links.
- `ArrowRight` expands a collapsed branch and then moves to its first child.
- `ArrowLeft` moves from a child to its parent, then collapses the parent.
- Movement skips hidden collapsed branches.
- Keyboard expansion in scan mode preserves sibling-collapse behavior.
- No local/session storage keys are written.

## Out of Scope

This does not redesign visual styling, introduce course-map persistence, add a
full ARIA tree widget, change course schemas, or add learner progress. Broader
visual course-shell redesign remains a separate UX/UI loop.
