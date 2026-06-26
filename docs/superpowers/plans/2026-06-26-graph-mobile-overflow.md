# Graph Mobile Overflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent mobile graph toolbar internal scrolling from widening the whole document.

**Architecture:** Keep the fix in the existing static renderer CSS. Cover the behavior in the existing browser e2e test that already exercises the mobile graph toolbar.

**Tech Stack:** Python static builder, generated CSS in `packages/static/src/raya_static/rendering.py`, Playwright e2e tests through `uv run pytest`.

---

### Task 1: Mobile Graph Toolbar Overflow Regression

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Write the failing test**

Add `_assert_no_horizontal_overflow(page)` to `test_preview_graph_mobile_toolbar_uses_compact_command_strip` after the graph page has loaded and the selected graph node is rendered. Keep the existing toolbar scroll assertions so the test proves both requirements: no document overflow and preserved internal toolbar overflow.

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_graph_mobile_toolbar_uses_compact_command_strip
```

Expected before the fix: FAIL from `_assert_no_horizontal_overflow(page)` because the document is wider than the `390px` viewport.

- [x] **Step 3: Implement minimal CSS fix**

In the existing `@media (max-width: 520px)` graph toolbar rules, constrain the graph page and toolbar to avoid intrinsic-width expansion. The toolbar should use `max-width: 100%` and `min-width: 0`; the graph page and graph toolbar containers should also have `min-width: 0` where needed.

- [x] **Step 4: Run focused test to verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_graph_mobile_toolbar_uses_compact_command_strip
```

Expected after the fix: PASS.

- [x] **Step 5: Run adjacent graph checks**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_preview_graph_mobile_toolbar_uses_compact_command_strip \
  tests/e2e/test_preview_static_read_path.py::test_preview_graph_mobile_workspace_prioritizes_map_panel \
  tests/e2e/test_preview_static_read_path.py::test_preview_graph_deeplink_keeps_orientation_controls_in_initial_viewport \
  tests/e2e/test_preview_static_read_path.py::test_preview_graph_toolbar_remains_compact_above_label_breakpoint
```

Expected: all four tests pass.

- [x] **Step 6: Rebuild fixture and run render debug**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture && ./scripts/check-render-debug.sh
```

Expected: build passes and `check-render-debug` passes.
