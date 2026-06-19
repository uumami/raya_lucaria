# Section Landing Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Upgrade generated child-page indexes into static section landing cards.

**Architecture:** Reuse the existing `_render_generated_index()` insertion point so the cards stay article-local and derived from current content hierarchy. Add semantic classed markup in `builder.py`, token-based styling in `rendering.py`, focused contract/e2e tests, and role/foundation docs.

**Tech Stack:** Python 3.10 static builder, local CSS, pytest, Playwright.

---

### Task 1: Contract Test For Generated Index Cards

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Add failing assertions**

Extend the render-fixture/static-builder coverage to assert that generated
indexes include:

```python
assert 'class="raya-generated-index raya-section-landing"' in html
assert 'class="raya-section-card-list"' in html
assert 'class="raya-section-card"' in html
assert 'class="raya-section-card-title"' in html
assert 'class="raya-section-card-summary"' in html
assert "recommend" not in html.lower()
assert "progress" not in html.lower()
assert "mastery" not in html.lower()
```

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages -q
```

Expected: FAIL on missing `raya-section-landing`.

### Task 2: Browser Test For Landing Card UX

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add browser assertions**

Extend the render-fixture preview test to open `index.html` on desktop and
mobile, assert card count, assert no horizontal overflow, and click the first
card link to prove normal navigation.

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_section_landing_cards_are_static_navigation -q
```

Expected: FAIL on missing card selectors.

### Task 3: Generated Index Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [x] **Step 1: Update `_render_generated_index()`**

Render child entries as:

```html
<section class="raya-generated-index raya-section-landing" aria-label="Generated index">
  <h2>Course Index</h2>
  <ol class="raya-section-card-list">
    <li class="raya-section-card">
      <a class="raya-section-card-link" href="...">
        <span class="raya-section-card-title">...</span>
        <span class="raya-section-card-summary">...</span>
        <span class="raya-section-card-meta">...</span>
      </a>
    </li>
  </ol>
</section>
```

Omit empty summary/meta spans.

- [x] **Step 2: Run contract test**

Run the focused contract test from Task 1. Expected: PASS once CSS-independent
markup exists.

### Task 4: Card Styling And Docs

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] **Step 1: Add responsive card CSS**

Use existing `--raya-*` tokens. Cards should be links, fit desktop/mobile, have
visible focus states, and avoid nested card styling.

- [x] **Step 2: Document behavior**

Document cards as generated course structure. Explicitly avoid personal progress
or recommendation wording.

### Task 5: Review, Verify, Commit, Push

**Files:**
- All files above.

- [x] **Step 1: Request independent review**

Use a read-only subagent on the uncommitted diff. Fix valid Critical/Important
findings.

- [x] **Step 2: Final verification**

Run:

```bash
git diff --check
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages tests/e2e/test_preview_static_read_path.py::test_render_fixture_section_landing_cards_are_static_navigation -q
./scripts/check-render-debug.sh
./scripts/check.sh
```

- [x] **Step 3: Commit and push**

Commit with:

```bash
git commit -m "Add section landing cards"
git push origin new_rayalucaria
```
