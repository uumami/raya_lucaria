# Reader Rail Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the generated reader left and right rails so they match the approved compact preview direction and old-main UX strengths without carrying forward contaminated component structure.

**Architecture:** Keep the existing static renderer and shell hooks, but replace the rail-specific markup and CSS with one clean rail system. The left rail owns search, compact two-per-row command tiles, and course hierarchy; the right rail owns page-local context using the same visual grammar. JavaScript should remain mostly stable and only be touched for accessibility attributes or stale selector cleanup.

**Tech Stack:** Python 3.10, `packages/static` HTML string renderer, generated CSS in `rendering.py`, shell behavior in `shell.py`, pytest, Playwright/Chromium.

## Global Constraints

- `docs/foundation/` remains the highest source of truth.
- Reader pages must not render a reader top command bar.
- Do not restore Eleventy, Tailwind, Pagefind, CDN assets, old generated data shapes, or durable sidebar state.
- Keep stable hooks: `#raya-course-map`, `#raya-course-map-list`, `#raya-learning-rail`, `#raya-learning-rail-body`, `data-raya-course-map-toggle`, `data-raya-learning-rail-toggle`, drawer/backdrop hooks.
- Course-map branch expansion may use accepted course-scoped `sessionStorage`; other shell, rail, drawer, search, filter, and context state must not persist.
- Phone layouts keep the article first and open the course map as a modal drawer.

---

## File Structure

- Modify `packages/static/src/raya_static/builder.py`: rebuild rail HTML helpers while preserving IDs/data hooks.
- Modify `packages/static/src/raya_static/rendering.py`: replace contaminated rail CSS blocks with the approved rail visual system.
- Modify `packages/static/src/raya_static/shell.py` only if tests expose stale accessibility or focus behavior.
- Modify `tests/contracts/test_static_builder.py`: assert generated markup/CSS contracts.
- Modify `tests/e2e/test_preview_static_read_path.py`: assert Chromium geometry, collapse behavior, and no overlap.
- Keep `docs/superpowers/previews/reader-rails-preview.html` as visual reference only.

---

### Task 1: Lock The Rail Markup Contract

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Later consumes: generated HTML from `build_course`
- Produces: contract assertions for the rebuilt rail structure

- [ ] **Step 1: Add failing contract assertions**

In the existing reader-shell contract test near the assertions for `raya-course-map-tools`, add exact checks:

```python
assert '<section class="raya-course-rail-tools" aria-label="Course tools"' in html
assert 'class="raya-course-rail-search"' in html
assert 'class="raya-course-rail-command raya-command-graph"' in html
assert 'class="raya-course-rail-command raya-command-practice"' in html
assert 'class="raya-course-rail-command raya-command-tasks"' in html
assert 'class="raya-course-rail-command raya-command-schedule"' in html
assert 'class="raya-course-rail-command raya-text-size-toggle"' in html
assert 'class="raya-course-rail-command raya-font-toggle"' in html
assert 'class="raya-course-rail-command raya-command-context"' in html
assert 'class="raya-course-map-tool-grid"' not in html
assert '<p class="raya-course-map-tools-label">Course Tools</p>' not in html
```

- [ ] **Step 2: Run the focused contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k "reader_shell or course_map"
```

Expected: FAIL because production still emits the old `raya-course-map-tool-grid` structure.

- [ ] **Step 3: Rebuild course rail tool markup**

In `packages/static/src/raya_static/builder.py`, replace `_render_course_map_tools` with a structure equivalent to:

```python
def _render_course_map_tools(
    *,
    search_href: str,
    graph_href: str,
    practice_href: str,
    tasks_href: str,
    schedule_href: str,
    graph_label: str,
    practice_label: str,
    tasks_label: str,
    schedule_label: str,
) -> str:
    return "\n".join(
        [
            '<section class="raya-course-rail-tools" aria-label="Course tools" data-raya-course-map-tools>',
            _render_command_search_form(search_href).replace(
                'class="raya-command-search-form"',
                'class="raya-course-rail-search raya-command-search-form"',
            ),
            '<div class="raya-course-rail-command-list" role="group" aria-label="Course workspaces">',
            _render_compact_command_link(
                class_name="raya-course-rail-command raya-command-search",
                href=search_href,
                aria_label="Open course search",
                icon="search",
                label="Search",
                tooltip="Open course search",
            ),
            _render_compact_command_link(
                class_name="raya-course-rail-command raya-command-graph",
                href=graph_href,
                aria_label=graph_label,
                icon="graph",
                label="Graph",
                tooltip=graph_label,
            ),
            _render_compact_command_link(
                class_name="raya-course-rail-command raya-command-practice",
                href=practice_href,
                aria_label=practice_label,
                icon="practice",
                label="Practice",
                tooltip=practice_label,
            ),
            _render_compact_command_link(
                class_name="raya-course-rail-command raya-command-tasks",
                href=tasks_href,
                aria_label=tasks_label,
                icon="tasks",
                label="Tasks",
                tooltip=tasks_label,
            ),
            _render_compact_command_link(
                class_name="raya-course-rail-command raya-command-schedule",
                href=schedule_href,
                aria_label=schedule_label,
                icon="schedule",
                label="Schedule",
                tooltip=schedule_label,
            ),
            _render_command_button(
                class_name="raya-course-rail-command raya-command-context",
                aria_label="Hide learning context",
                icon="context",
                label="Context",
                extra_attrs=" data-raya-learning-rail-toggle aria-controls=\"raya-learning-rail-body\" aria-expanded=\"true\"",
            ),
            _render_command_button(
                class_name="raya-course-rail-command raya-text-size-toggle",
                aria_label="Text size: normal",
                icon="text-size",
                label="Text size",
                aria_pressed="false",
            ),
            _render_command_button(
                class_name="raya-course-rail-command raya-font-toggle",
                aria_label="Toggle OpenDyslexic font",
                icon="font",
                label="OpenDyslexic",
                aria_pressed="false",
            ),
            "</div>",
            "</section>",
        ]
    )
```

Keep `data-raya-course-map-tools` so existing shell tests and hidden-state logic still have a stable hook.

- [ ] **Step 4: Run contract test again**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k "reader_shell or course_map"
```

Expected: PASS for the new markup assertions, or fail only on CSS/layout assertions addressed in Task 2.

---

### Task 2: Replace Rail CSS With One Clean Visual System

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `tests/contracts/test_static_builder.py`
- Produces: full-height narrow rails, dense two-per-row command tiles, scrollable hierarchy, matched right rail

- [ ] **Step 1: Add failing CSS contract checks**

In `tests/contracts/test_static_builder.py`, near existing CSS checks for `.raya-course-map`, add:

```python
assert ".raya-course-rail-tools" in css_text
assert ".raya-course-rail-command-list" in css_text
assert ".raya-course-rail-command" in css_text
assert ".raya-course-map-tool-grid" not in css_text
assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in css_text
assert "grid-template-columns: repeat(3" not in css_text
assert "height: calc(100vh - 1.5rem)" in css_text
assert ".raya-learning-rail" in css_text
```

- [ ] **Step 2: Run CSS contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k "rich_css or reader_shell or course_map"
```

Expected: FAIL because old grid CSS still exists.

- [ ] **Step 3: Replace old rail tool CSS**

In `packages/static/src/raya_static/rendering.py`, remove CSS rules that target `.raya-course-map-tool-grid` and replace them with:

```css
.raya-course-rail-tools {
  border-bottom: 1px solid color-mix(in srgb, var(--raya-color-border) 72%, transparent);
  display: grid;
  gap: 0.3125rem;
  padding: 0.5rem 0.75rem;
}
.raya-course-rail-search.raya-command-search-form {
  display: flex;
  gap: 0.375rem;
  width: 100%;
}
.raya-course-rail-search .raya-command-search-input,
.raya-course-rail-search .raya-command-search-submit {
  min-height: 2.25rem;
}
.raya-course-rail-command-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.3125rem;
}
.raya-course-rail-command {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-surface) 94%, var(--raya-color-page));
  border: 1px solid color-mix(in srgb, var(--raya-color-border) 84%, transparent);
  border-radius: 0.4375rem;
  color: var(--raya-color-text);
  display: inline-flex;
  gap: 0.375rem;
  justify-content: flex-start;
  min-height: 1.75rem;
  padding: 0.25rem 0.4375rem;
  text-align: left;
  width: 100%;
}
.raya-course-rail-command .raya-command-icon {
  flex: 0 0 auto;
  height: 0.9375rem;
  width: 0.9375rem;
}
.raya-course-rail-command .raya-command-label {
  display: inline;
  font-size: 0.75rem;
  font-weight: 700;
  line-height: 1.2;
}
```

Use existing command color classes (`.raya-command-graph`, `.raya-command-practice`, etc.) for semantic icon colors. Do not introduce a single-hue palette.

- [ ] **Step 4: Rebuild medium-width and collapsed CSS**

Still in `rendering.py`, update the medium-width rules so expanded rails use fixed side positions and collapsed rails only expose edge openers:

```css
@media (min-width: 640px) and (max-width: 1279px) {
  .raya-course-map {
    height: calc(100vh - 1.5rem);
    width: min(16rem, calc(100vw - 3rem));
  }
  .raya-learning-rail {
    height: calc(100vh - 1.5rem);
    width: min(16rem, calc(100vw - 3rem));
  }
  html[data-raya-course-map="collapsed"] .raya-course-map,
  .raya-course-map[data-raya-course-map="collapsed"],
  html[data-raya-learning-rail="collapsed"] .raya-learning-rail,
  .raya-learning-rail[data-raya-learning-rail="collapsed"] {
    background: transparent;
    border: 0;
    box-shadow: none;
    width: 2.75rem;
  }
}
```

Keep existing inert/hidden selectors for collapsed content.

- [ ] **Step 5: Run CSS contract test again**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k "rich_css or reader_shell or course_map"
```

Expected: PASS.

---

### Task 3: Add Browser Geometry Tests For The Approved Viewports

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Produces: Chromium evidence that rails render correctly at desktop and screenshot-width layouts

- [ ] **Step 1: Add failing geometry assertions**

Add or extend the reader shell e2e test with:

```python
for viewport in [
    {"width": 1440, "height": 900},
    {"width": 894, "height": 670},
]:
    page.set_viewport_size(viewport)
    page.goto(f"{base_url}/4_reader_ux/")
    map_box = page.locator("#raya-course-map").bounding_box()
    article_box = page.locator("#raya-article").bounding_box()
    rail_box = page.locator("#raya-learning-rail").bounding_box()
    assert map_box is not None
    assert article_box is not None
    assert rail_box is not None
    assert map_box["x"] < article_box["x"]
    assert article_box["x"] + article_box["width"] <= rail_box["x"] + 1
    assert 188 <= map_box["width"] <= 290
    assert 188 <= rail_box["width"] <= 310
    assert page.locator(".raya-course-rail-search").is_visible()
    assert page.locator(".raya-course-rail-command").first.is_visible()
    assert page.locator("#raya-course-map-list").is_visible()
```

- [ ] **Step 2: Run the browser test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k "reader_shell"
```

Expected: FAIL until CSS and selectors match the new rail system.

- [ ] **Step 3: Adjust CSS only until geometry passes**

Modify only `packages/static/src/raya_static/rendering.py` unless the failure shows missing HTML classes from Task 1. Keep rail widths narrow enough to preserve article readability and wide enough to show labels.

- [ ] **Step 4: Run browser test again**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k "reader_shell"
```

Expected: PASS with no horizontal overflow.

---

### Task 4: Verify Collapse, Inertness, And Drawer Safety

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `packages/static/src/raya_static/shell.py` only if required
- Produces: accessible collapse behavior for cleaned rails

- [ ] **Step 1: Add collapse regression assertions**

Extend the same e2e area with:

```python
page.set_viewport_size({"width": 894, "height": 670})
page.goto(f"{base_url}/4_reader_ux/")
page.click("#raya-course-map .raya-course-map-toggle")
page.wait_for_function("document.documentElement.dataset.rayaCourseMap === 'collapsed'")
state = page.evaluate(
    """() => {
      const map = document.querySelector('#raya-course-map');
      const list = document.querySelector('#raya-course-map-list');
      const toggle = document.querySelector('#raya-course-map .raya-course-map-toggle');
      return {
        mapWidth: map.getBoundingClientRect().width,
        listHidden: list.getAttribute('aria-hidden'),
        listInert: list.inert,
        toggleVisible: getComputedStyle(toggle).display !== 'none',
        activeHiddenLinks: Array.from(map.querySelectorAll('a')).filter((link) => link.tabIndex >= 0).length,
      };
    }"""
)
assert state["mapWidth"] <= 56
assert state["listHidden"] == "true"
assert state["listInert"] is True
assert state["toggleVisible"] is True
assert state["activeHiddenLinks"] == 0
```

- [ ] **Step 2: Run collapse test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k "collapse and reader_shell"
```

Expected: FAIL if the cleanup leaves hidden controls tabbable.

- [ ] **Step 3: Fix shell accessibility only if needed**

If hidden links remain tabbable, update `packages/static/src/raya_static/shell.py` in the existing map collapse synchronization path so `#raya-course-map-list` has `aria-hidden="true"` and `inert = true` while collapsed, and restores both when expanded. Do the same for `#raya-learning-rail-body`.

- [ ] **Step 4: Run collapse test again**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k "collapse and reader_shell"
```

Expected: PASS.

---

### Task 5: Update Foundation And Role Guidance If Behavior Changes

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md` or nearest existing student role page if present
- Modify: `docs/guides/es/estudiantes/index.md` or nearest existing student role page if present
- Produces: docs aligned with the rebuilt rail behavior

- [ ] **Step 1: Check whether docs already match**

Run:

```bash
rg -n "top bar|Course Tools|course rail|learning rail|Course map|Context" docs/foundation/20_learning_renderer_contract.md docs/guides/en docs/guides/es
```

Expected: identify any stale top-bar or old tool-grid wording.

- [ ] **Step 2: Patch only stale guidance**

If stale wording exists, update it to say:

```markdown
Reader commands live in the left course rail. The rail starts with course search, then compact icon-labeled command rows, then the scrollable course map. The right learning rail is page-local context and can collapse into an edge opener on desktop and medium-width layouts.
```

Keep English and Spanish role pages separate. Technical identifiers remain in English.

- [ ] **Step 3: Run doc hygiene checks**

Run:

```bash
rg -n "reader top bar|top command bar|raya-course-map-tool-grid|Course Workspaces" docs/foundation docs/guides README.md AGENTS.md openspec/config.yaml
```

Expected: no stale reader-shell guidance unless explicitly historical and marked as such.

---

### Task 6: Final Verification And Screenshots

**Files:**
- No new production files expected
- May update local screenshot evidence only if useful; do not commit generated render-debug output

- [ ] **Step 1: Run focused verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py -k "reader_shell or course_map or rich_css"
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py -k "reader_shell"
```

Expected: PASS.

- [ ] **Step 2: Run render debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS; inspect generated screenshots if it fails.

- [ ] **Step 3: Run canonical gates sequentially**

Run:

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

Expected: PASS. Run sequentially, not concurrently.

- [ ] **Step 4: Commit**

Use a short imperative subject:

```bash
git add docs/superpowers/specs/2026-07-08-reader-rail-rebuild-design.md docs/superpowers/plans/2026-07-08-reader-rail-rebuild.md packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py packages/static/src/raya_static/shell.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py docs/foundation/20_learning_renderer_contract.md docs/guides/en docs/guides/es
git commit -m "Rebuild reader rails"
```

Only include files actually changed.

---

## Self-Review

- Spec coverage: tasks cover left rail search, command rows, hierarchy, right rail visual consistency, collapse, inertness, mobile/drawer safety, docs, and verification.
- Placeholder scan: no placeholder markers or open-ended steps.
- Interface consistency: stable IDs and data hooks match the existing shell contract and design spec.
