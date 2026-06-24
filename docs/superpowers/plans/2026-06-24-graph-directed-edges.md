# Graph Directed Edges Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add static SVG arrowheads to graph edges so readers can see relationship direction without inspecting detail lists.

**Architecture:** Reuse the current embedded graph payload and SVG renderer. `graph.js` creates local `<defs><marker>` definitions per group color, assigns `marker-end` to line edges, and keeps all existing edge classes/status behavior.

**Tech Stack:** Python-generated vanilla JavaScript string, SVG, CSS, pytest, Playwright.

---

### Task 1: Add Failing Contract Assertions

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add graph direction assertions**

In `test_build_writes_local_visual_graph_surface`, near existing graph script assertions for edge color/kind, add:

```python
assert "raya-graph-arrow-marker" in graph_script
assert "marker-end" in graph_script
assert "Graph arrows show link direction" in graph_html
```

- [ ] **Step 2: Verify the test fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: FAIL because `graph.js` does not create markers and graph help does not mention direction arrows.

### Task 2: Add Failing Browser Assertions

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add SVG marker assertions**

In `test_preview_serves_local_visual_graph_surface`, inside the edge-style loop near the existing `computed` edge object, assert:

```python
marker_end = edge.first.get_attribute("marker-end")
assert marker_end is not None
assert marker_end.startswith("url(#raya-graph-arrow-")
marker_id = marker_end.removeprefix("url(#").removesuffix(")")
marker = page.locator(f"#{marker_id}")
assert marker.count() == 1
assert marker.get_attribute("class") == "raya-graph-arrow-marker"
marker_path_style = marker.locator("path").evaluate(
    "node => node.style.getPropertyValue('--raya-graph-edge-color')"
)
assert marker_path_style == computed["color"]
```

Also assert that a navigation edge and its reciprocal parent edge do not share identical geometry, preserving the existing parallel-edge check.

- [ ] **Step 2: Verify the e2e fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: FAIL because current SVG edge lines have no `marker-end`.

### Task 3: Implement Local SVG Arrowheads

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Add marker helpers in `graph.py`**

Add helpers before `render()`:

```javascript
function graphArrowMarkerId(edge) {
  return `raya-graph-arrow-${groupColorIndex((nodesById.get(edge.from) || {}).group || "")}`;
}

function graphArrowMarkerUrl(edge) {
  return `url(#${graphArrowMarkerId(edge)})`;
}

function appendGraphArrowMarkers(activeEdges) {
  const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
  const markerIds = new Set();
  activeEdges.forEach((edge) => {
    const markerId = graphArrowMarkerId(edge);
    if (markerIds.has(markerId)) return;
    markerIds.add(markerId);
    const marker = document.createElementNS("http://www.w3.org/2000/svg", "marker");
    marker.setAttribute("id", markerId);
    marker.setAttribute("class", "raya-graph-arrow-marker");
    marker.setAttribute("markerWidth", "8");
    marker.setAttribute("markerHeight", "8");
    marker.setAttribute("refX", "7");
    marker.setAttribute("refY", "4");
    marker.setAttribute("orient", "auto");
    marker.setAttribute("markerUnits", "strokeWidth");
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", "M 0 0 L 8 4 L 0 8 z");
    path.style.setProperty("--raya-graph-edge-color", edgeColorFor(edge));
    marker.appendChild(path);
    defs.appendChild(marker);
  });
  canvas.appendChild(defs);
}
```

- [ ] **Step 2: Insert defs and marker-end in render**

After `canvas.replaceChildren();`, call:

```javascript
appendGraphArrowMarkers(activeEdges);
```

When creating each edge line, add:

```javascript
line.setAttribute("marker-end", graphArrowMarkerUrl(edge));
```

- [ ] **Step 3: Add help/legend copy**

In `packages/static/src/raya_static/builder.py`, add a graph help paragraph:

```python
(
    "<p>Graph arrows show link direction from the source page to the "
    "target page. Direction is generated graph structure.</p>"
),
```

- [ ] **Step 4: Add CSS for marker path**

In `packages/static/src/raya_static/rendering.py`, near edge CSS:

```css
.raya-graph-arrow-marker path {
  fill: var(--raya-graph-edge-color, var(--raya-color-border));
  opacity: 0.82;
}
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: both tests PASS.

### Task 4: Review, Verify, Commit, Push

**Files:**
- No additional source files.

- [ ] **Step 1: Request code review**

Dispatch two reviewers:

- Static contract reviewer: no schema changes, no external dependencies, no fetch/storage, no learner-state language.
- Browser UX reviewer: arrows are visible, not disruptive, preserve edge kind/search/inspection styling.

- [ ] **Step 2: Run focused and broad verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
./scripts/check-render-debug.sh
./scripts/check.sh
```

Expected: all pass.

- [ ] **Step 3: Commit and push**

Run:

```bash
git status --short
git add docs/superpowers/specs/2026-06-24-graph-directed-edges-design.md docs/superpowers/plans/2026-06-24-graph-directed-edges.md packages/static/src/raya_static/graph.py packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add directed graph edge arrows"
git push origin new_rayalucaria
```

Expected: commit succeeds and branch pushes.

## Self-Review

- Spec coverage: direction cue, SVG-local implementation, no schema/fetch/storage/dependency changes, and verification are covered.
- Placeholder scan: no TODO/TBD placeholders.
- Type consistency: marker IDs, marker class, and `marker-end` assertions use the same names across tests and implementation.
