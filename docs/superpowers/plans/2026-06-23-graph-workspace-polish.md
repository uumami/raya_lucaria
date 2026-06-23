# Graph Workspace Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the static graph page into a desktop-first workspace with collapsible panels while preserving local-only static rendering and current graph contracts.

**Architecture:** Keep the current Python-generated HTML and local SVG JavaScript. Add semantic workspace containers in `builder.py`, CSS grid/panel states in `rendering.py`, and small non-persistent toggle handling in `graph.py`. No new runtime dependencies.

**Tech Stack:** Python static builder, embedded CSS, local vanilla JavaScript, Playwright e2e tests, pytest contract tests.

---

## File Structure

- `packages/static/src/raya_static/builder.py`: render graph workspace shell, panel toggles, and structural labels.
- `packages/static/src/raya_static/rendering.py`: desktop graph grid, panel collapse states, expanded workspace styles, mobile fallback.
- `packages/static/src/raya_static/graph.py`: non-persistent panel toggle behavior and accessibility state handling.
- `tests/e2e/test_preview_static_read_path.py`: browser tests for workspace layout, collapse behavior, focus safety, and expanded canvas.
- `tests/contracts/test_static_builder.py`: structural graph HTML/JS/CSS assertions.

## Task 1: Red Tests For Workspace Structure And Panel Behavior

- [x] Add e2e expectations in `test_preview_serves_local_visual_graph_surface` after graph page load:
  - `.raya-graph-workspace` is visible.
  - `.raya-graph-map-panel`, `.raya-graph-list-panel`, and `.raya-graph-inspector-panel` are visible on desktop.
  - At `1280px`, graph canvas width is larger than inspector width and list width.
  - Clicking list and inspector toggle buttons sets panel state to `collapsed`.
  - Collapsed panels hide focusable contents from keyboard navigation with `aria-hidden="true"` and disabled tab access.
  - Re-clicking restores panel state.
  - Expanded mode sets a workspace expanded state, collapses the list panel through the same accessible state path, and increases graph workspace width on desktop.
  - The graph workspace remains overflow-free at a near-breakpoint `1120px` viewport.
  - Search status distinguishes direct matches from connected context pages.

- [x] Add contract assertions in `test_browser_graph_surface_includes_static_workspace_controls` or the existing graph contract test:
  - HTML includes `raya-graph-workspace`, `data-raya-graph-list-panel`, `data-raya-graph-inspector-panel`.
  - HTML includes buttons with `data-raya-graph-toggle-panel`.
  - Graph JS includes `setGraphPanelState` and does not include storage/fetch tokens.

- [x] Run focused tests and verify they fail for missing workspace/panel behavior:
  - `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q`
  - `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -q -k graph`

## Task 2: Implement Graph Workspace Markup

- [x] In `packages/static/src/raya_static/builder.py`, wrap current graph content in:
  - `.raya-graph-workspace`
  - `.raya-graph-list-panel`
  - `.raya-graph-map-panel`
  - `.raya-graph-inspector-panel`

- [x] Move group filters and page list into list panel.

- [x] Move hover status, selected-page detail, legend, and help into inspector panel.

- [x] Add explicit buttons:
  - `data-raya-graph-toggle-panel="list"` controlling `raya-graph-list-panel`
  - `data-raya-graph-toggle-panel="inspector"` controlling `raya-graph-inspector-panel`

- [x] Keep search/layout/zoom/reset/expand controls above the workspace.

## Task 3: Implement Styling And Non-Persistent Panel State

- [x] In `packages/static/src/raya_static/rendering.py`, add desktop grid:
  - list panel: `minmax(16rem, 22rem)`
  - map panel: `minmax(34rem, 1fr)`
  - inspector panel: `minmax(18rem, 24rem)`

- [x] Add collapsed states:
  - `[data-raya-graph-list-state="collapsed"]`
  - `[data-raya-graph-inspector-state="collapsed"]`
  - collapsed panels become compact rails, not full cards.

- [x] In `packages/static/src/raya_static/graph.py`, add `setGraphPanelState(panelName, expanded)`:
  - update root data attributes;
  - update panel `aria-hidden`;
  - set panel focusable descendants to `tabIndex=-1` while collapsed and restore previous/default tab behavior when expanded;
  - update toggle button `aria-expanded` and label text.

- [x] Keep state non-persistent. Do not use storage.

## Task 4: Verify Focused Behavior

- [x] Run focused graph e2e test:
  - `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q`

- [x] Run graph/static contract subset:
  - `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -q -k graph`

- [x] Run render debug:
  - `./scripts/check-render-debug.sh`

## Task 5: Review And Full Verification

- [x] Request code review from independent agents after implementation.

- [x] Address concrete findings using `superpowers:receiving-code-review`.

- [x] Run canonical host gate:
  - `./scripts/check.sh`

- [x] Run Docker gate sequentially after host gate:
  - `./scripts/check-docker.sh`

- [x] Start preview and report local URL:
  - `UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --host 127.0.0.1 --port 0`

- [x] Commit and push to `origin/new_rayalucaria` after verification.
