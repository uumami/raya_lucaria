# Local Course Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local static course search page and command-bar link using generated page metadata only.

**Architecture:** Follow the existing local graph page pattern. The builder writes `_raya/search/index.html`, embeds a safe JSON payload, writes local `search.js`, and normal pages link to search through the top command bar. The browser filters an already-rendered fallback list; no fetches, Pagefind, CDN, or source paths are introduced.

**Tech Stack:** Python 3.10 static builder, generated HTML/CSS/JS, pytest, Playwright, current Glintstone render fixture.

---

## File Structure

- Create `packages/static/src/raya_static/search.py`: local search JavaScript resource.
- Modify `packages/static/src/raya_static/builder.py`: constants, resource writing, search surface rendering, command-bar link, search payload.
- Modify `packages/static/src/raya_static/rendering.py`: search page CSS and search command symbol.
- Modify `docs/foundation/20_learning_renderer_contract.md`: document local page-metadata search.
- Modify `tests/contracts/test_static_builder.py`: search surface contract checks.
- Modify `tests/e2e/test_preview_static_read_path.py`: preview/browser search checks and command count update.

## Task 1: Contract Test Search Surface

- [ ] **Step 1: Write failing contract assertions**

Add a test near `test_build_writes_local_visual_graph_surface` in `tests/contracts/test_static_builder.py`:

```python
def test_build_writes_local_course_search_surface(tmp_path: Path) -> None:
    course = _copy_render_fixture(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    site = course / "artifact" / "site"
    index_html = (site / "index.html").read_text(encoding="utf-8")
    search_html = (site / "_raya" / "search" / "index.html").read_text(encoding="utf-8")
    search_js = (site / "_raya" / "render" / "search.js").read_text(encoding="utf-8")

    assert 'href="_raya/search/index.html"' in index_html
    assert 'data-raya-surface="search"' in search_html
    assert '<script type="application/json" id="raya-search-data">' in search_html
    assert 'src="../render/search.js"' in search_html
    assert 'href="../render/rich.css"' in search_html
    assert 'href="../render/skin.css"' in search_html
    assert 'href="../../data/pages.json"' not in search_html
    assert "https://" not in search_html
    assert "http://" not in search_html
    assert "pagefind" not in search_html.lower()
    assert "graph-search" not in search_html
    assert "course/5_authoring_matrix" not in search_html
    assert "raya-search-results" in search_html
    assert "Authoring Matrix Fixture" in search_html
    assert "../../authoring-matrix/index.html" in search_html
    assert "raya-search-data" in search_js
    assert "fetch(" not in search_js
    assert "XMLHttpRequest" not in search_js
```

- [ ] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface -q
```

Expected: fail because `_raya/search/index.html` and `search.js` do not exist.

- [ ] **Step 3: Implement search surface and resource**

Create `packages/static/src/raya_static/search.py` with `SEARCH_SCRIPT_NAME = "search.js"` and `search_resources()`.

In `builder.py`, add:

```python
STATIC_SEARCH_PATH = Path(STATIC_RESOURCE_DIR) / "search" / "index.html"
```

Write `_write_search_resources(...)`, `_write_search_surface(...)`, `_render_search_surface(...)`, and `_browser_search_payload(...)`.

Call resource and surface writers during `build_course(...)` alongside graph writers.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface -q
```

Expected: pass.

## Task 2: Command Bar And CSS

- [ ] **Step 1: Update focused tests first**

Update the command-bar contract/e2e tests to expect four commands and a search command:

```python
assert '<a class="raya-command raya-command-search"' in html
assert 'aria-label="Open course search"' in html
assert 'href="../_raya/search/index.html"' in html
```

In the browser command-bar test:

```python
assert state["count"] == 4
assert state["searchHref"] == "_raya/search/index.html"
```

- [ ] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell tests/e2e/test_preview_static_read_path.py::test_render_fixture_command_bar_controls_are_dense_and_operable -q
```

Expected: fail because search command is not present.

- [ ] **Step 3: Implement command and CSS**

Update `_render_page(...)` to compute `search_href`.

Update `_render_top_command_bar(...)` signature to receive both `search_href` and `graph_href`, then render the `Search` command before `Graph`.

In `rendering.py`, add `.raya-command-search::before { content: "S"; }` and search page CSS for `.raya-search-page`, `.raya-search-controls`, `.raya-search-results`, `.raya-search-result-meta`, and `.raya-search-empty`.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell tests/contracts/test_static_builder.py::test_rich_css_defines_learning_shell_regions tests/e2e/test_preview_static_read_path.py::test_render_fixture_command_bar_controls_are_dense_and_operable -q
```

Expected: pass.

## Task 3: Browser Search Behavior

- [ ] **Step 1: Write failing e2e test**

Add `test_preview_serves_local_course_search_surface` in `tests/e2e/test_preview_static_read_path.py`:

```python
search_html = _fetch_text(f"{base_url}/_raya/search/index.html")
search_js = _fetch_text(f"{base_url}/_raya/render/search.js")
assert 'data-raya-surface="search"' in search_html
assert "pagefind" not in search_html.lower()
assert "fetch(" not in search_js
```

With Playwright, open desktop and mobile viewports, assert no horizontal overflow, fill `#raya-search-input` with `matrix`, and assert visible result text includes `Authoring Matrix Fixture` and status text reports visible result count.

- [ ] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_course_search_surface -q
```

Expected: fail before the behavior exists.

- [ ] **Step 3: Implement browser filtering**

In `search.py`, read `#raya-search-data`, normalize query and result text, hide nonmatching `[data-raya-search-result]` list items, and update `#raya-search-status`. Keep all results visible when query is empty.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_course_search_surface -q
```

Expected: pass.

## Task 4: Documentation, Review, And Full Verification

- [ ] **Step 1: Document current behavior**

Update `docs/foundation/20_learning_renderer_contract.md` to list local page-metadata search as current renderer behavior and preserve the non-goals around no inferred recommendations/progress.

- [ ] **Step 2: Run focused checks**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell tests/contracts/test_static_builder.py::test_rich_css_defines_learning_shell_regions tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_course_search_surface tests/e2e/test_preview_static_read_path.py::test_render_fixture_command_bar_controls_are_dense_and_operable -q
```

- [ ] **Step 3: Request independent review**

Ask a reviewer to inspect local/static constraints, no source/artifact path leakage, accessibility labels, and whether search stays metadata-only.

- [ ] **Step 4: Run full verification**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py -q
./scripts/check-render-debug.sh
```

- [ ] **Step 5: Commit**

```bash
git add packages/static/src/raya_static/search.py packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py docs/foundation/20_learning_renderer_contract.md tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py docs/superpowers/specs/2026-06-19-local-course-search-design.md docs/superpowers/plans/2026-06-19-local-course-search.md
git commit -m "Add local course search surface"
```

## Self-Review

- The plan covers search surface generation, local JavaScript, command-bar integration, CSS, docs, tests, review, and full verification.
- It does not add Pagefind, external resources, persistent state, source paths, body scraping, or dynamic study behavior.
- It reuses current graph-page/static-resource patterns rather than introducing a new frontend stack.
