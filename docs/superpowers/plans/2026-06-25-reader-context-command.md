# Reader Context Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a desktop top-bar command that toggles the right learning context rail without hiding the course map.

**Architecture:** Reuse the existing right-rail collapse state and focus management. The builder emits one additional command button; the shell treats all learning-rail controls as one synchronized control set; CSS hides the command on non-desktop layouts where the rail must remain expanded.

**Tech Stack:** Python static builder, generated CSS/JavaScript resources, pytest contract tests, Playwright e2e tests, English/Spanish Markdown role docs.

---

## File Structure

- Modify `packages/static/src/raya_static/builder.py`: emit the top-bar `Context` command with `data-raya-learning-rail-toggle`.
- Modify `packages/static/src/raya_static/shell.py`: synchronize top-bar, rail-collapse, and rail-expand controls through the existing right-rail state.
- Modify `packages/static/src/raya_static/rendering.py`: hide the top-bar context command below desktop width and include it in reduced-motion transition rules if needed.
- Modify `tests/contracts/test_static_builder.py`: assert markup and script hooks.
- Modify `tests/e2e/test_preview_static_read_path.py`: assert desktop toggle behavior and mobile hidden behavior.
- Modify `docs/foundation/20_learning_renderer_contract.md`: document top-bar context toggling as static comfort state.
- Modify `docs/guides/en/students/index.md`, `docs/guides/en/agents/index.md`, `docs/guides/es/estudiantes/index.md`, and `docs/guides/es/agentes/index.md`: describe learner use and agent checks.

## Task 1: Static Markup And Script Contract

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/shell.py`

- [ ] **Step 1: Write failing contract assertions**

In `tests/contracts/test_static_builder.py`, in the rendered reader-shell HTML assertions near the existing `Focus reading` and course-map controls, add:

```python
    assert 'class="raya-command raya-command-context"' in html
    assert "data-raya-learning-rail-toggle" in html
    assert 'aria-controls="raya-learning-rail-body"' in html
    assert 'aria-label="Hide learning context"' in html
```

In the shell resource contract test that reads `shell.js`, add:

```python
    assert "learningRailToggleButtons" in script_text
    assert "syncLearningRailToggleButtons" in script_text
    assert "data-raya-learning-rail-toggle" in script_text
```

- [ ] **Step 2: Run the contract tests to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_build_writes_local_shell_resource tests/contracts/test_static_builder.py::test_build_writes_shell_learning_context -q
```

Expected: FAIL because the top-bar context command and shared shell hook do not exist.

- [ ] **Step 3: Emit the top-bar context command**

In `packages/static/src/raya_static/builder.py`, inside `_render_top_command_bar(...)`, insert this command immediately after the `Focus reading` command:

```python
            _render_command_button(
                class_name="raya-command raya-command-context",
                aria_label="Hide learning context",
                icon="context",
                label="Context",
                aria_pressed=None,
                extra_attrs=(
                    " data-raya-learning-rail-toggle "
                    'aria-controls="raya-learning-rail-body" '
                    'aria-expanded="true"'
                ),
            ),
```

If `_command_icon()` does not support `context`, add a compact panel icon branch that uses the existing inline SVG pattern and no external assets.

- [ ] **Step 4: Add shared shell hook**

In `packages/static/src/raya_static/shell.py`, near the existing right-rail element constants, add:

```javascript
  const learningRailToggleButtons = Array.from(
    document.querySelectorAll("[data-raya-learning-rail-toggle]")
  );
```

Add a helper before `setLearningRailExpanded(...)`:

```javascript
  function syncLearningRailToggleButtons(nextExpanded) {
    learningRailToggleButtons.forEach((button) => {
      button.setAttribute("aria-expanded", nextExpanded ? "true" : "false");
      button.setAttribute(
        "aria-label",
        nextExpanded ? "Hide learning context" : "Show learning context"
      );
    });
  }
```

Inside `setLearningRailExpanded(nextExpanded)`, after setting `learningRail.dataset.rayaLearningRail`, call:

```javascript
    syncLearningRailToggleButtons(nextExpanded);
```

After the existing `readerFocusToggle` click listener, add:

```javascript
  learningRailToggleButtons.forEach((button) => {
    button.addEventListener("click", () => {
      if (!isDesktopShell()) {
        setLearningRailExpanded(true);
        return;
      }
      setLearningRailExpanded(root.dataset.rayaLearningRail !== "expanded");
      clearReaderFocus();
    });
  });
```

- [ ] **Step 5: Run contract tests to verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_build_writes_local_shell_resource tests/contracts/test_static_builder.py::test_build_writes_shell_learning_context -q
```

Expected: PASS.

## Task 2: Browser Behavior And Desktop/Mobile Layout

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `packages/static/src/raya_static/shell.py`

- [ ] **Step 1: Write failing desktop e2e assertions**

In `tests/e2e/test_preview_static_read_path.py`, add a new test near the other reader-shell e2e tests:

```python
def test_render_fixture_top_context_command_toggles_right_rail_only(
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
                    initial = page.evaluate(
                        """() => ({
                          mapState: document.documentElement.dataset.rayaCourseMap,
                          railState: document.documentElement.dataset.rayaLearningRail,
                          contextExpanded: document
                            .querySelector('[data-raya-learning-rail-toggle]')
                            ?.getAttribute('aria-expanded'),
                          collapseExpanded: document
                            .querySelector('[data-raya-learning-rail-collapse]')
                            ?.getAttribute('aria-expanded'),
                          expandExpanded: document
                            .querySelector('[data-raya-learning-rail-expand]')
                            ?.getAttribute('aria-expanded'),
                          commandVisible: document
                            .querySelector('[data-raya-learning-rail-toggle]')
                            ?.getClientRects().length > 0,
                          articleWidth: document
                            .querySelector('#raya-article')
                            ?.getBoundingClientRect().width,
                          railWidth: document
                            .querySelector('#raya-learning-rail')
                            ?.getBoundingClientRect().width,
                        })"""
                    )
                    assert initial["commandVisible"] is True
                    assert initial["mapState"] == "expanded"
                    assert initial["railState"] == "expanded"
                    assert initial["contextExpanded"] == "true"
                    assert initial["collapseExpanded"] == "true"
                    assert initial["expandExpanded"] == "true"
                    assert initial["articleWidth"] > 620
                    assert initial["railWidth"] >= 220

                    page.click("[data-raya-learning-rail-toggle]")
                    page.wait_for_function(
                        "() => document.documentElement.dataset.rayaLearningRail === 'collapsed'"
                    )
                    collapsed = page.evaluate(
                        """() => ({
                          mapState: document.documentElement.dataset.rayaCourseMap,
                          railState: document.documentElement.dataset.rayaLearningRail,
                          contextExpanded: document
                            .querySelector('[data-raya-learning-rail-toggle]')
                            ?.getAttribute('aria-expanded'),
                          contextLabel: document
                            .querySelector('[data-raya-learning-rail-toggle]')
                            ?.getAttribute('aria-label'),
                          collapseExpanded: document
                            .querySelector('[data-raya-learning-rail-collapse]')
                            ?.getAttribute('aria-expanded'),
                          expandExpanded: document
                            .querySelector('[data-raya-learning-rail-expand]')
                            ?.getAttribute('aria-expanded'),
                          articleWidth: document
                            .querySelector('#raya-article')
                            ?.getBoundingClientRect().width,
                          railWidth: document
                            .querySelector('#raya-learning-rail')
                            ?.getBoundingClientRect().width,
                          railBodyHidden: document
                            .querySelector('#raya-learning-rail-body')
                            ?.getAttribute('aria-hidden'),
                          railBodyInert: document
                            .querySelector('#raya-learning-rail-body')?.inert,
                        })"""
                    )
                    assert collapsed["mapState"] == "expanded"
                    assert collapsed["railState"] == "collapsed"
                    assert collapsed["contextExpanded"] == "false"
                    assert collapsed["contextLabel"] == "Show learning context"
                    assert collapsed["collapseExpanded"] == "false"
                    assert collapsed["expandExpanded"] == "false"
                    assert collapsed["articleWidth"] > initial["articleWidth"] + 80
                    assert collapsed["railWidth"] <= 80
                    assert collapsed["railBodyHidden"] == "true"
                    assert collapsed["railBodyInert"] is True
                    _assert_no_horizontal_overflow(page)

                    page.click("[data-raya-learning-rail-toggle]")
                    page.wait_for_function(
                        "() => document.documentElement.dataset.rayaLearningRail === 'expanded'"
                    )
                    restored = page.evaluate(
                        """() => ({
                          contextExpanded: document
                            .querySelector('[data-raya-learning-rail-toggle]')
                            ?.getAttribute('aria-expanded'),
                          contextLabel: document
                            .querySelector('[data-raya-learning-rail-toggle]')
                            ?.getAttribute('aria-label'),
                          railBodyHidden: document
                            .querySelector('#raya-learning-rail-body')
                            ?.getAttribute('aria-hidden'),
                        })"""
                    )
                    assert restored == {
                        "contextExpanded": "true",
                        "contextLabel": "Hide learning context",
                        "railBodyHidden": "false",
                    }
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Write failing mobile e2e assertions**

In `test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading`, after the topbar height assertion, add:

```python
                    assert not page.locator(
                        "[data-raya-learning-rail-toggle]"
                    ).is_visible()
                    assert (
                        page.locator("#raya-learning-rail-body")
                        .get_attribute("aria-hidden")
                        == "false"
                    )
```

- [ ] **Step 3: Run e2e tests to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_top_context_command_toggles_right_rail_only tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading -q
```

Expected: FAIL because the top-bar context command is not present or hidden correctly.

- [ ] **Step 4: Add CSS behavior**

In `packages/static/src/raya_static/rendering.py`, update the existing tablet/mobile rule that hides `.raya-command-focus` to hide context too:

```css
@media (max-width: 1279px) {
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-focus,
  .raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-context {
    display: none;
  }
}
```

If the added command causes the top bar to exceed the mobile height assertion,
prefer this hide rule and existing label clipping over changing command text.

- [ ] **Step 5: Run e2e tests to verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_top_context_command_toggles_right_rail_only tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading -q
```

Expected: PASS.

## Task 3: Documentation, Review, Verification, Commit

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Update docs**

Update the course-shell and reader-control paragraphs in `docs/foundation/20_learning_renderer_contract.md` to state that desktop reader pages may expose a top-bar `Context` command that toggles the right learning rail as volatile display state.

In the English and Spanish student guides, add one sentence to the reader-navigation/accessibility section explaining that desktop readers can use `Context` to hide or restore the right-side learning context while keeping the course map available.

In the English and Spanish agent guides, add one sentence explaining that agents should verify the command as static layout state only and must not treat it as progress, storage, or recommendation state.

- [ ] **Step 2: Run focused verification before review**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_build_writes_local_shell_resource tests/contracts/test_static_builder.py::test_build_writes_shell_learning_context tests/e2e/test_preview_static_read_path.py::test_render_fixture_top_context_command_toggles_right_rail_only tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading -q
```

Expected: PASS.

- [ ] **Step 3: Request independent review**

Dispatch a code-review subagent with:

- description: `Added a desktop top-bar Context command that toggles the existing right learning rail`
- requirements: this plan and `docs/superpowers/specs/2026-06-25-reader-context-command-design.md`
- base SHA: the commit before implementation
- head SHA: current implementation commit

Fix Critical and Important issues before proceeding.

- [ ] **Step 4: Run renderer verification**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS with no raw TeX leakage, no overflow, no external renderer requests.

- [ ] **Step 5: Run full host verification**

Run:

```bash
./scripts/check.sh
```

Expected: PASS.

- [ ] **Step 6: Run Docker verification**

Run:

```bash
./scripts/check-docker.sh
```

Expected: PASS.

- [ ] **Step 7: Commit and push**

Run:

```bash
git add packages/static/src/raya_static/builder.py packages/static/src/raya_static/shell.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/en/agents/index.md docs/guides/es/estudiantes/index.md docs/guides/es/agentes/index.md
git commit -m "Add reader context command"
git push origin new_rayalucaria
```

Expected: push updates `origin/new_rayalucaria`.

## Self-Review

- Spec coverage: the plan covers builder markup, shell state sync, desktop/mobile behavior, docs, review, and verification.
- Placeholder scan: no unresolved placeholders remain.
- Type consistency: the plan uses `data-raya-learning-rail-toggle`, `learningRailToggleButtons`, and `syncLearningRailToggleButtons` consistently.
