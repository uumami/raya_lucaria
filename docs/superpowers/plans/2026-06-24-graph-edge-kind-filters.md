# Graph Edge Kind Filters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local graph edge-kind filter chips so readers can isolate navigation, content, prerequisite, and parent relationships without leaving the static graph.

**Architecture:** Render edge-kind filter buttons in the generated graph HTML, maintain a transient `hiddenEdgeKinds` set in `graph.js`, filter only visible SVG edges, and update status/reset behavior. Keep nodes, graph list, inspector, search, group filters, and payload schema unchanged.

**Tech Stack:** Python static builder, embedded vanilla JavaScript graph renderer, CSS in `rich.css`, pytest, Playwright.

---

## File Map

- `packages/static/src/raya_static/builder.py`: graph HTML for the filter button group and help copy.
- `packages/static/src/raya_static/graph.py`: transient edge-kind filter state, edge filtering, status text, reset behavior, and chip event handlers.
- `packages/static/src/raya_static/rendering.py`: chip layout and pressed/unpressed styling.
- `tests/contracts/test_static_builder.py`: generated HTML/JS/CSS assertions.
- `tests/e2e/test_preview_static_read_path.py`: browser behavior assertions for toggling and reset.

## Task 1: Add Failing Contract Assertions

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add graph edge-filter HTML assertions**

In `test_build_writes_local_visual_graph_surface`, near the existing graph toolbar and edge legend assertions, add:

```python
assert 'aria-label="Edge filters"' in graph_html
for kind, label in (
    ("navigation", "Navigation"),
    ("content", "Content"),
    ("prerequisite", "Prerequisite"),
    ("parent", "Parent"),
):
    assert f'data-raya-graph-edge-kind-filter="{kind}"' in graph_html
    assert f'aria-pressed="true">{label}</button>' in graph_html
```

- [ ] **Step 2: Add graph edge-filter script/style assertions**

In the same test, near existing graph script/style assertions, add:

```python
assert "hiddenEdgeKinds" in graph_script
assert "visibleGraphEdges" in graph_script
assert "data-raya-graph-edge-kind-filter" in graph_script
assert "edge kind" in graph_script.lower()
assert ".raya-graph-edge-kind-filters" in stylesheet
assert ".raya-graph-edge-kind-filter" in stylesheet
assert "localStorage" not in graph_script
assert "sessionStorage" not in graph_script
```

- [ ] **Step 3: Verify the contract test fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: FAIL because graph HTML has no edge-kind filter buttons and graph JS has no `hiddenEdgeKinds` logic.

## Task 2: Add Failing Browser Assertions

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Assert default edge filters are pressed**

In `test_preview_serves_local_visual_graph_surface`, after the legend visibility assertions, add:

```python
for kind in ("navigation", "content", "prerequisite", "parent"):
    button = page.locator(f'[data-raya-graph-edge-kind-filter="{kind}"]')
    assert button.is_visible()
    assert button.get_attribute("aria-pressed") == "true"
```

- [ ] **Step 2: Assert toggling one edge kind hides only that kind**

After the existing edge-kind assertions have confirmed the fixture contains all four kinds, add:

```python
content_filter = page.locator('[data-raya-graph-edge-kind-filter="content"]')
content_edges = page.locator(
    '#raya-graph-canvas .raya-graph-edge[data-raya-graph-kind="content"]'
)
content_count = content_edges.count()
assert content_count >= 1
node_count_before_filter = page.locator(
    "#raya-graph-canvas [data-raya-graph-node]"
).count()
content_filter.click()
page.wait_for_function(
    """() => document
      .querySelector('[data-raya-graph-edge-kind-filter="content"]')
      ?.getAttribute('aria-pressed') === 'false'"""
)
assert content_edges.count() == 0
assert page.locator(
    "#raya-graph-canvas [data-raya-graph-node]"
).count() == node_count_before_filter
assert "1 edge kind hidden" in page.locator("#graph-status").inner_text()
assert page.locator("#raya-graph-canvas .raya-graph-arrow-marker").count() == page.locator(
    "#raya-graph-canvas .raya-graph-edge"
).count()
```

- [ ] **Step 3: Assert reset restores hidden edge kinds**

Continue the same browser block:

```python
page.click("#graph-reset")
page.wait_for_function(
    """() => document
      .querySelector('[data-raya-graph-edge-kind-filter="content"]')
      ?.getAttribute('aria-pressed') === 'true'"""
)
assert page.locator(
    '#raya-graph-canvas .raya-graph-edge[data-raya-graph-kind="content"]'
).count() == content_count
```

- [ ] **Step 4: Verify the e2e test fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: FAIL because no edge-kind filter buttons exist.

## Task 3: Implement Edge-Kind Filters

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/graph.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Add edge-filter buttons to graph HTML**

In `_render_graph_surface()`, inside `.raya-graph-controls`, add a toolbar group after the layout/search controls:

```python
(
    '<div class="raya-graph-toolbar-group raya-graph-edge-kind-filters" '
    'role="group" aria-label="Edge filters">'
),
"<span>Edges</span>",
(
    '<button type="button" data-raya-graph-edge-kind-filter="navigation" '
    'aria-pressed="true">Navigation</button>'
),
(
    '<button type="button" data-raya-graph-edge-kind-filter="content" '
    'aria-pressed="true">Content</button>'
),
(
    '<button type="button" data-raya-graph-edge-kind-filter="prerequisite" '
    'aria-pressed="true">Prerequisite</button>'
),
(
    '<button type="button" data-raya-graph-edge-kind-filter="parent" '
    'aria-pressed="true">Parent</button>'
),
"</div>",
```

Add help copy:

```python
(
    "<p>Edge filters hide or show relationship kinds in the SVG graph. "
    "They do not remove pages from the list or selected-page inspector.</p>"
),
```

- [ ] **Step 2: Add transient filter state to graph JS**

Near `groupFilters`, add:

```javascript
const edgeKindFilters = Array.from(
  document.querySelectorAll("[data-raya-graph-edge-kind-filter]")
);
```

Near `hiddenGroups`, add:

```javascript
const hiddenEdgeKinds = new Set();
```

Add helper functions near `visibleEdges()`:

```javascript
function visibleGraphEdges(visibleIds) {
  return edges.filter((edge) => (
    visibleIds.has(edge.from) &&
    visibleIds.has(edge.to) &&
    !hiddenEdgeKinds.has(edgeKind(edge))
  ));
}

function updateEdgeKindFilters() {
  edgeKindFilters.forEach((button) => {
    const kind = button.getAttribute("data-raya-graph-edge-kind-filter") || "";
    button.setAttribute("aria-pressed", hiddenEdgeKinds.has(kind) ? "false" : "true");
  });
}

function hiddenEdgeKindStatusText() {
  const count = hiddenEdgeKinds.size;
  if (!count) return "";
  return `${count} edge kind${count === 1 ? "" : "s"} hidden.`;
}
```

In `render()`, change:

```javascript
const activeEdges = visibleEdges(activeIds);
```

to:

```javascript
const activeEdges = visibleGraphEdges(activeIds);
```

Then append `hiddenEdgeKindStatusText()` to both status branches:

```javascript
const edgeKindText = hiddenEdgeKindStatusText();
...
status.textContent = [baseStatusText, edgeKindText].filter(Boolean).join(" ");
```

- [ ] **Step 3: Wire filter events and reset**

Near the group filter event listeners, add:

```javascript
edgeKindFilters.forEach((button) => {
  button.addEventListener("click", () => {
    const kind = button.getAttribute("data-raya-graph-edge-kind-filter") || "";
    if (!kind) return;
    if (hiddenEdgeKinds.has(kind)) {
      hiddenEdgeKinds.delete(kind);
    } else {
      hiddenEdgeKinds.add(kind);
    }
    graphViewBox = null;
    updateEdgeKindFilters();
    render();
  });
});
```

Inside the reset click handler, after `hiddenGroups.clear();`, add:

```javascript
hiddenEdgeKinds.clear();
updateEdgeKindFilters();
```

During initialization before `renderDetail();`, call:

```javascript
updateEdgeKindFilters();
```

- [ ] **Step 4: Add CSS for filter chips**

Near `.raya-graph-toolbar` styles in `rendering.py`, add:

```css
.raya-graph-edge-kind-filters {
  align-items: center;
}
.raya-graph-edge-kind-filters > span {
  color: var(--raya-color-muted);
  font-size: 0.85rem;
  font-weight: 800;
}
.raya-graph-edge-kind-filter[aria-pressed="false"],
[data-raya-graph-edge-kind-filter][aria-pressed="false"] {
  background: var(--raya-color-surface);
  border-color: var(--raya-color-border);
  color: var(--raya-color-muted);
  opacity: 0.72;
}
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: both tests PASS.

## Task 4: Review, Verify, Commit, Push

**Files:**
- No additional source files.

- [ ] **Step 1: Request independent review**

Dispatch at least one reviewer focused on:

- No schema change, no storage/fetch/CDN/library.
- Edge-kind filters hide only SVG edges/markers, not pages.
- Search, group filters, arrows, reset, list layout, and inspector still make sense.

- [ ] **Step 2: Run verification**

Run sequentially:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: all commands PASS.

- [ ] **Step 3: Commit and push**

Run:

```bash
git status --short
git add docs/superpowers/specs/2026-06-24-graph-edge-kind-filters-design.md docs/superpowers/plans/2026-06-24-graph-edge-kind-filters.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/graph.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add graph edge kind filters"
git push origin new_rayalucaria
```

Expected: commit succeeds and `origin/new_rayalucaria` advances.

## Self-Review

- Spec coverage: transient filter state, edge-only filtering, reset behavior, no schema/storage/library changes, and test coverage are mapped to tasks.
- Placeholder scan: no TODO/TBD placeholders.
- Type consistency: `hiddenEdgeKinds`, `visibleGraphEdges`, `data-raya-graph-edge-kind-filter`, and CSS class names are consistent across plan, tests, and implementation steps.
