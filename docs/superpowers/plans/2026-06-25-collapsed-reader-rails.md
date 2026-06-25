# Collapsed Reader Rails Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish the collapsed desktop reader rails so they read as intentional vertical tabs instead of cramped square controls.

**Architecture:** Keep behavior in the existing static shell script and styling in `packages/static/src/raya_static/rendering.py`. Use CSS pseudo-elements and existing buttons/links so the generated HTML remains simple and accessible.

**Tech Stack:** Python static builder, generated CSS/JS strings, Playwright e2e tests through `pytest`, static HTML output.

---

### Task 1: Add Collapsed Rail UX Regression Tests

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write the failing desktop test**

Add a test that opens `examples/courses/render-fixture`, collapses the course map and context rail, then evaluates computed styles for the collapsed tab labels and article width.

Expected assertions:
- `.raya-course-map-toggle::after` content is `"Map"`.
- `.raya-learning-rail-expand::after` content is `"Context"`.
- both pseudo-elements use a non-horizontal writing mode.
- article width grows after each collapse.
- map compact links remain focusable.
- right rail body is `aria-hidden="true"` and inert after context collapse.

- [ ] **Step 2: Write the mobile guard assertion**

Extend the existing mobile shell test so it asserts the desktop collapsed labels are not visible and the right rail body remains expanded/available on mobile.

- [ ] **Step 3: Run focused tests and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_collapsed_reader_rails_use_vertical_tabs tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading -q
```

Expected: the new desktop test fails because the current pseudo labels are `Nav` and `Info` and do not use vertical writing mode.

### Task 2: Implement Collapsed Rail Styling

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Update desktop collapsed map styling**

In the `@media (min-width: 1280px)` collapsed course-map section:
- Change the collapsed map column from `4.5rem` to a width that comfortably supports vertical tabs.
- Change `.raya-course-map-toggle::after` content from `Nav` to `Map`.
- Style the pseudo-element with vertical writing mode, upright text orientation, stable dimensions, and centered placement.
- Keep the button focusable and preserve the existing accessible label.

- [ ] **Step 2: Update desktop collapsed context styling**

In the collapsed learning-rail section:
- Change the collapsed rail column from `3.25rem` to a width that comfortably supports vertical tabs.
- Change `.raya-learning-rail-expand::after` content from `Info` to `Context`.
- Style the pseudo-element with vertical writing mode, upright text orientation, stable dimensions, and centered placement.
- Keep the collapsed rail body hidden and inert through existing JS state.

- [ ] **Step 3: Smooth the rail transition polish**

Add transition coverage for opacity, transform, border-color, and box-shadow under `html[data-raya-shell-ready="true"]`, while leaving `prefers-reduced-motion: reduce` as transition-free.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_collapsed_reader_rails_use_vertical_tabs tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading -q
```

Expected: both tests pass.

### Task 3: Update Contract and Role Docs

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Document the collapsed rail affordance**

Update the foundation renderer contract to say collapsed desktop rails become compact vertical tabs, remain operable, and stay non-persistent.

- [ ] **Step 2: Update student role docs**

Add one sentence in English and Spanish explaining that desktop readers can collapse map/context rails into vertical tabs to regain reading width.

- [ ] **Step 3: Update agent role docs**

Add one verification sentence in English and Spanish requiring agents to check vertical tabs, keyboard operability, mobile hiding, and no persistent storage.

### Task 4: Review, Verify, Commit

**Files:**
- All files changed in Tasks 1-3

- [ ] **Step 1: Run focused verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_collapsed_reader_rails_use_vertical_tabs tests/e2e/test_preview_static_read_path.py::test_render_fixture_top_context_command_toggles_right_rail_only tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading -q
```

- [ ] **Step 2: Run render-debug verification**

Run:

```bash
./scripts/check-render-debug.sh
```

- [ ] **Step 3: Request independent code review**

Dispatch a reviewer with the design and plan paths plus the commit diff.

- [ ] **Step 4: Run broader host gate**

Run:

```bash
./scripts/check.sh
```

- [ ] **Step 5: Commit**

Run:

```bash
git add docs/superpowers/specs/2026-06-25-collapsed-reader-rails-design.md docs/superpowers/plans/2026-06-25-collapsed-reader-rails.md tests/e2e/test_preview_static_read_path.py packages/static/src/raya_static/rendering.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/es/estudiantes/index.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md
git commit -m "Polish collapsed reader rails"
```

