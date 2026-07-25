# Rail Home Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an always-visible course-home icon control to the top of the left course rail, returning the reader to the course landing page.

**Architecture:** The rail header (`_render_rail_chrome` in `builder.py`) gains an optional `header_home_html` slot, filled only for the course map (never the learning rail) and only when the course has a real index root. To make room in the one-row, height-parity-pinned header, the `Hide map` collapse button is converted from text to an icon (keeping its accessible name via aria-label and its `textContent` via a visually-hidden span), and the shared sub-894 header `min-height` is raised so both rail headers grow equally and left/right height parity holds by construction.

**Tech Stack:** Python 3.10, uv workspace (`raya_schema`, `raya_cli`, `raya_static`). HTML/CSS emitted as Python strings from `builder.py` / `rendering.py`. Tests: pytest; browser e2e via Playwright + google-chrome through `raya_cli.preview.create_preview`.

**Design spec:** `docs/superpowers/specs/2026-07-20-rail-home-control-contract-amendment-design.md` (final, validated across three adversarial rounds + a parity-fix confirmation).

## Global Constraints

- **Authority order:** `docs/foundation/` is seed truth. This change amends `docs/foundation/20_learning_renderer_contract.md` deliberately; keep the foundation internally self-consistent (`13_truth_surfaces.md`).
- **Test command:** `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest <path> -v` (run from repo root `/home/uumami/itam/raya_lucaria`).
- **Full-suite gate exceeds the 10-min shell cap (~17 min).** Never run the whole suite in the foreground — it detaches and strands the run. Run it in the background to a log file and read the log on completion: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q > /tmp/full-suite.log 2>&1` via a background execution, then read the log.
- **Browser e2e** requires google-chrome (resolved by `_browser_executable()` at `/usr/bin/google-chrome`). Mirror the existing launch/goto boilerplate already repeated throughout `tests/e2e/test_rail_collapse_contract.py` and `tests/e2e/test_preview_static_read_path.py` (`create_preview(course, host="127.0.0.1", port=0, dry_run=False)` → `handle.base_url` → `p.chromium.launch(executable_path=str(_browser_executable()))` → `page.goto(f"{handle.base_url}/<page>/index.html", wait_until="networkidle")`).
- **Render fixture:** `examples/courses/render-fixture` (root is `course/0_index.md`, so `root_id` is set and the home control renders). Reader page for measurements: `authoring-matrix/index.html`.
- **Keep English/Spanish role guides separate.** Commands, paths, class names, schema fields, accessible names stay in English.
- **The eight body command tiles are NOT changed.** The header gains one action (home); the body stays eight.
- **Do not edit generated outputs** (`_site/`, `artifact/`, `node_modules/`, `.pytest_cache/`).
- **Commits:** scoped to this repo only. End each commit body with:
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`

---

## File Structure

- `docs/foundation/20_learning_renderer_contract.md` — amended (6 edits): header action enumeration, nine→ten reader actions, `:33` table row, drawer chrome, Verification, deployment-neutrality.
- `docs/guides/en/students/index.md`, `docs/guides/es/estudiantes/index.md`, `docs/guides/en/agents/index.md`, `docs/guides/es/agentes/index.md` — extend the header description to mention the course-home control and the icon rendering of `Hide map` (no count change; body stays "eight").
- `packages/static/src/raya_static/builder.py` — add `collapse` glyph; add `label_hidden` param to `_render_course_map_toggle`; icon-ify the course-map collapse button; add `_render_rail_home_link`; add `header_home_html` param to `_render_rail_chrome`; wire the home control (gated on `root_id`) into `_render_course_map`.
- `packages/static/src/raya_static/rendering.py` — raise shared sub-894 header `min-height` from `2.9375rem` to `3.625rem`.
- `tests/contracts/test_documentation_surfaces.py` — add course-home-control assertion.
- `tests/contracts/test_static_builder.py` — update the collapse-button markup pin (`:5591-5597`); header child-order pins gain the home `<a>`.
- `tests/e2e/test_preview_static_read_path.py` — update collapse width/height pins (`:17338`, `:20943`, `:17339`, `:20944`).
- `tests/e2e/test_rail_home_control.py` (new) — parity, icon conversion, home present/named/omit, aria-current, drawer order, collapsed-one-control.
- `examples/courses/<two-root fixture>` (new) — a two-root/no-index course for the omit-gate test.

---

## Task 1: Contract amendment + role guides

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md` (lines 23, 25, 33, 27, and the `## Verification` section)
- Modify: `docs/guides/en/students/index.md`, `docs/guides/es/estudiantes/index.md`, `docs/guides/en/agents/index.md`, `docs/guides/es/agentes/index.md`
- Test: `tests/contracts/test_documentation_surfaces.py`

**Interfaces:**
- Consumes: nothing (documentation authority layer).
- Produces: the amended contract text that Tasks B–D implement; no code symbols.

- [ ] **Step 1: Add the failing doc-surface assertion**

In `tests/contracts/test_documentation_surfaces.py`, find the reader-rail visual-parity truth-surface test (around `:378-399`, the one pinning `"Hide map"`, the tile enumeration, and `"header Map action"`). Add an assertion that the contract now enumerates a course-home rail action. Read the surrounding assertions first and match their style; the new assertion should require the foundation text to contain the course-home rail control, e.g.:

```python
    # Rail home control is part of the amended header enumeration.
    assert "course-home action" in contract_text
    assert "ten reader actions" in contract_text
```

(Use the exact variable name the test already uses for the loaded contract file — likely `contract_text` or similar; match it.)

- [ ] **Step 2: Run it to verify it fails**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_documentation_surfaces.py -v`
Expected: FAIL (the strings are not yet in the contract).

- [ ] **Step 3: Amend `docs/foundation/20_learning_renderer_contract.md`**

Edit `:25` sentence 1. Change:
> At structural reader widths, the left course rail header presents `Course map` and an explicit `Hide map` Map action.

to:
> At structural reader widths, the left course rail header presents `Course map`, a course-home action, and an explicit `Hide map` Map action rendered as an icon control with the accessible name `Hide course map`.

Edit `:25` sentence 3. Change:
> The header Map action and eight body commands preserve the existing nine reader actions without duplicating Map inside the body.

to:
> The header Map action, the header course-home action, and eight body commands preserve the existing ten reader actions without duplicating Map inside the body.

Edit the `:33` table row ("Course map and reading context"). Change its header clause:
> a structural header that presents `Course map` and an explicit `Hide map` Map action

to:
> a structural header that presents `Course map`, a course-home action, and an explicit `Hide map` Map action rendered as an icon control

(Leave "Keep the header Map action separate from the eight body commands." unchanged — it stays valid.)

Edit `:27` (phone drawer sentence). After the drawer chrome enumeration ("visible chrome, a close button, backdrop and Escape close paths, focus containment, background inertness, and temporary background scroll lock"), add that the drawer chrome may include the course-home control. Insert a clause, e.g.: "The drawer chrome may include the course-home action ordered before the close button."

Edit the `## Verification` section. In the breadcrumb-check sentence ("Breadcrumb checks should cover accessible navigation markup, course-home and ancestor links, current-page marking, deployment-neutral relative URLs, no source/private paths, no external requests, and desktop/mobile no-overflow behavior."), add a following sentence: "Rail home-control checks should cover the same: an accessible course-home link resolving to the course root, deployment-neutral relative URLs, no source/private paths, no external requests, omission when the course has no index root, and left/right rail header height parity."

Edit `:23`. Change:
> Breadcrumb links are deployment-neutral static links and must not expose authored source paths.

to:
> Reader navigation links — breadcrumbs and the left-rail course-home control — are deployment-neutral static links and must not expose authored source paths.

- [ ] **Step 4: Update the four role guides**

In `docs/guides/en/students/index.md:51` and `docs/guides/es/estudiantes/index.md:52`, the sentence describing the rail header ("the rail header shows `Course map` with a `Hide map` Map action" / its Spanish equivalent) — extend it to mention the course-home control and that `Hide map` renders as an icon. Keep each language's prose in its own file; keep `Course map`, `Hide map`, and control names in English. Example (English): "the rail header shows a course-home control, `Course map`, and a `Hide map` Map action rendered as an icon". Mirror in Spanish, keeping the English tokens.

In `docs/guides/en/agents/index.md:144` and `docs/guides/es/agentes/index.md:155`, the "eight reader commands" / "ocho comandos lectores" sentence stays **unchanged in count**. Add a note that the header also presents the course-home control alongside the `Hide map` icon action. Do not change "eight"/"ocho".

- [ ] **Step 5: Run the doc-surface test to verify it passes**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_documentation_surfaces.py -v`
Expected: PASS. If other assertions in this file break (e.g. it re-reads the exact `:25` sentence), update them to the amended wording.

- [ ] **Step 6: Verify no other foundation surface contradicts the change**

Run: `rg -n "nine reader actions|nine reader|existing nine" docs/`
Expected: no remaining "nine reader actions" in `docs/foundation/` or `docs/guides/`. Fix any straggler.

- [ ] **Step 7: Commit**

```bash
git add docs/foundation/20_learning_renderer_contract.md docs/guides tests/contracts/test_documentation_surfaces.py
git commit -m "docs(contract): amend rail header to grant a course-home action"
```

---

## Task 2: Icon-ify the `Hide map` collapse button + raise header min-height (parity fix)

These land together: icon-ification breaks left/right header height parity at 640/893; the min-height fix restores it. Committing them separately would leave the suite red between commits.

**Files:**
- Modify: `packages/static/src/raya_static/builder.py` (`_COMMAND_ICON_BODIES` ~`:3232`; `_render_course_map_toggle` `:1894-1922`; the collapse call at `:2208-2214`)
- Modify: `packages/static/src/raya_static/rendering.py` (`:4082`, the `min-height` in the shared `.raya-course-map-header, .raya-learning-rail-header` rule)
- Modify: `tests/contracts/test_static_builder.py` (`:5591-5597` markup pin; `:4946`/`:4970` stay green)
- Modify: `tests/e2e/test_preview_static_read_path.py` (`:17338`, `:20943` width; `:17339`, `:20944` height)
- Create/Test: `tests/e2e/test_rail_home_control.py` (parity + icon-conversion tests)

**Interfaces:**
- Consumes: `_command_icon(name)` (`builder.py:3288`), `.raya-visually-hidden` CSS (`rendering.py:638-646`).
- Produces:
  - `_COMMAND_ICON_BODIES["collapse"]` — a new glyph body.
  - `_render_course_map_toggle(..., label_hidden: bool = False)` — when `label_hidden` is True and `icon` is set, the label is wrapped in `<span class="raya-visually-hidden">` instead of `<span class="raya-command-label">`.
  - The course-map collapse button now renders `_command_icon("collapse")` + a visually-hidden `Hide map` span, keeping `aria-label="Hide course map"` and `textContent === "Hide map"`.

- [ ] **Step 1: Write the failing icon-conversion unit test**

In `tests/contracts/test_static_builder.py` (or a focused new test — match the file's existing render-a-course pattern), assert the collapse button renders an icon and a visually-hidden label:

```python
def test_course_map_collapse_renders_icon_with_hidden_label():
    html_out = _render_minimal_course_html()  # reuse the file's existing render helper
    # icon present, aria-hidden
    assert 'data-raya-command-icon="collapse"' in html_out
    # label preserved but visually hidden (textContent stays "Hide map")
    assert '<span class="raya-visually-hidden">Hide map</span>' in html_out
    # accessible name preserved via aria-label
    assert 'aria-label="Hide course map"' in html_out
```

(Use the existing helper this file already uses to render a course to HTML; grep for how `test_static_builder.py` builds `html`/`text` around `:4946`.)

- [ ] **Step 2: Run it to verify it fails**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_course_map_collapse_renders_icon_with_hidden_label -v`
Expected: FAIL (no `collapse` icon, label not hidden).

- [ ] **Step 3: Add the `collapse` glyph**

In `packages/static/src/raya_static/builder.py`, add to `_COMMAND_ICON_BODIES` (after the `"home"` entry, `:3233-3237`):

```python
    "collapse": (
        '<path d="M13 7l-5 5 5 5"/>'
        '<path d="M18 7v10"/>'
    ),
```

(A left chevron plus a vertical bar — "collapse the panel toward the edge".)

- [ ] **Step 4: Add the `label_hidden` param to `_render_course_map_toggle`**

Modify `_render_course_map_toggle` (`builder.py:1894-1922`). Add `label_hidden: bool = False` to the keyword-only params, and change the icon branch so the label span class depends on it:

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
    label_hidden: bool = False,
) -> str:
    aria_expanded = "true" if expanded else "false"
    aria_label_attr = (
        f' aria-label="{html.escape(aria_label, quote=True)}"' if aria_label else ""
    )
    marker_attr = f" {marker}" if marker else ""
    label_markup = html.escape(label)
    if icon is not None:
        label_span_class = "raya-visually-hidden" if label_hidden else "raya-command-label"
        label_markup = (
            f"{_command_icon(icon)}"
            f'<span class="{label_span_class}">{html.escape(label)}</span>'
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

- [ ] **Step 5: Icon-ify the collapse call**

In `_render_course_map` (`builder.py:2208-2214`), change the `collapse_button_html` argument to pass the icon and hidden label:

```python
        collapse_button_html=_render_course_map_toggle(
            "Hide map",
            class_name="raya-course-map-collapse",
            aria_label="Hide course map",
            icon="collapse",
            controls="raya-course-map-body",
            marker="data-raya-course-map-collapse",
            label_hidden=True,
        ),
```

(Leave the `expand_button_html` call — the `"Map"` edge opener — unchanged.)

- [ ] **Step 6: Run the unit test to verify it passes**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_course_map_collapse_renders_icon_with_hidden_label -v`
Expected: PASS.

- [ ] **Step 7: Update the collapse-button markup pin**

`tests/contracts/test_static_builder.py:5591-5597` pins the literal old markup (`...aria-label="Hide course map">Hide map</button>`). Update it to the new icon + visually-hidden-span markup. Read the current assertion, then replace the expected substring with the new button output (icon svg + `<span class="raya-visually-hidden">Hide map</span>`). The `"Hide map" in text` pins at `:4946` and `:4970` stay as-is (textContent still contains "Hide map").

- [ ] **Step 8: Write the failing parity + icon e2e test**

Create `tests/e2e/test_rail_home_control.py`. Mirror the launch/goto boilerplate from `tests/e2e/test_rail_collapse_contract.py` (import `_browser_executable`, `create_preview`, the `RENDER_FIXTURE` course path). Add a parity test that measures both rail headers at four widths, in all four font×density cells:

```python
def test_rail_header_height_parity_across_widths():
    from raya_cli.preview import create_preview
    handle = create_preview(RENDER_FIXTURE, host="127.0.0.1", port=0, dry_run=False)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=str(_browser_executable()))
            page = browser.new_page()
            page.goto(f"{handle.base_url}/authoring-matrix/index.html",
                      wait_until="networkidle")
            for width in (640, 893, 894, 1280):
                page.set_viewport_size({"width": width, "height": 900})
                # ensure both rails expanded exactly as the parity gate does;
                # reuse the expand-state helper pattern from test_preview_static_read_path.py
                heights = page.evaluate(
                    """() => {
                        const mh = document.querySelector('.raya-course-map-header');
                        const rh = document.querySelector('.raya-learning-rail-header');
                        return {
                            map: mh ? mh.getBoundingClientRect().height : null,
                            rail: rh ? rh.getBoundingClientRect().height : null,
                        };
                    }"""
                )
                assert heights["map"] is not None and heights["rail"] is not None
                assert abs(heights["map"] - heights["rail"]) <= 1, (width, heights)
            browser.close()
    finally:
        handle.stop()
```

Add a companion assertion that the collapse button now renders an icon (no visible text) and keeps its names:

```python
def test_course_map_collapse_is_icon_with_preserved_names():
    from raya_cli.preview import create_preview
    handle = create_preview(RENDER_FIXTURE, host="127.0.0.1", port=0, dry_run=False)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=str(_browser_executable()))
            page = browser.new_page()
            page.goto(f"{handle.base_url}/authoring-matrix/index.html",
                      wait_until="networkidle")
            data = page.evaluate(
                """() => {
                    const b = document.querySelector('[data-raya-course-map-collapse]');
                    return {
                        text: b.textContent.trim(),
                        aria: b.getAttribute('aria-label'),
                        hasIcon: !!b.querySelector('[data-raya-command-icon="collapse"]'),
                    };
                }"""
            )
            assert data["hasIcon"] is True
            assert data["text"] == "Hide map"
            assert data["aria"] == "Hide course map"
            browser.close()
    finally:
        handle.stop()
```

- [ ] **Step 9: Run the parity test to verify it FAILS at 640/893**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_home_control.py::test_rail_header_height_parity_across_widths -v`
Expected: FAIL at width 640 (and 893) — the icon collapse pushed the map header taller than the learning-rail header. This demonstrates the parity break the min-height fix must close.

- [ ] **Step 10: Raise the shared sub-894 header min-height**

In `packages/static/src/raya_static/rendering.py:4082`, inside the `.raya-course-map-header, .raya-learning-rail-header { ... }` rule, change:

```css
  min-height: 2.9375rem;
```

to:

```css
  min-height: 3.625rem;
```

(Leave the `@media (min-width: 894px)` override at `:4117-4121`, `min-height: 3.9375rem`, unchanged — it still dominates at ≥894.)

- [ ] **Step 11: Run the parity test to verify it PASSES at all four widths**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_home_control.py -v`
Expected: PASS at 640/893/894/1280 (delta ≈ 0). Both icon-conversion and parity tests green.

- [ ] **Step 12: Update the collapse width/height pins**

In `tests/e2e/test_preview_static_read_path.py`:
- `:17338` `assert 80 <= header_collapse["width"] <= 100` → change to the icon width, `assert 40 <= header_collapse["width"] <= 56`.
- `:20943` (the second copy, `80 <= ... <= 100`) → same change.
- `:17339` and `:20944` (`28 <= height <= 40`) → widen the upper bound to `28 <= height <= 44` (the icon button measures ~40.4px and must not sit one sub-pixel from failing).

Confirm the exact current text at each line before editing (line numbers may have drifted from Task 1's doc-only commit — grep `80 <= ` and `mapCollapseWidth` / `header_collapse`).

- [ ] **Step 13: Run the affected read-path tests**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py -k "collapse or header or parity" -v`
Expected: PASS. (This is a subset; the full-suite gate runs at task end.)

- [ ] **Step 14: Full-suite gate (background) + commit**

Run the full suite in the background to a log (never foreground — it exceeds the 10-min cap):
`UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q > /tmp/suite-taskB.log 2>&1`
Read the log on completion; all green before committing. Then:

```bash
git add packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py tests/e2e/test_rail_home_control.py
git commit -m "feat(rail): icon-ify Hide map and grow header min-height for parity"
```

---

## Task 3: Add the course-home control (helper, param, wiring, behaviour)

**Files:**
- Modify: `packages/static/src/raya_static/builder.py` (new `_render_rail_home_link`; `header_home_html` param on `_render_rail_chrome` `:1930-1972`; wiring in `_render_course_map` around `:1995` and `:2196-2230`)
- Modify: `tests/contracts/test_static_builder.py` (header child-order pins gain the home `<a>`)
- Modify: `tests/render/test_render_debug_report.py`, `tests/render/test_render_debug_parity_gate.py` (only if they snapshot header markup)
- Test: `tests/e2e/test_rail_home_control.py`

**Interfaces:**
- Consumes: `_command_icon("home")`, `_course_home_page(content_model)` (`builder.py:3475`), `_relative_href(page.output_path, home_page.output_path)` (the breadcrumb's URL derivation, `builder.py:3507`), `content_model.root_id`.
- Produces:
  - `_render_rail_home_link(home_href: str) -> str` — `<a class="raya-course-map-home" href=... aria-label="Back to course">{home icon}</a>`.
  - `_render_rail_chrome(..., header_home_html: str | None = None)` — a new keyword-only slot inserted **between** `header_prefix_html` and the region-title paragraph.

- [ ] **Step 1: Write the failing "home present + named" e2e test**

Add to `tests/e2e/test_rail_home_control.py`:

```python
def test_rail_home_link_present_and_resolves_from_nested_page():
    from raya_cli.preview import create_preview
    handle = create_preview(RENDER_FIXTURE, host="127.0.0.1", port=0, dry_run=False)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=str(_browser_executable()))
            page = browser.new_page()
            page.goto(f"{handle.base_url}/authoring-matrix/index.html",
                      wait_until="networkidle")
            link = page.locator('.raya-course-map-header a.raya-course-map-home')
            assert link.count() == 1
            assert link.get_attribute("aria-label") == "Back to course"
            href = link.get_attribute("href")
            assert href and "://" not in href and not href.startswith("/")  # deployment-neutral relative
            browser.close()
    finally:
        handle.stop()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_home_control.py::test_rail_home_link_present_and_resolves_from_nested_page -v`
Expected: FAIL (no `.raya-course-map-home` yet).

- [ ] **Step 3: Add the `_render_rail_home_link` helper**

In `builder.py`, near `_render_course_map_toggle`, add:

```python
def _render_rail_home_link(home_href: str) -> str:
    """Icon-only course-home control for the left rail header.

    Accessible name comes from aria-label (matching the discovery command bar's
    "Back to course"); the home glyph is aria-hidden. No aria-current: the map
    tree already marks the current page inside this same landmark.
    """
    return (
        '<a class="raya-course-map-home" '
        f'href="{html.escape(home_href)}" '
        'aria-label="Back to course">'
        f'{_command_icon("home")}'
        "</a>"
    )
```

- [ ] **Step 4: Add the `header_home_html` slot to `_render_rail_chrome`**

Modify `_render_rail_chrome` (`builder.py:1930-1972`): add `header_home_html: str | None = None` to the keyword-only params, and insert it into `items` between `header_prefix_html` and the region-title paragraph:

```python
    header_home_html: str | None = None,
    ...
    items: list[str | None] = [
        landmark_open_html,
        f'<div class="{header_class}">',
        header_prefix_html,
        header_home_html,
        f'<p class="raya-region-title">{html.escape(region_title)}</p>',
        header_suffix_html,
        collapse_button_html,
        "</div>",
        ...
    ]
```

The existing `"\n".join(item for item in items if item is not None)` keeps output byte-identical when `header_home_html` is None (the learning-rail path never passes it).

- [ ] **Step 5: Wire the home control into `_render_course_map` (gated on `root_id`)**

In `_render_course_map`, after `root_identity = content_model.root_id or course_title` (`:1995`), compute the home slot:

```python
    header_home_html: str | None = None
    if content_model.root_id is not None:
        home_page = _course_home_page(content_model)
        if home_page is not None:
            home_href = _relative_href(page.output_path, home_page.output_path)
            header_home_html = _render_rail_home_link(home_href)
```

Then pass it in the `_render_rail_chrome(...)` call (`:2196`), adding one argument:

```python
        header_home_html=header_home_html,
```

Do **not** add `header_home_html` to the `_render_learning_rail` call (`:2257`) — the learning rail must not gain a home control.

- [ ] **Step 6: Run the home-present test to verify it passes**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_home_control.py::test_rail_home_link_present_and_resolves_from_nested_page -v`
Expected: PASS.

- [ ] **Step 7: Write + pass the remaining behaviour tests**

Add these to `tests/e2e/test_rail_home_control.py` (mirror the boilerplate). Run each; all must pass:

```python
def test_no_home_control_in_learning_rail_header():
    # the learning-rail header must NOT gain a home control (shared-helper leak guard)
    ...
    count = page.locator('.raya-learning-rail-header a.raya-course-map-home').count()
    assert count == 0

def test_single_aria_current_on_course_root_page():
    # open the course root; exactly one aria-current inside #raya-course-map
    ...
    page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
    n = page.locator('#raya-course-map a[aria-current="page"]').count()
    assert n == 1

def test_drawer_home_before_close_and_shift_tab_wrap():
    # at phone width, open the drawer; home precedes close in DOM and is the
    # shift-Tab wrap target (focusable[0]); initial focus stays on close.
    ...

def test_collapsed_rail_exposes_one_visible_control():
    # at >=894 collapse the map; header (with home) is display:none; only the
    # expand chip is visible.
    ...
```

Fill each in against the existing helpers (grep `test_preview_static_read_path.py` for how it opens the drawer, collapses the map, and enumerates focusables — reuse those patterns rather than inventing new ones).

- [ ] **Step 8: Update header child-order / markup pins**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py tests/render/test_render_debug_report.py tests/render/test_render_debug_parity_gate.py -v`
Any failure is a header-markup snapshot/child-order pin that now must include the home `<a class="raya-course-map-home">` before the title. Update each expected markup/child list to include it. Do not weaken the assertions — add the home element in the correct position.

- [ ] **Step 9: Full-suite gate (background) + commit**

`UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q > /tmp/suite-taskC.log 2>&1` (background), read the log, all green. Then:

```bash
git add packages/static/src/raya_static/builder.py tests/
git commit -m "feat(rail): add always-visible course-home control to the left rail"
```

---

## Task 4: Omit the control when the course has no index root

**Files:**
- Create: `examples/courses/rail-two-root-fixture/` (a minimal two-root, no-index course)
- Test: `tests/e2e/test_rail_home_control.py`

**Interfaces:**
- Consumes: the `root_id` gate added in Task 3.
- Produces: a reusable fixture proving the omit path.

- [ ] **Step 1: Create the two-root fixture**

Create a minimal course whose `course/` holds two depth-0 files with no `0_`/`00_` index — e.g. `course/1_alpha.md` and `course/2_beta.md`, each with the minimal front-matter the validator requires (copy the shape from `examples/courses/minimal` and rename so there is no zero-order index file). Confirm it validates and builds:

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate examples/courses/rail-two-root-fixture`
Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/rail-two-root-fixture`
Expected: both succeed; the build produces no `site/index.html` (two roots, `root_id` unset).

- [ ] **Step 2: Write the failing omit test**

```python
def test_home_control_omitted_when_no_index_root():
    from raya_cli.preview import create_preview
    handle = create_preview(TWO_ROOT_FIXTURE, host="127.0.0.1", port=0, dry_run=False)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=str(_browser_executable()))
            page = browser.new_page()
            page.goto(f"{handle.base_url}/alpha/index.html", wait_until="networkidle")
            assert page.locator('a.raya-course-map-home').count() == 0
            browser.close()
    finally:
        handle.stop()
```

(Point `TWO_ROOT_FIXTURE` at the new course; adjust the opened page path to whatever the fixture emits.)

- [ ] **Step 3: Run it — it should already PASS**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_home_control.py::test_home_control_omitted_when_no_index_root -v`
Expected: PASS (the `root_id is not None` gate from Task 3 already omits it). If it FAILS (the control renders), the gate is wrong — revisit Task 3 Step 5 (must gate on `content_model.root_id`, not on `_course_home_page()` resolving).

- [ ] **Step 4: Full-suite gate (background) + commit**

`UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q > /tmp/suite-taskD.log 2>&1` (background), read the log, all green. Then:

```bash
git add examples/courses/rail-two-root-fixture tests/e2e/test_rail_home_control.py
git commit -m "test(rail): omit course-home control for two-root no-index courses"
```

---

## Deploy & verify (after all tasks)

Per the standing goal, after the branch is green and merged:

1. Trigger deploy: `gh workflow run deploy.yml --ref new_rayalucaria`.
2. Once the run succeeds, chromium-verify the live site (`uumami.wiki/raya_lucaria/`): the left rail shows a home icon at top, clicking it returns to the course landing page, the collapse control is now an icon with accessible name "Hide course map", and left/right rail headers are the same height at narrow widths. Verify with a Playwright script against the live URL (mirror the sub-goal-1 `live_verify.py` pattern).

## Self-Review (completed)

- **Spec coverage:** Contract amendment (6 edits) → Task 1. Icon conversion + parity min-height + accessible-name/textContent preservation → Task 2 (spec §Enabling change, tests #1/#2/#3/#7). Home control helper/param/wiring + no-leak + aria-current + drawer order + collapsed-one-control → Task 3 (tests #4/#6/#8/#9). Omit gate + two-root fixture → Task 4 (test #5). Role guides + doc-surface → Task 1. All pinning-test updates assigned (`:5591-5597`, `:17338/:20943`, `:17339/:20944` → B; child-order/render-debug → C; doc-surface → A). No spec requirement left unassigned.
- **Placeholder scan:** Behaviour tests in Task 3 Step 7 and the drawer/collapsed bodies are described, not fully coded, because they must reuse existing drawer-open / collapse / focusable-enumeration helpers in `test_preview_static_read_path.py` that differ in signature; the plan names the exact helpers to mirror. All load-bearing code (glyph, `label_hidden`, home helper, chrome slot, wiring, min-height) is shown in full.
- **Type consistency:** `header_home_html: str | None` used consistently in `_render_rail_chrome` and `_render_course_map`; `_render_rail_home_link(home_href: str) -> str`; `label_hidden: bool` on `_render_course_map_toggle`. Names match across tasks.
