# Course Shell Workspace Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the static reading shell so desktop pages feel like a cohesive learning workspace and mobile pages keep controls compact.

**Architecture:** Keep the current Python static renderer and local shell JavaScript. Make the smallest CSS/test changes needed to enforce compact mobile command chrome while preserving current desktop shell behavior.

**Tech Stack:** Python 3.10, pytest, Playwright, current `raya_static` renderer resources.

---

### Task 1: Add Mobile Command-Bar Regression Coverage

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write the failing test assertion**

Add an assertion in `test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading` after page load:

```python
topbar = _bounding_box(page, ".raya-top-command-bar")
assert topbar["height"] <= 220
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading -q
```

Expected before implementation: failure because the main reading command bar is too tall on a 390px viewport.

### Task 2: Compact Main Reading Tools on Small Screens

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Patch responsive CSS**

Inside the `@media (max-width: 520px)` block, give normal reading pages the same compact command treatment as discovery pages:

```css
.raya-top-command-bar:not(.raya-discovery-command-bar) .raya-course-tools {
  flex-wrap: nowrap;
  justify-content: flex-start;
  overflow-x: auto;
}
.raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command {
  min-width: 2.5rem;
  padding: 0.45rem;
}
.raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-label {
  clip: rect(0 0 0 0);
  height: 1px;
  overflow: hidden;
  position: absolute;
  white-space: nowrap;
  width: 1px;
}
```

- [ ] **Step 2: Run focused test to verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading -q
```

Expected after implementation: pass.

### Task 3: Verify Shell Slice

**Files:**
- Read-only verification

- [ ] **Step 1: Run focused shell tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_desktop_shell_has_modern_workspace_chrome tests/e2e/test_preview_static_read_path.py::test_render_fixture_balanced_workspace_visual_hierarchy tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading -q
```

- [ ] **Step 2: Run render debug gate**

```bash
./scripts/check-render-debug.sh
```

- [ ] **Step 3: Check git status**

```bash
git status --short --branch
```
