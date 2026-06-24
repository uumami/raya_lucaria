# Graph Selected Page Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make selected graph page navigation obvious and keyboard-operable while preserving click-to-select inspection.

**Architecture:** Keep the static graph data, layouts, and selected-detail model unchanged. Promote the selected-page open link into a primary detail action, preserve pointer click-to-select, and let focused SVG graph node Enter activation open the generated page with normal link semantics. No schema, storage, fetch, or external library changes.

**Tech Stack:** Python 3.10 static builder, generated HTML/CSS/JavaScript, pytest, Playwright.

---

## File Structure

- `packages/static/src/raya_static/builder.py`
  - Update selected-detail action markup label/class.
  - Update graph help copy with click/double-click/Enter behavior.
- `packages/static/src/raya_static/graph.py`
  - Set selected page detail link label to `Open selected page`.
  - Add `openGraphNode()` helper for local page navigation.
  - Add `keydown` handling on SVG graph node anchors: Enter opens the focused node URL.
- `packages/static/src/raya_static/rendering.py`
  - Add primary-action styling for the selected-page open link.
- `tests/contracts/test_static_builder.py`
  - Assert generated markup, help text, and script symbols.
- `tests/e2e/test_preview_static_read_path.py`
  - Assert primary action navigation, pointer click-to-select, focused-node Enter-to-open, and existing double-click/search Enter regressions.
- `docs/foundation/20_learning_renderer_contract.md`
  - Document selected-page open affordance and keyboard behavior as static navigation.
- `docs/guides/en/agents/index.md`
  - Add English verification guidance.
- `docs/guides/es/agentes/index.md`
  - Add Spanish verification guidance.

---

### Task 1: Contract Tests For Selected Navigation

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add failing graph HTML assertions**

In `test_build_writes_local_visual_graph_surface`, near the existing selected
detail assertions, add:

```python
    assert "raya-graph-detail-open-primary" in graph_html
    assert (
        '<a class="raya-graph-detail-open-primary" '
        'data-raya-graph-detail-link href="../../index.html">'
        "Open selected page</a>"
    ) in graph_html
    assert "Click a graph page once to inspect it" in graph_html
    assert "Double-click a graph page to open it" in graph_html
    assert "When a graph page has keyboard focus, press Enter to open it" in graph_html
```

Near the graph script token assertions, add:

```python
    assert "openGraphNode" in graph_script
    assert "event.key === \"Enter\"" in graph_script
    assert "selectedId === node.id" in graph_script
```

- [ ] **Step 2: Run contract test to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: fails because the primary class, selected-page label, new help text,
and `openGraphNode` script helper do not exist yet.

### Task 2: Browser Tests For Keyboard And Primary Navigation

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add primary action and keyboard assertions**

Inside `test_preview_serves_local_visual_graph_surface`, in the existing graph
navigation block after selecting the first graph node and before navigating
through `[data-raya-graph-detail-link]`, add:

```python
                        assert page.locator(
                            "[data-raya-graph-detail-link]"
                        ).inner_text() == "Open selected page"
                        assert page.locator(
                            ".raya-graph-detail-open-primary"
                        ).is_visible()
```

After the existing double-click graph navigation regression, add:

```python
                        page.goto(
                            f"{base_url}/_raya/graph/index.html",
                            wait_until="networkidle",
                        )
                        keyboard_node = page.locator(
                            '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
                        )
                        keyboard_href = keyboard_node.evaluate(
                            "node => new URL(node.getAttribute('href'), document.baseURI).href"
                        )
                        with page.expect_navigation():
                            keyboard_node.focus()
                            page.keyboard.press("Enter")
                        assert page.url == keyboard_href
```

- [ ] **Step 2: Run browser test to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: fails because the selected detail label is still `Open page`, the
primary class does not exist, and focused graph node Enter does not open the page.

### Task 3: Implement Static Navigation Affordance

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/graph.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Update generated selected action markup and help**

In `packages/static/src/raya_static/builder.py`, replace the existing selected
page link markup:

```python
            '<a data-raya-graph-detail-link href="../../index.html">Open page</a>',
```

with:

```python
            (
                '<a class="raya-graph-detail-open-primary" '
                'data-raya-graph-detail-link href="../../index.html">'
                "Open selected page</a>"
            ),
```

In the graph controls help, add a paragraph near the interaction/help text:

```python
            (
                "<p>Click a graph page once to inspect it. Double-click a graph "
                "page to open it. When a graph page has keyboard focus, press "
                "Enter to open it.</p>"
            ),
```

- [ ] **Step 2: Update detail link label**

In `packages/static/src/raya_static/graph.py`, in `renderDetail()`, replace:

```javascript
      detailLink.textContent = "Open page";
```

with:

```javascript
      detailLink.textContent = "Open selected page";
```

- [ ] **Step 3: Add graph open helper**

Near `selectGraphNode(nodeId)`, add:

```javascript
  function openGraphNode(nodeId) {
    const node = nodesById.get(nodeId);
    if (!node || !node.url) return;
    window.location.href = node.url;
  }
```

- [ ] **Step 4: Add SVG node Enter behavior**

In the SVG node creation block, after the existing `dblclick` listener, add:

```javascript
      link.addEventListener("keydown", (event) => {
        if (event.key !== "Enter") return;
        event.preventDefault();
        window.clearTimeout(pendingSelectTimer);
        openGraphNode(node.id);
      });
```

Replace the `dblclick` listener body:

```javascript
        window.location.href = node.url;
```

with:

```javascript
        openGraphNode(node.id);
```

- [ ] **Step 5: Style the primary selected-page action**

In `packages/static/src/raya_static/rendering.py`, near existing
`.raya-graph-detail-actions a` rules, add:

```css
.raya-graph-detail-actions .raya-graph-detail-open-primary {
  background: var(--raya-accent);
  border-color: var(--raya-accent);
  color: var(--raya-accent-contrast);
  font-weight: 800;
}

.raya-graph-detail-actions .raya-graph-detail-open-primary:focus-visible,
.raya-graph-detail-actions .raya-graph-detail-open-primary:hover {
  filter: brightness(0.96);
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
navigation paragraph to state:

```markdown
Graph selected-page details may expose a primary `Open selected page` action.
Pointer users may click a graph node to select and inspect it, then use the
primary action or double-click the graph node to open the generated page.
Keyboard users may focus a graph node and press Enter to open the focused
generated page. These navigation affordances must use generated local page URLs
and must not change graph data, store graph state, fetch remote data, or imply
recommendation, progress, ranking, mastery, or learner state.
```

- [ ] **Step 2: Update English agent guide**

In `docs/guides/en/agents/index.md`, add:

```markdown
For selected-page navigation, verify that the Graph detail card shows a visible
primary `Open selected page` link, click still selects graph nodes for
inspection, double-click still opens graph node pages, and focused graph nodes
use Enter to open local page URLs without writing browser storage or changing
graph data.
```

- [ ] **Step 3: Update Spanish agent guide**

In `docs/guides/es/agentes/index.md`, add:

```markdown
Para navegacion de pagina seleccionada, verifica que la card de detalle del
Graph muestre un enlace primario visible `Open selected page`, que click siga
seleccionando nodos para inspeccion, que doble click siga abriendo paginas del
grafo, y que los nodos con foco usen Enter para abrir URLs locales de pagina
sin escribir almacenamiento del navegador ni cambiar datos del grafo.
```

### Task 5: Review, Gates, Commit, Push, Preview

**Files:**
- All files modified by prior tasks.

- [ ] **Step 1: Request focused code review**

Use `superpowers:requesting-code-review` and dispatch one reviewer. Ask it to
inspect selected-page navigation correctness, keyboard behavior, static
constraints, tests, docs, and regressions to click-to-select, double-click-open,
search Enter, graph viewport controls, no-storage, no-fetch, and local URLs.

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
git add docs/foundation/20_learning_renderer_contract.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md docs/superpowers/plans/2026-06-24-graph-selected-page-navigation.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/graph.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add graph selected page navigation"
git push origin new_rayalucaria
```

- [ ] **Step 5: Start local preview**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --port 0
```

Report:

```text
http://127.0.0.1:<port>/index.html
http://127.0.0.1:<port>/_raya/graph/index.html?page=authoring-matrix
```

## Self-Review

- The plan implements the design through one scoped graph navigation affordance.
- It keeps single-click selection and existing double-click navigation.
- It adds keyboard parity without adding browser storage, fetch, external graph
  libraries, schema changes, learner state, progress, ranking, recommendation,
  or mastery semantics.
- It includes RED contract and browser tests before implementation.
