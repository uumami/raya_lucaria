# Discovery First Viewport Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Search, Practice, Tasks, and Schedule start as usable work surfaces by placing controls/results before support material while preserving compact overview and collapsible quick-guide help.

**Architecture:** Render each workspace immediately after the page header, then render overview and quick guide as secondary support material. Convert the generated quick guide from a full expanded section into a native closed `details` element with the existing guide cards inside. Tighten discovery overview and guide spacing in shared CSS; keep all behavior static, local, and storage-free.

**Tech Stack:** Python 3.10 static builder, generated HTML/CSS, pytest, Playwright/Chromium.

---

### Task 1: Contract Tests For Collapsed Guide Markup

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Update `_assert_discovery_quick_guide` to require native closed details**

Replace the current section-specific assertions with checks for:

```python
assert (
    '<details class="raya-discovery-quick-guide" '
    f'data-raya-discovery-guide="{kind}" '
) in html
assert "<summary>Quick guide</summary>" in html
assert "<h2>Quick guide</h2>" not in html
```

Keep the existing label, snippet, and forbidden-language assertions unchanged.

- [ ] **Step 2: Run contract tests to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace tests/contracts/test_static_builder.py::test_build_writes_static_official_tasks_workspace tests/contracts/test_static_builder.py::test_build_writes_static_schedule_workspace -q
```

Expected: FAIL because quick guides are still generated as expanded `section`
elements with `<h2>Quick guide</h2>`.

### Task 2: Browser First-Viewport Tests

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Strengthen `test_discovery_workspace_guides_are_visible_without_overflow`**

For each workspace and viewport, assert:

```python
guide = page.locator(f'[data-raya-discovery-guide="{kind}"]')
assert guide.evaluate("node => node.tagName.toLowerCase()") == "details"
assert guide.evaluate("node => node.open") is False
summary = guide.locator("summary")
assert summary.is_visible()
workspace = page.locator(
    {
        "search": ".raya-search-workspace",
        "practice": ".raya-practice-workspace",
        "tasks": ".raya-tasks-workspace",
        "schedule": ".raya-schedule-workspace",
    }[kind]
)
workspace_box = workspace.bounding_box()
assert workspace_box is not None
assert workspace_box["y"] < viewport["height"] * 0.72
guide_box = guide.bounding_box()
assert guide_box is not None
assert workspace_box["y"] < guide_box["y"]
summary.click()
assert guide.evaluate("node => node.open") is True
```

Keep the existing no-overflow assertions and card checks after opening the
guide.

- [ ] **Step 2: Run browser test to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_discovery_workspace_guides_are_visible_without_overflow -q
```

Expected: FAIL because the guide is not a `details` element and the workspace
still starts after support material.

### Task 3: Builder Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Change `_render_discovery_quick_guide` to emit closed details**

Generate this structure and render it after the workspace section:

```html
<details class="raya-discovery-quick-guide" data-raya-discovery-guide="search" aria-label="Workspace quick guide">
<summary>Quick guide</summary>
<div class="raya-discovery-guide-cards">
...
</div>
</details>
```

Do not add the `open` attribute.

- [ ] **Step 2: Run contract tests to verify GREEN for markup**

Run the Task 1 command again.

Expected: PASS.

### Task 4: Shared CSS Density

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Tighten overview and quick-guide spacing**

Adjust shared discovery styles so:

- `.raya-discovery-overview` uses smaller gaps, smaller margin, and compact
  padding;
- `.raya-discovery-overview-meta` uses smaller minimum columns;
- `.raya-discovery-overview-actions a` has smaller min-height and padding;
- `.raya-discovery-quick-guide` styles `summary` as the visible compact row;
- `.raya-discovery-guide-cards` only takes full card space when details is open.

- [ ] **Step 2: Run browser first-viewport test to verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_discovery_workspace_guides_are_visible_without_overflow -q
```

Expected: PASS.

### Task 5: Verification, Review, Commit, Push

**Files:**
- Verify all modified files.

- [ ] **Step 1: Run focused verification**

Run:

```bash
git diff --check
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace tests/contracts/test_static_builder.py::test_build_writes_static_official_tasks_workspace tests/contracts/test_static_builder.py::test_build_writes_static_schedule_workspace tests/e2e/test_preview_static_read_path.py::test_discovery_workspace_guides_are_visible_without_overflow -q
```

Expected: PASS.

- [ ] **Step 2: Request independent review**

Ask a reviewer to inspect the diff for current-framework fit, accessibility,
first-viewport utility, and static/no-storage constraints.

- [ ] **Step 3: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-discovery-first-viewport-design.md docs/superpowers/plans/2026-06-26-discovery-first-viewport.md tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py
git commit -m "Compact discovery workspace guides"
git push origin new_rayalucaria
```
