# Discovery Workspace Reset Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `Escape` a reliable whole-workspace reset for Search, Practice, Tasks, and Schedule.

**Architecture:** Keep the existing static workspace pages and page-specific scripts. Add small reset helpers in each script so visible `Clear` and workspace `Escape` share the same reset path, while preserving query-input arrow/enter navigation and no-storage/no-fetch constraints.

**Tech Stack:** Python-generated static HTML, local JavaScript resource strings, Playwright e2e tests through `uv`.

**Status: implemented.** This checklist is a historical execution record. Current
source support lives in the Search, Practice, Tasks, and Schedule workspace
reset helpers, shared `Escape` handling, and focused browser tests.

---

## Files

- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `packages/static/src/raya_static/search.py`
- Modify: `packages/static/src/raya_static/practice.py`
- Modify: `packages/static/src/raya_static/tasks.py`
- Modify: `packages/static/src/raya_static/schedule.py`
- Verify: `examples/courses/render-fixture/artifact/site`

## Task 1: Add Failing Browser Coverage

- [ ] Add assertions that pressing `Escape` from a non-input Search result resets query/page focus and focuses `#raya-search-input`.
- [ ] Add assertions that pressing `Escape` from a non-input Practice object resets filters/page focus and focuses `#raya-practice-search`.
- [ ] Add assertions that pressing `Escape` from a non-input Tasks object resets type/page focus/sort and focuses `#raya-tasks-search`.
- [ ] Add assertions that pressing `Escape` from a non-input Schedule item resets type/date/page focus and focuses `#raya-schedule-search`.
- [ ] Run focused e2e tests and confirm the new assertions fail because `Escape` is only handled by the query input scripts.

## Task 2: Implement Minimal Reset Helpers

- [ ] In each workspace script, create a `reset...Workspace({ focusInput = true } = {})` helper or adapt the existing clear helper.
- [ ] Make the visible `Clear` button call that helper.
- [ ] Add a `keydown` listener on the workspace root for `Escape`.
- [ ] Ignore duplicate root handling when the query input handler already handled the event by checking `event.defaultPrevented`.
- [ ] For Tasks, ensure reset sets `sort.value = "course"`.
- [ ] Run the focused e2e tests and confirm they pass.

## Task 3: Verify Static Constraints

- [ ] Confirm workspace scripts still contain no `fetch(`, `XMLHttpRequest`, `localStorage`, or `sessionStorage`.
- [ ] Rebuild the render fixture and run `./scripts/check-render-debug.sh`.
- [ ] Run `./scripts/check.sh` and `./scripts/check-docker.sh` sequentially after focused gates pass.
- [ ] Request independent review for spec compliance and code quality.
