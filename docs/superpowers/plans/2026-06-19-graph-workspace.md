# Graph Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Upgrade the static local graph page into a more useful graph workspace with fuzzy search, selected-page details, and an expanded view.

**Architecture:** Keep the graph page as manifest-derived static HTML plus local vanilla JavaScript. Add markup in `builder.py`, behavior in `graph.py`, visual rules in `rendering.py`, and coverage in contract/e2e tests. Do not add external graph engines or persistent graph state.

**Tech Stack:** Python 3.10 static builder, local SVG, local vanilla JavaScript, pytest, Playwright.

---

### Task 1: Contract Tests For Graph Workspace Markup

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Add failing graph surface assertions**

In `test_build_writes_local_visual_graph_surface`, add assertions:

```python
assert "graph-expand" in graph_html
assert "raya-graph-detail" in graph_html
assert "data-raya-graph-detail-empty" in graph_html
assert "data-raya-graph-detail-panel" in graph_html
assert "data-raya-graph-detail-title" in graph_html
assert "data-raya-graph-detail-outgoing" in graph_html
assert "data-raya-graph-detail-incoming" in graph_html
assert "data-raya-graph-detail-clear" in graph_html
assert "levenshtein" in graph_script
assert "selectGraphNode" in graph_script
assert "data-raya-graph-expanded" in graph_script
assert "fetch(" not in graph_script
assert "XMLHttpRequest" not in graph_script
assert "localStorage" not in graph_script
assert "sessionStorage" not in graph_script
```

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: FAIL because detail and expand controls are not rendered yet.

### Task 2: Browser Test For Graph Interactions

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Extend the graph Playwright test**

In `test_preview_serves_local_visual_graph_surface`, after the existing search
checks, add behavior checks:

```python
page.fill("#graph-search", "matrx")
page.wait_for_function(
    """() => document
      .querySelector('#graph-status')
      ?.textContent
      ?.includes('visible node')"""
)
assert "matrix" in page.locator("#raya-graph-list").inner_text().lower()

page.locator("#raya-graph-canvas [data-raya-graph-node]").first.click()
assert page.locator("[data-raya-graph-detail-panel]").is_visible()
assert page.locator("[data-raya-graph-detail-title]").inner_text().strip()
assert page.locator("[data-raya-graph-detail-link]").get_attribute("href")

before_height = page.locator("#raya-graph-canvas").bounding_box()["height"]
page.click("#graph-expand")
assert page.locator("[data-raya-graph-page]").get_attribute("data-raya-graph-expanded") == "true"
after_height = page.locator("#raya-graph-canvas").bounding_box()["height"]
assert after_height >= before_height

page.click("[data-raya-graph-detail-clear]")
assert page.locator("[data-raya-graph-detail-empty]").is_visible()

page.click("#graph-reset")
assert page.locator("[data-raya-graph-page]").get_attribute("data-raya-graph-expanded") == "false"
assert page.locator("[data-raya-graph-detail-empty]").is_visible()
```

Keep the existing `requested_urls` tracking or add it so graph interactions prove
they make no network requests after page load.

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: FAIL because graph detail and expand behavior do not exist.

### Task 3: Graph Surface Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [x] **Step 1: Add the expand control**

In `_render_graph_surface`, render after `graph-reset`:

```html
<button id="graph-expand" type="button" aria-pressed="false">Expand graph</button>
```

- [x] **Step 2: Add the detail panel**

Render the detail section after graph status and before the SVG:

```html
<section class="raya-graph-detail" aria-label="Selected page" data-raya-graph-detail>
  <p data-raya-graph-detail-empty>Select a page in the graph or list.</p>
  <div data-raya-graph-detail-panel hidden>
    <div class="raya-graph-detail-header">
      <h2 data-raya-graph-detail-title>Selected page</h2>
      <button type="button" data-raya-graph-detail-clear>Clear</button>
    </div>
    <p class="raya-graph-detail-meta" data-raya-graph-detail-meta></p>
    <p><a data-raya-graph-detail-link href="../../index.html">Open page</a></p>
    <div class="raya-graph-detail-links">
      <section>
        <h3>Links from this page</h3>
        <ul data-raya-graph-detail-outgoing></ul>
      </section>
      <section>
        <h3>Links to this page</h3>
        <ul data-raya-graph-detail-incoming></ul>
      </section>
    </div>
  </div>
</section>
```

- [x] **Step 3: Run the contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: still FAIL until JavaScript tokens are added.

### Task 4: Graph JavaScript Behavior

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`

- [x] **Step 1: Add fuzzy matching**

Add local `levenshtein(a, b)` and `fuzzyMatch(query, target)` helpers. Use fuzzy
matching in `matchesNode(node)` over title, nav title, ID, status, group title,
and hierarchy label.

- [x] **Step 2: Add selected detail behavior**

Add DOM references for the detail panel. Implement:

```javascript
function selectGraphNode(nodeId) { ... }
function clearGraphSelection() { ... }
function renderDetail() { ... }
```

Use graph edges and backlinks from the embedded payload. Selection updates the
panel and re-renders node/edge emphasis. SVG node click should select the node,
not navigate. Detail and list links remain normal navigation links.

- [x] **Step 3: Add expanded mode**

Add `graphExpand` DOM reference and `setGraphExpanded(nextExpanded)`. It should
set `root.dataset.rayaGraphExpanded` to `"true"` or `"false"`, update
`aria-pressed`, and switch button text between `Expand graph` and `Compact graph`.
Reset sets expanded mode to false.

- [x] **Step 4: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: fails only on CSS/visibility if CSS is not finished.

### Task 5: Graph CSS And Docs

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] **Step 1: Add graph detail and expanded workspace CSS**

Style `.raya-graph-detail`, `.raya-graph-detail-header`,
`.raya-graph-detail-links`, `[data-raya-graph-expanded="true"]`, active graph
nodes, and active list rows. Expanded mode should increase graph canvas height on
desktop without causing horizontal overflow.

- [x] **Step 2: Document graph behavior**

Document that graph search/detail is generated course structure from artifact
data, local-only, non-persistent, and not personal progress or recommendations.

- [x] **Step 3: Verify focused and visual gates**

Run:

```bash
git diff --check
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
./scripts/check-render-debug.sh
```

Expected: PASS.

### Task 6: Review, Final Gate, Commit, Push, Preview

**Files:**
- All files modified above.

- [x] **Step 1: Request code review**

Use `superpowers:requesting-code-review` on the uncommitted diff. Fix Critical
and Important issues.

- Review fixes applied: list links keep normal navigation, hover/focus no longer
  create sticky selection, expanded mode cannot shrink below the default canvas
  height, filter/search changes clear hidden selections, and browser coverage now
  includes detail-link navigation plus SVG double-click navigation.

- [x] **Step 2: Run final verification**

Run:

```bash
./scripts/check.sh
```

Expected: PASS.

- [x] **Step 3: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-19-graph-workspace-design.md docs/superpowers/plans/2026-06-19-graph-workspace.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/graph.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/en/professors/index.md docs/guides/en/contributors/index.md docs/guides/en/agents/index.md docs/guides/es/estudiantes/index.md docs/guides/es/profesores/index.md docs/guides/es/colaboradores/index.md docs/guides/es/agentes/index.md
git commit -m "Improve graph workspace"
git push origin new_rayalucaria
```

- [x] **Step 4: Start preview**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --port 0
```

Report the local URL.
