# Reading Context Bar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a compact, sticky reading-context region to the top command bar.

**Architecture:** Extend `_render_top_command_bar` so it receives the current page and content model, then renders static orientation data beside the existing tool controls. Reuse existing navigation helpers for structural page position and relative previous/next links. Keep behavior static and non-persistent.

**Tech Stack:** Python static builder, static CSS in `rich.css`, pytest contract tests, Playwright preview tests.

---

### Task 1: Contract Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Write failing rendered-HTML assertions**

In `test_render_fixture_uses_static_learning_shell`, assert that the reader page command bar includes a reading-context region:

```python
assert '<div class="raya-reading-context" aria-label="Current reading position">' in html
assert '<span class="raya-reading-context-course">Render Fixture</span>' in html
assert '<span class="raya-reading-context-page">Reader UX Fixture</span>' in html
assert '<span class="raya-reading-context-position">Page 5 of 6</span>' in html
assert '<nav class="raya-reading-context-sequence" aria-label="Compact previous and next pages">' in html
assert 'class="raya-reading-context-link raya-reading-context-prev"' in html
assert 'href="../numbered-objects/index.html"' in html
assert 'aria-label="Previous page: Numbered Objects"' in html
assert 'class="raya-reading-context-link raya-reading-context-next"' in html
assert 'href="../authoring-matrix/index.html"' in html
assert 'aria-label="Next page: Authoring Matrix Fixture"' in html
```

Add root and last page checks in the same test:

```python
assert 'class="raya-reading-context-link raya-reading-context-prev"' not in root_html
last_html = (course / "artifact" / "site" / "authoring-matrix" / "index.html").read_text(encoding="utf-8")
assert 'class="raya-reading-context-link raya-reading-context-next"' not in last_html
assert '<span class="raya-reading-context-position">Page 6 of 6</span>' in last_html
```

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell -q
```

Expected: FAIL because `raya-reading-context` markup does not exist.

### Task 2: Builder And CSS

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Render reading context**

Change `_render_top_command_bar` to accept `page` and `content_model`, then add a helper that renders:

```html
<div class="raya-reading-context" aria-label="Current reading position">
  <span class="raya-reading-context-course">Course</span>
  <span class="raya-reading-context-page">Page</span>
  <span class="raya-reading-context-position">Page N of M</span>
  <nav class="raya-reading-context-sequence" aria-label="Compact previous and next pages">
    <a class="raya-reading-context-link raya-reading-context-prev" ...>Previous</a>
    <a class="raya-reading-context-link raya-reading-context-next" ...>Next</a>
  </nav>
</div>
```

- [x] **Step 2: Add responsive CSS**

Add CSS for `.raya-reading-context`, `.raya-reading-context-page`,
`.raya-reading-context-position`, `.raya-reading-context-sequence`, and
`.raya-reading-context-link`. Keep text truncation stable on desktop and allow
wrapping on mobile without horizontal overflow.

- [x] **Step 3: Verify GREEN**

Run the Task 1 focused contract test. Expected: PASS.

### Task 3: Browser Proof And Docs

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] **Step 1: Add browser layout assertions**

Extend `test_render_fixture_command_bar_controls_are_dense_and_operable` to assert:

```javascript
contextText: document.querySelector('.raya-reading-context')?.innerText,
contextWidth: document.querySelector('.raya-reading-context')?.getBoundingClientRect().width,
prevHref: document.querySelector('.raya-reading-context-prev')?.getAttribute('href') || '',
nextHref: document.querySelector('.raya-reading-context-next')?.getAttribute('href') || '',
```

Assert the context contains the page title and page position, links are relative,
and command bar scroll width stays within viewport on desktop and mobile.

- [x] **Step 2: Update role docs and foundation**

Document the reading-context bar as static structural orientation, not progress
or recommendation state.

- [x] **Step 3: Focused verification**

Run:

```bash
git diff --check
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell tests/contracts/test_static_builder.py::test_render_fixture_search_graph_course_map_visible_text_avoids_learner_state_language tests/e2e/test_preview_static_read_path.py::test_render_fixture_command_bar_controls_are_dense_and_operable -q
```

Expected: PASS.

### Task 4: Review And Gates

**Files:** no source edits expected.

- [x] **Step 1: Request independent code review**

Dispatch a read-only reviewer focused on static orientation boundaries,
relative links, no learner-state wording, and responsive overflow.

- [x] **Step 2: Run gates**

Run:

```bash
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: all commands exit 0.

Evidence:
- Focused docs/contract/browser checks passed: `4 passed`.
- Renderer debug passed: `114 check(s)`.
- Host archive gate passed: `451 passed`; `check: passed`.
- Docker reference gate passed: `451 passed`; `check-docker: passed`.
