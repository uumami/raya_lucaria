# Discovery Context Actions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add active-result action links to Search, Practice, Tasks, and Schedule context panels.

**Architecture:** Keep the existing generated workspace pages and local scripts. Add one static context-actions container per workspace, then update it from already embedded public payload records when active context changes.

**Tech Stack:** Python static HTML generation in `packages/static/src/raya_static/builder.py`, local JavaScript resources in `packages/static/src/raya_static/{search,practice,tasks,schedule}.py`, CSS in `packages/static/src/raya_static/rendering.py`, pytest + Playwright.

---

### Task 1: Contract And Browser RED Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add contract assertions for context action containers**

In the existing Search, Practice, Tasks, and Schedule static builder tests, assert each workspace HTML includes:

```python
'class="raya-discovery-context-actions"'
"data-raya-search-context-actions"
"data-raya-practice-context-actions"
"data-raya-tasks-context-actions"
"data-raya-schedule-context-actions"
```

Also assert each local script includes `updateContextActions`.

- [ ] **Step 2: Add browser assertions for active context links**

Extend existing Playwright coverage so each workspace:

```python
page.locator("#raya-*-search").focus()
page.press("#raya-*-search", "ArrowDown")
assert page.locator("[data-raya-*-context-actions] a").count() >= 2
```

Search must assert `Open page`, `View graph`, and generated sibling workspace
links for `authoring-matrix`. Practice, Tasks, and Schedule must assert
`Open page` and `View graph` for their active item.

- [ ] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/contracts/test_static_builder.py::test_build_writes_official_practice_workspace tests/contracts/test_static_builder.py::test_build_writes_official_tasks_workspace tests/contracts/test_static_builder.py::test_build_writes_official_schedule_workspace -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_search_and_discovery_workspaces -q
```

Expected: failures mentioning missing context action containers or missing
context action links.

### Task 2: Generate Context Action Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add action containers to workspace context panels**

Add one paragraph or nav container inside each context panel body:

```html
<p class="raya-discovery-context-actions" data-raya-search-context-actions hidden></p>
```

Use the corresponding data attribute for Practice, Tasks, and Schedule.

- [ ] **Step 2: Verify contract tests still fail only on script behavior**

Run the focused contract command from Task 1. Expected: HTML container
assertions pass; script token assertions fail until Task 3.

### Task 3: Populate Context Actions In Local Scripts

**Files:**
- Modify: `packages/static/src/raya_static/search.py`
- Modify: `packages/static/src/raya_static/practice.py`
- Modify: `packages/static/src/raya_static/tasks.py`
- Modify: `packages/static/src/raya_static/schedule.py`

- [ ] **Step 1: Add a small `setContextActions` helper per script**

Use DOM-created anchors, never `innerHTML` from payload values:

```javascript
function setContextActions(actions, container) {
  if (!container) return;
  container.replaceChildren();
  const visibleActions = actions.filter((action) => action.href);
  container.hidden = visibleActions.length === 0;
  visibleActions.forEach((action) => {
    const link = document.createElement("a");
    link.href = action.href;
    link.textContent = action.label;
    container.appendChild(link);
  });
}
```

- [ ] **Step 2: Update Search context**

For the active page, pass:

```javascript
[
  { label: "Open page", href: page.url },
  { label: "View graph", href: page.graph_url },
  { label: "Open practice", href: page.practice_url },
  { label: "Open tasks", href: page.tasks_url },
  { label: "Open schedule", href: page.schedule_url },
]
```

When no page is visible, clear and hide the container.

- [ ] **Step 3: Update Practice, Tasks, and Schedule context**

For the active object/item, pass:

```javascript
[
  { label: "Open page", href: item.page_url },
  { label: "View graph", href: item.graph_url },
]
```

When no item is visible, clear and hide the container.

- [ ] **Step 4: Verify focused browser and contract tests pass**

Run the focused commands from Task 1. Expected: all selected tests pass.

### Task 4: Style And Documentation

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`

- [ ] **Step 1: Style context action links**

Add `.raya-discovery-context-actions` styling that wraps links, keeps tap
targets usable, and avoids layout shift inside the context panel.

- [ ] **Step 2: Update contract and role docs**

Document that discovery workspace context panels may expose active-result
static action links, and that the links are generated public navigation only.

- [ ] **Step 3: Verify docs and rendering**

Run focused docs/static tests and render debug:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_documentation_surfaces.py tests/contracts/test_static_builder.py -q
./scripts/check-render-debug.sh
```

### Task 5: Review, Full Verification, Commit, Push

**Files:**
- Review all modified files.

- [ ] **Step 1: Request independent review**

Ask one reviewer to check current-renderer/foundation alignment and one reviewer
to check frontend behavior/accessibility risk.

- [ ] **Step 2: Process review feedback**

Fix Critical and Important findings with focused tests.

- [ ] **Step 3: Run full host gate**

```bash
./scripts/check.sh
```

Expected: `check: passed`.

- [ ] **Step 4: Commit and push**

```bash
git add docs/superpowers/specs/2026-06-26-discovery-context-actions-design.md docs/superpowers/plans/2026-06-26-discovery-context-actions.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/search.py packages/static/src/raya_static/practice.py packages/static/src/raya_static/tasks.py packages/static/src/raya_static/schedule.py packages/static/src/raya_static/rendering.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/es/estudiantes/index.md tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add discovery context actions"
git push origin new_rayalucaria
```
