# Reader Shell Contract Hardening Design

## Context

The legacy `main` branch had a richer sidebar experience: hierarchical
navigation, current-page orientation, quick workspace links, a collapsed rail,
and right-side table-of-contents behavior. The current static renderer has
already adapted most of that into the new framework as a course map, command
bar, right learning rail, workspace shortcut cards, keyboard sequence
navigation, and local comfort controls.

Two independent audits found that the current shell is mostly aligned with the
foundation contract, but still has small contract gaps and weak behavioral test
coverage. This slice hardens the shell without importing legacy Eleventy,
Tailwind, persisted sidebar state, service-worker assumptions, Pagefind, theme
switching, browser-side graph fetches, or learner-state semantics.

## Goals

- Keep the current reader shell architecture and visual model.
- Make course-map filtering match rendered page labels only, not hidden stable
  IDs.
- Make course-map Tasks and Schedule shortcut cards page-focused when their
  badges describe accepted objects owned by the current page.
- Add browser assertions for stateful shell behavior that currently relies on
  script-token checks or screenshot-only evidence.
- Preserve non-persistent UI state: no `localStorage`, no `sessionStorage`, no
  graph/search/task/schedule state storage.
- Preserve article-first mobile layout and desktop compact rail behavior.

## Non-Goals

- No off-canvas mobile drawer.
- No persisted sidebar expansion, scroll position, theme, or route state.
- No Pagefind, Eleventy, Tailwind, service worker, or runtime data fetch.
- No new learner progress, recommendations, ranking, mastery, or analytics.
- No broad visual redesign of the course map or learning rail.
- No accordion mode in this slice; dense-map accordion remains a possible later
  enhancement after the current contract is fully verified.

## Options Considered

### Option A: Port legacy sidebar behavior broadly

This would bring over more of old `main` at once, including accordion behavior,
mobile drawers, and persisted state. It is too broad for a safe static-renderer
slice and conflicts with current non-persistent state rules.

### Option B: Add tests only

This would improve evidence for the existing shell, but it would leave known
contract mismatches in place: hidden stable IDs can match course-map filtering,
and current-page Tasks/Schedule shortcut badges can point to whole-course
workspaces.

### Option C: Contract hardening plus focused browser tests

This is the selected design. The implementation changes only the two contract
mismatches and adds browser coverage for existing shell behavior. It makes the
current adapted shell more trustworthy before adding new visual features.

## Design

### Course-Map Filter Semantics

The course-map filter remains a local, transient search input. Its match text
will be limited to rendered navigation text and the generated rendered label in
`data-raya-map-label`. It will stop matching `data-raya-map-node` stable IDs.

This keeps the filter aligned with the foundation phrase "rendered page labels"
and prevents hidden identifiers from becoming a reader-facing search surface.
The stable ID remains present as machine-readable DOM state for current shell
logic and tests, but it no longer participates in the visible map filter.

### Page-Focused Tasks And Schedule Shortcuts

The course-map workspace cards already show direct current-page counts:

- Tasks uses a current-page accepted task-family count.
- Schedule uses a current-page accepted dated task count.

When those direct counts are nonzero, the shortcut href should include
`?page=<current-page-id>`, matching the existing Practice shortcut pattern. If
the count is zero, the link remains the course-level workspace URL.

This makes the card badge and navigation target describe the same scope without
adding personal due-state or recommendation semantics.

### Browser Evidence

Focused e2e coverage will assert behavior that matters to readers:

- desktop page load starts with expanded map state;
- the current map link is visible after automatic orientation;
- Escape collapses the map and the explicit toggle re-expands it;
- compact-map rail still exposes real visible anchors;
- rendered-label filter matches visible labels;
- stable-ID-only filter text does not match when the rendered label does not;
- Tasks and Schedule current-page shortcuts include `?page=` only when page
  counts justify page focus;
- mobile layout stays article-first and Escape does not create an inert hidden
  learning rail state.

Contract tests will assert the static href and script-level filter semantics.

## Self-Review

- No placeholders remain.
- Scope is limited to reader shell contract hardening, not a sidebar redesign.
- The design follows current static-renderer constraints and rejects legacy
  persistence and runtime dependency assumptions.
- The requirements are testable in contract and browser tests.
