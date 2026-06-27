# Graph Key Object Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Make Graph search match generated public key-object labels and select the owning page.

**Architecture:** Add key-object fields from each graph node to the existing `nodeSearchText(node)` haystack. Keep Graph search page-level and reuse the current selected-page inspector for object anchor jumps.

**Tech Stack:** Python static builder tests, generated vanilla JavaScript, Playwright e2e, pytest.

---

### Task 1: Failing Graph Search Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add failing browser test**

Add a focused test near the other Graph search tests:

```python
def test_render_fixture_graph_search_matches_key_object_text(tmp_path: Path) -> None:
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
        base_url = handle.base_url
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
                        f"{base_url}/_raya/graph/index.html",
                        wait_until="networkidle",
                    )
                    page.fill("#graph-search", "projection triangle")
                    page.wait_for_function(
                        "() => new URL(window.location.href).searchParams.get('page') === 'reader-ux'"
                    )
                    state = page.evaluate(
                        """() => ({
                          selected: document
                            .querySelector('[data-raya-graph-state-selected]')
                            ?.textContent.trim() || '',
                          title: document
                            .querySelector('[data-raya-graph-detail-title]')
                            ?.textContent.trim() || '',
                          keyObjects: Array.from(
                            document.querySelectorAll('[data-raya-graph-detail-key-objects] a')
                          ).map((link) => ({
                            text: link.textContent.trim(),
                            href: link.getAttribute('href') || '',
                          })),
                          activeListText: document
                            .querySelector('#raya-graph-list [data-raya-graph-node="reader-ux"]')
                            ?.textContent.trim() || '',
                          storage: [
                            Object.keys(localStorage),
                            Object.keys(sessionStorage),
                          ],
                          overflow: Math.ceil(
                            document.documentElement.scrollWidth - window.innerWidth
                          ),
                        })"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert "reader-ux" in state["selected"]
    assert state["title"] == "Projection Residuals"
    assert "Projection Residuals" in state["activeListText"]
    assert any(
        item["text"].startswith("Figure 4.1 Projection triangle")
        and item["href"].endswith("/reader-ux/index.html#raya-object-orthogonal-figure")
        for item in state["keyObjects"]
    )
    assert state["storage"] == [[], []]
    assert state["overflow"] <= 1
    assert requested_urls
    assert all(url.startswith(f"{base_url}/") for url in requested_urls)
```

- [x] **Step 2: Run RED test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_search_matches_key_object_text
```

Expected: FAIL because `projection triangle` does not match `reader-ux` through `nodeSearchText(node)`.

### Task 2: Graph Search Haystack

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`

- [x] **Step 1: Add key-object fields to `nodeSearchText(node)`**

In `nodeSearchText(node)`, add this expression before tags:

```javascript
Array.isArray(node.key_objects)
  ? node.key_objects.map((item) => [
    item.reference,
    item.kind,
    item.title,
    item.anchor,
  ].join(" ")).join(" ")
  : "",
```

- [x] **Step 2: Run GREEN test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_search_matches_key_object_text
```

Expected: PASS.

### Task 3: Verification, Review, Commit, Push

**Files:**
- No additional source files expected.

- [x] **Step 1: Run focused graph tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_search_matches_key_object_text tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_url_state_and_debug_readout
```

Expected: PASS.

- [x] **Step 2: Run render-debug**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS.

- [x] **Step 3: Request independent review**

Ask a reviewer to inspect the graph search change for public-data-only indexing, no storage/fetch regressions, no graph semantic drift, and test coverage.

- [x] **Step 4: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-27-graph-key-object-search-design.md docs/superpowers/plans/2026-06-27-graph-key-object-search.md packages/static/src/raya_static/graph.py tests/e2e/test_preview_static_read_path.py
git commit -m "Index key objects in graph search"
git push origin new_rayalucaria
```
