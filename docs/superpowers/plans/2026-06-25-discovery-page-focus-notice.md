# Discovery Page Focus Notice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make URL-scoped Search, Practice, Tasks, and Schedule handoffs visibly explain that the workspace is focused on one public page.

**Architecture:** Each workspace already parses `?page=<page-id>` into local `activePage` state and filters embedded payload-backed DOM cards. This plan adds one hidden notice placeholder per workspace, updates the existing render functions to fill/hide it from embedded public data, and styles the notice through shared discovery CSS.

**Tech Stack:** Python static builder, embedded local JavaScript strings, CSS custom properties, pytest, Playwright.

---

### Task 1: Page Focus Notice RED Tests

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add Search page-focus assertions**

In `test_preview_serves_local_visual_graph_surface`, after the existing Search handoff assertions for page-scoped search, add assertions that the search workspace exposes a focus notice:

```python
page.goto(
    f"{base_url}/_raya/search/index.html?page=authoring-matrix",
    wait_until="networkidle",
)
page.wait_for_function(
    """() => document
      .querySelector('#raya-search-status')
      ?.textContent
      ?.includes('1 visible result')"""
)
search_focus_notice = page.locator("[data-raya-search-page-focus]")
assert search_focus_notice.is_visible()
assert "Focused on page" in search_focus_notice.inner_text()
assert "Authoring Matrix Fixture" in search_focus_notice.inner_text()
assert "1 visible result" in search_focus_notice.inner_text()
page.click("#raya-search-clear")
page.wait_for_function(
    """() => document
      .querySelector('#raya-search-status')
      ?.textContent
      ?.includes('6 visible result')"""
)
assert search_focus_notice.is_hidden()
```

- [x] **Step 2: Add Practice page-focus assertions**

In `test_preview_serves_static_official_practice_workspace`, after the existing `?page=first-topic` assertions, add:

```python
practice_focus_notice = page.locator("[data-raya-practice-page-focus]")
assert practice_focus_notice.is_visible()
assert "Focused on page" in practice_focus_notice.inner_text()
assert "First Topic" in practice_focus_notice.inner_text()
assert "3 visible practice object" in practice_focus_notice.inner_text()
page.click("#raya-practice-clear")
page.wait_for_function(
    """() => document
      .querySelector('#raya-practice-status')
      ?.textContent
      ?.includes('3 visible practice object')"""
)
assert practice_focus_notice.is_hidden()
```

For the existing missing-page visit in the same test, add:

```python
assert page.locator("[data-raya-practice-page-focus]").is_hidden()
```

- [x] **Step 3: Add Tasks and Schedule page-focus assertions**

In `test_preview_serves_static_official_tasks_workspace`, inside the scoped tasks page block, add:

```python
tasks_focus_notice = scoped_tasks.locator("[data-raya-tasks-page-focus]")
assert tasks_focus_notice.is_visible()
assert "Focused on page" in tasks_focus_notice.inner_text()
assert "First Topic" in tasks_focus_notice.inner_text()
assert "4 visible tasks" in tasks_focus_notice.inner_text()
scoped_tasks.click("#raya-tasks-clear")
scoped_tasks.wait_for_function(
    """() => document
      .querySelector('#raya-tasks-status')
      ?.textContent
      ?.includes('5 visible tasks')"""
)
assert tasks_focus_notice.is_hidden()
```

Inside the scoped schedule page block, add equivalent assertions:

```python
schedule_focus_notice = scoped_schedule.locator("[data-raya-schedule-page-focus]")
assert schedule_focus_notice.is_visible()
assert "Focused on page" in schedule_focus_notice.inner_text()
assert "First Topic" in schedule_focus_notice.inner_text()
assert "3 visible schedule item" in schedule_focus_notice.inner_text()
scoped_schedule.click("#raya-schedule-clear")
scoped_schedule.wait_for_function(
    """() => document
      .querySelector('#raya-schedule-status')
      ?.textContent
      ?.includes('4 visible schedule items')"""
)
assert schedule_focus_notice.is_hidden()
```

- [x] **Step 4: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q --tb=short tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_official_practice_workspace tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_official_tasks_workspace
```

Expected: fail because `[data-raya-*-page-focus]` elements do not exist.

### Task 2: Add Focus Notice Markup and Styles

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Add hidden notice placeholders**

Add one hidden paragraph after each existing discovery summary in `builder.py`:

```html
<p class="raya-discovery-page-focus" data-raya-search-page-focus hidden aria-live="polite"></p>
<p class="raya-discovery-page-focus" data-raya-practice-page-focus hidden aria-live="polite"></p>
<p class="raya-discovery-page-focus" data-raya-tasks-page-focus hidden aria-live="polite"></p>
<p class="raya-discovery-page-focus" data-raya-schedule-page-focus hidden aria-live="polite"></p>
```

Use the matching data attribute in each workspace only.

- [x] **Step 2: Style the notice**

Add CSS in `rendering.py` near the discovery summary/context styles:

```css
.raya-discovery-page-focus {
  background: color-mix(in srgb, var(--raya-color-accent) 10%, var(--raya-color-surface));
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 35%, var(--raya-color-border));
  border-radius: 0.55rem;
  color: var(--raya-color-text);
  font-size: 0.9rem;
  line-height: 1.45;
  margin: 0.65rem 0 0;
  padding: 0.6rem 0.7rem;
}

.raya-discovery-page-focus[hidden] {
  display: none;
}
```

- [ ] **Step 3: Verify static markup test still fails for script behavior**

Run the RED command from Task 1. Expected: fail because the placeholders exist but remain hidden and empty.

### Task 3: Implement Workspace Notice Updates

**Files:**
- Modify: `packages/static/src/raya_static/search.py`
- Modify: `packages/static/src/raya_static/practice.py`
- Modify: `packages/static/src/raya_static/tasks.py`
- Modify: `packages/static/src/raya_static/schedule.py`

- [x] **Step 1: Add notice constants**

In each script, add the matching query near the existing summary/context constants:

```javascript
const pageFocusNotice = document.querySelector("[data-raya-search-page-focus]");
const pageFocusNotice = document.querySelector("[data-raya-practice-page-focus]");
const pageFocusNotice = document.querySelector("[data-raya-tasks-page-focus]");
const pageFocusNotice = document.querySelector("[data-raya-schedule-page-focus]");
```

Use only the one matching the script.

- [x] **Step 2: Add page lookup helpers**

Search can reuse `pagesById`. Practice/Tasks/Schedule can derive the active
page from the current embedded objects:

```javascript
function pageTitleForActivePage() {
  if (!activePage) return "";
  const item = items.find((candidate) => candidate.page_id === activePage);
  return item ? (item.page_title || activePage) : "";
}
```

In Search use:

```javascript
function pageTitleForActivePage() {
  if (!activePage) return "";
  const page = pagesById.get(activePage);
  return page ? (page.title || page.nav_title || activePage) : "";
}
```

- [x] **Step 3: Add notice update functions**

In Search:

```javascript
function updatePageFocusNotice(visibleCount) {
  if (!pageFocusNotice) return;
  const title = pageTitleForActivePage();
  if (!activePage || !title) {
    pageFocusNotice.hidden = true;
    pageFocusNotice.textContent = "";
    return;
  }
  pageFocusNotice.hidden = false;
  pageFocusNotice.textContent = `Focused on page ${title}. ${visibleCount} visible result(s). Use Clear to show all.`;
}
```

In Practice:

```javascript
function updatePageFocusNotice(visibleCount) {
  if (!pageFocusNotice) return;
  const title = pageTitleForActivePage();
  if (!activePage || !title) {
    pageFocusNotice.hidden = true;
    pageFocusNotice.textContent = "";
    return;
  }
  pageFocusNotice.hidden = false;
  pageFocusNotice.textContent = `Focused on page ${title}. ${visibleCount} visible practice object(s). Use Clear to show all.`;
}
```

In Tasks:

```javascript
function updatePageFocusNotice(visibleCount) {
  if (!pageFocusNotice) return;
  const title = pageTitleForActivePage();
  if (!activePage || !title) {
    pageFocusNotice.hidden = true;
    pageFocusNotice.textContent = "";
    return;
  }
  pageFocusNotice.hidden = false;
  pageFocusNotice.textContent = `Focused on page ${title}. ${taskCountText(visibleCount)} Use Clear to show all.`;
}
```

In Schedule:

```javascript
function updatePageFocusNotice(visibleCount) {
  if (!pageFocusNotice) return;
  const title = pageTitleForActivePage();
  if (!activePage || !title) {
    pageFocusNotice.hidden = true;
    pageFocusNotice.textContent = "";
    return;
  }
  pageFocusNotice.hidden = false;
  pageFocusNotice.textContent = `Focused on page ${title}. ${scheduleCountText(visibleCount)} Use Clear to show all.`;
}
```

- [x] **Step 4: Call the updater from render**

In each `render()` after the visible count is known and before/after status update, call:

```javascript
updatePageFocusNotice(visible);
```

- [x] **Step 5: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q --tb=short tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_official_practice_workspace tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_official_tasks_workspace
```

Expected: pass.

### Task 4: Documentation

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] **Step 1: Update foundation contract**

Add one sentence to the discovery workspace paragraph:

```markdown
When Search, Practice, Tasks, or Schedule open from `?page=<page-id>`, they may show a compact page-focus notice naming the public page and visible count; this is URL-only workspace context, not learner state, progress, recommendation, ranking, or personalization.
```

- [x] **Step 2: Update role docs**

Add short English and Spanish notes:

- Students: page-focused workspace links can show a notice naming the page and visible count; Clear/Escape restores all.
- Contributors/agents: notices must use embedded public data, avoid storage/fetch/private paths, and avoid recommendation/progress language.

### Task 5: Review, Verification, Commit

**Files:**
- All files changed in Tasks 1-4.

- [x] **Step 1: Request independent review**

Dispatch a reviewer to check:

```text
Review the discovery page-focus notice diff. Verify it uses only embedded public payload data, does not add storage/fetch/CDN/URL mutation, clears on Clear/Escape, handles missing ?page values calmly, avoids recommendation/progress language, and has browser coverage for Search, Practice, Tasks, and Schedule.
```

- [x] **Step 2: Run verification**

Run:

```bash
git diff --check
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q --tb=short tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_course_search_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_official_practice_workspace tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_official_tasks_workspace
rg -n "fetch\\(|XMLHttpRequest|localStorage|sessionStorage|https?://|cdn|recommended|progress|mastery|personalized" packages/static/src/raya_static/search.py packages/static/src/raya_static/practice.py packages/static/src/raya_static/tasks.py packages/static/src/raya_static/schedule.py packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py docs/foundation/20_learning_renderer_contract.md docs/guides/en docs/guides/es
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: all commands exit 0. The `rg` command may report existing documented forbidden terms in guidance; inspect each hit and confirm no new learner-state or recommendation wording was added to runtime workspace UI.

- [x] **Step 3: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-25-discovery-page-focus-notice-design.md docs/superpowers/plans/2026-06-25-discovery-page-focus-notice.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py packages/static/src/raya_static/search.py packages/static/src/raya_static/practice.py packages/static/src/raya_static/tasks.py packages/static/src/raya_static/schedule.py tests/e2e/test_preview_static_read_path.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/en/professors/index.md docs/guides/en/contributors/index.md docs/guides/en/agents/index.md docs/guides/es/estudiantes/index.md docs/guides/es/profesores/index.md docs/guides/es/colaboradores/index.md docs/guides/es/agentes/index.md
git commit -m "Add discovery page focus notices"
git push origin new_rayalucaria
```
