# Reading Focus And Graph Debug Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add a volatile reader focus command and hide graph debug readout behind an intentional disclosure.

**Architecture:** The reader shell already owns course-map and learning-rail collapse state, so focus mode should call those existing state paths instead of creating a second layout system. Graph debug markup stays generated static HTML and uses native `<details>` for disclosure.

**Tech Stack:** Python static renderer, local shell JavaScript, CSS custom properties, pytest, Playwright.

---

### Task 1: Reader Focus RED Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add a focused desktop behavior test**

Add assertions to the existing reader shell e2e area or create `test_render_fixture_reader_focus_command_collapses_map_and_rail`:

```python
def test_render_fixture_reader_focus_command_collapses_map_and_rail(tmp_path: Path) -> None:
    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    _run_cli(["build", str(course)])
    with _static_server(course / "artifact" / "site") as base_url:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(f"{base_url}/reader-ux/index.html")
                focus = page.locator("[data-raya-reader-focus-toggle]")
                assert focus.is_visible()
                assert focus.get_attribute("aria-pressed") == "false"
                focus.click()
                assert page.locator("html").get_attribute("data-raya-reader-focus") == "active"
                assert page.locator("#raya-course-map").get_attribute("data-raya-course-map") == "collapsed"
                assert page.locator("#raya-learning-rail").get_attribute("data-raya-rail-state") == "collapsed"
                assert focus.get_attribute("aria-pressed") == "true"
                storage = page.evaluate("() => [Object.keys(localStorage), Object.keys(sessionStorage)]")
                assert storage == [[], []]
                focus.click()
                assert page.locator("html").get_attribute("data-raya-reader-focus") == "inactive"
                assert page.locator("#raya-course-map").get_attribute("data-raya-course-map") == "expanded"
                assert page.locator("#raya-learning-rail").get_attribute("data-raya-rail-state") == "expanded"
            finally:
                browser.close()
```

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_focus_command_collapses_map_and_rail
```

Expected: fail because `[data-raya-reader-focus-toggle]` does not exist.

### Task 2: Reader Focus Implementation

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Render the command**

Add a command-bar button on reader pages:

```html
<button class="raya-command raya-command-focus" type="button" data-raya-reader-focus-toggle aria-pressed="false" aria-label="Focus reading">
  <span class="raya-command-icon" data-raya-command-icon="focus" aria-hidden="true"></span>
  <span class="raya-command-label">Focus reading</span>
</button>
```

- [x] **Step 2: Wire volatile shell behavior**

In `shell.py`, select `[data-raya-reader-focus-toggle]`, add `setReaderFocus(nextActive)`, and reuse existing `setExpanded(...)` plus the learning rail collapse/expand helpers. The function should set `root.dataset.rayaReaderFocus` to `active` or `inactive`, update `aria-pressed`, and never touch storage or URL state.

- [x] **Step 3: Style the command**

In `rendering.py`, style `.raya-command-focus` consistently with other command buttons and add a simple focus icon rule under the existing command icon block.

- [x] **Step 4: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_focus_command_collapses_map_and_rail
```

Expected: pass.

### Task 3: Graph Debug Disclosure RED/GREEN

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Add graph disclosure assertions**

Extend `test_preview_serves_local_visual_graph_surface` to assert:

```python
debug = page.locator("[data-raya-graph-debug]")
assert debug.is_visible()
assert debug.get_attribute("open") is None
assert page.locator("[data-raya-graph-copy-url]").count() == 1
debug.locator("summary").click()
assert debug.get_attribute("open") == ""
assert page.locator("[data-raya-graph-copy-url]").is_visible()
```

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
```

Expected: fail because the graph debug disclosure does not exist.

- [x] **Step 3: Render native details**

Wrap graph state readout and copy URL status in:

```html
<details class="raya-graph-debug" data-raya-graph-debug>
  <summary>Graph state</summary>
  ...
</details>
```

Keep the existing copy URL button and status inside the disclosure.

- [x] **Step 4: Verify GREEN**

Run the same focused test. Expected: pass.

### Task 4: Documentation, Review, Verification, Commit

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] **Step 1: Update docs**

Document reader focus as a volatile desktop comfort control, and graph debug disclosure as a local inspection affordance. Use structural language only.

- [x] **Step 2: Request review**

Ask an independent reviewer to inspect the diff for static-only behavior, accessibility, no storage except allowed comfort preferences, no URL-state drift, and no mobile hidden/inert rail regression.

- [x] **Step 3: Verify**

Run:

```bash
git diff --check
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_focus_command_collapses_map_and_rail tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: all commands exit 0.

- [x] **Step 4: Commit and push**

```bash
git add docs/superpowers/specs/2026-06-25-reading-focus-graph-debug-design.md docs/superpowers/plans/2026-06-25-reading-focus-graph-debug.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/shell.py packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/en/professors/index.md docs/guides/en/contributors/index.md docs/guides/en/agents/index.md docs/guides/es/estudiantes/index.md docs/guides/es/profesores/index.md docs/guides/es/colaboradores/index.md docs/guides/es/agentes/index.md
git commit -m "Add reader focus mode"
git push origin new_rayalucaria
```
