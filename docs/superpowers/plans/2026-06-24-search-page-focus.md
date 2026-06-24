# Search Page Focus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make generated Search accept exact `?page=<page-id>` focus and update Graph selected-page search links to use it.

**Architecture:** Reuse the existing embedded Search payload and discovery URL-state pattern. Add page-focus parsing to `search.js`, change generated `search_url` values to `page` queries, and verify Graph-to-Search opens the exact same page context without storage or runtime fetching.

**Tech Stack:** Python 3.10 static builder, generated HTML/CSS/JavaScript, pytest, Playwright.

---

### Task 1: Contract Tests For Exact Search Page Focus

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Add failing contract assertions**

In `test_build_writes_local_course_search_surface`, change the generated Search
payload and script assertions so Search page URLs and script tokens require
exact page focus:

```python
    assert 'href="../search/index.html?page=authoring-matrix"' in graph_html
    assert pages_by_id["authoring-matrix"]["search_url"] == (
        "../search/index.html?page=authoring-matrix"
    )
    assert 'params.get("page")' in search_script
    assert "activePage" in search_script
    assert "matchesPage" in search_script
```

Also replace the older broad assertion:

```python
        assert node["search_url"].startswith("../search/index.html?q=")
```

with:

```python
        assert node["search_url"].startswith("../search/index.html?page=")
        assert node["id"] in node["search_url"]
```

- [x] **Step 2: Run contract test to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface -q
```

Expected: fails because graph/search payload links still use `q=` and the
Search script does not parse `page`.

Actual: failed because Graph/Search payload `search_url` values still used
`q=` title queries.

### Task 2: Browser Test For Search `?page=` Focus

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add a matrix-like distractor page to the Search fixture setup**

Inside `test_preview_serves_local_course_search_surface`, before preview
creation, add:

```python
    distractor = course / "course" / "6_matrix_reference" / "0_index.md"
    distractor.parent.mkdir(parents=True)
    distractor.write_text(
        "\n".join(
            [
                "---",
                "id: matrix-reference",
                "title: Matrix Reference",
                "summary: Matrix vocabulary without authoring matrix tasks.",
                "status: ready",
                "---",
                "",
                "# Matrix Reference",
                "",
                "This page makes fuzzy matrix search broader than exact page focus.",
                "",
            ]
        ),
        encoding="utf-8",
    )
```

- [x] **Step 2: Add exact page-focus browser assertions**

After the existing `q=Authoring Matrix Fixture` Search assertions and before the
Graph navigation assertion, add:

```python
                        page.goto(
                            f"{base_url}/_raya/search/index.html?page=authoring-matrix",
                            wait_until="networkidle",
                        )
                        assert page.input_value("#raya-search-input") == ""
                        assert (
                            page.locator(
                                "#raya-search-results [data-raya-search-result]:visible"
                            ).count()
                            == 1
                        )
                        exact_card = page.locator(
                            '[data-raya-search-result="authoring-matrix"]'
                        )
                        assert exact_card.is_visible()
                        assert (
                            exact_card.get_attribute("data-raya-search-active")
                            == "true"
                        )
                        assert page.locator(
                            '[data-raya-search-result="matrix-reference"]'
                        ).is_hidden()
                        assert (
                            "Authoring Matrix Fixture"
                            in page.locator(
                                "[data-raya-search-context-title]"
                            ).inner_text()
                        )
                        page.goto(
                            (
                                f"{base_url}/_raya/search/index.html"
                                "?page=authoring-matrix&q=Matrix"
                            ),
                            wait_until="networkidle",
                        )
                        assert page.input_value("#raya-search-input") == "Matrix"
                        assert (
                            page.locator(
                                "#raya-search-results [data-raya-search-result]:visible"
                            ).count()
                            == 1
                        )
                        page.goto(
                            (
                                f"{base_url}/_raya/search/index.html"
                                "?page=authoring-matrix&q=zz-no-result"
                            ),
                            wait_until="networkidle",
                        )
                        assert page.locator("#raya-search-empty").is_visible()
                        page.click("#raya-search-clear")
                        assert (
                            page.locator(
                                "#raya-search-results [data-raya-search-result]:visible"
                            ).count()
                            > 1
                        )
                        assert page.locator(
                            '[data-raya-search-result="matrix-reference"]'
                        ).is_visible()
                        page.goto(
                            f"{base_url}/_raya/search/index.html?page=missing-page",
                            wait_until="networkidle",
                        )
                        assert page.locator("#raya-search-empty").is_visible()
                        page.press("#raya-search-input", "Escape")
                        assert page.locator("#raya-search-empty").is_hidden()
```

- [x] **Step 3: Update Graph-to-Search browser assertion**

Replace the existing Graph detail Search link assertion:

```python
                            .endswith(
                                "/_raya/search/index.html?q=Authoring%20Matrix%20Fixture"
                            )
```

with:

```python
                            .endswith(
                                "/_raya/search/index.html?page=authoring-matrix"
                            )
```

Then click the link and assert Search opens scoped:

```python
                        page.click("[data-raya-graph-detail-search-link]")
                        page.wait_for_url("**/_raya/search/index.html?page=authoring-matrix")
                        assert (
                            page.locator(
                                "#raya-search-results [data-raya-search-result]:visible"
                            ).count()
                            == 1
                        )
```

- [x] **Step 4: Run browser test to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_course_search_surface -q
```

Expected: fails because Search ignores `page=` and Graph still links to `q=`.

Actual: failed because `?page=authoring-matrix` still showed all visible Search
results.

### Task 3: Implement Search Page Focus

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/search.py`

- [x] **Step 1: Change generated public search URLs**

In `_public_discovery_page_payload()`, replace:

```python
        "search_url": _href_with_query(
            _relative_href(search_from_path, STATIC_SEARCH_PATH.as_posix()),
            {"q": page.title},
        ),
```

with:

```python
        "search_url": _href_with_query(
            _relative_href(search_from_path, STATIC_SEARCH_PATH.as_posix()),
            {"page": page.id},
        ),
```

- [x] **Step 2: Add page-focus state to Search script**

In `packages/static/src/raya_static/search.py`, after `let activeIndex = -1;`,
add:

```javascript
  let activePage = "";
```

Add helper:

```javascript
  function matchesPage(item) {
    return !activePage ||
      (item.getAttribute("data-raya-search-result") || "") === activePage;
  }
```

Update `render()` so the matched expression composes page focus and query:

```javascript
      const matched = matchesPage(item) && (text ? fuzzyMatch(query, text) : false);
```

- [x] **Step 3: Parse initial `page` and reset it**

Replace `initialQuery()` with:

```javascript
  function initialParams() {
    try {
      const params = new URLSearchParams(window.location.search || "");
      return {
        page: params.get("page") || "",
        query: params.get("q") || "",
      };
    } catch {
      return { page: "", query: "" };
    }
  }
```

Update `clearSearch()` so it clears page focus:

```javascript
  function clearSearch() {
    input.value = "";
    activePage = "";
    activeIndex = -1;
    render();
    input.focus();
  }
```

Update startup:

```javascript
  const params = initialParams();
  activePage = params.page;
  input.value = params.query;
  render();
```

- [x] **Step 4: Auto-activate the focused page result**

In `render()`, before `setActiveResult(...)`, set the active index from the
focused page when present:

```javascript
    if (activePage) {
      const visible = visibleResults();
      activeIndex = visible.findIndex((item) => (
        (item.getAttribute("data-raya-search-result") || "") === activePage
      ));
    }
```

- [x] **Step 5: Run focused tests and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_course_search_surface -q
```

Expected: both pass.

Actual: passed with `test_build_writes_local_visual_graph_surface`,
`test_build_writes_local_course_search_surface`, and
`test_preview_serves_local_course_search_surface`.

### Task 4: Documentation

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] **Step 1: Update renderer contract**

Add Search page-focus language where Local course search and generated discovery
cards are described:

```markdown
Search may accept URL-only exact page focus such as `?page=<page-id>` from
Graph or other generated workspace handoffs. Page focus narrows visible Search
results to that public page ID until Clear or Escape restores all visible
results. This is structural URL state only, not learner state.
```

- [x] **Step 2: Update agent guides**

In the English and Spanish agent guide pages, add guidance that agents should
verify `?page=<page-id>` Search focus as exact structural state, while also
checking no storage, fetch, external requests, source/private paths, progress,
mastery, or recommendation wording is introduced.

### Task 5: Review, Gates, Commit, Push, Preview

**Files:**
- All modified files from prior tasks.

- [x] **Step 1: Request code review**

Use `superpowers:requesting-code-review` with a focused reviewer prompt covering
the current diff and exact Search page focus requirements.

Actual: reviewer found no blocking issues and identified one residual direct
test gap for `?page=<page-id>&q=<query>` composition. The gap was addressed in
the browser test.

- [x] **Step 2: Run focused checks**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_course_search_surface -q
```

Actual: passed with `test_build_writes_local_visual_graph_surface`,
`test_build_writes_local_course_search_surface`, and
`test_preview_serves_local_course_search_surface` after adding page+query
composition coverage.

- [x] **Step 3: Run canonical gates sequentially**

Run:

```bash
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

Actual:

```text
./scripts/check-render-debug.sh
passed; render-debug-report passed with 129 checks

./scripts/check.sh
passed; pytest reported 479 passed in 524.67s

./scripts/check-docker.sh
passed; container pytest reported 479 passed in 700.34s
```

- [ ] **Step 4: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-24-search-page-focus-design.md docs/superpowers/plans/2026-06-24-search-page-focus.md docs/foundation/20_learning_renderer_contract.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/search.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add exact search page focus"
git push origin new_rayalucaria
```

- [ ] **Step 5: Start local preview**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --port 0
```

Report the preview URL and the Search URL with exact page focus:

```text
/_raya/search/index.html?page=authoring-matrix
```

## Self-Review

- The plan covers exact Search `?page=` parsing, Graph search-link generation,
  Clear/Escape reset, docs, focused tests, review, gates, commit, push, and
  preview.
- No source schema or artifact contract change is required.
- No persistent learner state, fetch, external resource, progress, mastery, or
  recommendation behavior is introduced.
