# Navigation Workspace Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Make static search and graph easier to use as one navigation workspace while preserving reset renderer constraints.

**Architecture:** Search behavior stays in `packages/static/src/raya_static/search.py`; graph/search markup stays in `builder.py`; styling stays in `rendering.py`. The implementation only consumes embedded generated metadata and local static resources.

**Tech Stack:** Python 3.10 static builder, local vanilla JavaScript, Playwright e2e tests, pytest contract tests.

---

## Task 1: RED Tests For Search And Graph Workspace Polish

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add contract assertions for new static markup**

In `test_build_writes_local_visual_graph_surface`, assert graph legend and help
markup exist and forbidden runtime tokens remain absent:

```python
assert 'class="raya-graph-legend"' in graph_html
assert 'data-raya-graph-legend="node"' in graph_html
assert 'data-raya-graph-help' in graph_html
assert "<summary>Graph controls</summary>" in graph_html
assert "recommend" not in graph_html.lower()
assert "progress" not in graph_html.lower()
assert "mastery" not in graph_html.lower()
assert "completion" not in graph_html.lower()
```

In `test_build_writes_local_course_search_surface`, assert clear button and
active-result hooks exist:

```python
assert 'id="raya-search-clear"' in search_html
assert 'data-raya-search-active="false"' in search_html
assert "levenshtein" in search_script
assert "setActiveResult" in search_script
assert "raya-search-clear" in search_script
assert "window.location.href" in search_script
assert "localStorage" not in search_script
assert "sessionStorage" not in search_script
```

- [x] **Step 2: Add browser assertions for fuzzy and keyboard search**

In `test_preview_serves_local_course_search_surface`, after the existing
`matrix` query check, add:

```python
page.fill("#raya-search-input", "matrx")
page.wait_for_function(
    """() => document
      .querySelector('#raya-search-status')
      ?.textContent
      ?.includes('visible result')"""
)
assert "Authoring Matrix Fixture" in page.locator("#raya-search-results").inner_text()
page.press("#raya-search-input", "ArrowDown")
active = page.locator('#raya-search-results [data-raya-search-active="true"]')
assert active.count() == 1
active_href = active.locator("a").evaluate("node => node.href")
with page.expect_navigation():
    page.press("#raya-search-input", "Enter")
assert page.url == active_href
page.goto(f"{base_url}/_raya/search/index.html", wait_until="networkidle")
page.fill("#raya-search-input", "matrix")
page.click("#raya-search-clear")
assert page.input_value("#raya-search-input") == ""
assert page.locator('#raya-search-results [data-raya-search-active="true"]').count() == 0
```

- [x] **Step 3: Add browser assertions for graph legend/help**

In `test_preview_serves_local_visual_graph_surface`, after loading the graph
page, add:

```python
assert page.locator(".raya-graph-legend").is_visible()
assert page.locator("[data-raya-graph-legend='node']").is_visible()
assert page.locator("[data-raya-graph-help]").is_visible()
assert page.locator("[data-raya-graph-help]").get_attribute("open") is None
page.locator("[data-raya-graph-help] summary").click()
assert "Search" in page.locator("[data-raya-graph-help]").inner_text()
```

- [x] **Step 4: Run RED tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_course_search_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: FAIL because the new graph legend/help markup, search clear button,
fuzzy search function, active-result state, and keyboard navigation are absent.

## Task 2: Implement Static Markup And Search Interactions

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/search.py`

- [x] **Step 1: Add graph legend/help markup in `builder.py`**

Add a legend section after graph group chips and a closed help disclosure before
the graph canvas. Use static text only and no external links.

- [x] **Step 2: Add search clear button markup in `builder.py`**

Render a button in `.raya-search-controls`:

```html
<button id="raya-search-clear" type="button">Clear</button>
```

Set initial result state on each result item:

```html
data-raya-search-active="false"
```

- [x] **Step 3: Replace search matching with fuzzy matching in `search.py`**

Add local `levenshtein` and `fuzzyMatch` helpers matching the graph's static
algorithm. Keep matching limited to embedded page metadata.

- [x] **Step 4: Add active-result keyboard behavior in `search.py`**

Maintain `activeIndex` over visible results. ArrowDown and ArrowUp move active
state, Escape clears active state, Enter opens the active result link with
`window.location.href`. Input changes reset active state.

- [x] **Step 5: Add clear button behavior in `search.py`**

Clear query, clear active state, render all results, and focus the search input.

- [x] **Step 6: Run focused tests**

Run the command from Task 1 Step 4.

Expected: PASS.

## Task 3: Style And Documentation

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] **Step 1: Add CSS for graph legend/help and search active state**

Use existing tokens only. Add selectors for `.raya-graph-legend`,
`.raya-graph-legend-item`, `.raya-graph-legend-swatch`, `.raya-graph-help`,
`.raya-search-controls button`, and search result active states.

- [x] **Step 2: Update docs**

Document that static search supports local approximate matching and keyboard
navigation over metadata, and that the static graph includes a legend/help panel
for source relationships only.

- [x] **Step 3: Run focused tests and CSS contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/contracts/test_static_builder.py::test_rich_css_defines_learning_shell_regions tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_course_search_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
```

Expected: PASS.

## Task 4: Review, Verify, Commit, Push, Preview

**Files:**
- All changed source, tests, and docs.

- [x] **Step 1: Request independent code review**

Ask an independent reviewer to check for static contract violations, keyboard
accessibility gaps, and drift from current renderer patterns.

- [x] **Step 2: Run verification gates**

Run:

```bash
git diff --check
UV_PROJECT_ENVIRONMENT=.venv-local uv run python -m py_compile packages/static/src/raya_static/builder.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/contracts/test_static_builder.py::test_rich_css_defines_learning_shell_regions tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_course_search_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface -q
./scripts/check-render-debug.sh
./scripts/check.sh
```

Expected: all commands exit 0.

- [x] **Step 3: Commit and push**

Commit with:

```bash
git add docs/superpowers/specs/2026-06-19-navigation-workspace-polish-design.md docs/superpowers/plans/2026-06-19-navigation-workspace-polish.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/search.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/en/professors/index.md docs/guides/en/contributors/index.md docs/guides/en/agents/index.md docs/guides/es/estudiantes/index.md docs/guides/es/profesores/index.md docs/guides/es/colaboradores/index.md docs/guides/es/agentes/index.md
git commit -m "Polish navigation workspace"
git push origin new_rayalucaria
```

- [x] **Step 4: Start preview**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --port 0
```

Report the `entrypoint` URL.
