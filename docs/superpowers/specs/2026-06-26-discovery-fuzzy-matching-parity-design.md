---
id: superpowers-discovery-fuzzy-matching-parity-design
title: Discovery Fuzzy Matching Parity Design
status: accepted
---
# Discovery Fuzzy Matching Parity Design

## Context

The current Search workspace and Graph workspace already support approximate
matching for mistyped queries such as `matrx`. Practice, Tasks, and Schedule
still use exact normalized substring matching. That makes the discovery
workspaces feel inconsistent and less forgiving when a student is scanning
official objects or dated work from memory.

This slice continues the legacy UX convergence goal by adapting the useful
fuzzy-search affordance into current static workspaces without copying legacy
runtime architecture.

## Goal

Practice, Tasks, and Schedule should tolerate small spelling mistakes in their
local text filters while preserving existing exact filtering, URL-only page
focus, type filters, sort behavior, keyboard selection, context panels, and
static-only constraints.

## Design

Add local `levenshtein(a, b)` and `fuzzyMatch(queryText, targetText)` helpers to
the Python-generated Practice, Tasks, and Schedule script resources, matching
the conservative Search workspace pattern. The existing normalized searchable
text maps remain the primary data source, with the existing visible text
fallback preserved. `matchesSearch(...)` changes from exact
`haystack.includes(query)` to `fuzzyMatch(query, haystack)`.

The behavior remains intentionally local and non-authoritative:

- no schema change;
- no generated payload change;
- no fetch, XHR, storage, external search index, or Pagefind dependency;
- no ranking, recommendation, mastery, progress, personalization, or scoring;
- no fuzzy page-focus semantics. `?page=<page-id>` remains exact URL context.

## Expected Behavior

- Practice query `retrievel` should still find the accepted official prompt
  whose public text contains `retrieval`.
- Tasks query `retrievel` should still find the accepted task-family objects
  whose public title, summary, or tags include `retrieval`.
- Schedule query `retrievel` should still find dated task-family objects whose
  public fields include `retrieval`.
- Empty queries still show all items allowed by the current page/type/kind
  filters.
- Exact queries continue to work.

## Non-Goals

- No fuzzy matching for URL page IDs, stable IDs, graph relationship filters,
  or course map filters in this slice.
- No scoring or sorting by match quality.
- No shared JavaScript module extraction; the existing resource pattern stores
  each workspace script independently.
- No browser-side dependency or remote search library.

## Verification

Use TDD with focused Playwright tests first. The RED tests should show that
mistyped Practice, Tasks, and Schedule queries currently produce too few visible
items. After implementation, run the focused browser tests, static builder
contract tests that assert the local script helpers exist, `./scripts/check-render-debug.sh`,
and the full `./scripts/check.sh` gate before commit and push.
