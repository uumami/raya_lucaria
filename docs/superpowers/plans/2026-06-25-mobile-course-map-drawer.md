# Mobile Course Map Drawer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the tablet/mobile course-map drawer so it is comfortable, accessible, visually intentional, and verifiable as volatile static UI state.

**Architecture:** Reuse the existing static course-map `nav`, shell script, and renderer CSS. Add small drawer chrome in the builder, synchronize an explicit scroll-lock root data attribute in the shell script, and style the mobile drawer with existing skin tokens.

**Tech Stack:** Python static builder, generated HTML/CSS/JavaScript resources, Playwright browser tests through pytest, Superpowers TDD workflow.

---

## File Structure

- `packages/static/src/raya_static/builder.py` renders the course-map drawer HTML chrome.
- `packages/static/src/raya_static/shell.py` owns volatile drawer state, focus restore, inert handling, Escape/backdrop close, and scroll-lock synchronization.
- `packages/static/src/raya_static/rendering.py` owns static drawer CSS and reduced-motion behavior.
- `tests/e2e/test_preview_static_read_path.py` owns browser checks for mobile drawer behavior.
- `tests/contracts/test_static_builder.py` owns generated HTML/CSS/JS contract assertions.
- `docs/foundation/20_learning_renderer_contract.md` documents the renderer contract.
- `docs/guides/en/students/index.md` and `docs/guides/es/estudiantes/index.md` document student use.
- `docs/guides/en/agents/index.md` and `docs/guides/es/agentes/index.md` document verification expectations.

### Task 1: Add Failing Drawer Comfort Tests

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write the failing browser test**

Add a focused mobile assertion near the current course-map mobile coverage:

```python
def test_render_fixture_mobile_course_map_drawer_has_comfort_chrome(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "artifact"
    result = build_course_artifact(RENDER_FIXTURE_COURSE, artifact)
    assert result.exit_code == 0

    with _static_server(artifact / "site") as server:
        with sync_playwright() as playwright:
            browser = _launch_browser(playwright)
            try:
                page = browser.new_page(viewport={"width": 390, "height": 844})
                page.goto(f"{server}/reader-ux/index.html", wait_until="networkidle")
                page.click(".raya-command-map")
                page.wait_for_function(
                    "() => document.documentElement.dataset.rayaCourseMapDrawer === 'open'"
                )
                state = page.evaluate(
                    """() => {
                      const root = document.documentElement;
                      const body = document.body;
                      const map = document.querySelector('#raya-course-map');
                      const backdrop = document.querySelector('[data-raya-course-map-drawer-backdrop]');
                      const opener = document.querySelector('.raya-command-map');
                      const chrome = document.querySelector('.raya-course-map-drawer-chrome');
                      const title = document.querySelector('.raya-course-map-drawer-title');
                      const grip = document.querySelector('.raya-course-map-drawer-grip');
                      const close = document.querySelector('[data-raya-course-map-close]');
                      const mapBox = map.getBoundingClientRect();
                      const backdropStyle = getComputedStyle(backdrop);
                      return {
                        drawer: root.dataset.rayaCourseMapDrawer,
                        scrollLock: root.dataset.rayaCourseMapScrollLock,
                        htmlOverflow: getComputedStyle(root).overflow,
                        bodyOverflow: getComputedStyle(body).overflow,
                        ariaHidden: map.getAttribute('aria-hidden'),
                        inert: map.inert,
                        chromeVisible: chrome && getComputedStyle(chrome).display !== 'none',
                        title: title && title.textContent.trim(),
                        gripVisible: grip && getComputedStyle(grip).display !== 'none',
                        closeLabel: close && close.getAttribute('aria-label'),
                        width: mapBox.width,
                        left: mapBox.left,
                        right: mapBox.right,
                        backdropHidden: backdrop.hidden,
                        backdropDisplay: backdropStyle.display,
                        backdropBackground: backdropStyle.backgroundColor,
                        backdropFilter: backdropStyle.backdropFilter || backdropStyle.webkitBackdropFilter,
                        openerExpanded: opener.getAttribute('aria-expanded'),
                      };
                    }"""
                )
                assert state["drawer"] == "open"
                assert state["scrollLock"] == "true"
                assert state["htmlOverflow"] == "hidden"
                assert state["bodyOverflow"] == "hidden"
                assert state["ariaHidden"] == "false"
                assert state["inert"] is False
                assert state["chromeVisible"] is True
                assert state["title"] == "Course map"
                assert state["gripVisible"] is True
                assert state["closeLabel"] == "Close course map"
                assert 320 <= state["width"] <= 390
                assert state["left"] == 0
                assert state["right"] <= 390
                assert state["backdropHidden"] is False
                assert state["backdropDisplay"] == "block"
                assert "rgba" in state["backdropBackground"]
                assert state["backdropFilter"] != "none"
                assert state["openerExpanded"] == "true"

                page.keyboard.press("Escape")
                page.wait_for_function(
                    "() => document.documentElement.dataset.rayaCourseMapDrawer === 'closed'"
                )
                closed = page.evaluate(
                    """() => ({
                      scrollLock: document.documentElement.dataset.rayaCourseMapScrollLock,
                      htmlOverflow: getComputedStyle(document.documentElement).overflow,
                      bodyOverflow: getComputedStyle(document.body).overflow,
                      focusedClass: document.activeElement && document.activeElement.className,
                    })"""
                )
                assert closed["scrollLock"] == "false"
                assert closed["htmlOverflow"] != "hidden"
                assert closed["bodyOverflow"] != "hidden"
                assert "raya-command-map" in closed["focusedClass"]
            finally:
                browser.close()
```

- [ ] **Step 2: Write failing static contract assertions**

Add assertions near existing course-map shell contract checks:

```python
assert 'class="raya-course-map-drawer-chrome"' in html
assert 'class="raya-course-map-drawer-grip"' in html
assert 'class="raya-course-map-drawer-title">Course map</p>' in html
assert "data-raya-course-map-scroll-lock" in script_text
assert 'html[data-raya-course-map-scroll-lock="true"]' in rich_css
assert ".raya-course-map-drawer-chrome" in rich_css
```

- [ ] **Step 3: Run tests to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_builder_renders_course_map_shell_controls tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_course_map_drawer_has_comfort_chrome -q
```

Expected: fail because drawer chrome and scroll-lock behavior do not exist yet.

### Task 2: Implement Drawer Chrome, Scroll Lock, And CSS

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Add drawer chrome in builder output**

Insert the following inside `raya-course-map-header`, before the existing region title:

```python
'<div class="raya-course-map-drawer-chrome" aria-hidden="true">',
'<span class="raya-course-map-drawer-grip"></span>',
'<p class="raya-course-map-drawer-title">Course map</p>',
f'<p class="raya-course-map-drawer-position">{position}</p>' if position else "",
"</div>",
```

- [ ] **Step 2: Add scroll-lock synchronization**

In `syncCourseMapDrawerState()`, after computing `drawerOpen`, set:

```javascript
root.dataset.rayaCourseMapScrollLock = drawerOpen && !isDesktopShell() ? "true" : "false";
```

When desktop layout is restored, ensure `rayaCourseMapDrawer` is `closed` and `rayaCourseMapScrollLock` is `false`.

- [ ] **Step 3: Style drawer chrome and scroll lock**

Add CSS for:

```css
html[data-raya-course-map-scroll-lock="true"],
html[data-raya-course-map-scroll-lock="true"] body {
  overflow: hidden;
}
.raya-course-map-drawer-chrome {
  display: none;
}
@media (max-width: 1279px) {
  html[data-raya-course-map-drawer="open"] .raya-course-map {
    border-radius: 0 0.875rem 0.875rem 0;
    max-width: calc(100vw - 1rem);
    padding: 0;
    width: min(22rem, calc(100vw - 1rem));
  }
  html[data-raya-course-map-drawer="open"] .raya-course-map-drawer-backdrop {
    backdrop-filter: blur(0.55rem);
    -webkit-backdrop-filter: blur(0.55rem);
  }
  html[data-raya-course-map-drawer="open"] .raya-course-map-drawer-chrome {
    display: grid;
  }
}
```

Keep existing map content padded by applying padding to the header/workspaces/actions/filter/list blocks when the drawer is open.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_builder_renders_course_map_shell_controls tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_course_map_drawer_has_comfort_chrome -q
```

Expected: pass.

### Task 3: Update Renderer Contract And Role Docs

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Document student behavior**

State that mobile/tablet readers open the course map as a temporary drawer with visible title, position, close button, backdrop close, Escape close, and paused background scrolling.

- [ ] **Step 2: Document agent verification**

State that agents should verify drawer chrome, scroll lock cleanup, focus restore, inert/aria-hidden closed state, no storage persistence, no external requests, and article/rail availability after close.

- [ ] **Step 3: Run doc-sensitive focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_builder_renders_course_map_shell_controls tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_course_map_drawer_has_comfort_chrome -q
```

Expected: pass.

### Task 4: Verify And Review

**Files:**
- Inspect: git diff and test output.

- [ ] **Step 1: Run focused browser gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: all checks pass, no raw TeX leakage, no external renderer requests, no overflow failures.

- [ ] **Step 2: Run host archive gate**

Run:

```bash
./scripts/check.sh
```

Expected: all tests pass.

- [ ] **Step 3: Request independent review**

Dispatch one reviewer with the spec, plan, and diff. Ask them to check mobile drawer accessibility, scroll lock cleanup, state persistence, and doc alignment.

- [ ] **Step 4: Commit and push after review fixes**

Run:

```bash
git add packages/static/src/raya_static/builder.py packages/static/src/raya_static/shell.py packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py tests/contracts/test_static_builder.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/es/estudiantes/index.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md
git commit -m "Polish mobile course map drawer"
git push origin new_rayalucaria
```

Expected: branch pushed to the GitHub branch of the same name.
