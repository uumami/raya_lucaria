# Graph Inspection Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a compact graph inspection preview card that gives immediate page context on graph hover/focus without changing selection or navigation semantics.

**Architecture:** Add one static preview container to the graph map panel in `builder.py`, below the SVG canvas so inspection does not shift the graph under the pointer. Populate it from the already embedded graph JSON in `graph.py`, and style it with existing token-based CSS in `rendering.py`. The preview reuses existing inspection lifecycle state (`inspectedId`) and selected-page behavior (`selectGraphNode`) without adding storage, fetches, external libraries, or new graph data fields.

**Tech Stack:** Python 3.10 static builder, local vanilla JavaScript graph resource, token CSS, pytest/Playwright.

---

### Task 1: Add Failing Preview Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add contract assertions**

In `test_build_writes_local_visual_graph_surface`, near the existing graph hover/status assertions, add:

```python
assert "raya-graph-inspection-preview" in graph_html
assert "data-raya-graph-inspection-preview" in graph_html
assert "data-raya-graph-inspection-preview-title" in graph_html
assert "data-raya-graph-inspection-preview-summary" in graph_html
assert "data-raya-graph-inspection-preview-meta" in graph_html
assert "data-raya-graph-inspection-preview-counts" in graph_html
assert "data-raya-graph-inspection-preview-select" in graph_html
assert "data-raya-graph-inspection-preview-open" in graph_html
assert "renderInspectionPreview" in graph_script
assert "inspectionPreviewTextFor" in graph_script
assert ".raya-graph-inspection-preview" in stylesheet
```

- [x] **Step 2: Add browser behavior assertions**

In `test_preview_serves_local_visual_graph_surface`, in the first graph browser section after the existing initial graph layout assertions, add:

```python
preview = page.locator("[data-raya-graph-inspection-preview]")
assert preview.is_hidden()
page.locator(
    '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
).focus()
page.wait_for_selector("[data-raya-graph-inspection-preview]:not([hidden])")
assert "Authoring Matrix Fixture" in preview.locator(
    "[data-raya-graph-inspection-preview-title]"
).inner_text()
assert "Combined fixture page for copyable authoring patterns" in preview.locator(
    "[data-raya-graph-inspection-preview-summary]"
).inner_text()
assert "ready" in preview.locator(
    "[data-raya-graph-inspection-preview-meta]"
).inner_text().lower()
assert "4 outgoing" in preview.locator(
    "[data-raya-graph-inspection-preview-counts]"
).inner_text()
assert "2 incoming" in preview.locator(
    "[data-raya-graph-inspection-preview-counts]"
).inner_text()
assert "4 connected" in preview.locator(
    "[data-raya-graph-inspection-preview-counts]"
).inner_text()
assert page.locator("[data-raya-graph-detail-empty]").is_visible()
preview.locator("[data-raya-graph-inspection-preview-select]").click()
page.wait_for_selector("[data-raya-graph-detail-panel]:not([hidden])")
assert "Authoring Matrix Fixture" in page.locator(
    "[data-raya-graph-detail-title]"
).inner_text()
preview_open_href = preview.locator(
    "[data-raya-graph-inspection-preview-open]"
).get_attribute("href")
node_href = page.locator(
    '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
).get_attribute("href")
assert preview_open_href == node_href
page.click("#graph-reset")
assert preview.is_hidden()
```

- [x] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: FAIL because the preview markup, script hooks, and CSS class do not exist yet.

### Task 2: Add Preview Markup and Styles

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Add the static preview container**

In the graph map panel immediately after the SVG canvas, add:

```html
<section class="raya-graph-inspection-preview" data-raya-graph-inspection-preview hidden aria-label="Graph page preview" aria-live="polite">
  <div class="raya-graph-inspection-preview-header">
    <h2 data-raya-graph-inspection-preview-title>Page preview</h2>
    <p data-raya-graph-inspection-preview-meta></p>
  </div>
  <p data-raya-graph-inspection-preview-summary></p>
  <p class="raya-graph-inspection-preview-counts" data-raya-graph-inspection-preview-counts></p>
  <p class="raya-graph-inspection-preview-actions">
    <button type="button" data-raya-graph-inspection-preview-select>Inspect page</button>
    <a data-raya-graph-inspection-preview-open href="../../index.html">Open page</a>
  </p>
</section>
```

- [x] **Step 2: Add token-based CSS**

Add CSS in `packages/static/src/raya_static/rendering.py` near the existing graph status styles:

```css
.raya-graph-inspection-preview {
  background: color-mix(in srgb, var(--raya-color-surface) 90%, var(--raya-color-accent-soft));
  border: 1px solid var(--raya-color-border);
  border-radius: 0.5rem;
  margin: 0.65rem 0;
  padding: 0.8rem 0.9rem;
  pointer-events: none;
}
.raya-graph-inspection-preview-header {
  align-items: baseline;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.75rem;
  justify-content: space-between;
}
.raya-graph-inspection-preview h2 {
  font-size: 1rem;
  margin: 0;
}
.raya-graph-inspection-preview p {
  margin: 0.4rem 0 0;
}
.raya-graph-inspection-preview [data-raya-graph-inspection-preview-meta],
.raya-graph-inspection-preview-counts {
  color: var(--raya-color-muted);
  font-size: 0.875rem;
  font-weight: 700;
}
.raya-graph-inspection-preview-actions {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  pointer-events: auto;
}
```

### Task 3: Render Preview from Existing Inspection State

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`

- [x] **Step 1: Capture preview DOM nodes**

Near the other graph detail selectors, add:

```javascript
const inspectionPreview = document.querySelector("[data-raya-graph-inspection-preview]");
const inspectionPreviewTitle = document.querySelector("[data-raya-graph-inspection-preview-title]");
const inspectionPreviewMeta = document.querySelector("[data-raya-graph-inspection-preview-meta]");
const inspectionPreviewSummary = document.querySelector("[data-raya-graph-inspection-preview-summary]");
const inspectionPreviewCounts = document.querySelector("[data-raya-graph-inspection-preview-counts]");
const inspectionPreviewSelect = document.querySelector("[data-raya-graph-inspection-preview-select]");
const inspectionPreviewOpen = document.querySelector("[data-raya-graph-inspection-preview-open]");
```

- [x] **Step 2: Add preview text helpers**

Add:

```javascript
function inspectionPreviewTextFor(node) {
  const group = groupsById.get(node.group || "");
  return [
    group ? group.title : "",
    node.hierarchy_label || "",
    node.status ? `Status: ${node.status}` : "",
  ].filter(Boolean).join(" · ");
}

function inspectionPreviewCountTextFor(nodeId) {
  const counts = relationshipCountsFor(nodeId);
  return `${counts.outgoingCount} outgoing · ${counts.incomingCount} incoming · ${counts.connectedCount} connected`;
}
```

- [x] **Step 3: Add render function**

Add:

```javascript
function renderInspectionPreview(nodeId) {
  if (!inspectionPreview) return;
  const node = nodesById.get(nodeId);
  if (!node) {
    inspectionPreview.hidden = true;
    if (inspectionPreviewSelect) inspectionPreviewSelect.dataset.rayaGraphNode = "";
    if (inspectionPreviewOpen) inspectionPreviewOpen.removeAttribute("href");
    return;
  }
  if (inspectionPreviewTitle) {
    inspectionPreviewTitle.textContent = node.title || node.nav_title || node.id;
  }
  if (inspectionPreviewMeta) {
    inspectionPreviewMeta.textContent = inspectionPreviewTextFor(node);
  }
  if (inspectionPreviewSummary) {
    inspectionPreviewSummary.textContent = node.summary || "No summary available.";
  }
  if (inspectionPreviewCounts) {
    inspectionPreviewCounts.textContent = inspectionPreviewCountTextFor(node.id);
  }
  if (inspectionPreviewSelect) {
    inspectionPreviewSelect.dataset.rayaGraphNode = node.id;
  }
  if (inspectionPreviewOpen) {
    inspectionPreviewOpen.href = node.url || "#";
  }
  inspectionPreview.hidden = false;
}
```

- [x] **Step 4: Wire preview lifecycle**

In `inspectGraphNode`, after setting `hoverStatus.textContent`, call:

```javascript
renderInspectionPreview(inspectedId);
```

In every clear path inside `clearGraphInspection`, call `renderInspectionPreview(inspectedId)` when inspection remains active and `renderInspectionPreview("")` when inspection clears.

Add a click listener near the other control listeners:

```javascript
if (inspectionPreviewSelect) {
  inspectionPreviewSelect.addEventListener("click", () => {
    const nodeId = inspectionPreviewSelect.dataset.rayaGraphNode || "";
    if (nodeId) selectGraphNode(nodeId);
  });
}
```

- [x] **Step 5: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: PASS.

Actual focused result:

```text
..                                                                       [100%]
2 passed in 46.16s
```

Debug note: the graph e2e test keeps desktop hover coverage on the explicit SVG
hit target and uses the focus path on mobile, where touch-size viewports make
physical hover actionability an unstable proxy for the reader interaction. The
preview is placed below the SVG canvas so inspection updates do not shift the
graph under the pointer during click or double-click.

### Task 4: Review, Gates, Commit, Preview

**Files:**
- No additional production files expected.

- [x] **Step 1: Request independent review**

Ask a reviewer to inspect the diff for static-boundary regressions, focus/hover lifecycle bugs, accessibility issues, and tests that accidentally depend on generated artifacts.

Review found two Important issues and both were addressed:

- `render()` now clears `inspectedId` and hover status when the inspected node is no longer in the active graph.
- Graph click and double-click e2e coverage uses real pointer events against the rendered SVG node group instead of synthetic dispatched events.

- [x] **Step 2: Run render debug**

```bash
./scripts/check-render-debug.sh
```

Expected: PASS.

Actual result:

```text
render-debug-report: passed (129 check(s), report=/tmp/raya-render-debug.eA3Up9/index.html)
check-render-debug: passed
```

- [x] **Step 3: Run full gates sequentially**

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: both PASS.

Actual result:

```text
./scripts/check.sh: passed; pytest 479 passed in 516.99s
./scripts/check-docker.sh: passed; pytest 479 passed in 638.20s
```

- [ ] **Step 4: Commit and push**

```bash
git add docs/superpowers/specs/2026-06-25-graph-inspection-preview-design.md \
  docs/superpowers/plans/2026-06-25-graph-inspection-preview.md \
  packages/static/src/raya_static/builder.py \
  packages/static/src/raya_static/graph.py \
  packages/static/src/raya_static/rendering.py \
  tests/contracts/test_static_builder.py \
  tests/e2e/test_preview_static_read_path.py
git commit -m "Preview inspected graph pages"
git push origin new_rayalucaria
```

- [ ] **Step 5: Refresh local preview**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --host 127.0.0.1 --port 0
```

Expected: preview reports a local `http://127.0.0.1:<port>/index.html` entrypoint and `_raya/graph/index.html` includes the graph preview card.
