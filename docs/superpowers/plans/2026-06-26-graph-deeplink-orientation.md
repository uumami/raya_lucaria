# Graph Deeplink Orientation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep graph deep links oriented in the first viewport while preserving selected-page graph focus.

**Architecture:** The graph already separates URL state initialization, list active-result scrolling, selected-node graph fitting, and explicit detail focus. This change adds an e2e regression for initial deep-link orientation and changes only the initial page-focus fit so it updates the SVG viewBox without scrolling the document.

**Tech Stack:** Python static builder, generated vanilla JavaScript graph runtime, Playwright e2e tests.

---

### Task 1: Add Deep-Link First-Viewport Regression

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write the failing test**

Add `test_preview_graph_deeplink_keeps_orientation_controls_in_initial_viewport` near the existing graph viewport tests. The test should build the render fixture with `create_preview`, open `_raya/graph/index.html?page=reader-ux` at `1440x900`, `1024x768`, and `390x844`, then evaluate bounding boxes for `[data-raya-graph-orientation]`, `.raya-graph-toolbar`, and the selected `reader-ux` node. Assert selection exists, at least one orientation control intersects the viewport, and storage is empty.

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_graph_deeplink_keeps_orientation_controls_in_initial_viewport
```

Expected: FAIL before implementation because tablet/mobile deep links start scrolled past the orientation controls.

### Task 2: Suppress Initial Graph Deep-Link Document Scroll

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`

- [ ] **Step 1: Implement minimal runtime change**

Update `fitInitialPageFocus()` so it still calls `setGraphViewBox(box)` but does not call `canvas.scrollIntoView(...)` during initial URL restoration.

- [ ] **Step 2: Run focused regression**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_graph_deeplink_keeps_orientation_controls_in_initial_viewport
```

Expected: PASS.

- [ ] **Step 3: Run adjacent graph tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_url_state_and_debug_readout tests/e2e/test_preview_static_read_path.py::test_preview_graph_workspace_starts_in_first_desktop_viewport
```

Expected: PASS.

### Task 3: Verify, Review, Preview, Commit, Push

**Files:**
- Inspect: `docs/superpowers/specs/2026-06-26-graph-deeplink-orientation-design.md`
- Inspect: `docs/superpowers/plans/2026-06-26-graph-deeplink-orientation.md`
- Inspect: `tests/e2e/test_preview_static_read_path.py`
- Inspect: `packages/static/src/raya_static/graph.py`

- [ ] **Step 1: Rebuild render fixture**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture
```

Expected: build succeeds.

- [ ] **Step 2: Run render debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: exits 0 and writes local debug evidence only.

- [ ] **Step 3: Request code review**

Ask an independent review agent to inspect the diff for the graph deep-link behavior, test coverage, and unintended scrolling regressions.

- [ ] **Step 4: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-graph-deeplink-orientation-design.md docs/superpowers/plans/2026-06-26-graph-deeplink-orientation.md tests/e2e/test_preview_static_read_path.py packages/static/src/raya_static/graph.py
git commit -m "Keep graph deep links oriented"
git push origin new_rayalucaria
```
