# Graph Fit Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a static SVG graph `Fit selection` viewport command that frames the selected page and its visible direct graph context.

**Architecture:** Keep current graph data and layouts unchanged. Add one toolbar button, store the latest rendered graph geometry in the local graph script, compute padded selected-neighborhood bounds from that geometry, and set only the SVG `viewBox`. Preserve global `Fit`, `Reset view`, URL state, selection, search, filters, and no-storage/no-fetch constraints.

**Tech Stack:** Python 3.10 static builder, generated HTML/CSS/JavaScript, pytest, Playwright.

---

## File Structure

- `packages/static/src/raya_static/builder.py`
  - Add the `graph-fit-selection` toolbar button.
  - Update graph help copy to describe selected fitting as viewport-only.
- `packages/static/src/raya_static/graph.py`
  - Wire the new button.
  - Store latest rendered positions and active graph edges.
  - Add selected-neighborhood viewBox helpers and disabled-state updates.
  - Preserve global `Fit`, pan, zoom, reset, list layout, URL state, and selected details.
- `tests/contracts/test_static_builder.py`
  - Add contract assertions for generated control/help/script tokens and forbidden runtime behavior.
- `tests/e2e/test_preview_static_read_path.py`
  - Add browser assertions for disabled/enabled states, selected viewport fitting, preserved state, list layout disabled state, and global fit regression.
- `docs/foundation/20_learning_renderer_contract.md`
  - Document `Fit selection` as current graph viewport behavior.
- `docs/guides/en/agents/index.md`
  - Add English graph debugging guidance for selected-fit verification.
- `docs/guides/es/agentes/index.md`
  - Add Spanish graph debugging guidance for selected-fit verification.

---

### Task 1: Contract Tests For Fit Selection

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add failing graph HTML and script assertions**

In `test_build_writes_local_visual_graph_surface`, near the existing viewport
toolbar assertions, add:

```python
    assert "graph-fit-selection" in graph_html
    assert (
        '<button id="graph-fit-selection" type="button" disabled>'
        "Fit selection</button>"
    ) in graph_html
    assert "Fit selection frames the selected page" in graph_html
    assert "Fit selection changes only the SVG viewport" in graph_html
```

Near the graph script token assertions, add:

```python
    assert "fitSelection" in graph_script
    assert "selectedNeighborhoodBounds" in graph_script
    assert "setFitSelectionEnabled" in graph_script
    assert "latestRenderedPositions" in graph_script
    assert "latestRenderedEdges" in graph_script
```

- [ ] **Step 2: Run contract test to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: fails because `graph-fit-selection` and the selected-fit helper
symbols do not exist yet.

### Task 2: Browser Tests For Selected Viewport Fitting

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add helper for visible selected graph context**

Near existing graph/viewBox helpers, add:

```python
def _visible_graph_context(page, node_id: str, viewport: dict[str, int]) -> dict:
    return page.evaluate(
        """({ nodeId, viewport }) => {
          const canvas = document.querySelector('#raya-graph-canvas');
          const selected = document.querySelector(
            `#raya-graph-canvas [data-raya-graph-node="${nodeId}"] g`
          );
          const canvasBox = canvas.getBoundingClientRect();
          const selectedBox = selected.getBoundingClientRect();
          const visible = {
            x: Math.max(canvasBox.x, 0),
            y: Math.max(canvasBox.y, 0),
            right: Math.min(canvasBox.right, viewport.width),
            bottom: Math.min(canvasBox.bottom, viewport.height),
          };
          visible.width = Math.max(0, visible.right - visible.x);
          visible.height = Math.max(0, visible.bottom - visible.y);
          const intersects = (box) => !(
            box.right < visible.x ||
            box.x > visible.right ||
            box.bottom < visible.y ||
            box.y > visible.bottom
          );
          const edgeVisible = Array.from(
            document.querySelectorAll('#raya-graph-canvas .raya-graph-edge.is-active')
          ).some((edge) => intersects(edge.getBoundingClientRect()));
          return {
            canvas: {
              x: canvasBox.x,
              y: canvasBox.y,
              width: canvasBox.width,
              height: canvasBox.height,
            },
            visible,
            selected: {
              x: selectedBox.x,
              y: selectedBox.y,
              width: selectedBox.width,
              height: selectedBox.height,
            },
            selectedVisible: intersects(selectedBox),
            activeEdgeVisible: edgeVisible,
          };
        }""",
        {"nodeId": node_id, "viewport": viewport},
    )
```

- [ ] **Step 2: Add selected-fit browser assertions**

Inside `test_preview_serves_local_visual_graph_surface`, in the existing
desktop/mobile viewport loop after the generic graph click and viewport control
assertions, select the `authoring-matrix` fixture node and add:

```python
                        page.locator(
                            '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
                        ).click()
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-state-selected]')
                              ?.textContent
                              ?.includes('authoring-matrix')"""
                        )
                        initial_viewbox = page.locator(
                            "#raya-graph-canvas"
                        ).get_attribute("viewBox")
                        fit_selection = page.locator("#graph-fit-selection")
                        assert fit_selection.is_enabled()
                        page.click("#graph-zoom-in")
                        page.click('[data-raya-graph-pan="right"]')
                        drifted_viewbox = page.locator(
                            "#raya-graph-canvas"
                        ).get_attribute("viewBox")
                        fit_selection.click()
                        fitted_viewbox = page.locator(
                            "#raya-graph-canvas"
                        ).get_attribute("viewBox")
                        assert fitted_viewbox != initial_viewbox
                        assert fitted_viewbox != drifted_viewbox
                        assert _viewbox_width(fitted_viewbox) < _viewbox_width(
                            initial_viewbox
                        )
                        context = _visible_graph_context(
                            page, "authoring-matrix", viewport
                        )
                        assert context["selectedVisible"]
                        assert context["activeEdgeVisible"]
                        assert page.input_value("#graph-search") == ""
                        assert page.locator(
                            "[data-raya-graph-detail-panel]"
                        ).is_visible()
                        page.click("#graph-fit")
                        assert (
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                            == initial_viewbox
                        )
```

- [ ] **Step 3: Add no-selection and list-layout disabled assertions**

In the same browser flow, before the first graph selection, add:

```python
                        assert page.locator("#graph-fit-selection").is_disabled()
```

After the existing list-layout assertions where `#graph-zoom-in` and
`#graph-reset-view` are disabled, add:

```python
                        assert page.locator("#graph-fit-selection").is_disabled()
```

- [ ] **Step 4: Run browser test to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: fails because the selected-fit button does not exist yet.

### Task 3: Implement Fit Selection

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/graph.py`

- [ ] **Step 1: Add generated button markup**

In `_render_static_graph_page()`, inside the viewport toolbar group after the
global `Fit` button, add:

```python
            '<button id="graph-fit-selection" type="button" disabled>'
            "Fit selection</button>",
```

Update the graph help copy after the current global Fit paragraph:

```python
            (
                "<p>Fit selection frames the selected page and visible directly "
                "connected graph context. Fit selection changes only the SVG "
                "viewport; it does not change filters, selection, graph data, "
                "or learner state.</p>"
            ),
```

- [ ] **Step 2: Wire script state and control lookup**

In `packages/static/src/raya_static/graph.py`, after:

```javascript
  const fit = document.getElementById("graph-fit");
```

add:

```javascript
  const fitSelection = document.getElementById("graph-fit-selection");
```

After:

```javascript
  let lastActiveEdges = [];
```

add:

```javascript
  let latestRenderedPositions = new Map();
  let latestRenderedEdges = [];
```

- [ ] **Step 3: Add selected-neighborhood bounds helpers**

After `resetGraphView()`, add:

```javascript
  function paddedGraphBounds(points, padding) {
    if (!points.length || !fullViewBox) return null;
    const xs = points.map((point) => point.x);
    const ys = points.map((point) => point.y);
    const minX = Math.min(...xs) - padding;
    const maxX = Math.max(...xs) + padding;
    const minY = Math.min(...ys) - padding;
    const maxY = Math.max(...ys) + padding;
    const width = Math.max(120, maxX - minX);
    const height = Math.max(96, maxY - minY);
    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;
    const nextWidth = Math.min(fullViewBox.width, width);
    const nextHeight = Math.min(fullViewBox.height, height);
    const x = Math.max(
      fullViewBox.x,
      Math.min(fullViewBox.x + fullViewBox.width - nextWidth, centerX - nextWidth / 2)
    );
    const y = Math.max(
      fullViewBox.y,
      Math.min(fullViewBox.y + fullViewBox.height - nextHeight, centerY - nextHeight / 2)
    );
    return { x, y, width: nextWidth, height: nextHeight };
  }

  function selectedNeighborhoodBounds() {
    if (!selectedId || !fullViewBox || root.getAttribute("data-raya-graph-layout") === "list") {
      return null;
    }
    const selectedIds = neighborsOf(selectedId);
    const points = Array.from(selectedIds)
      .map((id) => latestRenderedPositions.get(id))
      .filter(Boolean);
    return paddedGraphBounds(points, 72);
  }

  function setFitSelectionEnabled() {
    if (!fitSelection) return;
    const enabled = Boolean(
      selectedId &&
      fullViewBox &&
      root.getAttribute("data-raya-graph-layout") !== "list" &&
      latestRenderedPositions.has(selectedId)
    );
    fitSelection.disabled = !enabled;
  }

  function fitSelectedGraphContext() {
    const box = selectedNeighborhoodBounds();
    if (!box) return;
    setGraphViewBox(box);
  }
```

- [ ] **Step 4: Store rendered geometry and update disabled state**

In `render()`, after:

```javascript
    const geometry = positionsFor(activeNodes, mode, activeEdges);
```

add:

```javascript
    latestRenderedPositions = geometry.positions;
    latestRenderedEdges = activeEdges;
```

In the `mode === "list"` branch before `return;`, add:

```javascript
      latestRenderedPositions = new Map();
      latestRenderedEdges = [];
      setFitSelectionEnabled();
```

At the end of the SVG render path, after `updateInspectionDom();`, add:

```javascript
    setFitSelectionEnabled();
```

- [ ] **Step 5: Add event listener**

After the existing global fit listener:

```javascript
  if (fit) {
    fit.addEventListener("click", () => {
      graphViewBox = null;
      render();
    });
  }
```

add:

```javascript
  if (fitSelection) {
    fitSelection.addEventListener("click", fitSelectedGraphContext);
  }
```

- [ ] **Step 6: Run focused tests and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: both tests pass.

### Task 4: Documentation

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Update foundation contract**

In `docs/foundation/20_learning_renderer_contract.md`, update the graph
contract sentence that names viewport controls from:

```markdown
Pan, Zoom in, Zoom out, Fit, and Reset view may change the SVG `viewBox`; they must
```

to:

```markdown
Pan, Zoom in, Zoom out, Fit, Fit selection, and Reset view may change the SVG `viewBox`; they must
```

Add one sentence after that paragraph:

```markdown
Fit selection may frame the selected page and visible directly connected graph context, but it must not change graph data, selection, filters, URL state, storage, progress, ranking, recommendation, or mastery semantics.
```

- [ ] **Step 2: Update English agent guide**

In `docs/guides/en/agents/index.md`, update the graph viewport control guidance
to name `Fit selection` and add:

```markdown
For selected-page fit behavior, verify that `Fit selection` is disabled without a selected page and in list layout, becomes enabled after page selection, changes only the SVG `viewBox`, keeps selected-page details/search/filter/URL state intact, and frames the selected page plus at least one visible connected edge when such an edge exists.
```

- [ ] **Step 3: Update Spanish agent guide**

In `docs/guides/es/agentes/index.md`, update the equivalent graph viewport
control guidance to name `Fit selection` and add:

```markdown
Para el ajuste de pagina seleccionada, verifica que `Fit selection` este deshabilitado sin pagina seleccionada y en layout de lista, se habilite despues de seleccionar una pagina, cambie solo el `viewBox` SVG, mantenga intactos detalles de pagina seleccionada, busqueda, filtros y estado de URL, y encuadre la pagina seleccionada mas al menos una arista conectada visible cuando exista.
```

### Task 5: Review, Gates, Commit, Push, Preview

**Files:**
- All files modified by prior tasks.

- [ ] **Step 1: Request focused code review**

Use `superpowers:requesting-code-review` and dispatch one reviewer. Ask it to
inspect the diff for selected-fit correctness, static constraints, test
coverage, docs, and regressions to global `Fit`, `Reset view`, URL state,
selection, search, filters, list layout, and no-storage/no-fetch rules.

- [ ] **Step 2: Run focused checks**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

- [ ] **Step 3: Run canonical gates sequentially**

Run:

```bash
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

- [ ] **Step 4: Commit and push**

Run:

```bash
git add docs/foundation/20_learning_renderer_contract.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md docs/superpowers/plans/2026-06-24-graph-fit-selection.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/graph.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add graph fit selection"
git push origin new_rayalucaria
```

- [ ] **Step 5: Start local preview**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --port 0
```

Report the preview URL and the focused graph URL:

```text
/_raya/graph/index.html?page=authoring-matrix
```

## Self-Review

- The plan implements the design through one scoped graph viewport feature.
- It keeps old-main inspiration limited to graph orientation and does not add
  Cytoscape, CDN requests, browser-side rendering, storage, learner state, or
  recommendation language.
- It includes RED contract and browser tests before implementation.
- It preserves the existing global `Fit` behavior with an explicit regression
  assertion.
