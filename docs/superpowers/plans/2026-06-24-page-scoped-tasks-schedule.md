# Page-Scoped Tasks and Schedule Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Search and Graph handoff links to Tasks and Schedule honor URL-only `?page=<page-id>` context.

**Architecture:** Tasks and Schedule already render embedded public payloads and local scripts. Add transient `activePage` state initialized from `window.location.search`, compose it with existing search/type/kind filters, and clear it through existing Clear/Escape reset paths.

**Tech Stack:** Python static builder resources containing local JavaScript strings, Playwright e2e tests through pytest, current Raya static renderer contracts.

---

## File Structure

- Modify `packages/static/src/raya_static/tasks.py`: add URL page parsing, page match helper, and reset behavior.
- Modify `packages/static/src/raya_static/schedule.py`: add equivalent URL page parsing, page match helper, and reset behavior.
- Modify `tests/e2e/test_preview_static_read_path.py`: extend Search source-link coverage and the static official Tasks/Schedule workspace browser test.
- Modify `docs/foundation/20_learning_renderer_contract.md`: record Tasks/Schedule `?page=` behavior and verification.
- Modify `docs/guides/en/agents/index.md`: add agent verification guidance.
- Modify `docs/guides/es/agentes/index.md`: add Spanish agent verification guidance.

## Task 1: Failing Browser Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add failing Tasks URL-scope assertions**

In `test_preview_serves_static_official_tasks_workspace`, add a second dated assignment on a separate page, then after the existing Tasks workspace assertions add a separate browser page that opens:

```python
scoped_tasks.goto(
    f"{base_url}/_raya/tasks/index.html?page=first-topic",
    wait_until="networkidle",
)
scoped_tasks.wait_for_function(
    """() => document
      .querySelector('#raya-tasks-status')
      ?.textContent
      ?.includes('4 visible tasks')"""
)
assert scoped_tasks.locator('[data-raya-task-object="unit-assignment"]').is_visible()
assert scoped_tasks.locator('[data-raya-task-object="unit-project"]').is_visible()
assert scoped_tasks.locator('[data-raya-task-object="extension-assignment"]').is_hidden()
assert "4 visible tasks" in scoped_tasks.locator("[data-raya-tasks-summary-count]").inner_text()
assert scoped_tasks.evaluate("() => localStorage.length") == 0
assert scoped_tasks.evaluate("() => sessionStorage.length") == 0
scoped_tasks.click("#raya-tasks-clear")
scoped_tasks.wait_for_function(
    """() => document
      .querySelector('#raya-tasks-status')
      ?.textContent
      ?.includes('5 visible tasks')"""
)
assert scoped_tasks.locator('[data-raya-task-object="extension-assignment"]').is_visible()
```

- [ ] **Step 2: Add failing Schedule URL-scope assertions**

Near existing Schedule workspace assertions, add a separate browser page that opens:

```python
scoped_schedule.goto(
    f"{base_url}/_raya/schedule/index.html?page=first-topic",
    wait_until="networkidle",
)
scoped_schedule.wait_for_function(
    """() => document
      .querySelector('#raya-schedule-status')
      ?.textContent
      ?.includes('3 visible schedule items')"""
)
assert scoped_schedule.locator('[data-raya-schedule-item="unit-assignment"]').is_visible()
assert scoped_schedule.locator('[data-raya-schedule-item="unit-project"]').is_visible()
assert scoped_schedule.locator('[data-raya-schedule-item="extension-assignment"]').is_hidden()
assert "3 visible schedule items" in scoped_schedule.locator("[data-raya-schedule-summary-count]").inner_text()
scoped_schedule.locator("#raya-schedule-search").focus()
scoped_schedule.press("#raya-schedule-search", "Escape")
scoped_schedule.wait_for_function(
    """() => document
      .querySelector('#raya-schedule-status')
      ?.textContent
      ?.includes('4 visible schedule items')"""
)
assert scoped_schedule.locator('[data-raya-schedule-item="unit-assignment"]').is_visible()
assert scoped_schedule.evaluate("() => localStorage.length") == 0
assert scoped_schedule.evaluate("() => sessionStorage.length") == 0
```

- [ ] **Step 3: Run focused test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_official_tasks_workspace -q
```

Expected: FAIL because Tasks and Schedule ignore the `page` URL query and show all items.

## Task 2: Tasks Script Support

**Files:**
- Modify: `packages/static/src/raya_static/tasks.py`

- [ ] **Step 1: Add active page initialization**

After `let activeType = "all";`, add:

```javascript
  let activePage = "";
  try {
    activePage = new URLSearchParams(window.location.search || "").get("page") || "";
  } catch {
    activePage = "";
  }
```

- [ ] **Step 2: Add page match helper**

After `matchesType`, add:

```javascript
  function matchesPage(object) {
    return !activePage || object.dataset.rayaTaskPage === activePage;
  }
```

- [ ] **Step 3: Include page match in render**

Change:

```javascript
const matched = matchesType(object) && matchesSearch(object, query);
```

to:

```javascript
const matched = matchesPage(object) && matchesType(object) && matchesSearch(object, query);
```

- [ ] **Step 4: Clear page scope on reset**

In both Escape and Clear handlers, set:

```javascript
activePage = "";
```

before `render();`.

- [ ] **Step 5: Run focused test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_official_tasks_workspace -q
```

Expected: Schedule scope still fails; Tasks scope passes.

## Task 3: Schedule Script Support

**Files:**
- Modify: `packages/static/src/raya_static/schedule.py`

- [ ] **Step 1: Add active page initialization**

After `let activeKind = "all";`, add:

```javascript
  let activePage = "";
  try {
    activePage = new URLSearchParams(window.location.search || "").get("page") || "";
  } catch {
    activePage = "";
  }
```

- [ ] **Step 2: Add page match helper**

After `matchesKind`, add:

```javascript
  function matchesPage(object) {
    return !activePage || object.dataset.rayaSchedulePage === activePage;
  }
```

- [ ] **Step 3: Include page match in render**

Change:

```javascript
const matched = matchesType(item) && matchesKind(item) && matchesSearch(item, query);
```

to:

```javascript
const matched = matchesPage(item) && matchesType(item) && matchesKind(item) && matchesSearch(item, query);
```

- [ ] **Step 4: Clear page scope on reset**

In both Escape and Clear handlers, set:

```javascript
activePage = "";
```

before `render();`.

- [ ] **Step 5: Run focused test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_official_tasks_workspace -q
```

Expected: PASS.

## Task 4: Builder Markup and Docs

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Add page data attributes to generated cards**

In task cards, add:

```python
f'data-raya-task-page="{html.escape(item["page_id"], quote=True)}" '
```

In schedule cards, add:

```python
f'data-raya-schedule-page="{html.escape(item["page_id"], quote=True)}" '
```

- [ ] **Step 2: Update docs**

Document that Tasks and Schedule may honor non-persistent `?page=<page-id>` links from Graph/Search and that Clear/Escape restores the all-items view without storage.

- [ ] **Step 3: Run contract and e2e checks**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/contracts/test_static_builder.py::test_build_writes_static_official_tasks_workspace tests/contracts/test_static_builder.py::test_build_writes_static_schedule_workspace tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_official_tasks_workspace -q
```

Expected: PASS.

## Task 5: Review, Full Verification, Commit, Push

**Files:**
- Review current diff.

- [ ] **Step 1: Request subagent code review**

Dispatch an independent read-only reviewer for static constraints, URL-only behavior, tests, docs, and no storage/fetch regressions.

- [ ] **Step 2: Run verification gates sequentially**

Run:

```bash
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: all pass.

- [ ] **Step 3: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-24-page-scoped-tasks-schedule-design.md \
  docs/superpowers/plans/2026-06-24-page-scoped-tasks-schedule.md \
  docs/foundation/20_learning_renderer_contract.md \
  docs/guides/en/agents/index.md \
  docs/guides/es/agentes/index.md \
  packages/static/src/raya_static/builder.py \
  packages/static/src/raya_static/tasks.py \
  packages/static/src/raya_static/schedule.py \
  tests/e2e/test_preview_static_read_path.py
git commit -m "Add page-scoped task handoffs"
git push origin new_rayalucaria
```

- [ ] **Step 4: Start preview**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --port 0
```

Report the entrypoint URL.

## Self-Review

- Spec coverage: URL-only page scope, Tasks, Schedule, reset behavior, static constraints, docs, tests, review, and gates are covered.
- Placeholder scan: no placeholders remain.
- Type consistency: `activePage`, `data-raya-task-page`, and `data-raya-schedule-page` are used consistently with existing `page_id` payload fields.
