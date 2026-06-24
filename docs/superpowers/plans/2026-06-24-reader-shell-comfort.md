# Reader Shell Comfort Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the static course shell more comfortable on desktop and make the render fixture read like a credible mini-lesson while preserving current renderer contracts.

**Architecture:** Keep the existing static HTML structure and JavaScript behavior. Update CSS for visual hierarchy and collapsed controls, then update render-fixture source content and local assets so existing builder paths produce a better student-facing page.

**Tech Stack:** Python static builder, generated HTML/CSS/JS, Markdown fixture content, Playwright browser e2e tests, local `uv` verification.

---

### Task 1: Browser Tests For Reader Comfort And Fixture Pedagogy

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add failing wide-desktop comfort assertions**

Add assertions to `test_render_fixture_desktop_shell_has_modern_workspace_chrome` that capture article primacy, quieter side chrome, and compact collapsed controls:

```python
assert chrome["articleWidth"] >= 980
assert chrome["articleWidth"] > chrome["mapWidth"] * 3
assert chrome["articleWidth"] > chrome["railWidth"] * 3
assert chrome["courseMapShadow"] == "none" or chrome["courseMapShadowAlpha"] <= 0.04
assert chrome["railShadow"] == "none" or chrome["railShadowAlpha"] <= 0.04
```

Also add a collapsed-state check on the same page:

```python
page.click(".raya-course-map-toggle")
page.click("[data-raya-learning-rail-collapse]")
collapsed = page.evaluate(
    """() => {
      const map = document.querySelector('nav.raya-course-map');
      const rail = document.querySelector('aside.raya-learning-rail');
      const mapToggle = document.querySelector('#raya-course-map .raya-course-map-toggle');
      const railExpand = document.querySelector('[data-raya-learning-rail-expand]');
      return {
        mapWidth: map.getBoundingClientRect().width,
        railWidth: rail.getBoundingClientRect().width,
        mapLabel: getComputedStyle(mapToggle, '::after').content,
        railLabel: getComputedStyle(railExpand, '::after').content,
        mapToggleWidth: mapToggle.getBoundingClientRect().width,
        railExpandWidth: railExpand.getBoundingClientRect().width,
      };
    }"""
)
assert collapsed["mapWidth"] <= 82
assert collapsed["railWidth"] <= 64
assert collapsed["mapLabel"] != '"Map"'
assert collapsed["railLabel"] != '"Info"'
assert collapsed["mapToggleWidth"] >= 40
assert collapsed["railExpandWidth"] >= 40
```

- [x] **Step 2: Add failing render-fixture mini-lesson assertions**

Add a new e2e test that opens `/reader-ux/index.html` and asserts:

```python
assert page.locator("h1").inner_text() == "Projection Residuals"
article_text = page.locator("article.raya-main-article").inner_text()
assert "What remains after projecting a vector onto a line?" in article_text
assert "Try this first" in article_text
assert "Misconception" in article_text
assert "Reader UX fixture" not in page.locator(".raya-page-brief").inner_text()
assert page.locator('img[alt="Projection residual diagram"]').is_visible()
assert page.locator("#raya-official-practice").is_visible()
assert page.locator(".raya-official-object").count() >= 2
```

- [x] **Step 3: Run tests to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_desktop_shell_has_modern_workspace_chrome tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_ux_is_learning_showcase -q
```

Expected: FAIL because the current article is narrower/side panels are louder, collapsed labels are `"Map"` and `"Info"`, the fixture title is `Reader UX Fixture`, the projection diagram is the generic static-path SVG, and there are no render-fixture official objects.

### Task 2: CSS Reader-Shell Comfort

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Implement minimal CSS changes**

Update `.raya-learning-shell`, side panel, and desktop media rules so:

- wide desktop article width reaches at least `980px` in the fixture test;
- map and rail remain between useful bounds but no longer visually compete with the article;
- collapsed map and rail use compact labels such as `☰` and `i`;
- controls keep stable square dimensions and accessible button text remains in HTML.

- [x] **Step 2: Run the wide-desktop test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_desktop_shell_has_modern_workspace_chrome -q
```

Expected: PASS.

### Task 3: Render-Fixture Mini-Lesson Content

**Files:**
- Modify: `examples/courses/render-fixture/raya.yaml`
- Modify: `examples/courses/render-fixture/course/4_reader_ux/0_index.md`
- Create: `examples/courses/render-fixture/course/4_reader_ux/_assets/projection-residual.svg`
- Create: `examples/courses/render-fixture/course/4_reader_ux/_official/cards/1_projection_residual_card.yaml`
- Create: `examples/courses/render-fixture/course/4_reader_ux/_official/quizzes/1_projection_residual_quiz.yaml`

- [x] **Step 1: Update visible metadata and lesson opening**

Change `reader-ux` metadata and H1 to student-facing projection residual language. Add an early callout that asks the learner to predict what remains after a projection before the formal definition.

- [x] **Step 2: Replace fixture-only headings and figure**

Rename fixture-only headings to meaningful lesson headings. Replace the generic static-path SVG reference with `_assets/projection-residual.svg`.

- [x] **Step 3: Add official practice objects**

Add one official card and one quiz under colocated `_official/` for the `reader-ux` page. Use stable IDs and ordinary official object schema fields.

- [x] **Step 4: Run the mini-lesson test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_ux_is_learning_showcase -q
```

Expected: PASS.

### Task 4: Focused Verification

**Files:**
- Existing tests and scripts only.

- [x] **Step 1: Run focused shell/fixture/browser tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_desktop_shell_has_modern_workspace_chrome tests/e2e/test_preview_static_read_path.py::test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_ux_is_learning_showcase tests/e2e/test_preview_static_read_path.py::test_preview_reader_print_view_is_static_handout -q
```

Expected: PASS.

- [x] **Step 2: Run render-debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS with no raw visible TeX, no external renderer requests, no overflow, and generated screenshot artifacts only in the debug temp directory.

### Task 5: Review, Full Check, Commit, Push

**Files:**
- All changed files.

- [x] **Step 1: Request independent code/UX review**

Dispatch at least one independent review agent with low context. Ask it to inspect the final diff for static renderer contract violations, learner-state language, external requests, layout regressions, and fixture-quality regressions.

- [x] **Step 2: Address review findings with tests first when behavior changes**

If review identifies behavior gaps, add or update tests before implementation changes.

- [x] **Step 3: Run final host check**

Run:

```bash
./scripts/check.sh
```

Expected: PASS.

- [x] **Step 4: Commit and push**

Run:

```bash
git status -sb
git add docs/superpowers/specs/2026-06-24-reader-shell-comfort-design.md docs/superpowers/plans/2026-06-24-reader-shell-comfort.md packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py examples/courses/render-fixture/raya.yaml examples/courses/render-fixture/course/4_reader_ux/0_index.md examples/courses/render-fixture/course/4_reader_ux/_assets/projection-residual.svg examples/courses/render-fixture/course/4_reader_ux/_official/cards/1_projection_residual_card.yaml examples/courses/render-fixture/course/4_reader_ux/_official/quizzes/1_projection_residual_quiz.yaml
git commit -m "Improve reader shell comfort"
git push origin new_rayalucaria
```

Expected: branch `new_rayalucaria` is clean and `origin/new_rayalucaria` points to the new commit.
