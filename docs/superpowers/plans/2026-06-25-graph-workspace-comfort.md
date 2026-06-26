# Graph Workspace Comfort Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the static Graph workspace toolbar and pan controls so the graph feels more like a usable learning surface and less like a diagnostic panel.

**Architecture:** Keep the current local SVG graph and generated artifact data. Update only generated Graph HTML, graph toolbar CSS, and focused tests. Preserve existing selectors and data attributes so current graph JavaScript continues to work.

**Tech Stack:** Python static builder, generated local HTML/CSS/JS, Playwright e2e tests, pytest.

---

### Task 1: Graph Toolbar Markup Contract

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Write the failing contract test**

Add assertions to `test_build_writes_local_visual_graph_surface` that expect:

```python
assert "Find pages" in graph_html
assert "Relationship filters" in graph_html
assert "Canvas view" in graph_html
assert "Move canvas" in graph_html
assert "Workspace" in graph_html
assert 'aria-label="Find pages"' in graph_html
assert 'aria-label="Relationship filters"' in graph_html
assert 'aria-label="Canvas view controls"' in graph_html
assert 'aria-label="Move canvas"' in graph_html
assert 'aria-label="Workspace controls"' in graph_html
assert 'aria-label="Pan graph left">&#8592;</button>' in graph_html
assert 'aria-label="Pan graph right">&#8594;</button>' in graph_html
assert 'aria-label="Pan graph up">&#8593;</button>' in graph_html
assert 'aria-label="Pan graph down">&#8595;</button>' in graph_html
```

- [ ] **Step 2: Run the focused contract test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: fail because the graph HTML still uses the old group labels and `L/R/U/D` pan text.

- [ ] **Step 3: Update generated Graph HTML**

In `packages/static/src/raya_static/builder.py`, update `_render_graph_page` toolbar group labels and pan button labels while preserving IDs and `data-raya-graph-*` attributes.

- [ ] **Step 4: Run the focused contract test and verify GREEN**

Run the same focused contract test. Expected: pass.

### Task 2: Graph Toolbar Visual Comfort

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Write the failing browser test**

In `test_preview_serves_local_visual_graph_surface`, add Playwright checks that:

```python
assert page.locator(".raya-graph-toolbar-label", has_text="Find pages").is_visible()
assert page.locator(".raya-graph-toolbar-label", has_text="Canvas view").is_visible()
pan_boxes = page.locator("[data-raya-graph-pan]").evaluate_all(
    """buttons => buttons.map((button) => {
      const box = button.getBoundingClientRect();
      return { width: box.width, height: box.height, text: button.textContent.trim() };
    })"""
)
assert [item["text"] for item in pan_boxes] == ["←", "→", "↑", "↓"]
for item in pan_boxes:
    assert item["width"] >= 34
    assert item["height"] >= 34
    assert abs(item["width"] - item["height"]) <= 12
```

- [ ] **Step 2: Run the focused e2e test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: fail before CSS/markup changes are complete.

- [ ] **Step 3: Update graph toolbar CSS**

In `packages/static/src/raya_static/rendering.py`, add styles for `.raya-graph-toolbar-label`, improve `.raya-graph-toolbar-group`, and give pan buttons stable square dimensions. Keep responsive wrapping and no overflow.

- [ ] **Step 4: Run focused e2e and render-debug checks**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
./scripts/check-render-debug.sh
```

Expected: both pass with no overflow, no external requests, and graph controls visible.

### Task 3: Documentation

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`

- [ ] **Step 1: Update docs**

Document that Graph workspace controls use grouped local controls for page search, relationship filters, canvas viewport, canvas movement, reset, and focus mode. Keep the wording structural and avoid progress/recommendation language.

- [ ] **Step 2: Run focused docs/build verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: pass.
