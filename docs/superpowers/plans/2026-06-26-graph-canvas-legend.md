# Graph Canvas Legend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a compact, canvas-adjacent graph group legend that remains visible when the graph Pages panel is collapsed.

**Architecture:** Reuse current generated graph group buttons and the existing local graph script state model. Add a second group-control surface inside the graph map panel, styled as a compact legend strip and verified through contract and browser tests.

**Tech Stack:** Python static builder, generated HTML/CSS, local graph JavaScript already emitted by Glintstone, pytest, Playwright.

---

### Task 1: Contract Test For Canvas Legend

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write the failing test**

Add a test that builds `examples/courses/render-fixture`, reads
`artifact/site/_raya/graph/index.html`, and asserts:

```python
legend = _section_html(html, "raya-graph-canvas-legend")
assert 'aria-label="Graph group legend"' in legend
assert legend.count('data-raya-graph-group-filter=') >= 2
assert "raya-graph-group-swatch" in legend
assert "https://cdn" not in html
assert "cytoscape" not in html.lower()
assert "localStorage" not in legend
assert "sessionStorage" not in legend
assert "fetch(" not in legend
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_graph_surface_exposes_canvas_group_legend
```

Expected: FAIL because `.raya-graph-canvas-legend` is not generated yet.

### Task 2: Browser Test For Collapsed Pages Panel

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write the failing browser test**

Add a Playwright test that opens `_raya/graph/index.html` at `1440x950`,
collapses the Pages panel, and evaluates:

```javascript
const legend = document.querySelector('.raya-graph-canvas-legend');
const firstButton = legend?.querySelector('[data-raya-graph-group-filter]');
const canvas = document.querySelector('.raya-graph-canvas');
const box = (node) => {
  const rect = node?.getBoundingClientRect();
  return rect ? { top: rect.top, bottom: rect.bottom, width: rect.width, height: rect.height } : null;
};
return {
  legend: box(legend),
  firstButton: box(firstButton),
  canvas: box(canvas),
  pressedBefore: firstButton?.getAttribute('aria-pressed'),
};
```

Then click the first legend button and assert the `aria-pressed` value changes
to `"false"`. Also assert no horizontal overflow and all requested URLs start
with the preview base URL.

- [ ] **Step 2: Run the browser test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_graph_canvas_legend_remains_visible_when_pages_panel_collapses
```

Expected: FAIL because the legend is missing.

### Task 3: Generate And Style The Legend

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Extract group button helper**

In `builder.py`, replace inline group button construction with a helper that
accepts a CSS class prefix or extra class and returns the existing button HTML
with `data-raya-graph-group-filter`.

- [ ] **Step 2: Render map-panel legend**

Inside `_render_graph_surface`, insert this structure inside
`.raya-graph-map-panel` after `.raya-graph-orientation` and before the SVG:

```html
<section class="raya-graph-canvas-legend" aria-label="Graph group legend">
  <h2>Groups</h2>
  <div class="raya-graph-canvas-legend-items">
    ...same group filter buttons...
  </div>
</section>
```

- [ ] **Step 3: Add compact CSS**

In `rendering.py`, style `.raya-graph-canvas-legend` and
`.raya-graph-canvas-legend-items` so it is compact, wraps, uses existing
surface/border tokens, and does not stretch the canvas below the first viewport.

- [ ] **Step 4: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_graph_surface_exposes_canvas_group_legend tests/e2e/test_preview_static_read_path.py::test_graph_canvas_legend_remains_visible_when_pages_panel_collapses
```

Expected: PASS.

### Task 4: Verification, Review, Commit

**Files:**
- Verify all files changed in this slice.

- [ ] **Step 1: Run graph/debug verification**

Run:

```bash
./scripts/check-render-debug.sh
git diff --check
```

Expected: both exit 0.

- [ ] **Step 2: Request independent code review**

Ask a read-only reviewer to inspect the diff for static-only graph contract
compliance, no duplicate state model, no external renderer dependency, and
meaningful tests.

- [ ] **Step 3: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-graph-canvas-legend-design.md docs/superpowers/plans/2026-06-26-graph-canvas-legend.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add graph canvas group legend"
git push origin new_rayalucaria
```
