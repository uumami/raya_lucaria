# Discovery Page Focus Notice Design

## Context

Legacy `main` made navigation state visible through sidebars, graph status text,
and obvious controls. The reset renderer already supports URL-scoped discovery
handoffs: Search, Practice, Tasks, and Schedule accept `?page=<page-id>`, filter
to that public page, and Clear/Escape restores the full workspace. The missing
UX piece is visibility. A student who arrives from Graph or a page-focused link
can see fewer results, but the workspace does not consistently name why.

This slice makes URL-scoped discovery handoffs visible and reversible without
changing the source contract, artifact schema, graph data, or filtering model.

## Options Considered

### Option A: Put page focus only in the context side panel

This keeps markup small, but the focus can be missed on mobile or when the
context panel is visually below the results.

### Option B: Add a compact notice in each control panel

This places the focus explanation beside Search/Clear and existing filter
controls. It remains visible before the reader scans results, works on mobile,
and reuses the existing Clear behavior.

### Option C: Add URL state to all workspaces

This would make the state shareable beyond the initial `?page=` handoff, but it
would broaden the contract and increase drift from the current simple reset
rules.

## Chosen Design

Use Option B. Each discovery workspace gets a compact page-focus notice in the
control panel:

- Search: `data-raya-search-page-focus`
- Practice: `data-raya-practice-page-focus`
- Tasks: `data-raya-tasks-page-focus`
- Schedule: `data-raya-schedule-page-focus`

The notice is hidden when no valid `activePage` exists. When `?page=<page-id>`
is active, the workspace script fills the notice from embedded public payload
data and the current visible count. The copy is structural, for example:

`Focused on page First Topic. 3 visible practice objects. Use Clear to show all.`

If the URL page does not resolve to public payload data, the notice stays hidden
and the existing empty state/status handles the zero-result view. Clear and
Escape clear `activePage`, hide the notice, and restore the full workspace.

The notice does not add a separate button. The existing Clear button remains the
single reset control for query, type filters, sort/kind filters, and page focus.

## Constraints

- No new source syntax, schema, manifest data, or artifact data contract.
- No `fetch`, `XMLHttpRequest`, external assets, CDN resources, or browser
  storage.
- No shell-script dependency on discovery workspaces.
- No URL mutation when Clear/Escape resets page focus.
- No recommendation, progress, mastery, ranking, due-for-you, or personalized
  wording.
- Missing or invalid `?page=` values must fail calmly without exposing source
  paths, private support paths, stack traces, or learner-state language.
- The notice must be compact enough for mobile and must not introduce horizontal
  overflow.

## Implementation Surface

- `packages/static/src/raya_static/builder.py` adds hidden notice placeholders
  to the four discovery control panels.
- `packages/static/src/raya_static/search.py`, `practice.py`, `tasks.py`, and
  `schedule.py` update notice text during render.
- `packages/static/src/raya_static/rendering.py` styles the notice with existing
  discovery/control tokens.
- `tests/e2e/test_preview_static_read_path.py` adds browser assertions for
  visible focus notices, Clear/Escape hiding them, missing-page behavior, no
  storage, no external requests, and no mobile overflow.
- `docs/foundation/20_learning_renderer_contract.md` and English/Spanish role
  docs describe page-focus notices as URL-only static workspace context.

## Acceptance Criteria

- Opening Search with `?page=<page-id>` shows a compact focus notice with the
  public page title and current visible count.
- Opening Practice, Tasks, and Schedule with `?page=<page-id>` shows equivalent
  notices using each workspace's count language.
- Clear and Escape hide the notice and restore the full list.
- Invalid `?page=` values do not show a misleading focus notice.
- Local/session storage remain unused by these workspace focus states.
- Static read paths use only local resources and existing embedded payloads.
- Desktop and mobile browser checks show no horizontal overflow.
