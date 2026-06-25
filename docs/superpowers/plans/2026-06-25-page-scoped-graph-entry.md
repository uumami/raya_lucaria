# Page-Scoped Graph Entry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make graph links from reader pages land on a framed selected-page neighborhood instead of an unframed full-course graph.

**Architecture:** Reuse the existing URL `page` parameter, selected-page detail state, and `selectedNeighborhoodBounds()`/`setGraphViewBox()` helpers in the local graph script. Add a small page-focus readout in the graph state panel and e2e tests that verify viewport behavior.

**Tech Stack:** Python 3.10 static builder, local vanilla JS graph resource, pytest/Playwright e2e tests.

---

### Task 1: Add Failing Page-Scoped Entry Tests

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Extend page-query graph test**

In the existing graph page-query test around `/_raya/graph/index.html?page=authoring-matrix`, capture the full graph viewBox from a plain graph load, then load the page-scoped URL and assert:

```python
plain_viewbox = page.locator("#raya-graph-canvas").get_attribute("viewBox")
page.goto(f"{base_url}/_raya/graph/index.html?page=authoring-matrix", wait_until="networkidle")
page.wait_for_function(
    """() => document.querySelector('[data-raya-graph-state-selected]')
      ?.textContent?.includes('authoring-matrix')"""
)
page_scoped_viewbox = page.locator("#raya-graph-canvas").get_attribute("viewBox")
assert _viewbox_width(page_scoped_viewbox) < _viewbox_width(plain_viewbox)
assert page.locator("#graph-fit-selection").is_enabled()
context = _visible_graph_context(page, "authoring-matrix", viewport)
assert context["selectedVisible"]
assert context["activeEdgeVisible"]
assert (
    page.locator("[data-raya-graph-state-page-focus]").inner_text()
    == "authoring-matrix"
)
```

- [x] **Step 2: Assert reset behavior**

After clicking `#graph-reset-view`, assert the full viewBox returns while selected page details remain. After clicking `#graph-reset`, assert page focus readout is `none` and detail panel is empty.

- [x] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: FAIL because page-scoped entry still uses the full graph viewBox and has no `data-raya-graph-state-page-focus` readout.

### Task 2: Add Page-Focus Readout Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Add graph state row**

In the graph state `<dl>`, add:

```html
<div><dt>Page focus</dt><dd data-raya-graph-state-page-focus>none</dd></div>
```

- [x] **Step 2: Add contract assertion**

Assert graph HTML includes `data-raya-graph-state-page-focus`.

### Task 3: Auto-Fit Initial Page Focus

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`

- [x] **Step 1: Track initial page focus**

Add:

```javascript
let pageFocusId = "";
let pendingInitialPageFit = false;
```

When parsing URL state, if `page=<id>` is valid, set `selectedId`, `pageFocusId`, and `pendingInitialPageFit = true`.

- [x] **Step 2: Update state readout**

Capture `[data-raya-graph-state-page-focus]` and update it to `pageFocusId || "none"`.

- [x] **Step 3: Fit after first graph render**

After `latestRenderedPositions` and `latestRenderedEdges` are set in `render()`, if `pendingInitialPageFit` is true, selected page exists, and layout is not `list`, call `selectedNeighborhoodBounds()` and `setGraphViewBox(box)` if a box is available. Clear `pendingInitialPageFit` afterward.

- [x] **Step 4: Clear page focus on manual selection/reset**

Manual node selection and reset graph should set `pageFocusId = ""`. Reset view should not clear it.

- [x] **Step 5: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: PASS.

### Task 4: Review and Gates

**Files:**
- No additional production files expected.

- [x] **Step 1: Request independent review**

Ask a reviewer to check static boundaries, URL-state behavior, reset behavior, and test coverage.

- [x] **Step 2: Run render debug**

```bash
./scripts/check-render-debug.sh
```

Expected: PASS.

- [x] **Step 3: Run full gates sequentially**

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: PASS.

- [x] **Step 4: Commit, push, preview**

Commit with:

```bash
git add packages/static/src/raya_static/builder.py packages/static/src/raya_static/graph.py tests/e2e/test_preview_static_read_path.py tests/contracts/test_static_builder.py docs/superpowers/specs/2026-06-25-page-scoped-graph-entry-design.md docs/superpowers/plans/2026-06-25-page-scoped-graph-entry.md
git commit -m "Focus graph entry on selected page"
git push origin new_rayalucaria
```

Start a fresh preview and report the URL.
