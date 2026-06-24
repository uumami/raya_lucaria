# Page-Scoped Tasks and Schedule Handoff Design

## Context

The Graph detail card already links selected pages to `_raya/tasks/index.html?page=<page-id>` and `_raya/schedule/index.html?page=<page-id>`. The Practice workspace already honors the same URL-only `?page=` handoff, but Tasks and Schedule currently ignore it. This leaves a visible graph affordance that does not narrow the destination workspace.

## Design

Tasks and Schedule will read `page` from `window.location.search` during local script startup. When the value matches the `page_id` of embedded public payload items, the workspace initially filters visible cards to that page. The filter is transient URL context only: it is not written to local storage, session storage, cookies, or the artifact payload.

Clear and Escape will reset the workspace to all task or schedule items. They will also clear search text and reset type/kind filters to `all`, matching the existing reset behavior. If the URL page value is absent or matches no embedded public item, the workspace will behave exactly as the all-items view.

The visible cards, status text, summary count, and context panel will all follow the filtered set. Tasks will filter accepted task-family objects by `page_id`; Schedule will filter dated task-family items by `page_id`. Existing text/type/kind filters and sorting remain local and compose with the page filter until Clear or Escape removes the page scope.

## Boundaries

This feature stays inside the static renderer. It must not fetch data at runtime, load external resources, persist state, infer recommendations, compute progress, calculate personal due state, or expose source/private paths. It uses only already embedded public task and schedule payload data.

## Files

- `packages/static/src/raya_static/tasks.py`: read URL page context and include it in match logic/reset behavior.
- `packages/static/src/raya_static/schedule.py`: same for dated schedule items.
- `tests/e2e/test_preview_static_read_path.py`: browser coverage for Graph-to-Tasks and Graph-to-Schedule handoffs, Clear/Escape reset, no storage, and local request parity.
- `docs/foundation/20_learning_renderer_contract.md`: contract wording for URL-only `?page=` filtering in Tasks/Schedule verification.
- `docs/guides/en/agents/index.md` and `docs/guides/es/agentes/index.md`: agent guidance for verifying the handoff without treating it as learner state.

## Verification

Focused verification should build/preview a fixture with task-family objects on at least two pages and use Playwright to open `_raya/tasks/index.html?page=first-topic` and `_raya/schedule/index.html?page=first-topic`. The tests should prove only the selected page's task-family objects are initially visible, Clear/Escape restores all items, no browser storage is written, and all requests stay local.

Full verification remains the repository gate sequence: focused e2e test, `./scripts/check-render-debug.sh`, `./scripts/check.sh`, and `./scripts/check-docker.sh`.
