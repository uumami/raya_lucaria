# Discovery Workspace Chrome Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `_raya/search/` and `_raya/graph/` feel like first-class static course workspaces with shared course chrome and comfort controls.

**Architecture:** Add a small builder helper for discovery command chrome and reuse it in the generated Search and Graph surfaces. Style the helper with existing command-bar tokens and keep each page on its own local JavaScript, embedded JSON payload, and local accessibility resources.

**Tech Stack:** Python static builder, static CSS in `packages/static/src/raya_static/rendering.py`, local accessibility resources, pytest contract tests, Playwright static-read-path tests.

---

### Task 1: Contract Tests For Discovery Chrome

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add graph chrome assertions**

In `test_build_writes_local_visual_graph_surface`, assert the generated graph HTML contains:

```python
assert 'class="raya-discovery-command-bar"' in graph_html
assert "Graph workspace" in graph_html
assert 'href="../search/index.html"' in graph_html
assert '<span class="raya-command-label">Search</span>' in graph_html
assert '<button class="raya-command raya-command-size raya-text-size-toggle"' in graph_html
assert '<button class="raya-command raya-command-font raya-font-toggle"' in graph_html
assert "shell.js" not in graph_html
assert "localStorage" not in graph_html
```

- [ ] **Step 2: Add search chrome assertions**

In `test_build_writes_local_course_search_surface`, assert the generated search HTML contains:

```python
assert 'class="raya-discovery-command-bar"' in search_html
assert "Search workspace" in search_html
assert 'href="../graph/index.html"' in search_html
assert '<span class="raya-command-label">Graph</span>' in search_html
assert '<button class="raya-command raya-command-size raya-text-size-toggle"' in search_html
assert '<button class="raya-command raya-command-font raya-font-toggle"' in search_html
assert "shell.js" not in search_html
assert "localStorage" not in search_html
```

- [ ] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface -q
```

Expected: FAIL because discovery chrome does not exist yet.

### Task 2: Browser Tests For Cross-Workspace Chrome

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Extend graph browser test**

In `test_preview_serves_local_visual_graph_surface`, assert:

```python
assert page.locator(".raya-discovery-command-bar").is_visible()
assert page.locator(".raya-command-search").get_attribute("href").endswith("/_raya/search/index.html")
assert page.locator(".raya-command-size").is_visible()
assert page.locator(".raya-command-font").is_visible()
```

- [ ] **Step 2: Extend search browser test**

In `test_preview_serves_local_course_search_surface`, assert:

```python
assert page.locator(".raya-discovery-command-bar").is_visible()
assert page.locator(".raya-command-graph").get_attribute("href").endswith("/_raya/graph/index.html")
assert page.locator(".raya-command-size").is_visible()
assert page.locator(".raya-command-font").is_visible()
```

- [ ] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_course_search_surface -q
```

Expected: FAIL because the shared chrome is absent.

### Task 3: Builder Implementation

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add helper**

Add `_render_discovery_command_bar(...)` near `_render_top_command_bar`:

```python
def _render_discovery_command_bar(
    *,
    course_title: str,
    workspace_label: str,
    home_href: str,
    search_href: str | None,
    graph_href: str | None,
) -> str:
    commands = [
        (
            f'<a class="raya-command raya-command-home" href="{html.escape(home_href)}" '
            'aria-label="Back to course">'
            '<span class="raya-command-label">Course</span>'
            "</a>"
        )
    ]
    if search_href is not None:
        commands.append(
            f'<a class="raya-command raya-command-search" href="{html.escape(search_href)}" '
            'aria-label="Open course search">'
            '<span class="raya-command-label">Search</span>'
            "</a>"
        )
    if graph_href is not None:
        commands.append(
            f'<a class="raya-command raya-command-graph" href="{html.escape(graph_href)}" '
            'aria-label="Open course graph">'
            '<span class="raya-command-label">Graph</span>'
            "</a>"
        )
    commands.extend(
        [
            (
                '<button class="raya-command raya-command-size raya-text-size-toggle" type="button" '
                'aria-label="Text size: normal" aria-pressed="false">'
                '<span class="raya-command-label">Text size</span>'
                "</button>"
            ),
            (
                '<button class="raya-command raya-command-font raya-font-toggle" type="button" '
                'aria-label="Toggle OpenDyslexic font" aria-pressed="false">'
                '<span class="raya-command-label">OpenDyslexic</span>'
                "</button>"
            ),
        ]
    )
    return "\n".join(
        [
            '<header class="raya-top-command-bar raya-discovery-command-bar" aria-label="Course discovery tools">',
            '<div class="raya-top-command-bar-inner">',
            '<div class="raya-reading-context">',
            f'<span class="raya-reading-context-course">{html.escape(course_title)}</span>',
            '<span class="raya-reading-context-separator" aria-hidden="true">/</span>',
            f'<span class="raya-reading-context-page">{html.escape(workspace_label)}</span>',
            "</div>",
            '<div class="raya-course-tools">',
            "\n".join(commands),
            "</div>",
            "</div>",
            "</header>",
        ]
    )
```

- [ ] **Step 2: Use helper on Graph**

In `_render_graph_surface`, insert the helper immediately after the skip link:

```python
_render_discovery_command_bar(
    course_title=course_title,
    workspace_label="Graph workspace",
    home_href="../../index.html",
    search_href="../search/index.html",
    graph_href=None,
),
```

- [ ] **Step 3: Use helper on Search**

In `_render_search_surface`, insert the helper immediately after the skip link:

```python
_render_discovery_command_bar(
    course_title=course_title,
    workspace_label="Search workspace",
    home_href="../../index.html",
    search_href=None,
    graph_href="../graph/index.html",
),
```

- [ ] **Step 4: Keep existing page-local back link**

Do not remove existing `Back to course` links in the page headers during this slice. They remain useful inside the page body and avoid changing navigation tests.

### Task 4: CSS Implementation

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Add discovery selectors**

Add CSS:

```css
.raya-discovery-command-bar {
  box-shadow: 0 0.75rem 2rem color-mix(in srgb, var(--raya-color-text) 18%, transparent);
}
.raya-command-home::before {
  content: "C";
}
```

- [ ] **Step 2: Verify focused GREEN**

Run:

```bash
git diff --check && UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_visual_graph_surface tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_course_search_surface -q
```

Expected: PASS.

### Task 5: Documentation And Review

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Document discovery chrome**

Document that Search and Graph may share static course discovery chrome and local comfort controls, but do not store search or graph state.

- [ ] **Step 2: Request independent review**

Dispatch a read-only reviewer focused on static boundaries, no `shell.js` dependency, no storage state, local links, and no recommendation/progress wording.

### Task 6: Full Verification, Commit, Push

**Files:**
- All files changed in this plan.

- [ ] **Step 1: Run focused visual/debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS.

- [ ] **Step 2: Run full gates**

Run sequentially:

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: both PASS.

- [ ] **Step 3: Commit and push**

```bash
git add docs/superpowers/specs/2026-06-23-discovery-workspace-chrome-design.md docs/superpowers/plans/2026-06-23-discovery-workspace-chrome.md docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/en/agents/index.md docs/guides/es/estudiantes/index.md docs/guides/es/agentes/index.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add discovery workspace chrome"
git push origin new_rayalucaria
```
