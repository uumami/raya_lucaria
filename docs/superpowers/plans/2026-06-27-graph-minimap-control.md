# Graph Minimap Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the passive graph minimap into a keyboard-reachable viewport control that centers the main SVG graph view.

**Architecture:** Keep all behavior inside the existing generated graph workspace. Add operable minimap markup in `builder.py`, styling in `rendering.py`, and local viewport math/event handling in `graph.py`.

**Tech Stack:** Python static builder, generated local JavaScript, SVG, CSS, pytest, Playwright.

---

### Task 1: RED Tests

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Extend the minimap browser test**

Add assertions that clicking the minimap changes the main SVG `viewBox`, moves the minimap viewport, keeps the selected page selected, keeps storage empty, keeps overflow safe, and makes no external requests.

- [x] **Step 2: Extend the graph resource contract test**

Assert that generated HTML exposes the minimap as `role="button"` with `tabindex="0"`, that the accessible label names the center action, that CSS gives the minimap an action cursor, and that graph JS includes `centerGraphViewFromMinimapEvent` plus click and keydown listeners.

- [x] **Step 3: Run RED tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_minimap_tracks_viewport \
  tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface
```

Expected: FAIL because the minimap is not yet operable and graph JS has no minimap event handler.

### Task 2: Minimap Markup and Styling

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Update minimap semantics**

In `_render_graph_surface`, change the minimap SVG to:

```html
<svg id="raya-graph-minimap" class="raya-graph-minimap"
     role="button"
     aria-label="Graph overview and current viewport; activate to center the graph view"
     tabindex="0" focusable="true">
```

- [x] **Step 2: Style the minimap as operable**

Add cursor/focus styling:

```css
.raya-graph-minimap {
  cursor: crosshair;
}
.raya-graph-minimap:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
```

### Task 3: Minimap Viewport Centering

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`

- [x] **Step 1: Add viewBox clamping helper**

Add a helper near viewport functions:

```javascript
function clampGraphViewBox(box) {
  if (!fullViewBox) return box;
  const width = Math.min(box.width, fullViewBox.width);
  const height = Math.min(box.height, fullViewBox.height);
  const x = Math.max(
    fullViewBox.x,
    Math.min(fullViewBox.x + fullViewBox.width - width, box.x)
  );
  const y = Math.max(
    fullViewBox.y,
    Math.min(fullViewBox.y + fullViewBox.height - height, box.y)
  );
  return { x, y, width, height };
}
```

- [x] **Step 2: Center the main view from minimap activation**

Add:

```javascript
function centerGraphViewFromMinimapEvent(event) {
  if (!minimap || !graphViewBox || !fullViewBox || root.getAttribute("data-raya-graph-layout") === "list") {
    return;
  }
  const rect = minimap.getBoundingClientRect();
  const ratioX = event && typeof event.clientX === "number"
    ? Math.max(0, Math.min(1, (event.clientX - rect.left) / Math.max(1, rect.width)))
    : 0.5;
  const ratioY = event && typeof event.clientY === "number"
    ? Math.max(0, Math.min(1, (event.clientY - rect.top) / Math.max(1, rect.height)))
    : 0.5;
  const centerX = fullViewBox.x + fullViewBox.width * ratioX;
  const centerY = fullViewBox.y + fullViewBox.height * ratioY;
  setGraphViewBox(clampGraphViewBox({
    x: centerX - graphViewBox.width / 2,
    y: centerY - graphViewBox.height / 2,
    width: graphViewBox.width,
    height: graphViewBox.height,
  }));
}
```

- [x] **Step 3: Wire click and keyboard events**

Near existing canvas event wiring, add:

```javascript
if (minimap) {
  minimap.addEventListener("click", centerGraphViewFromMinimapEvent);
  minimap.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    centerGraphViewFromMinimapEvent(null);
  });
}
```

### Task 4: Verification, Review, Commit, Push

**Files:**
- No additional source files expected.

- [x] **Step 1: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_minimap_tracks_viewport \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_focus_mode_refits_selected_context \
  tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface
```

Expected: PASS.

- [x] **Step 2: Run render-debug**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS.

- [x] **Step 3: Request independent review**

Ask a reviewer to inspect the viewport-only behavior, no storage/no fetch/no external dependency, keyboard reachability, and test coverage.

- [x] **Step 4: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-27-graph-minimap-control-design.md \
  docs/superpowers/plans/2026-06-27-graph-minimap-control.md \
  packages/static/src/raya_static/builder.py \
  packages/static/src/raya_static/rendering.py \
  packages/static/src/raya_static/graph.py \
  tests/e2e/test_preview_static_read_path.py \
  tests/contracts/test_static_builder.py
git commit -m "Make graph minimap control viewport"
git push origin new_rayalucaria
```
