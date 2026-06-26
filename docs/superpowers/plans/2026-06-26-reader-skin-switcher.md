# Reader Skin Switcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add reader-facing local skin cycling without changing authored course skin truth.

**Architecture:** Extend generated `skin.css` with `html[data-raya-skin-override]` selectors, add local prepaint and toggle JavaScript resources, and add one command button to the reader comfort group. The body `data-raya-skin` remains canonical generated artifact truth.

**Tech Stack:** Python 3.10, pytest, Playwright, generated static HTML/CSS/JS.

---

### Task 1: Skin CSS Override Contract

**Files:**
- Modify: `tests/contracts/test_static_skins.py`
- Modify: `packages/static/src/raya_static/skins.py`

- [ ] **Step 1: Write failing contract test**

Add an assertion to `test_render_skin_css_is_deterministic_and_writes_token_variables` that `render_skin_css()` emits:

```python
'[data-raya-skin="a-skin"]' in css
':root[data-raya-skin-override="a-skin"]' in css
```

- [ ] **Step 2: Run RED**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_skins.py::test_render_skin_css_is_deterministic_and_writes_token_variables
```

Expected: FAIL before implementation.

- [ ] **Step 3: Implement CSS selector pair**

Update `render_skin_css()` so each skin block targets both:

```css
[data-raya-skin="<id>"],
:root[data-raya-skin-override="<id>"] {
  ...
}
```

- [ ] **Step 4: Run GREEN**

Run the same focused contract test. Expected: PASS.

### Task 2: Generated Skin Toggle Resources

**Files:**
- Modify: `packages/static/src/raya_static/skins.py`
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write failing builder assertions**

In `test_render_fixture_builds_rich_static_pages`, assert:

```python
skin_prepaint_js = site_dir / "_raya" / "render" / "skin-prepaint.js"
skin_toggle_js = site_dir / "_raya" / "render" / "skin-toggle.js"
assert skin_prepaint_js.is_file()
assert skin_toggle_js.is_file()
assert "raya:skin-override" in skin_prepaint_js.read_text(encoding="utf-8")
assert "raya:skin-override" in skin_toggle_js.read_text(encoding="utf-8")
assert "fetch(" not in skin_toggle_js.read_text(encoding="utf-8")
assert 'src="_raya/render/skin-prepaint.js"' in html
assert 'src="_raya/render/skin-toggle.js"' in html
assert 'localStorage.getItem("raya:skin-override")' not in html
assert 'class="raya-command raya-command-skin raya-skin-toggle"' in html
```

- [ ] **Step 2: Run RED**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages
```

Expected: FAIL before implementation.

- [ ] **Step 3: Implement resources and button**

Add constants/functions in `skins.py`:

- `SKIN_PREPAINT_JS_NAME = "skin-prepaint.js"`;
- `SKIN_TOGGLE_JS_NAME = "skin-toggle.js"`;
- `skin_prepaint_script()`;
- `skin_toggle_script()`;
- `skin_cycle_entries(context)`.

Update `builder.py` to:

- write both scripts under `_raya/render/`;
- include prepaint before `skin.css`;
- include deferred toggle script after shell/accessibility scripts;
- add a `Skin` command button to the comfort group with `data-raya-skin-cycle`
  and `data-raya-skin-labels`.

- [ ] **Step 4: Run GREEN**

Run the same focused builder test. Expected: PASS.

### Task 3: Browser Behavior

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add failing browser test**

Add `test_render_fixture_skin_toggle_cycles_local_override`:

- open `/reader-ux/index.html`;
- assert body `data-raya-skin` starts as `practice-lab`;
- record computed `--raya-color-accent`;
- click `.raya-skin-toggle`;
- assert `html[data-raya-skin-override]` is non-empty;
- assert body `data-raya-skin` is still `practice-lab`;
- assert computed accent changed;
- reload and assert override persisted;
- click until authored state returns and assert override is removed;
- assert all requests start with the preview base URL.

- [ ] **Step 2: Run RED/GREEN**

Run the new e2e test before and after implementation:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_skin_toggle_cycles_local_override
```

Expected: FAIL before implementation, PASS after.

### Task 4: Verification, Review, Commit

**Files:**
- Commit all modified docs, tests, and implementation files.

- [ ] **Step 1: Focused verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_skins.py tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages tests/e2e/test_preview_static_read_path.py::test_render_fixture_skin_toggle_cycles_local_override tests/e2e/test_preview_static_read_path.py::test_render_fixture_applies_course_and_section_skins
./scripts/check-render-debug.sh
git diff --check
```

- [ ] **Step 2: Independent review**

Ask a reviewer to inspect:

- authored `data-raya-skin` remains canonical;
- override selector and scripts are local/static;
- no external requests or inline storage code in HTML;
- persistence is limited to `raya:skin-override`;
- tests prove behavior without overfitting.

- [ ] **Step 3: Commit, push, refresh URL**

```bash
git add docs/superpowers/specs/2026-06-26-reader-skin-switcher-design.md \
  docs/superpowers/plans/2026-06-26-reader-skin-switcher.md \
  packages/static/src/raya_static/skins.py \
  packages/static/src/raya_static/builder.py \
  tests/contracts/test_static_skins.py \
  tests/contracts/test_static_builder.py \
  tests/e2e/test_preview_static_read_path.py
git commit -m "Add reader skin switcher"
git push origin new_rayalucaria
```
