# Graph Orientation Controls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the static graph workspace with denser controls and a more useful selected-page orientation card.

**Architecture:** Reuse the existing embedded graph payload and local `graph.js`. Add only public, build-time graph payload fields for Tasks/Schedule handoffs and render them in the existing inspector. Keep selectors stable where possible so current graph interactions continue to work.

**Tech Stack:** Python static builder, local SVG JavaScript, shared renderer CSS, pytest, Playwright.

---

### Task 1: Failing Graph Contract Coverage

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] Add contract assertions that graph HTML contains grouped toolbar containers: `raya-graph-toolbar`, `raya-graph-toolbar-primary`, `raya-graph-toolbar-viewport`, `raya-graph-toolbar-pan`, and `raya-graph-toolbar-state`.
- [x] Add contract assertions that graph detail scaffolding contains `data-raya-graph-detail-sequence`, `data-raya-graph-detail-previous`, `data-raya-graph-detail-current`, `data-raya-graph-detail-next`, `data-raya-graph-detail-tasks-link`, and `data-raya-graph-detail-schedule-link`.
- [x] Extend the graph payload allowed-key assertion to include `tasks_url` and `schedule_url`.
- [x] Assert a page without task-family objects has empty `tasks_url` and `schedule_url`.
- [x] Add fixture official task-family objects to a graph page and assert that page has `tasks_url` and `schedule_url` pointing to local `_raya/tasks/` and `_raya/schedule/` page-focused handoffs.
- [x] Add e2e assertions that selecting a graph node populates previous/current/next sequence text and shows or hides Tasks/Schedule links correctly.
- [x] Run focused graph tests and confirm they fail because the new toolbar/detail fields do not exist yet.

### Task 2: Builder Payload And Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [x] Add graph-payload support for `tasks_url` when the page has accepted public task-family objects.
- [x] Add graph-payload support for `schedule_url` when the page has accepted public task-family objects with `content.due` or `content.available`.
- [x] Group existing graph controls into toolbar sections without changing current IDs: search/layout, viewport controls, pan controls, and reset/expand.
- [x] Add selected-page sequence and optional task/schedule action anchors to graph detail markup.
- [x] Run focused contract tests and confirm payload/markup assertions pass.

### Task 3: Local Graph Behavior And Styling

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] Populate Previous, Current, and Next graph detail sequence links from selected node payload.
- [x] Populate Tasks and Schedule detail action links only when the selected node has non-empty URLs.
- [x] Keep detail metadata structural while adding sequence and action sections that avoid learner-state wording.
- [x] Style toolbar groups and detail card sections for dense desktop scanning and no mobile overflow.
- [x] Run focused e2e graph tests and confirm they pass.

### Task 4: Docs, Review, Verification

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify role docs only if the behavior needs user-facing guidance.

- [x] Document graph selected-page sequence and workspace handoffs as static structural discovery cues.
- [x] Request independent code review focused on static-resource boundaries, learner-state wording, and graph usability.
- [ ] Run `./scripts/check-render-debug.sh`.
- [ ] Run `./scripts/check.sh`.
- [ ] Commit and push to `origin/new_rayalucaria`.
