# Active Key Object Tracking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Highlight the currently visible numbered object or proof in the existing right-rail `Key objects` list.

**Architecture:** Add explicit `data-raya-key-object-link` attributes to generated key-object links, then extend the existing local shell script to observe public object sections and toggle `aria-current="location"` on the matching link. Keep heading current-section tracking separate.

**Tech Stack:** Python static builder, generated HTML/CSS, local vanilla JavaScript, pytest, Playwright.

---

### Task 1: Static Markup And CSS Test

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Add failing contract assertions**

In `test_render_fixture_builds_rich_static_pages`, after the existing right-rail key-object assertions, assert:

```python
assert 'data-raya-key-object-link="raya-object-orthogonal-definition"' in reader_html
assert 'data-raya-key-object-link="raya-proof-proof-orthogonal-proposition"' in reader_html
```

In `test_build_writes_local_visual_graph_surface` or the renderer stylesheet assertions near graph/rail CSS checks, assert:

```python
assert ".raya-page-toc-object-item a[aria-current=\"location\"]" in stylesheet
```

- [x] **Step 2: Run RED contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages
```

Expected: FAIL because key-object links do not yet have `data-raya-key-object-link`.

### Task 2: Browser Scroll Tracking Test

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add failing e2e test**

Create `test_render_fixture_key_object_links_track_visible_object` near other reader-rail tests. It should:

```python
page.goto(f"{handle.base_url}/reader-ux/index.html", wait_until="networkidle")
page.locator("#raya-object-orthogonal-definition").scroll_into_view_if_needed()
page.wait_for_function(
    """() => document
      .querySelector('[data-raya-key-object-link="raya-object-orthogonal-definition"]')
      ?.getAttribute('aria-current') === 'location'"""
)
state = page.evaluate("""() => ({
  activeObjectHref: document
    .querySelector('.raya-page-toc-objects a[aria-current="location"]')
    ?.getAttribute('href') || '',
  activeObjectText: document
    .querySelector('.raya-page-toc-objects a[aria-current="location"]')
    ?.textContent.trim() || '',
  currentSectionHref: document
    .querySelector('.raya-current-section-link')
    ?.getAttribute('href') || '',
  storage: [Object.keys(localStorage), Object.keys(sessionStorage)],
  overflow: Math.ceil(document.documentElement.scrollWidth - window.innerWidth),
})""")
```

Expected assertions:

```python
assert state["activeObjectHref"] == "#raya-object-orthogonal-definition"
assert state["activeObjectText"].startswith("Definition 4.1")
assert state["currentSectionHref"] != "#raya-object-orthogonal-definition"
assert state["storage"] == [[], []]
assert state["overflow"] <= 1
```

- [x] **Step 2: Run RED e2e test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_key_object_links_track_visible_object
```

Expected: FAIL because object links are not active-tracked yet.

### Task 3: Builder Markup

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`

- [x] **Step 1: Add object-link data attributes**

In `_render_page_contents_object_links`, change each key-object anchor from:

```python
f'<a href="#{html.escape(anchor, quote=True)}">'
```

to:

```python
escaped_anchor = html.escape(anchor, quote=True)
f'<a href="#{escaped_anchor}" data-raya-key-object-link="{escaped_anchor}">'
```

- [x] **Step 2: Run contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages
```

Expected: contract assertions for link attributes pass after CSS is added in Task 5.

### Task 4: Shell Active Object Tracking

**Files:**
- Modify: `packages/static/src/raya_static/shell.py`

- [x] **Step 1: Select object links and target sections**

Near the current-section selectors, add:

```javascript
const keyObjectLinks = Array.from(document.querySelectorAll("[data-raya-key-object-link]"));
const keyObjectTargets = keyObjectLinks
  .map((link) => document.getElementById(link.getAttribute("data-raya-key-object-link") || ""))
  .filter(Boolean);
```

- [x] **Step 2: Add a sync function**

Add:

```javascript
function setActiveKeyObject(id) {
  keyObjectLinks.forEach((link) => {
    const isActive = link.getAttribute("data-raya-key-object-link") === id;
    if (isActive) {
      link.setAttribute("aria-current", "location");
    } else {
      link.removeAttribute("aria-current");
    }
  });
}
```

- [x] **Step 3: Observe public object targets**

Use a separate `IntersectionObserver` from heading tracking:

```javascript
if (keyObjectLinks.length && keyObjectTargets.length && "IntersectionObserver" in window) {
  const activeObjects = new Set();
  const objectObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) activeObjects.add(entry.target.id);
      else activeObjects.delete(entry.target.id);
    });
    const orderedActive = keyObjectTargets.find((target) => activeObjects.has(target.id));
    setActiveKeyObject(orderedActive ? orderedActive.id : "");
  }, { rootMargin: "-20% 0px -55% 0px", threshold: 0 });
  keyObjectTargets.forEach((target) => objectObserver.observe(target));
}
```

- [x] **Step 4: Run e2e test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_key_object_links_track_visible_object
```

Expected: PASS after CSS and markup are present.

### Task 5: Active Link Styles

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Add active object style**

Near `.raya-page-toc-object-item a`, add:

```css
.raya-page-toc-object-item a[aria-current="location"] {
  background: color-mix(in srgb, var(--raya-color-accent) 12%, transparent);
  border-color: var(--raya-color-accent);
  color: var(--raya-color-text);
}
```

- [x] **Step 2: Run focused tests together**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages tests/e2e/test_preview_static_read_path.py::test_render_fixture_key_object_links_track_visible_object
```

Expected: PASS.

### Task 6: Verification, Review, Commit, Push

**Files:**
- No additional source files expected.

- [x] **Step 1: Run build**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture
```

Expected: exit 0.

- [x] **Step 2: Run render-debug**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: exit 0.

- [x] **Step 3: Request independent review**

Ask a reviewer to inspect object tracking for accessibility, no storage, no current-section regression, and no private/source data exposure.

- [x] **Step 4: Commit and push**

Run:

```bash
git add docs/superpowers/specs/2026-06-27-active-key-object-tracking-design.md docs/superpowers/plans/2026-06-27-active-key-object-tracking.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/shell.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Track active key objects in reader rail"
git push origin new_rayalucaria
```
