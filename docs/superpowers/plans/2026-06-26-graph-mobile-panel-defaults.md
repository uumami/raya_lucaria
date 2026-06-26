# Graph Mobile Panel Defaults Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Default graph list and inspector panels to compact collapsed summaries on stacked mobile/tablet layouts.

**Architecture:** Reuse existing graph panel state functions in `packages/static/src/raya_static/graph.py`. Add responsive default helpers and e2e coverage; avoid new markup and storage.

**Tech Stack:** Local generated graph JavaScript, Playwright e2e tests through `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest`.

---

### Task 1: Responsive Panel Defaults

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Write the failing test**

Add a browser test opening `_raya/graph/index.html?page=reader-ux` at `390x844` and desktop `1440x950`. Assert mobile starts collapsed, summaries are visible, panel bodies are hidden, panel body focusables are `tabindex="-1"`, toggles expand panels, and desktop starts expanded. Also assert `?list=1&inspector=1` expands mobile panels and reset returns to collapsed responsive default.

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_graph_mobile_defaults_to_compact_panels
```

Expected before implementation: FAIL because mobile starts `expanded` and panel bodies are visible.

- [x] **Step 3: Implement responsive defaults**

In `packages/static/src/raya_static/graph.py`:

- Add `graphPanelsDefaultExpanded()` based on `window.matchMedia("(max-width: 1279px)")`.
- Add `setGraphPanelsToResponsiveDefault()`.
- Initialize list/inspector with responsive defaults before URL state is applied.
- Extend URL parsing to accept `list=1` and `inspector=1`.
- Update URL state so `list=0`/`inspector=0` are emitted only when default is expanded and collapsed, while `list=1`/`inspector=1` are emitted when default is collapsed and expanded.
- Make reset restore responsive defaults.
- Make every focus-mode exit path restore responsive defaults.

- [x] **Step 4: Run focused test to verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_graph_mobile_defaults_to_compact_panels
```

Expected: PASS.

- [x] **Step 5: Run adjacent graph checks**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_preview_graph_mobile_defaults_to_compact_panels \
  tests/e2e/test_preview_static_read_path.py::test_preview_graph_mobile_keeps_canvas_in_first_viewport \
  tests/e2e/test_preview_static_read_path.py::test_preview_graph_mobile_toolbar_uses_compact_command_strip \
  tests/e2e/test_preview_static_read_path.py::test_preview_graph_deeplink_keeps_orientation_controls_in_initial_viewport
```

Expected: all four tests pass.

- [x] **Step 6: Rebuild fixture and run render debug**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture && ./scripts/check-render-debug.sh
```

Expected: build passes and `check-render-debug` passes.
