# Graph First Viewport Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make page-focused graph deeplinks first-paint with visible selected graph content in the browser viewport.

**Architecture:** Keep the current static SVG graph and public embedded payload. Add browser tests that fail on the current low first-paint graph position, then tighten CSS layout so the graph map panel becomes a viewport-bounded work surface and the SVG receives the usable height.

**Tech Stack:** Python static builder tests, Playwright e2e tests, static CSS in `packages/static/src/raya_static/rendering.py`.

---

### Task 1: Failing First-Viewport Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add a strict deeplink first-viewport assertion**

In `test_preview_graph_deeplink_keeps_orientation_controls_in_initial_viewport`, extend the existing browser probe to return viewport intersections for the selected SVG node, selected canvas, active edge, and canvas dimensions:

```python
selectedIntersectsViewport: intersectsViewport(
  box('#raya-graph-canvas [data-raya-graph-node="reader-ux"] g')
),
canvasIntersectsViewport: intersectsViewport(box('#raya-graph-canvas')),
activeEdgeIntersectsViewport: Array.from(
  document.querySelectorAll('#raya-graph-canvas .raya-graph-edge.is-active')
).some((edge) => intersectsViewport(edge.getBoundingClientRect())),
canvas: box('#raya-graph-canvas'),
```

Then assert:

```python
assert probe["canvasIntersectsViewport"], (viewport, probe)
assert probe["selectedIntersectsViewport"], (viewport, probe)
assert probe["activeEdgeIntersectsViewport"], (viewport, probe)
if viewport["width"] >= 1280:
    assert probe["canvas"]["height"] >= viewport["height"] * 0.48, (viewport, probe)
else:
    assert probe["canvas"]["height"] >= min(360, viewport["height"] * 0.42), (
        viewport,
        probe,
    )
assert probe["canvas"]["height"] <= viewport["height"] * 0.78, (viewport, probe)
```

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_preview_graph_deeplink_keeps_orientation_controls_in_initial_viewport
```

Expected: fail because selected graph content is below the first viewport on at least desktop and tablet.

### Task 2: Viewport-Bounded Graph CSS

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Tighten graph page spacing**

Update the graph page and workspace CSS so the graph surface starts sooner:

```css
.raya-graph-page {
  padding-top: 0.35rem;
}
.raya-graph-controls.raya-graph-toolbar,
.raya-graph-instructions {
  margin-bottom: 0.35rem;
}
.raya-graph-workspace {
  gap: 0.75rem;
  margin-top: 0.35rem;
}
```

- [x] **Step 2: Prioritize the canvas inside the map panel**

Keep `.raya-graph-map-panel` as a flex column and use flex ordering so first-paint shows the graph before secondary orientation, legend, and minimap controls:

```css
.raya-graph-map-panel {
  display: flex;
  flex-direction: column;
  position: relative;
}
.raya-graph-canvas {
  order: 4;
}
.raya-graph-orientation {
  order: 5;
}
.raya-graph-canvas-legend {
  order: 6;
}
```

- [x] **Step 3: Give the SVG a viewport-bounded useful height**

Update the canvas height rules:

```css
.raya-graph-canvas {
  flex: 0 0 auto;
  height: clamp(24rem, 50vh, 36rem);
}
```

- [x] **Step 4: Add responsive bounds**

Inside the existing `@media (max-width: 1279px)` block, keep the map panel unclipped and reduce above-canvas explanation:

```css
.raya-graph-map-panel {
  max-height: none;
  min-height: 0;
  overflow: visible;
}
.raya-graph-instructions {
  display: none;
}
.raya-graph-canvas {
  height: clamp(18rem, 43vh, 23rem);
}
```

- [x] **Step 5: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_preview_graph_deeplink_keeps_orientation_controls_in_initial_viewport
```

Expected: pass.

### Task 3: Focused Regression Gates

**Files:**
- Inspect only unless failures require fixes.

- [x] **Step 1: Run graph first-viewport and workspace tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_preview_graph_workspace_starts_in_first_desktop_viewport \
  tests/e2e/test_preview_static_read_path.py::test_preview_graph_deeplink_keeps_orientation_controls_in_initial_viewport \
  tests/e2e/test_preview_static_read_path.py::test_preview_graph_mobile_workspace_prioritizes_map_panel \
  tests/e2e/test_preview_static_read_path.py::test_preview_graph_mobile_toolbar_uses_compact_command_strip \
  tests/e2e/test_preview_static_read_path.py::test_graph_canvas_legend_remains_visible_when_pages_panel_collapses
```

Expected: pass with no horizontal overflow and preserved mobile toolbar behavior.

- [x] **Step 2: Run render-debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: pass with no raw TeX leakage, no external renderer requests, no overflow regression, and static-site parity intact.

### Task 4: Review, Commit, Push

**Files:**
- Inspect all changed files.

- [ ] **Step 1: Request independent review**

Ask a reviewer to inspect the CSS/test diff for first-viewport correctness, mobile overflow, graph state/storage constraints, and accidental weakening of existing graph tests.

- [ ] **Step 2: Fix confirmed issues with TDD**

For each confirmed issue, add or adjust a failing test first, verify RED, apply the smallest fix, and rerun the focused graph tests.

- [ ] **Step 3: Final local checks**

Run:

```bash
git diff --check
git status --short --branch
```

Expected: no whitespace errors and only intentional tracked changes.

- [ ] **Step 4: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-27-graph-first-viewport-design.md \
  docs/superpowers/plans/2026-06-27-graph-first-viewport.md \
  packages/static/src/raya_static/rendering.py \
  tests/e2e/test_preview_static_read_path.py
git commit -m "Keep graph deeplinks in first viewport"
git push origin new_rayalucaria
```
