# Graph Study Objects Design

## Context

The static graph workspace already lets readers select a page, inspect explicit incoming/outgoing links, and jump to search, practice, tasks, and schedule surfaces. The next learning improvement is to connect the selected page to its authored study objects without turning those objects into graph nodes.

This keeps the graph useful for learning decisions: a reader can ask "what can I do on this page?" while still understanding the page's structural context.

## Decision

Add a compact `Study objects` section to the selected-page graph inspector.

The section is generated from accepted official objects already available to the static builder. It is embedded in the graph browser payload only, not written to `data/graph.json`, so the graph index schema remains page-node/link-edge v1.

## Behavior

- When no page is selected, the inspector keeps the existing empty state.
- When a selected page has official objects, the inspector shows a `Study objects` section.
- Each row shows only public object fields:
  - type label
  - title or preview text
  - optional due/available date for task-family objects
  - link to the rendered page anchor
- The section is hidden for pages without public study objects.
- Graph search may match public study-object titles and previews so students can find the owning page from task language.

## Constraints

- No schema change to `data/graph.json`.
- No object-level graph nodes yet.
- No runtime `fetch`, XHR, CDN, worker, or external graph library.
- No `localStorage` or `sessionStorage` for graph state.
- No recommendations, mastery, progress, completion, ranking, or grading language.
- Do not expose private support data:
  - `_official`
  - source paths
  - answers
  - solutions
  - correctness keys
  - back sides of cards

## Files

- `packages/static/src/raya_static/builder.py`
  - Build a public study-object summary for each graph payload node.
  - Add a graph-inspector placeholder element.
- `packages/static/src/raya_static/graph.py`
  - Render selected-node study objects into the inspector.
  - Include public study-object text in local graph search.
- `packages/static/src/raya_static/rendering.py`
  - Style the compact section and rows.
- `tests/contracts/test_static_builder.py`
  - Assert graph payload shape, public fields, anchor URLs, and private leak guards.
- `tests/e2e/test_preview_static_read_path.py`
  - Assert rendered graph inspector behavior in Chromium and no external/runtime storage regressions.

## Verification

- Focused contract graph test.
- Focused graph e2e test.
- Render-debug parity gate.
- Host archive gate before commit.
