# Reader Navigation Spine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make existing reader navigation surfaces feel like one coherent static reading path.

**Architecture:** Keep the current renderer architecture: `builder.py` generates static HTML, `rendering.py` owns browser-facing CSS, and `shell.py` owns existing volatile collapse behavior only if needed. This plan does not add source or artifact schema fields; it improves generated labels, grouping, and visual hierarchy around existing navigation, Page connections, and learning rail data.

**Tech Stack:** Python 3.10, static HTML generation in `packages/static`, Playwright e2e tests in `tests/e2e/test_preview_static_read_path.py`, render-fixture course.

---

## File Structure

- Modify `tests/e2e/test_preview_static_read_path.py`: add focused browser assertions for the reader navigation spine before changing renderer code.
- Modify `packages/static/src/raya_static/builder.py`: refine existing generated HTML in `_render_reading_flow_rail()`, `_render_article_connections()`, `_article_connection_section()`, `_article_connection_item()`, `_render_sequence_cards()`, and related helper output where needed.
- Modify `packages/static/src/raya_static/rendering.py`: refine CSS for `.raya-article-sequence-cards`, `.raya-article-connections`, `.raya-connection-preview`, `.raya-reading-flow-*`, and `.raya-rail-panel` hierarchy.
- Avoid `packages/static/src/raya_static/shell.py` unless a failing test proves a collapse accessibility issue in existing behavior.

---

### Task 1: Failing Reader Navigation Spine Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Add focused test for visible reader navigation spine**

Add this test near the existing article sequence and Page connections tests:

```python
def test_render_fixture_reader_navigation_spine_is_coherent(
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
                requested_urls: list[str] = []
                page.on("request", lambda request: requested_urls.append(request.url))
                try:
                    page.goto(
                        f"{handle.base_url}/reader-ux/index.html",
                        wait_until="networkidle",
                    )
                    requested_urls.clear()
                    _assert_no_horizontal_overflow(page)
                    state = page.evaluate(
                        """() => {
                          const textOf = (selector) =>
                            document.querySelector(selector)?.innerText || "";
                          const articleSequence = document
                            .querySelector('.raya-article-sequence-cards');
                          const connections = document
                            .querySelector('.raya-article-connections');
                          const railPanels = Array.from(
                            document.querySelectorAll(
                              '#raya-learning-rail .raya-rail-panel'
                            )
                          ).map((panel) => ({
                            className: panel.className,
                            title: panel
                              .querySelector('.raya-rail-toggle')
                              ?.textContent
                              ?.trim(),
                            expanded: panel
                              .querySelector('.raya-rail-toggle')
                              ?.getAttribute('aria-expanded'),
                            hidden: panel
                              .querySelector('.raya-rail-panel-body')
                              ?.getAttribute('aria-hidden'),
                          }));
                          const sequenceBox = articleSequence.getBoundingClientRect();
                          const connectionBox = connections.getBoundingClientRect();
                          return {
                            articleSequenceText: articleSequence.innerText,
                            sequenceLabel: articleSequence.getAttribute('aria-label'),
                            sequenceTop: sequenceBox.top,
                            connectionTop: connectionBox.top,
                            connectionText: connections.innerText,
                            connectionCountText: textOf('.raya-article-connections-summary'),
                            connectionRows: Array.from(
                              connections.querySelectorAll('.raya-article-connection-item')
                            ).map((item) => item.innerText),
                            graphLinks: Array.from(
                              connections.querySelectorAll('a[href*="_raya/graph/index.html"]')
                            ).map((link) => link.getAttribute('href')),
                            railPanels,
                            railText: textOf('#raya-learning-rail'),
                            localKeys: Object.keys(window.localStorage),
                            sessionKeys: Object.keys(window.sessionStorage),
                            privateLinks: Array.from(document.querySelectorAll('a[href]'))
                              .map((link) => link.getAttribute('href') || '')
                              .filter((href) =>
                                href.includes('_official/')
                                || href.includes('_drafts/')
                                || href.includes('_partials/')
                              ),
                            recommendationText: [
                              document.body.innerText.includes('recommended'),
                              document.body.innerText.includes('Recommended'),
                              document.body.innerText.includes('progress'),
                              document.body.innerText.includes('mastery'),
                            ],
                          };
                        }"""
                    )
                    assert state["sequenceLabel"] == "Previous and next pages"
                    assert "Previous page" in state["articleSequenceText"]
                    assert "Next page" in state["articleSequenceText"]
                    assert state["sequenceTop"] < state["connectionTop"]
                    assert "Page connections" in state["connectionText"]
                    assert "from this page" in state["connectionCountText"]
                    assert "links here" in state["connectionCountText"]
                    assert state["connectionRows"]
                    assert all(
                        "Graph" in row or "graph" in row
                        for row in state["connectionRows"]
                    )
                    assert all(
                        href.startswith("../_raya/graph/index.html")
                        for href in state["graphLinks"]
                    )
                    assert [panel["title"] for panel in state["railPanels"]] == [
                        "On this page",
                        "Reading flow",
                        "Page context",
                        "Connections",
                    ]
                    assert all(panel["expanded"] == "true" for panel in state["railPanels"])
                    assert all(panel["hidden"] == "false" for panel in state["railPanels"])
                    assert "Page 5 of 6" in state["railText"]
                    assert "Previous" in state["railText"]
                    assert "Next" in state["railText"]
                    assert state["localKeys"] == []
                    assert state["sessionKeys"] == []
                    assert state["privateLinks"] == []
                    assert state["recommendationText"] == [False, False, False, False]
                    assert requested_urls == []
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_navigation_spine_is_coherent -q
```

Expected: FAIL because current rail panel titles and/or article connection rows do not yet match the navigation spine contract.

- [ ] **Step 3: Commit failing test**

Run:

```bash
git add tests/e2e/test_preview_static_read_path.py
git commit -m "Test reader navigation spine coherence"
```

Expected: commit succeeds with only the failing test.

---

### Task 2: Generated Navigation Spine Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Rename and group learning rail panels**

In `packages/static/src/raya_static/builder.py`, adjust the functions that assemble the rail body so the generated rail panel titles appear in this order:

```python
[
    _render_toc_rail(toc_html),              # title: "On this page"
    _render_reading_flow_rail(...),          # title: "Reading flow"
    _render_page_context_rail(...),          # title: "Page context"
    _render_connections_rail(...),           # title: "Connections"
]
```

Use existing helpers where possible. If there is no `_render_page_context_rail()`, add it as a small wrapper that combines the existing summary/status/estimated-time/tags/prerequisites panel content under one `_render_rail_panel("raya-page-context", "Page context", body, expanded=True)`.

Keep the generated content static and escaped with `html.escape()`.

- [ ] **Step 2: Make Page connections rows explicitly scannable**

Update `_article_connection_item()` so each row includes:

```html
<li class="raya-article-connection-item">
  ...existing preview...
  <p class="raya-article-connection-actions">
    <span class="raya-article-connection-kind">Content</span>
    <span class="raya-article-connection-direction">From this page</span>
    <a class="raya-article-connection-context" href="../_raya/graph/index.html?page=reader-ux">Graph focus</a>
  </p>
</li>
```

Use the real `kind`, `target_id`, and relative graph URL already available in the connection item data. Do not duplicate the connected page title outside the existing preview if `_connection_preview_item()` already renders it.

- [ ] **Step 3: Keep article sequence cards as primary continuation**

Update `_render_sequence_cards()` only if needed so the nav keeps:

```html
<nav class="raya-article-sequence-cards" aria-label="Previous and next pages">
```

and card text keeps `Previous page` and `Next page`.

- [ ] **Step 4: Run focused test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_navigation_spine_is_coherent -q
```

Expected: PASS.

- [ ] **Step 5: Commit generated markup**

Run:

```bash
git add packages/static/src/raya_static/builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Build reader navigation spine markup"
```

Expected: commit succeeds.

---

### Task 3: Visual Hierarchy And Responsive Polish

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add CSS hierarchy for navigation spine**

In `packages/static/src/raya_static/rendering.py`, refine existing rules for these selectors:

```css
.raya-article-sequence-cards
.raya-sequence-card
.raya-article-connections
.raya-article-connection-actions
.raya-article-connection-kind
.raya-article-connection-direction
.raya-rail-panel
.raya-rail-title
.raya-reading-flow-grid
```

Use current CSS variables only. Keep card radius at `0.375rem` or less. Ensure desktop cards use available width and mobile stacks without horizontal overflow.

- [x] **Step 2: Add CSS for connection action row**

Add this shape, adapting colors to nearby existing patterns:

```css
.raya-article-connection-actions {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin: 0.45rem 0 0;
}
.raya-article-connection-kind,
.raya-article-connection-direction {
  border: 1px solid var(--raya-color-border);
  border-radius: 999px;
  color: var(--raya-color-muted);
  display: inline-flex;
  font-size: 0.72rem;
  font-weight: 800;
  line-height: 1;
  padding: 0.22rem 0.42rem;
}
```

- [x] **Step 3: Add browser visual assertions**

Extend `test_render_fixture_reader_navigation_spine_is_coherent` with:

```python
layout = page.evaluate(
    """() => {
      const seq = document.querySelector('.raya-article-sequence-cards')
        .getBoundingClientRect();
      const conn = document.querySelector('.raya-article-connections')
        .getBoundingClientRect();
      const action = document.querySelector('.raya-article-connection-actions')
        .getBoundingClientRect();
      return {
        seqWidth: seq.width,
        connWidth: conn.width,
        actionHeight: action.height,
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
      };
    }"""
)
assert layout["seqWidth"] >= 520
assert layout["connWidth"] >= 520
assert layout["actionHeight"] >= 20
assert layout["scrollWidth"] <= layout["clientWidth"]
```

- [x] **Step 4: Run focused visual tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_navigation_spine_is_coherent tests/e2e/test_preview_static_read_path.py::test_render_fixture_article_sequence_cards_are_visible_and_static tests/e2e/test_preview_static_read_path.py::test_render_fixture_article_page_connections_are_visible_and_static -q
```

Expected: PASS.

- [x] **Step 5: Commit visual polish**

Run:

```bash
git add packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py
git commit -m "Polish reader navigation spine"
```

Expected: commit succeeds.

---

### Task 4: Collapse And Mobile Verification

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify only if needed: `packages/static/src/raya_static/shell.py`

- [x] **Step 1: Add collapse/mobile assertions**

Extend existing learning-rail collapse tests or add a focused test:

```python
def test_reader_navigation_spine_collapse_keeps_static_contract(
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
                    page.click("[data-raya-learning-rail-collapse]")
                    collapsed = page.evaluate(
                        """() => {
                          const body = document.querySelector('#raya-learning-rail-body');
                          return {
                            rail: document.querySelector('#raya-learning-rail')
                              ?.getAttribute('data-raya-learning-rail'),
                            hidden: body?.getAttribute('aria-hidden'),
                            inert: body?.hasAttribute('inert'),
                            bodyLinks: Array.from(body.querySelectorAll('a,button'))
                              .map((item) => ({
                                tabindex: item.getAttribute('tabindex'),
                                disabled: item.hasAttribute('disabled'),
                              })),
                            localKeys: Object.keys(window.localStorage),
                            sessionKeys: Object.keys(window.sessionStorage),
                          };
                        }"""
                    )
                    assert collapsed["rail"] == "collapsed"
                    assert collapsed["hidden"] == "true"
                    assert collapsed["inert"] is True
                    assert collapsed["bodyLinks"]
                    assert all(item["tabindex"] == "-1" for item in collapsed["bodyLinks"])
                    assert collapsed["localKeys"] == []
                    assert collapsed["sessionKeys"] == []

                    page.click("[data-raya-learning-rail-expand]")
                    expanded = page.evaluate(
                        """() => {
                          const body = document.querySelector('#raya-learning-rail-body');
                          return {
                            rail: document.querySelector('#raya-learning-rail')
                              ?.getAttribute('data-raya-learning-rail'),
                            hidden: body?.getAttribute('aria-hidden'),
                            inert: body?.hasAttribute('inert'),
                          };
                        }"""
                    )
                    assert expanded == {
                        "rail": "expanded",
                        "hidden": "false",
                        "inert": False,
                    }

                    page.set_viewport_size({"width": 390, "height": 844})
                    page.wait_for_function(
                        "() => document.documentElement.clientWidth === 390"
                    )
                    mobile = page.evaluate(
                        """() => {
                          const body = document.querySelector('#raya-learning-rail-body');
                          return {
                            bodyVisible: !!body.getClientRects().length,
                            hidden: body?.getAttribute('aria-hidden'),
                            inert: body?.hasAttribute('inert'),
                            collapseVisible: !!document
                              .querySelector('[data-raya-learning-rail-collapse]')
                              ?.getClientRects().length,
                          };
                        }"""
                    )
                    assert mobile["bodyVisible"] is True
                    assert mobile["hidden"] == "false"
                    assert mobile["inert"] is False
                    assert mobile["collapseVisible"] is False
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [x] **Step 2: Run collapse test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_reader_navigation_spine_collapse_keeps_static_contract -q
```

Expected: PASS. If it fails because current shell behavior violates the design, make the smallest `shell.py` fix and rerun.

- [x] **Step 3: Run focused rail tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_learning_rail_can_collapse_without_losing_accessibility tests/e2e/test_preview_static_read_path.py::test_render_fixture_learning_rail_mobile_keeps_context_accessible tests/e2e/test_preview_static_read_path.py::test_reader_navigation_spine_collapse_keeps_static_contract -q
```

Expected: PASS. If a named existing test is absent, locate the current rail tests with `rg -n "learning_rail|raya-learning-rail" tests/e2e/test_preview_static_read_path.py` and run the closest current equivalents.

- [x] **Step 4: Commit collapse verification**

Run:

```bash
git add tests/e2e/test_preview_static_read_path.py packages/static/src/raya_static/shell.py
git commit -m "Verify reader navigation spine collapse behavior"
```

Expected: commit succeeds. If `shell.py` was not modified, omit it from `git add`.

---

### Task 5: Final Verification, Review, Push

**Files:**
- Verify all modified files.

- [x] **Step 1: Run focused e2e suite**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_navigation_spine_is_coherent tests/e2e/test_preview_static_read_path.py::test_reader_navigation_spine_collapse_keeps_static_contract tests/e2e/test_preview_static_read_path.py::test_render_fixture_article_sequence_cards_are_visible_and_static tests/e2e/test_preview_static_read_path.py::test_render_fixture_article_page_connections_are_visible_and_static -q
```

Expected: PASS.

- [x] **Step 2: Run syntax and diff hygiene**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run python -m py_compile tests/e2e/test_preview_static_read_path.py
git diff --check
```

Expected: both commands exit 0.

- [x] **Step 3: Run render-debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS with no raw TeX leakage, no external renderer requests, no overflow, and static-site parity.

- [x] **Step 4: Request code review**

Use `superpowers:requesting-code-review`. Ask one reviewer to check:

- spec alignment with `docs/superpowers/specs/2026-06-29-reader-navigation-spine-design.md`;
- no recommendation/progress/learner-state language;
- static renderer boundaries: no storage, no fetch, no external resources;
- accessibility of rail collapse/expand and mobile behavior.

- [ ] **Step 5: Fix review findings one at a time**

For each Critical or Important finding:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_navigation_spine_is_coherent -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_reader_navigation_spine_collapse_keeps_static_contract -q
```

Expected: the focused test related to the finding passes after the fix. If the
review finding names another existing test, run that exact node id as well.

- [ ] **Step 6: Final status and push**

Run:

```bash
git status --short --branch
git push origin new_rayalucaria
```

Expected: branch is clean and synced with `origin/new_rayalucaria`.
