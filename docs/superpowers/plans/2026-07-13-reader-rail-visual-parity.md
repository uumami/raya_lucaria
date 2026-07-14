# Reader Rail Visual Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the left course rail mirror the right learning rail's expanded header, outer geometry, collapsed edge opener, and accessibility state without changing course-map destinations or phone drawer behavior.

**Architecture:** Keep the map and context bodies semantically separate, but give them one outer rail grammar. Generated map markup gains a dedicated body plus distinct collapse and expand controls; `shell.py` synchronizes that body and deterministic focus targets, while `rendering.py` owns shared geometry at the existing phone, compact-structural, medium, and desktop bands.

**Tech Stack:** Python 3.10, generated static HTML/CSS/JavaScript, pytest, Playwright Chromium, Docker Compose, GitHub Actions and GitHub Pages.

## Global Constraints

- `docs/foundation/` remains the highest source of truth; change `20_learning_renderer_contract.md` before package behavior and keep affected English/Spanish role guides aligned.
- Structural widths are `640px+`; compact structural is `640px-893px`, medium fixed-edge is `894px-1279px`, and desktop grid is `1280px+`.
- Expanded rail widths are `15.75rem` at `640px-893px` and `15rem` at `894px+`; simultaneously visible rails must differ by at most one CSS pixel.
- At `894px`, both expanded rails leave at least `23.75rem` for the article; at `1280px`, both expanded rails leave at least `42rem`.
- The structural map header shows `Course map` and `Hide map`; the body contains course search followed by exactly Search, Graph, Practice, Tasks, Schedule, Context, Text size, and OpenDyslexic in two columns.
- A collapsed structural map body is absent from layout, inert, `aria-hidden`, and untabbable; its separate `Map` opener has accessible name `Expand course map`, remains operable, and mirrors the right `Context` opener.
- Below `640px`, preserve the existing modal course-map drawer, backdrop, focus containment, Escape close path, background inertness, and volatile state.
- Preserve `raya:reader-shell:v1:<course_id>` and `raya:course-map-branches:v1:<course_id>` without adding storage keys, writes, or payload fields.
- Use no new dependency, external request, backend, framework, source schema, artifact payload, breakpoint, or transition duration.
- Write tests first, observe the intended failure, make the smallest implementation change, and commit only each task's allowlisted paths.

---

### Task 1: Align Foundation And Role Truth Surfaces

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md:23-35`
- Modify: `docs/guides/en/students/index.md:49-80`
- Modify: `docs/guides/es/estudiantes/index.md:50-88`
- Modify: `docs/guides/en/agents/index.md:142-181`
- Modify: `docs/guides/es/agentes/index.md:152-195`
- Test: `tests/contracts/test_documentation_surfaces.py`

**Interfaces:**
- Consumes: the approved design's structural header/body command boundary.
- Produces: exact foundation and bilingual role wording used by renderer contract tests and later implementation tasks.

- [ ] **Step 1: Add a failing truth-surface parity test**

Append this test to `tests/contracts/test_documentation_surfaces.py`:

```python
def test_reader_rail_visual_parity_truth_surfaces_agree() -> None:
    paths = {
        "foundation": ROOT / "docs/foundation/20_learning_renderer_contract.md",
        "student_en": ROOT / "docs/guides/en/students/index.md",
        "student_es": ROOT / "docs/guides/es/estudiantes/index.md",
        "agent_en": ROOT / "docs/guides/en/agents/index.md",
        "agent_es": ROOT / "docs/guides/es/agentes/index.md",
    }
    text = {name: path.read_text(encoding="utf-8") for name, path in paths.items()}

    for name in ("foundation", "student_en", "agent_en"):
        assert "Hide map" in text[name], name
        assert "Search, Graph, Practice, Tasks, Schedule, Context, Text size, and OpenDyslexic" in text[name], name
    for name in ("student_es", "agent_es"):
        assert "Hide map" in text[name], name
        assert "Search, Graph, Practice, Tasks, Schedule, Context, Text size y OpenDyslexic" in text[name], name

    assert "header Map action" in text["agent_en"]
    assert "accion Map del header" in text["agent_es"]
    assert "all nine actions as body tiles" not in text["foundation"]
```

- [ ] **Step 2: Run the test and verify the contract is red**

Run:

```bash
UV_PROJECT_ENVIRONMENT=/home/uumami/itam/raya_lucaria/.venv-local uv run pytest -q tests/contracts/test_documentation_surfaces.py::test_reader_rail_visual_parity_truth_surfaces_agree
```

Expected: FAIL because the current documents do not name `Hide map`, the header/body boundary, or the exact eight-command body.

- [ ] **Step 3: Update the foundation contract**

Replace the left-course-rail command sentence in `docs/foundation/20_learning_renderer_contract.md` with this text and make the corresponding table row use the same boundary:

```markdown
At structural reader widths, the left course rail header presents `Course map` and an explicit `Hide map` Map action. Its body contains course search, then exactly eight compact icon-labeled command tiles rendered two per row for Search, Graph, Practice, Tasks, Schedule, Context, Text size, and OpenDyslexic, followed by structural page position, the locally filterable hierarchical map, and its scrollable course tree. The header Map action and eight body commands preserve the existing nine reader actions without duplicating Map inside the body.
```

Keep the existing storage, phone drawer, article-primary, and collapsed accessibility paragraphs unchanged.

- [ ] **Step 4: Update the English student and agent guides**

Use this English student wording in the shell overview and remove contradictory claims that all commands are body tiles:

```markdown
At structural widths, the rail header shows `Course map` with a `Hide map` Map action. The body starts with course search, then compact icon-labeled tiles arranged two per row for Search, Graph, Practice, Tasks, Schedule, Context, Text size, and OpenDyslexic, followed by page position and the course map. Collapsing the rail removes that body and leaves one floating Map opener that matches the right Context opener.
```

Use this English agent wording in the shell verification section:

```markdown
Verify the structural `Hide map` header Map action separately from the eight reader commands under `[data-raya-course-map-tools]`. Verify `.raya-course-map-body` owns search, the ordered Search, Graph, Practice, Tasks, Schedule, Context, Text size, and OpenDyslexic command tiles, position, filter, and tree, while `[data-raya-course-map-expand]` remains outside that hidden/inert body.
```

- [ ] **Step 5: Update the Spanish student and agent guides**

Use these equivalent Spanish paragraphs:

```markdown
En anchos estructurales, el header del riel muestra `Course map` con una accion Map `Hide map`. El body empieza con course search, luego mosaicos compactos con icono y label acomodados dos por fila para Search, Graph, Practice, Tasks, Schedule, Context, Text size y OpenDyslexic, seguidos por la posicion de pagina y el mapa del curso. Al colapsar el riel, ese body desaparece y queda un solo opener flotante Map que corresponde al opener Context de la derecha.

Verifica la accion Map `Hide map` del header estructural por separado de los ocho comandos lectores bajo `[data-raya-course-map-tools]`. Verifica que `.raya-course-map-body` contenga search, los mosaicos ordenados Search, Graph, Practice, Tasks, Schedule, Context, Text size y OpenDyslexic, posicion, filtro y arbol, mientras `[data-raya-course-map-expand]` permanece fuera de ese body oculto e inerte.
```

- [ ] **Step 6: Run the focused and renderable-doc contract tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=/home/uumami/itam/raya_lucaria/.venv-local uv run pytest -q \
  tests/contracts/test_documentation_surfaces.py::test_reader_rail_visual_parity_truth_surfaces_agree \
  tests/contracts/test_documentation_surfaces.py::test_current_documentation_tree_is_a_renderable_docs_course
```

Expected: `2 passed`.

- [ ] **Step 7: Commit the truth-surface change**

```bash
git add -- \
  docs/foundation/20_learning_renderer_contract.md \
  docs/guides/en/students/index.md \
  docs/guides/es/estudiantes/index.md \
  docs/guides/en/agents/index.md \
  docs/guides/es/agentes/index.md \
  tests/contracts/test_documentation_surfaces.py
git diff --cached --check
git commit -m "Align reader rail parity contract"
```

### Task 2: Generate A Mirrored Map Rail Structure

**Files:**
- Modify: `packages/static/src/raya_static/builder.py:1894-1919,2110-2165`
- Test: `tests/contracts/test_static_builder.py:4980-5055,5532-5605`

**Interfaces:**
- Consumes: `data-raya-course-map-toggle`, `#raya-course-map`, and the ordered eight-command body already generated by `_render_course_map_tools`.
- Produces: `#raya-course-map-body`, `[data-raya-course-map-collapse]`, and `[data-raya-course-map-expand]` for Tasks 3-5.

- [ ] **Step 1: Add failing generated-markup assertions**

Add these assertions to `test_static_builder_renders_collapsible_shell_controls_and_page_position` after the `#raya-course-map` assertions:

```python
    assert (
        '<button class="raya-course-map-collapse" type="button" '
        'data-raya-course-map-toggle data-raya-course-map-collapse '
        'aria-controls="raya-course-map-body" aria-expanded="true" '
        'aria-label="Hide course map">Hide map</button>'
    ) in html
    assert (
        '<div id="raya-course-map-body" class="raya-course-map-body" '
        'aria-hidden="false">'
    ) in html
    assert (
        '<button class="raya-course-map-expand" type="button" '
        'data-raya-course-map-toggle data-raya-course-map-expand '
        'aria-controls="raya-course-map-body" aria-expanded="true" '
        'aria-label="Expand course map">Map</button>'
    ) in html

    header_index = html.index('<div class="raya-course-map-header">')
    body_index = html.index('<div id="raya-course-map-body"')
    expand_index = html.index('<button class="raya-course-map-expand"')
    assert header_index < body_index < expand_index
    body_html = html[body_index:expand_index]
    assert body_html.count('class="raya-course-rail-command ') == 8
    assert body_html.index('class="raya-course-rail-search') < body_html.index(
        'class="raya-course-rail-command-list'
    )
    assert 'data-raya-course-map-collapse' not in body_html
    assert 'data-raya-course-map-expand' not in body_html
```

Update the old assertions for `.raya-course-map-toggle` / `Map` to expect the two dedicated controls above.

- [ ] **Step 2: Run the builder test and verify it fails for the new structure**

Run:

```bash
UV_PROJECT_ENVIRONMENT=/home/uumami/itam/raya_lucaria/.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_static_builder_renders_collapsible_shell_controls_and_page_position
```

Expected: FAIL because the current builder has one header toggle and no map-body wrapper or separate opener.

- [ ] **Step 3: Extend the map-toggle renderer with explicit control ownership**

Change `_render_course_map_toggle` to accept exact control and marker attributes:

```python
def _render_course_map_toggle(
    label: str = "Course map",
    expanded: bool = True,
    *,
    class_name: str = "raya-course-map-toggle",
    aria_label: str | None = None,
    icon: str | None = None,
    controls: str = "raya-course-map",
    marker: str = "",
) -> str:
    aria_expanded = "true" if expanded else "false"
    aria_label_attr = (
        f' aria-label="{html.escape(aria_label, quote=True)}"' if aria_label else ""
    )
    marker_attr = f" {marker}" if marker else ""
    label_markup = html.escape(label)
    if icon is not None:
        label_markup = (
            f"{_command_icon(icon)}"
            f'<span class="raya-command-label">{html.escape(label)}</span>'
        )
    return (
        f'<button class="{html.escape(class_name, quote=True)}" type="button" '
        f"data-raya-course-map-toggle{marker_attr} "
        f'aria-controls="{html.escape(controls, quote=True)}" '
        f'aria-expanded="{aria_expanded}"{aria_label_attr}>'
        f"{label_markup}"
        "</button>"
    )
```

Existing mobile or command-bar callers keep the default `controls="raya-course-map"` and empty marker.

- [ ] **Step 4: Emit the header, body, and opener as siblings**

In `_render_course_map`, retain drawer chrome and the phone close button in `.raya-course-map-header`, then replace the header toggle and wrap the existing body content with this exact shape:

```python
            _render_course_map_toggle(
                "Hide map",
                class_name="raya-course-map-collapse",
                aria_label="Hide course map",
                controls="raya-course-map-body",
                marker="data-raya-course-map-collapse",
            ),
            "</div>",
            '<div id="raya-course-map-body" class="raya-course-map-body" aria-hidden="false">',
            tools_html,
            f'<p class="raya-page-position">{position}</p>' if position else "",
            '<label class="raya-course-map-filter-label" for="raya-course-map-filter">Filter map</label>',
            (
                '<input id="raya-course-map-filter" '
                'class="raya-course-map-filter" type="search" autocomplete="off" '
                "data-raya-course-map-filter>"
            ),
            '<p class="raya-map-filter-empty" data-raya-map-filter-empty hidden>No map matches.</p>',
            '<div class="raya-course-map-list" id="raya-course-map-list" aria-hidden="false">',
            "<ol>",
            "\n".join(nav_items),
            "</ol>",
            "</div>",
            (
                '<div class="raya-course-map-compact-preview" '
                'data-raya-course-map-compact-preview aria-hidden="true" hidden></div>'
            ),
            "</div>",
            _render_course_map_toggle(
                "Map",
                class_name="raya-course-map-expand",
                aria_label="Expand course map",
                controls="raya-course-map-body",
                marker="data-raya-course-map-expand",
            ),
```

- [ ] **Step 5: Run the static builder contract tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=/home/uumami/itam/raya_lucaria/.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py::test_reader_shell_uses_static_learning_shell \
  tests/contracts/test_static_builder.py::test_static_builder_renders_collapsible_shell_controls_and_page_position
```

Expected: `2 passed`.

- [ ] **Step 6: Commit the generated structure**

```bash
git add -- packages/static/src/raya_static/builder.py tests/contracts/test_static_builder.py
git diff --cached --check
git commit -m "Structure mirrored course map controls"
```

### Task 3: Synchronize Body Accessibility And Deterministic Focus

**Files:**
- Modify: `packages/static/src/raya_static/shell.py:21-52,97-143,462-505,1397-1431,1542-1560,1727-1741`
- Modify: `packages/static/src/raya_static/rendering.py:4059-4118,5219-5562,6660-6945`
- Test: `tests/e2e/test_preview_static_read_path.py:11674-11747,15334-15501,16047-16218`

**Interfaces:**
- Consumes: `#raya-course-map-body`, `[data-raya-course-map-collapse]`, and `[data-raya-course-map-expand]` from Task 2.
- Produces: one `setExpanded(bool, options)` path that synchronizes the body, both controls, prepaint hiding, session state, and focus.

- [ ] **Step 1: Make collapse accessibility assertions target the whole body**

Update `test_reader_shell_collapse_sets_inert_hidden_state_without_tabbable_links` to collapse with `[data-raya-course-map-collapse]` and assert:

```python
                    page.click("[data-raya-course-map-collapse]")
                    page.wait_for_function(
                        "() => document.documentElement.dataset.rayaCourseMap === 'collapsed'"
                    )
                    state = page.evaluate(
                        """() => {
                          const body = document.querySelector('#raya-course-map-body');
                          const collapse = document.querySelector('[data-raya-course-map-collapse]');
                          const expand = document.querySelector('[data-raya-course-map-expand]');
                          return {
                            bodyDisplay: getComputedStyle(body).display,
                            bodyHidden: body.getAttribute('aria-hidden'),
                            bodyInert: body.inert,
                            tabbableBodyControls: Array.from(body.querySelectorAll(
                              'a[href], button, input, [tabindex]'
                            )).filter((element) => element.tabIndex >= 0).length,
                            collapseVisible: collapse.checkVisibility(),
                            expandVisible: expand.checkVisibility(),
                            expandLabel: expand.getAttribute('aria-label'),
                            expandExpanded: expand.getAttribute('aria-expanded'),
                            activeIsExpand: document.activeElement === expand,
                          };
                        }"""
                    )
                    assert state == {
                        "bodyDisplay": "none",
                        "bodyHidden": "true",
                        "bodyInert": True,
                        "tabbableBodyControls": 0,
                        "collapseVisible": False,
                        "expandVisible": True,
                        "expandLabel": "Expand course map",
                        "expandExpanded": "false",
                        "activeIsExpand": True,
                    }
```

- [ ] **Step 2: Extend prepaint and breakpoint focus tests**

In `test_reader_shell_prepaint_restores_width_safe_state_before_deferred_shell`, replace the map visibility measurement with:

```javascript
mapVisible: document.querySelector('#raya-course-map-body').checkVisibility(),
mapBodyDisplay: getComputedStyle(
  document.querySelector('#raya-course-map-body')
).display,
```

Add `"mapBodyDisplay": "none"` to every prepaint-collapsed expected case and `"mapBodyDisplay": "flex"` to every expanded case.

In `test_reader_shell_breakpoint_reconciliation_preserves_visible_focus`, replace structural map focus targets with `[data-raya-course-map-expand]` when the next effective map state is collapsed and `[data-raya-course-map-collapse]` when it is expanded.

- [ ] **Step 3: Run the three tests and verify they fail for body ownership/focus**

Run:

```bash
UV_PROJECT_ENVIRONMENT=/home/uumami/itam/raya_lucaria/.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_collapse_sets_inert_hidden_state_without_tabbable_links \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_prepaint_restores_width_safe_state_before_deferred_shell \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_breakpoint_reconciliation_preserves_visible_focus
```

Expected: FAIL because shell state currently targets the list/subcontrols, a collapsed prepaint can expose the new body, and focus queries select the old generic toggle.

- [ ] **Step 4: Bind the shell to the body and dedicated controls**

At shell initialization add:

```javascript
  const mapBody = document.querySelector("#raya-course-map-body");
  const mapCollapseButton = document.querySelector("[data-raya-course-map-collapse]");
  const mapExpandButton = document.querySelector("[data-raya-course-map-expand]");
```

Require all three alongside `shell`, `map`, and `toggleButtons`. Replace `updateMapLinkTabOrder` internals with body-level synchronization while retaining desktop map tabindex behavior:

```javascript
  function updateMapLinkTabOrder(nextExpanded) {
    const hideBody = isStructuralRailShell() && !nextExpanded;
    mapBody.setAttribute("aria-hidden", hideBody ? "true" : "false");
    setElementInert(mapBody, hideBody);
    setFocusableDescendantsEnabled(mapBody, !hideBody);
    if (desktopMapQuery.matches) {
      map.removeAttribute("tabindex");
    } else {
      map.setAttribute("tabindex", "-1");
    }
  }

  function syncCourseMapToggleButtons(nextExpanded) {
    toggleButtons.forEach((button) => {
      button.setAttribute("aria-expanded", nextExpanded ? "true" : "false");
      if (button === mapCollapseButton) {
        button.setAttribute("aria-label", "Hide course map");
        button.textContent = "Hide map";
      } else if (button === mapExpandButton) {
        button.setAttribute("aria-label", "Expand course map");
        button.textContent = "Map";
      } else {
        button.setAttribute(
          "aria-label",
          nextExpanded ? "Collapse course map" : "Expand course map"
        );
      }
    });
  }
```

Call `syncCourseMapToggleButtons(nextExpanded)` from `setExpanded` after setting root/shell/map state.

- [ ] **Step 5: Use dedicated visible focus targets**

Add:

```javascript
  function courseMapFocusTarget(nextState) {
    if (!isStructuralRailShell()) {
      return mobileMapOpener || article;
    }
    return nextState === "collapsed"
      ? mapExpandButton || article
      : mapCollapseButton || article;
  }
```

Use it in `readerShellReconciliationFocusTarget`, the map-toggle click handler, and the Escape handler. For structural clicks, after `setExpanded(nextExpanded, { skipPersist: true })`, focus `courseMapFocusTarget(nextExpanded ? "expanded" : "collapsed")` when the clicked control is inside `#raya-course-map`. Escape from focused map content always focuses `mapExpandButton` after collapse.

- [ ] **Step 6: Add the CSS-first collapsed safety boundary**

Define the default opener state and structural collapsed boundary outside skin-specific rules:

```css
.raya-course-map-body {
  display: flex;
}
.raya-course-map-expand {
  display: none;
}

@media (min-width: 640px) {
  html[data-raya-course-map="collapsed"] .raya-course-map-header,
  html[data-raya-course-map="collapsed"] .raya-course-map-body,
  .raya-course-map[data-raya-course-map="collapsed"] .raya-course-map-header,
  .raya-course-map[data-raya-course-map="collapsed"] .raya-course-map-body {
    display: none;
  }
  html[data-raya-course-map="collapsed"] .raya-course-map-expand,
  .raya-course-map[data-raya-course-map="collapsed"] .raya-course-map-expand {
    display: inline-flex;
  }
}

@media (max-width: 639px) {
  .raya-course-map-expand,
  .raya-course-map-collapse {
    display: none;
  }
}
```

Remove any later selector that re-displays `.raya-course-map-header` or map-body descendants in collapsed structural state.

- [ ] **Step 7: Run focused state, storage, drawer, and focus tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=/home/uumami/itam/raya_lucaria/.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_collapse_sets_inert_hidden_state_without_tabbable_links \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_prepaint_restores_width_safe_state_before_deferred_shell \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_breakpoint_reconciliation_preserves_visible_focus \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_medium_actions_store_coordinated_pair \
  tests/e2e/test_preview_static_read_path.py::test_mobile_course_map_drawer_is_modal_and_volatile
```

Expected: `5 passed`.

- [ ] **Step 8: Commit the accessible state boundary**

```bash
git add -- \
  packages/static/src/raya_static/shell.py \
  packages/static/src/raya_static/rendering.py \
  tests/e2e/test_preview_static_read_path.py
git diff --cached --check
git commit -m "Synchronize course map body state"
```

### Task 4: Mirror Outer Rail Geometry And Controls

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py:3979-4287,5219-5578,6660-6950`
- Test: `tests/e2e/test_preview_static_read_path.py:17476-18115`

**Interfaces:**
- Consumes: dedicated controls/body and synchronized state from Tasks 2-3.
- Produces: equal expanded panel widths, shared header treatment, corresponding edge openers, and exact article minimums at existing breakpoints.

- [ ] **Step 1: Add a browser geometry helper and parity test**

Add `test_render_fixture_reader_rails_share_outer_geometry` beside the existing collapse/medium geometry tests. For viewports `640`, `893`, `894`, `1279`, `1280`, and `1440`, measure this state after opening each permitted rail:

```javascript
() => {
  const box = (selector) => {
    const element = document.querySelector(selector);
    const rect = element.getBoundingClientRect();
    return {
      left: Math.round(rect.left),
      right: Math.round(rect.right),
      top: Math.round(rect.top),
      width: Math.round(rect.width),
      height: Math.round(rect.height),
      visible: element.checkVisibility(),
    };
  };
  const style = (selector) => {
    const computed = getComputedStyle(document.querySelector(selector));
    return {
      backgroundColor: computed.backgroundColor,
      borderColor: computed.borderColor,
      borderRadius: computed.borderRadius,
      borderWidth: computed.borderWidth,
      boxShadow: computed.boxShadow,
    };
  };
  return {
    map: box('#raya-course-map'),
    rail: box('#raya-learning-rail'),
    mapStyle: style('#raya-course-map'),
    railStyle: style('#raya-learning-rail'),
    article: box('#raya-article'),
    mapHeader: box('.raya-course-map-header'),
    railHeader: box('.raya-learning-rail-header'),
    mapCollapseText: document.querySelector('[data-raya-course-map-collapse]')
      .textContent.trim(),
    railCollapseText: document.querySelector('[data-raya-learning-rail-collapse]')
      .textContent.trim(),
    overflow: Math.ceil(document.documentElement.scrollWidth - innerWidth),
  };
}
```

Assert:

```python
assert state["mapCollapseText"] == "Hide map"
assert state["railCollapseText"] == "Hide context"
assert abs(state["map"]["width"] - state["rail"]["width"]) <= 1
assert abs(state["mapHeader"]["height"] - state["railHeader"]["height"]) <= 1
assert state["mapStyle"] == state["railStyle"]
assert state["overflow"] <= 1
if width >= 894:
    assert state["map"]["width"] in range(239, 242)
if width == 894:
    assert state["article"]["width"] >= 380
if width == 1280:
    assert state["article"]["width"] >= 672
if width <= 893:
    assert state["map"]["width"] in range(251, 254)
```

At `640px-893px`, open and measure left and right separately because only one may remain expanded. Compare the two expanded measurements captured from separate fresh page states; compare simultaneously expanded panels only at `894px+`.

- [ ] **Step 2: Extend the collapsed-opener test to compare both edges**

Rename `test_render_fixture_collapsed_reader_rails_use_compact_horizontal_tabs` to `test_render_fixture_collapsed_reader_rails_use_mirrored_edge_openers`. Measure `[data-raya-course-map-expand]` and `[data-raya-learning-rail-expand]` after both collapse and assert equal width, height, top, surface color, border width, radius, shadow, and corresponding viewport-edge offsets within one pixel. Also assert both rail bodies are `display: none` and neither opener intersects `#raya-article`.

- [ ] **Step 3: Extend the existing exact-boundary test**

In `test_render_fixture_course_map_drawer_boundary_switches_to_inline_rails`, keep the existing `(639, 640, 730, 767, 768, 893, 894, 1279, 1280)` cases and add these fields to the evaluated state:

```javascript
mapBodyDisplay: getComputedStyle(
  document.querySelector('#raya-course-map-body')
).display,
mapCollapseVisible: document
  .querySelector('[data-raya-course-map-collapse]').checkVisibility(),
mapExpandVisible: document
  .querySelector('[data-raya-course-map-expand]').checkVisibility(),
```

Assert the exact boundary behavior:

```python
if width < 640:
    assert state["mapBodyDisplay"] == "flex"
    assert state["mapCollapseVisible"] is False
    assert state["mapExpandVisible"] is False
elif width < 894:
    assert state["mapBodyDisplay"] == "none"
    assert state["mapCollapseVisible"] is False
    assert state["mapExpandVisible"] is True
else:
    assert state["mapBodyDisplay"] == "flex"
    assert state["mapCollapseVisible"] is True
    assert state["mapExpandVisible"] is False
```

Retain the existing resize sequence across `639/640`, `893/894`, and `1279/1280`. Call this helper after each `set_viewport_size` / state wait:

```python
def assert_visible_focus_and_clear_openers(page) -> None:
    state = page.evaluate(
        """() => {
          const article = document.querySelector('#raya-article').getBoundingClientRect();
          const intersectsArticle = (selector) => {
            const element = document.querySelector(selector);
            if (!element.checkVisibility()) return false;
            const box = element.getBoundingClientRect();
            return !(
              box.right <= article.left || box.left >= article.right ||
              box.bottom <= article.top || box.top >= article.bottom
            );
          };
          return {
            activeVisible: document.activeElement.checkVisibility(),
            mapIntersects: intersectsArticle('[data-raya-course-map-expand]'),
            railIntersects: intersectsArticle('[data-raya-learning-rail-expand]'),
          };
        }"""
    )
    assert state == {
        "activeVisible": True,
        "mapIntersects": False,
        "railIntersects": False,
    }
```

- [ ] **Step 4: Run the geometry tests and verify they fail on current asymmetry**

Run:

```bash
UV_PROJECT_ENVIRONMENT=/home/uumami/itam/raya_lucaria/.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_rails_share_outer_geometry \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_collapsed_reader_rails_use_mirrored_edge_openers \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_medium_reader_rails_are_overlay_controls \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_course_map_drawer_boundary_switches_to_inline_rails
```

Expected: FAIL because desktop tracks differ, medium right padding/width differs, and the left collapsed control uses old map-only styling.

- [ ] **Step 5: Establish shared outer/header/control rules**

Replace separate outer header/control declarations with shared rules:

```css
.raya-course-map-header,
.raya-learning-rail-header {
  align-items: center;
  border-bottom: 1px solid var(--raya-color-border);
  display: flex;
  gap: 0.75rem;
  justify-content: space-between;
  margin-bottom: 0.25rem;
  padding-bottom: 0.75rem;
}
.raya-course-map-header .raya-region-title,
.raya-learning-rail-header .raya-region-title {
  margin-bottom: 0;
}
.raya-course-map-collapse,
.raya-course-map-expand,
.raya-learning-rail-collapse,
.raya-learning-rail-expand {
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  cursor: pointer;
  font: inherit;
  font-size: 0.8125rem;
  font-weight: 700;
  line-height: 1;
  padding: 0.45rem 0.65rem;
  white-space: nowrap;
}
.raya-course-map-collapse:focus-visible,
.raya-course-map-expand:focus-visible,
.raya-learning-rail-collapse:focus-visible,
.raya-learning-rail-expand:focus-visible {
  outline: 3px solid var(--raya-color-accent);
  outline-offset: 2px;
}
```

Keep drawer chrome selectors scoped to `max-width: 639px` so they do not alter structural header height.

- [ ] **Step 6: Make desktop tracks equal and reclaim them independently**

Use these `1280px+` layouts and remove the later `1400px` unequal-track override:

```css
@media (min-width: 1280px) {
  [data-raya-course-map="expanded"][data-raya-learning-rail="expanded"] .raya-learning-shell,
  .raya-learning-shell[data-raya-course-map="expanded"][data-raya-learning-rail="expanded"] {
    grid-template-areas: "course-map main-article learning-rail";
    grid-template-columns: 15rem minmax(42rem, 1fr) 15rem;
  }
  [data-raya-course-map="expanded"][data-raya-learning-rail="collapsed"] .raya-learning-shell,
  .raya-learning-shell[data-raya-course-map="expanded"][data-raya-learning-rail="collapsed"] {
    grid-template-areas: "course-map main-article";
    grid-template-columns: 15rem minmax(48rem, 1fr);
  }
  [data-raya-course-map="collapsed"][data-raya-learning-rail="expanded"] .raya-learning-shell,
  .raya-learning-shell[data-raya-course-map="collapsed"][data-raya-learning-rail="expanded"] {
    grid-template-areas: "main-article learning-rail";
    grid-template-columns: minmax(48rem, 1fr) 15rem;
  }
  [data-raya-course-map="collapsed"][data-raya-learning-rail="collapsed"] .raya-learning-shell,
  .raya-learning-shell[data-raya-course-map="collapsed"][data-raya-learning-rail="collapsed"] {
    grid-template-areas: "main-article";
    grid-template-columns: minmax(0, 1fr);
  }
}
```

- [ ] **Step 7: Make medium fixed panels and reserved padding equal**

Inside `640px-1279px`, set both panels and expanded padding to `15rem` / `16rem` including the one-rem gap. Add a later `640px-893px` override using `15.75rem` / `16.75rem`. Preserve the existing at-most-one-expanded state rule; do not change its persistence logic.

```css
@media (min-width: 640px) and (max-width: 1279px) {
  .raya-course-map,
  .raya-learning-rail {
    width: min(15rem, calc(100vw - 3rem));
  }
  html[data-raya-course-map="expanded"] .raya-learning-shell,
  .raya-learning-shell[data-raya-course-map="expanded"] {
    padding-left: calc(min(15rem, calc(100vw - 3rem)) + 1rem);
  }
  html[data-raya-learning-rail="expanded"] .raya-learning-shell,
  .raya-learning-shell[data-raya-learning-rail="expanded"] {
    padding-right: calc(min(15rem, calc(100vw - 3rem)) + 1rem);
  }
}
@media (min-width: 640px) and (max-width: 893px) {
  .raya-course-map,
  .raya-learning-rail {
    width: min(15.75rem, calc(100vw - 3rem));
  }
  html[data-raya-course-map="expanded"] .raya-learning-shell,
  .raya-learning-shell[data-raya-course-map="expanded"] {
    padding-left: calc(min(15.75rem, calc(100vw - 3rem)) + 1rem);
  }
  html[data-raya-learning-rail="expanded"] .raya-learning-shell,
  .raya-learning-shell[data-raya-learning-rail="expanded"] {
    padding-right: calc(min(15.75rem, calc(100vw - 3rem)) + 1rem);
  }
}
```

- [ ] **Step 8: Use one mirrored edge-opener grammar**

At structural widths, replace the separate collapsed map/rail declarations with this shared grammar. Delete the obsolete collapsed mini-map link/index rules because `.raya-course-map-body` is now fully absent.

```css
@media (min-width: 640px) {
  html[data-raya-course-map="collapsed"] .raya-course-map,
  .raya-course-map[data-raya-course-map="collapsed"],
  html[data-raya-learning-rail="collapsed"] .raya-learning-rail,
  .raya-learning-rail[data-raya-learning-rail="collapsed"] {
    align-items: start;
    background: transparent;
    border: 0;
    box-shadow: none;
    box-sizing: border-box;
    display: grid;
    height: auto;
    justify-items: center;
    margin: 0;
    max-height: none;
    overflow: visible;
    padding: 0;
    pointer-events: none;
    position: fixed;
    width: 2.75rem;
    z-index: 45;
  }
  html[data-raya-course-map="collapsed"] .raya-course-map,
  .raya-course-map[data-raya-course-map="collapsed"] {
    left: 0.35rem;
  }
  html[data-raya-learning-rail="collapsed"] .raya-learning-rail,
  .raya-learning-rail[data-raya-learning-rail="collapsed"] {
    right: 0.35rem;
  }
  html[data-raya-course-map="collapsed"] .raya-course-map-expand,
  .raya-course-map[data-raya-course-map="collapsed"] .raya-course-map-expand,
  html[data-raya-learning-rail="collapsed"] .raya-learning-rail-expand,
  .raya-learning-rail[data-raya-learning-rail="collapsed"] .raya-learning-rail-expand {
    align-items: center;
    background: rgba(255, 255, 255, 0.44);
    backdrop-filter: blur(0.35rem);
    -webkit-backdrop-filter: blur(0.35rem);
    border: 1px solid color-mix(in srgb, var(--raya-color-accent) 30%, transparent);
    border-radius: 0.375rem;
    box-shadow: 0 0.45rem 1rem rgba(31, 35, 40, 0.12);
    display: inline-flex;
    font-size: 0;
    height: 2.5rem;
    justify-content: center;
    min-height: 2.5rem;
    min-width: 2.5rem;
    padding: 0;
    pointer-events: auto;
    width: 2.5rem;
  }
  html[data-raya-course-map="collapsed"] .raya-course-map-expand::after,
  .raya-course-map[data-raya-course-map="collapsed"] .raya-course-map-expand::after {
    content: ">";
    font-size: 1.35rem;
    font-weight: 900;
    line-height: 1;
  }
  html[data-raya-learning-rail="collapsed"] .raya-learning-rail-expand::after,
  .raya-learning-rail[data-raya-learning-rail="collapsed"] .raya-learning-rail-expand::after {
    content: "<";
    font-size: 1.35rem;
    font-weight: 900;
    line-height: 1;
  }
}
@media (min-width: 640px) and (max-width: 1279px) {
  html[data-raya-course-map="collapsed"] .raya-course-map,
  .raya-course-map[data-raya-course-map="collapsed"],
  html[data-raya-learning-rail="collapsed"] .raya-learning-rail,
  .raya-learning-rail[data-raya-learning-rail="collapsed"] {
    top: 0.75rem;
    transform: none;
  }
}
@media (min-width: 1280px) {
  html[data-raya-course-map="collapsed"] .raya-course-map,
  .raya-course-map[data-raya-course-map="collapsed"],
  html[data-raya-learning-rail="collapsed"] .raya-learning-rail,
  .raya-learning-rail[data-raya-learning-rail="collapsed"] {
    top: 50%;
    transform: translateY(-50%);
  }
}
```

- [ ] **Step 9: Run outer-geometry and existing transition tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=/home/uumami/itam/raya_lucaria/.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_rails_share_outer_geometry \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_collapsed_reader_rails_use_mirrored_edge_openers \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_medium_reader_rails_are_overlay_controls \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_course_map_drawer_boundary_switches_to_inline_rails \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_collapsed_reader_rails_expand_article_width_independently \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_desktop_course_map_expansion_hides_full_list_until_transition_end \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_desktop_learning_rail_expansion_keeps_body_accessible_during_transition
```

Expected: `7 passed`.

- [ ] **Step 10: Commit mirrored geometry**

```bash
git add -- packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py
git diff --cached --check
git commit -m "Mirror reader rail geometry"
```

### Task 5: Harden Commands, Comfort Modes, Skins, And Motion

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py:4128-4215,6660-7117`
- Modify: `packages/static/src/raya_static/shell.py:46-52,462-482,1010-1045`
- Test: `tests/e2e/test_preview_static_read_path.py:11750-12168,16792-16960,18117-18479`

**Interfaces:**
- Consumes: final body/outer geometry from Tasks 3-4.
- Produces: stable two-column commands, readable long labels, equivalent final reduced-motion state, and screenshot-ready behavior across supported skins.

- [ ] **Step 1: Replace the obsolete compact-strip test with structural command-body assertions**

Rename `test_render_fixture_tablet_course_map_uses_compact_tool_strip` to `test_render_fixture_structural_course_map_uses_stable_command_body`. Reuse its existing viewport loop, expand it to `[640, 893, 894, 912, 1279, 1280]`, and assert:

```python
expected_commands = [
    "Search", "Graph", "Practice", "Tasks", "Schedule",
    "Context", "Text size", "OpenDyslexic",
]
assert state["visibleCommandTexts"] == expected_commands
assert state["searchFormVisible"] is True
assert state["commandListScrollWidth"] <= state["commandListClientWidth"]
assert len(state["commandGridColumns"].split()) == 2
assert all(item["writingMode"] == "horizontal-tb" for item in state["commands"])
assert all(item["scrollWidth"] <= item["clientWidth"] + 1 for item in state["commands"])
```

Measure each command's `.raya-command-label` writing mode and its command `clientWidth` / `scrollWidth`; keep the existing command order, focus-size stability, icon, and page-order assertions.

- [ ] **Step 2: Extend comfort, skin, and reduced-motion assertions**

In `test_reader_shell_geometry_survives_large_text_and_open_dyslexic`, run the existing largest text/OpenDyslexic state at `894`, `1279`, and `1280` for every supported render-fixture skin:

```python
skin_ids = [
    "eva-unit-01",
    "eva-unit-02",
    "eva-unit-03",
    "ghost-in-the-shell",
    "practice-lab",
    "warm-academic",
]
for skin_id in skin_ids:
    page.evaluate("skin => { document.body.dataset.rayaSkin = skin; }", skin_id)
    for width in (894, 1279, 1280):
        page.set_viewport_size({"width": width, "height": 900})
        state = page.evaluate(
            """() => {
              const box = (selector) => {
                const rect = document.querySelector(selector).getBoundingClientRect();
                return {left: rect.left, right: rect.right, width: rect.width};
              };
              return {
                map: box('#raya-course-map'),
                article: box('#raya-article'),
                rail: box('#raya-learning-rail'),
                commandWritingModes: Array.from(document.querySelectorAll(
                  '.raya-course-rail-command .raya-command-label'
                )).map((label) => getComputedStyle(label).writingMode),
                overflow: Math.ceil(document.documentElement.scrollWidth - innerWidth),
              };
            }"""
        )
        assert abs(state["map"]["width"] - state["rail"]["width"]) <= 1
        assert state["map"]["right"] <= state["article"]["left"] + 1
        assert state["article"]["right"] <= state["rail"]["left"] + 1
        assert state["article"]["width"] >= (672 if width == 1280 else 380)
        assert set(state["commandWritingModes"]) == {"horizontal-tb"}
        assert state["overflow"] <= 1
```

In `test_render_fixture_shell_respects_reduced_motion`, click `[data-raya-course-map-collapse]` and assert after one animation frame:

```python
assert state["mapState"] == "collapsed"
assert state["mapTransitionMarker"] is None
assert state["activeIsMapExpand"] is True
assert state["bodyDisplay"] == "none"
```

- [ ] **Step 3: Run the three stress tests and verify the new assertions fail**

Run:

```bash
UV_PROJECT_ENVIRONMENT=/home/uumami/itam/raya_lucaria/.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_structural_course_map_uses_stable_command_body \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_geometry_survives_large_text_and_open_dyslexic \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_shell_respects_reduced_motion
```

Expected: FAIL on obsolete test assumptions, at least one stress measurement, and the 240ms transition marker retained under reduced motion.

- [ ] **Step 4: Stabilize command tracks and normal label wrapping**

Use these body rules at all structural widths and remove medium icon-only/pill overrides:

```css
.raya-course-map-body {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  min-height: 0;
}
.raya-course-rail-command-list {
  display: grid;
  gap: 0.3125rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  min-width: 0;
}
.raya-course-rail-command {
  box-sizing: border-box;
  min-width: 0;
  overflow: hidden;
}
.raya-course-rail-command .raya-command-label {
  display: inline;
  font-size: 0.75rem;
  font-weight: 700;
  hyphens: none;
  line-height: 1.2;
  min-width: 0;
  overflow-wrap: normal;
  word-break: normal;
}
.raya-course-map-list {
  flex: 1 1 auto;
  min-height: 0;
}
```

Keep the existing emergency `overflow-wrap: break-word` behavior for authored unbroken course-tree identifiers; do not apply `anywhere` to ordinary command or tree labels.

- [ ] **Step 5: Suppress transition markers under reduced motion**

Add `const reducedMotionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");`. In both `setExpanded` and `setLearningRailExpanded`, create transition markers only when the structural state changes and `!reducedMotionQuery.matches`. The final state, storage write, inertness, and focus path remain identical.

- [ ] **Step 6: Run stress tests plus mobile and long-label regressions**

Run:

```bash
UV_PROJECT_ENVIRONMENT=/home/uumami/itam/raya_lucaria/.venv-local uv run pytest -q \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_structural_course_map_uses_stable_command_body \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_geometry_survives_large_text_and_open_dyslexic \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_shell_respects_reduced_motion \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_desktop_course_map_labels_stay_scannable \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_course_map_keeps_emergency_breaks_for_long_labels \
  tests/e2e/test_preview_static_read_path.py::test_mobile_course_map_drawer_is_modal_and_volatile
```

Expected: `6 passed`.

- [ ] **Step 7: Commit command and comfort resilience**

```bash
git add -- \
  packages/static/src/raya_static/rendering.py \
  packages/static/src/raya_static/shell.py \
  tests/e2e/test_preview_static_read_path.py
git diff --cached --check
git commit -m "Harden reader rail visual parity"
```

### Task 6: Verify Visual Evidence And Archive Gates

**Files:**
- Inspect only: `docs/artifact/site/`
- Inspect only: render-debug screenshots and reports generated outside source truth
- Verify: all files changed by Tasks 1-5

**Interfaces:**
- Consumes: the complete implementation and focused regression suite.
- Produces: browser evidence, archive-gate evidence, and a clean reviewable branch ready for deployment.

- [ ] **Step 1: Run the complete focused contract/browser subset**

```bash
UV_PROJECT_ENVIRONMENT=/home/uumami/itam/raya_lucaria/.venv-local uv run pytest -q \
  tests/contracts/test_documentation_surfaces.py \
  tests/contracts/test_static_builder.py \
  tests/e2e/test_preview_static_read_path.py -k 'reader_rail or course_map or learning_shell or reduced_motion'
```

Expected: all selected tests pass with no warnings or page errors.

- [ ] **Step 2: Generate render-debug evidence**

```bash
./scripts/check-render-debug.sh
```

Expected: exit `0`; `report.json` records no overflow/parity failure and desktop/medium/mobile screenshots are produced as local evidence only.

- [ ] **Step 3: Inspect representative screenshots and browser geometry**

Inspect screenshots at `1440x950`, `1280x900`, `894x900`, `640x900`, and `390x844`. Confirm expanded left/right widths match, both headers use the same grammar, collapsed states show only matching edge openers, command labels remain horizontal, the article is unobscured, and the phone map remains a drawer. Do not stage generated reports, screenshots, or `docs/artifact/`.

- [ ] **Step 4: Request adversarial code and visual review**

Use `superpowers:requesting-code-review` with one reviewer focused on contract/accessibility/state and one reviewer focused on breakpoint geometry/visual evidence. Resolve every high- or medium-severity finding through a new red-green cycle before continuing.

- [ ] **Step 5: Run canonical gates sequentially**

```bash
./scripts/check.sh
./scripts/smoke-test.sh
./scripts/check-docker.sh
```

Expected: every command exits `0`. Do not run host and Docker checks concurrently.

- [ ] **Step 6: Verify branch scope and commit any review-only corrections**

```bash
git status --short
git diff --check origin/new_rayalucaria...HEAD
git diff --name-only origin/new_rayalucaria...HEAD
```

Expected tracked paths are limited to the approved design/plan, foundation, four role guides, builder/rendering/shell, and the three test files named in this plan. Commit any reviewed correction with an imperative subject and rerun its focused test before the canonical gates.

### Task 7: Merge, Deploy, And Verify The Live Reader

**Files:**
- No source edits expected.
- Deploy workflow: `.github/workflows/deploy.yml`

**Interfaces:**
- Consumes: reviewed branch with passing host, smoke, Docker, and CI gates.
- Produces: merged `new_rayalucaria`, a successful manual GitHub Pages deployment, and a live URL with fresh-browser visual evidence.

- [ ] **Step 1: Push the reviewed branch and open the PR**

```bash
git push -u origin fix/reader-rail-parity
gh pr create \
  --base new_rayalucaria \
  --head fix/reader-rail-parity \
  --title "Mirror reader rail controls" \
  --body "Restores the course-map rail as the left counterpart of Learning context, adds a separate inert body and edge opener, aligns bilingual truth surfaces, and verifies desktop, medium, phone, comfort, storage, and accessibility behavior."
```

Expected: GitHub returns a PR URL.

- [ ] **Step 2: Wait for PR checks and merge**

```bash
gh pr checks --watch
gh pr merge --merge --delete-branch
```

Expected: `Checks / host-check` and `Checks / docker-check` pass; the PR merges into `new_rayalucaria`.

- [ ] **Step 3: Dispatch and watch the Pages workflow**

```bash
gh workflow run deploy.yml --ref new_rayalucaria
run_id="$(gh run list --workflow deploy.yml --branch new_rayalucaria --limit 1 \
  --json databaseId --jq '.[0].databaseId')"
test -n "$run_id"
gh run watch "$run_id" --exit-status
gh run view "$run_id" --json status,conclusion,url
```

Expected: `Deploy Docs to GitHub Pages` completes with conclusion `success`.

- [ ] **Step 4: Verify the live URL without cached session state**

Use a fresh Playwright browser context at `https://uumami.wiki/raya_lucaria/`, clear `sessionStorage`, and verify at `1440x950`, `894x900`, and `390x844`:

```javascript
() => ({
  ready: document.documentElement.dataset.rayaShellReady,
  mapState: document.documentElement.dataset.rayaCourseMap,
  mapHeader: document.querySelector('[data-raya-course-map-collapse]')?.textContent.trim(),
  mapBodyVisible: document.querySelector('#raya-course-map-body')?.checkVisibility(),
  overflow: Math.ceil(document.documentElement.scrollWidth - innerWidth),
})
```

Expected expanded structural result: `ready === "true"`, `mapHeader === "Hide map"`, `mapBodyVisible === true`, and `overflow <= 1`. After collapse, only `[data-raya-course-map-expand]` is visible and it matches the right Context opener. At phone width, the desktop opener is absent and the Map launcher opens the modal drawer.

- [ ] **Step 5: Report the live URL and evidence**

Report the PR, merge commit, deployment run, live URL, canonical commands, focused test counts, and inspected viewport list. Do not claim completion until the live fresh-browser checks pass.
