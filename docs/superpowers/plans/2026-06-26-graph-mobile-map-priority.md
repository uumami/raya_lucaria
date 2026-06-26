# Graph Mobile Map Priority Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the graph map the first graph workspace panel on tablet and mobile while preserving the desktop three-column layout.

**Architecture:** The generated graph HTML remains in its current source order for desktop layout and accessibility. The responsive CSS at the existing `max-width: 1279px` breakpoint assigns explicit grid order values so the map panel appears before page and inspector panels when the workspace becomes single-column.

**Tech Stack:** Python static renderer, CSS generated from `packages/static/src/raya_static/rendering.py`, Playwright e2e tests.

---

### Task 1: Add Responsive Panel Order Regression

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write the failing test**

Add `test_preview_graph_mobile_workspace_prioritizes_map_panel` near existing graph layout tests. The test should preview the render fixture, open `_raya/graph/index.html?page=reader-ux`, and inspect `.raya-graph-list-panel`, `.raya-graph-map-panel`, and `.raya-graph-inspector-panel` at `1440x900`, `1024x768`, and `390x844`.

Assertions:

- desktop: list top is before map top;
- tablet/mobile: map top is before list and inspector top;
- tablet/mobile: map top is less than viewport height;
- selected state is `reader-ux`;
- storage keys are empty.

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_graph_mobile_workspace_prioritizes_map_panel
```

Expected: FAIL before implementation because tablet/mobile source order places the pages panel before the map panel.

### Task 2: Reorder Graph Panels At The Single-Column Breakpoint

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Implement minimal CSS**

Inside the existing `@media (max-width: 1279px)` graph block, add:

```css
.raya-graph-map-panel {
  order: 1;
}
.raya-graph-list-panel {
  order: 2;
}
.raya-graph-inspector-panel {
  order: 3;
}
```

- [ ] **Step 2: Run focused regression**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_graph_mobile_workspace_prioritizes_map_panel
```

Expected: PASS.

- [ ] **Step 3: Run adjacent graph layout tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_graph_deeplink_keeps_orientation_controls_in_initial_viewport tests/e2e/test_preview_static_read_path.py::test_preview_graph_workspace_starts_in_first_desktop_viewport tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_collapsed_rails_prioritize_canvas_space
```

Expected: PASS.

### Task 3: Verify, Review, Rebuild, Commit, Push

**Files:**
- Inspect: `docs/superpowers/specs/2026-06-26-graph-mobile-map-priority-design.md`
- Inspect: `docs/superpowers/plans/2026-06-26-graph-mobile-map-priority.md`
- Inspect: `tests/e2e/test_preview_static_read_path.py`
- Inspect: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Rebuild render fixture**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture
```

Expected: build succeeds and refreshes `examples/courses/render-fixture/artifact/site`.

- [ ] **Step 2: Run render debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: exits 0.

- [ ] **Step 3: Request independent review**

Ask one review agent to inspect the diff for responsive ordering regressions, current-framework alignment, and test coverage.

- [ ] **Step 4: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-graph-mobile-map-priority-design.md docs/superpowers/plans/2026-06-26-graph-mobile-map-priority.md tests/e2e/test_preview_static_read_path.py packages/static/src/raya_static/rendering.py
git commit -m "Prioritize graph map on mobile"
git push origin new_rayalucaria
```
