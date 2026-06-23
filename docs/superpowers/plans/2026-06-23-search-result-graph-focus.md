# Search Result Graph Focus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add static graph-focus links to Course Search results so readers can move from a found page to the graph focused on that same page.

**Architecture:** Extend the existing static search payload with one generated `graph_url` field per page. Render that field as a secondary result action while keeping the current primary page link and keyboard Enter behavior. Update contracts, browser checks, and role docs to keep the feature clearly structural and metadata-only.

**Tech Stack:** Python 3.10 static builder, local generated JavaScript/CSS, pytest, Playwright e2e tests, Markdown docs.

---

### Task 1: Contract Tests For Search Graph Focus

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write the failing contract assertions**

In `test_build_writes_local_course_search_surface`, add assertions that search results and payload entries include graph-focus links:

```python
    assert (
        'class="raya-search-result-actions"' in search_html
    )
    assert (
        'class="raya-search-result-graph"' in search_html
    )
    assert (
        'href="../graph/index.html?page=authoring-matrix"' in search_html
    )
    assert "View in graph" in search_html
```

Update `allowed_page_keys` in the same test:

```python
    allowed_page_keys = {
        "graph_url",
        "hierarchy_label",
        "id",
        "nav_title",
        "status",
        "summary",
        "tags",
        "title",
        "url",
    }
```

Add per-page graph URL checks in the payload loop:

```python
        assert page["graph_url"].startswith("../graph/index.html?page=")
        assert page["id"] in page["graph_url"]
        assert not page["graph_url"].startswith("../../data/")
```

- [ ] **Step 2: Run the focused contract test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface
```

Expected: FAIL because `graph_url`, `.raya-search-result-actions`, and `.raya-search-result-graph` do not exist yet.

### Task 2: Browser Test For Search-To-Graph Handoff

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Extend the Course Search browser test**

In the existing render-fixture Course Search Playwright test, after searching for `matrix`, capture the graph-focus link for the visible `authoring-matrix` result and open it:

```python
                        graph_focus_href = page.locator(
                            '[data-raya-search-result="authoring-matrix"] '
                            '.raya-search-result-graph'
                        ).get_attribute("href")
                        assert graph_focus_href == "../graph/index.html?page=authoring-matrix"
                        page.click(
                            '[data-raya-search-result="authoring-matrix"] '
                            '.raya-search-result-graph'
                        )
                        page.wait_for_url("**/_raya/graph/index.html?page=authoring-matrix")
                        page.wait_for_selector(
                            '[data-raya-graph-detail-panel]:not([hidden])'
                        )
                        assert (
                            "Authoring Matrix Fixture"
                            in page.locator("[data-raya-graph-detail-title]").inner_text()
                        )
                        _assert_no_horizontal_overflow(page)
```

- [ ] **Step 2: Run the focused browser test and verify RED**

Run the exact test containing Course Search behavior:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k "course_search"
```

Expected: FAIL because the graph-focus result link does not exist yet.

### Task 3: Implement Static Search Graph Links

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Generate graph URLs in the search payload**

In `_browser_search_payload`, add:

```python
                "graph_url": _href_with_query(
                    _relative_href(
                        STATIC_SEARCH_PATH.as_posix(),
                        STATIC_GRAPH_PATH.as_posix(),
                    ),
                    {"page": page.id},
                ),
```

- [ ] **Step 2: Render the secondary action**

In `_render_static_search_page`, inside each search result `<li>`, keep the primary title link unchanged and add:

```python
            '<p class="raya-search-result-actions">'
            f'<a class="raya-search-result-graph" href="{html.escape(page["graph_url"])}" '
            f'aria-label="View {html.escape(page["title"], quote=True)} in course graph">'
            "View in graph</a>"
            "</p>"
```

after the metadata paragraph.

- [ ] **Step 3: Style the secondary action**

In `packages/static/src/raya_static/rendering.py`, add compact styles near the existing search result styles:

```css
.raya-search-result-actions {
  margin: 0.65rem 0 0;
}

.raya-search-result-graph {
  display: inline-flex;
  align-items: center;
  min-height: 2.25rem;
  padding: 0.25rem 0.65rem;
  border: 1px solid var(--raya-color-border);
  border-radius: 0.35rem;
  background: color-mix(in srgb, var(--raya-color-surface) 88%, var(--raya-color-accent-soft));
  color: var(--raya-color-link);
  font-weight: 700;
}
```

- [ ] **Step 4: Run focused tests and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k "course_search"
```

Expected: both pass.

### Task 4: Documentation Updates

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Update the renderer contract**

In the Local course search row and paragraph, state that search may expose graph-focus links generated from stable page IDs and rendered graph URLs.

- [ ] **Step 2: Update role docs**

Students/estudiantes: describe `View in graph` as a way to inspect where a found page sits in the course graph.

Contributors/colaboradores and Agents/agentes: state that search graph-focus links must remain metadata-only, local, deployment-neutral, and non-recommendation language.

- [ ] **Step 3: Check for forbidden learner-state wording**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_render_fixture_search_graph_course_map_visible_text_avoids_learner_state_language
```

Expected: pass.

### Task 5: Verification, Review, Commit, Push

**Files:**
- All modified files

- [ ] **Step 1: Run focused renderer debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: pass.

- [ ] **Step 2: Run host archive gate**

Run:

```bash
./scripts/check.sh
```

Expected: pass.

- [ ] **Step 3: Run Docker archive gate**

Run:

```bash
./scripts/check-docker.sh
```

Expected: pass.

- [ ] **Step 4: Request code review**

Use `superpowers:requesting-code-review` and send one reviewer the complete diff for Search/Graph contract and UX risks.

- [ ] **Step 5: Commit and push**

Run:

```bash
git status --short
git add docs/superpowers/specs/2026-06-23-search-result-graph-focus-design.md \
  docs/superpowers/plans/2026-06-23-search-result-graph-focus.md \
  docs/foundation/20_learning_renderer_contract.md \
  docs/guides/en/students/index.md \
  docs/guides/en/contributors/index.md \
  docs/guides/en/agents/index.md \
  docs/guides/es/estudiantes/index.md \
  docs/guides/es/colaboradores/index.md \
  docs/guides/es/agentes/index.md \
  packages/static/src/raya_static/builder.py \
  packages/static/src/raya_static/rendering.py \
  tests/contracts/test_static_builder.py \
  tests/e2e/test_preview_static_read_path.py
git commit -m "Add search result graph focus links"
git push origin new_rayalucaria
```

Expected: branch `new_rayalucaria` is pushed to the matching GitHub branch.
