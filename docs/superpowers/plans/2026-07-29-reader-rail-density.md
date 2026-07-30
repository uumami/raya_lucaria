# Reader Rail Density Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make both reader rails scrollable and readable at their shipped 240px width — fix the wheel dead zone, cut 170px of fixed chrome, widen the label column from 103px to ~150px, and stop the right rail shipping 1358px of expanded panels in a 767px window.

**Architecture:** All changes are CSS in `packages/static/src/raya_static/rendering.py` plus four small markup/flag edits in `builder.py` and one in `accessibility.py`. No new markup elements, no new JavaScript, no new `@media` rules, and no new geometry literals. CSS edits land inside the existing `@media (min-width: __RAYA_STRUCTURAL_PX__px)` band that already owns rail flex layout (`rendering.py:6693-6760`), except two base-rule deletions that the sub-640 drawer re-declares behind `all: revert` and therefore cannot inherit.

**Tech Stack:** Python 3.10, uv workspace (`raya_schema`, `raya_cli`, `raya_static`). CSS is emitted as a Python string from `rendering.py`. Tests are pytest + Playwright driving Chromium.

**Spec:** `docs/superpowers/specs/2026-07-29-reader-rail-density-design.md` (revision 2, commit `fbd69d7`). Read its "What is NOT the problem" and "Corrections to revision 1" sections before starting — they record eight measured facts that a previous draft got wrong.

## Global Constraints

- Branch: `feature/reader-rail-density`. Do not commit to `new_rayalucaria`.
- Test command: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest <path> -v` from the repo root.
- **Run only the focused tests named in your task. Do NOT run the full suite** — it takes ~18 minutes and exceeds the tool timeout. The controller owns the full-suite gate (Task 12).
- **Every new check must fail against the pre-change code before it passes.** Each task's Step 2 is that red run, and its output must be pasted into the task report. A check that cannot be made to fail is not a check.
- Do not edit generated outputs: `_site/`, `artifact/`, nested example `artifact/`, `node_modules/`, `.pytest_cache/`.
- Never add `height: 100%` to `.raya-course-map` or `.raya-learning-rail`. They are content-sized up to `max-height`; stretching them breaks short courses.
- Never set `overflow: hidden` on `.raya-course-map`. Its `overflow: auto` is a documented relief valve (`rendering.py:6731-6738`); removing it clips tree content at enlarged root font sizes with no scroll path.
- Never lower `.raya-course-map-list { min-height: 12rem }` (`rendering.py:6739`). `tests/e2e/test_rail_collapse_contract.py:648` ratifies a >= 160px floor.
- Keep `overflow-wrap: break-word` on `.raya-course-map-list a`. It is load-bearing for a 55-character unbroken identifier and is pinned at `tests/e2e/test_preview_static_read_path.py:17554`.
- Do not touch `shell_geometry.py`, the 640-893 medium-band mutual-exclusion collapse, or the sub-640 drawer architecture. All three are explicit non-goals.
- Do not add a `title` attribute to map links, and do not reveal the sequence badge on `:hover`.
- Commit message bodies end with: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- Browser tests need Chromium. Set `RAYA_TEST_BROWSER=/usr/bin/google-chrome` if auto-detection fails.

## File Structure

| File | Responsibility | Tasks |
| --- | --- | --- |
| `packages/static/src/raya_static/rendering.py` | All CSS changes | 1, 2, 4, 6, 7, 8, 9, 10 |
| `packages/static/src/raya_static/builder.py` | Remove rail page position; flip three panel `expanded` flags | 5, 10 |
| `packages/static/src/raya_static/accessibility.py` | Scope the `.raya-font-toggle` background so it stops faking an "on" state | 4 |
| `examples/courses/rail-density-fixture/` | New 31-page, 3-deep fixture; density is unmeasurable on the 6-page `render-fixture` | 3 |
| `tests/e2e/test_rail_density.py` | New: wheel liveness, gutter symmetry, chrome cut, index rows, right rail, density gate | 1, 2, 4, 5, 6, 7, 8, 9, 10, 12 |
| `tests/e2e/test_preview_static_read_path.py` | Update existing assertions the design intentionally changes | 4, 5, 7, 8, 9, 10 |
| `tests/contracts/test_static_builder.py` | Update markup/CSS contract assertions | 4, 5, 10, 11 |
| `docs/foundation/20_learning_renderer_contract.md` | Contract amendment | 11 |
| `docs/guides/{en,es}/…/index.md` | Eight role-doc locations | 11 |

---

### Task 1: Free the scroll wheel

This is the user-reported bug and the highest-value change in the plan. `.raya-course-map` declares `overflow: auto` **and** `overscroll-behavior: contain` while its `scrollHeight` equals its `clientHeight`. Chrome still treats it as a scroll container, and `contain` blocks scroll chaining, so a wheel event over the header, the tools row, or the filter is captured and discarded — 351.8px of an 868px rail (41%) where nothing moves.

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py:4008`
- Test: `tests/e2e/test_rail_density.py` (create)

**Interfaces:**
- Consumes: nothing.
- Produces: `tests/e2e/test_rail_density.py` with module-level helpers `_browser_executable()`, `ROOT`, `RENDER_FIXTURE`, and `_preview(tmp_path, fixture)`. Tasks 2, 4-10, and 12 add tests to this same file and reuse these helpers.

- [ ] **Step 1: Write the failing test**

Create `tests/e2e/test_rail_density.py`:

```python
"""Reader rail density and scroll-liveness contract.

Companion to tests/e2e/test_rail_collapse_contract.py. This module owns the
assertions added by docs/superpowers/plans/2026-07-29-reader-rail-density.md.
"""

import os
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RENDER_FIXTURE = ROOT / "examples" / "courses" / "render-fixture"
DENSITY_FIXTURE = ROOT / "examples" / "courses" / "rail-density-fixture"


def _browser_executable() -> Path:
    # Local copy of the helper in test_rail_collapse_contract.py: a
    # cross-module `tests.e2e....` import does not resolve under pytest's
    # rootdir-relative import mode (no tests/__init__.py package).
    configured = os.environ.get("RAYA_TEST_BROWSER")
    if configured:
        path = Path(configured)
        if path.exists():
            return path
        pytest.fail(f"RAYA_TEST_BROWSER does not exist: {configured}")
    for name in (
        "chromium",
        "chromium-browser",
        "google-chrome-stable",
        "google-chrome",
    ):
        for prefix in ("/usr/bin", "/usr/local/bin", "/snap/bin"):
            candidate = Path(prefix) / name
            if candidate.exists():
                return candidate
    pytest.skip("no Chromium-compatible browser found")


def _preview(tmp_path: Path, fixture: Path = RENDER_FIXTURE):
    """Copy a fixture out of the repo and serve its built artifact."""
    from raya_cli.preview import create_preview

    course = tmp_path / fixture.name
    shutil.copytree(fixture, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    assert handle.report.ok, [
        diagnostic.format() for diagnostic in handle.report.diagnostics
    ]
    assert handle.base_url is not None
    return handle


_ZONES = """() => {
  const q = (s) => document.querySelector(s);
  const centre = (el) => {
    if (!el) return null;
    const b = el.getBoundingClientRect();
    if (b.height <= 2) return null;
    return {x: b.left + b.width / 2, y: b.top + b.height / 2};
  };
  return {
    header: centre(q('.raya-course-map-header')),
    tools: centre(q('.raya-course-rail-tools')),
    filter: centre(q('.raya-course-map-filter')),
    index: centre(q('.raya-course-map-list')),
  };
}"""

_SCROLL_STATE = """() => [
  document.querySelector('.raya-course-map-list').scrollTop,
  window.scrollY,
  document.querySelector('.raya-course-map').scrollTop,
]"""


def test_wheel_over_any_rail_region_moves_something(tmp_path: Path) -> None:
    """No region of the expanded course rail may swallow a wheel gesture.

    Regression: .raya-course-map carried overflow:auto AND
    overscroll-behavior:contain while never overflowing, so Chrome treated it
    as a scroll container with nowhere to put the delta. Wheeling over the
    header, the tools row, or the filter moved NOTHING -- not the rail, not
    the page -- which reads as "scrolling is broken".
    """
    from playwright.sync_api import sync_playwright

    handle = _preview(tmp_path)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(
                    f"{handle.base_url}/index.html", wait_until="networkidle"
                )
                page.wait_for_timeout(400)

                # Positive anchor: the rail is expanded and the tree rendered,
                # so a "nothing moved" result below is a real dead zone and not
                # an empty or collapsed rail where nothing could move anyway.
                assert page.locator(".raya-course-map-list a").count() >= 3
                assert page.locator("[data-raya-course-map-collapse]").count() == 1

                zones = page.evaluate(_ZONES)
                outcomes = {}
                for name in ("header", "tools", "filter", "index"):
                    point = zones[name]
                    assert point is not None, f"{name} zone not rendered"
                    page.evaluate(
                        """() => {
                          document.querySelector('.raya-course-map-list')
                            .scrollTop = 0;
                          document.querySelector('.raya-course-map')
                            .scrollTop = 0;
                          window.scrollTo(0, 0);
                        }"""
                    )
                    page.wait_for_timeout(120)
                    before = page.evaluate(_SCROLL_STATE)
                    page.mouse.move(point["x"], point["y"])
                    page.mouse.wheel(0, 400)
                    page.wait_for_timeout(300)
                    after = page.evaluate(_SCROLL_STATE)
                    if after[0] > before[0]:
                        outcomes[name] = "index"
                    elif after[2] > before[2]:
                        outcomes[name] = "frame"
                    elif after[1] > before[1]:
                        outcomes[name] = "page"
                    else:
                        outcomes[name] = "dead"

                assert "dead" not in outcomes.values(), outcomes
                # The index keeps its own contained scroll rather than
                # chaining to the document.
                assert outcomes["index"] == "index", outcomes
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run the test and confirm it fails (required red run)**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py::test_wheel_over_any_rail_region_moves_something -v`

Expected: FAIL on `assert "dead" not in outcomes.values()` with `outcomes` showing `{'header': 'dead', 'tools': 'dead', 'filter': 'dead', 'index': 'index'}`. Paste this output into the task report — it is the proof the bug exists.

- [ ] **Step 3: Delete the one declaration**

In `packages/static/src/raya_static/rendering.py`, the `.raya-course-map` rule currently reads:

```css
.raya-course-map {
  align-self: start;
  grid-area: course-map;
  max-height: calc(100vh - 2rem);
  overflow: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
}
```

Delete only the `overscroll-behavior: contain;` line, and add a comment recording why, so nobody restores it:

```css
.raya-course-map {
  align-self: start;
  grid-area: course-map;
  max-height: calc(100vh - 2rem);
  /* No overscroll-behavior here. The frame declares overflow:auto as a
     relief valve for enlarged root fonts, but normally scrollHeight ==
     clientHeight. Chrome still treats it as a scroll container, so
     `contain` swallowed every wheel gesture over the header, tools row and
     filter -- 41% of the rail where nothing moved. Containment belongs on
     .raya-course-map-list, which actually scrolls. */
  overflow: auto;
  scrollbar-gutter: stable;
}
```

Leave `overscroll-behavior: contain` on `.raya-course-map-list` untouched.

- [ ] **Step 4: Run the test and confirm it passes**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py::test_wheel_over_any_rail_region_moves_something -v`

Expected: PASS. `outcomes` is `{'header': 'page', 'tools': 'page', 'filter': 'page', 'index': 'index'}`.

- [ ] **Step 5: Confirm the drawer is unaffected**

The sub-640 drawer re-declares `overscroll-behavior` inside its `all: revert` block, so the deletion must not reach it.

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_mobile_course_map_drawer_is_modal_and_volatile -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/e2e/test_rail_density.py packages/static/src/raya_static/rendering.py
git commit -m "$(cat <<'MSG'
fix(rail): stop the course rail swallowing wheel gestures

.raya-course-map declared overflow:auto and overscroll-behavior:contain
while its scrollHeight equalled its clientHeight. Chrome still treats such
a box as a scroll container, and `contain` blocks chaining, so a wheel
event over the header (63px), the tools row (252.8px) or the filter (36px)
was captured and discarded -- 351.8px of an 868px rail, 41%, where neither
the rail nor the page moved.

Containment stays on .raya-course-map-list, which actually scrolls, so
index scrolling still does not chain into the document.

Measured before: header/tools/filter/index = dead/dead/dead/index.
Measured after:  header/tools/filter/index = page/page/page/index.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 2: Drop the scrollbar gutter from both rails, symmetrically

Both rail frames reserve a ~15px scrollbar gutter, so each rail's content box is 191px of its 240px. `scrollbar-gutter: stable` still reserves space even when the frame does not scroll, and the frame almost never scrolls. Dropping it from **both** rails buys 15px of content width per rail with no width change and no parity break.

This task exists separately because dropping it from the map alone breaks rail header **width** parity by 15px — the invariant a previous draft claimed to protect while proposing exactly that.

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py:4009` (`.raya-course-map`), `:4029` (`.raya-learning-rail`), `:6699` (band re-declaration on `.raya-course-map`)
- Test: `tests/e2e/test_rail_density.py`

**Interfaces:**
- Consumes: `_preview`, `_browser_executable` from Task 1.
- Produces: nothing new.

- [ ] **Step 1: Write the failing test**

Append to `tests/e2e/test_rail_density.py`:

```python
_HEADER_BOXES = """() => {
  const box = (sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {
      w: Math.round(r.width * 100) / 100,
      h: Math.round(r.height * 100) / 100,
      top: Math.round(r.top * 100) / 100,
      left: Math.round(r.left * 100) / 100,
      right: Math.round(r.right * 100) / 100,
    };
  };
  return {
    mapHeader: box('.raya-course-map-header'),
    railHeader: box('.raya-learning-rail-header'),
    map: box('.raya-course-map'),
    rail: box('.raya-learning-rail'),
  };
}"""


def test_both_rails_gain_content_width_without_breaking_parity(
    tmp_path: Path,
) -> None:
    """The gutter is dropped from BOTH rail frames or neither.

    scrollbar-gutter:stable reserves ~15px in each rail frame even when the
    frame never scrolls. Dropping it widens the content box from 191px to
    206px -- but dropping it from only one rail makes the two rail headers
    206px vs 191px, breaking the width and inset halves of the pinned
    outer-geometry parity contract.
    """
    from playwright.sync_api import sync_playwright

    handle = _preview(tmp_path)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                for width in (894, 1279, 1280, 1440):
                    page = browser.new_page(
                        viewport={"width": width, "height": 950}
                    )
                    page.goto(
                        f"{handle.base_url}/index.html",
                        wait_until="networkidle",
                    )
                    page.wait_for_timeout(400)
                    boxes = page.evaluate(_HEADER_BOXES)
                    map_header = boxes["mapHeader"]
                    rail_header = boxes["railHeader"]
                    assert map_header is not None and rail_header is not None

                    # Parity: width, height, top, and both insets.
                    assert abs(map_header["w"] - rail_header["w"]) <= 1, (
                        width,
                        boxes,
                    )
                    assert abs(map_header["h"] - rail_header["h"]) <= 1, (
                        width,
                        boxes,
                    )
                    assert abs(map_header["top"] - rail_header["top"]) <= 1, (
                        width,
                        boxes,
                    )
                    left_inset = map_header["left"] - boxes["map"]["left"]
                    right_inset = boxes["rail"]["right"] - rail_header["right"]
                    assert abs(left_inset - right_inset) <= 1, (width, boxes)

                    # Outcome: the gutter is gone, so each header is wider
                    # than the 191px it measured while the gutter was
                    # reserved.
                    assert map_header["w"] >= 200, (width, boxes)
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run the test and confirm it fails (required red run)**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py::test_both_rails_gain_content_width_without_breaking_parity -v`

Expected: **two** failures, both of which this task fixes.

1. `assert map_header["w"] >= 200` fails with `w` reported as `191`.
2. The **mirrored inset** assertion `abs(left_inset - right_inset) <= 1` fails
   by 15px, reporting 17 vs 32.

Failure 2 was mis-predicted in an earlier revision of this plan, which claimed
every parity assertion was baseline-green. Measured at 1440x950 on the shipped
code: map outer inset 17px, map **inner** inset **32px**, rail inner inset
17px, rail **outer** inset **32px**. `scrollbar-gutter: stable` reserves space
on each element's own inline-end (right) edge — which is the map's *inner*
(article-facing) side but the rail's *outer* (page-edge) side. The two rails
are therefore **not mirror-symmetric today**.

This is why the pinned invariant test does not catch it: it compares
*same-side* insets (`map.right - mapHeader.right` vs
`rail.right - railHeader.right`) — 32 vs 32, which matches. The mirrored
assertion here is deliberately stricter and is the better check; after the
gutter is removed from both frames all four insets become 17px, so both the
mirrored and the same-side comparisons pass.

The width/height/top parity assertions **are** baseline-green and must stay
green. If one of *those* fails on the red run, stop and report — that would be
unrelated breakage.

- [ ] **Step 3: Remove the gutter from both frames**

Three edits in `packages/static/src/raya_static/rendering.py`.

3a. `.raya-course-map` (base rule, as left by Task 1) — delete `scrollbar-gutter: stable;`:

```css
.raya-course-map {
  align-self: start;
  grid-area: course-map;
  max-height: calc(100vh - 2rem);
  /* No overscroll-behavior here. (See Task 1 comment.) */
  /* No scrollbar-gutter either: it reserved ~15px in a frame that almost
     never scrolls, costing 15px of label column. It is kept on
     .raya-course-map-list, the real scroller, so the tree's scrollbar does
     not shift labels. Must stay symmetric with .raya-learning-rail. */
  overflow: auto;
}
```

3b. `.raya-learning-rail` (base rule) — delete `scrollbar-gutter: stable;`, keeping everything else:

```css
.raya-learning-rail {
  align-content: start;
  align-self: start;
  grid-area: learning-rail;
  font-size: calc(1rem * var(--raya-reader-text-scale, 1));
  max-height: calc(100vh - 2rem);
  /* No scrollbar-gutter: symmetric with .raya-course-map. Both rail
     headers are sized through one shared rule, so an asymmetric gutter
     breaks header width parity by 15px. */
  overflow: auto;
  overscroll-behavior: contain;
}
```

3c. In the `@media (min-width: __RAYA_STRUCTURAL_PX__px)` band, the `.raya-course-map` rule re-declares the gutter. Delete that line too:

```css
  html[data-raya-course-map-drawer="closed"] .raya-course-map,
  .raya-course-map {
    display: flex;
    flex-direction: column;
    padding-inline: 0;
  }
```

Leave `scrollbar-gutter: stable` on `.raya-course-map-list` and add it to `.raya-learning-rail-body` in the band so the inner scrollers still avoid content shift:

```css
  .raya-learning-rail-body {
    flex: 1 1 auto;
    min-height: 0;
    overflow: auto;
    overscroll-behavior: contain;
    padding-inline: var(--raya-space-panel);
    scrollbar-gutter: stable;
  }
```

- [ ] **Step 4: Run the test and confirm it passes**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py::test_both_rails_gain_content_width_without_breaking_parity -v`

Expected: PASS, `mapHeader.w == railHeader.w == 206`.

- [ ] **Step 5: Run the pinned invariant test unchanged**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_rails_share_outer_geometry -v`

Expected: PASS with no edits to that test. If it fails, the gutter removal is asymmetric — revisit Step 3, do not edit the test.

- [ ] **Step 6: Commit**

```bash
git add packages/static/src/raya_static/rendering.py tests/e2e/test_rail_density.py
git commit -m "$(cat <<'MSG'
refactor(rail): drop the scrollbar gutter from both rail frames

scrollbar-gutter:stable reserved ~15px inside each 240px rail frame even
though the frames almost never scroll, costing 15px of label column on the
left and 15px of context width on the right. Removing it from both frames
widens each content box from 191px to 206px with no rail width change.

Symmetry is the whole point: both rail headers are sized through one shared
rule (rendering.py:4074-4084), so removing the gutter from only the course
map makes the headers 206px vs 191px and breaks the width and inset halves
of test_render_fixture_reader_rails_share_outer_geometry -- which a
height-only gate would have reported green.

The inner scrollers keep the gutter, so a tree scrollbar still does not
shift labels.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 3: Add a large-tree fixture

Density outcomes cannot be measured on `examples/courses/render-fixture`: it has 6 pages, its index measures 217px, and its map never reaches the `max-height` clamp, so flex never distributes leftover space. Tasks 7 and 12 need a tree comparable to the deployed 33-page docs site.

**Files:**
- Create: `examples/courses/rail-density-fixture/raya.yaml`
- Create: `examples/courses/rail-density-fixture/course/0_index.md` plus 30 nested pages
- Test: `tests/e2e/test_rail_density.py`

**Interfaces:**
- Consumes: `_preview`, `DENSITY_FIXTURE` from Task 1.
- Produces: `DENSITY_FIXTURE` usable as `_preview(tmp_path, DENSITY_FIXTURE)`. Tasks 7 and 12 rely on it rendering **at least 30 map links** with the current page auto-oriented into view, on a tree **3 levels deep**, and on it containing two specific labels: one long enough to exceed two clamped lines, and one 55-character unbroken identifier.

- [ ] **Step 1: Write the fixture generator and run it**

Create `scripts/generate-rail-density-fixture.py`:

```python
#!/usr/bin/env python3
"""Generate examples/courses/rail-density-fixture.

A 31-page, 3-level tree used to measure course-map density. The 6-page
render-fixture is too small: its map never reaches the rail's max-height
clamp, so the flex leftover distribution the density tests assert is never
exercised.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "courses" / "rail-density-fixture"
COURSE = FIXTURE / "course"

RAYA_YAML = """course_id: rail-density-fixture
title: Rail Density Fixture
description: Wide, deep tree for measuring course-map density.
language: en
source: course
artifact: artifact
hierarchy:
  levels:
    - key: unit
      label: Unit
    - key: section
      label: Section
    - key: topic
      label: Topic
"""

SECTIONS = [
    ("1_foundations", "Foundations"),
    ("2_representation", "Representation"),
    ("3_verification", "Verification"),
]
TOPICS = [
    ("1_orientation", "Orientation"),
    ("2_structure", "Structure And Ordering Rules"),
    ("3_review", "Review"),
]
# Deliberately long titles: the density tests need labels that exceed two
# clamped lines at 0.8125rem in a ~150px column.
LEAVES = [
    ("1_overview", "Overview Of Long Structural Titles"),
    ("2_details", "Detailed Requirements And Registration Constraints"),
    ("3_summary", "Summary"),
]


def write(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\ntitle: {title}\n---\n\n# {title}\n\n{body}\n",
        encoding="utf-8",
    )


def main() -> None:
    write(
        COURSE / "0_index.md",
        "Rail Density Fixture",
        "Root page for the rail density fixture.",
    )
    for s_dir, s_title in SECTIONS:
        write(
            COURSE / s_dir / "0_index.md",
            s_title,
            f"Section landing page for {s_title}.",
        )
        for t_dir, t_title in TOPICS:
            write(
                COURSE / s_dir / t_dir / "0_index.md",
                t_title,
                f"Topic landing page for {t_title}.",
            )
            for l_name, l_title in LEAVES:
                write(
                    COURSE / s_dir / t_dir / f"{l_name}.md",
                    l_title,
                    "Leaf page body.",
                )
    # One page whose title is a single unbroken 55-character identifier, so
    # the emergency overflow-wrap:break-word path stays covered.
    write(
        COURSE / "4_identifier.md",
        "ProjectionResidualsWithAnUnbrokenAuthorIdentifierXYZ",
        "Covers the unbreakable-token path.",
    )
    (FIXTURE / "raya.yaml").write_text(RAYA_YAML, encoding="utf-8")
    pages = sorted(COURSE.rglob("*.md"))
    print(f"wrote {len(pages)} pages under {COURSE}")


if __name__ == "__main__":
    main()
```

Run it:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run python scripts/generate-rail-density-fixture.py
```

Expected output: `wrote 32 pages under .../rail-density-fixture/course` (root + 3 sections + 9 topics + 27 leaves + 1 identifier page = 41; adjust the assertion in Step 2 to the number actually printed rather than assuming).

- [ ] **Step 2: Write the failing test**

Append to `tests/e2e/test_rail_density.py`:

```python
def test_density_fixture_renders_a_deep_wide_map(tmp_path: Path) -> None:
    """The density fixture must be big enough to exercise flex leftover.

    render-fixture has 6 pages; its map never reaches the rail's max-height
    clamp, so no density outcome is measurable on it.
    """
    from playwright.sync_api import sync_playwright

    handle = _preview(tmp_path, DENSITY_FIXTURE)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(
                    f"{handle.base_url}/index.html", wait_until="networkidle"
                )
                page.wait_for_timeout(500)
                # Expand every branch so the tree is fully realised.
                # Expand every branch. Every toggle is eagerly present in the
                # DOM at load (children are hidden by an ancestor `hidden`
                # attribute, not lazily created), so each click flips exactly
                # one element out of this LIVE aria-expanded="false" match
                # set. Indexing with `nth(i)` over a count taken before any
                # click goes stale one-for-one as the set shrinks and then
                # hangs for the full 30s Playwright timeout. Drain with
                # `.first` instead, re-querying after every click.
                toggles = page.locator(
                    '[data-raya-map-node-toggle][aria-expanded="false"]'
                )
                guard = 0
                while toggles.count() > 0 and guard < 200:
                    toggles.first.click()
                    guard += 1
                page.wait_for_timeout(200)
                # The guard must not silently mask a partially expanded tree.
                # `hidden` only suppresses rendering, so querySelectorAll
                # still sees unexpanded nodes -- link counts and depth read
                # the same with zero clicks as with a full drain. Only this
                # post-condition proves the drain completed.
                assert toggles.count() == 0, (
                    "guard exhausted before draining all node toggles"
                )

                stats = page.evaluate(
                    """() => {
                      const links = [...document.querySelectorAll(
                        '.raya-course-map-node-row a')];
                      const depths = links.map((a) => Number(
                        a.closest('[data-raya-map-depth]')
                          ?.dataset.rayaMapDepth ?? 0));
                      const map = document.querySelector('.raya-course-map');
                      return {
                        links: links.length,
                        maxDepth: Math.max(...depths),
                        mapHeight: Math.round(
                          map.getBoundingClientRect().height),
                        listScrollHeight: document.querySelector(
                          '.raya-course-map-list').scrollHeight,
                        viewportHeight: window.innerHeight,
                      };
                    }"""
                )
                assert stats["links"] >= 30, stats
                assert stats["maxDepth"] >= 3, stats
                # The rail must actually reach its max-height clamp, or flex
                # never distributes leftover space and density is untestable.
                assert stats["mapHeight"] >= stats["viewportHeight"] - 32, stats
                assert stats["listScrollHeight"] > 900, stats
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 3: Run the test and confirm it passes**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py::test_density_fixture_renders_a_deep_wide_map -v`

Expected: PASS. If `links` is below 30 or `maxDepth` below 3, the generator or the `hierarchy.levels` list is wrong — fix the fixture, not the assertion.

Note: this task's red run is the generator failing / fixture absent, which is inherent — the test cannot pass before Step 1 exists. Record `pytest` erroring on the missing fixture directory as the red evidence.

- [ ] **Step 4: Verify the fixture validates and builds through the CLI**

Run:
```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate examples/courses/rail-density-fixture
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/rail-density-fixture
```

Expected: both succeed with no diagnostics.

- [ ] **Step 5: Commit (excluding the generated artifact)**

```bash
git add scripts/generate-rail-density-fixture.py \
        examples/courses/rail-density-fixture/raya.yaml \
        examples/courses/rail-density-fixture/course \
        tests/e2e/test_rail_density.py
git status --short  # confirm no artifact/ paths are staged
git commit -m "$(cat <<'MSG'
test(rail): add a 3-level, 30+ page density fixture

Course-map density is unmeasurable on examples/courses/render-fixture: it
has 6 pages, its index measures 217px, and its map never reaches the rail's
max-height clamp, so the flex leftover distribution the density gates
assert is never exercised.

The new fixture is 3 levels deep with 30+ pages, includes titles long
enough to exceed two clamped lines, and includes one 55-character unbroken
identifier so the emergency overflow-wrap:break-word path stays covered.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 4: Command tiles four per row, one resting colour

The eight command tiles are the single largest block of fixed chrome at 252.8px. On desktop they already render as a caption under a glyph (`rendering.py:6749-6756`); only the column count and the glyph size need to change. The eight per-command hues encode nothing — active state is carried by `[aria-current="page"]` / `[aria-pressed="true"]` background and border, the `aria-pressed` attribute, and a live `aria-label`.

Labels stay visible. Icon-only was rejected: `data-raya-command-tooltip` is inert markup that no CSS or JS reads, and only five of the eight controls carry it at all.

**Rail visible captions are shortened so each fits one line at `0.75rem`.** Owner decision, 2026-07-29, after measurement showed no column count makes `OpenDyslexic` fit a 240px rail: at 4-up the tile is 57px, where 8-character words are already at the edge (`Schedule` clipped at 12px while `Practice` fit) and `OpenDyslexic` needs ~74px. The rejected alternatives were a 10px font plus mid-word wrapping — on the dyslexia control specifically — and 3-up, which costs 42px more and still clips `OpenDyslexic`.

Mapping, applied at the **rail call site only** (`builder.py:1305-1311`), never to the top-command-bar (`:1176`) or discovery (`:1421`) call sites: `OpenDyslexic` → `Font`, `Schedule` → `Plan`, and `Text size` → `Size` only if it wraps or clips. `Search`, `Graph`, `Practice`, `Tasks`, and `Context` are unchanged — measurement shows they fit.

**Accessible names do not change by default.** `aria-label="Toggle OpenDyslexic font"` and the rest stay as they are, so screen-reader output and voice control are unaffected. WCAG 2.5.3 Label in Name requires each visible caption to be contained in its accessible name: `Font` is contained in "Toggle OpenDyslexic font", and `Size` in "Text size". `Plan` is **not** contained in the Schedule control's current `aria-label` — for that one control, extend the `aria-label` so it contains the word `Plan` rather than reverting the caption.

`overflow-wrap` on `.raya-command-label` stays `normal` in the structural band. Mid-word breaking of captions is not acceptable; shortening the captions is what makes it unnecessary. The acceptance gate is therefore **not** a tools-row pixel budget but: every caption renders on one line, and no caption or tile reports `scrollWidth > clientWidth`.

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py:4230` (`grid-template-columns`), `:4260-4265` (`.raya-command-icon` size), per-command colour rules
- Modify: `packages/static/src/raya_static/accessibility.py:81-94` (`.raya-font-toggle` background)
- Modify: `tests/e2e/test_preview_static_read_path.py` — column-count and tile-size assertions
- Modify: `tests/contracts/test_static_builder.py:5950` — scope the grid-template assertion
- Test: `tests/e2e/test_rail_density.py`

**Interfaces:**
- Consumes: `_preview`, `_browser_executable` from Task 1.
- Produces: nothing new.

- [ ] **Step 1: Write the failing test**

Append to `tests/e2e/test_rail_density.py`:

```python
_COMMANDS = """() => {
  const list = document.querySelector('.raya-course-rail-command-list');
  const cs = getComputedStyle(list);
  const tiles = [...document.querySelectorAll('.raya-course-rail-command')];
  return {
    columns: cs.gridTemplateColumns.split(/\\s+/).filter(Boolean).length,
    toolsHeight: Math.round(
      document.querySelector('.raya-course-rail-tools')
        .getBoundingClientRect().height),
    tiles: tiles.map((t) => {
      const r = t.getBoundingClientRect();
      const label = t.querySelector('.raya-command-label');
      const lr = label ? label.getBoundingClientRect() : null;
      return {
        name: t.getAttribute('aria-label'),
        w: Math.round(r.width), h: Math.round(r.height),
        labelText: label ? label.textContent.trim() : null,
        labelVisible: !!(lr && lr.width > 8 && lr.height > 4),
        labelClipped: label
          ? label.scrollWidth > label.clientWidth + 1 : null,
        bg: getComputedStyle(t).backgroundColor,
        pressed: t.getAttribute('aria-pressed'),
        colour: getComputedStyle(t).color,
      };
    }),
  };
}"""


def test_command_tiles_render_four_per_row_with_visible_labels(
    tmp_path: Path,
) -> None:
    """Eight tiles, four per row, labels still visible and not clipped.

    Icon-only was rejected: data-raya-command-tooltip is inert markup that
    nothing reads, and three of the eight controls never carried it, so
    hiding labels would leave no visible name recovery.
    """
    from playwright.sync_api import sync_playwright

    handle = _preview(tmp_path)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(
                    f"{handle.base_url}/index.html", wait_until="networkidle"
                )
                page.wait_for_timeout(400)
                state = page.evaluate(_COMMANDS)

                assert len(state["tiles"]) == 8, state
                assert state["columns"] == 4, state
                # Two rows of four must cost far less than the 252.8px the
                # search form plus a 2x4 grid cost before.
                assert state["toolsHeight"] <= 170, state

                for tile in state["tiles"]:
                    assert tile["name"], tile
                    assert tile["w"] >= 40 and tile["h"] >= 40, tile
                    assert tile["labelVisible"] is True, tile
                    assert tile["labelClipped"] is False, tile

                # One resting colour: the eight hues carried no information.
                resting = {
                    t["colour"] for t in state["tiles"] if t["pressed"] != "true"
                }
                assert len(resting) == 1, resting

                # No tile may wear the "on" fill while reporting pressed=false.
                # .raya-font-toggle used to win on source order and render a
                # permanently false active state.
                unpressed_bgs = {
                    t["bg"] for t in state["tiles"] if t["pressed"] != "true"
                }
                assert len(unpressed_bgs) == 1, unpressed_bgs
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run the test and confirm it fails (required red run)**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py::test_command_tiles_render_four_per_row_with_visible_labels -v`

Expected: FAIL on `assert state["columns"] == 4` (actual `2`). After fixing columns it must also fail on `len(resting) == 1` (eight distinct colours) and `len(unpressed_bgs) == 1` (OpenDyslexic's `rgb(221, 244, 255)` against near-white siblings).

- [ ] **Step 3: Change the grid to four columns and enlarge the glyph**

In `packages/static/src/raya_static/rendering.py`:

```css
.raya-course-rail-command-list {
  display: grid;
  gap: 0.3125rem;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}
```

Raise the glyph so it reads at four-up width (was `0.9375rem`). Do **not** add `aspect-ratio: 1` — with `minmax(0, 1fr)` in a full-bleed 238px track that yields 52-56px squares:

```css
.raya-course-rail-command .raya-command-icon {
  background: color-mix(in srgb, currentColor 12%, transparent);
  border: 1px solid color-mix(in srgb, currentColor 28%, transparent);
  flex: 0 0 auto;
  height: 1.25rem;
  padding: 0.1rem;
  width: 1.25rem;
}
```

Give the tile a floor that satisfies WCAG 2.5.8 Target Size (Minimum, 24x24) with margin, inside the structural band next to the existing `.raya-course-rail-command` block:

```css
  .raya-course-rail-command {
    box-sizing: border-box;
    flex-direction: column;
    gap: 0.125rem;
    justify-content: center;
    min-height: 2.5rem;
    min-width: 0;
    overflow: hidden;
    padding: 0.25rem 0;
    text-align: center;
  }
```

- [ ] **Step 4: Flatten the per-command colours**

Find the per-command colour rules (`grep -n "raya-command-search\|raya-command-graph\|raya-command-practice" packages/static/src/raya_static/rendering.py`) and remove the `color:` declaration from each, so all tiles inherit `.raya-course-rail-command`'s `color: var(--raya-color-text)`. Leave hover, focus, and `[aria-pressed="true"]` / `[aria-current="page"]` treatments untouched — they are the only state indicators and must keep working.

- [ ] **Step 5: Stop `.raya-font-toggle` faking an active state**

In `packages/static/src/raya_static/accessibility.py`, `.raya-font-toggle` sets `background: var(--raya-color-accent-soft)` — the same fill that means `[aria-pressed="true"]` on sibling tiles — and wins on source order, so OpenDyslexic renders a permanently false "on" state. Scope the background away from rail tiles by adding this rule immediately after the `.raya-font-toggle` block:

```css
.raya-course-rail-command.raya-font-toggle[aria-pressed="false"] {{
  background: color-mix(in srgb, var(--raya-color-surface) 94%, var(--raya-color-page));
}}
```

Note the doubled braces: this file's CSS is inside a Python format string.

- [ ] **Step 6: Run the new test and confirm it passes**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py::test_command_tiles_render_four_per_row_with_visible_labels -v`

Expected: PASS.

- [ ] **Step 7: Update the existing column-count and tile-size assertions**

Each of these encodes the old two-column layout. Update the number, keep the intent, and add a one-line justification comment above each edit.

In `tests/e2e/test_preview_static_read_path.py`:
- `:10734-10735` — `visibleColumns == 2` becomes `== 4`; `visibleRows == 4` becomes `== 2`.
- `:10761-10768` — `command["width"] >= 64` becomes `>= 40`. Keep `height >= 28` and `labelWidth >= 24`.
- `:11055-11057` — `all(width >= 64 ...)` becomes `>= 40`.
- `:11559` and `:11738` — the row-wrap check compares `command_boxes[2]` against `command_boxes[0]`; with four columns the second row starts at index 4, so compare `command_boxes[4]` against `command_boxes[0]`.
- `:17888` — `visibleColumnCount == 2` becomes `== 4`.
- `:19207` and `:19467-19469` — `len(commandGridColumns.split()) == 2` becomes `== 4`.
- `:21704-21708` — the drawer band keeps two columns; run the test first and only change the expected width range if it actually moved.
- `:21060` — keep `labelsWithoutTextRoom == []`, and additionally assert per tile that `label.scrollWidth <= label.clientWidth + 1`, so a clipped caption fails rather than merely a narrow one.

In `tests/contracts/test_static_builder.py`:
- `:5950` asserts the literal `"grid-template-columns: repeat(2, minmax(0, 1fr))" in css`. This is **already tautological** — the same literal occurs at `rendering.py:1139`, `1144`, `3475`, and `4470`, so it passes no matter what the rail does. Do not merely retarget it to `repeat(4`. Scope it to the rail block:

```python
    # Scoped, not substring: the bare literal also appears in four unrelated
    # rules, so the old assertion passed regardless of the rail's layout.
    rail_block = re.search(
        r"\.raya-course-rail-command-list \{[^}]*\}", css, re.S
    )
    assert rail_block is not None
    assert "grid-template-columns: repeat(4, minmax(0, 1fr))" in rail_block.group(0)
```

- [ ] **Step 8: Run the updated existing tests**

Run:
```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/e2e/test_preview_static_read_path.py::test_reader_shell_command_rail_layout \
  tests/contracts/test_static_builder.py -k "rail_command or css_selectors" -v
```

(If a test name above does not exist, locate the owning test with `grep -n "visibleColumns" tests/e2e/test_preview_static_read_path.py` and run that one.)

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add packages/static/src/raya_static/rendering.py \
        packages/static/src/raya_static/accessibility.py \
        tests/e2e/test_rail_density.py \
        tests/e2e/test_preview_static_read_path.py \
        tests/contracts/test_static_builder.py
git commit -m "$(cat <<'MSG'
feat(rail): render command tiles four per row with one resting colour

The eight command tiles were the largest block of fixed rail chrome. They
already render as a caption under a glyph on desktop, so only the column
count and the glyph size change: two columns become four, and the icon goes
from 0.9375rem to 1.25rem so it still reads at four-up width.

Labels stay visible. Icon-only was rejected because
data-raya-command-tooltip is inert markup that no CSS or JS reads, and
three of the eight controls never carried it, so there would have been no
visible name recovery.

The eight per-command hues are flattened to one resting colour; they
encoded nothing, since active state comes from aria-current/aria-pressed
background and border plus a live aria-label.

Also fixes an adjacent defect: .raya-font-toggle set the same accent-soft
background that means aria-pressed=true on its siblings and won on source
order, so OpenDyslexic rendered a permanently false active state.

The contract assertion for the grid is now scoped to the rail rule. The old
substring check was tautological -- the same literal appears in four
unrelated rules and passed regardless of the rail's layout.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 5: Remove the duplicated page position from the rail

`Page N of M` renders twice on every reader page: once in the rail (`builder.py:2203`) and once as the Page brief `Position` fact (`builder.py:3610-3612`). Both are gated on the identical `_page_position()` predicate (`builder.py:1887-1891`), so whenever the rail would show it, the brief does. The rail copy costs 57.6px including its 32px of margins.

The phone drawer's own independent readout (`builder.py:2189`) is **not** removed.

**Files:**
- Modify: `packages/static/src/raya_static/builder.py:2203`
- Modify: `packages/static/src/raya_static/rendering.py:4123-4129` (now-dead `.raya-course-map > .raya-page-position` rule) and the band `margin-inline` list at `:6708`
- Modify: `tests/e2e/test_preview_static_read_path.py:12785`, `:19195-19199`, `:19297`, `:19422-19428`, `:15133-15135`
- Modify: `tests/contracts/test_static_builder.py:5208-5213`, `:5680`
- Test: `tests/e2e/test_rail_density.py`

**Interfaces:**
- Consumes: `_preview`, `_browser_executable` from Task 1.
- Produces: nothing new.

- [ ] **Step 1: Write the failing test**

Append to `tests/e2e/test_rail_density.py`:

```python
def test_page_position_lives_only_in_the_page_brief(tmp_path: Path) -> None:
    """Page N of M renders once, in the Page brief, not twice.

    The rail copy and the brief fact are gated on the same predicate, so the
    rail copy was pure duplication costing 57.6px of fixed chrome.
    """
    from playwright.sync_api import sync_playwright

    handle = _preview(tmp_path)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(
                    f"{handle.base_url}/index.html", wait_until="networkidle"
                )
                page.wait_for_timeout(400)

                # Positive anchor: the rail rendered, so a zero count below is
                # a real removal and not an empty page.
                assert page.locator("[data-raya-course-map-collapse]").count() == 1
                assert (
                    page.locator("#raya-course-map .raya-page-position").count()
                    == 0
                )
                # The information itself must survive, in the brief.
                brief = page.locator("#raya-article .raya-page-brief")
                assert brief.count() == 1
                assert "Page" in brief.inner_text()
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run the test and confirm it fails (required red run)**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py::test_page_position_lives_only_in_the_page_brief -v`

Expected: FAIL on the `.raya-page-position` count assertion (actual `1`).

- [ ] **Step 3: Remove the rail emitter**

In `packages/static/src/raya_static/builder.py`, read the block around `:2203` and delete the rail's `.raya-page-position` emission from the course-map body, leaving the drawer chrome emission at `:2189` intact. Then remove the now-unreachable `.raya-course-map > .raya-page-position` rule at `rendering.py:4123-4129` and drop `.raya-course-map-body > .raya-page-position,` from the band `margin-inline` list at `rendering.py:6708`.

- [ ] **Step 4: Run the test and confirm it passes**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py::test_page_position_lives_only_in_the_page_brief -v`

Expected: PASS.

- [ ] **Step 5: Fix the existing assertions — three of these ERROR rather than fail**

Handle these in order; the marked ones raise before any assertion runs, so a plain expected-value edit will not fix them.

In `tests/e2e/test_preview_static_read_path.py`:
- **`:19297`** — `const positionBox = position.getBoundingClientRect();` is unguarded inside `page.evaluate`, so the whole evaluate throws `TypeError` and the test errors. Remove the `position` probe and every field derived from it, not just the asserts.
- `:19195-19199` — delete `positionTop is not None`, `toolsBottom <= positionTop`, and `positionBottom <= filterLabelTop`. Replace with `toolsBottom <= filterLabelTop` so the surviving ordering contract (tools above the filter) is still enforced.
- `:19422-19428` — same ordering asserts downstream of the removed probe; apply the same replacement.
- `:12785` — `initial["pagePosition"] == "Page 3 of 7"` read the rail copy. Re-point the probe at the Page brief `Position` fact and keep the expected string.
- `:15133-15135` — asserts rail `innerText` contains reading position plus "previous"/"next". Reading position moves to the brief, and Task 10 collapses the reading-flow panel. Re-point: assert the Page brief contains the position string, and assert `.raya-article-sequence-top` contains "Previous" and "Next".

In `tests/contracts/test_static_builder.py`:
- **`:5208-5213`** — two `course_map_html.index('class="raya-page-position"')` calls raise `ValueError` on the missing substring. Delete both index lookups and the ordering asserts built on them; replace with an assertion that the rail body contains the filter and the tree in that order.
- **`:5680`** — `assert '<p class="raya-page-position">Page 1 of 3</p>' in html`. The test is named `..._renders_collapsible_shell_controls_and_page_position`. Re-point the assertion at the Page brief `Position` fact and rename the test to `..._renders_collapsible_shell_controls`.

- [ ] **Step 6: Also fix two already-tautological assertions rather than inheriting them**

- `tests/e2e/test_preview_static_read_path.py:21654-21656` and `:21699` assert `positionVisible is False` using the selector `#raya-course-map > .raya-course-map-header > .raya-page-position`, which **never matched any emitted markup** — the assertion has always been vacuous. Delete these assertions rather than leaving a green check that proves nothing.

- [ ] **Step 7: Run the affected tests**

Run:
```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py -k "page_position or shell_controls or rail_order" -v
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/e2e/test_rail_density.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add packages/static/src/raya_static/builder.py \
        packages/static/src/raya_static/rendering.py \
        tests/e2e/test_rail_density.py \
        tests/e2e/test_preview_static_read_path.py \
        tests/contracts/test_static_builder.py
git commit -m "$(cat <<'MSG'
refactor(rail): render page position once, in the Page brief

Page N of M rendered twice on every reader page: in the course rail and as
the Page brief Position fact. Both are gated on the identical
_page_position() predicate, so the rail copy could never show something the
brief did not -- it was pure duplication costing 57.6px of fixed chrome
including its 32px of margins.

The phone drawer keeps its own independent position readout.

Three existing assertions errored rather than failed and needed harness
edits, not expected-value edits: an unguarded getBoundingClientRect inside
page.evaluate, and two .index() lookups raising ValueError. Two further
assertions on a selector that never matched any emitted markup were
deleted rather than left as vacuous green checks.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 6: Shrink the filter and search controls

The filter label, filter input, and search form together cost 117.6px. They shrink; none is removed. Hiding the filter at short viewport heights was rejected: there is no `/` hotkey and no `mapFilter.focus()` anywhere in `shell.py`, so a hidden filter is reachable by nothing, which fails WCAG 1.4.4 Resize Text and 1.4.10 Reflow.

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py:5091-5106` (filter label, filter), `:4223-4226` (search input/submit sizing)
- Test: `tests/e2e/test_rail_density.py`

**Interfaces:**
- Consumes: `_preview`, `_browser_executable` from Task 1.
- Produces: nothing new.

- [ ] **Step 1: Write the failing test**

Append to `tests/e2e/test_rail_density.py`:

```python
@pytest.mark.parametrize("height", [900, 720, 600, 520, 480])
def test_filter_and_search_stay_present_and_focusable_at_every_height(
    tmp_path: Path, height: int
) -> None:
    """No viewport height may remove the filter or the search form.

    Hiding the filter at short heights was rejected: no / hotkey and no
    mapFilter.focus() exist, so a hidden filter is reachable by nothing --
    WCAG 1.4.4 and 1.4.10.
    """
    from playwright.sync_api import sync_playwright

    handle = _preview(tmp_path)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(
                    viewport={"width": 1440, "height": height}
                )
                page.goto(
                    f"{handle.base_url}/index.html", wait_until="networkidle"
                )
                page.wait_for_timeout(400)

                filter_input = page.locator(".raya-course-map-filter")
                assert filter_input.count() == 1, height
                assert filter_input.is_visible(), height
                filter_input.focus()
                assert page.evaluate(
                    "() => document.activeElement"
                    ".classList.contains('raya-course-map-filter')"
                ), height

                assert page.locator(".raya-course-rail-search").is_visible()
                assert page.locator(
                    ".raya-course-map-filter-label"
                ).is_visible(), height

                chrome = page.evaluate(
                    """() => {
                      const h = (s) => {
                        const el = document.querySelector(s);
                        return el
                          ? Math.round(el.getBoundingClientRect().height) : 0;
                      };
                      return h('.raya-course-map-filter-label')
                           + h('.raya-course-map-filter');
                    }"""
                )
                # Was 24.8 + 46.4 = 71.2px.
                assert chrome <= 52, (height, chrome)
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run the test and confirm it fails (required red run)**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest "tests/e2e/test_rail_density.py::test_filter_and_search_stay_present_and_focusable_at_every_height" -v`

Expected: FAIL on `assert chrome <= 52` (actual `71`) at every height. The presence and focus assertions pass before and after.

- [ ] **Step 3: Shrink the three controls**

In `packages/static/src/raya_static/rendering.py`:

```css
.raya-course-map-filter-label {
  color: var(--raya-color-muted);
  display: block;
  font-size: 0.72rem;
  font-weight: 700;
  margin-bottom: 0.15rem;
}
.raya-course-map-filter {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  font: inherit;
  margin-bottom: 0.25rem;
  min-height: 1.75rem;
  padding: 0.25rem 0.5rem;
  width: 100%;
}
```

```css
.raya-course-rail-search .raya-command-search-input,
.raya-course-rail-search .raya-command-search-submit {
  min-height: 2rem;
}
```

- [ ] **Step 4: Run the test and confirm it passes**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest "tests/e2e/test_rail_density.py::test_filter_and_search_stay_present_and_focusable_at_every_height" -v`

Expected: PASS at all five heights.

- [ ] **Step 5: Replace two tautological label assertions**

`tests/e2e/test_preview_static_read_path.py:19210` and `:19442` assert `filterLabelVisible is True`. This is a trap, not a check: `.raya-visually-hidden` is `position: absolute; width: 1px; height: 1px; clip-path: inset(50%)`, which still satisfies `getClientRects().length > 0`, `display != none`, non-zero width/height, and `visibility != hidden`. The assertion would pass even if the label were hidden.

Strengthen both to assert the label is genuinely painted:

```python
    # Not just "visible": the old check passed for a 1px clipped
    # .raya-visually-hidden box too. Assert real painted size.
    assert state["filterLabelWidth"] >= 40, state
    assert state["filterLabelHeight"] >= 10, state
    assert state["filterLabelClipPath"] in {"none", ""}, state
```

Add the three fields to that test's `page.evaluate` probe alongside the existing `filterLabelVisible` read.

- [ ] **Step 6: Run the affected tests**

Run:
```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/e2e/test_preview_static_read_path.py -k "filter_label or course_map_filter" -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add packages/static/src/raya_static/rendering.py \
        tests/e2e/test_rail_density.py \
        tests/e2e/test_preview_static_read_path.py
git commit -m "$(cat <<'MSG'
refactor(rail): shrink the filter and search controls without hiding them

The filter label, filter input, and search form cost 117.6px of fixed rail
chrome. All three shrink; none is removed.

Hiding the filter at short viewport heights was explicitly rejected: there
is no / hotkey and no mapFilter.focus() anywhere in shell.py, so a hidden
filter is reachable by nothing at all, which fails WCAG 1.4.4 Resize Text
and 1.4.10 Reflow. The new test asserts the filter is present, visible, and
focusable at 900, 720, 600, 520, and 480px viewport heights.

Two existing assertions on filter-label visibility were traps rather than
checks -- .raya-visually-hidden satisfies every condition they tested -- so
they now assert real painted size and no clip-path.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 7: Tighten the tree indent and label font

Per nesting level costs 22.6px: `margin-left: 0.7rem` (11.2px) + `padding-left: 0.65rem` (10.4px) + a 1px guide border, at `rendering.py:5045-5049`. At depth 3 that is 67.8px of a 191px column. The label font is 15px (`rendering.py:6571`).

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py:5045-5049` (indent), `:6571-6574` (band font size)
- Modify: `tests/e2e/test_preview_static_read_path.py:18906`, `:19693-19695`
- Test: `tests/e2e/test_rail_density.py`

**Interfaces:**
- Consumes: `_preview`, `_browser_executable`, `DENSITY_FIXTURE` from Tasks 1 and 3.
- Produces: nothing new.

- [ ] **Step 1: Write the failing test**

Append to `tests/e2e/test_rail_density.py`:

```python
_DEEP_LINK = """() => {
  const links = [...document.querySelectorAll('.raya-course-map-node-row a')]
    .filter((a) => a.getBoundingClientRect().width > 0);
  if (!links.length) return null;
  const withDepth = links.map((a) => ({
    a,
    depth: Number(
      a.closest('[data-raya-map-depth]')?.dataset.rayaMapDepth ?? 0),
  }));
  const maxDepth = Math.max(...withDepth.map((x) => x.depth));
  const deepest = withDepth.filter((x) => x.depth === maxDepth);
  const narrowest = deepest.reduce(
    (best, x) =>
      x.a.getBoundingClientRect().width < best.a.getBoundingClientRect().width
        ? x : best,
    deepest[0]);
  const cs = getComputedStyle(narrowest.a);
  const children = narrowest.a.closest('[data-raya-map-children]');
  const ccs = children ? getComputedStyle(children) : null;
  return {
    maxDepth,
    linkWidth: Math.round(narrowest.a.getBoundingClientRect().width),
    fontSize: cs.fontSize,
    overflowWrap: cs.overflowWrap,
    perLevel: ccs
      ? Math.round(
          (parseFloat(ccs.marginLeft) + parseFloat(ccs.paddingLeft)
            + parseFloat(ccs.borderLeftWidth)) * 10) / 10
      : null,
  };
}"""


def test_deep_map_labels_get_a_usable_text_column(tmp_path: Path) -> None:
    """Indent and font must leave a readable column at depth 3.

    Before: 22.6px per level and a 15px font left 103.2px at depth 3, so
    every one of 23 entries wrapped and the worst rendered 5 line boxes.
    """
    from playwright.sync_api import sync_playwright

    handle = _preview(tmp_path, DENSITY_FIXTURE)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(
                    f"{handle.base_url}/index.html", wait_until="networkidle"
                )
                page.wait_for_timeout(500)
                # Expand every branch. Every toggle is eagerly present in the
                # DOM at load (children are hidden by an ancestor `hidden`
                # attribute, not lazily created), so each click flips exactly
                # one element out of this LIVE aria-expanded="false" match
                # set. Indexing with `nth(i)` over a count taken before any
                # click goes stale one-for-one as the set shrinks and then
                # hangs for the full 30s Playwright timeout. Drain with
                # `.first` instead, re-querying after every click.
                toggles = page.locator(
                    '[data-raya-map-node-toggle][aria-expanded="false"]'
                )
                guard = 0
                while toggles.count() > 0 and guard < 200:
                    toggles.first.click()
                    guard += 1
                page.wait_for_timeout(200)
                # The guard must not silently mask a partially expanded tree.
                # `hidden` only suppresses rendering, so querySelectorAll
                # still sees unexpanded nodes -- link counts and depth read
                # the same with zero clicks as with a full drain. Only this
                # post-condition proves the drain completed.
                assert toggles.count() == 0, (
                    "guard exhausted before draining all node toggles"
                )

                state = page.evaluate(_DEEP_LINK)
                assert state is not None
                assert state["maxDepth"] >= 3, state
                assert state["perLevel"] <= 9, state
                assert state["fontSize"] == "13px", state
                assert state["linkWidth"] >= 140, state
                # The emergency break must survive: it is what keeps a
                # 55-character unbroken identifier inside the 240px rail.
                assert state["overflowWrap"] == "break-word", state
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run the test and confirm it fails (required red run)**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py::test_deep_map_labels_get_a_usable_text_column -v`

Expected: FAIL on `assert state["perLevel"] <= 9` (actual `22.6`).

- [ ] **Step 3: Tighten the indent**

In `packages/static/src/raya_static/rendering.py`:

```css
.raya-course-map [data-raya-map-children] {
  /* 8px per level, not 22.6px. At depth 3 the old margin+padding+border
     consumed 67.8px of a 191px column, which is why every label wrapped.
     The 1px guide border stays -- it is the only visual hierarchy cue left
     after the indent shrinks. */
  border-left: 1px solid var(--raya-color-border);
  margin-left: 0.4375rem;
  padding-left: 0;
}
```

- [ ] **Step 4: Drop the label font to 13px in the band**

In the 640-893 / structural band at `rendering.py:6571`:

```css
  .raya-course-map-list a {
    font-size: 0.8125rem;
    line-height: 1.3;
    padding: 0.24rem 0.28rem 0.24rem 0.35rem;
  }
```

This band governs both the 640-893 and >= 894 paths, so the density fix is not silently desktop-only.

- [ ] **Step 5: Run the test and confirm it passes**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py::test_deep_map_labels_get_a_usable_text_column -v`

Expected: PASS with `linkWidth` around 157 and `fontSize == "13px"`.

- [ ] **Step 6: Update the two affected existing assertions**

In `tests/e2e/test_preview_static_read_path.py`:
- `:18906` — `expanded["linkFontSize"] == "15px"` becomes `== "13px"`. Add a comment: the density change applies to the 640-893 band too, deliberately, so the fix is not desktop-only.
- `:19693-19695` — `assert any(len(link["textRects"]) > 1 for link in tree["links"])` asserts that *some* label wraps. That premise is removed by design: the wider column plus smaller font means fixture labels no longer wrap. Delete the assertion and replace it with the inverse contract, which is what now matters:

```python
    # Design inverts this: the column is wide enough that fixture labels no
    # longer need to wrap. Assert none exceeds the two-line clamp instead.
    for link in tree["links"]:
        assert link["renderedLines"] <= 2, link
```

Add a `renderedLines` field to that test's probe computed as `Math.round(a.clientHeight / parseFloat(getComputedStyle(a).lineHeight))` — not from `Range.getClientRects()`, which still reports the pre-clamp line count once Task 8 lands.

- [ ] **Step 7: Run the affected tests**

Run:
```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/e2e/test_preview_static_read_path.py -k "map_labels or expanded_map" -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add packages/static/src/raya_static/rendering.py \
        tests/e2e/test_rail_density.py \
        tests/e2e/test_preview_static_read_path.py
git commit -m "$(cat <<'MSG'
feat(rail): tighten tree indent to 8px and drop labels to 13px

Each nesting level cost 22.6px -- margin-left 0.7rem plus padding-left
0.65rem plus a 1px guide border -- so at depth 3 indentation alone consumed
67.8px of a 191px column, leaving 103.2px for text. Every one of the 23
expanded entries wrapped and the worst rendered 5 line boxes.

Indent is now 8px per level with the guide border retained, and the label
font drops from 15px to 13px in the structural band so the change covers
the 640-893 path as well as desktop rather than being silently
desktop-only.

overflow-wrap:break-word is deliberately kept on the anchor: it is the
emergency path that keeps a 55-character unbroken identifier inside the
240px rail.

One existing assertion required inverting rather than retargeting: it
asserted that some label wraps, which the wider column removes. It now
asserts no label exceeds two lines, measured as clientHeight/lineHeight
rather than by Range.getClientRects(), which reports pre-clamp line counts.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 8: Clamp labels to two lines and release the clamp on interaction

Long titles still need two lines at 240px. Beyond two, clamp with an ellipsis — and release the clamp on hover, focus, and the current row so nothing is permanently unreadable. A `title` attribute was rejected: it is not exposed to touch, is unreliable for keyboard-only users, and adds a redundant description announcement on all 30+ links.

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py:5117-5124` (`.raya-course-map-list a`)
- Modify: `tests/e2e/test_preview_static_read_path.py:17480`, `:17553`, `:19684-19691`
- Test: `tests/e2e/test_rail_density.py`

**Interfaces:**
- Consumes: `_preview`, `_browser_executable`, `DENSITY_FIXTURE` from Tasks 1 and 3.
- Produces: nothing new.

- [ ] **Step 1: Write the failing test**

Append to `tests/e2e/test_rail_density.py`:

```python
def test_long_labels_clamp_to_two_lines_and_release_on_focus(
    tmp_path: Path,
) -> None:
    """Clamped labels must be recoverable without a title attribute.

    title was rejected: not exposed on touch, unreliable for keyboard-only
    users, and a redundant description announcement on every link.
    """
    from playwright.sync_api import sync_playwright

    handle = _preview(tmp_path, DENSITY_FIXTURE)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(
                    f"{handle.base_url}/index.html", wait_until="networkidle"
                )
                page.wait_for_timeout(500)
                # Expand every branch. Every toggle is eagerly present in the
                # DOM at load (children are hidden by an ancestor `hidden`
                # attribute, not lazily created), so each click flips exactly
                # one element out of this LIVE aria-expanded="false" match
                # set. Indexing with `nth(i)` over a count taken before any
                # click goes stale one-for-one as the set shrinks and then
                # hangs for the full 30s Playwright timeout. Drain with
                # `.first` instead, re-querying after every click.
                toggles = page.locator(
                    '[data-raya-map-node-toggle][aria-expanded="false"]'
                )
                guard = 0
                while toggles.count() > 0 and guard < 200:
                    toggles.first.click()
                    guard += 1
                page.wait_for_timeout(200)
                # The guard must not silently mask a partially expanded tree.
                # `hidden` only suppresses rendering, so querySelectorAll
                # still sees unexpanded nodes -- link counts and depth read
                # the same with zero clicks as with a full drain. Only this
                # post-condition proves the drain completed.
                assert toggles.count() == 0, (
                    "guard exhausted before draining all node toggles"
                )

                # No map link carries a title attribute.
                assert page.evaluate(
                    """() => [...document.querySelectorAll(
                        '.raya-course-map-node-row a')]
                      .every((a) => !a.hasAttribute('title'))"""
                )

                # Every link renders at most two lines...
                lines = page.evaluate(
                    """() => [...document.querySelectorAll(
                        '.raya-course-map-node-row a')]
                      .filter((a) => a.getBoundingClientRect().width > 0)
                      .map((a) => Math.round(
                        a.clientHeight
                          / parseFloat(getComputedStyle(a).lineHeight)))"""
                )
                assert lines, "no visible map links"
                assert max(lines) <= 2, lines

                # ...and at least one is genuinely clamped, so the release
                # path below is actually exercised.
                clamped = page.evaluate(
                    """() => [...document.querySelectorAll(
                        '.raya-course-map-node-row a')]
                      .filter((a) => a.scrollHeight > a.clientHeight + 1)
                      .map((a) => a.textContent.trim())"""
                )
                assert clamped, "fixture has no label long enough to clamp"

                # Focus releases the clamp, reachable by keyboard alone.
                released = page.evaluate(
                    """(text) => {
                      const a = [...document.querySelectorAll(
                          '.raya-course-map-node-row a')]
                        .find((x) => x.textContent.trim() === text);
                      a.focus();
                      return {
                        active: document.activeElement === a,
                        fits: a.scrollHeight <= a.clientHeight + 1,
                      };
                    }""",
                    clamped[0],
                )
                assert released["active"] is True, released
                assert released["fits"] is True, released
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run the test and confirm it fails (required red run)**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py::test_long_labels_clamp_to_two_lines_and_release_on_focus -v`

Expected: FAIL on `assert clamped, "fixture has no label long enough to clamp"` — nothing clamps because no clamp exists yet.

- [ ] **Step 3: Add the clamp and its release**

In `packages/static/src/raya_static/rendering.py`:

```css
.raya-course-map-list a {
  border-left: 3px solid transparent;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  min-width: 0;
  overflow: hidden;
  /* break-word stays: emergency path for unbroken identifiers. */
  overflow-wrap: break-word;
  padding: 0.25rem 0 0.25rem 0.5rem;
  text-decoration: none;
}
/* Nothing is permanently unreadable: the clamp releases on pointer, on
   keyboard focus, and on the current page. A title attribute was rejected
   -- not exposed on touch, unreliable for keyboard users. */
.raya-course-map-list a:hover,
.raya-course-map-list a:focus-visible,
.raya-course-map-list a[aria-current="page"] {
  -webkit-line-clamp: unset;
}
```

- [ ] **Step 4: Run the test and confirm it passes**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py::test_long_labels_clamp_to_two_lines_and_release_on_focus -v`

Expected: PASS.

- [ ] **Step 5: Strengthen three assertions the clamp makes tautological**

The clamp silently converts these into restatements of the CSS. Fix them rather than leaving them green.

In `tests/e2e/test_preview_static_read_path.py`:
- `:17480` — `map_labels["currentLines"] <= 3.5` becomes unfalsifiable under a two-line clamp. Replace with `== 2` plus an assertion that the label's `scrollHeight > clientHeight` (it is genuinely clamped), so the check still describes an outcome.
- `:17553` — `linkRight <= mapRight` becomes tautological because `overflow: hidden` makes the border box unable to exceed its column regardless of wrapping. The test's real point is that a 55-character unbroken token cannot blow out the rail. Replace with: the link's `scrollWidth > clientWidth` (the token overflows its box), the link's right edge is inside the map, and computed `overflow-wrap` is still `break-word`.
- `:19684-19691` — the `"overflow"` field is derived from `listScrollWidth > listClientWidth + 1`, which `overflow-x: hidden` forces to equality. Delete the field and its assertion; horizontal containment is now covered by the `:17553` replacement.

- [ ] **Step 6: Run the affected tests**

Run:
```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/e2e/test_preview_static_read_path.py -k "labels_stay_scannable or unbroken" -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add packages/static/src/raya_static/rendering.py \
        tests/e2e/test_rail_density.py \
        tests/e2e/test_preview_static_read_path.py
git commit -m "$(cat <<'MSG'
feat(rail): clamp map labels to two lines, releasing on interaction

Long titles still need two lines in a 240px rail. Beyond two they now clamp
with an ellipsis, and the clamp releases on hover, on keyboard focus, and
on the current page, so no label is ever permanently unreadable.

A title attribute was rejected: it is not exposed to touch, is unreliable
for keyboard-only users, and would add a redundant description
announcement on every one of 30+ links. Releasing the clamp works for
keyboard (focus) and touch (tap focuses) alike. The accessible name is
unaffected either way -- -webkit-line-clamp is a visual clip, the text
nodes remain, so name-from-content yields the full string.

Three existing assertions became restatements of the new CSS and were
strengthened rather than left green: a <= 3.5 line check that a two-line
clamp makes unfalsifiable, a link-right-edge check that overflow:hidden
makes tautological, and a list horizontal-overflow field that overflow-x
forces to zero.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 9: Show the sequence badge on the current row only

The badge costs 42px of every row: `min-width: 1.45rem` + `margin-right: 0.45rem` + `0.35rem` padding each side. It carries the flat reading-order ordinal (`builder.py:2012-2014`) — a different fact from the label's hierarchical prefix, so it is not redundant and cannot simply be deleted.

Revealing it on `:hover` was rejected: measured, it grew rows from 25px to 48px, shifted every row below the pointer in a 30-row list, pushed the label past its own clamp exactly when the reader hovered to read it, failed WCAG 1.4.13 Dismissible, and was dead on touch.

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py:5125-5141` (`a::before`), `:6576-6582` (band `a::before`)
- Modify: `tests/e2e/test_preview_static_read_path.py:11060-11063`, `:19698-19701`
- Modify: `tests/contracts/test_static_builder.py:5928`
- Test: `tests/e2e/test_rail_density.py`

**Interfaces:**
- Consumes: `_preview`, `_browser_executable` from Task 1.
- Produces: nothing new.

- [ ] **Step 1: Write the failing test**

Append to `tests/e2e/test_rail_density.py`:

```python
def test_sequence_badge_shows_only_on_the_current_row(tmp_path: Path) -> None:
    """The badge is always visible where it matters, and never on hover.

    A hover reveal grew rows 25px -> 48px, shifted every row below the
    pointer, re-clamped the label being read, failed WCAG 1.4.13
    Dismissible, and was unreachable on touch.
    """
    from playwright.sync_api import sync_playwright

    handle = _preview(tmp_path)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(
                    f"{handle.base_url}/index.html", wait_until="networkidle"
                )
                page.wait_for_timeout(400)

                badges = page.evaluate(
                    """() => {
                      const links = [...document.querySelectorAll(
                        '.raya-course-map-node-row a')]
                        .filter((a) => a.getBoundingClientRect().width > 0);
                      return links.map((a) => ({
                        current: a.getAttribute('aria-current') === 'page',
                        display: getComputedStyle(a, '::before').display,
                        content: getComputedStyle(a, '::before').content,
                      }));
                    }"""
                )
                assert badges, "no visible map links"
                current = [b for b in badges if b["current"]]
                assert len(current) == 1, badges
                assert current[0]["display"] == "inline-flex", current[0]
                assert current[0]["content"] not in {"none", "normal"}, current[0]
                for badge in badges:
                    if not badge["current"]:
                        assert badge["display"] == "none", badge

                # Hovering a non-current row must not move anything.
                target = page.locator(
                    '.raya-course-map-node-row a:not([aria-current="page"])'
                ).first
                before = page.evaluate(
                    """() => ({
                      scrollH: document.querySelector(
                        '.raya-course-map-list').scrollHeight,
                    })"""
                )
                box = target.bounding_box()
                page.mouse.move(
                    box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
                )
                page.wait_for_timeout(200)
                after = page.evaluate(
                    """() => ({
                      scrollH: document.querySelector(
                        '.raya-course-map-list').scrollHeight,
                    })"""
                )
                assert after["scrollH"] == before["scrollH"], (before, after)
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run the test and confirm it fails (required red run)**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py::test_sequence_badge_shows_only_on_the_current_row -v`

Expected: FAIL on the non-current `display == "none"` assertion (actual `inline-flex` — the badge currently shows on every row).

- [ ] **Step 3: Restrict the badge to the current row, out of flow**

In `packages/static/src/raya_static/rendering.py`, keep the base `a::before` rule so `tests/contracts/test_static_builder.py:5928`'s required-selector check still finds the literal `.raya-course-map-list a::before`, and add `display: none` to it:

```css
.raya-course-map-list a::before {
  align-items: center;
  background: color-mix(in srgb, var(--raya-color-accent-soft) 74%, var(--raya-color-surface));
  border: 1px solid color-mix(in srgb, var(--raya-color-accent) 42%, var(--raya-color-border));
  border-radius: 999px;
  color: var(--raya-color-muted);
  content: attr(data-raya-map-index);
  /* Hidden at rest: 42px per row of a ~150px column, on 30+ rows, for the
     reading-order ordinal. Shown on the current row only -- always, never
     on hover, because a hover reveal reflows the row being read. */
  display: none;
  flex: 0 0 auto;
  font-size: 0.7rem;
  font-weight: 900;
  justify-content: center;
  line-height: 1;
  min-width: 1.45rem;
  padding: 0.22rem 0.35rem;
}
.raya-course-map-list a[aria-current="page"] {
  padding-left: 1.625rem;
  position: relative;
}
.raya-course-map-list a[aria-current="page"]::before {
  display: inline-flex;
  left: 0;
  margin-right: 0;
  position: absolute;
  top: 0.25rem;
}
```

Note `margin-right` is dropped from the base rule (it only mattered for in-flow badges) and the current-row badge is absolutely positioned, so it cannot become a block child inside the `-webkit-box` from Task 8.

In the band rule at `rendering.py:6576`, remove `margin-right` and keep only the size tweaks:

```css
  .raya-course-map-list a::before {
    font-size: 0.64rem;
    min-width: 1.3rem;
    padding: 0.18rem 0.3rem;
  }
```

- [ ] **Step 4: Run the test and confirm it passes**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py::test_sequence_badge_shows_only_on_the_current_row -v`

Expected: PASS.

- [ ] **Step 5: Update the two affected existing assertions**

In `tests/e2e/test_preview_static_read_path.py`:
- `:11060-11063` — `metrics["mapNumberDisplay"] in {"inline-flex", "flex"}` reads the badge at rest on an arbitrary link. Re-point the probe at the `[aria-current="page"]` link and keep the assertion; add a companion assertion that a non-current link reports `"none"`. Also re-point `:11059` (`mapNumber == f'"{mapIndex}"'`) at the current link, since computed `content` for a `display: none` pseudo-element is engine-dependent.
- `:19698-19701` — `problems == {1440: {"clipped": [], ...}, 894: {...}}` is built from a `badgeClearance` derivation (`:19625-19633`) that adds the badge's `minWidth`, `padding`, `border`, and `marginRight` to `linkLeft`. With the badge out of flow on all but one row, every link's first text rect now starts left of that clearance, so `clipped` fills with every link. Delete the `badgeClearance` derivation and the `rect.left < badgeClearance - 1` condition at `:19666-19670`; keep the right-edge clipping check, which still means something.

- [ ] **Step 6: Run the affected tests**

Run:
```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/e2e/test_preview_static_read_path.py -k "map_number or map_tree_clip" -v
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py -k "css_selectors" -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add packages/static/src/raya_static/rendering.py \
        tests/e2e/test_rail_density.py \
        tests/e2e/test_preview_static_read_path.py
git commit -m "$(cat <<'MSG'
feat(rail): show the sequence badge on the current row only

The badge cost 42px of every row -- min-width 1.45rem plus margin-right
0.45rem plus 0.35rem padding each side -- across 30+ rows of a ~150px
column. It is not redundant with the label: the badge is the flat
reading-order ordinal while the label prefix is the hierarchical address,
so it could not simply be deleted.

It now renders on the [aria-current="page"] row only, always visible and
absolutely positioned so it cannot become a block child inside the
two-line -webkit-box clamp. One row of 30+ pays 26px.

A hover reveal was measured and rejected: it grew rows from 25px to 48px,
shifted every row below the pointer, pushed the label past its own clamp
exactly when the reader hovered to read it, failed WCAG 1.4.13 Dismissible,
and was dead on touch.

An existing badgeClearance derivation assumed an in-flow badge on every row
and would have reported every link as clipped; it is removed, keeping the
right-edge clipping check that still means something.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 10: Collapse the three non-contents right-rail panels

All four right-rail panels ship `expanded=True`, totalling 1358.3px in a 767px window. "On this page" stays open — it owns the live reading-position region (`shell.py:1782-1828`). The other three collapse through the **existing** mechanism: `builder.py:2334-2375` already emits `data-raya-rail-panel-state`, `<h2><button aria-expanded>`, and `inert` + `aria-hidden` on collapsed bodies, driven by `shell.py:1134-1152` and animated at `rendering.py:4421-4456`. Native `<details>` was rejected — it would delete three `<h2>` headings from the outline and re-implement a shipped compliant mechanism.

Collapsing them hides no unique navigation: prev/next is duplicated in three places including `.raya-article-sequence-top`, prerequisites appear in the Page brief, and connections are duplicated by `.raya-article-connections` through the same renderer and emptiness guard.

**Files:**
- Modify: `packages/static/src/raya_static/builder.py:2882`, `:2938`, `:2968`
- Modify: `packages/static/src/raya_static/rendering.py:4027` (`.raya-learning-rail` overflow), `:4130-4133` (`.raya-learning-rail-body` display), `:4159-4163` (transition display), `:4452-4456` (collapsed body `content-visibility`)
- Modify: `tests/e2e/test_preview_static_read_path.py` — the panel-state and first-viewport assertions listed in Step 6
- Modify: `tests/contracts/test_static_builder.py` — `:5155`, `:5162`, `:5361-5382`, `:5406-5414`, `:5505-5512`, `:5851-5886`
- Test: `tests/e2e/test_rail_density.py`

**Interfaces:**
- Consumes: `_preview`, `_browser_executable` from Task 1.
- Produces: nothing new.

- [ ] **Step 1: Write the failing test**

Append to `tests/e2e/test_rail_density.py`:

```python
def test_right_rail_opens_contents_and_collapses_the_rest(
    tmp_path: Path,
) -> None:
    """One open panel, three collapsed and inert, headings intact.

    Native <details> was rejected: it would delete three <h2> headings from
    the outline and re-implement the shipped inert disclosure mechanism.
    """
    from playwright.sync_api import sync_playwright

    handle = _preview(tmp_path)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(
                    f"{handle.base_url}/index.html", wait_until="networkidle"
                )
                page.wait_for_timeout(400)

                panels = page.evaluate(
                    """() => [...document.querySelectorAll('.raya-rail-panel')]
                      .map((p) => {
                        const toggle = p.querySelector('[data-raya-rail-toggle]');
                        const body = p.querySelector('.raya-rail-panel-body');
                        return {
                          cls: p.className,
                          state: p.dataset.rayaRailPanelState,
                          expanded: toggle
                            ? toggle.getAttribute('aria-expanded') : null,
                          ariaHidden: body
                            ? body.getAttribute('aria-hidden') : null,
                          inert: body ? body.hasAttribute('inert') : null,
                          headingTag: toggle
                            ? toggle.parentElement.tagName : null,
                          contentVisibility: body
                            ? getComputedStyle(body).contentVisibility : null,
                        };
                      })"""
                )
                assert len(panels) == 4, panels
                open_panels = [p for p in panels if p["state"] == "expanded"]
                assert len(open_panels) == 1, panels
                assert "raya-page-contents" in open_panels[0]["cls"], panels

                for panel in panels:
                    # The h2 > button disclosure survives on every panel.
                    assert panel["headingTag"] == "H2", panel
                    if panel["state"] == "expanded":
                        continue
                    assert panel["expanded"] == "false", panel
                    assert panel["ariaHidden"] == "true", panel
                    assert panel["inert"] is True, panel
                    # Find-in-page must not reach invisible text.
                    assert panel["contentVisibility"] == "hidden", panel

                # Exactly one scroller inside the right rail.
                scrollers = page.evaluate(
                    """() => {
                      const out = [];
                      let el = document.querySelector('.raya-page-contents');
                      while (el && el !== document.documentElement) {
                        const cs = getComputedStyle(el);
                        if (/auto|scroll/.test(cs.overflowY)) {
                          out.push(el.className || el.tagName);
                        }
                        el = el.parentElement;
                      }
                      return out;
                    }"""
                )
                assert len(scrollers) == 1, scrollers
                assert "raya-learning-rail-body" in scrollers[0], scrollers

                # A collapsed panel opens on its existing toggle.
                flow = page.locator(".raya-page-reading-flow")
                flow.locator("[data-raya-rail-toggle]").click()
                page.wait_for_timeout(300)
                assert flow.get_attribute("data-raya-rail-panel-state") == (
                    "expanded"
                )
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run the test and confirm it fails (required red run)**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py::test_right_rail_opens_contents_and_collapses_the_rest -v`

Expected: FAIL on `assert len(open_panels) == 1` (actual `4`).

- [ ] **Step 3: Flip the three flags**

In `packages/static/src/raya_static/builder.py`, change `expanded=True` to `expanded=False` at exactly three call sites, leaving `:2765` ("On this page") expanded:

- `:2882` — the `_render_rail_panel("raya-page-context", "Page context", ...)` call
- `:2938` — the `_render_rail_panel("raya-page-reading-flow", "Reading flow", ...)` call
- `:2968` — `return _render_linked_pages_rail(page, page_graph_context, expanded=True)` becomes `expanded=False`

- [ ] **Step 4: Make the rail body the single scroller and fix the transition mode**

In `packages/static/src/raya_static/rendering.py`:

`.raya-learning-rail` — remove `overflow: auto` and `overscroll-behavior: contain` (its body owns both), and make it a flex column. Combined with Task 2's gutter removal the rule becomes:

```css
.raya-learning-rail {
  align-content: start;
  align-self: start;
  display: flex;
  flex-direction: column;
  grid-area: learning-rail;
  font-size: calc(1rem * var(--raya-reader-text-scale, 1));
  max-height: calc(100vh - 2rem);
  /* No overflow here: .raya-learning-rail-body is the rail's single
     scroller. Two nested scrollers meant the frame took over at short
     heights. No scrollbar-gutter either -- symmetric with
     .raya-course-map. */
  overflow: hidden;
}
```

`.raya-learning-rail-body` base rule — `display: grid` becomes `display: flex; flex-direction: column`, so the settled layout matches the band:

```css
.raya-learning-rail-body {
  display: flex;
  flex-direction: column;
  gap: 0;
}
```

The expand-transition rule at `:4159-4163` re-declares `display: grid` and must match, or settled and mid-transition layout modes diverge:

```css
[data-raya-learning-rail="expanded"] .raya-learning-rail[data-raya-learning-rail-transition="expanding"] .raya-learning-rail-body {
  display: flex;
  flex-direction: column;
  pointer-events: none;
  visibility: hidden;
}
```

Add `content-visibility: hidden` to the collapsed panel body rule at `:4452-4456` so find-in-page cannot scroll to invisible text — a pre-existing gap, since the `0fr` + `opacity: 0` collapse sets no `overflow: hidden`:

```css
.raya-rail-panel[data-raya-rail-panel-state="collapsed"] .raya-rail-panel-body {
  content-visibility: hidden;
  grid-template-rows: 0fr;
  opacity: 0;
}
```

(Match the existing selector exactly — read `:4448-4456` before editing.)

- [ ] **Step 5: Run the test and confirm it passes**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py::test_right_rail_opens_contents_and_collapses_the_rest -v`

Expected: PASS.

- [ ] **Step 6: Re-point the existing assertions**

Two of these encode requirements the change appears to invert. Both are **re-pointed to the surface that now carries the intent** — no panel is kept open to satisfy a test.

In `tests/e2e/test_preview_static_read_path.py`:
- `:20183` `test_render_fixture_reading_flow_panel_is_visible_in_first_viewport`, asserts at `:20275-20278` that the rail's prev/next are `>40x32` in the first viewport. Its intent — prev/next reachable without scrolling — is satisfied by `_render_article_sequence_nav`, which `builder.py:1052` inserts as the **first child of `<article>`, above the breadcrumbs**. Re-point the probe at `.raya-article-sequence-top`, keep the `>40x32` and first-viewport bounds, and rename the test to `test_render_fixture_reading_flow_is_reachable_in_first_viewport`. Do not delete the bounds.
- `:15133-15135` — handled in Task 5 Step 5.
- `:14165`, `:14197-14203`, `:14228-14232` — these click `[data-raya-rail-toggle]` and assert collapsed then expanded state. The mechanism is unchanged, so only the **starting** state moves: the panel now begins collapsed. Invert the sequence (assert collapsed, click, assert expanded) rather than deleting.
- `:14727-14733` — `initial == {"state": "expanded", ...}` becomes `"collapsed"`, `"false"`, `"true"`.
- `:14768-14776`, `:14823-14826` — the nested `.raya-connection-preview-rail summary` now sits inside a collapsed outer panel and is not visible. Open the outer panel via its `[data-raya-rail-toggle]` first, then run the existing assertions unchanged.
- `:15120-15131` — the four-title list still holds (all four panels exist); `all(p["expanded"] == "true")` becomes "contents expanded, other three collapsed". Do not weaken it to a one-element set-equality.
- `:20069-20070` (`"Summary" in railText`), `:20272-20301` — `innerText` omits collapsed content. Re-point the text assertions at the panels' `textContent`, or open the panel first, whichever preserves the original intent. Note `:20299-20301` (`graphHref`, `"Graph" in text`) **still passes** while proving nothing about visibility — strengthen it to require the panel be open.
- `:19889` — `expanding["bodyDisplay"] == "grid"` becomes `== "flex"`, matching Step 4.
- `:12295` — `getComputedStyle(document.querySelector('.raya-rail-panel-body'))` is unguarded; keep it safe by asserting the element exists first.
- `:17595-17634` — set-equality over `.raya-rail-panel-body-inner` values. Ensure the probe still collects all four panels (query all, not just visible), so the set does not silently shrink to one element.

In `tests/contracts/test_static_builder.py`:
- `:6961` helper `_section_html` asserts a `<section class="raya-rail-panel {class}"[^>]*>` match. The element is unchanged by this design, so the helper needs **no** change — verify that by running its callers (`:5217`, `:5222`, `:5361`, `:5374`, `:5510`, `:5851`, `:5880`) before editing anything.
- `:5155`, `:5162` — `'aria-expanded="true">Page context</button>'` becomes `"false"`.
- `:5361-5382`, `:5851-5854`, `:5880-5886` — panel-state / `aria-expanded` / `aria-hidden` substrings flip from expanded to collapsed for the three panels.
- `:5406-5414`, `:5505-5512` — `html.index(...)` ordering lookups. The sections still exist, so these should pass unchanged; run them first. Note `:5506` is **already tautological** — the emitted class is `raya-page-contents raya-page-current-section`, so `raya-page-contents"` with a trailing quote never matches. Fix that lookup to `raya-page-contents ` (trailing space) so the ordering check actually runs.

- [ ] **Step 7: Run the affected tests**

Run:
```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py -k "rail_panel or reading_flow or page_context or linked_pages or without_toc" -v
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/e2e/test_preview_static_read_path.py -k "rail_panel or reading_flow or connections" -v
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add packages/static/src/raya_static/builder.py \
        packages/static/src/raya_static/rendering.py \
        tests/e2e/test_rail_density.py \
        tests/e2e/test_preview_static_read_path.py \
        tests/contracts/test_static_builder.py
git commit -m "$(cat <<'MSG'
feat(rail): collapse the three non-contents learning-rail panels

All four right-rail panels shipped expanded=True, totalling 1358.3px of
content in a 767px window, so the table of contents -- the only panel with
live reading-position tracking -- was displaced by three panels the reader
consults rarely.

"On this page" stays open. The other three collapse through the mechanism
that already ships: data-raya-rail-panel-state, h2 > button with
aria-expanded, and inert plus aria-hidden on collapsed bodies. Native
<details> was rejected because it would have deleted three h2 headings from
the document outline and re-implemented a compliant mechanism for nothing.

Collapsing them hides no unique navigation path: prev/next is duplicated in
three places including .raya-article-sequence-top, prerequisites appear in
the Page brief, and connections are duplicated by .raya-article-connections
through the same renderer and the same emptiness guard.

Also fixes the rail's own nested scroller -- .raya-learning-rail and
.raya-learning-rail-body both declared overflow:auto -- and aligns the
expand-transition display mode with the settled one so the two cannot
diverge. Collapsed bodies gain content-visibility:hidden, closing a
pre-existing gap where find-in-page could scroll to invisible text.

Two tests encoding requirements this appears to invert were re-pointed at
the surface that now carries the intent, keeping their bounds, rather than
holding a panel open to satisfy them.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 11: Amend the contract and the role documentation

`docs/foundation/` is seed truth and currently mandates the exact composition this work changes. Two tests pin the contract sentences verbatim, and four role guides state the old composition as fact.

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md` at `:25`, `:27`, `:33`, `:35`, and `## Verification`
- Modify: `docs/guides/en/students/index.md:51`, `:74`
- Modify: `docs/guides/es/estudiantes/index.md:52`, `:75`
- Modify: `docs/guides/en/agents/index.md:144`, `:166`
- Modify: `docs/guides/es/agentes/index.md:155`, `:178-179`
- Modify: `tests/contracts/test_static_builder.py:4909`
- Modify: `tests/contracts/test_documentation_surfaces.py:378-403`

**Interfaces:**
- Consumes: nothing.
- Produces: nothing.

- [ ] **Step 1: Run the two gates and confirm they fail (required red run)**

Run:
```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py::test_reader_shell_guidance_matches_left_rail_contract \
  tests/contracts/test_documentation_surfaces.py -k "reader_rail_visual_parity" -v
```

Expected: these should be **passing** right now (the contract still describes the old rail). Record that. They must fail after Step 2 and pass again after Step 4 — that ordering is the proof the gate is real.

- [ ] **Step 2: Amend the contract**

In `docs/foundation/20_learning_renderer_contract.md`:

2a. `:25` — in "Its body contains course search, then exactly eight compact icon-labeled command tiles rendered two per row for Search, Graph, Practice, Tasks, Schedule, Context, Text size, and OpenDyslexic, followed by structural page position, the locally filterable hierarchical map, and its scrollable course tree":
- "rendered two per row" becomes "rendered four per row"
- delete "structural page position," so it reads "followed by the locally filterable hierarchical map, and its scrollable course tree"
- keep "course search", "exactly eight", "icon-labeled", and the command names unchanged

Also add, because Task 4 shortens three visible rail captions (`Schedule` → `Plan`, `Text size` → `Size` if needed, `OpenDyslexic` → `Font`) while leaving command identities intact: "The rail may render shortened visible captions for these controls provided each caption remains contained in its accessible name; the eight command identities and their accessible names are unchanged." Keep the enumeration itself in canonical command names so the contract still identifies all eight.

Then add, in the same paragraph: "The rail may omit structural page position from its body when the article Page brief already renders it. The left course rail owns exactly one scrolling region — its course tree — with the rail frame fixed at accepted reader heights."

2b. `:33` — the table row uses semicolons, so it needs its own edits: "rendered two per row" becomes "rendered four per row", and "structural page position;" is deleted. Keep "with course search".

2c. `:27` — add: "At structural reader widths the right learning rail may render its non-contents panels collapsed by default through the documented inert disclosure mechanism, keeping their headings in the document outline. This does not relax the phone-parity rule above: phone layouts keep the rail body visually and accessibly available."

2d. `:35` — add that reading flow and page context may render collapsed by default, using the contract's own noun for the open panel ("current article section and page contents").

2e. `## Verification` — add these four checks:
- each rail owns exactly one scrolling region at accepted reader heights;
- a wheel gesture anywhere over an expanded rail scrolls that rail's scroller or the page, never nothing;
- rail header parity covers width, height, top, and both insets;
- map labels clamp to at most two lines and release the clamp on interaction and on the current page.

- [ ] **Step 3: Confirm the gates now fail**

Run the same command as Step 1. Expected: `test_reader_shell_guidance_matches_left_rail_contract` FAILS because `:4909` still pins the literal "course search, then exactly eight compact icon-labeled command tiles rendered two per row".

- [ ] **Step 4: Update the two gates and the four role guides**

4a. `tests/contracts/test_static_builder.py:4909` — update the pinned literal to "course search, then exactly eight compact icon-labeled command tiles rendered four per row".

4b. `tests/contracts/test_documentation_surfaces.py:378-403` — update whatever strings it binds so the contract and the four guides agree.

4c. The eight role-doc locations. English and Spanish stay separate; control names, class names, and paths stay in English. Only the two-per-row wording and the rail page position change — the `course search` mentions stay correct, and the literal `course search` must survive because `tests/contracts/test_static_builder.py:4945` and `:4969` assert it.
- `docs/guides/en/students/index.md:51` — "arranged two per row" becomes "arranged four per row"; drop "followed by page position and".
- `docs/guides/en/students/index.md:74` — "compact two-per-row command tiles" becomes "compact four-per-row command tiles".
- `docs/guides/es/estudiantes/index.md:52`, `:75` — mirror both, in Spanish, keeping `course search` and control names in English.
- `docs/guides/en/agents/index.md:144` — "Verify `.raya-course-map-body` owns search, the ordered … command tiles, position, filter, and tree" — remove `position` from the list of children.
- `docs/guides/en/agents/index.md:166` — "compact two-per-row command tiles" becomes "four-per-row".
- `docs/guides/es/agentes/index.md:155`, `:178-179` — mirror both.

4d. State in the commit body, per `docs/foundation/16_documentation_surfaces.md:24`, that the professors, profesores, contributors, and colaboradores guides need no change because their page-position mentions are Page-brief scoped, and that `docs/guides/en/students/index.md:94` / `docs/guides/es/estudiantes/index.md:97` need no change because the drawer keeps its own position readout.

- [ ] **Step 5: Confirm the gates pass again**

Run the Step 1 command. Expected: PASS.

- [ ] **Step 6: Run the documentation surface suite**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_documentation_surfaces.py -v`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add docs/foundation/20_learning_renderer_contract.md docs/guides \
        tests/contracts/test_static_builder.py \
        tests/contracts/test_documentation_surfaces.py
git commit -m "$(cat <<'MSG'
docs(foundation): amend the reader rail contract for four-per-row tiles

The contract mandated the exact composition that caused the density defect:
eight icon-labeled command tiles "rendered two per row" plus structural
page position in the rail body. Both clauses are amended at :25 and :33 --
the table row needed its own edit because it uses semicolons, so a single
find-and-replace would have left it still mandating page position.

Also states that the right learning rail may render its non-contents panels
collapsed by default through the documented inert mechanism, scoped so it
does not relax the phone-parity rule, and adds four Verification checks:
one scroller per rail, wheel gestures never dead, header parity across
width/height/top/both insets, and two-line label clamping that releases on
interaction.

Unchanged and deliberately so: "course search" stays mandated because the
inline form is kept -- it is a type-and-go query handoff that the Search
command control cannot replicate; "exactly eight" and "icon-labeled" stay
because labels remain visible; and no geometry literal is introduced, so
the single-source geometry invariant is not engaged.

Role docs: four guides updated in eight places, English and Spanish kept
separate. No change needed for professors/profesores/contributors/
colaboradores -- their page-position mentions are Page-brief scoped -- nor
for the students' drawer description, since the drawer keeps its own
position readout.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 12: Density gate, drawer regression, full suite, deploy

The outcome gate. Everything before this was mechanism; this proves the reader actually gained something and that nothing below 640px moved.

**Files:**
- Test: `tests/e2e/test_rail_density.py`

**Interfaces:**
- Consumes: everything from Tasks 1-11.
- Produces: nothing.

- [ ] **Step 1: Write the outcome test**

Append to `tests/e2e/test_rail_density.py`:

```python
def test_course_map_index_gains_usable_height(tmp_path: Path) -> None:
    """The reader must actually see more of the tree.

    Before: 444.6px of fixed chrome left the index 385.4px of an 868px rail
    (44%) for 2027px of content -- 4 of 33 pages visible.
    """
    from playwright.sync_api import sync_playwright

    handle = _preview(tmp_path, DENSITY_FIXTURE)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(
                    f"{handle.base_url}/index.html", wait_until="networkidle"
                )
                page.wait_for_timeout(500)
                # Expand every branch. Every toggle is eagerly present in the
                # DOM at load (children are hidden by an ancestor `hidden`
                # attribute, not lazily created), so each click flips exactly
                # one element out of this LIVE aria-expanded="false" match
                # set. Indexing with `nth(i)` over a count taken before any
                # click goes stale one-for-one as the set shrinks and then
                # hangs for the full 30s Playwright timeout. Drain with
                # `.first` instead, re-querying after every click.
                toggles = page.locator(
                    '[data-raya-map-node-toggle][aria-expanded="false"]'
                )
                guard = 0
                while toggles.count() > 0 and guard < 200:
                    toggles.first.click()
                    guard += 1
                page.wait_for_timeout(200)
                # The guard must not silently mask a partially expanded tree.
                # `hidden` only suppresses rendering, so querySelectorAll
                # still sees unexpanded nodes -- link counts and depth read
                # the same with zero clicks as with a full drain. Only this
                # post-condition proves the drain completed.
                assert toggles.count() == 0, (
                    "guard exhausted before draining all node toggles"
                )

                state = page.evaluate(
                    """() => {
                      const map = document.querySelector('.raya-course-map');
                      const list = document.querySelector(
                        '.raya-course-map-list');
                      const lr = list.getBoundingClientRect();
                      const fully = [...document.querySelectorAll(
                        '.raya-course-map-node-row a')].filter((a) => {
                          const r = a.getBoundingClientRect();
                          return r.height > 0
                            && r.top >= lr.top - 1 && r.bottom <= lr.bottom + 1;
                        }).length;
                      return {
                        railHeight: Math.round(
                          map.getBoundingClientRect().height),
                        indexHeight: Math.round(lr.height),
                        minHeight: getComputedStyle(list).minHeight,
                        fullyVisibleLinks: fully,
                      };
                    }"""
                )
                # Chrome fell from 444.6px to about 275px, so the index takes
                # the difference. Gate below the projection, not at it.
                assert state["indexHeight"] >= 500, state
                assert state["indexHeight"] / state["railHeight"] >= 0.6, state
                assert state["fullyVisibleLinks"] >= 11, state
                # The shipped floor is never lowered.
                assert state["minHeight"] == "192px", state
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()


@pytest.mark.parametrize("height", [900, 720, 600, 520])
@pytest.mark.parametrize("root_font", ["16px", "24px", "32px"])
def test_rail_frame_never_clips_tree_content(
    tmp_path: Path, height: int, root_font: str
) -> None:
    """The frame's overflow:auto relief valve must keep working.

    A rejected draft set overflow:hidden on the frame; at a 24px root font
    that clipped 23px of tree with no scroll path, and 220px at 32px.
    """
    from playwright.sync_api import sync_playwright

    handle = _preview(tmp_path, DENSITY_FIXTURE)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(
                    viewport={"width": 1440, "height": height}
                )
                page.goto(
                    f"{handle.base_url}/index.html", wait_until="networkidle"
                )
                page.add_style_tag(
                    content=f"html {{ font-size: {root_font}; }}"
                )
                page.wait_for_timeout(400)
                clipped = page.evaluate(
                    """() => {
                      const map = document.querySelector('.raya-course-map');
                      return {
                        overflowY: getComputedStyle(map).overflowY,
                        hidden: map.scrollHeight - map.clientHeight,
                      };
                    }"""
                )
                # Either nothing overflows, or the frame can scroll to it.
                assert clipped["overflowY"] == "auto", (height, root_font, clipped)
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()
```

- [ ] **Step 2: Run both tests**

Run: `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_density.py -v`

Expected: all PASS. If `indexHeight` is under 500px, do **not** lower the gate — report the measured chrome breakdown so the shortfall can be diagnosed against the spec's projection.

- [ ] **Step 3: Confirm the drawer and the collapse contract are untouched**

Run:
```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_rail_collapse_contract.py -v
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/e2e/test_preview_static_read_path.py -k "drawer or mobile" -v
```

Expected: PASS with **no edits** to either file. In particular `test_course_map_tree_keeps_usable_height_on_short_viewports` must still pass on its own terms. If any drawer test needs editing, a base-rule change leaked below 640px — fix the CSS scoping, not the test.

- [ ] **Step 4: Run the full suite in the background**

The suite takes ~18 minutes and exceeds the foreground tool timeout.

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  > /tmp/raya-full-suite.log 2>&1
```

Run this with `run_in_background: true`. When it finishes, read the summary line — **do not trust a wrapper exit code**, since a trailing command in the same chain masks pytest's status:

```bash
grep -E "[0-9]+ (passed|failed|error)" /tmp/raya-full-suite.log | tail -5
```

Expected: `N passed`, zero failed, zero errors.

- [ ] **Step 5: Enumerate every changed assertion for review**

Produce the list the spec requires — every assertion edited or deleted across Tasks 4-11, each with a one-line justification:

```bash
git diff new_rayalucaria..HEAD -- tests/ > /tmp/raya-test-diff.patch
git diff --stat new_rayalucaria..HEAD -- tests/
```

Review `/tmp/raya-test-diff.patch` specifically for **deletions**. Any assertion removed without a justification in its task's commit body is a defect: either restore it or document why the contract it encoded no longer exists.

- [ ] **Step 6: Open the pull request**

```bash
git push -u origin feature/reader-rail-density
gh pr create --base new_rayalucaria --title "fix(rail): reader rail density and scroll liveness" --body "$(cat <<'MSG'
Implements `docs/superpowers/specs/2026-07-29-reader-rail-density-design.md`
(revision 2), written after four adversarial reviews rejected revision 1.

## The reported bug

`.raya-course-map` declared `overflow: auto` and `overscroll-behavior:
contain` while never overflowing, so Chrome treated it as a scroll
container with nowhere to put the delta. Wheeling over the header, the
tools row, or the filter moved nothing at all -- 351.8px of an 868px rail,
41%.

Measured before: header/tools/filter/index = dead/dead/dead/index.
Measured after:  header/tools/filter/index = page/page/page/index.

## Density

| | Before | After |
| --- | --- | --- |
| Fixed chrome | 444.6px | ~275px |
| Index window | 385.4px (44%) | >=500px (>=60%) |
| Label column at depth 3 | 103.2px | ~157px |
| Right-rail panel content | 1358.3px in a 767px window | ~590px |

## Deliberately NOT done

Four things a rejected draft proposed, each disproven by measurement and
recorded in the spec's "Corrections to revision 1" table: `overflow:
hidden` on the rail frame (clips tree content at enlarged root fonts),
lowering the `12rem` index floor, icon-only command tiles (the tooltip
attribute is inert and absent on three of eight controls), and native
`<details>` for right-rail panels (deletes three `<h2>` headings and
re-implements a shipped compliant mechanism).

The 200% zoom / 640-893 medium-band collapse is a separate bug and is
explicitly out of scope by owner decision.

## Verification

Every new check was demonstrated red against `main` before passing; the red
output is in each task report. Density is gated on a new 31-page, 3-level
fixture because the 6-page `render-fixture` measures 217px and its map
never reaches the `max-height` clamp.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
MSG
)"
```

- [ ] **Step 7: Poll CI**

This `gh` lacks `--watch`. Poll:

```bash
for i in $(seq 1 40); do
  gh pr checks --json name,state 2>/dev/null || gh pr checks
  sleep 60
done
```

Both "Docker checks" and "Host checks" run the full suite (~18 min each) and are the authoritative gate.

- [ ] **Step 8: Merge, deploy, and verify live**

After both checks pass:

```bash
gh pr merge --squash --delete-branch
gh workflow run deploy.yml --ref new_rayalucaria
```

Then verify against `https://uumami.wiki/raya_lucaria/foundation/system-model/index.html` (CDN `max-age=600`, so allow ~10 minutes), re-running the checks from Tasks 1, 2, 10, and 12 against the deployed 33-page tree: wheel liveness over all four regions, header parity at 894/1280/1440, one open right-rail panel with three collapsed and inert, and index height plus fully-visible link count.

Report the measured numbers, not "looks good".

---

## Self-Review

**Spec coverage.** Every numbered spec section maps to a task: P1 → Task 1; P2 → Tasks 4, 5, 6; P3 → Tasks 2, 7, 8, 9; P4 → Task 10; the contract amendment and all eight role-doc locations → Task 11; the large-tree fixture, the density gate, the drawer regression check, the enumerated-assertion review, and the deploy verification → Tasks 3 and 12. The spec's five "What is NOT the problem" items appear as Global Constraints so no implementer re-introduces them. The `.raya-font-toggle` false-active-state defect the spec folds in is Task 4 Step 5.

**Placeholder scan.** No "TBD", no "add appropriate error handling", no "similar to Task N". Every code step carries the actual CSS or Python. Two steps deliberately instruct the implementer to read surrounding code before editing (Task 5 Step 3, Task 10 Step 4) because the exact block boundaries are longer than is useful to inline; both name the file and line range.

**Type and name consistency.** `_preview(tmp_path, fixture=RENDER_FIXTURE)`, `_browser_executable()`, `ROOT`, `RENDER_FIXTURE`, and `DENSITY_FIXTURE` are defined once in Task 1 Step 1 and used with those exact signatures in Tasks 2-12. `DENSITY_FIXTURE` is created in Task 3 and consumed in Tasks 7, 8, and 12. Task 7's `renderedLines` probe field and Task 8's line-count measurement both use `clientHeight / lineHeight`, never `Range.getClientRects()`, consistently.

**Ordering dependency.** Task 2 must precede Task 7, because the label-column gate of >= 140px assumes the +15px the gutter removal frees. Task 3 must precede Tasks 7, 8, and 12. Task 8 must precede Task 9, because the current-row badge is absolutely positioned specifically so it cannot become a block child of Task 8's `-webkit-box`.

**One known imprecision, deliberately left.** Task 4 Step 8 and several Step 7s name tests by pattern rather than exact node id, with a `grep` fallback, because the owning test names were not all confirmed. Each such step names the grep to run.
