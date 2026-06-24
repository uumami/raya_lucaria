# Graph Neighborhood Focus Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add explicit, transient graph controls that narrow the Course graph to the selected page's neighborhood and let readers select connected pages from the detail panel without navigating away.

**Architecture:** Keep the current static graph payload and local SVG renderer. Add a static focus button placeholder in the graph detail panel, one in-memory JavaScript state flag, a filter step over already-visible graph nodes, item-level focus buttons in incoming/outgoing detail lists, small CSS affordances, focused contract/browser tests, and role/foundation docs.

**Tech Stack:** Python static builder, local JavaScript string in `packages/static/src/raya_static/graph.py`, static CSS in `packages/static/src/raya_static/rendering.py`, pytest contract tests, Playwright e2e tests, Superpowers review and verification gates.

---

### Task 1: Contract Test

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write the failing contract assertions**

In `test_build_writes_local_visual_graph_surface`, after the existing graph detail assertions, add:

```python
assert "data-raya-graph-focus-neighborhood" in graph_html
assert "Focus neighborhood" in graph_html
assert "setGraphNeighborhoodFocus" in graph_script
assert "neighborhoodFocus" in graph_script
assert "data-raya-graph-focus-node" in graph_script
assert "focusGraphDetailNode" in graph_script
```

- [ ] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface
```

Expected: FAIL because the focus button and graph focus state do not exist yet.

### Task 2: Browser Behavior Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write the failing browser assertions**

In `test_preview_serves_local_visual_graph_surface`, inside the existing loop after loading `/_raya/graph/index.html?page=authoring-matrix` and asserting neighbor classes, add:

```python
focus_button = page.locator("[data-raya-graph-focus-neighborhood]")
assert focus_button.is_visible()
assert focus_button.inner_text() == "Focus neighborhood"
focus_button.click()
page.wait_for_function(
    """() => document
      .querySelector('[data-raya-graph-page]')
      ?.getAttribute('data-raya-graph-neighborhood-focus') === 'true'"""
)
assert focus_button.inner_text() == "Show full graph"
assert "Neighborhood focus:" in page.locator("#graph-status").inner_text()
assert page.locator(
    '#raya-graph-list [data-raya-graph-node="authoring-matrix"]'
).is_visible()
assert page.locator(
    '#raya-graph-list [data-raya-graph-node="render-root"]'
).is_visible()
assert page.locator(
    '#raya-graph-list [data-raya-graph-node="static-path"]'
).is_hidden()
focus_button.click()
page.wait_for_function(
    """() => document
      .querySelector('[data-raya-graph-page]')
      ?.getAttribute('data-raya-graph-neighborhood-focus') === 'false'"""
)
assert page.locator(
    '#raya-graph-list [data-raya-graph-node="static-path"]'
).is_visible()
focus_math = page.locator('[data-raya-graph-focus-node="math-authoring"]').first
focus_math.click()
page.wait_for_function(
    """() => document
      .querySelector('[data-raya-graph-detail-title]')
      ?.textContent
      ?.includes('Math Authoring Fixture')"""
)
assert page.locator(
    '#raya-graph-list [data-raya-graph-node="math-authoring"]'
).evaluate("node => node.classList.contains('is-active')")
assert page.url.endswith("/_raya/graph/index.html?page=authoring-matrix")
page.click("#graph-reset")
assert (
    page.locator("[data-raya-graph-page]")
    .get_attribute("data-raya-graph-neighborhood-focus")
    == "false"
)
```

- [ ] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: FAIL because the focus button does not exist yet.

### Task 3: Static Graph Markup And Script

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/graph.py`

- [ ] **Step 1: Add the detail-panel button placeholder**

In `_render_graph_surface`, inside `.raya-graph-detail-actions`, after the existing graph detail links, add:

```html
<button type="button" data-raya-graph-focus-neighborhood hidden>Focus neighborhood</button>
```

- [ ] **Step 2: Add script references and state**

In `graph.py`, add:

```javascript
const focusNeighborhood = document.querySelector("[data-raya-graph-focus-neighborhood]");
let neighborhoodFocus = false;
```

- [ ] **Step 3: Add focus helper**

Add this helper before `renderDetail()`:

```javascript
function setGraphNeighborhoodFocus(enabled) {
  neighborhoodFocus = Boolean(enabled && selectedId);
  root.setAttribute("data-raya-graph-neighborhood-focus", neighborhoodFocus ? "true" : "false");
  if (focusNeighborhood) {
    focusNeighborhood.hidden = !selectedId;
    focusNeighborhood.textContent = neighborhoodFocus ? "Show full graph" : "Focus neighborhood";
    focusNeighborhood.setAttribute("aria-pressed", neighborhoodFocus ? "true" : "false");
  }
}
```

- [ ] **Step 4: Apply focus filtering**

In `visibleNodes()`, after the current search-expanded node set is computed, filter it through `neighborsOf(selectedId)` when `neighborhoodFocus` and `selectedId` are active. The helper should preserve hidden group filters:

```javascript
function applyNeighborhoodFocus(activeNodes) {
  if (!neighborhoodFocus || !selectedId) return activeNodes;
  const focusIds = neighborsOf(selectedId);
  return activeNodes.filter((node) => focusIds.has(node.id));
}
```

Use it for both the no-query and query branches.

- [ ] **Step 5: Keep focus state coherent**

In `renderDetail()`, call `setGraphNeighborhoodFocus(false)` when there is no selected node and `setGraphNeighborhoodFocus(neighborhoodFocus)` after rendering a selected node.

In `selectGraphNode(nodeId)`, reset `neighborhoodFocus = false` before rendering detail.

In `clearGraphSelection()` and Reset, call `setGraphNeighborhoodFocus(false)`.

Add a click listener:

```javascript
if (focusNeighborhood) {
  focusNeighborhood.addEventListener("click", () => {
    setGraphNeighborhoodFocus(!neighborhoodFocus);
    graphViewBox = null;
    render();
  });
}
```

- [ ] **Step 6: Add connected-item focus buttons**

In `renderDetailList(listEl, items, emptyText)`, keep the existing page link and
edge-kind text, then add a separate button when `item.id` resolves to a known
node:

```javascript
if (nodesById.has(item.id)) {
  const focus = document.createElement("button");
  focus.type = "button";
  focus.className = "raya-graph-detail-focus-node";
  focus.dataset.rayaGraphFocusNode = item.id;
  focus.textContent = "Focus";
  focus.addEventListener("click", () => focusGraphDetailNode(item.id));
  li.appendChild(focus);
}
```

Add a helper before `renderDetailList()`:

```javascript
function focusGraphDetailNode(nodeId) {
  if (!nodesById.has(nodeId)) return;
  graphViewBox = null;
  selectGraphNode(nodeId);
}
```

- [ ] **Step 7: Update status text**

When focus mode is active, make `#graph-status` start with:

```text
Neighborhood focus:
```

and keep the existing visible node/edge count language after it.

- [ ] **Step 8: Verify GREEN for focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: PASS.

### Task 4: CSS And Documentation

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Style the focus button**

Extend the graph detail button styles so `[data-raya-graph-focus-neighborhood]` and `.raya-graph-detail-focus-node` have the same shape as the detail clear button and visibly active `aria-pressed="true"` state:

```css
.raya-graph-detail button[aria-pressed="true"] {
  background: var(--raya-color-accent);
  border-color: var(--raya-color-accent);
  color: var(--raya-color-accent-contrast);
}
.raya-graph-detail-focus-node {
  margin-left: 0.4rem;
}
```

- [ ] **Step 2: Update foundation docs**

In `docs/foundation/20_learning_renderer_contract.md`, extend the static graph paragraph to mention non-persistent selected-neighborhood focus mode that narrows visible graph/list nodes to explicit directly connected pages and never implies recommendation/progress/mastery.

- [ ] **Step 3: Update agent docs in English and Spanish**

In the Course graph verification paragraphs, add selected-neighborhood focus mode to the checks and explicitly require no graph-state persistence, fetch, external graph libraries, or recommendation/progress language.

- [ ] **Step 4: Verify docs and focused tests**

Run:

```bash
git diff --check
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: both commands exit 0.

### Task 5: Review And Gates

**Files:**
- Review all changed files.

- [ ] **Step 1: Request independent code review**

Dispatch a read-only reviewer with the design, plan, and git diff. Ask it to focus on graph static boundaries, no persistence/fetch, accessibility, selected-neighborhood correctness, and test coverage.

- [ ] **Step 2: Run focused render-debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: exits 0 and reports passed checks.

- [ ] **Step 3: Run full host gate**

Run:

```bash
./scripts/check.sh
```

Expected: exits 0.

- [ ] **Step 4: Run Docker gate**

Run:

```bash
./scripts/check-docker.sh
```

Expected: exits 0.

- [ ] **Step 5: Commit and push**

Run:

```bash
git add docs/foundation/20_learning_renderer_contract.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/graph.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add graph neighborhood focus mode"
git push origin new_rayalucaria
```
