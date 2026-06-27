# Graph Orientation Fit Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a selected-page `Fit selection` action to the graph orientation band without changing graph data, URL state, storage, or renderer dependencies.

**Architecture:** Reuse the existing static graph HTML, `fitSelectedGraphContext()` JavaScript behavior, and fit-selection availability predicate. The orientation action is a second entry point into the same viewport-only behavior as the toolbar button.

**Tech Stack:** Python static builder, generated local JavaScript, Playwright e2e tests, pytest contract tests.

---

### Task 1: Failing Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add contract assertions**

In `tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface`, assert that generated graph HTML contains `data-raya-graph-orientation-fit-selection`, and that generated graph JavaScript contains `orientationFitSelection` and `orientationFitSelection.addEventListener("click", fitSelectedGraphContext)`.

- [ ] **Step 2: Add browser behavior test**

In `tests/e2e/test_preview_static_read_path.py`, add `test_render_fixture_graph_orientation_fit_selection_frames_context`. The test opens `_raya/graph/index.html?page=reader-ux`, verifies the orientation action is visible and enabled, enters a search query that still matches the selected page, moves the graph viewport away with zoom/pan controls, clicks the orientation action, and asserts:

- the SVG `viewBox` changed;
- the selected `reader-ux` node still exists and is visible in the canvas viewport;
- at least one connected edge is visible in the canvas viewport;
- the selected detail title remains visible;
- the search query remains `reader`;
- the page URL is unchanged;
- `localStorage` and `sessionStorage` keys remain empty.

- [ ] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_orientation_fit_selection_frames_context
```

Expected: fail because the orientation fit-selection button and JavaScript binding do not exist yet.

### Task 2: Builder Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add the orientation action**

Add this button to the existing `raya-graph-orientation-actions` markup after `Focus neighborhood` and before `Clear selection`:

```html
<button type="button" data-raya-graph-orientation-fit-selection hidden disabled>Fit selection</button>
```

- [ ] **Step 2: Run the contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface
```

Expected: still fail on missing JavaScript binding until Task 3 is complete.

### Task 3: Graph JavaScript Wiring

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`

- [ ] **Step 1: Select the orientation action**

Add:

```js
const orientationFitSelection = document.querySelector(
  "[data-raya-graph-orientation-fit-selection]"
);
```

- [ ] **Step 2: Share the fit-selection availability state**

Update `setFitSelectionEnabled()` so it computes `enabled` once, applies it to the toolbar button when present, and applies `hidden` plus `disabled` to `orientationFitSelection`.

- [ ] **Step 3: Reuse the existing viewport behavior**

Add:

```js
if (orientationFitSelection) {
  orientationFitSelection.addEventListener("click", fitSelectedGraphContext);
}
```

- [ ] **Step 4: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_orientation_fit_selection_frames_context
```

Expected: pass.

### Task 4: Focused Regression Gate

**Files:**
- Inspect only unless failures require fixes.

- [ ] **Step 1: Run graph-focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_orientation_fit_selection_frames_context \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_focus_mode_refits_selected_context \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_minimap_tracks_viewport \
  tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface
```

Expected: pass.

- [ ] **Step 2: Run render-debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: pass with no raw TeX leakage, no external renderer requests, no graph storage regressions, and no layout overflow regressions.

### Task 5: Review And Push

**Files:**
- Inspect diff and review output.

- [ ] **Step 1: Request independent review**

Ask a fresh subagent to review the diff for UX regressions, state persistence mistakes, foundation-contract drift, missing tests, and static deployment parity.

- [ ] **Step 2: Fix confirmed issues**

For any confirmed issue, write or update the failing test first, verify RED, implement the smallest fix, and rerun the focused gate.

- [ ] **Step 3: Final verification**

Run:

```bash
git diff --check
git status --short --branch
```

Expected: no whitespace errors and only intentional tracked changes before commit.

- [ ] **Step 4: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-27-graph-orientation-fit-selection-design.md \
  docs/superpowers/plans/2026-06-27-graph-orientation-fit-selection.md \
  packages/static/src/raya_static/builder.py \
  packages/static/src/raya_static/graph.py \
  tests/contracts/test_static_builder.py \
  tests/e2e/test_preview_static_read_path.py
git commit -m "Add orientation fit selection action"
git push origin new_rayalucaria
```
