# Reader Rail Session Persistence Design

## Context

The rebuilt reader shell lets readers explicitly expand or collapse the left
course rail and right learning rail. Those display choices currently reset on
page navigation. A working-tree follow-up restores them from `sessionStorage`,
but its origin-global keys can leak a choice between separate courses served
from the same origin.

The foundation contract permits same-tab storage only for course-map branch
identifiers and explicit left/right reader rail expanded or collapsed display
state. Drawer state, filters, content state, progress, mastery,
recommendations, and authored data remain non-persistent.

## Goal

Preserve explicit reader rail display choices across refresh and same-tab page
navigation without transferring those choices to another course, another tab,
or any durable storage surface.

## Accepted Direction

The shell will derive both reader rail storage keys from the existing generated
`data-raya-course-map-storage-key`. Each key will append a reader-shell segment
and the rail name to that course-scoped base:

```text
raya:course-map:<course-identity>:reader-shell:course-map
raya:course-map:<course-identity>:reader-shell:learning-rail
```

The shell must use the complete generated base key rather than parsing it or
deriving scope from the current page URL. This keeps every page in one course
on the same keys while isolating courses that share an origin and remaining
stable when an artifact is deployed under a different path.

Only the values `expanded` and `collapsed` are accepted. Missing, invalid, or
unreadable values use the current responsive default. Storage read or write
errors must not prevent the shell from initializing or responding to controls.

## Runtime Behavior

On shell initialization, the left and right rails independently read their
course-scoped display values. At structural reader widths, valid values replace
the responsive defaults. At phone widths, the article-first drawer and
accessible learning-context behavior remain authoritative; loading or crossing
responsive boundaries must not overwrite the saved structural preference.

An explicit structural rail control writes only that rail's display value.
Responsive normalization, drawer open or close actions, filter changes, map
orientation, and other shell synchronization paths do not write rail state.
Returning to structural reader geometry restores the saved values.

Opening a second course on the same origin starts from that course's own
responsive defaults until the reader explicitly changes its rails. The shell
does not synchronize state between tabs and relies only on the browser's
tab-session lifetime and isolation semantics.

## Documentation Boundary

Foundation and role guidance will consistently describe explicit course-scoped
left/right rail display state as the only reader-shell persistence exception
besides course-map branch identifiers. The term `volatile` may still describe
drawer, filter, active context, and other transient state, but must not describe
the accepted structural rail display preference. Guidance that categorically
forbids storage for rail collapse must be removed or narrowed.

## Verification

Browser coverage will prove:

- both rail choices survive refresh and same-tab navigation within one course;
- a second course on the same origin does not inherit the first course's state;
- invalid stored values fall back to responsive defaults;
- unavailable `sessionStorage`, failed reads, and failed writes leave both rails
  operable and accessible;
- phone drawer and learning-context behavior remain non-persistent and usable;
- responsive changes do not overwrite saved structural preferences;
- only course-scoped Raya reader-shell keys are written and `localStorage`
  remains untouched.

Contract coverage will reject stale guidance that calls accepted rail display
state volatile or categorically prohibits its storage.

## Non-Goals

- No persistence in `localStorage`, cookies, network services, or authored or
  generated course data.
- No cross-tab or cross-course synchronization.
- No persistence for drawer state, filters, current-page orientation, active
  context, focus, scroll position, progress, mastery, recommendations, or
  personalization.
- No new source course field, artifact data shape, or package boundary.
- No change to rail visuals, responsive breakpoints, or transition timing.
