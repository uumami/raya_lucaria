# Graph Pan Viewport Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local graph viewport panning through SVG drag, focused canvas arrow keys, and explicit pan buttons without changing graph data or state persistence.

**Architecture:** Reuse the existing `graphViewBox` and `fullViewBox` state in the generated graph script. Pan controls mutate only the SVG `viewBox`; they do not trigger graph re-render or clear search, filters, selected details, or graph data.

**Tech Stack:** Python 3.10 package resources that emit static HTML/CSS/JS, pytest, Playwright e2e static preview tests.

---

## File Structure

- `packages/static/src/raya_static/builder.py`: add pan button markup and focusable SVG attributes.
- `packages/static/src/raya_static/graph.py`: add pan helper, pointer drag handling, and keyboard handling.
- `packages/static/src/raya_static/rendering.py`: add pan button/canvas drag affordance styles.
- `docs/foundation/20_learning_renderer_contract.md`: authoritative renderer contract wording.
- `docs/guides/en/agents/index.md`: English agent verification guidance.
- `docs/guides/es/agentes/index.md`: Spanish agent verification guidance.
- `tests/contracts/test_static_builder.py`: generated graph HTML/JS/CSS assertions.
- `tests/e2e/test_preview_static_read_path.py`: Playwright graph viewport behavior assertions.

## Task 1: Failing Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add contract assertions**

In `test_build_writes_local_visual_graph_surface`, assert:

```python
assert "Pan graph left" in graph_html
assert "Pan graph right" in graph_html
assert 'tabindex="0"' in graph_html
assert "panGraphView" in graph_script
assert "startGraphPan" in graph_script
assert "data-raya-graph-pan" in graph_script
assert ".raya-graph-pan-controls" in stylesheet
```

- [ ] **Step 2: Add browser pan assertions**

In `test_preview_serves_local_visual_graph_surface`, after existing graph viewport checks, add:

```python
page.fill("#graph-search", "matrix")
page.press("#graph-search", "ArrowDown")
page.locator(
    '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
).click()
assert page.input_value("#graph-search") == "matrix"
assert page.locator("[data-raya-graph-detail-panel]").is_visible()
before_pan = _viewbox_values(page.locator("#raya-graph-canvas").get_attribute("viewBox"))
page.locator("#raya-graph-canvas").focus()
page.keyboard.press("ArrowRight")
after_key_pan = _viewbox_values(page.locator("#raya-graph-canvas").get_attribute("viewBox"))
assert after_key_pan[0] > before_pan[0]
assert page.input_value("#graph-search") == "matrix"
assert page.locator("[data-raya-graph-detail-panel]").is_visible()

page.click('[data-raya-graph-pan="left"]')
after_button_pan = _viewbox_values(page.locator("#raya-graph-canvas").get_attribute("viewBox"))
assert after_button_pan[0] < after_key_pan[0]

box = page.locator("#raya-graph-canvas").bounding_box()
assert box is not None
before_drag = _viewbox_values(page.locator("#raya-graph-canvas").get_attribute("viewBox"))
page.mouse.move(box["x"] + box["width"] * 0.55, box["y"] + box["height"] * 0.55)
page.mouse.down()
page.mouse.move(box["x"] + box["width"] * 0.35, box["y"] + box["height"] * 0.55)
page.mouse.up()
after_drag = _viewbox_values(page.locator("#raya-graph-canvas").get_attribute("viewBox"))
assert after_drag[0] > before_drag[0]
assert page.input_value("#graph-search") == "matrix"
assert page.locator("[data-raya-graph-detail-panel]").is_visible()
```

- [ ] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: FAIL because pan controls and helpers are not implemented yet.

## Task 2: Graph Markup And Script

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/graph.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Add pan controls and focusable SVG**

In `_render_graph_surface()`, near the zoom controls, add four pan buttons:

```html
<span class="raya-graph-pan-controls" aria-label="Pan graph">
  <button type="button" data-raya-graph-pan="left" aria-label="Pan graph left">Left</button>
  <button type="button" data-raya-graph-pan="right" aria-label="Pan graph right">Right</button>
  <button type="button" data-raya-graph-pan="up" aria-label="Pan graph up">Up</button>
  <button type="button" data-raya-graph-pan="down" aria-label="Pan graph down">Down</button>
</span>
```

Add `tabindex="0"` to `#raya-graph-canvas`.

- [ ] **Step 2: Add pan state and controls**

In `packages/static/src/raya_static/graph.py`, query pan buttons:

```javascript
  const panButtons = Array.from(document.querySelectorAll("[data-raya-graph-pan]"));
```

Add transient drag state near `graphViewBox`:

```javascript
  let graphPanStart = null;
```

- [ ] **Step 3: Add pan helper**

Near `zoomGraphView`, add:

```javascript
  function panGraphView(dxRatio, dyRatio) {
    if (!graphViewBox || !fullViewBox || root.getAttribute("data-raya-graph-layout") === "list") {
      return;
    }
    setGraphViewBox({
      x: graphViewBox.x + graphViewBox.width * dxRatio,
      y: graphViewBox.y + graphViewBox.height * dyRatio,
      width: graphViewBox.width,
      height: graphViewBox.height,
    });
  }
```

- [ ] **Step 4: Add pointer drag helpers**

Add:

```javascript
  function startGraphPan(event) {
    if (!graphViewBox || event.button !== 0 || root.getAttribute("data-raya-graph-layout") === "list") {
      return;
    }
    const rect = canvas.getBoundingClientRect();
    graphPanStart = {
      pointerId: event.pointerId,
      clientX: event.clientX,
      clientY: event.clientY,
      rectWidth: Math.max(1, rect.width),
      rectHeight: Math.max(1, rect.height),
      box: { ...graphViewBox },
    };
    canvas.setPointerCapture(event.pointerId);
    canvas.classList.add("is-panning");
    event.preventDefault();
  }

  function moveGraphPan(event) {
    if (!graphPanStart || graphPanStart.pointerId !== event.pointerId) return;
    const dx = ((event.clientX - graphPanStart.clientX) / graphPanStart.rectWidth) * graphPanStart.box.width;
    const dy = ((event.clientY - graphPanStart.clientY) / graphPanStart.rectHeight) * graphPanStart.box.height;
    setGraphViewBox({
      x: graphPanStart.box.x - dx,
      y: graphPanStart.box.y - dy,
      width: graphPanStart.box.width,
      height: graphPanStart.box.height,
    });
  }

  function endGraphPan(event) {
    if (!graphPanStart || graphPanStart.pointerId !== event.pointerId) return;
    graphPanStart = null;
    canvas.classList.remove("is-panning");
  }
```

- [ ] **Step 5: Wire events**

Add event listeners:

```javascript
  panButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const direction = button.getAttribute("data-raya-graph-pan") || "";
      if (direction === "left") panGraphView(-0.16, 0);
      if (direction === "right") panGraphView(0.16, 0);
      if (direction === "up") panGraphView(0, -0.16);
      if (direction === "down") panGraphView(0, 0.16);
    });
  });
  canvas.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      panGraphView(-0.12, 0);
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      panGraphView(0.12, 0);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      panGraphView(0, -0.12);
    } else if (event.key === "ArrowDown") {
      event.preventDefault();
      panGraphView(0, 0.12);
    }
  });
  canvas.addEventListener("pointerdown", startGraphPan);
  canvas.addEventListener("pointermove", moveGraphPan);
  canvas.addEventListener("pointerup", endGraphPan);
  canvas.addEventListener("pointercancel", endGraphPan);
```

- [ ] **Step 6: Add CSS**

In `packages/static/src/raya_static/rendering.py`, add:

```css
.raya-graph-pan-controls {
  align-items: center;
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.raya-graph-canvas {
  cursor: grab;
}
.raya-graph-canvas.is-panning {
  cursor: grabbing;
}
.raya-graph-canvas:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
```

- [ ] **Step 7: Add help copy**

In graph help copy, add:

```html
<p>Drag the graph canvas, use pan buttons, or focus the graph and use Arrow keys to move the viewport. Pan changes only the viewport.</p>
```

- [ ] **Step 8: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: PASS.

## Task 3: Documentation

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Update foundation wording**

In the static graph paragraph, add that graph viewport controls may include zoom,
pan buttons, focused canvas Arrow-key panning, pointer drag panning, Fit, and
Reset view. Keep the sentence that viewport changes do not clear search,
filters, selected-page details, or graph data.

- [ ] **Step 2: Update English agent guidance**

Add verification guidance that pan controls are local, transient, keyboard
reachable, and do not persist or clear graph state.

- [ ] **Step 3: Update Spanish agent guidance**

Add equivalent Spanish guidance while keeping technical identifiers such as
`Arrow keys`, `Fit`, and `Reset view` in English.

- [ ] **Step 4: Verify focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/contracts/test_static_builder.py::test_render_fixture_search_graph_course_map_visible_text_avoids_learner_state_language tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: PASS.

## Task 4: Review And Gates

**Files:**
- No direct edits unless review finds issues.

- [ ] **Step 1: Request independent code review**

Ask a subagent to review current working tree for Critical/Important issues in
graph viewport pan behavior, static constraints, accessibility, and test
coverage.

- [ ] **Step 2: Fix valid Critical/Important findings**

Use TDD for any behavior change found by review.

- [ ] **Step 3: Run verification**

Run:

```bash
git diff --check
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: all pass. Run `check.sh` and `check-docker.sh` sequentially, not concurrently.

- [ ] **Step 4: Commit and push**

Commit and push:

```bash
git add docs/foundation/20_learning_renderer_contract.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/graph.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add graph viewport panning"
git push origin new_rayalucaria
```

## Self-Review

- The plan covers every design goal.
- The task list starts with failing tests before implementation.
- No placeholders remain.
- The plan keeps graph viewport state transient and avoids external resources or storage.
