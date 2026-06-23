# Course Map Orientation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Auto-orient the expanded course map to the current page without persisting navigation state.

**Architecture:** Add a small helper in the existing static `shell.js` resource that checks the active course-map link against the course-map panel viewport and scrolls only that local region. Make the course-map panel a real bounded scroll region on desktop by opting it out of grid stretch sizing. Keep all data in generated HTML and local script state, with no storage writes beyond existing comfort preferences outside this shell.

**Tech Stack:** Python-generated static JavaScript resource, generated HTML from `packages/static`, pytest contract tests, Playwright static-read-path tests, EN/ES Markdown docs.

---

### Task 1: Contract Test For Shell Orientation

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Write the failing contract assertions**

In `test_static_build_writes_local_shell_resource`, add:

```python
assert "function orientCourseMapToCurrentPage" in script_text
assert "rayaCourseMapOriented" in script_text
assert "scrollIntoView" not in script_text
assert "glintstone-nav-expanded" not in script_text
assert ".raya-course-map {\\n  align-self: start;\\n  grid-area: course-map;\\n  max-height: calc(100vh - 6rem);\\n  overflow: auto;" in css_text
```

These assertions require an explicit current-page orientation helper, a real desktop scroll panel, and prevent the legacy persistence key from reappearing.

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_build_writes_local_shell_resource -q
```

Expected: FAIL because the orientation helper does not exist yet.

### Task 2: Browser Test For Current-Page Visibility

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Write the failing browser assertions**

In `test_render_fixture_course_map_hierarchy_filters_without_requests`, after loading `authoring-matrix/index.html` and clearing `requested_urls`, add:

```python
page.evaluate(
    """() => {
      const map = document.querySelector('.raya-course-map');
      const list = document.querySelector('#raya-course-map-list');
      const filter = document.querySelector('#raya-course-map-filter');
      if (!map || !list || !filter) {
        throw new Error('missing course map controls');
      }
      map.style.maxHeight = '5rem';
      map.style.overflow = 'auto';
      map.scrollTop = 0;
      delete map.dataset.rayaCourseMapOriented;
      filter.value = 'matrix';
      window.rayaOrientCourseMapToCurrentPageAutomatic?.();
      if (map.scrollTop !== 0) {
        throw new Error('filtered automatic orientation scrolled');
      }
      filter.value = '';
      window.rayaOrientCourseMapToCurrentPage?.();
    }"""
)
orientation = page.evaluate(
    """() => {
      const map = document.querySelector('.raya-course-map');
      const list = document.querySelector('#raya-course-map-list');
      const current = list?.querySelector('a[aria-current="page"]');
      if (!map || !list || !current) return null;
      const mapRect = map.getBoundingClientRect();
      const currentRect = current.getBoundingClientRect();
      return {
        oriented: map.dataset.rayaCourseMapOriented,
        scrollTop: map.scrollTop,
        currentTop: currentRect.top,
        currentBottom: currentRect.bottom,
        mapTop: mapRect.top,
        mapBottom: mapRect.bottom,
        localStorageKeys: Object.keys(localStorage),
        sessionStorageKeys: Object.keys(sessionStorage),
      };
    }"""
)
assert orientation is not None
assert orientation["oriented"] == "true"
assert orientation["scrollTop"] > 0
assert orientation["currentTop"] >= orientation["mapTop"]
assert orientation["currentBottom"] <= orientation["mapBottom"]
assert orientation["localStorageKeys"] == []
assert orientation["sessionStorageKeys"] == []
```

- [x] **Step 2: Verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_course_map_hierarchy_filters_without_requests -q
```

Expected: FAIL because `window.rayaOrientCourseMapToCurrentPage` is absent and the current page is not auto-oriented.

### Task 3: Shell Implementation

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `packages/static/src/raya_static/shell.py`

- [x] **Step 1: Make the desktop map panel scrollable**

In the `.raya-course-map` CSS rule, add:

```css
  align-self: start;
  max-height: calc(100vh - 6rem);
  overflow: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
```

This prevents grid stretch from defeating the viewport-bound map scroll region.

- [x] **Step 2: Add orientation helper**

Add this helper after `applyCourseMapFilter()`:

```javascript
  function orientCourseMapToCurrentPage(options = {}) {
    const mapList = map.querySelector("#raya-course-map-list");
    const currentLink = mapList
      ? mapList.querySelector('a[aria-current="page"]')
      : null;
    const scrollContainer = map;
    if (!mapList || !currentLink || !scrollContainer) {
      return false;
    }
    if (mapFilter && mapFilter.value && !options.force) {
      return false;
    }
    if (
      scrollContainer.dataset.rayaCourseMapOriented === "true" &&
      !options.force &&
      !options.repeat
    ) {
      return false;
    }
    const containerRect = scrollContainer.getBoundingClientRect();
    const linkRect = currentLink.getBoundingClientRect();
    const isVisible =
      linkRect.top >= containerRect.top && linkRect.bottom <= containerRect.bottom;
    if (!isVisible) {
      const offset =
        scrollContainer.scrollTop +
        linkRect.top -
        containerRect.top -
        scrollContainer.clientHeight / 2 +
        currentLink.offsetHeight / 2;
      scrollContainer.scrollTop = Math.max(0, offset);
    }
    scrollContainer.dataset.rayaCourseMapOriented = "true";
    return true;
  }

  window.rayaOrientCourseMapToCurrentPage = () =>
    orientCourseMapToCurrentPage({ force: true });
  window.rayaOrientCourseMapToCurrentPageAutomatic = () =>
    orientCourseMapToCurrentPage({ repeat: true });
```

- [x] **Step 3: Invoke orientation**

After `setExpanded(true);` and `setLearningRailExpanded(true);`, add:

```javascript
  window.requestAnimationFrame(() => orientCourseMapToCurrentPage());
```

Inside the map toggle click handler, after `setExpanded(...)`, add:

```javascript
      if (root.dataset.rayaCourseMap === "expanded") {
        window.requestAnimationFrame(() =>
          orientCourseMapToCurrentPage({ repeat: true })
        );
      }
```

Do not add storage reads or writes.

- [x] **Step 4: Verify focused GREEN**

Run:

```bash
git diff --check && UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_static_build_writes_local_shell_resource tests/e2e/test_preview_static_read_path.py::test_render_fixture_course_map_hierarchy_filters_without_requests -q
```

Expected: PASS.

### Task 4: Documentation

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] **Step 1: Document non-persistent orientation**

Document that the course map may auto-orient the current page into the visible map region, but does not store map state, filter text, progress, or recommendations.

- [x] **Step 2: Focused docs check**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate docs
```

Expected: PASS.

### Task 5: Review And Verification

**Files:**
- All files changed above.

- [x] **Step 1: Request review**

Dispatch a read-only reviewer focused on static boundaries, accessibility, no storage state, current-page visibility, and no external requests.

- [x] **Step 2: Run verification**

Run:

```bash
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

`./scripts/check.sh` and `./scripts/check-docker.sh` must be sequential.

- [ ] **Step 3: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-23-course-map-orientation-design.md docs/superpowers/plans/2026-06-23-course-map-orientation.md docs/foundation/20_learning_renderer_contract.md docs/guides/en/students/index.md docs/guides/en/agents/index.md docs/guides/es/estudiantes/index.md docs/guides/es/agentes/index.md packages/static/src/raya_static/rendering.py packages/static/src/raya_static/shell.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add course map current-page orientation"
git push origin new_rayalucaria
```
