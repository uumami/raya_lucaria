# Responsive Shell Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent responsive shell state mismatches while preserving the old-main-inspired compact desktop shell.

**Architecture:** Keep generated HTML unchanged. Add browser tests first, then update `shell.py` to make right-rail collapse desktop-only and update `rendering.py` to remove the dead tablet three-column shell rule. Document the responsive invariant in the foundation and agent guides only if behavior text needs clarification.

**Tech Stack:** Python 3.10, generated static HTML/CSS/JavaScript, pytest, Playwright.

---

### Task 1: Browser Tests For Responsive Shell State

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add a focused mobile/tablet shell state test**

Add this test near the existing reader shell layout tests:

```python
def test_render_fixture_responsive_shell_state_remains_accessible(
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
                page = browser.new_page(viewport={"width": 390, "height": 844})
                try:
                    page.goto(
                        f"{handle.base_url}/reader-ux/index.html",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(page)
                    page.focus("#raya-learning-rail a")
                    page.keyboard.press("Escape")
                    mobile_state = page.evaluate(
                        """() => {
                          const root = document.documentElement;
                          const rail = document.querySelector('#raya-learning-rail');
                          const body = document.querySelector('#raya-learning-rail-body');
                          const collapse = document.querySelector('[data-raya-learning-rail-collapse]');
                          const expand = document.querySelector('[data-raya-learning-rail-expand]');
                          return {
                            rootState: root.dataset.rayaLearningRail,
                            railState: rail?.dataset.rayaLearningRail,
                            bodyHidden: body?.getAttribute('aria-hidden'),
                            bodyInert: body?.inert,
                            bodyDisplay: body ? getComputedStyle(body).display : '',
                            collapseVisible: !!collapse && getComputedStyle(collapse).display !== 'none',
                            expandVisible: !!expand && getComputedStyle(expand).display !== 'none',
                          };
                        }"""
                    )
                    assert mobile_state["rootState"] == "expanded"
                    assert mobile_state["railState"] == "expanded"
                    assert mobile_state["bodyHidden"] == "false"
                    assert mobile_state["bodyInert"] is False
                    assert mobile_state["bodyDisplay"] != "none"
                    assert mobile_state["collapseVisible"] is False
                    assert mobile_state["expandVisible"] is False

                    page.set_viewport_size({"width": 1180, "height": 900})
                    page.wait_for_timeout(100)
                    _assert_no_horizontal_overflow(page)
                    tablet = page.evaluate(
                        """() => {
                          const article = document.querySelector('article.raya-main-article');
                          const map = document.querySelector('nav.raya-course-map');
                          const rail = document.querySelector('aside.raya-learning-rail');
                          const body = document.querySelector('#raya-learning-rail-body');
                          return {
                            articleY: article.getBoundingClientRect().y,
                            mapY: map.getBoundingClientRect().y,
                            railY: rail.getBoundingClientRect().y,
                            bodyHidden: body.getAttribute('aria-hidden'),
                            bodyInert: body.inert,
                          };
                        }"""
                    )
                    assert tablet["articleY"] < tablet["mapY"] < tablet["railY"]
                    assert tablet["bodyHidden"] == "false"
                    assert tablet["bodyInert"] is False

                    page.set_viewport_size({"width": 1440, "height": 950})
                    page.wait_for_timeout(100)
                    page.click("[data-raya-learning-rail-collapse]")
                    page.wait_for_function(
                        "() => document.documentElement.dataset.rayaLearningRail === 'collapsed'"
                    )
                    page.set_viewport_size({"width": 390, "height": 844})
                    page.wait_for_function(
                        "() => document.documentElement.dataset.rayaLearningRail === 'expanded'"
                    )
                    restored = page.evaluate(
                        """() => {
                          const body = document.querySelector('#raya-learning-rail-body');
                          return {
                            bodyHidden: body.getAttribute('aria-hidden'),
                            bodyInert: body.inert,
                          };
                        }"""
                    )
                    assert restored["bodyHidden"] == "false"
                    assert restored["bodyInert"] is False
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [x] **Step 2: Extend desktop chrome test for compact map rail operability and storage**

In `test_render_fixture_desktop_shell_has_modern_workspace_chrome`, after the
existing collapsed assertions, add:

```python
    storage_state = page.evaluate(
        """() => ({
          localKeys: Object.keys(window.localStorage),
          sessionKeys: Object.keys(window.sessionStorage),
        })"""
    )
    compact_links = page.evaluate(
        """() => Array.from(document.querySelectorAll('#raya-course-map a[href]'))
          .map((link) => {
            const box = link.getBoundingClientRect();
            link.focus();
            return {
              href: link.getAttribute('href'),
              width: box.width,
              height: box.height,
              focused: document.activeElement === link,
            };
          })"""
    )
```

Then add assertions after the existing collapsed assertions:

```python
    assert storage_state["localKeys"] == []
    assert storage_state["sessionKeys"] == []
    assert compact_links
    assert all(not link["href"].startswith(("http://", "https://")) for link in compact_links)
    assert all(link["width"] > 0 for link in compact_links)
    assert all(link["height"] >= 24 for link in compact_links)
    assert all(link["focused"] for link in compact_links)
```

- [x] **Step 3: Run focused tests and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_responsive_shell_state_remains_accessible tests/e2e/test_preview_static_read_path.py::test_render_fixture_desktop_shell_has_modern_workspace_chrome -q
```

Actual: the branch already restored responsive rail state, so the new
responsive test passed. The desktop hardening test failed first because it
included hidden course-map links in the compact-link operability assertion;
scoping the assertion to visible compact links preserved the intended contract.

### Task 2: Implement Desktop-Only Rail Collapse

**Files:**
- Modify: `packages/static/src/raya_static/shell.py`

- [x] **Step 1: Add a desktop guard helper**

Inside `_SHELL_JAVASCRIPT`, near `desktopMapQuery`, add:

```javascript
  function isDesktopShell() {
    return desktopMapQuery.matches;
  }
```

- [x] **Step 2: Guard right-rail collapse controls**

Change the learning-rail collapse click listener so it only collapses on desktop:

```javascript
  if (learningRailCollapse) {
    learningRailCollapse.addEventListener("click", () => {
      if (!isDesktopShell()) {
        setLearningRailExpanded(true);
        return;
      }
      setLearningRailExpanded(false);
      if (learningRailExpand) {
        learningRailExpand.focus();
      }
    });
  }
```

- [x] **Step 3: Guard Escape collapse**

Change the learning-rail `Escape` branch to:

```javascript
    if (
      event.key === "Escape" &&
      root.dataset.rayaLearningRail === "expanded" &&
      isDesktopShell()
    ) {
      const activeElement = document.activeElement;
      const shouldMoveFocus =
        activeElement instanceof Element &&
        learningRail &&
        learningRail.contains(activeElement);
      if (shouldMoveFocus) {
        setLearningRailExpanded(false);
        if (learningRailExpand) {
          learningRailExpand.focus();
        }
      }
    }
```

- [x] **Step 4: Restore expanded rail state when leaving desktop width**

The existing match-media setup already restored expanded rail state when leaving
desktop width:

```javascript
  function syncResponsiveRailState() {
    if (!isDesktopShell()) {
      setLearningRailExpanded(true);
    }
  }

  if (desktopMapQuery.addEventListener) {
    desktopMapQuery.addEventListener("change", syncResponsiveRailState);
  } else if (desktopMapQuery.addListener) {
    desktopMapQuery.addListener(syncResponsiveRailState);
  }
  syncResponsiveRailState();
```

- [x] **Step 5: Run focused tests and verify GREEN for behavior**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_responsive_shell_state_remains_accessible tests/e2e/test_preview_static_read_path.py::test_render_fixture_desktop_shell_has_modern_workspace_chrome -q
```

Expected: both tests pass.

### Task 3: Remove Dead Tablet Shell CSS

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Add a CSS contract assertion**

In `test_rich_css_defines_learning_shell_regions`, assert that the desktop
three-column rule remains present, the dead tablet media-copy of that rule is
absent, and the intended article-first media block is present:

```python
    assert 'grid-template-areas: "course-map main-article learning-rail";' in css
    assert (
        '@media (max-width: 1279px) {\n  .raya-learning-shell {\n    grid-template-areas: "course-map main-article learning-rail";'
        not in css
    )
    assert (
        'grid-template-areas:\\n      "main-article"\\n      "course-map"\\n      "learning-rail";'
        in css
    )
```

- [x] **Step 2: Run contract test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_rich_css_defines_learning_shell_regions -q
```

Actual: covered by the focused contract/e2e run after adding the assertion and
removing the dead rule in this short slice.

- [x] **Step 3: Remove the dead shell override**

In the first `@media (max-width: 1279px)` block in
`packages/static/src/raya_static/rendering.py`, remove only:

```css
  .raya-learning-shell {
    grid-template-areas: "course-map main-article learning-rail";
    grid-template-columns: minmax(13.75rem, 16rem) minmax(0, 1fr) minmax(16rem, 18rem);
  }
```

Do not remove the graph and discovery workspace single-column rules in that
block.

- [x] **Step 4: Run focused tests and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_rich_css_defines_learning_shell_regions tests/e2e/test_preview_static_read_path.py::test_render_fixture_responsive_shell_state_remains_accessible -q
```

Expected: both tests pass.

### Task 4: Documentation And Final Verification

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] **Step 1: Document responsive shell state**

Update the course shell contract to state that learning-rail collapse is
desktop-only and tablet/mobile rail state remains visually and accessibility
expanded when collapse controls are hidden.

- [x] **Step 2: Update agent guidance**

Add English and Spanish agent guidance to test responsive shell state across
desktop, tablet, and mobile, including mobile `Escape` behavior and absence of
non-comfort storage keys.

- [x] **Step 3: Run focused verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_responsive_shell_state_remains_accessible tests/e2e/test_preview_static_read_path.py::test_render_fixture_desktop_shell_has_modern_workspace_chrome tests/contracts/test_static_builder.py::test_rich_css_defines_learning_shell_regions -q
```

Expected: all selected tests pass.

- [x] **Step 4: Run canonical verification**

Run sequentially:

```bash
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: all commands pass.

- [x] **Step 5: Commit and push**

```bash
git add docs/superpowers/specs/2026-06-24-responsive-shell-hardening-design.md docs/superpowers/plans/2026-06-24-responsive-shell-hardening.md docs/foundation/20_learning_renderer_contract.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md packages/static/src/raya_static/shell.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Harden responsive shell state"
git push origin new_rayalucaria
```
