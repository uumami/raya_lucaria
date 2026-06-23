# Page Connection Previews Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add static, keyboard-reachable previews to explicit page connection items in the rail and article connection blocks.

**Architecture:** Extend the build-time page graph context with public linked-page metadata and explicit relationship counts. Render each connection item as native `<details>` markup with local page and graph links, then style it for compact rail usage and roomier article usage.

**Tech Stack:** Python static builder, generated HTML/CSS, pytest contract tests, Playwright e2e tests, Markdown documentation.

---

## File Structure

- Modify `packages/static/src/raya_static/builder.py` to enrich `_graph_context_by_page`, render connection previews, and share count/meta helpers.
- Modify `packages/static/src/raya_static/rendering.py` to style rail and article preview disclosures.
- Modify `packages/static/src/raya_static/shell.py` to keep native `summary` controls out of collapsed rail tab order when `inert` fallback handling is needed.
- Modify `tests/contracts/test_static_builder.py` to assert static preview structure and forbidden strings.
- Modify `tests/e2e/test_preview_static_read_path.py` to assert disclosure interaction, graph handoff, no overflow, and no requests.
- Modify `docs/foundation/20_learning_renderer_contract.md` and EN/ES student/agent guides to document the behavior.

## Task 1: Contract Test For Static Preview Data

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Write the failing test assertions**

In `test_render_fixture_uses_static_learning_shell`, after the existing rail `Connections` assertions, add assertions like:

```python
    assert 'class="raya-connection-preview raya-connection-preview-rail"' in connections_panel
    assert "<summary>Reader UX Fixture</summary>" in connections_panel
    assert "Reader UX fixture for course-shell navigation" in connections_panel
    assert '<span class="raya-connection-preview-status">ready</span>' in connections_panel
    assert '<span><strong>1</strong> from this page</span>' in connections_panel
    assert '<span><strong>2</strong> links here</span>' in connections_panel
    assert 'class="raya-connection-preview-open" href="../reader-ux/index.html"' in connections_panel
    assert 'class="raya-connection-preview-graph" href="../_raya/graph/index.html?page=reader-ux"' in connections_panel
```

In the existing `article_connections` assertions, add:

```python
    assert 'class="raya-connection-preview raya-connection-preview-article"' in article_connections
    assert "<summary>Math Authoring Fixture</summary>" in article_connections
    assert "Fixture page for current build-time MathJax authoring patterns." in article_connections
    assert '<span class="raya-connection-preview-status">ready</span>' in article_connections
    assert '<span><strong>1</strong> from this page</span>' in article_connections
    assert '<span><strong>2</strong> links here</span>' in article_connections
    assert 'class="raya-connection-preview-open" href="../math-authoring/index.html"' in article_connections
    assert 'class="raya-connection-preview-graph" href="../_raya/graph/index.html?page=math-authoring"' in article_connections
```

- [x] **Step 2: Run the focused contract test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell -q
```

Expected: FAIL because `raya-connection-preview` markup is not rendered yet.

## Task 2: Browser Test For Disclosure Interaction

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Write failing e2e assertions**

In `test_render_fixture_article_page_connections_are_visible_and_static`, inside the existing viewport loop after the `state` assertions, add:

```python
                        preview = block.locator(
                            '.raya-connection-preview-article summary',
                            has_text="Math Authoring Fixture",
                        ).first
                        preview.click()
                        preview_state = block.evaluate(
                            """(block) => {
                              const details = Array
                                .from(block.querySelectorAll('.raya-connection-preview-article'))
                                .find((node) => node.querySelector('summary')?.innerText.includes('Math Authoring Fixture'));
                              return {
                                open: details?.open,
                                text: details?.innerText,
                                openHref: details?.querySelector('.raya-connection-preview-open')?.getAttribute('href'),
                                graphHref: details?.querySelector('.raya-connection-preview-graph')?.getAttribute('href'),
                              };
                            }"""
                        )
                        assert preview_state["open"] is True
                        assert "Fixture page for current build-time MathJax authoring patterns." in preview_state["text"]
                        assert "1 from this page" in preview_state["text"]
                        assert "2 links here" in preview_state["text"]
                        assert preview_state["openHref"] == "../math-authoring/index.html"
                        assert preview_state["graphHref"] == "../_raya/graph/index.html?page=math-authoring"
                        assert "recommend" not in preview_state["text"].lower()
                        assert "progress" not in preview_state["text"].lower()
                        assert "mastery" not in preview_state["text"].lower()
```

- [x] **Step 2: Run the focused browser test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_article_page_connections_are_visible_and_static -q
```

Expected: FAIL because `.raya-connection-preview-article` does not exist.

## Task 3: Enrich Graph Context And Render Previews

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [x] **Step 1: Add public page metadata to graph context**

Create helper functions near `_graph_context_by_page`:

```python
def _public_graph_page_context(
    page: ContentPage,
    *,
    outgoing_count: int,
    incoming_count: int,
) -> dict[str, str]:
    data = {
        "id": page.id,
        "title": page.nav_title or page.title,
        "url": page.output_path,
        "outgoing_count": str(outgoing_count),
        "incoming_count": str(incoming_count),
    }
    if page.summary:
        data["summary"] = page.summary
    if page.status:
        data["status"] = page.status
    return data
```

Then compute outgoing/incoming counts from explicit content edges and use this helper for each context item.

- [x] **Step 2: Replace simple connection list items with preview disclosures**

Change `_linked_page_item` and `_article_connection_item` to call a shared helper:

```python
def _connection_preview_item(page: ContentPage, item: dict[str, str], variant: str) -> str:
    title = item["title"]
    href = _relative_href(page.output_path, item["url"])
    graph_href = _href_with_query(
        _relative_href(page.output_path, STATIC_GRAPH_PATH.as_posix()),
        {"page": item["id"]},
    )
    return ...
```

The helper must render `details.raya-connection-preview`, a `summary`, optional summary/status, count chips, and two links: `Open page` and `Graph`.

- [x] **Step 3: Run focused contract test and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell -q
```

Expected: PASS.

## Task 4: Style Previews

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Add CSS for connection preview disclosures**

Add rules near existing connection CSS:

```css
.raya-connection-preview {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  min-width: 0;
}
.raya-connection-preview summary {
  cursor: pointer;
  font-weight: 800;
  overflow-wrap: anywhere;
  padding: 0.45rem 0.55rem;
}
```

Include styles for body, metadata chips, and action links. Keep text wrapping stable on mobile.

- [x] **Step 2: Run focused browser test and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_article_page_connections_are_visible_and_static -q
```

Expected: PASS.

## Task 5: Documentation

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] **Step 1: Document the static preview contract**

Update the foundation and role docs to say that connection previews use generated public metadata and explicit relationship counts, are native disclosures, and do not infer recommendations, progress, or rankings.

- [x] **Step 2: Run focused docs-adjacent tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell tests/e2e/test_preview_static_read_path.py::test_render_fixture_article_page_connections_are_visible_and_static -q
```

Expected: PASS.

## Task 6: Verification And Review

**Files:**
- Inspect all modified files.

- [x] **Step 1: Run focused renderer checks**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell tests/e2e/test_preview_static_read_path.py::test_render_fixture_article_page_connections_are_visible_and_static -q
./scripts/check-render-debug.sh
```

Expected: PASS.

- [x] **Step 2: Request code review**

Ask subagents to review:

- static contract compliance;
- browser/layout behavior;
- documentation and authority boundaries.

- [x] **Step 3: Run archive gates before commit**

Run sequentially:

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: PASS.

- [x] **Step 4: Commit and push**

Commit with:

```bash
git add packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py packages/static/src/raya_static/shell.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/es/estudiantes/index.md docs/guides/en/agents/index.md docs/guides/es/agentes/index.md docs/superpowers/specs/2026-06-23-page-connection-previews-design.md docs/superpowers/plans/2026-06-23-page-connection-previews.md
git commit -m "Add page connection previews"
git push origin new_rayalucaria
```
