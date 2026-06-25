# Continuous Reader Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make ordinary reader pages calmer and immediately searchable while handing off to the existing static Search workspace.

**Architecture:** Add a small HTML search form inside the reader command bar and style it with existing shell tokens. Adjust renderer CSS so the main article is a continuous reading surface while course map and context rail remain secondary framed supports. Keep all search behavior in the existing static Search workspace.

**Tech Stack:** Python static builder, generated HTML/CSS, local browser tests with Playwright, pytest.

---

### Task 1: Contract-Test Reader Search Form And Continuous Article Surface

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Write the failing contract assertions**

Add assertions to `test_render_fixture_uses_static_learning_shell`:

```python
    assert '<form class="raya-command-search-form"' in html
    assert 'action="../_raya/search/index.html"' in html
    assert 'method="get"' in html
    assert 'name="q"' in html
    assert 'placeholder="Search course"' in html
    assert 'aria-label="Search course text"' in html
    assert '<button class="raya-command-search-submit" type="submit">' in html
```

Add CSS assertions to `test_static_build_writes_local_shell_resource`:

```python
    assert ".raya-command-search-form" in css_text
    assert ".raya-command-search-input" in css_text
    assert ".raya-command-search-submit" in css_text
    assert ".raya-main-article {\n  background: var(--raya-color-surface);" in css_text
    assert "box-shadow: 0 1rem 2.5rem rgba(31, 35, 40, 0.08);" not in css_text
```

- [ ] **Step 2: Run the focused contract tests to verify failure**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_build_writes_local_shell_resource tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell -q
```

Expected: fail because the command-bar search form and lighter article CSS do not exist yet.

### Task 2: Implement Reader Search Form Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [ ] **Step 1: Add a small renderer helper**

Add a helper near `_render_top_command_bar`:

```python
def _render_command_search_form(search_href: str) -> str:
    return (
        '<form class="raya-command-search-form" action="'
        f'{html.escape(search_href, quote=True)}" method="get" role="search">'
        '<label class="raya-visually-hidden" for="raya-command-search-input">'
        'Search course text</label>'
        '<input id="raya-command-search-input" class="raya-command-search-input" '
        'type="search" name="q" placeholder="Search course" '
        'autocomplete="off" aria-label="Search course text">'
        '<button class="raya-command-search-submit" type="submit">'
        '<span class="raya-visually-hidden">Open search results</span>'
        '<span aria-hidden="true">Search</span>'
        '</button>'
        '</form>'
    )
```

- [ ] **Step 2: Render it before the Search command link**

Inside `_render_top_command_bar`, insert:

```python
            _render_command_search_form(search_href),
```

immediately before the existing Search command link.

- [ ] **Step 3: Run the contract tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell -q
```

Expected: the markup assertions pass; CSS assertions still fail until Task 3.

### Task 3: Implement Continuous Reader CSS

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Add command-bar search CSS**

In the command-bar CSS section, add styles for:

```css
.raya-command-search-form {
  align-items: center;
  display: flex;
  gap: 0.35rem;
  min-width: min(17rem, 100%);
}
.raya-command-search-input {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  font: inherit;
  min-width: 9rem;
  padding: 0.45rem 0.6rem;
}
.raya-command-search-submit {
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  cursor: pointer;
  font: inherit;
  font-weight: 800;
  padding: 0.45rem 0.65rem;
}
.raya-command-search-input:focus-visible,
.raya-command-search-submit:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 2px;
}
```

- [ ] **Step 2: Lighten the main article surface**

Replace the shared shell surface rule so only support panels and inspection main
keep the framed card border. Give `.raya-main-article` its own background and
subtle inline separators:

```css
.raya-course-map,
.raya-learning-rail,
.raya-inspection-main {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  min-width: 0;
}
.raya-main-article {
  background: var(--raya-color-surface);
  border-block: 1px solid color-mix(in srgb, var(--raya-color-border) 42%, transparent);
  border-radius: 0;
  min-width: 0;
}
```

Keep the existing padding rule for `.raya-main-article`.

- [ ] **Step 3: Keep compact layouts readable**

Add a media rule under the existing small-screen section:

```css
  .raya-command-search-form {
    order: 2;
    width: 100%;
  }
  .raya-command-search-input {
    flex: 1 1 auto;
  }
```

- [ ] **Step 4: Run focused contract tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_build_writes_local_shell_resource tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell -q
```

Expected: pass.

### Task 4: Browser-Test Reader Search Handoff

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Extend `test_preview_serves_local_course_search_surface`**

After opening the preview, add a reader-page check:

```python
                    page.goto(f"{handle.base_url}/reader-ux/index.html", wait_until="networkidle")
                    page.locator("#raya-command-search-input").fill("projection residual")
                    page.locator(".raya-command-search-form").evaluate("form => form.requestSubmit()")
                    page.wait_for_url("**/_raya/search/index.html?q=projection+residual")
                    expect(page.locator("[data-raya-search-result='reader-ux']")).to_be_visible()
```

- [ ] **Step 2: Run the browser test to verify it fails before implementation if Task 2 was skipped, then passes after Tasks 2-3**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_course_search_surface -q
```

Expected: pass after Tasks 2-3.

### Task 5: Documentation And Verification

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`

- [ ] **Step 1: Document the behavior**

Update the renderer contract and student guides to state that reader pages may
include a compact search form that submits to the generated static Search
workspace and that article framing should keep authored content primary.

- [ ] **Step 2: Run focused verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_build_writes_local_shell_resource tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_course_search_surface -q
./scripts/check-render-debug.sh
```

Expected: focused tests pass and `check-render-debug: passed`.

- [ ] **Step 3: Request independent review**

Ask a reviewer to inspect static/local constraints, shell accessibility, mobile
overflow, and whether the continuous article surface still keeps the course map
and right rail operable.

- [ ] **Step 4: Run full gates sequentially before push**

Run:

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: both pass.

