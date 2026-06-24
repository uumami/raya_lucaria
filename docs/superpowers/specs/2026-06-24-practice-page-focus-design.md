# Practice Page Focus Design

## Goal

Carry page context from Search and Graph into the generated Official Practice
workspace without adding browser-side fetching, storage-backed state,
recommendations, or learner progress.

## Design

Generated discovery payloads already know which pages own accepted official
objects. When a page has accepted official practice objects, its public
`practice_url` should point to `_raya/practice/index.html?page=<page-id>`
instead of the generic workspace root. The Practice workspace reads that URL
parameter on load, filters visible official objects to the matching owning page,
sets a transient active object when one is visible, and updates its public
context panel from the same embedded payload it already uses.

The focus is URL state only. Clear and Escape reset the Practice workspace to
the normal all-object view. The focus does not write `localStorage` or
`sessionStorage`, does not fetch data, does not infer related practice, and does
not expose private source paths or answer-only support.

## Scope

Current scope:

- Search result `Open practice` links include `?page=<page-id>` when a page has
  accepted official objects.
- Graph selected-page `Open practice` links include the same page query when
  the selected page has accepted official objects.
- Practice reads `?page=<page-id>` on load and shows only objects owned by that
  page.
- Clear and Escape remove the page focus by returning the UI to the all-object
  view. They do not need to rewrite browser history in this loop.

Out of scope:

- related-practice inference;
- task-specific page focus;
- object-level focus;
- full-text search;
- calendar/schedule surfaces;
- browser storage beyond existing reader comfort controls.

## Verification

Tests should prove the generated Search/Graph payload and HTML use page-focused
Practice URLs, and that the browser Practice workspace opens filtered by page,
resets with Clear/Escape, keeps keyboard active-object behavior, and leaves
browser storage empty.
