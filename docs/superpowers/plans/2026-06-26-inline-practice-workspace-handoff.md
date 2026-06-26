# Inline Practice Workspace Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a visible inline handoff from each rendered Official practice section to the existing page-scoped Practice workspace.

**Architecture:** Reuse the current static builder path. `_render_page()` computes the page-scoped Practice URL from the current page output path and passes it into `_render_official_practice_section()`, which emits one static action row when official objects render. CSS lives in `rendering.py` and uses existing skin tokens only.

**Tech Stack:** Python static builder, generated HTML/CSS, pytest contract tests, Playwright e2e tests.

---

### Task 1: Contract Test For Inline Practice Handoff

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Add failing assertions**

In the existing static official practice contract test that reads
`unit/topic/index.html`, add:

```python
official_section = _tag_html(topic_html, "section", "raya-official-practice")
assert 'class="raya-official-practice-actions"' in official_section
assert (
    '<a class="raya-official-practice-open" '
    'href="../../_raya/practice/index.html?page=first-topic">'
    "Open all page practice</a>"
) in official_section
```

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_minimal_fixture_into_temporary_course -q
```

Expected: FAIL because the current inline Official practice section does not
emit an action row.

### Task 2: Static Markup And CSS Implementation

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Pass the page-scoped href into the official section**

In `_render_page()`, call:

```python
official_practice_html = _render_official_practice_section(
    official_objects,
    practice_href=course_map_practice_href,
)
```

Update the function signature:

```python
def _render_official_practice_section(
    objects: list[dict[str, Any]],
    *,
    practice_href: str,
) -> str:
```

- [x] **Step 2: Emit the action row**

Inside `_render_official_practice_section()`, after the explanatory paragraph
and before the rendered objects, add:

```python
(
    '<p class="raya-official-practice-actions">'
    f'<a class="raya-official-practice-open" href="{html.escape(practice_href)}">'
    "Open all page practice</a>"
    "</p>"
),
```

- [x] **Step 3: Style the action row**

In `packages/static/src/raya_static/rendering.py`, near the
`.raya-official-practice` CSS, add:

```css
.raya-official-practice-actions {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0;
}
.raya-official-practice-open {
  background: var(--raya-color-accent);
  border: 1px solid var(--raya-color-accent);
  border-radius: 999px;
  color: var(--raya-color-surface);
  display: inline-flex;
  font-size: 0.86rem;
  font-weight: 850;
  line-height: 1;
  padding: 0.55rem 0.75rem;
  text-decoration: none;
}
.raya-official-practice-open:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 3px;
}
```

- [x] **Step 4: Verify GREEN for contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_minimal_fixture_into_temporary_course -q
```

Expected: PASS.

### Task 3: Browser Evidence For Page-Scoped Handoff

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add browser assertions**

Add a render-fixture browser test or extend the existing study-object family
test to assert:

```python
action = page.locator("#raya-official-practice .raya-official-practice-open")
assert action.is_visible()
assert action.get_attribute("href") == "../_raya/practice/index.html?page=reader-ux"
page.goto(f"{base_url}/_raya/practice/index.html?page=reader-ux", wait_until="networkidle")
focus_notice = page.locator("[data-raya-practice-page-focus]")
assert focus_notice.is_visible()
assert "Projection Residuals" in focus_notice.inner_text()
visible_pages = page.locator('[data-raya-practice-object]:not([hidden])').evaluate_all(
    "nodes => nodes.map((node) => node.dataset.rayaPracticePage)"
)
assert visible_pages == ["reader-ux", "reader-ux"]
```

- [x] **Step 2: Run browser test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_study_object_families_are_visually_distinct -q
```

Expected: PASS after implementation.

### Task 4: Verification, Review, Commit, Push

**Files:**
- Create: `docs/superpowers/specs/2026-06-26-inline-practice-workspace-handoff-design.md`
- Create: `docs/superpowers/plans/2026-06-26-inline-practice-workspace-handoff.md`
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Run focused tests**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_minimal_fixture_into_temporary_course tests/e2e/test_preview_static_read_path.py::test_render_fixture_study_object_families_are_visually_distinct -q
```

- [x] **Step 2: Run render debug**

```bash
./scripts/check-render-debug.sh
```

- [x] **Step 3: Request code review**

Ask an independent reviewer to verify the handoff is static, page-scoped,
local-only, and does not add state or private data leakage.

- [ ] **Step 4: Commit and push**

```bash
git add docs/superpowers/specs/2026-06-26-inline-practice-workspace-handoff-design.md docs/superpowers/plans/2026-06-26-inline-practice-workspace-handoff.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add inline practice workspace handoff"
git push origin new_rayalucaria
```

## Plan Self-Review

- Every requirement in the design maps to a test or implementation step.
- The plan uses existing helpers and current emitted classes.
- No step introduces external requests, browser storage, scoring, schema
  changes, or object-level Practice focus.
