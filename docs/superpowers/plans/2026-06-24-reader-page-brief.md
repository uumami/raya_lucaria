# Reader Page Brief Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development or local TDD execution. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a compact static Page brief near the start of reader pages so
students can quickly see page summary, status, position, prerequisites,
connections, and available official practice.

**Architecture:** Add a `_render_page_brief()` helper in
`packages/static/src/raya_static/builder.py`, call it from `_render_page()` after
breadcrumbs and before authored content, style it in
`packages/static/src/raya_static/rendering.py`, and document it in foundation and
role docs.

**Tech Stack:** Python static builder, generated HTML/CSS, pytest contract tests,
Playwright-backed e2e tests.

---

### Task 1: Contract Test For Page Brief

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Test: `tests/contracts/test_static_builder.py`

- [ ] Add failing assertions against `examples/courses/render-fixture` proving
  `reader-ux/index.html` renders:
  - `section.raya-page-brief`;
  - the page summary;
  - status, structural page position, estimated time, and tags;
  - a resolved prerequisite link;
  - explicit graph connection counts and a page-focused graph link;
  - an official-practice anchor when accepted objects exist;
  - no recommendation/progress/mastery wording, private paths, fetches, storage,
    or external URLs.
- [ ] Run the focused test and confirm RED.

### Task 2: Implement Page Brief Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Test: `tests/contracts/test_static_builder.py`

- [ ] Add `_render_page_brief()` and small helpers for brief facts.
- [ ] Reuse current `official_counts`, `content_model`, and
  `page_graph_context`.
- [ ] Call the helper in `_render_page()` after breadcrumbs.
- [ ] Run the focused contract test and confirm GREEN.

### Task 3: Style And Browser Verify The Brief

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] Add responsive brief CSS using existing skin variables.
- [ ] Add or extend a browser static-read-path test proving desktop/mobile
  visibility, no horizontal overflow, and same-origin static requests.
- [ ] Run the focused browser test and confirm GREEN.

### Task 4: Documentation

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: role docs under `docs/guides/en/` and `docs/guides/es/`

- [ ] Document the brief as current static shell behavior.
- [ ] Explain for each role that it uses accepted metadata only and does not
  imply progress, recommendations, grading, or personalization.

### Task 5: Review And Verification

**Files:**
- No planned edits unless review finds issues.

- [ ] Request code review for the completed renderer/docs change.
- [ ] Address verified review findings.
- [ ] Run focused tests, `./scripts/check-render-debug.sh`, `./scripts/check.sh`,
  and `./scripts/check-docker.sh` sequentially.
- [ ] Commit and push to `origin/new_rayalucaria`.
