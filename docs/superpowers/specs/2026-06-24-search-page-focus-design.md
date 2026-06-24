# Search Page Focus Design

## Context

The current generated discovery workspaces already share static chrome and local
handoffs. Practice, Tasks, and Schedule accept `?page=<page-id>` so a Graph
selected-page detail can open those workspaces scoped to the same page. Search is
the exception: Graph's "Find in search" link currently uses a title query such as
`?q=Authoring%20Matrix%20Fixture`, and Search only initializes from `q`.

That fuzzy title handoff can show similarly named pages and does not preserve the
same exact page context the rest of the discovery family uses.

## Goal

Make Search accept exact, URL-only page focus so Graph-to-Search and
page-to-Search handoffs can keep the same selected page thread without adding
runtime fetches, browser storage, personal state, or a new data contract.

## Selected Approach

Add exact `?page=<page-id>` support to the existing static Search workspace.

On Search startup:

- read `page` from `window.location.search`;
- if `page` is present, show only the result whose public page ID matches;
- keep `q` support unchanged, and compose it with page focus when both are
  present;
- set the focused page as the active search result when visible;
- update the existing context panel from the focused result;
- let Clear and Escape remove page focus, clear the query, and restore all
  visible results.

Graph selected-page detail links should use `../search/index.html?page=<page-id>`
instead of title-query search. Reader page shortcuts may keep title-query search
for broad lookup in this slice unless a current exact-page handoff already exists
near the graph/action context.

## Alternatives Considered

1. **Visible page-focus banner across all workspaces**: useful, but broader than
   needed. It should come after all workspaces support the same exact page-focus
   contract.
2. **Selection-aware graph viewport fitting**: valuable for graph orientation,
   but the graph already has selected first-paint visibility and viewport
   controls. Search page focus closes a clearer cross-workspace inconsistency.
3. **Full-text search snippets from old main**: high value, but it needs a new
   public text/snippet index and stricter privacy rules. That should be a later
   contract-sized slice.

## Static Boundary

This feature uses only embedded Search payload data and current static links. It
must not fetch data at runtime, load external resources, write `localStorage` or
`sessionStorage`, expose private source paths, infer recommendations, rank pages
by importance, or describe page focus as progress, mastery, completion, or a
personal next step.

`?page=` is shareable structural UI state, matching Graph, Practice, Tasks, and
Schedule handoffs.

## Documentation Impact

Update the learning renderer contract and agent role docs to state that Search
may accept URL-only exact page focus. Make clear that it is structural discovery
state and not learner state.

## Testing

Use TDD.

- Contract tests should assert Search payload/pages expose stable page IDs,
  Search script contains page-focus parsing/reset behavior, and Graph search
  links point to `../search/index.html?page=<page-id>`.
- Browser tests should open Search with `?page=authoring-matrix`, assert exactly
  that page is visible and active, verify context follows it, and prove Clear and
  Escape restore all visible results.
- Browser tests should open Graph for a selected page, assert the detail search
  link carries `?page=<page-id>`, follow it, and verify Search opens in exact
  page focus.
- Existing no-storage, no-fetch, no-external-request checks remain mandatory.

## Self-Review

- No placeholders remain.
- Scope is small enough for one implementation plan.
- The design reuses current discovery payloads and URL-state patterns.
- The design does not require a source schema, artifact data, or foundation
  authority expansion beyond exact Search URL focus.
