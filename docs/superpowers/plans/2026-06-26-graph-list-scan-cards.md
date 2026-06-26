# Graph List Scan Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Graph workspace page list readable as structured scan cards instead of cramped inline title and metadata text.

**Architecture:** Keep the existing `li[data-raya-graph-node]` graph list contract so `graph.js` behavior remains unchanged. Update only generated list item markup in `builder.py`, token-based CSS in `rendering.py`, and focused contract/browser tests.

**Tech Stack:** Python 3.10 static builder, generated HTML/CSS, local vanilla graph script, pytest, Playwright.

---

### Task 1: Contract Test For Structured Graph List Items

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Add failing contract assertions**

In `test_build_writes_local_visual_graph_surface`, after the existing
`assert "raya-graph-list-metrics" in graph_html`, add:

```python
    assert "raya-graph-list-title-row" in graph_html
    assert "raya-graph-list-status" in graph_html
    assert "raya-graph-list-relationship-counts" in graph_html
    assert "raya-graph-list-stable-id" in graph_html
    assert (
        '<span class="raya-graph-list-status">ready</span>'
        in graph_html
    )
    assert graph_html.index("raya-graph-list-title-row") < graph_html.index(
        "raya-graph-list-metrics"
    )
    assert graph_html.index("raya-graph-list-metrics") < graph_html.index(
        "raya-graph-list-summary"
    )
```

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: FAIL because the generated graph list still lacks the structured row
classes.

### Task 2: Generate Structured List Card Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [x] **Step 1: Replace graph list item string assembly**

In `_render_graph_surface()`, replace the current `node_items.append(...)`
body with:

```python
        node_items.append(
            f'<li data-raya-graph-node="{html.escape(node["id"], quote=True)}">'
            '<div class="raya-graph-list-title-row">'
            f'<a href="{html.escape(node["url"])}">{html.escape(node["title"])}</a>'
            f'<span class="raya-graph-list-status">{html.escape(node["status"])}</span>'
            "</div>"
            '<span class="raya-graph-list-metrics">'
            f'<span class="raya-graph-list-stable-id">Stable ID '
            f'{html.escape(node["stable_id"])}</span>'
            f'<span class="raya-graph-list-relationship-counts">'
            f'Explicit links: {edge_count}; Backlinks: {backlink_count}</span>'
            "</span>"
            f'<span class="raya-graph-list-summary">{html.escape(node["summary"])}</span>'
            "</li>"
        )
```

- [x] **Step 2: Verify GREEN for contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: PASS.

### Task 3: Style Graph List Scan Cards

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add failing browser assertions**

In `test_preview_serves_local_visual_graph_surface`, after the assertion that
`.raya-graph-list-panel` is visible, add:

```python
                        list_card_probe = page.evaluate(
                            """() => {
                              const item = document.querySelector(
                                '#raya-graph-list [data-raya-graph-node="reader-ux"]'
                              );
                              const titleRow = item?.querySelector('.raya-graph-list-title-row');
                              const metrics = item?.querySelector('.raya-graph-list-metrics');
                              const summary = item?.querySelector('.raya-graph-list-summary');
                              const status = item?.querySelector('.raya-graph-list-status');
                              const box = (node) => {
                                const rect = node?.getBoundingClientRect();
                                return rect
                                  ? { top: rect.top, left: rect.left, width: rect.width, height: rect.height }
                                  : null;
                              };
                              return {
                                titleRow: box(titleRow),
                                metrics: box(metrics),
                                summary: box(summary),
                                status: box(status),
                                titleDisplay: getComputedStyle(titleRow).display,
                                metricsDisplay: getComputedStyle(metrics).display,
                                summaryDisplay: getComputedStyle(summary).display,
                                statusText: status?.textContent?.trim(),
                                summaryText: summary?.textContent?.trim(),
                              };
                            }"""
                        )
                        assert list_card_probe["titleDisplay"] == "flex"
                        assert list_card_probe["metricsDisplay"] in {"flex", "grid"}
                        assert list_card_probe["summaryDisplay"] == "block"
                        assert list_card_probe["statusText"] == "ready"
                        assert "projection residuals" in list_card_probe["summaryText"]
                        assert (
                            list_card_probe["metrics"]["top"]
                            > list_card_probe["titleRow"]["top"]
                        )
                        assert (
                            list_card_probe["summary"]["top"]
                            > list_card_probe["metrics"]["top"]
                        )
                        assert list_card_probe["status"]["width"] >= 42
```

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: FAIL because the existing graph list CSS does not create the scan-card
row layout.

- [x] **Step 3: Add CSS for structured graph list cards**

In `packages/static/src/raya_static/rendering.py`, update the graph list CSS
near `.raya-graph-list li` with:

```css
.raya-graph-list li {
  border: 1px solid var(--raya-color-border);
  border-left: 4px solid var(--raya-graph-node-color, var(--raya-color-accent));
  border-radius: 0.5rem;
  display: block;
  margin: 0 0 0.65rem;
  padding: 0.7rem 0.75rem;
}
.raya-graph-list-title-row {
  align-items: flex-start;
  display: flex;
  gap: 0.5rem;
  justify-content: space-between;
}
.raya-graph-list-title-row a {
  font-weight: 850;
  min-width: 0;
}
.raya-graph-list-status {
  border: 1px solid var(--raya-color-border);
  border-radius: 999px;
  color: var(--raya-color-muted);
  flex: 0 0 auto;
  font-size: 0.72rem;
  font-weight: 800;
  line-height: 1;
  padding: 0.25rem 0.45rem;
  text-transform: uppercase;
}
.raya-graph-list-metrics {
  color: var(--raya-color-muted);
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.65rem;
  font-size: 0.84rem;
  line-height: 1.35;
  margin-top: 0.35rem;
}
.raya-graph-list-summary {
  color: var(--raya-color-muted);
  display: block;
  font-size: 0.9rem;
  line-height: 1.45;
  margin-top: 0.45rem;
}
```

- [x] **Step 4: Verify GREEN for browser test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: PASS.

- [x] **Step 5: Preserve focused list inspection over stale canvas hover**

Add a direct browser assertion that focuses the `static-path` graph list link,
dispatches `mouseenter` on a different canvas node, and confirms the focused
list node remains the inspected node:

```python
assert list_focus_over_hover["activeNode"] == "static-path"
assert "Static Path" in list_focus_over_hover["hoverStatus"]
assert list_focus_over_hover["inspectedListNodes"] == ["static-path"]
```

In `packages/static/src/raya_static/graph.py`, guard canvas hover inspection:

```javascript
function graphListHasFocus() {
  const active = document.activeElement;
  return Boolean(active && list && list.contains(active));
}

link.addEventListener("mouseenter", () => {
  if (graphListHasFocus()) return;
  inspectGraphNode(node.id, { bubble: true });
});
```

RED/GREEN verification:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: FAIL without the guard and PASS with the guard.

### Task 4: Verification, Review, Commit, Push

**Files:**
- Create: `docs/superpowers/specs/2026-06-26-graph-list-scan-cards-design.md`
- Create: `docs/superpowers/plans/2026-06-26-graph-list-scan-cards.md`
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `packages/static/src/raya_static/graph.py`
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Run focused tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

- [x] **Step 2: Run render debug**

```bash
./scripts/check-render-debug.sh
```

- [x] **Step 3: Request independent code review**

Ask a reviewer to verify that the graph list is more readable, the static graph
contract is preserved, and no runtime storage/fetch/external dependency was
introduced.

- [ ] **Step 4: Commit and push**

```bash
git add docs/superpowers/specs/2026-06-26-graph-list-scan-cards-design.md docs/superpowers/plans/2026-06-26-graph-list-scan-cards.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py packages/static/src/raya_static/graph.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Polish graph list scan cards"
git push origin new_rayalucaria
```

## Plan Self-Review

- The markup task preserves `li[data-raya-graph-node]` and existing anchors.
- The CSS task changes presentation only; the small graph-script guard keeps
  focused list navigation from being overwritten by stale canvas hover.
- The tests cover generated static markup and browser layout.
- No task adds fetch, storage, browser-side math, external requests, or graph
  payload changes.
