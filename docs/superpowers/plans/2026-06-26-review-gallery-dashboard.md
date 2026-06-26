# Review Gallery Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `examples/gallery/index.html` a static review dashboard for fixture UX states and debugging commands.

**Architecture:** Keep the gallery as a hand-authored static HTML page. Add sections and links only; do not add JavaScript, iframes, generated screenshots, or generated artifact files. Update existing gallery tests to protect fixture authority, deep links, and responsive layout.

**Tech Stack:** Static HTML/CSS, pytest, Playwright static server tests.

**Status: implemented.** This checklist is a historical execution record. Current
source support lives in `examples/gallery/index.html` and gallery static-read
path tests.

---

### Task 1: Gallery Contract Tests

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `tests/e2e/test_static_read_path.py`

- [x] **Step 1: Write failing tests**

Add assertions that `examples/gallery/index.html` contains:

```python
assert "Review states" in gallery_html
assert "../courses/render-fixture/artifact/site/reader-ux/index.html" in gallery_html
assert "../courses/render-fixture/artifact/site/_raya/graph/index.html?page=reader-ux" in gallery_html
assert "../courses/render-fixture/artifact/site/_raya/search/index.html?q=matrix" in gallery_html
assert "../courses/render-fixture/artifact/site/_raya/practice/index.html?page=reader-ux" in gallery_html
assert "../courses/render-fixture/artifact/site/_raya/tasks/index.html?page=reader-ux" in gallery_html
assert "../courses/render-fixture/artifact/site/_raya/schedule/index.html?page=reader-ux" in gallery_html
assert "scripts/check-render-debug.sh" in gallery_html
assert "./scripts/check-render-debug.sh" not in gallery_html
assert "<script" not in gallery_html
assert "<iframe" not in gallery_html
assert "https://" not in gallery_html
assert "http://" not in gallery_html
assert ".png" not in gallery_html
```

Also update the responsive browser gallery test to assert `.gallery-review-grid` cards do not overlap.

- [x] **Step 2: Run tests to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_static_read_path.py::test_examples_gallery_static_read_path_links_built_fixtures tests/e2e/test_preview_static_read_path.py::test_examples_gallery_has_reviewable_responsive_fixture_cards -q
```

Expected: FAIL because review-state links and sections are not present.

### Task 2: Gallery HTML/CSS

**Files:**
- Modify: `examples/gallery/index.html`

- [x] **Step 1: Implement static dashboard sections**

Add:

- review checklist;
- review-state cards for reader shell, graph/search, official workspaces, and render debug;
- command block with `scripts/check-render-debug.sh`, `uv run raya build examples/courses/render-fixture`, and `uv run raya preview examples/courses/render-fixture`.

- [x] **Step 2: Keep styling responsive and static**

Use CSS classes such as `.gallery-section`, `.gallery-review-grid`, `.gallery-command-list`, and `.gallery-checklist`. Keep all CSS inline in the gallery page, matching the current file style.

- [x] **Step 3: Run tests to verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_static_read_path.py::test_examples_gallery_static_read_path_links_built_fixtures tests/e2e/test_preview_static_read_path.py::test_examples_gallery_has_reviewable_responsive_fixture_cards -q
```

Expected: PASS.

### Task 3: Verification and Review

**Files:**
- No planned source changes unless review finds issues.

- [x] **Step 1: Run focused checks**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_static_read_path.py::test_examples_gallery_static_read_path_links_built_fixtures tests/e2e/test_preview_static_read_path.py::test_examples_gallery_has_reviewable_responsive_fixture_cards -q
git diff --check
```

Expected: PASS and no whitespace errors.

- [x] **Step 2: Request independent review**

Ask a reviewer to inspect the gallery diff for fixture-authority labeling, deployment-neutral links, no external assets, and responsive layout coverage.

- [x] **Step 3: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-review-gallery-dashboard-design.md docs/superpowers/plans/2026-06-26-review-gallery-dashboard.md examples/gallery/index.html tests/e2e/test_static_read_path.py tests/e2e/test_preview_static_read_path.py
git commit -m "Expand example gallery review dashboard"
git push origin new_rayalucaria
```
