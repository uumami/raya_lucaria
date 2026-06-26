# Pre-Paint Comfort Restore Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore accepted reader comfort preferences before first paint.

**Architecture:** Add a small static helper in `packages/static/src/raya_static/accessibility.py`, emit it inline in reader-page heads before CSS links, and verify it works even when the deferred accessibility script is blocked.

**Tech Stack:** Python 3.10 static builder, generated HTML, local CSS/JS resources, pytest, Playwright.

**Status: implemented.** This checklist is a historical execution record. Current
source support lives in `packages/static/src/raya_static/accessibility.py`,
reader-page head generation in `packages/static/src/raya_static/builder.py`,
and focused browser tests.

---

### Task 1: RED Browser Coverage

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add pre-paint regression**

Add a browser test that seeds `localStorage` with `raya:open-dyslexic=true` and
`raya:text-size=x-large`, blocks `_raya/render/accessibility/open-dyslexic-toggle.js`,
opens `index.html`, and asserts the root attributes and CSS custom properties
already reflect the stored values.

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_restores_comfort_preferences_before_deferred_script -q
```

Expected before implementation: fail because the root element has no restored
comfort attributes when the deferred script is blocked.

### Task 2: Minimal Implementation

**Files:**
- Modify: `packages/static/src/raya_static/accessibility.py`
- Modify: `packages/static/src/raya_static/builder.py`

- [x] **Step 1: Add static helper**

Add `comfort_prepaint_script()` that reads only accepted comfort keys, validates
text size, catches storage failures, and writes root attributes.

- [x] **Step 2: Emit helper before CSS**

Insert `<script>{comfort_prepaint_script()}</script>` in normal reader-page
heads before stylesheet links. Do not add it to graph/discovery workspaces.

### Task 3: GREEN Verification

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Assert HTML order**

Extend the skin/accessibility test so `index.html` contains the pre-paint
storage reads before `rich.css`.

- [x] **Step 2: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_applies_course_and_section_skins tests/e2e/test_preview_static_read_path.py::test_render_fixture_open_dyslexic_toggle_changes_computed_font tests/e2e/test_preview_static_read_path.py::test_render_fixture_restores_comfort_preferences_before_deferred_script -q
```

Expected: pass.
