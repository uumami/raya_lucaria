# Reader Graph Context Rail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a compact `Linked pages` right-rail panel that shows explicit incoming and outgoing content links for the current page from generated graph data.

**Architecture:** Compute `links_index` and `graph_index` before page rendering, derive a per-page graph context in memory, and pass it into `_render_learning_rail`. The panel uses the existing rail component and only shows explicit `content` edges, not navigation, parent edges, recommendations, practice, progress, or mastery.

**Tech Stack:** Python static builder, existing graph/link index helpers, existing collapsible rail shell JS, pytest contract tests, Playwright preview e2e tests.

---

## File Map

- Modify `packages/static/src/raya_static/builder.py`
  - Move `_links_index(...)` and `_graph_index(...)` creation before page rendering.
  - Add `_graph_context_by_page(...)`.
  - Add `_render_linked_pages_rail(...)`.
  - Pass `page_graph_context` through `_render_page(...)` and `_render_learning_rail(...)`.
- Modify `tests/contracts/test_static_builder.py`
  - Add contract test for incoming/outgoing explicit graph context.
- Modify `tests/e2e/test_preview_static_read_path.py`
  - Add browser test for collapse/focus behavior.

---

## Task 1: Contract Test For Explicit Linked Pages Panel

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write the failing test**

Add this test near `test_render_fixture_reader_page_exercises_learning_rail_metadata`:

```python
def test_render_fixture_reader_page_shows_explicit_graph_context(
    tmp_path: Path,
) -> None:
    course = _copy_render_fixture(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    html = (course / "artifact" / "site" / "reader-ux" / "index.html").read_text(
        encoding="utf-8"
    )
    panel = _section_html(html, "raya-page-linked-pages")
    visible = _visible_text(panel).lower()

    assert '<section class="raya-rail-panel raya-page-linked-pages"' in panel
    assert 'aria-expanded="false">Linked pages</button>' in panel
    assert 'aria-hidden="true" inert' in panel
    assert "From this page" in panel
    assert "Links here" in panel
    assert 'href="../numbered-objects/index.html"' in panel
    assert 'href="../authoring-matrix/index.html"' in panel
    assert "navigation" not in visible
    assert "parent" not in visible
    assert "recommended" not in visible
    assert "practice" not in visible
    assert "progress" not in visible
    assert "mastery" not in visible
```

Why these pages:

- `reader-ux` links to `numbered-objects`, so it has outgoing `content`.
- `authoring-matrix` links to `reader-ux`, so `reader-ux` has incoming `content`.

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_reader_page_shows_explicit_graph_context -q
```

Expected: fail because `raya-page-linked-pages` is not rendered yet.

---

## Task 2: Compute Graph Context Before Page Rendering

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Move graph data creation earlier**

In `build_course`, after `references_by_page = _references_by_page(references)` and before `rendered_pages = []`, add:

```python
    links_index = _links_index(
        course_id,
        content_model,
        pages_by_reference,
        pages_by_source,
        root,
    )
    graph_index = _graph_index(course_id, content_model, links_index)
    graph_context_by_page = _graph_context_by_page(content_model, graph_index)
```

Then remove the later duplicate creation of `links_index` and `graph_index` near data index writing. Keep the existing `_write_json(data_dir / "links.json", links_index, report)` and `_write_json(data_dir / "graph.json", graph_index, report)` calls.

- [ ] **Step 2: Pass page graph context into page rendering**

Add `page_graph_context=graph_context_by_page.get(page.id, {})` to the `_render_page(...)` call in `build_course`.

Add the parameter to `_render_page(...)`:

```python
    page_graph_context: dict[str, list[dict[str, str]]],
```

Pass it to `_render_learning_rail(...)`:

```python
    learning_rail = _render_learning_rail(
        page,
        toc_html,
        content_model,
        support_panels,
        page_graph_context,
    )
```

Update `_render_learning_rail(...)` signature:

```python
def _render_learning_rail(
    page: ContentPage,
    toc_html: str,
    content_model: ContentModel,
    support_panels: str,
    page_graph_context: dict[str, list[dict[str, str]]],
) -> str:
```

Add `_render_linked_pages_rail(page, page_graph_context)` after `_render_prerequisites_rail(page, content_model)` in `panels`.

- [ ] **Step 3: Add graph context projection helper**

Add near `_graph_index(...)`:

```python
def _graph_context_by_page(
    content_model: ContentModel,
    graph_index: dict[str, Any],
) -> dict[str, dict[str, list[dict[str, str]]]]:
    pages_by_id = content_model.pages_by_id
    context: dict[str, dict[str, list[dict[str, str]]]] = {
        page.id: {"outgoing": [], "incoming": []} for page in content_model.pages
    }
    seen: set[tuple[str, str, str]] = set()
    for edge in graph_index["edges"]:
        if edge["kind"] != "content":
            continue
        source = pages_by_id.get(edge["from"])
        target = pages_by_id.get(edge["to"])
        if source is None or target is None or source.id == target.id:
            continue
        key = (source.id, target.id, edge["kind"])
        if key in seen:
            continue
        seen.add(key)
        context[source.id]["outgoing"].append(
            {
                "id": target.id,
                "title": target.nav_title or target.title,
                "url": target.output_path,
                "kind": edge["kind"],
            }
        )
        context[target.id]["incoming"].append(
            {
                "id": source.id,
                "title": source.nav_title or source.title,
                "url": source.output_path,
                "kind": edge["kind"],
            }
        )
    return context
```

- [ ] **Step 4: Run contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_reader_page_shows_explicit_graph_context -q
```

Expected: still fail because the panel renderer does not exist yet.

---

## Task 3: Render Linked Pages Rail Panel

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add panel renderer**

Add near `_render_prerequisites_rail(...)`:

```python
def _render_linked_pages_rail(
    page: ContentPage,
    page_graph_context: dict[str, list[dict[str, str]]],
) -> str:
    sections = []
    outgoing = page_graph_context.get("outgoing", [])
    incoming = page_graph_context.get("incoming", [])
    if outgoing:
        sections.append(
            "<h3>From this page</h3>"
            "<ul>"
            + "\n".join(
                _linked_page_item(page, item) for item in outgoing
            )
            + "</ul>"
        )
    if incoming:
        sections.append(
            "<h3>Links here</h3>"
            "<ul>"
            + "\n".join(
                _linked_page_item(page, item) for item in incoming
            )
            + "</ul>"
        )
    if not sections:
        return ""
    return _render_rail_panel(
        "raya-page-linked-pages",
        "Linked pages",
        "\n".join(sections),
    )
```

Add:

```python
def _linked_page_item(page: ContentPage, item: dict[str, str]) -> str:
    href = _relative_href(page.output_path, item["url"])
    return (
        f'<li><a href="{html.escape(href)}">'
        f'{html.escape(item["title"])}</a></li>'
    )
```

- [ ] **Step 2: Run contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_reader_page_shows_explicit_graph_context -q
```

Expected: pass after exact-string corrections.

---

## Task 4: Browser Collapse And Focus Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write browser test**

Add near `test_render_fixture_learning_rail_panels_collapse_without_focus_leaks`:

```python
def test_render_fixture_graph_context_panel_collapses_without_focus_leaks(
    tmp_path: Path,
) -> None:
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
                page = browser.new_page(viewport={"width": 1440, "height": 950})
                page.add_init_script("delete HTMLElement.prototype.inert;")
                try:
                    page.goto(f"{handle.base_url}/reader-ux/index.html", wait_until="networkidle")
                    _assert_no_horizontal_overflow(page)
                    panel = page.locator(".raya-page-linked-pages").first
                    collapsed = panel.evaluate(
                        """(panel) => {
                          const body = panel.querySelector('.raya-rail-panel-body');
                          const link = body?.querySelector('a');
                          link?.focus();
                          return {
                            state: panel.dataset.rayaRailPanelState,
                            expanded: panel.querySelector('[data-raya-rail-toggle]')
                              ?.getAttribute('aria-expanded'),
                            ariaHidden: body?.getAttribute('aria-hidden'),
                            inert: body?.inert,
                            bodyHeight: body?.getBoundingClientRect().height,
                            hasLink: !!link,
                            linkTabIndex: link?.getAttribute('tabindex'),
                          };
                        }"""
                    )
                    assert collapsed["state"] == "collapsed"
                    assert collapsed["expanded"] == "false"
                    assert collapsed["ariaHidden"] == "true"
                    assert collapsed["inert"] is True
                    assert collapsed["bodyHeight"] < 2
                    assert collapsed["hasLink"] is True
                    assert collapsed["linkTabIndex"] == "-1"

                    panel.locator("[data-raya-rail-toggle]").click()
                    page.wait_for_function(
                        """() => document
                          .querySelector('.raya-page-linked-pages')
                          ?.dataset.rayaRailPanelState === 'expanded'"""
                    )
                    expanded = panel.evaluate(
                        """(panel) => {
                          const body = panel.querySelector('.raya-rail-panel-body');
                          const link = body?.querySelector('a');
                          link?.focus();
                          return {
                            state: panel.dataset.rayaRailPanelState,
                            expanded: panel.querySelector('[data-raya-rail-toggle]')
                              ?.getAttribute('aria-expanded'),
                            ariaHidden: body?.getAttribute('aria-hidden'),
                            inert: body?.inert,
                            bodyHeight: body?.getBoundingClientRect().height,
                            linkTabIndex: link?.getAttribute('tabindex'),
                            linkFocused: document.activeElement === link,
                            text: panel.innerText,
                          };
                        }"""
                    )
                    assert expanded["state"] == "expanded"
                    assert expanded["expanded"] == "true"
                    assert expanded["ariaHidden"] == "false"
                    assert expanded["inert"] in {False, None}
                    assert expanded["linkTabIndex"] is None
                    assert expanded["linkFocused"] is True
                    assert "From this page" in expanded["text"]
                    assert "Links here" in expanded["text"]
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run browser test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_context_panel_collapses_without_focus_leaks -q
```

Expected: pass after implementation. If it fails, use `superpowers:systematic-debugging` before making changes.

---

## Task 5: Verification And Review

**Files:**
- No planned file edits.

- [ ] **Step 1: Run focused tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_reader_page_shows_explicit_graph_context tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_context_panel_collapses_without_focus_leaks -q
```

Expected: pass.

- [ ] **Step 2: Run broader checks**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py -q
./scripts/check-render-debug.sh
```

Expected: pass.

- [ ] **Step 3: Request code review**

Use `superpowers:requesting-code-review` with:

- Description: Reader graph context rail panel.
- Requirements: `docs/superpowers/specs/2026-06-19-reader-graph-context-rail-design.md` and this plan.
- Base SHA: commit before implementation.
- Head SHA: implementation candidate.

- [ ] **Step 4: Commit**

After addressing Critical/Important review findings:

```bash
git add packages/static/src/raya_static/builder.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add reader graph context rail"
```

---

## Self-Review

- Spec coverage: explicit incoming/outgoing content links, no inferred relationships, existing rail behavior, foundation wording, and test coverage are represented.
- Placeholder scan: no placeholders remain.
- Type consistency: `page_graph_context` is a dictionary with `outgoing` and `incoming` lists of dictionaries containing `id`, `title`, `url`, and `kind`.
