# Graph Focus Fit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Graph Focus mode expand the canvas into a viewport-dominant focused workspace and refit selected graph context after expansion.

**Architecture:** Keep the current static SVG graph and volatile panel state. Update focused-mode CSS for canvas height and schedule the existing `fitSelectedGraphContext()` after entering focus mode.

**Tech Stack:** Python static builder resources, generated CSS/JavaScript, pytest, Playwright.

---

### Task 1: Failing Browser Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add failing e2e test**

Add a focused test near the existing Graph Focus tests:

```python
def test_render_fixture_graph_focus_mode_refits_selected_context(
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
                        f"{handle.base_url}/_raya/graph/index.html?page=reader-ux",
                        wait_until="networkidle",
                    )
                    page.wait_for_selector(
                        '#raya-graph-canvas [data-raya-graph-node="reader-ux"] '
                        ".raya-graph-node.is-selected"
                    )
                    before = page.locator("#raya-graph-canvas").bounding_box()
                    assert before is not None
                    page.click("#graph-expand")
                    page.wait_for_function(
                        """() => document
                          .querySelector('[data-raya-graph-page]')
                          ?.getAttribute('data-raya-graph-expanded') === 'true'"""
                    )
                    page.wait_for_function(
                        """() => {
                          const canvas = document.querySelector('#raya-graph-canvas');
                          if (!canvas) return false;
                          const rect = canvas.getBoundingClientRect();
                          return rect.height >= window.innerHeight * 0.8;
                        }"""
                    )
                    probe = page.evaluate(
                        """() => {
                          const canvas = document.querySelector('#raya-graph-canvas');
                          const selected = document.querySelector(
                            '#raya-graph-canvas [data-raya-graph-node="reader-ux"] g'
                          );
                          const edges = Array.from(
                            document.querySelectorAll('#raya-graph-canvas .raya-graph-edge')
                          );
                          const box = (node) => {
                            const rect = node.getBoundingClientRect();
                            return {
                              x: rect.x,
                              y: rect.y,
                              width: rect.width,
                              height: rect.height,
                            };
                          };
                          return {
                            canvas: box(canvas),
                            selected: selected ? box(selected) : null,
                            connectedEdges: edges
                              .filter((edge) => {
                                const from = edge.getAttribute('data-raya-graph-from') || '';
                                const to = edge.getAttribute('data-raya-graph-to') || '';
                                return from === 'reader-ux' || to === 'reader-ux';
                              })
                              .map(box),
                            viewport: {
                              x: 0,
                              y: 0,
                              width: window.innerWidth,
                              height: window.innerHeight,
                            },
                            rootExpanded: document
                              .querySelector('[data-raya-graph-page]')
                              ?.getAttribute('data-raya-graph-expanded'),
                            listState: document
                              .querySelector('[data-raya-graph-page]')
                              ?.getAttribute('data-raya-graph-list-state'),
                            inspectorState: document
                              .querySelector('[data-raya-graph-page]')
                              ?.getAttribute('data-raya-graph-inspector-state'),
                            storage: [
                              Object.keys(localStorage),
                              Object.keys(sessionStorage),
                            ],
                            overflow: Math.ceil(
                              document.documentElement.scrollWidth - window.innerWidth
                            ),
                          };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    visible_canvas = _intersection_box(probe["canvas"], probe["viewport"])
    assert probe["rootExpanded"] == "true"
    assert probe["listState"] == "collapsed"
    assert probe["inspectorState"] == "collapsed"
    assert probe["canvas"]["height"] >= probe["viewport"]["height"] * 0.8
    assert visible_canvas["height"] > probe["viewport"]["height"] * 0.45
    assert probe["selected"] is not None
    assert _boxes_intersect(visible_canvas, probe["selected"])
    assert any(
        _boxes_intersect(visible_canvas, edge) for edge in probe["connectedEdges"]
    )
    assert probe["storage"] == [[], []]
    assert probe["overflow"] <= 1
```

- [x] **Step 2: Run RED test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_focus_mode_refits_selected_context
```

Expected: FAIL because focused canvas height remains below 80% of the desktop viewport.

### Task 2: Focused Canvas Height

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Increase focused canvas height**

Change:

```css
[data-raya-graph-expanded="true"] .raya-graph-canvas {
  height: clamp(34rem, 72vh, 48rem);
}
```

to:

```css
[data-raya-graph-expanded="true"] .raya-graph-canvas {
  height: clamp(42rem, 84vh, 64rem);
}
```

### Task 3: Post-Expansion Refit

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`

- [x] **Step 1: Schedule a selected-context fit after focus expansion**

Add this helper near `fitSelectedGraphContext()`:

```javascript
function refitGraphFocusContext() {
  if (!selectedId || root.dataset.rayaGraphExpanded !== "true") return;
  window.requestAnimationFrame(() => {
    window.requestAnimationFrame(() => {
      if (!selectedId || root.dataset.rayaGraphExpanded !== "true") return;
      fitSelectedGraphContext();
      render();
    });
  });
}
```

In the `#graph-expand` click handler, after `render();`, add:

```javascript
if (nextExpanded) {
  refitGraphFocusContext();
}
```

- [x] **Step 2: Run GREEN test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_focus_mode_refits_selected_context
```

Expected: PASS.

### Task 4: Verification, Review, Commit, Push

**Files:**
- No additional source files expected.

- [x] **Step 1: Run focused graph tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_focus_mode_refits_selected_context tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_url_state_and_debug_readout
```

Expected: PASS.

- [x] **Step 2: Run render-debug**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS.

- [x] **Step 3: Request independent review**

Ask a reviewer to inspect focused graph mode for static-only behavior, accessibility/state regressions, no storage writes, no external requests, and test coverage.

- [x] **Step 4: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-27-graph-focus-fit-design.md docs/superpowers/plans/2026-06-27-graph-focus-fit.md packages/static/src/raya_static/rendering.py packages/static/src/raya_static/graph.py tests/e2e/test_preview_static_read_path.py
git commit -m "Refit graph focus mode"
git push origin new_rayalucaria
```
