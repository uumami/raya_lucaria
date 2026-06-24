# Graph URL State Debug Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make graph workspace state URL-addressable and visible in a compact inspector readout.

**Architecture:** Keep graph data and rendering static. Add one readout section to the generated graph inspector, then extend `graph.js` to initialize selected state from query parameters and update `history.replaceState` as graph controls change.

**Tech Stack:** Python 3.10 static builder, generated HTML/CSS/JavaScript, pytest, Playwright.

---

### Task 1: Contract Tests For Static Markup And Script Tokens

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Add graph-state markup assertions**

In `test_build_writes_static_graph_surface`, add assertions that the generated
graph HTML includes:

```python
    assert "raya-graph-state" in graph_html
    assert "data-raya-graph-state-readout" in graph_html
    assert "data-raya-graph-state-selected" in graph_html
    assert "data-raya-graph-state-query" in graph_html
    assert "data-raya-graph-state-layout" in graph_html
    assert "data-raya-graph-state-visible" in graph_html
    assert "data-raya-graph-state-hidden-groups" in graph_html
    assert "data-raya-graph-state-hidden-edges" in graph_html
    assert "data-raya-graph-state-neighborhood" in graph_html
    assert "data-raya-graph-state-url" in graph_html
```

- [x] **Step 2: Add script-token assertions**

In the same test, add assertions that `graph.js` includes:

```python
    assert "initializeGraphStateFromUrl" in graph_script
    assert "updateGraphUrlState" in graph_script
    assert "updateGraphStateReadout" in graph_script
    assert "history.replaceState" in graph_script
    assert 'params.get("q")' in graph_script
    assert 'params.get("layout")' in graph_script
    assert 'params.get("groups")' in graph_script
    assert 'params.get("edges")' in graph_script
    assert 'params.get("neighborhood")' in graph_script
```

- [x] **Step 3: Run contract test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface -q
```

Actual: failed on missing `raya-graph-state` markup.

### Task 2: Browser Test For URL State And Readout

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add focused e2e test**

Add a graph test near the existing graph tests:

```python
def test_render_fixture_graph_url_state_and_debug_readout(tmp_path: Path) -> None:
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
                        f"{handle.base_url}/_raya/graph/index.html"
                        "?page=reader-ux&q=projection&layout=connections",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(page)
                    assert page.locator("#graph-search").input_value() == "projection"
                    assert page.locator("#graph-layout").input_value() == "connections"
                    assert "reader-ux" in page.locator(
                        "[data-raya-graph-state-selected]"
                    ).inner_text()
                    assert "projection" in page.locator(
                        "[data-raya-graph-state-query]"
                    ).inner_text()
                    assert "connections" in page.locator(
                        "[data-raya-graph-state-layout]"
                    ).inner_text().lower()
                    assert "visible node" in page.locator(
                        "[data-raya-graph-state-visible]"
                    ).inner_text()
                    assert "page=reader-ux" in page.url
                    assert "q=projection" in page.url
                    assert "layout=connections" not in page.url

                    page.click('[data-raya-graph-edge-kind-filter="parent"]')
                    page.wait_for_function(
                        "() => new URL(window.location.href).searchParams.get('edges')"
                    )
                    assert "Parent" in page.locator(
                        "[data-raya-graph-state-hidden-edges]"
                    ).inner_text()
                    assert "edges=" in page.url

                    page.click('[data-raya-graph-group-filter="render-root"]')
                    page.wait_for_function(
                        "() => new URL(window.location.href).searchParams.get('groups')"
                    )
                    assert "hidden" in page.locator(
                        "[data-raya-graph-state-hidden-groups]"
                    ).inner_text().lower()

                    storage_state = page.evaluate(
                        "() => ({ local: Object.keys(localStorage), session: Object.keys(sessionStorage) })"
                    )
                    assert storage_state == {"local": [], "session": []}
                    assert requested_urls
                    assert all(url.startswith(f"{handle.base_url}/") for url in requested_urls)
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [x] **Step 2: Run e2e test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_url_state_and_debug_readout -q
```

Expected: fails because graph URL state is not initialized beyond `page` and no
debug readout exists.

Actual: failed because `#graph-search` did not initialize from `q=projection`.

### Task 3: Generate Graph State Readout Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Add readout HTML**

In `_render_graph_surface`, inside the graph inspector body after
`data-raya-graph-hover-status`, add:

```html
<section class="raya-graph-state" data-raya-graph-state-readout aria-label="Graph state">
  <h3>Graph state</h3>
  <dl>
    <div><dt>Selected</dt><dd data-raya-graph-state-selected>none</dd></div>
    <div><dt>Search</dt><dd data-raya-graph-state-query>none</dd></div>
    <div><dt>Layout</dt><dd data-raya-graph-state-layout>connections</dd></div>
    <div><dt>Visible</dt><dd data-raya-graph-state-visible>0 visible node(s), 0 visible edge(s)</dd></div>
    <div><dt>Hidden groups</dt><dd data-raya-graph-state-hidden-groups>none</dd></div>
    <div><dt>Hidden edges</dt><dd data-raya-graph-state-hidden-edges>none</dd></div>
    <div><dt>Neighborhood</dt><dd data-raya-graph-state-neighborhood>off</dd></div>
    <div><dt>Share URL</dt><dd><code data-raya-graph-state-url></code></dd></div>
  </dl>
</section>
```

- [x] **Step 2: Add compact CSS**

Add CSS rules for `.raya-graph-state`, `.raya-graph-state dl`,
`.raya-graph-state div`, `.raya-graph-state dt`, `.raya-graph-state dd`, and
`.raya-graph-state code` near existing graph detail CSS.

- [x] **Step 3: Run contract test and verify markup GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_static_graph_surface -q
```

Actual: covered by the combined focused GREEN run after Task 4.

### Task 4: Implement URL State Synchronization

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`

- [x] **Step 1: Add DOM handles and constants**

Read state readout elements with `document.querySelector` and define:

```javascript
  const defaultLayout = "connections";
  const graphLayouts = new Set(["connections", "topology", "cluster", "map", "radial", "list"]);
  const graphEdgeKinds = new Set(["navigation", "content", "prerequisite", "parent"]);
```

- [x] **Step 2: Add URL parsing helpers**

Implement helpers for current URL params, comma-list parsing, visible group and
edge serialization, and default omission.

- [x] **Step 3: Initialize controls from URL**

Implement `initializeGraphStateFromUrl()` so it:

- sets `selectedId` from `page` if valid;
- sets search value from `q`;
- sets layout from `layout` when valid;
- applies `groups` as the visible group set;
- applies `edges` as the visible edge-kind set;
- applies `neighborhood=1` only when `selectedId` exists;
- applies `expanded=1`, `list=0`, and `inspector=0`.

- [x] **Step 4: Update URL and readout from render state**

Implement `updateGraphUrlState()` with `history.replaceState` and
`updateGraphStateReadout(activeNodes, activeEdges)` with public state text.
Call both from `render()` after status text has been computed.

Review follow-up: non-render interactions now call the same sync path after
panel toggles and search-result selection, with the latest render counts reused
for the compact readout.

- [x] **Step 5: Avoid replacing URL during initial parse**

Initialization now applies URL state before the first render, and the first
render normalizes the URL after state is applied.

- [x] **Step 6: Run focused tests and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_url_state_and_debug_readout -q
```

Actual: both passed. Follow-up after review also passed:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_url_state_and_debug_readout -q
```

Actual: 1 passed.

### Task 5: Docs, Review, And Gates

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] **Step 1: Update docs**

Document URL-addressable graph state as a non-persistent static debugging and
orientation aid. State that URL parameters may encode graph query, selected
page, layout, visible groups/edges, neighborhood focus, expanded mode, and
panel state, but must not store personal learning state.

- [x] **Step 2: Request code review**

Use `superpowers:requesting-code-review` with a focused reviewer prompt before
final gates.

Actual: reviewer found URL/readout drift for panel toggles and search-result
selection. Both were verified against the codebase, fixed, and covered in the
focused browser test.

- [x] **Step 3: Run focused graph tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -k graph -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -k graph -q
```

Actual so far:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -k graph -q
```

Actual: 7 passed, 86 deselected.

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -k graph -q
```

Actual: 3 passed, 44 deselected.

- [x] **Step 4: Run canonical gates**

Run sequentially:

```bash
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

Actual:

```bash
./scripts/check-render-debug.sh
```

Actual: passed, 129 checks.

```bash
./scripts/check.sh
```

Actual: passed, including 479 tests.

```bash
./scripts/check-docker.sh
```

Actual: passed, including 479 tests in Docker.

- [x] **Step 5: Commit, push, and preview**

Commit as:

```bash
git add docs/superpowers/specs/2026-06-24-graph-url-state-debug-design.md docs/superpowers/plans/2026-06-24-graph-url-state-debug.md docs/foundation/20_learning_renderer_contract.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/graph.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add graph URL state debug readout"
git push origin new_rayalucaria
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --port 0
```

Actual:

```bash
git commit -m "Add graph URL state debug readout"
git push origin new_rayalucaria
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --port 0
```

Actual: committed, pushed to `origin/new_rayalucaria`, and preview served at
`http://127.0.0.1:43349/index.html`.
