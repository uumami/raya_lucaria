# Discovery Results Jump Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add mobile static Results jump links to Search, Practice, Tasks, and Schedule controls so narrow-screen readers can reach result panels immediately.

**Architecture:** Give each results panel a stable local fragment `id` and `tabindex="-1"`, then add a small anchor inside the matching controls body near the workspace state. Style the link through shared discovery CSS so it appears on narrow screens and stays hidden on desktop; do not add JavaScript, storage, backend calls, or new data contracts.

**Tech Stack:** Python 3.10 static builder, generated HTML/CSS, pytest, Playwright/Chromium.

---

### Task 1: Contract Tests For Generated Results Jumps

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add helper assertions**

Add a helper near `_assert_discovery_panel_shell`:

```python
def _assert_discovery_results_jump(
    html: str, *, workspace_class: str, control_body_id: str, results_id: str
) -> None:
    jump = (
        '<p class="raya-discovery-results-jump">'
        f'<a href="#{results_id}">Results</a></p>'
    )
    assert re.search(
        rf'<section id="{re.escape(results_id)}" '
        rf'class="{re.escape(workspace_class)}" '
        r'aria-label="[^"]+" tabindex="-1">',
        html,
    )
    assert jump in html
    assert re.search(
        rf'<div id="{re.escape(control_body_id)}" '
        r'class="raya-discovery-panel-body" '
        r'data-raya-discovery-panel-body="controls" aria-hidden="false">'
        r'.*?<div class="raya-discovery-control-state" aria-label="[^"]+">'
        r".*?</div>\s*"
        rf"{re.escape(jump)}\s*</div>\s*</aside>",
        html,
        re.DOTALL,
    )
    assert html.index(jump) < html.index(f'id="{results_id}"')
```

- [ ] **Step 2: Call helper for all four workspaces**

Use:

```python
_assert_discovery_results_jump(
    search_html,
    workspace_class="raya-search-results-panel",
    control_body_id="raya-search-control-panel-body",
    results_id="raya-search-results-panel",
)
_assert_discovery_results_jump(
    practice_html,
    workspace_class="raya-practice-results-panel",
    control_body_id="raya-practice-control-panel-body",
    results_id="raya-practice-results-panel",
)
_assert_discovery_results_jump(
    tasks_html,
    workspace_class="raya-tasks-results-panel",
    control_body_id="raya-tasks-control-panel-body",
    results_id="raya-tasks-results-panel",
)
_assert_discovery_results_jump(
    schedule_html,
    workspace_class="raya-schedule-results-panel",
    control_body_id="raya-schedule-control-panel-body",
    results_id="raya-schedule-results-panel",
)
```

- [ ] **Step 3: Run contract tests to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace tests/contracts/test_static_builder.py::test_build_writes_static_official_tasks_workspace tests/contracts/test_static_builder.py::test_build_writes_static_schedule_workspace -q
```

Expected: FAIL because results panels have no matching IDs or jump links.

### Task 2: Browser Test For Mobile Results Jump

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Extend the discovery guide/mobile workspace test**

In `test_discovery_workspace_guides_are_visible_without_overflow`, for the
`390x844` viewport, click each workspace jump link and assert the results panel
receives focus and intersects the viewport. At `768x1024` and `1366x900`, assert
the jump stays hidden:

```python
if viewport["width"] < 520:
    jump = page.locator(".raya-discovery-results-jump a")
    assert jump.is_visible()
    assert jump.evaluate("node => new URL(node.href).hash") == (
        f"#{kind_to_results_id[kind]}"
    )
    jump.click()
    assert page.locator(
        f"#{kind_to_results_id[kind]}"
    ).evaluate("node => document.activeElement === node")
    _assert_intersects_viewport(page, f"#{kind_to_results_id[kind]}")
else:
    assert (
        page.locator(".raya-discovery-results-jump a").first.is_visible()
        is False
    )
```

Use this mapping:

```python
kind_to_results_id = {
    "search": "raya-search-results-panel",
    "practice": "raya-practice-results-panel",
    "tasks": "raya-tasks-results-panel",
    "schedule": "raya-schedule-results-panel",
}
```

- [ ] **Step 2: Run browser test to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_discovery_workspace_guides_are_visible_without_overflow -q
```

Expected: FAIL because `.raya-discovery-results-jump` does not exist.

### Task 3: Builder Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add `Results` anchors in controls panel headers**

In each controls panel body, immediately after `.raya-discovery-control-state`,
insert:

```html
<p class="raya-discovery-results-jump"><a href="#raya-search-results-panel">Results</a></p>
```

Use the matching panel ID for each workspace.

- [ ] **Step 2: Add result panel IDs**

Change each results panel opening tag to include the matching ID:

```html
<section id="raya-search-results-panel" class="raya-search-results-panel" aria-label="Search results" tabindex="-1">
```

Repeat for Practice, Tasks, and Schedule.

### Task 4: Shared Styling

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Style the jump link inside panel headers**

Add CSS near the shared discovery control/result styles:

```css
.raya-discovery-results-jump {
  display: none;
  margin: 0.75rem 0 0;
}
.raya-discovery-results-jump a {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-surface) 82%, var(--raya-color-accent-soft));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 84%, var(--raya-color-accent));
  border-radius: 0.45rem;
  color: var(--raya-color-text);
  display: inline-flex;
  font-size: 0.9rem;
  font-weight: 800;
  justify-content: center;
  min-height: 2.25rem;
  padding: 0.35rem 0.65rem;
  text-decoration: none;
  width: 100%;
}
.raya-discovery-results-jump a:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
.raya-search-results-panel,
.raya-practice-results-panel,
.raya-tasks-results-panel,
.raya-schedule-results-panel {
  scroll-margin-top: calc(var(--raya-topbar-height, 4rem) + 1rem);
}
@media (max-width: 519px) {
  .raya-discovery-results-jump {
    display: block;
  }
}
```

### Task 5: GREEN Verification

**Files:**
- Verify all modified files.

- [ ] **Step 1: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace tests/contracts/test_static_builder.py::test_build_writes_static_official_tasks_workspace tests/contracts/test_static_builder.py::test_build_writes_static_schedule_workspace tests/e2e/test_preview_static_read_path.py::test_discovery_workspace_guides_are_visible_without_overflow tests/e2e/test_preview_static_read_path.py::test_rendered_surfaces_have_no_obvious_layout_overlap_at_viewports -q
```

Expected: PASS.

- [ ] **Step 2: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no output and exit 0.

### Task 6: Review, Commit, Push

**Files:**
- Commit all files from this plan.

- [x] **Step 1: Request independent review**

Independent review found two issues and both were incorporated before commit:

- Keep the shortcut visible only below `520px`, not throughout the broader
  tablet stack breakpoint.
- Make the contract helper prove the link is inside the collapsible controls
  body, not merely inside the surrounding aside.

Ask a reviewer to inspect static link behavior, accessibility, current
framework fit, and test coverage.

- [ ] **Step 2: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-discovery-results-jump-design.md docs/superpowers/plans/2026-06-26-discovery-results-jump.md tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py
git commit -m "Add discovery results jump links"
git push origin new_rayalucaria
```
