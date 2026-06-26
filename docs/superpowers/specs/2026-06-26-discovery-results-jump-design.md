# Discovery Results Jump Design

## Goal

Search, Practice, Tasks, and Schedule should let readers jump from controls to
results immediately, especially on phones where controls, results, and context
stack vertically.

## Current Problem

The discovery workspaces now render the tool before help material and support
collapsible controls on mobile. Still, a reader who opens a workspace on a
small screen must either scroll past controls or collapse controls manually
before reaching results. The page has useful results, but there is no explicit
static path from controls to the result list.

## Design

Add a small `Results` anchor link inside each controls panel body near the
workspace state/count:

- Search: `#raya-search-results-panel`
- Practice: `#raya-practice-results-panel`
- Tasks: `#raya-tasks-results-panel`
- Schedule: `#raya-schedule-results-panel`

Give each results panel the matching `id` and `tabindex="-1"` so fragment
navigation lands on a stable panel target. The link is a normal local fragment
anchor, not JavaScript. It works in local preview and static deployment, keeps
browser behavior predictable, and requires no persistence or backend.

The existing `Collapse controls` button remains the panel-state control. The
new link is a navigation affordance, not a state toggle. It is visible on
phone-width layouts below `520px`, where controls and results stack vertically
and scrolling cost is highest. It stays hidden on tablet and desktop widths
where the broader workspace layout already has enough horizontal and vertical
space for controls, results, and context.

## Constraints

- No `fetch`, `XMLHttpRequest`, `localStorage`, `sessionStorage`, or external
  resources.
- No progress, mastery, score, ranking, recommendation, grading, or submission
  language.
- Keep existing controls/results/context order and panel toggle behavior.
- Use the current shared discovery panel header style rather than introducing a
  new component system.

## Testing

Use TDD:

1. Contract tests fail until each generated workspace has a results panel `id`,
   `tabindex="-1"`, and a matching link inside the collapsible controls body.
2. Browser tests fail until the phone-width link focuses and scrolls the results
   panel into the viewport.
3. Browser tests also assert the link remains hidden at tablet and desktop
   widths.
4. After implementation, focused discovery and no-overflow tests pass.
