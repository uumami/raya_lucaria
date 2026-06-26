# Discovery Workspace Grouped Controls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Group Search, Practice, Tasks, and Schedule controls into readable static control sections and separate the visible count/page-focus state from input controls.

**Architecture:** Keep existing static builder functions and per-workspace scripts. Update only generated HTML in `packages/static/src/raya_static/builder.py`, shared CSS in `packages/static/src/raya_static/rendering.py`, and contract assertions in `tests/contracts/test_static_builder.py`.

**Tech Stack:** Python static builder, generated HTML/CSS, pytest contract tests.

---

### Task 1: Contract Tests For Grouped Controls

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add failing assertions for Search**

In `test_build_writes_local_course_search_surface`, assert:

```python
assert 'class="raya-discovery-control-group"' in search_html
assert "<legend>Query</legend>" in search_html
assert "<legend>Reset</legend>" in search_html
assert "raya-discovery-control-state" in search_html
assert 'id="raya-search-input"' in search_html
assert 'id="raya-search-clear"' in search_html
assert "data-raya-search-summary-count" in search_html
assert "data-raya-search-page-focus" in search_html
```

- [ ] **Step 2: Add failing assertions for Practice, Tasks, and Schedule**

Add equivalent assertions:

```python
assert "<legend>Object type</legend>" in practice_html
assert "<legend>Sort</legend>" in tasks_html
assert "<legend>Date kind</legend>" in schedule_html
```

Each workspace test also keeps the existing ID and data-hook assertions.

- [ ] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace tests/contracts/test_static_builder.py::test_build_writes_static_official_tasks_workspace tests/contracts/test_static_builder.py::test_build_writes_static_schedule_workspace -q
```

Expected: failure because grouped control markup does not exist yet.

### Task 2: Builder Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Group Search controls**

Wrap search input in a `Query` fieldset and Clear/status in a `Reset` fieldset.
Wrap summary and page-focus paragraphs in:

```html
<div class="raya-discovery-control-state" aria-label="Search workspace state">
```

- [ ] **Step 2: Group Practice controls**

Use `Query`, `Object type`, and `Reset` fieldsets. Keep
`raya-practice-search`, `raya-practice-clear`, and `raya-practice-filters`
unchanged.

- [ ] **Step 3: Group Tasks controls**

Use `Query`, `Sort`, `Object type`, and `Reset` fieldsets. Keep
`raya-tasks-search`, `raya-tasks-sort`, `raya-tasks-clear`, and
`raya-task-filters` unchanged.

- [ ] **Step 4: Group Schedule controls**

Use `Query`, `Date kind`, `Object type`, and `Reset` fieldsets. Keep
`raya-schedule-search`, `raya-schedule-clear`, and both
`raya-schedule-filters` containers unchanged.

- [ ] **Step 5: Verify GREEN for focused tests**

Run the focused pytest command from Task 1. Expected: all four tests pass.

### Task 3: Shared Styling And Verification

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Style grouped controls**

Add CSS for `.raya-discovery-control-group`,
`.raya-discovery-control-group legend`, and
`.raya-discovery-control-state`. Use compact borders, muted uppercase legends,
grid spacing, and `min-inline-size: 0` to avoid overflow.

- [ ] **Step 2: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace tests/contracts/test_static_builder.py::test_build_writes_static_official_tasks_workspace tests/contracts/test_static_builder.py::test_build_writes_static_schedule_workspace -q
```

Expected: all four tests pass.

- [ ] **Step 3: Run render/full verification**

Run:

```bash
./scripts/check.sh
```

Expected: command exits 0 and includes the render-debug gate.

- [ ] **Step 4: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-discovery-workspace-grouped-controls-design.md docs/superpowers/plans/2026-06-26-discovery-workspace-grouped-controls.md tests/contracts/test_static_builder.py packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py
git commit -m "Group discovery workspace controls"
git push origin new_rayalucaria
```
