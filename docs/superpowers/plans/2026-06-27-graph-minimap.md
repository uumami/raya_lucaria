# Graph Minimap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive minimap to the static Graph workspace that shows current graph extent and viewport position.

**Architecture:** Reuse the existing static SVG graph state. Add generated minimap markup in `builder.py`, style it in `rendering.py`, and update it from `graph.py` whenever the main graph render or viewBox changes.

**Tech Stack:** Python static builder, local JavaScript resource string, SVG, CSS, pytest, Playwright.

---

### Task 1: Browser RED Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add failing e2e test**

Add a test near the graph viewport tests:

```python
def test_render_fixture_graph_minimap_tracks_viewport(tmp_path: Path) -> None:
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
                requested_urls: list[str] = []
                page.on("request", lambda request: requested_urls.append(request.url))
                try:
                    page.goto(
                        f"{handle.base_url}/_raya/graph/index.html?page=reader-ux",
                        wait_until="networkidle",
                    )
                    page.wait_for_selector(
                        '#raya-graph-canvas [data-raya-graph-node="reader-ux"] '
                        ".raya-graph-node.is-selected"
                    )
                    page.wait_for_selector(
                        "#raya-graph-minimap [data-raya-graph-minimap-node]"
                    )
                    before = page.evaluate(
                        """() => {
                          const minimap = document.querySelector('#raya-graph-minimap');
                          const selected = document.querySelector(
                            '#raya-graph-canvas [data-raya-graph-node="reader-ux"] '
                            + '.raya-graph-node-link .raya-graph-node.is-selected'
                          );
                          const viewport = minimap?.querySelector(
                            '[data-raya-graph-minimap-viewport]'
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
                            minimap: box(minimap),
                            viewport: box(viewport),
                            viewBox: minimap?.getAttribute('viewBox'),
                            nodes: minimap?.querySelectorAll(
                              '[data-raya-graph-minimap-node]'
                            ).length,
                            edges: minimap?.querySelectorAll(
                              '[data-raya-graph-minimap-edge]'
                            ).length,
                            selected: Boolean(selected),
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
                    requested_urls.clear()
                    page.click("#graph-zoom-in")
                    page.click('[data-raya-graph-pan="right"]')
                    page.wait_for_function(
                        """(beforeX) => {
                          const viewport = document.querySelector(
                            '#raya-graph-minimap [data-raya-graph-minimap-viewport]'
                          );
                          if (!viewport) return false;
                          const x = Number(viewport.getAttribute('x') || '0');
                          return Math.abs(x - beforeX) > 0.01;
                        }""",
                        before["viewport"]["x"],
                    )
                    after = page.evaluate(
                        """() => {
                          const selected = document.querySelector(
                            '#raya-graph-canvas [data-raya-graph-node="reader-ux"] '
                            + '.raya-graph-node-link .raya-graph-node.is-selected'
                          );
                          const viewport = document.querySelector(
                            '#raya-graph-minimap [data-raya-graph-minimap-viewport]'
                          );
                          const rect = viewport.getBoundingClientRect();
                          return {
                            viewport: {
                              x: rect.x,
                              y: rect.y,
                              width: rect.width,
                              height: rect.height,
                            },
                            selected: Boolean(selected),
                            storage: [
                              Object.keys(localStorage),
                              Object.keys(sessionStorage),
                            ],
                          };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert before["minimap"]["width"] >= 120
    assert before["minimap"]["height"] >= 80
    assert before["viewBox"]
    assert before["nodes"] >= 3
    assert before["edges"] >= 1
    assert before["viewport"]["width"] > 0
    assert before["viewport"]["height"] > 0
    assert before["selected"] is True
    assert after["selected"] is True
    assert after["viewport"] != before["viewport"]
    assert before["storage"] == [[], []]
    assert after["storage"] == [[], []]
    assert before["overflow"] <= 1
    assert all(url.startswith(f"{base_url}/") for url in requested_urls)
```

- [x] **Step 2: Run RED test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_minimap_tracks_viewport
```

Expected: FAIL because `#raya-graph-minimap` does not exist.

### Task 2: Contract RED Test

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Add contract assertions**

In the graph resource/static builder tests, assert:

```python
assert 'id="raya-graph-minimap"' in graph_html
assert "data-raya-graph-minimap-viewport" in graph_html
assert "data-raya-graph-minimap-node" in graph_js
assert "data-raya-graph-minimap-edge" in graph_js
assert "fetch(" not in graph_js
assert "XMLHttpRequest" not in graph_js
assert "localStorage" not in graph_js
assert "sessionStorage" not in graph_js
assert "cytoscape" not in graph_html.lower()
```

- [x] **Step 2: Run RED contract test**

Run the focused contract test that owns graph HTML/resources.

Expected: FAIL on missing minimap HTML/JS markers.

### Task 3: Generated Markup and CSS

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Add minimap markup**

In `_render_graph_surface`, add this block after the main graph canvas:

```python
(
    '<aside class="raya-graph-minimap-panel" aria-label="Graph overview">'
    '<h2>Overview</h2>'
    '<svg id="raya-graph-minimap" class="raya-graph-minimap" '
    'role="img" aria-label="Graph overview and current viewport" '
    'focusable="false"></svg>'
    '<p class="raya-graph-minimap-caption">'
    'The rectangle shows the visible canvas area.'
    '</p>'
    '</aside>'
),
```

- [x] **Step 2: Add minimap CSS**

Add CSS near graph canvas styles:

```css
.raya-graph-minimap-panel {
  align-items: start;
  display: grid;
  gap: 0.28rem;
  grid-template-columns: minmax(0, 1fr) auto;
  margin: 0.55rem 0 0;
}
.raya-graph-minimap-panel h2 {
  color: var(--raya-color-heading);
  font-size: 0.76rem;
  line-height: 1.2;
  margin: 0;
}
.raya-graph-minimap {
  background: color-mix(in srgb, var(--raya-color-surface) 92%, var(--raya-color-accent-soft));
  border: 1px solid var(--raya-color-border);
  border-radius: 0.35rem;
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--raya-color-surface) 70%, white);
  display: block;
  height: 6.5rem;
  max-width: min(13.5rem, 100%);
  width: 13.5rem;
}
.raya-graph-minimap-caption {
  color: var(--raya-color-muted);
  font-size: 0.72rem;
  grid-column: 1 / -1;
  line-height: 1.25;
  margin: 0;
}
.raya-graph-minimap-edge {
  stroke: color-mix(in srgb, var(--raya-color-muted) 55%, transparent);
  stroke-width: 1.2;
}
.raya-graph-minimap-node {
  fill: var(--raya-graph-node-color, var(--raya-color-accent));
  opacity: 0.72;
}
.raya-graph-minimap-viewport {
  fill: color-mix(in srgb, var(--raya-color-accent) 13%, transparent);
  stroke: var(--raya-color-accent);
  stroke-width: 2;
}
@media (max-width: 900px) {
  .raya-graph-minimap-panel {
    grid-template-columns: minmax(0, 1fr);
  }
  .raya-graph-minimap {
    width: min(100%, 15rem);
  }
}
@media print {
  .raya-graph-minimap-panel {
    display: none !important;
  }
}
```

### Task 4: Minimap Rendering

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`

- [x] **Step 1: Add minimap DOM references**

Near existing top-level DOM constants:

```javascript
const minimap = document.getElementById("raya-graph-minimap");
```

- [x] **Step 2: Add minimap renderer**

Add helpers near `setGraphViewBox`:

```javascript
function clearMinimap() {
  if (minimap) minimap.replaceChildren();
}

function minimapPoint(point) {
  if (!fullViewBox) return { x: 0, y: 0 };
  const width = 216;
  const height = 104;
  const x = ((point.x - fullViewBox.x) / fullViewBox.width) * width;
  const y = ((point.y - fullViewBox.y) / fullViewBox.height) * height;
  return { x, y };
}

function renderGraphMinimap(activeNodes, activeEdges) {
  if (!minimap || !fullViewBox || !graphViewBox) return;
  const width = 216;
  const height = 104;
  minimap.setAttribute("viewBox", `0 0 ${width} ${height}`);
  minimap.replaceChildren();
  activeEdges.forEach((edge) => {
    const from = latestRenderedPositions.get(edge.from);
    const to = latestRenderedPositions.get(edge.to);
    if (!from || !to) return;
    const start = minimapPoint(from);
    const end = minimapPoint(to);
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("class", "raya-graph-minimap-edge");
    line.setAttribute("data-raya-graph-minimap-edge", "");
    line.setAttribute("x1", String(start.x));
    line.setAttribute("y1", String(start.y));
    line.setAttribute("x2", String(end.x));
    line.setAttribute("y2", String(end.y));
    minimap.appendChild(line);
  });
  activeNodes.forEach((node) => {
    const point = latestRenderedPositions.get(node.id);
    if (!point) return;
    const mapped = minimapPoint(point);
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("class", "raya-graph-minimap-node");
    circle.setAttribute("data-raya-graph-minimap-node", node.id);
    circle.setAttribute("cx", String(mapped.x));
    circle.setAttribute("cy", String(mapped.y));
    circle.setAttribute("r", node.id === selectedId ? "3.4" : "2.4");
    circle.style.setProperty("--raya-graph-node-color", groupColorFor(node.group || ""));
    minimap.appendChild(circle);
  });
  const viewport = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  const topLeft = minimapPoint({ x: graphViewBox.x, y: graphViewBox.y });
  const bottomRight = minimapPoint({
    x: graphViewBox.x + graphViewBox.width,
    y: graphViewBox.y + graphViewBox.height,
  });
  viewport.setAttribute("class", "raya-graph-minimap-viewport");
  viewport.setAttribute("data-raya-graph-minimap-viewport", "");
  viewport.setAttribute("x", String(Math.min(topLeft.x, bottomRight.x)));
  viewport.setAttribute("y", String(Math.min(topLeft.y, bottomRight.y)));
  viewport.setAttribute("width", String(Math.abs(bottomRight.x - topLeft.x)));
  viewport.setAttribute("height", String(Math.abs(bottomRight.y - topLeft.y)));
  minimap.appendChild(viewport);
}
```

- [x] **Step 3: Call minimap renderer from `render()`**

After `latestRenderedPositions` and `latestRenderedEdges` are updated and the main canvas has been drawn, call:

```javascript
renderGraphMinimap(activeNodes, activeEdges);
```

When list layout or empty graph hides the canvas, call:

```javascript
clearMinimap();
```

### Task 5: Verification, Review, Commit, Push

**Files:**
- No additional source files expected.

- [x] **Step 1: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_minimap_tracks_viewport tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_focus_mode_refits_selected_context
```

Expected: PASS.

- [x] **Step 2: Run contract tests**

Run the focused static builder/graph resource contract tests changed in Task 2.

Expected: PASS.

- [x] **Step 3: Run render-debug**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS.

- [x] **Step 4: Request independent review**

Ask a reviewer to inspect static-only behavior, no storage/no fetch/no external dependency, viewport synchronization, and accessibility/print behavior.

- [x] **Step 5: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-27-graph-minimap-design.md docs/superpowers/plans/2026-06-27-graph-minimap.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py packages/static/src/raya_static/graph.py tests/e2e/test_preview_static_read_path.py tests/contracts/test_static_builder.py
git commit -m "Add graph minimap overview"
git push origin new_rayalucaria
```
