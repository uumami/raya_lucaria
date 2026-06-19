# Hierarchical Course Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the flat static course map with a hierarchical, collapsible, filterable map derived from current content hierarchy.

**Architecture:** Build the hierarchy during static rendering from `ContentModel.children_by_parent` and page metadata. Add local shell JavaScript for map section toggles and filtering. Keep all behavior static, non-persistent, and independent from search/graph artifact pages.

**Tech Stack:** Python 3.10 static builder, local vanilla JavaScript embedded through `packages/static/src/raya_static/shell.py`, CSS in `packages/static/src/raya_static/rendering.py`, pytest and Playwright e2e tests.

---

### Task 1: Contract Tests For Hierarchical Course Map

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Write failing HTML contract assertions**

Add expectations to `test_static_builder_renders_collapsible_shell_controls_and_page_position`:

```python
assert 'class="raya-course-map-filter"' in html
assert 'id="raya-course-map-filter"' in html
assert 'data-raya-course-map-filter' in html
assert 'data-raya-map-node="minimal-root"' in html
assert 'data-raya-map-node="first-unit"' in html
assert 'data-raya-map-parent="minimal-root"' in html
assert 'data-raya-map-active="ancestor"' in middle_html
assert 'data-raya-map-children' in html
assert 'id="raya-map-children-2-first-unit" data-raya-map-children aria-hidden="false"' in html
assert 'data-raya-map-node-toggle' in html
```

- [x] **Step 2: Write failing shell-resource assertions**

Add expectations near shell CSS/JS contract coverage:

```python
assert "data-raya-course-map-filter" in script
assert "data-raya-map-node-toggle" in script
assert "raya-map-filter-empty" in css
```

- [x] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_builder_renders_collapsible_shell_controls_and_page_position -q
```

Expected: fails because the map has no filter, hierarchy nodes, or node toggles.

### Task 2: Browser Behavior Tests

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add failing Playwright test**

Create `test_render_fixture_course_map_hierarchy_filters_without_requests`:

```python
def test_render_fixture_course_map_hierarchy_filters_without_requests(tmp_path: Path) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        assert handle.base_url is not None
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                requested_urls: list[str] = []
                page.on("request", lambda request: requested_urls.append(request.url))
                try:
                    page.goto(f"{handle.base_url}/authoring-matrix/index.html", wait_until="networkidle")
                    requested_urls.clear()
                    assert page.locator("[data-raya-map-active='ancestor']").count() > 0
                    first_toggle = page.locator("[data-raya-map-node-toggle]").first
                    before = first_toggle.get_attribute("aria-expanded")
                    first_toggle.click()
                    after = first_toggle.get_attribute("aria-expanded")
                    assert before != after
                    page.fill("#raya-course-map-filter", "matrix")
                    assert page.locator("[data-raya-map-node]:visible").count() >= 1
                    assert "matrix" in page.locator("#raya-course-map-list").inner_text().lower()
                    assert page.locator("[data-raya-map-filter-empty]").is_hidden()
                    page.fill("#raya-course-map-filter", "zz-no-match")
                    assert page.locator("[data-raya-map-filter-empty]").is_visible()
                    page.fill("#raya-course-map-filter", "")
                    assert page.locator("[data-raya-map-filter-empty]").is_hidden()
                    assert requested_urls == []
                    _assert_no_horizontal_overflow(page)
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

Also add `test_minimal_course_map_nested_sections_are_expanded_and_collapsible`
so a true nested course structure verifies default expansion, nested collapse, compact
rail behavior, local filtering, and no interaction-time network requests.

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_course_map_hierarchy_filters_without_requests -q
```

Expected: fails because the filter and toggle elements do not exist.

### Task 3: Static Builder Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [x] **Step 1: Render recursive course-map nodes**

Replace `_render_course_map` flat link generation with recursive helpers that:

- start from `content_model.root_id`;
- render each page once;
- use `content_model.children_by_parent`;
- add `data-raya-map-node`, `data-raya-map-parent`, `data-raya-map-depth`, `data-raya-map-active`;
- add a button with `data-raya-map-node-toggle` and `aria-controls` when a page has children;
- add nested `<ol data-raya-map-children>` groups expanded by default.

- [x] **Step 2: Add filter markup**

Render:

```html
<label class="raya-course-map-filter-label" for="raya-course-map-filter">Filter map</label>
<input id="raya-course-map-filter" class="raya-course-map-filter" type="search" autocomplete="off" data-raya-course-map-filter>
<p class="raya-map-filter-empty" data-raya-map-filter-empty hidden>No map matches.</p>
```

- [x] **Step 3: Verify contract GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_builder_renders_collapsible_shell_controls_and_page_position -q
```

Expected: passes after shell/CSS tasks are complete.

### Task 4: Shell JavaScript And CSS

**Files:**
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Add local toggle/filter behavior**

In shell JS, initialize node toggles and filter input. Toggling updates `aria-expanded`, the node state, and child group hidden state. Filtering normalizes query text, hides nonmatching leaf branches, reveals ancestors of matches, and shows the empty message when no node matches.

- [x] **Step 2: Add CSS for tree map**

Style nested list spacing, toggle buttons, active ancestors, filter input, hidden nodes, and empty state. Keep compact collapsed map compatible with current numeric rail.

- [x] **Step 3: Verify behavior GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_course_map_hierarchy_filters_without_requests -q
```

Expected: passes.

### Task 5: Documentation And Verification

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] **Step 1: Document static hierarchy behavior**

Update docs to say the course map is a generated static hierarchy, filterable locally, and not personal progress.

- [x] **Step 2: Run focused verification**

Run:

```bash
git diff --check
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_builder_renders_collapsible_shell_controls_and_page_position tests/e2e/test_preview_static_read_path.py::test_render_fixture_course_map_hierarchy_filters_without_requests tests/e2e/test_preview_static_read_path.py::test_minimal_course_map_nested_sections_are_expanded_and_collapsible -q
./scripts/check-render-debug.sh
```

- [x] **Step 3: Request code review**

Use `superpowers:requesting-code-review` with the uncommitted diff. Fix Critical and Important findings before commit.

- [x] **Step 4: Final gate, commit, push, preview**

Run:

```bash
./scripts/check.sh
git add docs/superpowers/specs/2026-06-19-hierarchical-course-map-design.md docs/superpowers/plans/2026-06-19-hierarchical-course-map.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/shell.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/en/professors/index.md docs/guides/en/contributors/index.md docs/guides/en/agents/index.md docs/guides/es/estudiantes/index.md docs/guides/es/profesores/index.md docs/guides/es/colaboradores/index.md docs/guides/es/agentes/index.md
git commit -m "Add hierarchical course map"
git push origin new_rayalucaria
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --port 0
```
