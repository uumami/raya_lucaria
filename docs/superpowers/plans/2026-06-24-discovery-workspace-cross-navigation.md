# Discovery Workspace Cross-Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make generated Search, Graph, Practice, and Tasks workspaces cross-link through one local static discovery command bar.

**Architecture:** Extend the existing `_render_discovery_command_bar()` helper with one optional `tasks_href` argument and wire each generated workspace with local relative links to the other workspaces. Keep generated workspace comfort controls volatile so discovery pages do not rely on browser storage.

**Tech Stack:** Python static builder, pytest contract tests, local generated HTML.

---

### Task 1: Contract Coverage

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Write failing tests**

Add assertions to the existing graph, search, and practice workspace tests:

```python
assert 'href="../tasks/index.html"' in graph_html
assert '<span class="raya-command-label">Tasks</span>' in graph_html
assert 'src="../render/accessibility/open-dyslexic-toggle-volatile.js"' in graph_html
assert 'src="../render/accessibility/open-dyslexic-toggle.js"' not in graph_html
```

Repeat equivalent checks for `search_html` and `practice_html`.

- [x] **Step 2: Verify red**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_visual_graph_surface tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace -q
```

Expected: three failures on missing `href="../tasks/index.html"`.

### Task 2: Builder Wiring

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add `tasks_href` to `_render_discovery_command_bar()`**

Add an optional `tasks_href: str | None` parameter and render the Tasks command when it is present.

- [ ] **Step 2: Wire workspace calls**

Pass `tasks_href="../tasks/index.html"` from Graph, Search, and Practice. Pass `tasks_href=None` from Tasks.

- [ ] **Step 3: Use volatile accessibility script on all discovery workspaces**

Make Graph, Search, and Practice use `open-dyslexic-toggle-volatile.js`, matching Tasks.

- [ ] **Step 4: Verify green**

Run the focused contract command from Task 1 again. Expected: three passing tests.

### Task 3: Final Verification

**Files:**
- No additional production files expected.

- [ ] **Step 1: Run focused render debug**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: all render-debug checks pass.

- [ ] **Step 2: Request independent review**

Ask a subagent to review the builder/test/docs diff for discovery workspace consistency and static constraints.
