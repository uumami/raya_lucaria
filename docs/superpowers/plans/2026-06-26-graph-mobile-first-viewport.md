# Graph Mobile First Viewport Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce mobile pre-canvas graph chrome so the SVG graph appears earlier in the first viewport.

**Architecture:** Implement this as mobile-only CSS in the existing static renderer stylesheet. Cover it with a browser e2e regression against the render fixture graph page.

**Tech Stack:** Python static renderer CSS in `packages/static/src/raya_static/rendering.py`, Playwright e2e tests in `tests/e2e/test_preview_static_read_path.py`.

---

### Task 1: Mobile Graph First Viewport

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Write the failing test**

Add a mobile browser test that opens `_raya/graph/index.html?page=reader-ux` at `390x844`, waits for the selected node, and asserts:

```python
assert probe["canvas"]["top"] <= 620
assert probe["readingKeys"]["height"] <= 48
assert probe["instructions"]["height"] <= 40
assert probe["orientation"]["height"] <= 100
assert probe["toolbarScrollWidth"] > probe["toolbarClientWidth"]
assert probe["overflow"] <= 1
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_graph_mobile_keeps_canvas_in_first_viewport
```

Expected before the CSS fix: FAIL because the canvas top is about `760px`, reading keys are about `102px`, instructions are about `78px`, and orientation is about `214px`.

- [x] **Step 3: Implement mobile-only CSS**

In `packages/static/src/raya_static/rendering.py`, inside the existing `@media (max-width: 520px)` block:

- Make `.raya-graph-reading-keys` a one-row horizontal strip with `overflow-x: auto`.
- Make each reading-key article `flex: 0 0 ...` and keep its text compact.
- Line-clamp `.raya-graph-instructions` to two lines.
- Make `.raya-graph-orientation-meta` and `.raya-graph-orientation-actions` horizontally scrollable compact strips.
- Keep document overflow controlled.

- [x] **Step 4: Run focused test to verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_graph_mobile_keeps_canvas_in_first_viewport
```

Expected: PASS.

- [x] **Step 5: Run adjacent graph checks**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_preview_graph_mobile_keeps_canvas_in_first_viewport \
  tests/e2e/test_preview_static_read_path.py::test_preview_graph_mobile_toolbar_uses_compact_command_strip \
  tests/e2e/test_preview_static_read_path.py::test_preview_graph_mobile_workspace_prioritizes_map_panel \
  tests/e2e/test_preview_static_read_path.py::test_preview_graph_deeplink_keeps_orientation_controls_in_initial_viewport
```

Expected: all four tests pass.

- [x] **Step 6: Rebuild fixture and run render debug**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture && ./scripts/check-render-debug.sh
```

Expected: build passes and `check-render-debug` passes.
