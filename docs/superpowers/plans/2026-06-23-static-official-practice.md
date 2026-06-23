# Static Official Practice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render validated official learning objects on their owning static page as usable practice material without dynamic learner state.

**Architecture:** Group discovered official objects by `scope.quantum` during build and pass the owning page's objects into `_render_page`. Add focused renderer helpers in `builder.py` that emit escaped, static article sections and native `details` reveal controls. Use existing `shell.js` only for generic page behavior; no official-practice runtime script is needed.

**Tech Stack:** Python 3.10 static builder, semantic HTML, native `details`, pytest, Playwright.

---

### Task 1: Add Failing Contract Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Add official practice assertions**

Extend `test_build_minimal_fixture_into_temporary_course` after reading
`index_html` by also reading `unit/topic/index.html` and asserting:

```python
    topic_html = (artifact / "site" / "unit" / "topic" / "index.html").read_text(
        encoding="utf-8"
    )
    assert '<section class="raya-official-practice"' in topic_html
    assert 'aria-label="Official practice"' in topic_html
    assert 'id="raya-official-first-topic-card"' in topic_html
    assert "What loop does Raya Lucaria support?" in topic_html
    assert "Read, retrieve, reflect, adapt, revisit, and contribute." in topic_html
    assert 'id="raya-official-first-topic-prompt"' in topic_html
    assert "Explain how retrieval practice differs from rereading." in topic_html
    assert 'id="raya-official-first-topic-quiz"' in topic_html
    assert "Which action is part of the Raya Lucaria learning loop?" in topic_html
    assert "Retrieve" in topic_html
    assert "Vendor lock-in" in topic_html
    assert "Correct option" in topic_html
    assert "_official" not in topic_html
    assert "source_path" not in topic_html
    assert "localStorage" not in topic_html
    assert "fetch(" not in topic_html
```

- [x] **Step 2: Run the focused contract test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_minimal_fixture_into_temporary_course
```

Expected: FAIL because the rendered page does not contain `raya-official-practice`.

### Task 2: Add Failing Browser Tests

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add official practice browser coverage**

Add a test that previews `examples/courses/minimal`, opens
`/unit/topic/index.html`, checks the practice section on desktop and mobile,
opens the card answer and quiz answer `details`, asserts no horizontal overflow,
and asserts no network requests after page load.

- [x] **Step 2: Run the focused browser test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_minimal_fixture_official_practice_is_static_and_revealable
```

Expected: FAIL because the practice section does not exist.

### Task 3: Implement Static Practice Rendering

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Group official objects by page**

Add `_official_objects_by_page(official_objects)` near `_official_counts()` and
pass `official_by_page.get(page.id, [])` into `_render_page`.

- [x] **Step 2: Add rendering helpers**

Add helpers in `builder.py`:

- `_render_official_practice_section(objects)`
- `_render_official_object(item)`
- `_render_official_content(item)`
- `_official_type_label(object_type)`
- `_official_text(value)`
- `_official_list(values)`
- `_official_reveal(summary, body, class_name)`

The helpers must escape all strings with `html.escape`, sort by
`source_order`, and avoid source-path output.

- [x] **Step 3: Insert section in page article**

Render official practice after `article_connections_html` and before
`_render_article_sequence_cards(...)`.

- [x] **Step 4: Add CSS**

Add `.raya-official-practice`, `.raya-official-object`,
`.raya-official-object-header`, `.raya-official-kind`,
`.raya-official-authority`, `.raya-official-prompt`,
`.raya-official-options`, and `.raya-official-reveal` rules to
`rendering.py`, reusing existing skin tokens.

- [x] **Step 5: Run focused tests and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_build_minimal_fixture_into_temporary_course
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_minimal_fixture_official_practice_is_static_and_revealable
```

Expected: both pass.

### Task 4: Documentation

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

- [x] **Step 1: Update docs**

Document page-level official practice rendering, native reveal behavior, and
the no scoring/progress/storage contract.

- [x] **Step 2: Run visible-language check**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_render_fixture_search_graph_course_map_visible_text_avoids_learner_state_language
```

Expected: pass.

### Task 5: Verify, Review, Commit, Push

**Files:**
- All modified files

- [x] **Step 1: Run focused render debug**

```bash
./scripts/check-render-debug.sh
```

- [x] **Step 2: Run host gate**

```bash
./scripts/check.sh
```

- [x] **Step 3: Run Docker gate**

```bash
./scripts/check-docker.sh
```

- [x] **Step 4: Request code review**

Use `superpowers:requesting-code-review` on the final diff.

- [x] **Step 5: Commit and push**

```bash
git add docs/superpowers/specs/2026-06-23-static-official-practice-design.md \
  docs/superpowers/plans/2026-06-23-static-official-practice.md \
  docs/foundation/20_learning_renderer_contract.md \
  docs/guides/en/students/index.md docs/guides/en/professors/index.md \
  docs/guides/en/contributors/index.md docs/guides/en/agents/index.md \
  docs/guides/es/estudiantes/index.md docs/guides/es/profesores/index.md \
  docs/guides/es/colaboradores/index.md docs/guides/es/agentes/index.md \
  packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py \
  tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Render static official practice"
git push origin new_rayalucaria
```
