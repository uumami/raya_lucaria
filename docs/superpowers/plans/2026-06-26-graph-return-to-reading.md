# Graph Return To Reading Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the selected-page Graph detail read as a clear static return-to-reading path.

**Architecture:** Reuse the existing Graph selected-page detail markup and graph script. Add semantic wrappers and CSS around already generated actions and sequence links; update only the existing renderDetail text/classes where needed.

**Tech Stack:** Python static builder, generated local JavaScript, generated CSS, pytest, Playwright.

---

### Task 1: Contract Test For Reading Path Structure

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write the failing contract test**

Add assertions to the graph surface contract or a focused test:

```python
assert 'class="raya-graph-detail-reading-path"' in graph_html
assert 'data-raya-graph-detail-reading-path' in graph_html
assert "<h3>Reading path</h3>" in graph_html
assert 'class="raya-graph-detail-primary-actions"' in graph_html
assert 'class="raya-graph-detail-secondary-actions"' in graph_html
assert 'class="raya-graph-detail-sequence-card"' in graph_html
assert "recommend" not in graph_html.lower()
assert "mastery" not in graph_html.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_graph_surface_exposes_return_to_reading_path
```

Expected: FAIL because the reading path wrappers do not exist yet.

### Task 2: Browser Test For Page-Focused Graph Reading Path

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write the failing browser test**

Open `_raya/graph/index.html?page=authoring-matrix` at desktop and mobile
viewports. Assert:

```javascript
const detail = document.querySelector('[data-raya-graph-detail-panel]:not([hidden])');
const path = document.querySelector('[data-raya-graph-detail-reading-path]');
const primary = path?.querySelector('.raya-graph-detail-open-primary');
const previous = path?.querySelector('[data-raya-graph-detail-previous]');
const current = path?.querySelector('[data-raya-graph-detail-current]');
const next = path?.querySelector('[data-raya-graph-detail-next]');
```

Then verify visible `Reading path`, primary action text, previous/current/next
title text, no forbidden words, no local/session storage, and no horizontal
overflow.

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_graph_page_focus_exposes_return_to_reading_path
```

Expected: FAIL because the reading path wrapper is missing.

### Task 3: Implement Markup, Text, And CSS

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/graph.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Add graph detail reading path markup**

Wrap selected-page actions and sequence links in:

```html
<section class="raya-graph-detail-reading-path" data-raya-graph-detail-reading-path>
  <h3>Reading path</h3>
  <p class="raya-graph-detail-reading-path-summary" data-raya-graph-detail-reading-path-summary></p>
  <p class="raya-graph-detail-primary-actions">...</p>
  <p class="raya-graph-detail-secondary-actions">...</p>
  <nav class="raya-graph-detail-sequence" ...>...</nav>
</section>
```

- [ ] **Step 2: Update graph detail text**

In `graph.py`, set the summary to structural text such as:

```javascript
detailReadingPathSummary.textContent =
  "Return to the selected lesson or inspect its course-order neighbors.";
```

Keep the primary link text `Open selected page`.

- [ ] **Step 3: Style reading path cards**

In `rendering.py`, style the reading path section, primary/secondary action
rows, and sequence cards so the block scans clearly and wraps on mobile.

- [ ] **Step 4: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_graph_surface_exposes_return_to_reading_path tests/e2e/test_preview_static_read_path.py::test_graph_page_focus_exposes_return_to_reading_path
```

Expected: PASS.

### Task 4: Verification And Review

**Files:**
- Verify the whole slice.

- [ ] **Step 1: Run verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_graph_surface_exposes_return_to_reading_path tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_graph_page_focus_exposes_return_to_reading_path
git diff --check
./scripts/check-render-debug.sh
```

- [ ] **Step 2: Request independent review**

Ask a read-only reviewer to inspect static-only compliance, selected-page
reading UX, no lost graph behavior, and test quality.

- [ ] **Step 3: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-graph-return-to-reading-design.md docs/superpowers/plans/2026-06-26-graph-return-to-reading.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/graph.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Polish graph return to reading path"
git push origin new_rayalucaria
```
