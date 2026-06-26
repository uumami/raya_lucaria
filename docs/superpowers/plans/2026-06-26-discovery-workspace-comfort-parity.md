# Discovery Workspace Comfort Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a static orientation band to Search, Practice, Tasks, and Schedule as the first Discovery Workspace Comfort Parity slice.

**Architecture:** Use one small helper in `packages/static/src/raya_static/builder.py` to generate overview markup for all four workspaces. Keep scripts unchanged unless tests reveal missing dynamic behavior; this slice is static orientation, not full grouped-control parity. Add shared CSS in `packages/static/src/raya_static/rendering.py`.

**Tech Stack:** Python static builder, generated HTML/CSS, pytest contract tests.

---

### Task 1: Contract Tests For Workspace Overview

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Add failing assertions for Search**

In `test_build_writes_local_course_search_surface`, after existing workspace-panel
assertions, add assertions for `raya-discovery-overview`,
`raya-discovery-overview-meta`, `data-raya-discovery-overview="search"`,
`Public pages`, `Section anchors`, `Reset path`, `Clear or Escape`, and local
workspace action links.

- [x] **Step 2: Add failing assertions for Practice, Tasks, and Schedule**

Add equivalent assertions to the existing practice, tasks, and schedule
workspace tests using their expected generated labels:
`Official objects`, `Object types`, `Task-family objects`, `Dated objects`,
and `Dated event types`.

- [x] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace tests/contracts/test_static_builder.py::test_build_writes_static_official_tasks_workspace tests/contracts/test_static_builder.py::test_build_writes_static_schedule_workspace -q
```

Expected: failure because the new overview markup does not exist yet.

### Task 2: Builder Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [x] **Step 1: Add a shared overview helper**

Create `_render_discovery_overview(...)` near `_render_discovery_command_bar`.
It returns a `<section class="raya-discovery-overview">` with metadata cells and
local action links. Escape all text and href attributes.

- [x] **Step 2: Render overview in all four surfaces**

Insert the helper immediately after each discovery workspace header and before
the workspace grid in `_render_search_surface`, `_render_practice_surface`,
`_render_tasks_surface`, and `_render_schedule_surface`.

- [x] **Step 3: Verify GREEN for focused tests**

Run the same focused pytest command from Task 1. Expected: all four tests pass.

### Task 3: Shared Styling And Final Verification

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Review: `docs/superpowers/specs/2026-06-26-discovery-workspace-comfort-parity-design.md`
- Review: `docs/superpowers/plans/2026-06-26-discovery-workspace-comfort-parity.md`

- [x] **Step 1: Style the overview**

Add CSS for `.raya-discovery-overview`,
`.raya-discovery-overview-main`, `.raya-discovery-overview-meta`, and
`.raya-discovery-overview-actions`. Reuse Graph orientation spacing and color
patterns, keep cards compact, and use responsive grid behavior.

- [x] **Step 2: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace tests/contracts/test_static_builder.py::test_build_writes_static_official_tasks_workspace tests/contracts/test_static_builder.py::test_build_writes_static_schedule_workspace -q
```

Expected: all four tests pass.

- [x] **Step 3: Run branch gate**

Run:

```bash
./scripts/check.sh
```

Expected: command exits 0.

- [ ] **Step 4: Commit and push**

Commit with:

```bash
git add docs/superpowers/specs/2026-06-26-discovery-workspace-comfort-parity-design.md docs/superpowers/plans/2026-06-26-discovery-workspace-comfort-parity.md tests/contracts/test_static_builder.py packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py
git commit -m "Add discovery workspace overview"
git push origin new_rayalucaria
```
