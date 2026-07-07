# Left Rail Minimal Redesign

Date: 2026-07-06

## Context

The current reader left rail is doing too many jobs at the same visual priority:
course map, map section controls, workspace launchers, reader layout controls,
comfort controls, and duplicated workspace cards. The result is crowded,
hard to scan, and visually noisy. The approved V4 direction keeps the rail as a
single navigation surface with course tools as secondary support.

This design replaces the current stacked rail with a minimal, full-height rail
that makes the course map the primary content. It preserves the current static
renderer constraints: no backend, no external resources, and collapse/expand
must reclaim reading space. It adds one narrow same-tab `sessionStorage`
exception so branch expansion state survives refresh and page-to-page
navigation without becoming durable learner progress.

## Goals

- Make the left rail read as course navigation first.
- Keep only one workspace/tool surface.
- Remove duplicated Course Workspaces cards.
- Remove visible `Current`, `All`, `Scan`, and `Less` controls.
- Remove visible `Focus reading` from this rail redesign because map collapse
  and Context collapse already cover the same visible-space use case with less
  UI.
- Keep collapse/expand small, explicit, and keyboard reachable.
- Make the course map usable for deep nesting.
- Make the map use the available page height.
- Make each hierarchy branch independently collapsible.
- Restore branch expansion state after refresh and same-tab page changes.
- Keep colors theme-token driven, not hardcoded to one visual skin.
- Preserve static links and the current page-focused Graph, Practice, Tasks,
  and Schedule handoffs in the single Course Tools surface.

## Non-Goals

- No reader top bar.
- No permanent shell state in `localStorage`.
- No cross-tab or cross-course branch expansion memory.
- No new dynamic study state.
- No new backend, fetch, external icon library, or CDN dependency.
- No graph/workspace feature redesign beyond the left-rail entry points.

## Information Architecture

The expanded left rail uses this order:

1. Header
   - `Course map`
   - structural page position such as `Page 1 of 6`
   - small icon-only collapse button aligned right

2. Course tools
   - one compact tool area
   - Search, Graph, Practice, Tasks, Schedule
   - Context, Text size, OpenDyslexic
   - no visible `Focus reading` button
   - no separate Course Workspaces card section

3. Filter
   - one compact map filter input directly above the tree

4. Course map tree
   - primary rail content
   - flexible height and scrolls inside the rail when needed
   - current page and ancestors are visually distinct
   - nested levels use local numbering that moves with the nested item
   - connectors and indentation show parent/child structure
   - branches with children have a small disclosure affordance
   - branch expansion state is restored within the same browser tab

## Map Tree Design

The V4 map model uses depth-local row layout:

- Each row owns its number marker, connector, and label.
- Nested rows indent as a whole, including their number marker.
- Nested numbers are local to the branch, not compressed as `3.1` / `3.1.1`
  in the root gutter.
- Labels wrap normally inside the remaining row width.
- Deep nesting should remain readable without horizontal overflow.
- Parent rows expose a compact branch toggle that collapses or expands their
  descendants.
- The current page path is expanded by default when no stored branch state
  exists.
- Keyboard users can reach branch toggles and activate them with normal button
  semantics.

This avoids the confusing effect where child numbers appear aligned with
top-level pages.

## Branch State Design

Branch collapse is reader-local orientation state:

- Store only collapsed branch identifiers in `sessionStorage`.
- Scope the storage key to the current course/artifact identity so one course
  does not affect another.
- Restore stored state on page load before applying the default current-path
  expansion.
- Preserve state while navigating between rendered pages in the same tab.
- Preserve state across refresh in the same tab.
- Clear naturally when the tab session ends.
- Do not use `localStorage`, cookies, network calls, generated course files, or
  learner progress records for this behavior.

## Tool Design

Course tools should be compact and secondary:

- Icons should be visually clear and sized to the button.
- Buttons should be small enough to avoid pushing the map down.
- The five workspace buttons use icon-only visible labels, with accessible
  names and hover/focus tooltips.
- Utility buttons such as Context, Text, and Font may use short labels.
- Workspace href behavior currently held by Course Workspaces must be preserved
  in Course Tools: Graph keeps the page-focused graph handoff, and Practice,
  Tasks, and Schedule keep page-focused handoffs when the current page has
  accepted objects or dated task-family objects.

## Collapse Design

Expanded state:

- The rail may use full page height.
- The map tree is the flexible scrolling region and gets its own vertical
  scrolling when course contents are long.
- The collapse affordance is a small header button.

Collapsed state:

- The full rail content is hidden and removed from keyboard/assistive
  navigation.
- The article reclaims the rail column.
- A minimal floating Map opener remains keyboard reachable.
- Opening restores the full rail, map accessibility, and same-tab branch state.

## Code Surfaces

Expected implementation surfaces:

- `packages/static/src/raya_static/builder.py`
  - simplify `_render_course_map_tools`
  - remove visible map action buttons
  - remove Course Workspaces card output from the rail
  - move page-focused workspace href behavior into the single tool surface

- `packages/static/src/raya_static/shell.py`
  - remove unused map action/scan plumbing after visible controls are removed
  - keep current-page orientation, filter behavior, per-node disclosure, and
    collapse accessibility handling
  - persist collapsed branch identifiers in scoped `sessionStorage`
  - restore branch expansion after refresh and same-tab page navigation

- `packages/static/src/raya_static/rendering.py`
  - restyle rail as full-height compact navigation
  - remove retired Course Workspaces and map action styles
  - add depth-local map row layout
  - ensure colors use existing Raya custom properties / skin tokens

- Tests
  - update contract tests that assert removed controls
  - update e2e tests that click removed map action buttons
  - add browser layout checks for no duplicate workspaces, compact tools,
    depth-local nested numbering, no horizontal overflow, and collapse space
    reclaim
  - add browser behavior checks for branch collapse, branch restore after
    refresh, and branch restore after following an internal course page link

## Acceptance Criteria

- Expanded rail shows header, one Course Tools surface, filter, and map tree.
- No `Course Workspaces` section is rendered in reader rail.
- No visible `Current`, `All`, `Scan`, or `Less` map action buttons.
- Course Tools includes the active workspace/tool links and reader utilities.
- Course Tools does not show `Focus reading`.
- Map labels wrap cleanly.
- Nested map row numbers indent with their nested row.
- Deep nesting does not create horizontal overflow.
- Branches with descendants can collapse and expand independently.
- Collapsed branches hide descendants from keyboard navigation and visual
  layout.
- The map tree scrolls inside the rail when the course hierarchy is long.
- Same-tab refresh restores branch expansion state.
- Same-tab navigation to another rendered course page restores branch expansion
  state for that course.
- A fresh tab with no stored state expands the current page path by default.
- Collapsing the map removes the rail column and leaves only the floating
  opener keyboard reachable.
- Expanding restores map list accessibility and current-page orientation.
- Mobile drawer behavior remains modal, focus-trapped, and non-persistent.

## Risks

- Removing Course Workspaces could lose page-focused hrefs for Tasks or
  Schedule if not moved into Course Tools.
- Removing map action buttons requires deleting or retiring tests and JS paths
  that currently verify scan/current/all/less behavior.
- Deep nesting CSS can regress keyboard focus geometry or overflow if row
  indentation is not bounded.
- Icon-only workspace buttons need clear accessible labels and visible focus
  states.
- Branch state can become accidental progress memory if scoped too broadly or
  stored in `localStorage`; keep it in course-scoped `sessionStorage` only.
