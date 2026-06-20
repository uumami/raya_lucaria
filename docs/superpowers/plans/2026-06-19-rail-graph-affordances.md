# Rail Graph Affordances Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add compact graph-focus links to prerequisite and linked-page rail entries.

**Architecture:** Generate secondary graph links at build time beside existing rail page links. Reuse the existing static graph `?page=` bootstrap and existing shell inert behavior.

**Tech Stack:** Python static builder, static CSS in `rich.css`, pytest contract tests, Playwright preview tests.

---

### Task 1: Contract Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Write failing assertions**

In `test_render_fixture_uses_static_learning_shell`, assert that the reader prerequisite panel includes a graph-focus link:

```python
prereq_panel = _section_html(html, "raya-page-prerequisites")
assert 'class="raya-rail-context-link"' in prereq_panel
assert 'href="../_raya/graph/index.html?page=render-root"' in prereq_panel
assert 'aria-label="View Raya Lucaria Render Fixture in course graph"' in prereq_panel
```

In `test_render_fixture_authoring_page_shows_explicit_graph_context`, assert that linked pages include graph-focus links:

```python
assert 'href="../_raya/graph/index.html?page=numbered-objects"' in panel
assert 'href="../_raya/graph/index.html?page=reader-ux"' in panel
assert 'class="raya-rail-link-row"' in panel
assert 'class="raya-rail-context-link"' in panel
```

- [x] **Step 2: Run tests to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell tests/contracts/test_static_builder.py::test_render_fixture_authoring_page_shows_explicit_graph_context -q
```

Expected: FAIL because graph-focus rail links do not exist yet.

### Task 2: Builder And CSS

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Implement rail link rendering**

Add helper rendering so prerequisite and linked-page rail entries use:

```html
<li>
  <span class="raya-rail-link-row">
    <a href="...">Page title</a>
    <a class="raya-rail-context-link" href="../_raya/graph/index.html?page=target-id" aria-label="View Page title in course graph">Graph</a>
  </span>
</li>
```

The graph href must use `_href_with_query(_relative_href(page.output_path, STATIC_GRAPH_PATH.as_posix()), {"page": target_id})`.

- [x] **Step 2: Add compact styling**

Add CSS for `.raya-rail-link-row` and `.raya-rail-context-link` so the primary title and secondary chip wrap cleanly without horizontal overflow.

- [x] **Step 3: Run contract tests**

Run the Task 1 command again. Expected: PASS.

### Task 3: Browser Proof And Docs

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] **Step 1: Add browser test**

Extend the linked-pages rail e2e to expand the panel, click the graph link for `reader-ux`, and verify the graph opens with `Reader UX Fixture` selected.

- [x] **Step 2: Update docs**

Document that rail graph links are static orientation links into explicit graph context, not recommendations or learner state.

- [x] **Step 3: Run focused verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell tests/contracts/test_static_builder.py::test_render_fixture_authoring_page_shows_explicit_graph_context tests/contracts/test_static_builder.py::test_render_fixture_search_graph_course_map_visible_text_avoids_learner_state_language tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_context_panel_collapses_without_focus_leaks -q
git diff --check
```

Expected: tests pass and whitespace check is clean.

Debug note: the browser test exposed that the no-native-inert fallback left the `inert` attribute on expanded rail panel bodies. The shell now removes or sets the attribute explicitly while still assigning the `inert` property when available.

### Task 4: Full Verification

**Files:** no source edits expected.

- [ ] **Step 1: Request independent review**

Dispatch a read-only reviewer for the final diff. Fix Critical and Important findings.

- [ ] **Step 2: Run gates**

Run:

```bash
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: all commands exit 0.
