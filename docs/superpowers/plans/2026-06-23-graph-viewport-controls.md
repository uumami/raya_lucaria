# Graph Viewport Controls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add static SVG viewport controls to the Course Graph page so readers can zoom and reset the graph view without external libraries or persisted state.

**Architecture:** Extend the existing graph controls markup in `builder.py`, then implement transient viewBox state in `graph.py`. The SVG renderer keeps deterministic node positions; viewport controls only change the canvas `viewBox` after rendering. Styling stays in `rendering.py`, with tests covering static contract, browser behavior, and list-layout disabled controls.

**Tech Stack:** Python 3.10 static builder, embedded local JavaScript, SVG `viewBox`, pytest, Playwright.

---

### Task 1: Add Failing Contract Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Assert graph viewport controls exist**

In `test_build_writes_local_visual_graph_surface`, add:

```python
    assert "graph-zoom-in" in graph_html
    assert "graph-zoom-out" in graph_html
    assert "graph-reset-view" in graph_html
    assert "Zoom in" in graph_html
    assert "Zoom out" in graph_html
    assert "Reset view" in graph_html
    assert "setGraphViewBox" in graph_script
    assert "zoomGraphView" in graph_script
    assert "resetGraphView" in graph_script
    assert "setGraphViewportControlsEnabled" in graph_script
```

- [ ] **Step 2: Run the focused contract test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface
```

Expected: FAIL because graph viewport controls and helpers do not exist yet.

### Task 2: Add Failing Browser Tests

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Extend graph e2e coverage**

In `test_preview_serves_local_visual_graph_surface`, after the graph canvas is visible and before broad reset behavior, capture and exercise the viewBox controls:

```python
                        initial_viewbox = page.locator("#raya-graph-canvas").get_attribute("viewBox")
                        assert _viewbox_width(initial_viewbox) > 0
                        page.click("#graph-zoom-in")
                        zoomed_viewbox = page.locator("#raya-graph-canvas").get_attribute("viewBox")
                        assert zoomed_viewbox != initial_viewbox
                        assert _viewbox_width(zoomed_viewbox) < _viewbox_width(initial_viewbox)
                        page.click("#graph-zoom-out")
                        zoomed_out_viewbox = page.locator("#raya-graph-canvas").get_attribute("viewBox")
                        assert _viewbox_width(zoomed_out_viewbox) > _viewbox_width(zoomed_viewbox)
                        page.click("#graph-fit")
                        assert page.locator("#raya-graph-canvas").get_attribute("viewBox") == initial_viewbox
                        page.click("#graph-zoom-in")
                        page.fill("#graph-search", "matrx")
                        assert page.locator("#raya-graph-canvas").get_attribute("viewBox") == initial_viewbox
                        page.click("#graph-zoom-in")
                        page.click("#graph-reset-view")
                        assert page.locator("#raya-graph-canvas").get_attribute("viewBox") == initial_viewbox
                        assert page.input_value("#graph-search") == "matrx"
                        assert page.locator("[data-raya-graph-detail-panel]").is_visible()
                        page.select_option("#graph-layout", "list")
                        assert page.locator("#graph-zoom-in").is_disabled()
                        assert page.locator("#graph-zoom-out").is_disabled()
                        assert page.locator("#graph-reset-view").is_disabled()
                        page.select_option("#graph-layout", "map")
                        assert page.locator("#graph-zoom-in").is_enabled()
```

Add a small helper near the e2e helper functions:

```python
def _viewbox_width(value: str | None) -> float:
    assert value is not None
    return float(value.split()[2])
```

- [ ] **Step 2: Run the focused browser test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: FAIL because `#graph-zoom-in` does not exist yet.

### Task 3: Implement Markup, JS, and CSS

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/graph.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Add graph controls markup**

In `_render_graph_surface`, after `graph-fit`, add:

```python
            '<button id="graph-zoom-in" type="button" aria-label="Zoom in graph">Zoom in</button>',
            '<button id="graph-zoom-out" type="button" aria-label="Zoom out graph">Zoom out</button>',
            '<button id="graph-reset-view" type="button" aria-label="Reset graph view">Reset view</button>',
```

- [ ] **Step 2: Add transient viewBox state**

In `graph.py`, add constants/state:

```javascript
  const zoomIn = document.getElementById("graph-zoom-in");
  const zoomOut = document.getElementById("graph-zoom-out");
  const resetView = document.getElementById("graph-reset-view");
  let graphViewBox = null;
  let fullViewBox = null;
```

Add helper functions:

```javascript
  function viewBoxString(box) {
    return `${box.x} ${box.y} ${box.width} ${box.height}`;
  }

  function setGraphViewBox(box) {
    graphViewBox = box;
    if (canvas && box) canvas.setAttribute("viewBox", viewBoxString(box));
  }

  function resetGraphView() {
    if (!fullViewBox) return;
    setGraphViewBox({ ...fullViewBox });
  }

  function setGraphViewportControlsEnabled(enabled) {
    [zoomIn, zoomOut, resetView].forEach((button) => {
      if (button) button.disabled = !enabled;
    });
  }

  function zoomGraphView(factor) {
    if (!graphViewBox || root.getAttribute("data-raya-graph-layout") === "list") return;
    const minWidth = fullViewBox ? fullViewBox.width * 0.32 : 240;
    const maxWidth = fullViewBox ? fullViewBox.width * 1.75 : 1680;
    const nextWidth = Math.max(minWidth, Math.min(maxWidth, graphViewBox.width * factor));
    const nextHeight = Math.max(
      fullViewBox ? fullViewBox.height * 0.32 : 180,
      Math.min(fullViewBox ? fullViewBox.height * 1.75 : 980, graphViewBox.height * factor)
    );
    const centerX = graphViewBox.x + graphViewBox.width / 2;
    const centerY = graphViewBox.y + graphViewBox.height / 2;
    setGraphViewBox({
      x: centerX - nextWidth / 2,
      y: centerY - nextHeight / 2,
      width: nextWidth,
      height: nextHeight,
    });
  }
```

In `render()`, after geometry is computed, set `fullViewBox` and preserve `graphViewBox` when possible:

```javascript
    fullViewBox = { x: 0, y: 0, width: geometry.width, height: geometry.height };
    if (!graphViewBox) {
      setGraphViewBox({ ...fullViewBox });
    } else {
      canvas.setAttribute("viewBox", viewBoxString(graphViewBox));
    }
```

Ensure list layout clears only the SVG display, not search/selection state, and disables viewport buttons:

```javascript
      graphViewBox = null;
      fullViewBox = null;
      setGraphViewportControlsEnabled(false);
```

On search, group-filter, `fit`, layout changes, and broad `reset`, call `graphViewBox = null` before `render()`.

Add event listeners:

```javascript
  if (zoomIn) zoomIn.addEventListener("click", () => zoomGraphView(0.82));
  if (zoomOut) zoomOut.addEventListener("click", () => zoomGraphView(1.22));
  if (resetView) resetView.addEventListener("click", resetGraphView);
```

- [ ] **Step 3: Add CSS affordances**

In `rendering.py`, add:

```css
.raya-graph-controls button:disabled {
  cursor: not-allowed;
  opacity: 0.52;
}
```

- [ ] **Step 4: Run focused tests and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: both pass.

### Task 4: Documentation

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/foundation/15_system_overview.md`
- Modify: `docs/foundation/18_known_missing_work.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Update docs**

Document graph zoom, fit, and reset-view as transient local inspection controls. State that they do not store graph state or represent progress.

- [ ] **Step 2: Run visible-language check**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_render_fixture_search_graph_course_map_visible_text_avoids_learner_state_language
```

Expected: pass.

### Task 5: Verify, Review, Commit, Push

**Files:**
- All modified files

- [ ] **Step 1: Run focused render debug**

```bash
./scripts/check-render-debug.sh
```

- [ ] **Step 2: Run host gate**

```bash
./scripts/check.sh
```

- [ ] **Step 3: Run Docker gate**

```bash
./scripts/check-docker.sh
```

- [ ] **Step 4: Request code review**

Use `superpowers:requesting-code-review` on the final diff.

- [ ] **Step 5: Commit and push**

```bash
git add docs/superpowers/specs/2026-06-23-graph-viewport-controls-design.md \
  docs/superpowers/plans/2026-06-23-graph-viewport-controls.md \
  docs/foundation/15_system_overview.md docs/foundation/18_known_missing_work.md \
  docs/foundation/20_learning_renderer_contract.md \
  docs/guides/en/students/index.md docs/guides/en/contributors/index.md \
  docs/guides/en/professors/index.md docs/guides/en/agents/index.md \
  docs/guides/es/estudiantes/index.md docs/guides/es/colaboradores/index.md \
  docs/guides/es/profesores/index.md docs/guides/es/agentes/index.md \
  packages/static/src/raya_static/builder.py packages/static/src/raya_static/graph.py \
  packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py \
  tests/e2e/test_preview_static_read_path.py
git commit -m "Add graph viewport controls"
git push origin new_rayalucaria
```
