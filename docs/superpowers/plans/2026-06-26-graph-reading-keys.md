# Graph Reading Keys Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add compact first-viewport Graph reading keys that explain graph marks and interactions without adding state or dependencies.

**Architecture:** Generate static reading-key markup near the top of the Graph page, style it in the shared renderer CSS, and verify with focused contract/browser tests. Keep the existing detailed graph guide, legend, URL state, and local-only behavior intact. Apply only the graph-script cleanup needed to prevent stale inspection previews after filters hide graph nodes.

**Tech Stack:** Python static builder, generated HTML/CSS, pytest, Playwright, Superpowers design/plan docs.

**Status: implemented.** This checklist is a historical execution record. Current
source support lives in Graph reading-key markup, stale-preview cleanup in
`packages/static/src/raya_static/graph.py`, shared CSS, and focused tests.

---

## File Structure

- `packages/static/src/raya_static/builder.py` generates the Graph workspace HTML and will add the static reading-key strip near the Graph header.
- `packages/static/src/raya_static/graph.py` owns static Graph interactions and will keep inspection previews aligned with the active filtered graph.
- `packages/static/src/raya_static/rendering.py` owns Graph layout CSS and will style the compact cards.
- `tests/e2e/test_preview_static_read_path.py` owns browser-visible graph tests and will verify placement and wording.
- `tests/contracts/test_static_builder.py` owns static generated HTML contract checks and will verify the generated attributes/text.
- `docs/foundation/20_learning_renderer_contract.md` documents accepted static graph orientation behavior.
- `docs/guides/en/students/index.md` and `docs/guides/es/estudiantes/index.md` document student-facing Graph reading cues.

## Task 1: Static Graph Reading Keys Markup

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `packages/static/src/raya_static/builder.py`

- [x] **Step 1: Write the failing contract assertions**

In `tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface`, add assertions that `graph_html` contains:

```python
assert 'data-raya-graph-reading-keys' in graph_html
for label in ("Pages", "Arrows", "Selection", "Filters"):
    assert f'data-raya-graph-reading-key="{label.lower()}"' in graph_html
assert "circles are course pages" in graph_html
assert "arrows point from source page to target page" in graph_html
assert "hide visible graph marks only" in graph_html
```

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: fail because the Graph HTML does not yet include the reading-key strip.

- [x] **Step 3: Add generated reading-key markup**

In `packages/static/src/raya_static/builder.py`, immediately after the Graph
header and before the graph controls, add:

```python
(
    '<section class="raya-graph-reading-keys" '
    'data-raya-graph-reading-keys aria-label="Graph reading keys">'
    '<article data-raya-graph-reading-key="pages">'
    "<h2>Pages</h2>"
    "<p>Circles are course pages. Color follows generated course groups.</p>"
    "</article>"
    '<article data-raya-graph-reading-key="arrows">'
    "<h2>Arrows</h2>"
    "<p>Arrows point from source page to target page.</p>"
    "</article>"
    '<article data-raya-graph-reading-key="selection">'
    "<h2>Selection</h2>"
    "<p>Click once to inspect. Double-click or press Enter to open.</p>"
    "</article>"
    '<article data-raya-graph-reading-key="filters">'
    "<h2>Filters</h2>"
    "<p>Relationship filters hide visible graph marks only. Source data stays unchanged.</p>"
    "</article>"
    "</section>"
)
```

Keep wording structural and non-personal.

- [x] **Step 4: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Expected: pass.

## Task 2: First-Viewport Styling And Browser Checks

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Write failing browser assertions**

In the graph first-viewport/browser test block in
`tests/e2e/test_preview_static_read_path.py`, assert:

```python
reading_keys = page.locator("[data-raya-graph-reading-keys]")
assert reading_keys.is_visible()
reading_keys_box = reading_keys.bounding_box()
canvas_box = page.locator("#raya-graph-canvas").bounding_box()
orientation_box = page.locator("[data-raya-graph-orientation]").bounding_box()
assert reading_keys_box is not None
assert canvas_box is not None
assert orientation_box is not None
assert reading_keys_box["y"] < orientation_box["y"]
assert reading_keys_box["y"] < canvas_box["y"]
assert reading_keys_box["height"] <= 140
assert reading_keys_box["y"] < viewport["height"]
assert reading_keys_box["y"] + reading_keys_box["height"] <= viewport["height"]
for key in ("pages", "arrows", "selection", "filters"):
    assert page.locator(f'[data-raya-graph-reading-key="{key}"]').is_visible()
reading_text = reading_keys.inner_text().lower()
for forbidden in ("progress", "mastery", "ranking", "recommendation", "personalization"):
    assert forbidden not in reading_text
```

Also keep the existing assertion that `data-raya-graph-guide` remains a closed
native disclosure and its cards are hidden before opening.

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: fail because the reading-key strip is missing or unstyled.

- [x] **Step 3: Add CSS**

In `packages/static/src/raya_static/rendering.py`, near the graph orientation
and guide CSS, add:

```css
.raya-graph-reading-keys {
  display: grid;
  gap: 0.45rem;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin: 0 0 0.55rem;
}
.raya-graph-reading-keys article {
  background: color-mix(in srgb, var(--raya-color-surface) 88%, transparent);
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 84%, transparent);
  border-radius: 0.375rem;
  min-width: 0;
  padding: 0.5rem 0.58rem;
}
.raya-graph-reading-keys h2 {
  color: var(--raya-color-heading);
  font-size: 0.74rem;
  letter-spacing: 0;
  margin: 0 0 0.18rem;
}
.raya-graph-reading-keys p {
  color: var(--raya-color-muted);
  font-size: 0.68rem;
  line-height: 1.25;
  margin: 0;
}
@media (max-width: 900px) {
  .raya-graph-reading-keys {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 520px) {
  .raya-graph-reading-keys {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
```

- [x] **Step 4: Keep filter inspection previews consistent**

If the browser test reveals that hiding a group can leave or reopen an
inspection preview for a no-longer-visible graph node, update
`packages/static/src/raya_static/graph.py` so inspection previews only show
active graph nodes, pending selection timers are cleared on group-filter
changes, and hover inspection is briefly suppressed during filter rerenders.

- [x] **Step 5: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: pass.

## Task 3: Documentation And Full Verification

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`

- [x] **Step 1: Document the behavior**

Add one sentence to the graph paragraph in
`docs/foundation/20_learning_renderer_contract.md` stating that the graph may
show compact first-viewport reading keys for page nodes, arrows, selection, and
filters.

Add student-role guidance in English and Spanish explaining that the Graph page
shows quick reading keys near the canvas and that they are structural cues, not
progress or recommendations.

- [x] **Step 2: Run focused verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
./scripts/check-render-debug.sh
```

Expected: focused tests pass and render-debug reports passed checks.

- [x] **Step 3: Request independent review**

Ask a reviewer to check the implementation against this plan, current
foundation constraints, and legacy UX convergence goals.

- [ ] **Step 4: Run archive gates and push**

Run sequentially:

```bash
./scripts/check.sh
./scripts/check-docker.sh
git status --short --branch
git add docs/superpowers/specs/2026-06-26-graph-reading-keys-design.md docs/superpowers/plans/2026-06-26-graph-reading-keys.md tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py packages/static/src/raya_static/builder.py packages/static/src/raya_static/graph.py packages/static/src/raya_static/rendering.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/es/estudiantes/index.md
git commit -m "Add graph reading keys"
git push origin new_rayalucaria
```

Expected: both gates pass, the working tree is clean after commit, and the
branch pushes to `origin/new_rayalucaria`.

## Self-Review

- Spec coverage: The plan covers generated markup, visible styling, contract
  and browser checks, foundation/student docs, review, and host/Docker gates.
- Placeholder scan: No placeholders or deferred implementation steps remain.
- Type consistency: Data attributes and class names match across builder, CSS,
  and tests.
