# Discovery Workspace Panel Collapse Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add non-persistent controls/context panel collapse behavior to Search, Practice, Tasks, and Schedule.

**Architecture:** Add one shared `packages/static/src/raya_static/discovery.py` resource that writes `discovery.js` into `_raya/render/`. Update generated workspace markup in `packages/static/src/raya_static/builder.py` and shared CSS in `packages/static/src/raya_static/rendering.py`. Keep per-workspace scripts focused on filtering and active context.

**Tech Stack:** Python static builder, generated HTML/CSS/JavaScript, pytest contract tests, Playwright e2e.

**Status: implemented.** This checklist is a historical execution record. Current
source support lives in `packages/static/src/raya_static/discovery.py`, generated
workspace panel markup, shared CSS, and focused tests.

---

### Task 1: Contract Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add failing markup/resource assertions**

Add assertions to each of these tests:

```python
assert 'src="../render/discovery.js"' in search_html
assert 'data-raya-discovery-controls-state="expanded"' in search_html
assert 'data-raya-discovery-context-state="expanded"' in search_html
assert 'data-raya-discovery-toggle-panel="controls"' in search_html
assert 'data-raya-discovery-toggle-panel="context"' in search_html
assert 'data-raya-discovery-panel-body="controls"' in search_html
assert 'data-raya-discovery-panel-body="context"' in search_html
```

Apply equivalent assertions for `practice_html`, `tasks_html`, and
`schedule_html`.

- [ ] **Step 2: Add failing shared script assertions**

Read `_raya/render/discovery.js` from a built fixture and assert:

```python
assert "data-raya-discovery-toggle-panel" in discovery_script
assert "aria-expanded" in discovery_script
assert "aria-hidden" in discovery_script
assert "localStorage" not in discovery_script
assert "sessionStorage" not in discovery_script
assert "fetch(" not in discovery_script
assert "XMLHttpRequest" not in discovery_script
```

- [ ] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace tests/contracts/test_static_builder.py::test_build_writes_static_official_tasks_workspace tests/contracts/test_static_builder.py::test_build_writes_static_schedule_workspace -q
```

Expected: failure because the shared script and panel controls do not exist.

### Task 2: Builder And Shared Script

**Files:**
- Create: `packages/static/src/raya_static/discovery.py`
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add the shared script resource**

Create `DISCOVERY_SCRIPT_NAME = "discovery.js"`, `DISCOVERY_RESOURCE_PATH =
"_raya/render"`, `DiscoveryResources`, `discovery_resources()`, and JS that
listens for `[data-raya-discovery-toggle-panel]`.

- [ ] **Step 2: Write the shared resource**

Import the resource in `builder.py`, call `_write_discovery_resources(...)`
during build, and write `discovery.js` to `_raya/render/discovery.js`.

- [ ] **Step 3: Add panel headers and body wrappers**

Update Search, Practice, Tasks, and Schedule generated HTML with root state
attributes, panel headers, toggle buttons, and body wrappers. Preserve all
existing IDs and data hooks.

- [ ] **Step 4: Include `discovery.js` before each workspace script**

Add:

```html
<script src="../render/discovery.js" defer></script>
```

before Search, Practice, Tasks, and Schedule scripts.

- [ ] **Step 5: Verify GREEN for focused tests**

Run the focused pytest command from Task 1. Expected: all four tests pass.

### Task 3: CSS And Browser Verification

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Style panel headers and collapsed rails**

Add shared `.raya-discovery-panel-header` and
`.raya-discovery-panel-body` styles. Add desktop grid rules for collapsed
controls/context states and keep panel bodies visible at mobile widths.

- [ ] **Step 2: Add browser interaction coverage**

In the Search workspace e2e, click controls and context collapse buttons,
assert root state attributes, `aria-expanded`, `aria-hidden`, no horizontal
overflow, and no storage writes.

- [ ] **Step 3: Run focused e2e and contracts**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace tests/contracts/test_static_builder.py::test_build_writes_static_official_tasks_workspace tests/contracts/test_static_builder.py::test_build_writes_static_schedule_workspace tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_course_search_surface -q
```

Expected: all selected tests pass.

- [ ] **Step 4: Run final verification**

Run:

```bash
./scripts/check.sh
```

Expected: command exits 0.

- [ ] **Step 5: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-discovery-workspace-panel-collapse-design.md docs/superpowers/plans/2026-06-26-discovery-workspace-panel-collapse.md packages/static/src/raya_static/discovery.py packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add discovery workspace panel collapse"
git push origin new_rayalucaria
```
