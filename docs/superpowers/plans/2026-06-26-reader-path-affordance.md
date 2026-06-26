# Reader Path Affordance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make first-viewport page-brief navigation visibly scan as compact static learning-path controls.

**Architecture:** The renderer already derives static previous/next links from `ContentModel` navigation data. This slice renders those links inside the existing page brief facts row and updates `rich.css` generation so page-brief action values render as chip-like controls.

**Tech Stack:** Python static renderer, generated HTML/CSS, Playwright e2e tests through `uv`.

---

### Task 1: Failing Page Brief Path Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Write the failing test**

Extend `test_preview_reader_page_brief_is_visible_static_and_responsive`.
The test should build the minimal fixture, open `/unit/topic/index.html`, and
assert:

```python
path_fact = brief.locator(".raya-page-brief-path")
assert path_fact.is_visible()
assert "Learning path" in path_fact.inner_text()
```

It should also assert that the previous/next anchors have:

```python
previous = path_fact.locator("[rel='prev']")
next_link = path_fact.locator("[rel='next']")
assert previous.get_attribute("data-raya-prev-page") == ""
assert previous.get_attribute("aria-keyshortcuts") == "ArrowLeft"
assert next_link.get_attribute("data-raya-next-page") == ""
assert next_link.get_attribute("aria-keyshortcuts") == "ArrowRight"
assert previous.get_attribute("href") == "../../index.html"
assert next_link.get_attribute("href") == "../../unit/index.html"
```

Finally, read computed styles and mobile width:

```python
assert previous_style["display"] == "inline-flex"
assert previous_style["borderStyle"] == "solid"
assert previous_style["backgroundColor"] != "rgba(0, 0, 0, 0)"
assert box["width"] <= viewport["width"]
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_reader_page_brief_is_visible_static_and_responsive -q
```

Expected: FAIL because `.raya-page-brief-path` is missing.

### Task 2: Static Page Brief Markup And CSS Implementation

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Add static page-brief path markup**

Add a small helper in `builder.py`:

```python
def _page_brief_sequence_links(page: ContentPage, content_model: ContentModel) -> str:
    return _sequence_links(page, content_model)
```

Then add a `Learning path` fact after `Position` in `_render_page_brief` when
the helper returns links.

- [x] **Step 2: Style page-brief action links**

Update `.raya-page-brief-value a` CSS in `rendering.py` so brief action links
render as compact chips.

The links should use `inline-flex`, `border`, `background`, `font-weight: 800`,
`text-decoration: none`, visible hover/focus states, and responsive wrapping.

- [x] **Step 3: Run test to verify it passes**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_reader_page_brief_is_visible_static_and_responsive -q
```

Expected: PASS.

### Task 3: Verification And Delivery

**Files:**
- Verify modified files from Tasks 1 and 2.

- [x] **Step 1: Run focused sequence tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_reader_page_brief_is_visible_static_and_responsive tests/e2e/test_preview_static_read_path.py::test_render_fixture_end_of_page_sequence_cards_are_static_and_responsive -q
```

Expected: PASS.

- [x] **Step 2: Rebuild render fixture**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture
```

Expected: build passes and writes `examples/courses/render-fixture/artifact/site`.

- [x] **Step 3: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-reader-path-affordance-design.md docs/superpowers/plans/2026-06-26-reader-path-affordance.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py
git commit -m "Clarify reader path navigation"
git push origin new_rayalucaria
```

Expected: commit is pushed to `origin/new_rayalucaria`.
