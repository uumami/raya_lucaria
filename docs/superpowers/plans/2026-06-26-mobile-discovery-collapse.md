# Mobile Discovery Collapse Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable the existing Search, Practice, Tasks, and Schedule panel collapse affordance on narrow screens so students can reveal results faster on mobile.

**Architecture:** Reuse the existing `discovery.js` panel state functions at every viewport width. Remove the mobile-only forced expansion behavior and let shared `aria-hidden` CSS hide collapsed bodies; keep mobile headings horizontal and panels single-column.

**Tech Stack:** Python-generated JavaScript/CSS resources, Playwright/Chromium e2e tests, pytest through `uv`.

---

### Task 1: Mobile Collapse RED Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Replace the current mobile no-collapse assertion**

In `test_preview_serves_local_course_search_surface`, replace the mobile block
that expects `data-raya-discovery-controls-state == "expanded"` after a click
with assertions that mobile controls collapse:

```python
mobile_storage_before = page.evaluate(
    "() => [Object.keys(localStorage), Object.keys(sessionStorage)]"
)
mobile_controls_toggle.click()
page.wait_for_function(
    """() => document
      .querySelector('[data-raya-search-page]')
      ?.getAttribute('data-raya-discovery-controls-state') === 'collapsed'"""
)
assert mobile_controls_toggle.get_attribute("aria-expanded") == "false"
assert (
    page.locator('[data-raya-discovery-panel-body="controls"]')
    .get_attribute("aria-hidden")
    == "true"
)
assert page.locator("#raya-search-input").get_attribute("tabindex") == "-1"
assert page.locator(
    '[data-raya-discovery-panel-rail-summary="controls"]'
).is_visible()
assert (
    page.evaluate("() => [Object.keys(localStorage), Object.keys(sessionStorage)]")
    == mobile_storage_before
)
```

- [ ] **Step 2: Run the focused browser test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_course_search_surface -q
```

Expected: FAIL because the current script restores small viewport panels to
expanded.

### Task 2: Static Script Collapse Behavior

**Files:**
- Modify: `packages/static/src/raya_static/discovery.py`

- [ ] **Step 1: Remove the viewport guard from toggle clicks**

Change the click listener so it always computes the current state and toggles:

```javascript
button.addEventListener("click", () => {
  const expanded = root.getAttribute(stateAttribute(panelName)) !== "collapsed";
  setPanelState(root, panelName, !expanded);
});
```

- [ ] **Step 2: Remove forced small-viewport expansion**

Delete `collapseMedia`, `restoreSmallViewportPanels`, and the media listener.
Do not add storage, fetch, or new dependencies.

### Task 3: Mobile CSS Hidden Bodies

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Let `aria-hidden="true"` hide panel bodies on mobile**

Remove this rule from the `@media (max-width: 1279px)` block:

```css
.raya-discovery-panel-body[aria-hidden="true"] {
  display: block;
}
```

Keep the rules that make mobile collapsed panels `display: block`, heading
writing mode horizontal, and panel headers row-oriented.

### Task 4: GREEN Verification

**Files:**
- Verify: `tests/e2e/test_preview_static_read_path.py`
- Verify: `packages/static/src/raya_static/discovery.py`
- Verify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Run focused browser tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_preview_serves_local_course_search_surface tests/e2e/test_preview_static_read_path.py::test_discovery_workspace_guides_are_visible_without_overflow -q
```

Expected: PASS.

- [ ] **Step 2: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no output and exit 0.

### Task 5: Review, Commit, Push

**Files:**
- Commit all files from this plan.

- [ ] **Step 1: Request independent review**

Ask a reviewer to inspect mobile collapse behavior, static constraints,
accessibility state, and whether desktop behavior is preserved.

- [ ] **Step 2: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-26-mobile-discovery-collapse-design.md docs/superpowers/plans/2026-06-26-mobile-discovery-collapse.md tests/e2e/test_preview_static_read_path.py packages/static/src/raya_static/discovery.py packages/static/src/raya_static/rendering.py
git commit -m "Enable mobile discovery panel collapse"
git push origin new_rayalucaria
```

