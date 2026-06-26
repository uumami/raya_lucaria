# Reading Flow Rail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an expanded `Reading flow` rail panel that combines sequence and graph context.

**Architecture:** Reuse existing static builder data and rail panel helpers. Add tests first, then add one new render helper and small CSS refinements.

**Tech Stack:** Python 3.10, static HTML/CSS builder, pytest, Playwright.

---

### Task 1: Contract Coverage

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add failing contract test**

Add `test_render_fixture_learning_rail_exposes_reading_flow_panel` that builds
the render fixture and asserts `reader-ux/index.html` contains:

```python
'<section class="raya-rail-panel raya-page-reading-flow"' in html
'data-raya-rail-panel-state="expanded"' in reading_flow
'aria-expanded="true"' in reading_flow
'aria-hidden="false"' in reading_flow
'data-raya-prev-page' in reading_flow
'data-raya-next-page' in reading_flow
'from this page' in reading_flow
'links here' in reading_flow
'Open in course graph' in reading_flow
```

Also assert the rail no longer includes separate `raya-page-linked-pages` or
`raya-page-sequence` panels on that page, and the panel text does not contain
`progress`, `mastery`, `recommend`, `localStorage`, `sessionStorage`, or
`fetch(`.

- [ ] **Step 2: Run RED**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_render_fixture_learning_rail_exposes_reading_flow_panel
```

Expected: FAIL before implementation.

### Task 2: Builder Implementation

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Add helper**

Add `_render_reading_flow_rail(page, content_model, page_graph_context, graph_href)`.
It should return `""` if there are no sequence targets and no graph context.
Otherwise it returns `_render_rail_panel("raya-page-reading-flow", "Reading flow", body, expanded=True)`.

- [ ] **Step 2: Use helper in rail composition**

In `_render_learning_rail`, insert the reading-flow panel immediately after
summary/status/time. Remove the separate linked-pages and sequence rail calls
when reading-flow exists to avoid duplicate rail links.

- [ ] **Step 3: Add CSS**

Add compact classes:

- `.raya-reading-flow-grid`;
- `.raya-reading-flow-link`;
- `.raya-reading-flow-graph`;
- `.raya-reading-flow-counts`;
- `.raya-reading-flow-connections`.

Use existing skin tokens and small bordered chips.

- [ ] **Step 4: Run contract GREEN**

Run the focused contract test. Expected: PASS.

### Task 3: Browser Coverage

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add browser test**

Add `test_render_fixture_reading_flow_panel_is_visible_in_first_viewport`:

- open `/reader-ux/index.html` at `1440x950`;
- assert no horizontal overflow;
- assert `.raya-page-reading-flow` is visible and starts in the first viewport;
- assert previous, next, and graph links have nonzero boxes;
- assert graph context counts are visible;
- assert all requests are local.

- [ ] **Step 2: Run browser GREEN**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_reading_flow_panel_is_visible_in_first_viewport
```

Expected: PASS.

### Task 4: Verification and Review

**Files:**
- Commit docs, builder, rendering CSS, contract test, e2e test.

- [ ] **Step 1: Focused verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_render_fixture_learning_rail_exposes_reading_flow_panel \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_reading_flow_panel_is_visible_in_first_viewport \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_learning_shell_layout_and_accessibility \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_collapsed_reader_rails_use_compact_horizontal_tabs
./scripts/check-render-debug.sh
git diff --check
```

- [ ] **Step 2: Independent review**

Ask a reviewer to inspect duplication, first-viewport behavior, static contract
fit, and absence of progress/personalization/runtime claims.

- [ ] **Step 3: Commit and push**

```bash
git add docs/superpowers/specs/2026-06-26-reading-flow-rail-design.md \
  docs/superpowers/plans/2026-06-26-reading-flow-rail.md \
  packages/static/src/raya_static/builder.py \
  packages/static/src/raya_static/rendering.py \
  tests/contracts/test_static_builder.py \
  tests/e2e/test_preview_static_read_path.py
git commit -m "Add reading flow rail panel"
git push origin new_rayalucaria
```
