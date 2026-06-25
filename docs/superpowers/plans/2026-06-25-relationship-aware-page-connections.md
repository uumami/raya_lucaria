# Relationship-Aware Page Connections Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show explicit relationship kind and direction in article Page connections and rail Connections previews.

**Architecture:** Reuse the existing `kind` field already present on `page_graph_context` items. Thread a direction label into the existing preview helper, render a compact badge and structural direction sentence, style the badge with current skin tokens, and update focused tests plus role/foundation docs.

**Tech Stack:** Python static builder, generated HTML/CSS, pytest contract tests, Playwright static-read-path tests, Markdown docs.

---

### Task 1: Contract Tests For Relationship Labels

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write failing assertions**

In `test_render_fixture_uses_static_learning_shell`, extend the existing `connections_panel` and `article_connections` assertions with:

```python
    assert '<span class="raya-connection-preview-kind">Content</span>' in connections_panel
    assert (
        '<span class="raya-connection-preview-direction">Links here</span>'
        in connections_panel
    )
    assert (
        "This target page links here through an explicit content link."
        in connections_panel
    )
    assert '<span class="raya-connection-preview-kind">Content</span>' in article_connections
    assert (
        '<span class="raya-connection-preview-direction">From this page</span>'
        in article_connections
    )
    assert (
        "This page links to the target page through an explicit content link."
        in article_connections
    )
```

- [ ] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell -q
```

Expected: FAIL because relationship badge and explanation markup are absent.

### Task 2: Browser Test For Native Preview Orientation

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write failing assertions**

In the existing article Page connections browser assertions, extend the preview state assertions with:

```python
                        assert "Content" in preview_state["normalizedText"]
                        assert "From this page" in preview_state["normalizedText"]
                        assert (
                            "This page links to the target page through an explicit content link."
                            in preview_state["normalizedText"]
                        )
```

- [ ] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_article_page_connections_are_visible_and_static -q
```

Expected: FAIL because the preview text does not include relationship kind and direction yet.

### Task 3: Builder Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Thread direction through preview calls**

Change `_article_connection_section` so it passes the section title as preview direction:

```python
def _article_connection_section(
    title: str,
    items: list[dict[str, str]],
    page: ContentPage,
) -> str:
    rendered_items = "\n".join(
        _article_connection_item(page, item, title) for item in items
    )
```

Change `_article_connection_item` to accept `direction` and pass it to `_connection_preview_item`:

```python
def _article_connection_item(
    page: ContentPage,
    item: dict[str, str],
    direction: str,
) -> str:
    preview = _connection_preview_item(page, item, "article", direction)
    return f'<li class="raya-article-connection-item">{preview}</li>'
```

Change `_linked_page_item` to accept `direction`, and update the rail calls:

```python
def _linked_page_item(page: ContentPage, item: dict[str, str], direction: str) -> str:
    return "<li>" + _connection_preview_item(page, item, "rail", direction) + "</li>"
```

In `_render_linked_pages_rail`, render outgoing and incoming lists with:

```python
"\n".join(_linked_page_item(page, item, "From this page") for item in outgoing)
"\n".join(_linked_page_item(page, item, "Links here") for item in incoming)
```

- [ ] **Step 2: Render badge and explanation**

Change `_connection_preview_item` to accept `direction`, build the summary from a metadata badge plus title, and render the direction sentence before counts:

```python
def _connection_preview_item(
    page: ContentPage,
    item: dict[str, str],
    variant: str,
    direction: str,
) -> str:
    title = item["title"]
    href = _relative_href(page.output_path, item["url"])
    graph_href = _href_with_query(
        _relative_href(page.output_path, STATIC_GRAPH_PATH.as_posix()),
        {"page": item["id"]},
    )
    kind_label = _connection_kind_label(item.get("kind", "content"))
    metadata = _connection_preview_metadata(item, direction)
    return "\n".join(
        [
            (
                '<details class="raya-connection-preview '
                f'raya-connection-preview-{html.escape(variant, quote=True)}">'
            ),
            (
                "<summary>"
                '<span class="raya-connection-preview-meta">'
                f'<span class="raya-connection-preview-kind">{html.escape(kind_label)}</span>'
                f'<span class="raya-connection-preview-direction">{html.escape(direction)}</span>'
                "</span>"
                f'<span class="raya-connection-preview-title">{html.escape(title)}</span>'
                "</summary>"
            ),
            '<div class="raya-connection-preview-body">',
            metadata,
            '<p class="raya-connection-preview-actions">',
            (
                f'<a class="raya-connection-preview-open" href="{html.escape(href)}">'
                "Open page</a>"
            ),
            (
                f'<a class="raya-connection-preview-graph" href="{html.escape(graph_href)}" '
                f'aria-label="View {html.escape(title, quote=True)} in course graph">'
                "Graph</a>"
            ),
            "</p>",
            "</div>",
            "</details>",
        ]
    )
```

Add helper functions near `_relationship_count_label`:

```python
def _connection_kind_label(kind: str) -> str:
    labels = {
        "content": "Content",
        "prerequisite": "Prerequisite",
        "navigation": "Navigation",
        "parent": "Parent",
    }
    return labels.get(kind, kind.replace("-", " ").replace("_", " ").title())


def _connection_direction_sentence(direction: str, kind: str) -> str:
    kind_label = _connection_kind_label(kind).lower()
    if direction == "Links here":
        return f"This target page links here through an explicit {kind_label} link."
    return f"This page links to the target page through an explicit {kind_label} link."
```

Change `_connection_preview_metadata` signature and add the direction sentence:

```python
def _connection_preview_metadata(item: dict[str, str], direction: str) -> str:
    parts: list[str] = []
    kind = item.get("kind", "content")
    parts.append(
        '<p class="raya-connection-preview-direction-note">'
        f"{html.escape(_connection_direction_sentence(direction, kind))}</p>"
    )
```

- [ ] **Step 3: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell -q
```

Expected: PASS.

### Task 4: CSS Polish

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Style metadata badges**

Extend the existing connection preview CSS with:

```css
.raya-connection-preview summary {
  display: grid;
  gap: 0.35rem;
}
.raya-connection-preview-meta {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}
.raya-connection-preview-kind,
.raya-connection-preview-direction {
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 42%, var(--raya-color-border));
  border-radius: 999px;
  display: inline-flex;
  font-size: 0.7rem;
  font-weight: 900;
  line-height: 1;
  padding: 0.24rem 0.42rem;
}
.raya-connection-preview-kind {
  background: var(--raya-color-accent);
  color: var(--raya-color-accent-text);
}
.raya-connection-preview-direction {
  background: color-mix(in srgb, var(--raya-color-accent-soft) 76%, var(--raya-color-surface));
  color: var(--raya-color-text);
}
.raya-connection-preview-title {
  display: block;
}
.raya-connection-preview-direction-note {
  color: var(--raya-color-muted);
  font-size: 0.84rem;
}
```

- [ ] **Step 2: Run focused browser test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_article_page_connections_are_visible_and_static -q
```

Expected: PASS.

### Task 5: Documentation

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

- [ ] **Step 1: Update the contract**

Add that article and rail connection previews may show explicit relationship kind and direction from generated graph context, and remain static structural orientation.

- [ ] **Step 2: Update role docs**

Add one sentence to each role family:

```markdown
Connection previews may label relationship kind and direction, such as `Content` and `From this page`, using explicit generated graph context only.
```

Use natural Spanish equivalents in the Spanish role docs while keeping UI labels in English when they are literal generated text.

- [ ] **Step 3: Run docs/contract search**

Run:

```bash
rg -n "relationship kind and direction|tipo y direccion|Content` and `From this page" docs/foundation/20_learning_renderer_contract.md docs/guides/en docs/guides/es
```

Expected: matches in the foundation and all updated role docs.

### Task 6: Final Verification And Commit

**Files:**
- All files changed above.

- [ ] **Step 1: Run focused contract/browser tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell tests/e2e/test_preview_static_read_path.py::test_render_fixture_article_page_connections_are_visible_and_static -q
```

Expected: PASS.

- [ ] **Step 2: Run render debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS.

- [ ] **Step 3: Commit implementation**

Run:

```bash
git add packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/en/professors/index.md docs/guides/en/contributors/index.md docs/guides/en/agents/index.md docs/guides/es/estudiantes/index.md docs/guides/es/profesores/index.md docs/guides/es/colaboradores/index.md docs/guides/es/agentes/index.md docs/superpowers/plans/2026-06-25-relationship-aware-page-connections.md
git commit -m "Add relationship-aware page connections"
```

Expected: commit succeeds.

## Self-Review

- Every requirement in the design has a corresponding task.
- The plan keeps tests before builder/CSS changes.
- No schema, runtime fetch, external resource, learner-state, or browser-side math changes are included.
