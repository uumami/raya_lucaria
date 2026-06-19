# Reader Text Size Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local static text-size control to the reader command bar.

**Architecture:** Extend the existing accessibility resource generator and command bar. The feature uses local CSS custom properties plus a small local script; it does not change skin selection, course data, graph data, or MathJax rendering.

**Tech Stack:** Python 3.10, static HTML/CSS/JavaScript, pytest, Playwright.

---

### Task 1: Contract Surface

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/accessibility.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Write failing command-bar contract assertions**

Extend `test_render_fixture_learning_shell_has_course_tools_and_context_regions` to assert:

```python
assert '<button class="raya-command raya-command-size raya-text-size-toggle"' in html
assert 'aria-label="Text size: normal"' in html
assert '<span class="raya-command-label">Text size</span>' in html
```

- [ ] **Step 2: Write failing generated-resource assertions**

Extend `test_render_fixture_builds_rich_static_pages` to assert the accessibility CSS contains `--raya-reader-text-scale`, `[data-raya-text-size="large"]`, and `[data-raya-text-size="x-large"]`; assert the accessibility JavaScript contains `raya:text-size` and does not contain `fetch(`.

- [ ] **Step 3: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_learning_shell_has_course_tools_and_context_regions tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages -q
```

Expected: fail because the text-size command and resources do not exist yet.

- [ ] **Step 4: Implement minimal contract behavior**

Add the command button in `_render_top_command_bar`, add `.raya-command-size::before { content: "T"; }`, add CSS variables and reader text scaling, and extend the accessibility JavaScript with text-size cycling.

- [ ] **Step 5: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_learning_shell_has_course_tools_and_context_regions tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages -q
```

Expected: pass.

### Task 2: Browser Behavior

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `packages/static/src/raya_static/accessibility.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Write failing browser test**

Add `test_render_fixture_text_size_toggle_changes_reader_scale` that opens `index.html`, records `.raya-main-article` font size, clicks `.raya-text-size-toggle`, verifies `data-raya-text-size` and font size increase for `large`, clicks again for `x-large`, reloads to verify persistence, then clicks back to `normal` and verifies the URL is unchanged.

- [ ] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_text_size_toggle_changes_reader_scale -q
```

Expected: fail until the command and script exist.

- [ ] **Step 3: Finish script details**

Ensure invalid stored values fall back to `normal`, labels update to `Text size: normal`, `Text size: large`, and `Text size: x-large`, and only non-normal states set `aria-pressed="true"`.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_text_size_toggle_changes_reader_scale -q
```

Expected: pass.

### Task 3: Documentation and Debug Parity

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

- [ ] **Step 1: Update docs**

Document text size as a local static reader comfort preference, distinct from source-authored skins and course meaning.

- [ ] **Step 2: Run focused gates**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_text_size_toggle_changes_reader_scale tests/e2e/test_preview_static_read_path.py::test_render_fixture_command_bar_controls_are_dense_and_operable -q
./scripts/check-render-debug.sh
```

Expected: all pass.

### Task 4: Review and Commit

**Files:**
- Review all changed files.

- [ ] **Step 1: Request independent review**

Ask a reviewer to check reset-principle alignment, accessibility behavior, tests, and docs.

- [ ] **Step 2: Address valid findings**

For behavior changes, add or update a failing test first; for doc-only findings, patch the relevant authority or role doc.

- [ ] **Step 3: Final verification**

Run:

```bash
git diff --check
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_text_size_toggle_changes_reader_scale tests/e2e/test_preview_static_read_path.py::test_render_fixture_command_bar_controls_are_dense_and_operable -q
./scripts/check-render-debug.sh
```

Expected: all pass.

- [ ] **Step 4: Commit**

Run:

```bash
git add docs/superpowers/specs/2026-06-19-reader-text-size-control-design.md docs/superpowers/plans/2026-06-19-reader-text-size-control.md packages/static/src/raya_static/accessibility.py packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/en/professors/index.md docs/guides/en/contributors/index.md docs/guides/en/agents/index.md docs/guides/es/estudiantes/index.md docs/guides/es/profesores/index.md docs/guides/es/colaboradores/index.md docs/guides/es/agentes/index.md
git commit -m "Add reader text size control"
```

Expected: commit succeeds.
