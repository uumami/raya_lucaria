# Course Map Scan Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a non-persistent course-map scan mode that collapses sibling branches while preserving current static renderer constraints.

**Architecture:** The static builder emits a new `Scan` action button. The shell script tracks scan mode as volatile DOM state, reuses existing map expansion helpers, and applies sibling accordion collapse when a branch is opened. CSS gives the pressed scan button a visible active state using existing skin variables.

**Tech Stack:** Python static builder, generated vanilla JavaScript shell resource, generated CSS, pytest, Playwright.

---

### Task 1: Static Contract

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify after RED: `packages/static/src/raya_static/builder.py`
- Modify after RED: `packages/static/src/raya_static/shell.py`
- Modify after RED: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Write the failing static test assertions**

Add assertions to `test_static_builder_renders_collapsible_shell_controls_and_page_position` that expect:

```python
assert 'data-raya-course-map-action="scan"' in html
assert 'aria-pressed="false">Scan</button>' in html
```

Add assertions near the shell script checks that expect:

```python
assert 'data-raya-course-map-action="scan"' in html
assert "rayaCourseMapScan" in script_text
assert "collapseExpandedSiblingMapNodes" in script_text
assert '.raya-course-map-actions button[aria-pressed="true"]' in css_text
```

- [x] **Step 2: Run the static test to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_builder_renders_collapsible_shell_controls_and_page_position -q
```

Expected: FAIL because the scan action is missing.

- [x] **Step 3: Implement minimal static output**

In `builder.py`, add:

```html
<button type="button" data-raya-course-map-action="scan" aria-pressed="false">Scan</button>
```

In `shell.py`, add volatile scan state functions and route the new action through them.

In `rendering.py`, style pressed course-map action buttons with existing variables.

- [x] **Step 4: Run static test to verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_builder_renders_collapsible_shell_controls_and_page_position -q
```

Expected: PASS.

### Task 2: Browser Behavior

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify after RED if needed: `packages/static/src/raya_static/shell.py`

- [x] **Step 1: Write the failing browser behavior test**

Extend `test_minimal_course_map_nested_sections_are_expanded_and_collapsible` by adding extra sibling branches to the temporary minimal course and asserting:

```python
page.click('[data-raya-course-map-action="scan"]')
# scan is active, current remains visible, storage remains empty
page.click('[data-raya-map-node="map-branch-a"] [data-raya-map-node-toggle]')
page.click('[data-raya-map-node="map-branch-b"] [data-raya-map-node-toggle]')
# branch A collapses when branch B opens
page.click('[data-raya-course-map-action="expand-all"]')
# scan exits
page.click('[data-raya-course-map-action="scan"]')
page.click('[data-raya-course-map-action="current"]')
# scan exits through Current
page.click('[data-raya-course-map-action="scan"]')
page.fill("#raya-course-map-filter", "topic")
# scan exits through filtering
```

Also extend the existing mobile drawer and storage-unavailable tests so scan mode clears when the drawer closes and does not read or write browser storage.

- [x] **Step 2: Run the browser test to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_minimal_course_map_nested_sections_are_expanded_and_collapsible -q
```

Expected: FAIL before scan implementation.

- [x] **Step 3: Implement/fix minimal behavior**

Use the existing `setMapNodeExpanded` helper. When scan mode is active and a node is being opened, collapse expanded sibling nodes that share the same nearest parent list.

- [x] **Step 4: Run browser test to verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_minimal_course_map_nested_sections_are_expanded_and_collapsible -q
```

Expected: PASS.

### Task 3: Verification and Review

**Files:**
- No planned source changes unless verification reveals issues.

- [x] **Step 1: Run focused contract and browser tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_builder_renders_collapsible_shell_controls_and_page_position tests/e2e/test_preview_static_read_path.py::test_minimal_course_map_nested_sections_are_expanded_and_collapsible tests/e2e/test_preview_static_read_path.py::test_render_fixture_course_map_works_without_storage tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading -q
```

Expected: PASS.

- [x] **Step 2: Run render-debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS, with local render-debug artifacts only.

- [x] **Step 3: Request independent review**

Dispatch an independent reviewer to inspect the diff against this design, current renderer constraints, and tests.

- [ ] **Step 4: Commit and push**

Run:

```bash
git status --short
git diff --check
git add docs/superpowers/specs/2026-06-26-course-map-scan-mode-design.md docs/superpowers/plans/2026-06-26-course-map-scan-mode.md tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py packages/static/src/raya_static/builder.py packages/static/src/raya_static/shell.py packages/static/src/raya_static/rendering.py
git commit -m "Add course map scan mode"
git push origin new_rayalucaria
```

Expected: commit succeeds and branch pushes to GitHub.
