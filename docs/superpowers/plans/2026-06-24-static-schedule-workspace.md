# Static Schedule Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a static Schedule discovery workspace over accepted dated official task metadata.

**Architecture:** Reuse the existing official task extraction and embedded payload pattern. Add `_raya/schedule/index.html` and a local `schedule.js` resource, without adding a new artifact data contract or source schema.

**Tech Stack:** Python static builder, embedded local JavaScript resource module, static CSS in `rendering.py`, pytest, Playwright e2e.

---

### Task 1: Failing Contract Coverage

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] Add a builder contract test beside `test_build_writes_static_official_tasks_workspace` that copies the minimal fixture, calls `_add_official_task_objects(course)`, builds, and asserts `_raya/schedule/index.html` and `_raya/render/schedule.js` exist.
- [x] Assert the Schedule HTML includes dated public task objects such as `unit-assignment`, `unit-project`, and `unit-exam`.
- [x] Assert the Schedule HTML excludes the undated `unit-task`, the private-path string `_official`, `SHOULD_NOT_LEAK`, external URLs, `fetch(`, `XMLHttpRequest`, `localStorage`, and `sessionStorage`.
- [x] Assert discovery chrome links include Search, Graph, Practice, Tasks, and omit a self-link for Schedule.
- [x] Extend the reader shell/course-map e2e coverage to expect five workspace cards: Search, Graph, Practice, Tasks, Schedule.
- [x] Run the focused contract/e2e tests and confirm they fail because Schedule does not exist yet.

### Task 2: Resource And Builder Surface

**Files:**
- Create: `packages/static/src/raya_static/schedule.py`
- Modify: `packages/static/src/raya_static/builder.py`

- [x] Add `SCHEDULE_SCRIPT_NAME = "schedule.js"` and `SCHEDULE_RESOURCE_PATH = "_raya/render"` in the new module.
- [x] Implement local JavaScript equivalent to the Tasks workspace pattern: parse `#raya-schedule-data`, filter by search, task type, and event kind, update visible counts, update context, support ArrowUp/ArrowDown/Enter/Escape, and avoid all storage/fetch APIs.
- [x] Add `STATIC_SCHEDULE_PATH = Path("_raya") / "schedule" / "index.html"` to the builder.
- [x] Add `_write_schedule_resources(site_dir, report)` and call it beside tasks resources.
- [x] Add `_schedule_items_payload(content_model, official_by_page)` that derives from `_browser_tasks_payload(...)["objects"]` and keeps only items where `due` or `available` is non-empty.
- [x] Add `_render_schedule_surface(...)` and `_write_schedule_surface(...)` that render shared discovery chrome, controls, cards, context panel, embedded JSON payload, `schedule.js`, local rich/skin/accessibility CSS, and volatile OpenDyslexic controls.
- [x] Wire Schedule links into reader command bars, discovery command bars, and course-map workspace cards with a direct-page `N dated` badge.
- [x] Run focused tests and confirm the new surface passes.

### Task 3: Styling And Browser Behavior

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] Add `.raya-schedule-*` CSS using the existing Tasks/Practice grid pattern: page shell, header, workspace, control panel, results panel, context panel, chips, cards, active card, meta, tags, actions, hidden state, mobile layout, and print behavior.
- [x] Extend e2e static preview coverage to open `_raya/schedule/index.html` on desktop and mobile, assert no horizontal overflow, local requests only, visible command bar, visible controls/results/context, keyboard/search/filter behavior, volatile OpenDyslexic/text-size behavior, and no storage writes.
- [x] Run focused e2e tests and confirm they pass.

### Task 4: Documentation, Review, Verification

**Files:**
- Modify: `docs/foundation/06_artifact_contract.md`
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] Document Schedule as a static dated-task view over accepted official task metadata, not a calendar feed, sync surface, reminder system, progress marker, or recommendation.
- [x] Request independent code review focused on current renderer principles and no-state/static-resource boundaries.
- [x] Run focused tests.
- [x] Run `./scripts/check-render-debug.sh`.
- [x] Run `./scripts/check.sh`.
- [x] Commit and push to `origin/new_rayalucaria`.
