# Page-Aware Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add static page-context deep links so course pages can open local search and graph already focused on the current page.

**Architecture:** Keep page context in transient URL query parameters generated at build time. Search and graph scripts read those parameters from their own static page, update existing local UI state, and continue using embedded metadata only.

**Tech Stack:** Python static builder, embedded vanilla JavaScript resources, pytest contract tests, Playwright e2e preview tests.

---

### Task 1: Generated Page Context Links

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Test: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Write the failing test**

Add assertions to `test_build_writes_local_visual_graph_surface` and `test_build_writes_local_course_search_surface` proving rendered course pages include query-context links:

```python
assert 'href="_raya/graph/index.html?page=render-root"' in index_html
assert 'href="_raya/search/index.html?q=Raya%20Lucaria%20Render%20Fixture"' in index_html
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface -q
```

Expected: FAIL because the command bar links currently have no query context.

- [x] **Step 3: Write minimal implementation**

In `packages/static/src/raya_static/builder.py`, import `quote` from `urllib.parse`, create a helper that appends encoded query parameters to relative hrefs, and use it in `_render_page`:

```python
search_href = _href_with_query(
    _relative_href(page.output_path, STATIC_SEARCH_PATH.as_posix()),
    {"q": page.title},
)
graph_href = _href_with_query(
    _relative_href(page.output_path, STATIC_GRAPH_PATH.as_posix()),
    {"page": page.id},
)
```

- [x] **Step 4: Run test to verify it passes**

Run the same focused command. Expected: PASS.

### Task 2: Search Query Bootstrap

**Files:**
- Modify: `packages/static/src/raya_static/search.py`
- Test: `tests/contracts/test_static_builder.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Write the failing tests**

In `test_build_writes_local_course_search_surface`, assert:

```python
assert "URLSearchParams" in search_script
assert 'params.get("q")' in search_script
```

In `test_preview_serves_local_course_search_surface`, after the regular search checks, navigate to:

```python
page.goto(
    f"{base_url}/_raya/search/index.html?q=Authoring%20Matrix%20Fixture",
    wait_until="networkidle",
)
assert page.input_value("#raya-search-input") == "Authoring Matrix Fixture"
assert "Authoring Matrix Fixture" in page.locator("#raya-search-results").inner_text()
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_course_search_surface -q
```

Expected: FAIL because search does not read URL parameters yet.

- [x] **Step 3: Implement search bootstrap**

In `packages/static/src/raya_static/search.py`, read `q` with `URLSearchParams`, assign it to the input before the first `render()`, and keep Clear/Escape behavior unchanged.

- [x] **Step 4: Run tests to verify they pass**

Run the same focused command. Expected: PASS.

### Task 3: Graph Page Focus Bootstrap

**Files:**
- Modify: `packages/static/src/raya_static/graph.py`
- Test: `tests/contracts/test_static_builder.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Write the failing tests**

In `test_build_writes_local_visual_graph_surface`, assert:

```python
assert "URLSearchParams" in graph_script
assert 'params.get("page")' in graph_script
```

In `test_preview_serves_local_visual_graph_surface`, navigate to:

```python
page.goto(
    f"{base_url}/_raya/graph/index.html?page=authoring-matrix",
    wait_until="networkidle",
)
page.wait_for_selector("[data-raya-graph-detail-panel]:not([hidden])")
assert "Authoring Matrix Fixture" in page.locator("[data-raya-graph-detail-title]").inner_text()
assert page.locator(
    '#raya-graph-list [data-raya-graph-node="authoring-matrix"]'
).evaluate("node => node.classList.contains('is-active')")
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: FAIL because graph does not read page focus from URL parameters yet.

- [x] **Step 3: Implement graph bootstrap**

In `packages/static/src/raya_static/graph.py`, read `page`, validate it against `nodesById`, set `selectedId` before initial `renderDetail()` and `render()`, and do not persist the value.

- [x] **Step 4: Run tests to verify they pass**

Run the same focused command. Expected: PASS.

### Task 4: Documentation And Verification

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: role docs in `docs/guides/en/` and `docs/guides/es/`

- [x] **Step 1: Update docs**

Document that search/graph may accept transient query context from generated page links, but may not persist it or treat it as learner state.

- [x] **Step 2: Run focused verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_course_search_surface -q
git diff --check
```

Expected: tests pass and whitespace check is clean.

- [x] **Step 3: Run full gates before completion claim**

Run:

```bash
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: all commands exit 0.
