# Connections Rail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the low-signal linked-pages rail affordance with a clearer static Connections panel.

**Architecture:** Keep the existing graph-context data flow and rail collapse shell. Change only the rendered linked-pages panel body/title and CSS presentation, then update contract and browser checks around the existing render fixture.

**Tech Stack:** Python static builder, static CSS in `rich.css`, pytest contract tests, Playwright e2e tests.

---

### Task 1: Contract Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Write failing rendered-HTML assertions**

In `test_render_fixture_uses_static_learning_shell`, after the prerequisite panel assertions, add checks that the authoring matrix page renders the linked graph context as a `Connections` rail panel:

```python
last_html = (
    course / "artifact" / "site" / "authoring-matrix" / "index.html"
).read_text(encoding="utf-8")
connections_panel = _section_html(last_html, "raya-page-linked-pages")
assert 'aria-expanded="false">Connections</button>' in connections_panel
assert '<p class="raya-rail-connection-summary">' in connections_panel
assert '<strong>3</strong> from this page' in connections_panel
assert '<strong>1</strong> link here' in connections_panel
assert '<span class="raya-rail-count">3</span>' in connections_panel
assert '<span class="raya-rail-count">1</span>' in connections_panel
assert "From this page" in connections_panel
assert "Links here" in connections_panel
assert 'href="../math-authoring/index.html"' in connections_panel
assert 'href="../_raya/graph/index.html?page=reader-ux"' in connections_panel
assert "recommend" not in connections_panel.lower()
assert "progress" not in connections_panel.lower()
```

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell -q
```

Expected: FAIL because the current rail title is `Linked pages` and no connection summary/count chips exist.

### Task 2: Builder And CSS

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Render connection summary**

Update `_render_linked_pages_rail()` so it computes `outgoing_count` and
`incoming_count`, prepends a summary paragraph, renders section headings with
count chips, and passes title `Connections` to `_render_rail_panel()`.

- [x] **Step 2: Add static CSS hooks**

Add CSS for `.raya-rail-connection-summary`,
`.raya-rail-connection-heading`, and `.raya-rail-count`. Keep the presentation
compact, readable, and responsive without adding new JavaScript.

- [x] **Step 3: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell -q
```

Expected: PASS.

### Task 3: Browser Proof And Docs

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] **Step 1: Update browser assertions**

In `test_render_fixture_graph_context_panel_collapses_without_focus_leaks`,
keep the collapsed focus checks and add expanded checks for:

```python
assert "Connections" in expanded["text"]
assert "3 from this page" in expanded["text"]
assert "1 link here" in expanded["text"]
```

- [x] **Step 2: Update role docs and foundation**

Document Connections as an explicit static relationship panel, not a progress,
recommendation, or adaptive-study surface.

- [x] **Step 3: Focused verification**

Run:

```bash
git diff --check
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell tests/e2e/test_preview_static_read_path.py::test_render_fixture_graph_context_panel_collapses_without_focus_leaks -q
./scripts/check-render-debug.sh
```

Expected: all commands exit 0.

Evidence:
- Contract/browser focused check passed: `3 passed`.
- Renderer debug passed: `114 check(s)`.

### Task 4: Review And Gates

**Files:** no source edits expected.

- [x] **Step 1: Request independent code review**

Dispatch a read-only reviewer focused on static renderer boundaries, relative
links, accessibility, and no learner-state wording.

Outcome: one Important Spanish-guide wording issue and two minor plan/spec
grammar issues were fixed before archive gates.

- [x] **Step 2: Run gates**

Run:

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: both commands exit 0.

Evidence:
- Host archive gate passed: `451 passed`; `check: passed`.
- Docker reference gate passed: `451 passed`; `check-docker: passed`.
