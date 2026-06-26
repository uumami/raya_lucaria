# Graph First-Viewport Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the Course Graph workspace and SVG canvas into the first desktop viewport without changing graph data or interactions.

**Architecture:** Add one Playwright layout regression against the render fixture graph workspace, then adjust generated static renderer CSS to reduce graph page vertical chrome. The graph remains local SVG with the existing generated payload and JavaScript behavior.

**Tech Stack:** Python 3.10, `uv`, Playwright, Glintstone static renderer CSS in `packages/static/src/raya_static/rendering.py`.

---

### Task 1: Add Failing Graph First-Viewport Regression

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write the failing test**

Add this test near the other graph workspace tests:

```python
def test_preview_graph_workspace_starts_in_first_desktop_viewport(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        assert handle.base_url is not None
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 950})
                try:
                    page.goto(
                        f"{handle.base_url}/_raya/graph/index.html",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(page)
                    probe = page.evaluate(
                        """() => {
                          const workspace = document.querySelector('.raya-graph-workspace');
                          const mapPanel = document.querySelector('.raya-graph-map-panel');
                          const canvas = document.querySelector('#raya-graph-canvas');
                          const toolbar = document.querySelector('.raya-graph-toolbar');
                          const instructions = document.querySelector('.raya-graph-instructions');
                          const box = (node) => {
                            const rect = node?.getBoundingClientRect();
                            return rect
                              ? { top: rect.top, bottom: rect.bottom, height: rect.height }
                              : null;
                          };
                          return {
                            workspace: box(workspace),
                            mapPanel: box(mapPanel),
                            canvas: box(canvas),
                            toolbar: box(toolbar),
                            instructions: box(instructions),
                            viewportHeight: window.innerHeight,
                            nodes: document.querySelectorAll('#raya-graph-canvas [data-raya-graph-node]').length,
                            edges: document.querySelectorAll('#raya-graph-canvas [data-raya-graph-edge]').length,
                            rootLayout: document.querySelector('[data-raya-graph-page]')
                              ?.getAttribute('data-raya-graph-layout'),
                          };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert probe["rootLayout"] == "connections"
    assert probe["nodes"] >= 6
    assert probe["edges"] >= 10
    assert probe["toolbar"]["height"] <= 125
    assert probe["instructions"]["height"] <= 36
    assert probe["workspace"]["top"] < 340
    assert probe["mapPanel"]["top"] < 360
    assert probe["canvas"]["top"] < 520
    assert probe["canvas"]["bottom"] <= probe["viewportHeight"] + 260
    assert probe["canvas"]["height"] >= 420
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_graph_workspace_starts_in_first_desktop_viewport -q
```

Expected: FAIL because current `canvas.top` is about `603`, and likely because toolbar/instructions/workspace vertical chrome exceeds the new contract.

### Task 2: Compact Graph Page Vertical Chrome

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Add graph-specific compact spacing**

In `packages/static/src/raya_static/rendering.py`, add graph-specific overrides after the shared graph/search/practice header and margin rules:

```css
.raya-graph-page {
  padding-top: 0.75rem;
}
.raya-graph-header {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 1rem;
  align-items: baseline;
  max-width: none;
}
.raya-graph-header h1 {
  margin: 0;
}
.raya-graph-header p {
  color: var(--raya-color-muted);
  flex: 1 1 24rem;
  font-size: 0.95rem;
  margin: 0;
}
.raya-graph-controls.raya-graph-toolbar,
.raya-graph-instructions {
  margin-bottom: 0.55rem;
}
.raya-graph-instructions {
  color: var(--raya-color-muted);
  font-size: 0.88rem;
  line-height: 1.35;
}
.raya-graph-workspace {
  margin-top: 0.55rem;
}
```

- [ ] **Step 2: Tighten toolbar and map-panel spacing**

In the existing graph CSS blocks, adjust only graph-specific values:

```css
.raya-graph-toolbar {
  gap: 0.5rem;
  padding: 0.5rem;
}
.raya-graph-toolbar-group {
  gap: 0.4rem;
  padding-right: 0.55rem;
}
.raya-graph-toolbar-label {
  font-size: 0.7rem;
}
.raya-graph-controls input,
.raya-graph-controls select,
.raya-graph-controls button,
.raya-graph-chip {
  min-height: 2.25rem;
  padding: 0.35rem 0.6rem;
}
.raya-graph-map-panel {
  padding: 0.75rem;
}
.raya-graph-status {
  margin-bottom: 0.45rem;
}
.raya-graph-orientation {
  margin-bottom: 0.5rem;
  padding: 0.4rem 0.55rem;
}
```

Keep the existing search/practice control sizing untouched unless a selector is shared; graph-specific selectors must override only graph controls.

- [ ] **Step 3: Run focused graph layout test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_graph_workspace_starts_in_first_desktop_viewport -q
```

Expected: PASS.

### Task 3: Run Existing Graph Behavior Checks

**Files:**
- No new files.

- [ ] **Step 1: Run primary graph static-read-path test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: PASS, preserving graph search, graph panels, previews, filters, focus behavior, no external requests, and no forbidden runtime behavior.

- [ ] **Step 2: Run responsive overlap/layout test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_rendered_surfaces_have_no_obvious_layout_overlap_at_viewports -q
```

Expected: PASS.

### Task 4: Review, Render Debug, Commit, Push

**Files:**
- Create: `docs/superpowers/specs/2026-06-26-graph-first-viewport-layout-design.md`
- Create: `docs/superpowers/plans/2026-06-26-graph-first-viewport-layout.md`
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Run render debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS with screenshots, no horizontal overflow, no raw TeX leakage, no external renderer requests, and static-site parity.

- [ ] **Step 2: Request independent code review**

Use `superpowers:requesting-code-review` and dispatch a focused reviewer on:

- graph first-viewport layout contract;
- CSS scope and selector safety;
- preservation of current graph behavior/static constraints.

- [ ] **Step 3: Restart/confirm local preview**

Run:

```bash
pkill -f "raya preview examples/courses/render-fixture --host 127.0.0.1 --port 46400" || true
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --host 127.0.0.1 --port 46400
```

Expected: preview serves `http://127.0.0.1:46400/index.html`.

- [ ] **Step 4: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-graph-first-viewport-layout-design.md docs/superpowers/plans/2026-06-26-graph-first-viewport-layout.md packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py
git commit -m "Bring graph workspace into first viewport"
git push origin new_rayalucaria
```
