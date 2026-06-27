# Reader Shell Continuity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make reader shell map/context collapse and expand transitions feel continuous without adding persistent shell state or changing renderer authority.

**Architecture:** Keep the existing generated shell HTML and volatile state model. Add browser tests that prove expanding transitions do not expose narrow wrapped panel bodies, then update `shell.py` and `rendering.py` so the map list and learning-rail body remain visually hidden and inert during desktop expansion until the transition marker is removed.

**Tech Stack:** Python static builder, local shell JavaScript resource, CSS in `packages/static/src/raya_static/rendering.py`, Playwright e2e tests.

---

### Task 1: Failing Expansion Continuity Tests

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add a browser test for map expansion continuity**

Add a focused e2e test near the existing shell collapse tests:

```python
def test_render_fixture_desktop_course_map_expansion_hides_full_list_until_transition_end(
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
                    page.click("#raya-course-map .raya-course-map-toggle")
                    page.wait_for_function(
                        "() => document.documentElement.dataset.rayaCourseMap === 'collapsed'"
                    )
                    page.wait_for_function(
                        "() => !document.querySelector('#raya-course-map')?.dataset.rayaCourseMapTransition"
                    )
                    page.click("#raya-course-map .raya-course-map-toggle")
                    expanding = page.evaluate(
                        """async () => {
                          await new Promise((resolve) => requestAnimationFrame(resolve));
                          const map = document.querySelector('#raya-course-map');
                          const list = document.querySelector('#raya-course-map-list');
                          const firstLink = list?.querySelector('a[href]');
                          return {
                            rootState: document.documentElement.dataset.rayaCourseMap,
                            transition: map?.dataset.rayaCourseMapTransition,
                            width: map?.getBoundingClientRect().width,
                            listDisplay: list ? getComputedStyle(list).display : null,
                            listVisibility: list ? getComputedStyle(list).visibility : null,
                            listHidden: list?.getAttribute('aria-hidden'),
                            listInert: list?.inert,
                            firstLinkTabIndex: firstLink?.getAttribute('tabindex'),
                            overflow: Math.ceil(
                              document.documentElement.scrollWidth - window.innerWidth
                            ),
                            storage: {
                              local: Object.keys(localStorage),
                              session: Object.keys(sessionStorage),
                            },
                          };
                        }"""
                    )
                    assert expanding["rootState"] == "expanded"
                    assert expanding["transition"] == "expanding"
                    assert expanding["width"] < 220
                    assert expanding["listDisplay"] == "block"
                    assert expanding["listVisibility"] == "hidden"
                    assert expanding["listHidden"] == "true"
                    assert expanding["listInert"] is True
                    assert expanding["firstLinkTabIndex"] == "-1"
                    assert expanding["overflow"] <= 1
                    assert expanding["storage"] == {"local": [], "session": []}

                    page.wait_for_function(
                        "() => !document.querySelector('#raya-course-map')?.dataset.rayaCourseMapTransition"
                    )
                    expanded = page.evaluate(
                        """() => {
                          const map = document.querySelector('#raya-course-map');
                          const list = document.querySelector('#raya-course-map-list');
                          const firstLink = list?.querySelector('a[href]');
                          return {
                            width: map?.getBoundingClientRect().width,
                            listVisibility: list ? getComputedStyle(list).visibility : null,
                            listHidden: list?.getAttribute('aria-hidden'),
                            listInert: list?.inert,
                            firstLinkTabIndex: firstLink?.getAttribute('tabindex'),
                          };
                        }"""
                    )
                    assert expanded["width"] >= 220
                    assert expanded["listVisibility"] == "visible"
                    assert expanded["listHidden"] == "false"
                    assert expanded["listInert"] is False
                    assert expanded["firstLinkTabIndex"] is None
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Add a browser test for right-rail expansion continuity**

Add:

```python
def test_render_fixture_desktop_learning_rail_expansion_hides_body_until_transition_end(
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
                    page.click("[data-raya-learning-rail-toggle]")
                    page.wait_for_function(
                        "() => document.documentElement.dataset.rayaLearningRail === 'collapsed'"
                    )
                    page.wait_for_function(
                        "() => !document.querySelector('#raya-learning-rail')?.dataset.rayaLearningRailTransition"
                    )
                    page.click("[data-raya-learning-rail-expand]")
                    expanding = page.evaluate(
                        """async () => {
                          await new Promise((resolve) => requestAnimationFrame(resolve));
                          const rail = document.querySelector('#raya-learning-rail');
                          const body = document.querySelector('#raya-learning-rail-body');
                          const expand = document.querySelector('[data-raya-learning-rail-expand]');
                          const collapse = document.querySelector('[data-raya-learning-rail-collapse]');
                          return {
                            rootState: document.documentElement.dataset.rayaLearningRail,
                            transition: rail?.dataset.rayaLearningRailTransition,
                            width: rail?.getBoundingClientRect().width,
                            bodyDisplay: body ? getComputedStyle(body).display : null,
                            bodyVisibility: body ? getComputedStyle(body).visibility : null,
                            bodyHidden: body?.getAttribute('aria-hidden'),
                            bodyInert: body?.inert,
                            expandVisible: !!expand?.getClientRects().length,
                            collapseVisible: !!collapse?.getClientRects().length,
                            overflow: Math.ceil(
                              document.documentElement.scrollWidth - window.innerWidth
                            ),
                            storage: {
                              local: Object.keys(localStorage),
                              session: Object.keys(sessionStorage),
                            },
                          };
                        }"""
                    )
                    assert expanding["rootState"] == "expanded"
                    assert expanding["transition"] == "expanding"
                    assert expanding["width"] < 220
                    assert expanding["bodyDisplay"] == "grid"
                    assert expanding["bodyVisibility"] == "hidden"
                    assert expanding["bodyHidden"] == "true"
                    assert expanding["bodyInert"] is True
                    assert expanding["expandVisible"] is True
                    assert expanding["collapseVisible"] is False
                    assert expanding["overflow"] <= 1
                    assert expanding["storage"] == {"local": [], "session": []}

                    page.wait_for_function(
                        "() => !document.querySelector('#raya-learning-rail')?.dataset.rayaLearningRailTransition"
                    )
                    expanded = page.evaluate(
                        """() => {
                          const rail = document.querySelector('#raya-learning-rail');
                          const body = document.querySelector('#raya-learning-rail-body');
                          const expand = document.querySelector('[data-raya-learning-rail-expand]');
                          const collapse = document.querySelector('[data-raya-learning-rail-collapse]');
                          return {
                            width: rail?.getBoundingClientRect().width,
                            bodyVisibility: body ? getComputedStyle(body).visibility : null,
                            bodyHidden: body?.getAttribute('aria-hidden'),
                            bodyInert: body?.inert,
                            expandVisible: !!expand?.getClientRects().length,
                            collapseVisible: !!collapse?.getClientRects().length,
                          };
                        }"""
                    )
                    assert expanded["width"] >= 220
                    assert expanded["bodyVisibility"] == "visible"
                    assert expanded["bodyHidden"] == "false"
                    assert expanded["bodyInert"] is False
                    assert expanded["expandVisible"] is False
                    assert expanded["collapseVisible"] is True
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_desktop_course_map_expansion_hides_full_list_until_transition_end \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_desktop_learning_rail_expansion_hides_body_until_transition_end
```

Expected: fail because expansion currently reveals the full map list/right-rail body while the rail is still narrow and marks those descendants accessible immediately.

### Task 2: Expansion Transition Implementation

**Files:**
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Keep course-map links inert during desktop expansion**

In `packages/static/src/raya_static/shell.py`, update `setExpanded(nextExpanded)` so desktop expansion keeps the map list non-interactive until the transition marker clears:

```javascript
    if (isDesktopShell() && previousExpanded !== nextExpanded) {
      window.clearTimeout(courseMapTransitionTimer);
      map.dataset.rayaCourseMapTransition = nextExpanded ? "expanding" : "collapsing";
      if (nextExpanded) {
        updateMapLinkTabOrder(false);
      }
      courseMapTransitionTimer = window.setTimeout(() => {
        delete map.dataset.rayaCourseMapTransition;
        if (nextExpanded && root.dataset.rayaCourseMap === "expanded") {
          updateMapLinkTabOrder(true);
        }
      }, SHELL_TRANSITION_MS);
```

Keep the existing final `updateMapLinkTabOrder(nextExpanded)` call for non-transition paths and collapse paths by guarding it:

```javascript
    if (!(isDesktopShell() && previousExpanded !== nextExpanded && nextExpanded)) {
      updateMapLinkTabOrder(nextExpanded);
    }
```

- [ ] **Step 2: Keep learning-rail body inert during desktop expansion**

In `setLearningRailExpanded(nextExpanded)`, during desktop expansion keep `aria-hidden=true`, `inert=true`, and descendants disabled until the transition marker clears:

```javascript
      if (nextExpanded) {
        learningRailBody.setAttribute("aria-hidden", "true");
        setElementInert(learningRailBody, true);
        setFocusableDescendantsEnabled(learningRailBody, false);
      }
      learningRailTransitionTimer = window.setTimeout(() => {
        delete learningRail.dataset.rayaLearningRailTransition;
        if (nextExpanded && root.dataset.rayaLearningRail === "expanded") {
          learningRailBody.setAttribute("aria-hidden", "false");
          setElementInert(learningRailBody, false);
          setFocusableDescendantsEnabled(learningRailBody, true);
        }
      }, SHELL_TRANSITION_MS);
```

Guard the existing immediate body accessibility update so desktop expansion does not undo the temporary inert state.

- [ ] **Step 3: Hide full panel bodies while expanding**

In `packages/static/src/raya_static/rendering.py`, add CSS alongside the existing collapsing selectors:

```css
  [data-raya-learning-rail="expanded"] .raya-learning-rail[data-raya-learning-rail-transition="expanding"] .raya-learning-rail-body,
  .raya-learning-rail[data-raya-learning-rail="expanded"][data-raya-learning-rail-transition="expanding"] .raya-learning-rail-body {
    display: grid;
    pointer-events: none;
    visibility: hidden;
  }
  [data-raya-learning-rail="expanded"] .raya-learning-rail[data-raya-learning-rail-transition="expanding"] .raya-learning-rail-header,
  .raya-learning-rail[data-raya-learning-rail="expanded"][data-raya-learning-rail-transition="expanding"] .raya-learning-rail-header {
    display: none;
  }
  [data-raya-learning-rail="expanded"] .raya-learning-rail[data-raya-learning-rail-transition="expanding"] .raya-learning-rail-expand,
  .raya-learning-rail[data-raya-learning-rail="expanded"][data-raya-learning-rail-transition="expanding"] .raya-learning-rail-expand {
    align-items: center;
    align-self: stretch;
    display: inline-flex;
    font-size: 0;
    justify-content: center;
    min-height: 9rem;
    min-width: 3rem;
    padding: 0.7rem 0.45rem;
    width: 100%;
  }
```

Also add:

```css
  [data-raya-course-map="expanded"] .raya-course-map[data-raya-course-map-transition="expanding"] .raya-course-map-list,
  .raya-course-map[data-raya-course-map="expanded"][data-raya-course-map-transition="expanding"] .raya-course-map-list {
    display: block;
    pointer-events: none;
    visibility: hidden;
  }
```

- [ ] **Step 4: Verify GREEN**

Run the two focused tests from Task 1. Expected: both pass.

### Task 3: Regression Gates and Review

**Files:**
- Inspect only unless failures require fixes.

- [ ] **Step 1: Run focused shell regression tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_static_pages_use_expanded_course_map_shell \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_focus_collapses_map_and_context_without_storage \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_collapsed_reader_rails_use_compact_horizontal_tabs \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_desktop_course_map_expansion_hides_full_list_until_transition_end \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_desktop_learning_rail_expansion_hides_body_until_transition_end
```

Expected: pass with no storage keys, no horizontal overflow, stable compact tabs, and restored expanded bodies after transition cleanup.

- [ ] **Step 2: Run render-debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: pass with local resources only, no overflow regression, no raw TeX leakage, and static-site parity intact.

- [ ] **Step 3: Request independent code review**

Ask a reviewer to inspect the diff for:

- static renderer constraints;
- no persistent shell state;
- accessibility during hidden/inert transition windows;
- no discovery/graph regressions;
- test strength.

- [ ] **Step 4: Commit and push**

After verification and review:

```bash
git status --short --branch
git add docs/superpowers/plans/2026-06-27-reader-shell-continuity.md \
  packages/static/src/raya_static/shell.py \
  packages/static/src/raya_static/rendering.py \
  tests/e2e/test_preview_static_read_path.py
git commit -m "Smooth reader shell expansion transitions"
git push origin new_rayalucaria
```
