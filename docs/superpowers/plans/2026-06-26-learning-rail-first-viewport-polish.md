# Learning Rail First-Viewport Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep the desktop right learning rail visibly useful in the first viewport and preserve compact rail collapse behavior.

**Architecture:** Add a Playwright regression around the render fixture's `reader-ux/` page, then fix the CSS grid sizing invariant in the static renderer stylesheet. The generated HTML and shell JavaScript stay unchanged unless the regression shows a second root cause.

**Tech Stack:** Python 3.10, `uv`, Playwright, Glintstone static renderer CSS generated from `packages/static/src/raya_static/rendering.py`.

**Status: implemented.** This checklist is a historical execution record. Current
source support lives in reader shell/rail CSS in `packages/static/src/raya_static/rendering.py`
and focused first-viewport/collapse Playwright tests in
`tests/e2e/test_preview_static_read_path.py`.

---

### Task 1: Add Failing Rail Visibility Regression

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write the failing test**

Add this test near `test_render_fixture_collapsed_reader_rails_use_compact_horizontal_tabs`:

```python
def test_render_fixture_learning_rail_content_starts_in_first_viewport(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        assert handle.base_url is not None
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 950})
                try:
                    page.goto(
                        f"{handle.base_url}/reader-ux/index.html",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(page)
                    probe = page.evaluate(
                        """() => {
                          const rail = document.querySelector('#raya-learning-rail');
                          const header = rail?.querySelector('.raya-learning-rail-header');
                          const body = rail?.querySelector('#raya-learning-rail-body');
                          const firstPanel = rail?.querySelector('.raya-rail-panel');
                          const firstPanelBody = firstPanel?.querySelector('.raya-rail-panel-body');
                          const viewportHeight = window.innerHeight;
                          const box = (node) => {
                            const rect = node?.getBoundingClientRect();
                            return rect
                              ? { top: rect.top, bottom: rect.bottom, height: rect.height }
                              : null;
                          };
                          return {
                            railText: rail?.innerText || '',
                            railTop: rail?.getBoundingClientRect().top || 0,
                            header: box(header),
                            body: box(body),
                            firstPanel: box(firstPanel),
                            firstPanelBody: box(firstPanelBody),
                            viewportHeight,
                            railState: rail?.getAttribute('data-raya-learning-rail'),
                            bodyHidden: body?.getAttribute('aria-hidden'),
                          };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert "Learning context" in probe["railText"]
    assert "Summary" in probe["railText"]
    assert probe["railState"] == "expanded"
    assert probe["bodyHidden"] == "false"
    assert probe["header"]["top"] < 140
    assert probe["body"]["top"] < 190
    assert probe["firstPanel"]["top"] < 210
    assert probe["firstPanelBody"]["top"] < 260
    assert probe["firstPanelBody"]["bottom"] < probe["viewportHeight"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_learning_rail_content_starts_in_first_viewport -q
```

Expected: FAIL because `body.top`, `firstPanel.top`, and `firstPanelBody.top` are far below the first viewport.

### Task 2: Fix Rail Grid Stretching

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Add the minimal CSS invariant**

In the `.raya-learning-rail` CSS block near the shell layout rules, add:

```css
  align-content: start;
  align-self: start;
```

In the later `.raya-learning-rail` display block near the rail panel rules, keep `display: grid` but add:

```css
  align-content: start;
```

- [ ] **Step 2: Run focused test to verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_learning_rail_content_starts_in_first_viewport -q
```

Expected: PASS.

### Task 3: Focused Regression Around Collapse

**Files:**
- No new files.

- [ ] **Step 1: Run existing collapse/layout test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_collapsed_reader_rails_use_compact_horizontal_tabs -q
```

Expected: PASS, proving the compact `Context` tab behavior still works.

- [ ] **Step 2: Run related reader UX test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_ux_page_uses_scannable_static_numbering -q
```

Expected: PASS, proving the reader fixture still renders math, numbered content, and static environments.

### Task 4: Visual Debug Gate and Commit

**Files:**
- Modify: `docs/superpowers/specs/2026-06-26-learning-rail-first-viewport-polish-design.md`
- Modify: `docs/superpowers/plans/2026-06-26-learning-rail-first-viewport-polish.md`
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Run render debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS with no horizontal overflow, missing screenshots, raw TeX leakage, external renderer requests, or static parity failures.

- [ ] **Step 2: Restart local preview**

Run:

```bash
pkill -f "raya preview examples/courses/render-fixture --host 127.0.0.1 --port 46400" || true
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --host 127.0.0.1 --port 46400
```

Expected: preview serves `http://127.0.0.1:46400/index.html`.

- [ ] **Step 3: Commit**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-learning-rail-first-viewport-polish-design.md docs/superpowers/plans/2026-06-26-learning-rail-first-viewport-polish.md packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py
git commit -m "Keep learning rail content in first viewport"
git push origin new_rayalucaria
```
