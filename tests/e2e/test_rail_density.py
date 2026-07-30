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
                #
                # Every node's toggle is eagerly present in the DOM at load
                # (children are hidden via an ancestor `hidden` attribute,
                # not lazily created -- see setMapNodeExpanded in
                # packages/static/src/raya_static/shell.py), so each click
                # flips exactly one element out of this live
                # aria-expanded="false" selector's match set. A fixed
                # `range(toggles.count())` loop goes stale mid-loop as the
                # set shrinks one-for-one with each click, so re-query
                # `.first` after every click instead of indexing by a count
                # taken before any clicks happened.
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
      const lineHeight = label
        ? parseFloat(getComputedStyle(label).lineHeight) || lr.height
        : null;
      return {
        name: t.getAttribute('aria-label'),
        w: Math.round(r.width), h: Math.round(r.height),
        labelText: label ? label.textContent.trim() : null,
        labelVisible: !!(lr && lr.width > 8 && lr.height > 4),
        labelClipped: label
          ? label.scrollWidth > label.clientWidth + 1 : null,
        labelLines: lr ? Math.round(lr.height / lineHeight) : null,
        tileClipped: t.scrollWidth > t.clientWidth + 1,
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
                # Sanity bound only, not the binding constraint: an 11px/
                # mid-word-broken caption ("OpenDysle/xic") could satisfy a
                # tight height budget while reproducing the "crowded and
                # unreadable" complaint this change exists to fix. The real
                # acceptance criteria are per-tile below -- one line, never
                # clipped -- achieved by shortening captions ("OpenDyslexic"
                # -> "Font", "Schedule" -> "Plan"), not shrinking type.
                assert state["toolsHeight"] <= 200, state

                for tile in state["tiles"]:
                    assert tile["name"], tile
                    assert tile["w"] >= 40 and tile["h"] >= 40, tile
                    assert tile["labelVisible"] is True, tile
                    assert tile["labelClipped"] is False, tile
                    assert tile["tileClipped"] is False, tile
                    assert tile["labelLines"] == 1, tile

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
