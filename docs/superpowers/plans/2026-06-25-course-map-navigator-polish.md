# Course Map Navigator Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a denser, more controllable course-map navigator with desktop section controls and mobile drawer behavior while preserving the current static renderer rules.

**Architecture:** Keep the feature inside the existing Glintstone shell. `builder.py` emits static buttons and attributes, `shell.py` owns volatile behavior and focus safety, `rendering.py` owns responsive layout and density, and tests prove no schema, storage, fetch, CDN, or learner-state behavior was introduced.

**Tech Stack:** Python static builder, generated HTML/CSS/vanilla JavaScript, Playwright e2e tests, pytest contract tests.

---

## File Structure

- Modify `docs/foundation/20_learning_renderer_contract.md` to describe mobile drawer and section-control shell semantics.
- Modify `packages/static/src/raya_static/builder.py` to render course-map control buttons and mobile drawer close affordance.
- Modify `packages/static/src/raya_static/shell.py` to implement volatile map section actions and mobile drawer open/close/focus behavior.
- Modify `packages/static/src/raya_static/rendering.py` to style compact map controls, mobile drawer/backdrop, and denser map rows.
- Modify `tests/contracts/test_static_builder.py` for generated HTML/script contract assertions.
- Modify `tests/e2e/test_preview_static_read_path.py` for desktop section controls and mobile drawer behavior.

## Task 1: Contract And Static Markup Tests

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify later: `docs/foundation/20_learning_renderer_contract.md`
- Modify later: `packages/static/src/raya_static/builder.py`
- Modify later: `packages/static/src/raya_static/shell.py`

- [ ] **Step 1: Write failing contract assertions**

In `test_build_writes_minimal_static_site`, after existing course map assertions, add:

```python
    assert 'data-raya-course-map-action="current"' in index_html
    assert 'data-raya-course-map-action="expand-all"' in index_html
    assert 'data-raya-course-map-action="less"' in index_html
    assert 'data-raya-course-map-close' in index_html
    assert 'data-raya-course-map-drawer-backdrop' in index_html
    assert "openCourseMapDrawer" in shell_js
    assert "closeCourseMapDrawer" in shell_js
    assert "expandCurrentCourseMapPath" in shell_js
    assert "expandAllCourseMapNodes" in shell_js
    assert "collapseCourseMapToCurrentPath" in shell_js
    for forbidden_shell_token in (
        "fetch(",
        "XMLHttpRequest",
        "localStorage",
        "sessionStorage",
    ):
        assert forbidden_shell_token not in shell_js
```

- [ ] **Step 2: Run contract test to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_minimal_static_site -q
```

Expected: FAIL because the new static controls and shell functions do not exist yet.

- [ ] **Step 3: Update foundation contract**

In `docs/foundation/20_learning_renderer_contract.md`, extend the Course Shell paragraph so it states that the course map may expose volatile section controls (`Current`, `All`, `Less`) and a mobile drawer opened from the command bar. Make clear this is non-persistent, article-first, and not learner state.

- [ ] **Step 4: Render static controls**

In `packages/static/src/raya_static/builder.py`, inside `_render_course_map`, insert the controls after the workspace links and before the filter:

```python
            '<div class="raya-course-map-actions" aria-label="Course map section controls">',
            '<button type="button" data-raya-course-map-action="current">Current</button>',
            '<button type="button" data-raya-course-map-action="expand-all">All</button>',
            '<button type="button" data-raya-course-map-action="less">Less</button>',
            "</div>",
```

Add a mobile close button inside the course-map header:

```python
            '<button class="raya-course-map-close" type="button" '
            'data-raya-course-map-close aria-label="Close course map">Close</button>',
```

Add a backdrop sibling near the course map:

```python
            '<div class="raya-course-map-drawer-backdrop" '
            'data-raya-course-map-drawer-backdrop hidden></div>',
```

- [ ] **Step 5: Add shell function stubs and wiring**

In `packages/static/src/raya_static/shell.py`, define the named functions and hook buttons. The first green implementation may call existing primitives:

```javascript
  function expandCurrentCourseMapPath() {
    orientCourseMapToCurrentPage({ force: true });
  }

  function expandAllCourseMapNodes() {
    mapNodeToggles.forEach((button) => {
      const node = button.closest("[data-raya-map-node]");
      if (node) setMapNodeExpanded(node, true);
    });
  }

  function collapseCourseMapToCurrentPath() {
    mapNodeToggles.forEach((button) => {
      const node = button.closest("[data-raya-map-node]");
      if (!node) return;
      const hasCurrent = Boolean(node.querySelector('a[aria-current="page"]'));
      setMapNodeExpanded(node, hasCurrent);
    });
    orientCourseMapToCurrentPage({ force: true });
  }

  function openCourseMapDrawer() {
    setExpanded(true);
  }

  function closeCourseMapDrawer() {
    setExpanded(false);
  }
```

Wire `[data-raya-course-map-action]`, `[data-raya-course-map-close]`, and `[data-raya-course-map-drawer-backdrop]`.

- [ ] **Step 6: Run contract test to verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_minimal_static_site -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add docs/foundation/20_learning_renderer_contract.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/shell.py tests/contracts/test_static_builder.py
git commit -m "Add course map navigator controls"
```

## Task 2: Desktop Section Control Behavior

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Write failing desktop e2e assertions**

In `test_preview_serves_static_site_from_artifact`, inside the desktop viewport block that already tests course map behavior, add:

```python
                        page.click('[data-raya-course-map-action="expand-all"]')
                        assert (
                            page.locator(
                                "[data-raya-map-node][data-raya-map-expanded='false']"
                            ).count()
                            == 0
                        )
                        page.click('[data-raya-course-map-action="less"]')
                        assert page.locator(
                            "#raya-course-map a[aria-current='page']"
                        ).is_visible()
                        collapsed_after_less = page.locator(
                            "[data-raya-map-node][data-raya-map-expanded='false']"
                        ).count()
                        assert collapsed_after_less > 0
                        page.fill("#raya-course-map-filter", "matrix")
                        page.click('[data-raya-course-map-action="current"]')
                        assert page.input_value("#raya-course-map-filter") == ""
                        assert page.locator(
                            "#raya-course-map a[aria-current='page']"
                        ).is_visible()
```

- [ ] **Step 2: Run e2e test to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_site_from_artifact -q
```

Expected: FAIL until the section controls update expansion state and clear filter as specified.

- [ ] **Step 3: Implement robust desktop actions**

In `shell.py`, make `expandCurrentCourseMapPath()` clear the filter, expand only current ancestors, and orient the map. Make `expandAllCourseMapNodes()` clear filter and expand every node. Make `collapseCourseMapToCurrentPath()` clear filter, expand current ancestors, and collapse non-current branches.

- [ ] **Step 4: Add compact control CSS**

In `rendering.py`, add:

```css
.raya-course-map-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin: 0.55rem 0;
}

.raya-course-map-actions button,
.raya-course-map-close {
  border: 1px solid var(--raya-border);
  border-radius: 0.35rem;
  background: var(--raya-surface-muted);
  color: var(--raya-text);
  font: inherit;
  font-size: 0.78rem;
  padding: 0.32rem 0.5rem;
}

.raya-course-map-node-row {
  gap: 0.28rem;
}
```

Use existing variable names from adjacent shell CSS if they differ.

- [ ] **Step 5: Run e2e test to verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_site_from_artifact -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add packages/static/src/raya_static/shell.py packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py
git commit -m "Polish desktop course map controls"
```

## Task 3: Mobile Drawer Behavior

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `packages/static/src/raya_static/shell.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Write failing mobile e2e assertions**

In the same e2e test, inside the mobile viewport block, add:

```python
                        map_button = page.locator("[data-raya-course-map-toggle]").first
                        map_button.click()
                        assert (
                            page.locator("html").get_attribute(
                                "data-raya-course-map-drawer"
                            )
                            == "open"
                        )
                        assert page.locator("#raya-course-map").is_visible()
                        assert (
                            page.locator("#raya-course-map-list").get_attribute(
                                "aria-hidden"
                            )
                            == "false"
                        )
                        page.keyboard.press("Escape")
                        assert (
                            page.locator("html").get_attribute(
                                "data-raya-course-map-drawer"
                            )
                            == "closed"
                        )
                        assert map_button.evaluate("node => document.activeElement === node")
                        assert (
                            page.locator("#raya-learning-rail-body").get_attribute(
                                "aria-hidden"
                            )
                            == "false"
                        )
                        assert not page.locator("#raya-learning-rail-body").evaluate(
                            "node => node.inert"
                        )
```

- [ ] **Step 2: Run e2e test to verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_site_from_artifact -q
```

Expected: FAIL until mobile drawer state and focus behavior exist.

- [ ] **Step 3: Implement drawer focus safety**

In `shell.py`, track `courseMapDrawerOpener`, set
`root.dataset.rayaCourseMapDrawer`, toggle backdrop `hidden`, set `map.inert`
when the drawer is closed on non-desktop widths, and return focus to the opener
after close. Escape should close the drawer before desktop map/rail behavior.

- [ ] **Step 4: Implement drawer CSS**

In `rendering.py`, add mobile rules:

```css
.raya-course-map-drawer-backdrop {
  display: none;
}

@media (max-width: 1279px) {
  html[data-raya-course-map-drawer="open"] .raya-course-map {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: 80;
    width: min(88vw, 24rem);
    max-height: 100vh;
    overflow: auto;
  }

  html[data-raya-course-map-drawer="open"] .raya-course-map-drawer-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 70;
    background: rgba(0, 0, 0, 0.42);
  }

  html[data-raya-course-map-drawer="closed"] .raya-course-map {
    position: static;
  }
}
```

Adjust selectors to match existing mobile layout without hiding the normal
article-first map when it is not in drawer mode.

- [ ] **Step 5: Run e2e test to verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_site_from_artifact -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add packages/static/src/raya_static/shell.py packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add mobile course map drawer"
```

## Task 4: Review And Verification

**Files:**
- No planned source edits unless review finds issues.

- [ ] **Step 1: Request code review**

Spawn one review subagent to inspect uncommitted or recently committed changes
for static constraints, accessibility, mobile drawer focus safety, and test
coverage.

- [ ] **Step 2: Fix review findings with TDD**

For each blocking review finding, add a failing focused test first, run it RED,
apply the minimal fix, and rerun GREEN.

- [ ] **Step 3: Run focused verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_build_writes_minimal_static_site tests/e2e/test_preview_static_read_path.py::test_preview_serves_static_site_from_artifact -q
./scripts/check-render-debug.sh
```

Expected: PASS.

- [ ] **Step 4: Run full gates sequentially**

Run:

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: both commands exit 0. Do not run them concurrently.

- [ ] **Step 5: Push and preview**

If any final fixes are committed, push:

```bash
git push origin new_rayalucaria
```

Start a fresh local preview:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya preview examples/courses/render-fixture --host 127.0.0.1 --port 0
```

Report the entrypoint and graph URL.

## Self-Review

- Spec coverage: desktop controls, mobile drawer, volatile state, accessibility,
  CSS density, foundation update, tests, review, and verification all have
  tasks.
- Placeholder scan: no TODO/TBD placeholders remain.
- Type consistency: function names match the contract assertions:
  `openCourseMapDrawer`, `closeCourseMapDrawer`,
  `expandCurrentCourseMapPath`, `expandAllCourseMapNodes`, and
  `collapseCourseMapToCurrentPath`.
