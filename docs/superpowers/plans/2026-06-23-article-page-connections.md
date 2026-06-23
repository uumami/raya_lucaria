# Article Page Connections Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render explicit incoming/outgoing page connections inside the main article so graph context is visible at the end of a lesson.

**Architecture:** Reuse `page_graph_context` already generated from explicit content links. Add one builder helper for article-level HTML, one CSS section in the renderer stylesheet, focused contract/browser tests, and EN/ES docs. Do not change artifact schema, graph data shape, or runtime state.

**Tech Stack:** Python static builder, generated HTML/CSS, pytest contract tests, Playwright static-read-path tests, Markdown docs.

---

### Task 1: Contract Test For Article Connections

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Write failing assertions**

In `test_render_fixture_uses_static_learning_shell`, after reading `html`, add assertions for the generated root page:

```python
    assert 'class="raya-article-connections"' in html
    assert "<h2>Page connections</h2>" in html
    assert "From this page" in html
    assert "Links here" in html
    assert 'href="_raya/graph/index.html?page=render-root"' in html
    assert 'class="raya-article-connection-context"' in html
    article_connections = _element_html(
        html,
        '<section class="raya-article-connections"',
        "</section>",
    )
    assert "recommended" not in article_connections.lower()
    assert "progress" not in article_connections.lower()
    assert "mastery" not in article_connections.lower()
    assert "_official" not in article_connections
    assert "_drafts" not in article_connections
    assert "course/0_index.md" not in article_connections
```

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell -q
```

Expected: FAIL because `raya-article-connections` is not rendered yet.

### Task 2: Browser Test For Visibility And Local Links

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Write failing browser assertions**

Add a focused e2e test near the learning-shell tests:

```python
def test_render_fixture_article_page_connections_are_visible_and_static(
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
                for viewport in ({"width": 1280, "height": 900}, {"width": 390, "height": 844}):
                    page = browser.new_page(viewport=viewport)
                    requested_urls: list[str] = []
                    page.on("request", lambda request: requested_urls.append(request.url))
                    try:
                        page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                        requested_urls.clear()
                        _assert_no_horizontal_overflow(page)
                        block = page.locator(".raya-article-connections")
                        assert block.count() == 1
                        assert block.locator("text=Page connections").is_visible()
                        assert block.locator("text=From this page").is_visible()
                        assert block.locator("text=Links here").is_visible()
                        graph_href = block.locator(".raya-article-connections-graph").get_attribute("href")
                        assert graph_href == "_raya/graph/index.html?page=render-root"
                        text = block.inner_text().lower()
                        assert "recommended" not in text
                        assert "progress" not in text
                        assert "mastery" not in text
                        assert all(
                            url.startswith(handle.base_url)
                            for url in requested_urls
                        )
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_article_page_connections_are_visible_and_static -q
```

Expected: FAIL because the article block is absent.

### Task 3: Builder Implementation

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [x] **Step 1: Add article connections helper**

Add a helper near `_render_linked_pages_rail`:

```python
def _render_article_connections(
    page: ContentPage,
    page_graph_context: dict[str, list[dict[str, str]]],
    graph_href: str,
) -> str:
    outgoing = page_graph_context.get("outgoing", [])
    incoming = page_graph_context.get("incoming", [])
    if not outgoing and not incoming:
        return ""
    sections = []
    if outgoing:
        sections.append(
            _render_article_connection_group(page, "From this page", outgoing)
        )
    if incoming:
        sections.append(
            _render_article_connection_group(page, "Links here", incoming)
        )
    return "\n".join(
        [
            '<section class="raya-article-connections" aria-labelledby="raya-article-connections-title">',
            '<div class="raya-article-connections-header">',
            '<div>',
            '<p class="raya-article-connections-kicker">Course graph</p>',
            '<h2 id="raya-article-connections-title">Page connections</h2>',
            "</div>",
            (
                f'<a class="raya-article-connections-graph" href="{html.escape(graph_href)}">'
                "Open in course graph</a>"
            ),
            "</div>",
            '<p class="raya-article-connections-summary">',
            f"<span><strong>{len(outgoing)}</strong> {_relationship_count_label(len(outgoing), 'from this page', 'from this page')}</span>",
            f"<span><strong>{len(incoming)}</strong> {_relationship_count_label(len(incoming), 'links here', 'link here')}</span>",
            "</p>",
            '<div class="raya-article-connections-grid">',
            "\n".join(sections),
            "</div>",
            "</section>",
        ]
    )
```

Add:

```python
def _render_article_connection_group(
    page: ContentPage,
    title: str,
    items: list[dict[str, str]],
) -> str:
    return "\n".join(
        [
            '<section class="raya-article-connection-group">',
            f"<h3>{html.escape(title)}</h3>",
            '<ul class="raya-article-connection-list">',
            "\n".join(_article_connection_item(page, item) for item in items),
            "</ul>",
            "</section>",
        ]
    )
```

Add:

```python
def _article_connection_item(page: ContentPage, item: dict[str, str]) -> str:
    href = _relative_href(page.output_path, item["url"])
    graph_href = _href_with_query(
        _relative_href(page.output_path, STATIC_GRAPH_PATH.as_posix()),
        {"page": item["id"]},
    )
    title = html.escape(item["title"])
    return (
        '<li><span class="raya-article-connection-row">'
        f'<a href="{html.escape(href)}">{title}</a>'
        f'<a class="raya-article-connection-context" href="{html.escape(graph_href)}" '
        f'aria-label="View {html.escape(item["title"], quote=True)} in course graph">'
        "Graph</a>"
        "</span></li>"
    )
```

- [x] **Step 2: Insert article block**

In `_render_page_html`, after `article_html, toc_html = _extract_page_toc(article_html)`, add:

```python
    article_connections = _render_article_connections(
        page,
        page_graph_context,
        graph_href,
    )
```

Then insert `article_connections` after `article_html` inside the article element.

- [x] **Step 3: Verify GREEN for contract**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell -q
```

Expected: PASS.

### Task 4: Article Connections Styling

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Add CSS**

Add CSS near the main article/rail styles:

```css
.raya-article-connections {
  border-top: 1px solid var(--raya-color-border);
  margin-top: 2rem;
  padding-top: 1.25rem;
}
.raya-article-connections-header {
  align-items: start;
  display: flex;
  gap: 1rem;
  justify-content: space-between;
}
.raya-article-connections-kicker {
  color: var(--raya-color-muted);
  font-size: 0.8125rem;
  font-weight: 700;
  margin: 0 0 0.25rem;
  text-transform: uppercase;
}
.raya-article-connections h2 {
  margin: 0;
}
.raya-article-connections-graph,
.raya-article-connection-context {
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  font-size: 0.8125rem;
  font-weight: 700;
  padding: 0.35rem 0.55rem;
  text-decoration: none;
  white-space: nowrap;
}
.raya-article-connections-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}
.raya-article-connections-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
}
.raya-article-connection-group {
  min-width: 0;
}
.raya-article-connection-group h3 {
  font-size: 1rem;
  margin-bottom: 0.5rem;
}
.raya-article-connection-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.raya-article-connection-list li + li {
  margin-top: 0.45rem;
}
.raya-article-connection-row {
  align-items: center;
  display: flex;
  gap: 0.5rem;
  justify-content: space-between;
}
.raya-article-connection-row > a:first-child {
  min-width: 0;
  overflow-wrap: anywhere;
}
```

- [x] **Step 2: Verify browser test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_article_page_connections_are_visible_and_static -q
```

Expected: PASS.

### Task 5: Documentation

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] **Step 1: Update docs**

Document that the main article may show a `Page connections` block built from explicit incoming/outgoing graph context. State that it is static course structure, not recommendations, progress, ranking, mastery, or completion.

- [x] **Step 2: Verify docs**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate docs >/tmp/raya-validate-docs.log && tail -30 /tmp/raya-validate-docs.log
```

Expected: PASS with only accepted INFO diagnostics.

### Task 6: Review And Verification

**Files:**
- All files changed above.

- [x] **Step 1: Request read-only review**

Dispatch a read-only reviewer focused on static graph context, no inferred recommendations/progress, link safety, mobile/desktop visibility, and no storage/runtime requests.

- [x] **Step 2: Focused verification**

Run:

```bash
git diff --check && UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell tests/e2e/test_preview_static_read_path.py::test_render_fixture_article_page_connections_are_visible_and_static -q
```

Expected: PASS.

- [x] **Step 3: Full gates**

Run sequentially:

```bash
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: all pass.

- [ ] **Step 4: Commit and push**

```bash
git add docs/superpowers/specs/2026-06-23-article-page-connections-design.md docs/superpowers/plans/2026-06-23-article-page-connections.md docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/en/agents/index.md docs/guides/es/estudiantes/index.md docs/guides/es/agentes/index.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add article page connections"
git push origin new_rayalucaria
```
