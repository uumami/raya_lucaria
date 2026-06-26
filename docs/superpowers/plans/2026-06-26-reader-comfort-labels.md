# Reader Comfort Labels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make reader text-size and OpenDyslexic controls visibly named at normal desktop widths.

**Architecture:** This is a CSS-only renderer change. The generated command markup, JavaScript storage behavior, and source/artifact contracts remain unchanged.

**Tech Stack:** Python-generated static CSS, Playwright e2e tests through `uv`.

---

### Task 1: Failing Comfort Label Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Write the failing test**

Add a focused e2e test that opens `examples/courses/render-fixture` at
`/reader-ux/index.html`.

At `1366x900`, assert:

```python
size_label = page.locator(".raya-command-size .raya-command-label")
font_label = page.locator(".raya-command-font .raya-command-label")
assert size_label.bounding_box()["width"] >= 48
assert font_label.bounding_box()["width"] >= 80
assert page.evaluate("() => document.documentElement.scrollWidth <= document.documentElement.clientWidth")
```

At `390x844`, assert the labels remain visually clipped:

```python
assert size_label.bounding_box()["width"] <= 2
assert font_label.bounding_box()["width"] <= 2
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_reader_comfort_labels_are_visible_on_desktop_only -q
```

Expected: FAIL because desktop comfort labels are clipped to 1px.

### Task 2: CSS Implementation

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Add desktop-only comfort label override**

Inside the existing `@media (max-width: 1500px)` rules, add an override for
reader command bars:

```css
.raya-top-command-bar:not(.raya-discovery-command-bar)
  .raya-command-group-comfort .raya-command-label {
  clip: auto;
  height: auto;
  overflow: visible;
  position: static;
  white-space: nowrap;
  width: auto;
}
```

Then keep the existing `@media (max-width: 520px)` clipping rule as the mobile
override.

- [x] **Step 2: Run test to verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_reader_comfort_labels_are_visible_on_desktop_only -q
```

Expected: PASS.

### Task 3: Verification And Delivery

**Files:**
- Verify modified files from Tasks 1 and 2.

- [x] **Step 1: Run focused command-bar tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_reader_comfort_labels_are_visible_on_desktop_only tests/e2e/test_preview_static_read_path.py::test_render_fixture_command_bar_controls_are_dense_and_operable -q
```

Expected: PASS.

- [x] **Step 2: Rebuild render fixture**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture
```

Expected: build passes and writes `examples/courses/render-fixture/artifact/site`.

- [x] **Step 3: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-reader-comfort-labels-design.md docs/superpowers/plans/2026-06-26-reader-comfort-labels.md packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py
git commit -m "Show reader comfort labels on desktop"
git push origin new_rayalucaria
```

Expected: commit is pushed to `origin/new_rayalucaria`.
