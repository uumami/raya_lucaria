# Graph Mobile Toolbar Compaction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the mobile graph toolbar compact by using a horizontal command strip instead of vertical wrapping.

**Architecture:** The graph HTML and JavaScript remain unchanged. The renderer CSS adds a `max-width: 520px` rule that keeps `.raya-graph-toolbar` and its control groups on one horizontal axis with overflow, matching the existing mobile command-bar pattern.

**Tech Stack:** Python static renderer, generated CSS in `packages/static/src/raya_static/rendering.py`, Playwright e2e tests.

---

### Task 1: Add Mobile Toolbar Regression

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write the failing test**

Add `test_preview_graph_mobile_toolbar_uses_compact_command_strip` near the graph layout tests. It should open `_raya/graph/index.html?page=reader-ux` at `390x844`, then evaluate `.raya-graph-toolbar`, `.raya-graph-toolbar-group`, `#graph-search`, `#graph-layout`, `[data-raya-graph-edge-kind-filter="content"]`, `#graph-fit-selection`, and `[data-raya-graph-pan="right"]`.

Assert:

- toolbar height is at most `120`;
- toolbar `scrollWidth` is greater than `clientWidth`;
- all toolbar groups are present;
- the second group top is close to the first group top, proving horizontal layout;
- search and layout controls are visible;
- secondary controls exist and can be reached by horizontal scroll;
- map top remains before list top;
- storage keys are empty.

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_graph_mobile_toolbar_uses_compact_command_strip
```

Expected: FAIL before implementation because the toolbar height is much larger than `120` and groups wrap vertically.

### Task 2: Add Mobile Toolbar CSS

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Implement minimal CSS**

Inside the existing `@media (max-width: 520px)` block, add graph toolbar rules:

```css
.raya-graph-toolbar {
  align-items: center;
  flex-wrap: nowrap;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-gutter: stable;
}
.raya-graph-toolbar-group,
.raya-graph-pan-controls,
.raya-graph-shortcut-hints {
  flex: 0 0 auto;
  flex-wrap: nowrap;
}
.raya-graph-toolbar-primary {
  min-width: 20rem;
}
.raya-graph-toolbar-primary input {
  min-width: 9rem;
}
.raya-graph-controls button,
.raya-graph-controls select,
.raya-graph-controls input {
  white-space: nowrap;
}
.raya-graph-active-state {
  max-width: 12rem;
  white-space: nowrap;
}
.raya-graph-toolbar :is(input, select, button):focus-visible {
  outline-offset: -2px;
}
```

- [ ] **Step 2: Run focused regression**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_graph_mobile_toolbar_uses_compact_command_strip
```

Expected: PASS.

- [ ] **Step 3: Run adjacent responsive graph tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_graph_mobile_workspace_prioritizes_map_panel tests/e2e/test_preview_static_read_path.py::test_preview_graph_deeplink_keeps_orientation_controls_in_initial_viewport tests/e2e/test_preview_static_read_path.py::test_preview_graph_toolbar_remains_compact_above_label_breakpoint
```

Expected: PASS.

### Task 3: Verify, Review, Rebuild, Commit, Push

**Files:**
- Inspect: `docs/superpowers/specs/2026-06-26-graph-mobile-toolbar-compaction-design.md`
- Inspect: `docs/superpowers/plans/2026-06-26-graph-mobile-toolbar-compaction.md`
- Inspect: `tests/e2e/test_preview_static_read_path.py`
- Inspect: `packages/static/src/raya_static/rendering.py`

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

Expected: exits 0.

- [ ] **Step 3: Request independent review**

Ask a review agent to inspect the responsive CSS, test coverage, and current-framework constraints.

- [ ] **Step 4: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-graph-mobile-toolbar-compaction-design.md docs/superpowers/plans/2026-06-26-graph-mobile-toolbar-compaction.md tests/e2e/test_preview_static_read_path.py packages/static/src/raya_static/rendering.py
git commit -m "Compact mobile graph toolbar"
git push origin new_rayalucaria
```
