# Discovery Workspace Reset Parity Design

## Context

Search, Practice, Tasks, and Schedule already use the current reset framework: static pages, local JSON script payloads, volatile accessibility controls, and no external renderer requests. Graph has the most mature workspace behavior: reset is a whole-workspace action, keyboard recovery works from the workspace, and panel summaries stay useful when rails are collapsed.

Legacy `main` is useful as a UX reference for keyboard recovery, compact controls, graph-oriented focus, and reset affordances. Its Pagefind, persistent sidebar state, legacy theme stack, and client-side framework assumptions are not carried forward.

## Design

The next convergence slice is workspace-level reset and keyboard parity for `_raya/search`, `_raya/practice`, `_raya/tasks`, and `_raya/schedule`.

Each workspace keeps its existing controls and result cards, but `Escape` becomes equivalent to the visible `Clear` action when focus is anywhere inside the workspace, not only inside the query input. A reset clears query text, authored `?page=` focus, active result/object selection, filter chips, date-kind filters, and sort state where applicable. After reset, focus returns to the query input so keyboard users have a predictable recovery point.

Arrow and Enter navigation remain query-input behavior for now. This keeps the change small and avoids conflicting with native button, link, select, and card focus behavior.

## Requirements

- `Escape` inside Search resets query, page focus, active result, and hidden empty state, then focuses `#raya-search-input`.
- `Escape` inside Practice resets query, page focus, active object, and type filter, then focuses `#raya-practice-search`.
- `Escape` inside Tasks resets query, page focus, active task, type filter, and sort value to `course`, then focuses `#raya-tasks-search`.
- `Escape` inside Schedule resets query, page focus, active item, date-kind filter, and type filter, then focuses `#raya-schedule-search`.
- Reset must work from non-input workspace focus, including result cards and context actions.
- Reset must not write `localStorage`, `sessionStorage`, cookies, or URL state.
- Reset must not add `fetch`, `XMLHttpRequest`, CDN requests, Pagefind, or browser-side renderer dependencies.
- Existing collapsed panel behavior and rail summaries continue to work.

## Testing

Add browser tests against the static preview path because this behavior depends on real focus, keyboard events, and rendered HTML. The tests should prove `Escape` from a non-input element resets each workspace and that Tasks resets sort to `course`.

Focused commands:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_course_search_surface -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_official_practice_workspace -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_tasks_and_schedule_workspaces -q
```

Before completion, run the render-debug gate and the canonical host/Docker gates when the implementation is stable.

