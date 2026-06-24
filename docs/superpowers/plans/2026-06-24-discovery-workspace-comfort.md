# Discovery Workspace Comfort Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make generated Search, Graph, Practice, Tasks, and Schedule pages feel like one coherent, polished static learning workspace family.

**Architecture:** Keep the existing generated HTML and local JS architecture. Make the discovery command bar the single navigation layer, compact each workspace header, and consolidate CSS for discovery panels, cards, context panels, action links, and graph panels.

**Tech Stack:** Python static builder, generated HTML/CSS/JS, pytest, Playwright browser e2e tests, Superpowers workflow.

---

## File Structure

- Modify `packages/static/src/raya_static/builder.py` to remove duplicate course/back header markup from generated Graph/Search/Practice/Tasks/Schedule pages.
- Modify `packages/static/src/raya_static/rendering.py` to add shared discovery workspace CSS and graph panel alignment.
- Modify `tests/e2e/test_preview_static_read_path.py` to add failing browser/layout tests for the discovery workspaces.
- Modify `tests/contracts/test_static_builder.py` only if contract-level HTML/CSS assertions need to follow the new markup.

## Task 1: Add Failing Discovery Workspace Tests

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add assertions that workspace headers no longer duplicate course navigation**

Add checks to the existing search/workspace browser test so the command bar owns the course link and local headers do not contain `Back to course`.

```python
assert page.locator(".raya-discovery-command-bar .raya-command-home").is_visible()
assert page.locator(".raya-search-header .raya-course-title").count() == 0
assert page.locator(".raya-search-header .raya-graph-back-link").count() == 0
```

- [ ] **Step 2: Extend broad no-overflow coverage to generated workspaces**

In `test_rendered_surfaces_have_no_obvious_layout_overlap_at_viewports`, visit:

```python
for workspace_path in (
    "_raya/search/index.html",
    "_raya/graph/index.html",
    "_raya/practice/index.html",
    "_raya/tasks/index.html",
    "_raya/schedule/index.html",
):
    page.goto(f"{base_url}/{workspace_path}", wait_until="networkidle")
    _assert_no_horizontal_overflow(page)
```

- [ ] **Step 3: Add desktop region order checks for core discovery workspaces**

For desktop viewport only, assert controls/results/context order on Search, Practice, Tasks, and Schedule:

```python
for control_selector, results_selector, context_selector in (
    (".raya-search-control-panel", ".raya-search-results-panel", ".raya-search-context-panel"),
    (".raya-practice-control-panel", ".raya-practice-results-panel", ".raya-practice-context-panel"),
    (".raya-tasks-control-panel", ".raya-tasks-results-panel", ".raya-tasks-context-panel"),
    (".raya-schedule-control-panel", ".raya-schedule-results-panel", ".raya-schedule-context-panel"),
):
    control_box = page.locator(control_selector).bounding_box()
    results_box = page.locator(results_selector).bounding_box()
    context_box = page.locator(context_selector).bounding_box()
    assert control_box is not None
    assert results_box is not None
    assert context_box is not None
    assert control_box["x"] < results_box["x"] < context_box["x"]
```

- [ ] **Step 4: Run focused e2e tests and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_search_workspace_is_static_and_local tests/e2e/test_preview_static_read_path.py::test_rendered_surfaces_have_no_obvious_layout_overlap_at_viewports -q
```

Expected: failure because workspace headers still contain `.raya-course-title` and `.raya-graph-back-link`, and the broad test may expose missing workspace coverage.

## Task 2: Compact Generated Workspace Headers

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Remove duplicate course/back markup from Graph header**

Change the generated Graph header from:

```python
'<header class="raya-graph-header">',
f'<p class="raya-course-title">{html.escape(course_title)}</p>',
'<a class="raya-graph-back-link" href="../../index.html">Back to course</a>',
"<h1>Course Graph</h1>",
```

to:

```python
'<header class="raya-graph-header raya-discovery-header">',
"<h1>Course Graph</h1>",
```

- [ ] **Step 2: Apply the same compact header class to Search, Practice, Tasks, and Schedule**

Use `raya-discovery-header` alongside the existing page-specific header class and remove the local `.raya-course-title` and `.raya-graph-back-link` entries.

- [ ] **Step 3: Run the focused e2e tests and verify GREEN for header behavior**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_search_workspace_is_static_and_local -q
```

Expected: pass for command bar ownership and no duplicate local course/back header.

## Task 3: Consolidate Discovery Workspace CSS

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add shared discovery header/panel/card CSS scoped to workspace classes**

Add grouped selectors for `.raya-discovery-header`, workspace grids, control panels, results panels, context panels, action links, and active cards while preserving existing page-specific class names.

- [ ] **Step 2: Align Graph panels with shared discovery visual language**

Update graph panel backgrounds, borders, button styling, list item spacing, and toolbar surface to match the shared workspace treatment. Do not change graph JS behavior.

- [ ] **Step 3: Improve mobile command/workspace comfort**

Keep the mobile discovery command bar compact and horizontally scrollable. Ensure workspace grids stack to one column and context panels appear after results without horizontal overflow.

- [ ] **Step 4: Run focused e2e tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_search_workspace_is_static_and_local tests/e2e/test_preview_static_read_path.py::test_render_fixture_practice_workspace_is_static_and_local tests/e2e/test_preview_static_read_path.py::test_render_fixture_tasks_and_schedule_workspaces_are_static_and_local tests/e2e/test_preview_static_read_path.py::test_rendered_surfaces_have_no_obvious_layout_overlap_at_viewports -q
```

Expected: all pass without horizontal overflow.

## Task 4: Verify Static Contract Boundaries

**Files:**
- Potentially modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Run relevant contract tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -q
```

Expected: pass. If failures mention old duplicate header markup, update assertions to check command bar navigation instead.

- [ ] **Step 2: Run render debug**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: pass with no external renderer requests, no raw visible TeX leakage, no overflow, and copied static-site parity.

## Task 5: Review, Full Verification, Commit, Push, Preview

**Files:**
- Review all changed files.

- [ ] **Step 1: Request independent code review**

Dispatch independent reviewers over the final diff, asking them to check static contract boundaries, workspace UX, mobile layout, and test coverage.

- [ ] **Step 2: Apply only verified review fixes**

Use `superpowers:receiving-code-review` if reviewers identify issues before applying changes.

- [ ] **Step 3: Run full host gate**

Run:

```bash
./scripts/check.sh
```

Expected: all tests pass and script ends with `check: passed`.

- [ ] **Step 4: Commit and push**

Run:

```bash
git status --short
git add docs/superpowers/specs/2026-06-24-discovery-workspace-comfort-design.md docs/superpowers/plans/2026-06-24-discovery-workspace-comfort.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py tests/contracts/test_static_builder.py
git commit -m "Polish discovery workspaces"
git push origin new_rayalucaria
```

- [ ] **Step 5: Start a local preview and report the URL**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --port 0
```

Report the `_raya/search/index.html` or `_raya/graph/index.html` URL for inspection.
