# Discovery Workspace Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert Search and Practice into cohesive static discovery workspaces with desktop panels, safer shared comfort controls, and stronger tests.

**Architecture:** Reuse the current Python static builder and local JavaScript resource model. Add generated workspace markup in `builder.py`, CSS in `rendering.py`, small behavior changes in `practice.py` only where needed, and tests before implementation.

**Tech Stack:** Python 3.10, pytest, Playwright browser tests, local static HTML/CSS/JavaScript resources.

---

### Task 1: Contract Tests For Discovery Workspace Markup

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Add failing assertions for Search workspace regions**

Add assertions to `test_build_writes_local_course_search_surface` requiring:

```python
assert "raya-search-workspace" in search_html
assert "raya-search-control-panel" in search_html
assert "raya-search-results-panel" in search_html
assert "raya-search-context-panel" in search_html
assert "data-raya-search-summary-count" in search_html
assert "data-raya-search-context" in search_html
assert "data-raya-search-context-title" in search_html
assert "data-raya-search-context-meta" in search_html
```

- [x] **Step 2: Add failing assertions for Practice workspace regions**

Add assertions to `test_build_writes_static_official_practice_workspace` requiring:

```python
assert "raya-practice-workspace" in practice_html
assert "raya-practice-control-panel" in practice_html
assert "raya-practice-results-panel" in practice_html
assert "raya-practice-context-panel" in practice_html
assert "data-raya-practice-summary-count" in practice_html
assert "data-raya-practice-context" in practice_html
assert "data-raya-practice-context-title" in practice_html
assert "data-raya-practice-context-meta" in practice_html
assert 'src="../render/accessibility/open-dyslexic-toggle.js"' in practice_html
```

- [x] **Step 3: Run focused contract tests and confirm failure**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace -q
```

Expected: both tests fail because workspace markup is missing.

### Task 2: Browser Tests For Discovery Workspace Behavior

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Extend Search browser test**

In the existing search static-read-path test, assert desktop and mobile workspace layout has no horizontal overflow and that entering a query updates visible results and context summary without external requests.

- [x] **Step 2: Extend Practice browser test**

In the existing practice static-read-path test, assert desktop and mobile workspace layout has no horizontal overflow, type filters still work, context summary updates, and OpenDyslexic toggles via the shared accessibility script.

- [x] **Step 3: Run focused browser tests and confirm failure**

Run the affected e2e tests by exact test names after locating them with `rg -n "search|practice" tests/e2e/test_preview_static_read_path.py`.

Expected: tests fail because the workspace regions and context summary elements do not exist yet.

### Task 3: Implement Search Workspace Markup And Behavior

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/search.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Wrap Search controls/results/context**

In `_render_search_surface`, replace the flat controls/results structure with:

- `<section class="raya-search-workspace" aria-label="Search workspace">`
- `<aside class="raya-search-control-panel">` containing search input, clear button, status, and a generated summary count.
- `<section class="raya-search-results-panel">` containing empty state and ordered results.
- `<aside class="raya-search-context-panel" data-raya-search-context>` with public static guidance and selected/visible-result metadata placeholders.

- [x] **Step 2: Update Search script context**

In `search.py`, update the count element and context title/meta from the active result or from visible count. Do not add storage, fetch, XHR, external URLs, or answer/support data.

- [x] **Step 3: Add Search CSS**

In `rendering.py`, add responsive workspace CSS: three columns on wide desktop, two/one columns at smaller widths, sticky side panels on desktop, no horizontal overflow, and compact cards.

- [x] **Step 4: Run focused Search tests**

Run the focused contract and e2e search tests until green.

### Task 4: Implement Practice Workspace Markup And Shared Comfort Controls

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/practice.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Link shared accessibility script**

In `_render_practice_surface`, add `accessibility_js_href` and load the shared `../render/accessibility/open-dyslexic-toggle.js` resource like Search and Graph do.

- [x] **Step 2: Remove duplicate comfort-control logic from Practice script**

In `practice.py`, remove `.raya-font-toggle` and `.raya-text-size-toggle` handling. Leave only practice filtering/search behavior.

- [x] **Step 3: Wrap Practice controls/results/context**

In `_render_practice_surface`, add:

- `<section class="raya-practice-workspace" aria-label="Official practice workspace">`
- `<aside class="raya-practice-control-panel">` containing search, clear, type filters, status, and summary count.
- `<section class="raya-practice-results-panel">` containing empty state and grouped official-object cards.
- `<aside class="raya-practice-context-panel" data-raya-practice-context>` with public accepted-object metadata placeholders.

- [x] **Step 4: Update Practice script context**

Update visible-count summary and selected/first visible object context from public embedded metadata only. Keep filters transient.

- [x] **Step 5: Add Practice CSS**

Use the same responsive discovery workspace CSS pattern as Search, while preserving existing official-object card visual hierarchy.

- [x] **Step 6: Run focused Practice tests**

Run the focused contract and e2e practice tests until green.

### Task 5: Documentation And Verification

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] **Step 1: Document current behavior**

Update the foundation renderer contract to say Search and Practice use a static discovery workspace layout with control/results/context panels.

- [x] **Step 2: Update role docs**

Add concise English and Spanish guidance for using Search and Practice workspaces without implying progress, recommendations, scoring, or personal state.

- [x] **Step 3: Run verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_local_course_search_surface tests/contracts/test_static_builder.py::test_build_writes_static_official_practice_workspace -q
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: all pass.
