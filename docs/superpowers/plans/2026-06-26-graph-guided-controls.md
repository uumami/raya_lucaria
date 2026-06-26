# Graph Guided Controls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a compact static guide strip near the graph canvas so students can learn the graph controls without hunting through the inspector.

**Architecture:** Generate static guide markup in the graph page builder, style it in the shared rich CSS, and cover it with contract and browser tests. No JavaScript or runtime data path changes are required.

**Tech Stack:** Python 3.10, static HTML/CSS generation, pytest, Playwright/Chromium.

---

### Task 1: Contract Coverage

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add failing contract assertions**

In `test_static_builder_renders_local_visual_graph_surface`, after the existing orientation assertions, add:

```python
    assert "raya-graph-guide" in graph_html
    assert "data-raya-graph-guide" in graph_html
    for label in ("Find", "Choose a view", "Inspect", "Move", "Filter"):
        assert f"<h2>{label}</h2>" in graph_html
    assert "Search titles, stable IDs, tags, groups, and status." in graph_html
    assert "Pan, zoom, and fit change only this SVG viewport." in graph_html
    assert "Filters hide visible graph marks only." in graph_html
```

- [ ] **Step 2: Run the contract test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_builder_renders_local_visual_graph_surface -q
```

Expected: FAIL because `raya-graph-guide` is not yet generated.

### Task 2: Browser Coverage

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add graph guide browser assertions**

In `test_render_fixture_graph_url_state_and_debug_readout`, after the orientation height assertions and before orientation text assertions, add:

```python
                    guide = page.locator("[data-raya-graph-guide]")
                    assert guide.is_visible()
                    guide_box = guide.bounding_box()
                    assert guide_box is not None
                    assert guide_box["y"] > orientation_box["y"]
                    assert guide_box["y"] < canvas_box["y"]
                    assert guide_box["height"] <= 180
                    guide_text = guide.inner_text()
                    for label in ("Find", "Choose a view", "Inspect", "Move", "Filter"):
                        assert label in guide_text
                    assert "not progress" in guide_text.lower()
```

- [ ] **Step 2: Run the browser test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_url_state_and_debug_readout -q
```

Expected: FAIL because the guide strip does not exist.

### Task 3: Generate Static Guide Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Insert guide section after graph orientation**

Add this generated section inside the graph map panel after `</section>` for
`raya-graph-orientation` and before the SVG canvas:

```html
<section class="raya-graph-guide" data-raya-graph-guide aria-label="Graph quick guide">
  <article class="raya-graph-guide-card">
    <h2>Find</h2>
    <p>Search titles, stable IDs, tags, groups, and status. Use Arrow keys in results; Enter opens the active result.</p>
  </article>
  ...
</section>
```

Use five cards matching the contract test labels. Keep text explicit that graph
filters and viewport changes are structural readability only, not progress,
mastery, ranking, or recommendation.

### Task 4: Style the Guide

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Add compact guide CSS near graph orientation/help rules**

Add styles for:

- `.raya-graph-guide`
- `.raya-graph-guide-card`
- `.raya-graph-guide-card h2`
- `.raya-graph-guide-card p`

Use existing tokens, responsive grid/flex layout, compact spacing, and no
fixed pixel width that can overflow mobile.

### Task 5: Verification and Review

**Files:**
- Check: `packages/static/src/raya_static/builder.py`
- Check: `packages/static/src/raya_static/rendering.py`
- Check: `tests/contracts/test_static_builder.py`
- Check: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Run focused tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_builder_renders_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_url_state_and_debug_readout -q
```

Expected: PASS.

- [ ] **Step 2: Run render debug gate**

```bash
./scripts/check-render-debug.sh
```

Expected: PASS.

- [ ] **Step 3: Run final checks**

```bash
git diff --check
git status --short
```

Expected: no whitespace errors and only intended files changed.

- [ ] **Step 4: Request independent review**

Ask reviewers to inspect visual placement, renderer constraints, no storage or
fetch, and whether the guide adds progress/recommendation language.

- [ ] **Step 5: Commit and push**

```bash
git add docs/superpowers/specs/2026-06-26-graph-guided-controls-design.md docs/superpowers/plans/2026-06-26-graph-guided-controls.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add graph guided controls"
git push origin new_rayalucaria
```
