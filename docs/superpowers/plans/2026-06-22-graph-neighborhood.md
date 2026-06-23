# Graph Neighborhood Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add visible selected-neighborhood feedback to the static Course graph page.

**Architecture:** Keep the graph schema and generated payload unchanged. Add static graph-surface placeholders in the builder, compute selected-neighborhood counts in the existing local graph script, and style the new selected-neighbor state through existing graph CSS.

**Tech Stack:** Python static builder, embedded local JavaScript in `packages/static/src/raya_static/graph.py`, static CSS in `rich.css`, pytest contract tests, Playwright e2e tests.

---

### Task 1: Contract Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Write failing static HTML assertions**

In `test_build_writes_local_visual_graph_surface`, assert the graph surface names the connected-page state and includes a detail placeholder:

```python
assert 'data-raya-graph-legend="neighbor"' in graph_html
assert "Connected page" in graph_html
assert 'data-raya-graph-detail-neighborhood' in graph_html
assert "raya-graph-detail-neighborhood" in graph_html
```

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: FAIL because no neighbor legend or neighborhood placeholder exists yet.

### Task 2: Browser Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Write failing browser assertions**

In `test_preview_serves_local_visual_graph_surface`, after opening
`/_raya/graph/index.html?page=authoring-matrix`, assert:

```python
assert "Neighborhood: 4 outgoing link(s), 2 incoming link(s), 4 connected page(s)." in page.locator(
    "[data-raya-graph-detail-neighborhood]"
).inner_text()
assert page.locator(
    '#raya-graph-list [data-raya-graph-node="authoring-matrix"]'
).evaluate("node => node.classList.contains('is-active')")
for node_id in ("render-root", "math-authoring", "numbered-objects", "reader-ux"):
    assert page.locator(
        f'#raya-graph-list [data-raya-graph-node="{node_id}"]'
    ).evaluate("node => node.classList.contains('is-neighbor')")
```

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: FAIL because the neighborhood summary and list neighbor classes do not exist yet.

### Task 3: Builder, JavaScript, And CSS

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/graph.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Add static graph surface placeholders**

Add a legend item:

```html
<span class="raya-graph-legend-item" data-raya-graph-legend="neighbor">
  <span class="raya-graph-legend-swatch raya-graph-legend-neighbor"></span>
  Connected page
</span>
```

Add this inside the selected detail panel after the metadata paragraph:

```html
<p class="raya-graph-detail-neighborhood" data-raya-graph-detail-neighborhood></p>
```

- [x] **Step 2: Compute selected neighborhood**

In `graph.py`, add `detailNeighborhood`, `connectedNodeIds()`, and
`relationshipCountsFor(nodeId)` helpers. Use them in `renderDetail()` and
`renderList(activeIds)`.

- [x] **Step 3: Mark SVG neighbors**

When rendering SVG nodes, add `is-neighbor` to connected non-selected nodes.

- [x] **Step 4: Add CSS**

Style `.raya-graph-legend-neighbor`, `.raya-graph-node.is-neighbor circle`,
`.raya-graph-list li.is-neighbor a`, and `.raya-graph-detail-neighborhood`.

- [x] **Step 5: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: PASS.

### Task 4: Docs, Review, And Gates

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] **Step 1: Update docs**

Document selected-page neighborhood summaries as static graph context, not
recommendations or progress.

- [x] **Step 2: Focused verification**

Run:

```bash
git diff --check
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_renderer_dependencies.py::test_docs_cover_collapsible_learning_shell tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
./scripts/check-render-debug.sh
```

Expected: all commands exit 0.

- [x] **Step 3: Independent review**

Dispatch a read-only reviewer focused on static graph boundaries, no persistence,
no external requests, accessibility, and current renderer patterns.

- [x] **Step 4: Archive gates**

Run:

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: both commands exit 0 before commit/push.
