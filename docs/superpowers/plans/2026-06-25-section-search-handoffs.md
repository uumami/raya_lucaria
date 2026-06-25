# Section Search Handoffs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add public section-level search subresults and browser-verified static workspace handoffs.

**Architecture:** Extend the existing static builder search record with sanitized public section records extracted from rendered article headings and following public content. Render those records inside the static Search workspace and teach the local search script to match and reveal section subresults without fetch, storage, external libraries, or browser-side MathJax.

**Tech Stack:** Python 3.10, pytest, Playwright e2e tests, generated static HTML/CSS/JS, JSON Schema.

---

## Files

- Modify `packages/static/src/raya_static/builder.py` for section extraction, search payload, search index output, and search result markup.
- Modify `packages/static/src/raya_static/search.py` for section matching and context text.
- Modify `packages/static/src/raya_static/rendering.py` for compact section-result styling.
- Modify `packages/schema/src/raya_schema/schemas/search-index.schema.json` for optional public section records.
- Modify `tests/contracts/test_static_builder.py` for search payload/index contracts.
- Modify `tests/e2e/test_preview_static_read_path.py` for browser search and handoff checks.
- Modify `docs/foundation/17_rendering_execution_plan.md`, `docs/foundation/20_learning_renderer_contract.md`, and role guides only where needed to describe visible behavior.

### Task 1: Contract Test For Public Section Search Records

- [ ] **Step 1: Write the failing contract test**

Add assertions to `test_build_writes_static_search_workspace` in `tests/contracts/test_static_builder.py`:

```python
    allowed_section_keys = {
        "anchor",
        "id",
        "search_snippet",
        "search_text",
        "title",
        "url",
    }
    for page in search_payload["pages"]:
        assert "sections" in page
        assert isinstance(page["sections"], list)
        for section in page["sections"]:
            assert set(section) == allowed_section_keys
            assert section["id"].startswith(f"{page['id']}:")
            assert section["url"].startswith(page["url"] + "#")
            assert section["anchor"]
            assert section["title"]
            assert section["search_snippet"]

    matrix_sections = pages_by_id["authoring-matrix"]["sections"]
    section_by_title = {section["title"]: section for section in matrix_sections}
    assert "Matrix norm fixture" in section_by_title
    assert section_by_title["Matrix norm fixture"]["url"].endswith(
        "../../authoring-matrix/index.html#matrix-norm-fixture"
    )
    assert "matrix norm fixture" in (
        section_by_title["Matrix norm fixture"]["search_text"].lower()
    )
```

Also assert `search-index.json` mirrors the `sections` key and that forbidden tokens do not appear in serialized section data.

- [ ] **Step 2: Run the contract test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_static_search_workspace -q
```

Expected: FAIL because `sections` is missing from search payload/index records.

- [ ] **Step 3: Implement public section extraction**

In `packages/static/src/raya_static/builder.py`, add a small parser near `_PublicArticleTextParser` that:

- records `h2`-`h6` elements with an `id`,
- gathers public text until the next heading of the same or higher level,
- skips the same private/rendered classes and tags as `_PublicArticleTextParser`,
- sanitizes text with `_sanitize_public_search_text`,
- emits records with `id`, `anchor`, `title`, `search_text`, and `search_snippet`.

Store the list in each `search_record` as `sections`.

- [ ] **Step 4: Extend payload/index/schema**

Add `sections` to `_browser_search_payload`, `_search_index`, and `search-index.schema.json`. Preserve version `1` and require `sections` for generated records.

- [ ] **Step 5: Run the contract test and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_static_search_workspace -q
```

Expected: PASS.

### Task 2: Search UI Section Subresults

- [ ] **Step 1: Write failing UI contract assertions**

In `test_build_writes_static_search_workspace`, assert the generated search page contains:

```python
    assert "raya-search-result-sections" in search_html
    assert "Section matches" in search_html
    assert 'href="../../authoring-matrix/index.html#matrix-norm-fixture"' in search_html
    assert "data-raya-search-section" in search_html
```

Assert `search.js` contains section matching identifiers:

```python
    assert "matchingSections" in search_script
    assert "data-raya-search-section" in search_script
```

- [ ] **Step 2: Run the contract test and verify RED**

Run the same focused contract test. Expected: FAIL because section markup and script behavior are not present.

- [ ] **Step 3: Render compact section links**

In `_render_search_surface`, render a nested list for `page["sections"]` with `data-raya-search-section`, `data-raya-search-section-text`, and links to section URLs.

- [ ] **Step 4: Update local search script**

In `packages/static/src/raya_static/search.py`, include page section `search_text` in `pageText`; add `matchingSections(page, query)` and hide/show section list items on render. Update context text to include `Section matches: N` when a query has matching sections.

- [ ] **Step 5: Add CSS for section subresults**

In `packages/static/src/raya_static/rendering.py`, add styling for `.raya-search-result-sections`, `.raya-search-result-section-list`, and `.raya-search-result-section` that keeps links compact and readable on desktop/mobile.

- [ ] **Step 6: Run focused contract test and verify GREEN**

Run the same focused contract test. Expected: PASS.

### Task 3: Browser Handoff Coverage

- [ ] **Step 1: Write failing browser tests**

In `tests/e2e/test_preview_static_read_path.py`, add or extend tests to serve the render fixture and verify:

- `_raya/search/index.html?q=matrix%20norm` shows `Authoring Matrix Fixture` and the `Matrix norm fixture` section link,
- `_raya/search/index.html?page=authoring-matrix` shows a focus notice and Clear resets to all results,
- `_raya/graph/index.html?page=reader-ux` first-paints a selected node and at least one visible edge,
- `_raya/practice/index.html?page=reader-ux`, `_raya/tasks/index.html?page=authoring-matrix`, and `_raya/schedule/index.html?page=authoring-matrix` show their page-focus notices and reset with Escape or Clear.

- [ ] **Step 2: Run browser tests and verify RED**

Run the new focused test(s):

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::<new_test_name> -q
```

Expected: FAIL before the implementation or before selectors are wired.

- [ ] **Step 3: Adjust behavior only if needed**

If tests reveal missing handoff behavior, patch the relevant local script or markup with the smallest change. Do not add persistence or runtime fetch.

- [ ] **Step 4: Run browser tests and verify GREEN**

Run the focused tests again. Expected: PASS.

### Task 4: Documentation And Verification

- [ ] **Step 1: Update docs**

Update foundation and role docs to state that Search can show public section matches and that workspace handoffs are URL-only static review aids.

- [ ] **Step 2: Run focused verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_static_search_workspace -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::<new_test_name> -q
./scripts/check-render-debug.sh
```

- [ ] **Step 3: Request code review**

Use `superpowers:requesting-code-review` with at least one independent agent focused on contract/static-safety risks and one focused on browser UX.

- [ ] **Step 4: Run archive gates**

Run sequentially:

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

- [ ] **Step 5: Commit and push**

Commit the passing slice and push `new_rayalucaria` to `origin/new_rayalucaria`.
