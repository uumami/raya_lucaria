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


_SCROLL_OWNER_STATE = """() => [
  '.raya-course-map',
  '.raya-course-map-body',
  '.raya-course-map-navigation',
  '.raya-course-actions',
  '.raya-course-content',
  '.raya-course-map-list'
].map(selector => {
  const node = document.querySelector(selector);
  return {
    selector,
    overflowY: getComputedStyle(node).overflowY,
    clientHeight: node.clientHeight,
    scrollHeight: node.scrollHeight
  };
})"""


def _expand_course_map_branches(page) -> None:
    toggles = page.locator(
        '[data-raya-map-node-toggle][aria-expanded="false"]'
    )
    guard = 0
    while toggles.count() > 0 and guard < 200:
        toggles.first.evaluate("button => button.click()")
        guard += 1
    page.wait_for_timeout(200)
    assert toggles.count() == 0, "guard exhausted before draining all toggles"


@pytest.mark.parametrize("width", [1440, 894, 893, 640])
def test_course_map_has_a_single_scroll_owner(
    tmp_path: Path, width: int
) -> None:
    """Only the central navigation may own expanded-rail vertical scroll."""
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
                page = browser.new_page(viewport={"width": width, "height": 640})
                page.goto(
                    f"{handle.base_url}/index.html", wait_until="networkidle"
                )
                page.wait_for_timeout(400)
                _expand_course_map_branches(page)

                owners = page.evaluate(_SCROLL_OWNER_STATE)
                declared = [
                    item["selector"]
                    for item in owners
                    if item["overflowY"] in {"auto", "scroll"}
                ]
                assert declared == [".raya-course-map-navigation"], owners
                navigation = next(
                    item
                    for item in owners
                    if item["selector"] == ".raya-course-map-navigation"
                )
                assert navigation["scrollHeight"] > navigation["clientHeight"], (
                    navigation
                )
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()


@pytest.mark.parametrize("width", [1440, 894, 893, 640])
def test_course_map_header_footer_stay_fixed_while_navigation_scrolls(
    tmp_path: Path, width: int
) -> None:
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
                page = browser.new_page(viewport={"width": width, "height": 640})
                page.goto(
                    f"{handle.base_url}/index.html", wait_until="networkidle"
                )
                page.wait_for_timeout(400)
                _expand_course_map_branches(page)

                before = page.evaluate(
                    """() => {
                      const rect = selector => {
                        const box = document.querySelector(selector)
                          .getBoundingClientRect();
                        return {
                          top: box.top,
                          right: box.right,
                          bottom: box.bottom,
                          left: box.left,
                          width: box.width,
                          height: box.height
                        };
                      };
                      const navigation = document.querySelector(
                        '.raya-course-map-navigation'
                      );
                      return {
                        header: rect('.raya-course-map-header'),
                        footer: rect('.raya-course-map-footer'),
                        navigationScrollTop: navigation.scrollTop
                      };
                    }"""
                )
                after = page.evaluate(
                    """() => {
                      const rect = selector => {
                        const box = document.querySelector(selector)
                          .getBoundingClientRect();
                        return {
                          top: box.top,
                          right: box.right,
                          bottom: box.bottom,
                          left: box.left,
                          width: box.width,
                          height: box.height
                        };
                      };
                      const navigation = document.querySelector(
                        '.raya-course-map-navigation'
                      );
                      navigation.scrollTop = (
                        navigation.scrollHeight - navigation.clientHeight
                      ) / 2;
                      return {
                        header: rect('.raya-course-map-header'),
                        footer: rect('.raya-course-map-footer'),
                        navigationScrollTop: navigation.scrollTop
                      };
                    }"""
                )
                assert after["header"] == before["header"]
                assert after["footer"] == before["footer"]
                assert (
                    after["navigationScrollTop"]
                    > before["navigationScrollTop"]
                )
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_course_map_uses_256px_expanded_geometry(
    tmp_path: Path,
) -> None:
    """The left rail consumes its shared 256px token in every structural band."""
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
                for width in (640, 893, 894, 1279, 1280, 1440):
                    page = browser.new_page(
                        viewport={"width": width, "height": 950}
                    )
                    page.goto(
                        f"{handle.base_url}/index.html",
                        wait_until="networkidle",
                    )
                    page.wait_for_timeout(400)
                    geometry = page.evaluate(
                        """() => {
                          const map = document.querySelector('.raya-course-map');
                          const body = document.querySelector(
                            '.raya-course-map-body'
                          );
                          const navigation = document.querySelector(
                            '.raya-course-map-navigation'
                          );
                          const mapRect = map.getBoundingClientRect();
                          const bodyRect = body.getBoundingClientRect();
                          const navigationRect = navigation.getBoundingClientRect();
                          return {
                            mapWidth: mapRect.width,
                            bodyLeft: bodyRect.left,
                            bodyRight: bodyRect.right,
                            navigationLeft: navigationRect.left,
                            navigationRight: navigationRect.right,
                            documentOverflow:
                              document.documentElement.scrollWidth - innerWidth
                          };
                        }"""
                    )
                    assert 255 <= geometry["mapWidth"] <= 257, (width, geometry)
                    assert geometry["navigationLeft"] >= geometry["bodyLeft"] - 1
                    assert geometry["navigationRight"] <= geometry["bodyRight"] + 1
                    assert geometry["documentOverflow"] <= 1, (width, geometry)
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

                # Mirror of the unpressed check above, for the pressed half
                # of the cascade. Driven by forcing aria-pressed="true" via
                # JS rather than clicking, since Text size cycles through
                # three states instead of toggling -- this keeps the
                # assertion independent of interaction semantics.
                # Regression: .raya-font-toggle[aria-pressed="true"] is
                # (0,2,0), exactly equal to .raya-course-rail-command
                # [aria-pressed="true"], so unscoped it won by source order
                # (accessibility.py links after rich.css) and left the Font
                # tile permanently rendering a solid accent fill instead of
                # the shared soft accent-soft-38% pressed style every other
                # tile uses.
                pressed_bgs = page.evaluate(
                    """() => {
                      const tiles = [...document.querySelectorAll(
                        '.raya-course-rail-command'
                      )];
                      const original = tiles.map(
                        (t) => t.getAttribute('aria-pressed')
                      );
                      tiles.forEach((t) => t.setAttribute('aria-pressed', 'true'));
                      const bgs = tiles.map(
                        (t) => getComputedStyle(t).backgroundColor
                      );
                      tiles.forEach((t, i) => {
                        if (original[i] === null) t.removeAttribute('aria-pressed');
                        else t.setAttribute('aria-pressed', original[i]);
                      });
                      return bgs;
                    }"""
                )
                assert len(set(pressed_bgs)) == 1, pressed_bgs

                # Every tile must answer pointer hover, not just keyboard
                # focus. Regression: a `.raya-course-rail-command.raya-
                # font-toggle[aria-pressed="false"]` compound override
                # (0,3,0) used to outrank `.raya-course-rail-command:hover`
                # (0,2,0), leaving the Font tile the only one of eight with
                # no hover feedback for a pointer user.
                tiles_locator = page.locator(".raya-course-rail-command")
                for index in range(tiles_locator.count()):
                    tile = tiles_locator.nth(index)
                    box = tile.bounding_box()
                    assert box is not None, index
                    before = tile.evaluate(
                        "(el) => getComputedStyle(el).backgroundColor"
                    )
                    page.mouse.move(
                        box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
                    )
                    page.wait_for_timeout(60)
                    after = tile.evaluate(
                        "(el) => getComputedStyle(el).backgroundColor"
                    )
                    page.mouse.move(0, 0)
                    assert before != after, (index, before, after)

                page.close()
            finally:
                browser.close()
    finally:
        handle.close()


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
                assert page.evaluate(
                    "() => document.documentElement.dataset.rayaCourseMap"
                ) == "expanded"
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

                assert page.locator(".raya-course-action.raya-command-search").is_visible()
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


def test_long_labels_are_dense_contained_and_release_in_flow_for_fine_pointers(
    tmp_path: Path,
) -> None:
    """Fine pointers get compact rows without making long labels unreadable."""
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
                _expand_course_map_branches(page)
                assert page.evaluate(
                    "() => matchMedia('(any-pointer: fine)').matches"
                )

                state = page.evaluate(
                    """() => {
                      const navigation = document.querySelector(
                        '[data-raya-course-map-navigation]');
                      const links = [...document.querySelectorAll(
                        '.raya-course-map-node-row a')]
                        .filter((link) => link.getBoundingClientRect().width > 0);
                      const nonCurrent = links.filter(
                        (link) => link.getAttribute('aria-current') !== 'page');
                      const oneLineRows = nonCurrent
                        .filter((link) => {
                          const style = getComputedStyle(link);
                          const contentHeight = link.clientHeight
                            - parseFloat(style.paddingTop)
                            - parseFloat(style.paddingBottom);
                          return contentHeight <= parseFloat(style.lineHeight) + 1;
                        })
                        .map((link) => link.closest(
                          '.raya-course-map-node-row').getBoundingClientRect().height);
                      const lineCounts = nonCurrent.map((link) => {
                        const style = getComputedStyle(link);
                        const contentHeight = link.clientHeight
                          - parseFloat(style.paddingTop)
                          - parseFloat(style.paddingBottom);
                        return Math.round(
                          contentHeight / parseFloat(style.lineHeight));
                      });
                      const clamped = [...nonCurrent].reverse().find(
                        (link) => link.scrollHeight > link.clientHeight + 1);
                      const identifier = links.find((link) =>
                        link.textContent.includes(
                          'ProjectionResidualsWithAnUnbrokenAuthorIdentifierXYZ007'));
                      if (!navigation || !clamped || !identifier) return null;
                      const navigationRect = navigation.getBoundingClientRect();
                      const identifierRow = identifier.closest(
                        '.raya-course-map-node-row');
                      const identifierRect = identifierRow.getBoundingClientRect();
                      const identifierStyle = getComputedStyle(identifier);
                      return {
                        fontSizes: [...new Set(nonCurrent.map(
                          (link) => parseFloat(getComputedStyle(link).fontSize)))],
                        lineCounts,
                        oneLineRows,
                        clampedText: clamped.textContent.trim(),
                        currentReleased: links
                          .filter((link) => link.getAttribute('aria-current') === 'page')
                          .every((link) => {
                            const style = getComputedStyle(link);
                            return style.display === 'block'
                              && style.webkitLineClamp === 'none';
                          }),
                        identifier: {
                          right: identifierRect.right,
                          scrollWidth: identifierRow.scrollWidth,
                          writingMode: identifierStyle.writingMode,
                        },
                        scrollport: {
                          right: navigationRect.right,
                          clientWidth: navigation.clientWidth,
                        },
                      };
                    }"""
                )
                assert state is not None
                assert all(12 <= size <= 13 for size in state["fontSizes"]), state
                assert state["oneLineRows"], state
                assert all(27 <= height <= 30 for height in state["oneLineRows"]), state
                assert max(state["lineCounts"]) <= 2, state
                assert state["currentReleased"] is True, state
                assert state["identifier"]["right"] <= (
                    state["scrollport"]["right"] + 1
                ), state
                assert state["identifier"]["scrollWidth"] <= (
                    state["scrollport"]["clientWidth"] + 1
                ), state
                assert state["identifier"]["writingMode"] == "horizontal-tb", state

                page.keyboard.press("Tab")
                released = page.evaluate(
                    """(text) => {
                      const navigation = document.querySelector(
                        '[data-raya-course-map-navigation]');
                      const link = [...document.querySelectorAll(
                        '.raya-course-map-node-row a')]
                        .find((candidate) => candidate.textContent.trim() === text);
                      link.focus();
                      link.scrollIntoView({block: 'nearest'});
                      const navigationRect = navigation.getBoundingClientRect();
                      const rowRect = link.closest(
                        '.raya-course-map-node-row').getBoundingClientRect();
                      return {
                        active: document.activeElement === link,
                        fits: link.scrollHeight <= link.clientHeight + 1,
                        rowTop: rowRect.top,
                        rowBottom: rowRect.bottom,
                        navigationTop: navigationRect.top,
                        navigationBottom: navigationRect.bottom,
                      };
                    }""",
                    state["clampedText"],
                )
                assert released["active"] is True, released
                assert released["fits"] is True, released
                assert released["rowTop"] >= released["navigationTop"] - 1, released
                assert released["rowBottom"] <= (
                    released["navigationBottom"] + 1
                ), released
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()


_ORIENTATION = """() => {
  const navigation = document.querySelector('[data-raya-course-map-navigation]');
  const current = navigation?.querySelector('a[aria-current="page"]');
  if (!navigation || !current) return null;
  const navigationRect = navigation.getBoundingClientRect();
  const currentRect = current.getBoundingClientRect();
  return {
    oriented: navigation.dataset.rayaCourseMapOriented,
    navigationScrollTop: navigation.scrollTop,
    currentTop: currentRect.top,
    currentBottom: currentRect.bottom,
    currentHeight: currentRect.height,
    navigationTop: navigationRect.top,
    navigationBottom: navigationRect.bottom,
    navigationHeight: navigationRect.height,
  };
}"""


def test_course_map_orientation_is_one_shot_against_the_central_owner(
    tmp_path: Path,
) -> None:
    """Initial reconciliation may orient once; later layout work may not."""
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
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                requested_urls: list[str] = []
                page.on("request", lambda request: requested_urls.append(request.url))
                # The deepest, last leaf in the tree: bringing it into view
                # from a fully expanded, scrolled-to-top list requires the
                # largest scroll distance, so this is the least accidental
                # page to orient toward.
                page.goto(
                    f"{handle.base_url}/verification/review/summary/index.html",
                    wait_until="networkidle",
                )
                page.evaluate(
                    "() => document.fonts ? document.fonts.ready.then(() => true) : true"
                )
                requested_urls.clear()

                _expand_course_map_branches(page)

                # Positive anchor: prove the precondition this test exists to
                # provide -- a list that actually overflows its own window,
                # unlike render-fixture.
                overflow = page.evaluate(
                    """() => {
                      const list = document.querySelector(
                        '[data-raya-course-map-navigation]');
                      return {
                        clientHeight: list.clientHeight,
                        scrollHeight: list.scrollHeight,
                      };
                    }"""
                )
                assert overflow["scrollHeight"] > overflow["clientHeight"] + 50, (
                    overflow
                )

                # Reset scroll/orientation state, then force orientation --
                # mirrors the initial-load orientation contract.
                page.evaluate(
                    """() => {
                      const navigation = document.querySelector(
                        '[data-raya-course-map-navigation]');
                      navigation.scrollTop = 0;
                      delete navigation.dataset.rayaCourseMapOriented;
                      window.rayaOrientCourseMapToCurrentPage?.();
                    }"""
                )
                initial = page.evaluate(_ORIENTATION)
                assert initial is not None
                assert initial["oriented"] == "true"
                assert initial["navigationScrollTop"] > 0
                assert initial["currentTop"] >= initial["navigationTop"] - 1
                if initial["currentHeight"] <= initial["navigationHeight"]:
                    assert initial["currentBottom"] <= initial["navigationBottom"] + 1
                else:
                    assert initial["currentBottom"] >= initial["navigationTop"]

                manual_scroll = page.evaluate(
                    """() => {
                      const navigation = document.querySelector(
                        '[data-raya-course-map-navigation]');
                      navigation.scrollTop = Math.max(
                        1,
                        Math.min(48, navigation.scrollHeight - navigation.clientHeight)
                      );
                      return navigation.scrollTop;
                    }"""
                )
                assert manual_scroll > 0
                page.set_viewport_size({"width": 1279, "height": 899})
                page.set_viewport_size({"width": 1280, "height": 900})
                page.wait_for_timeout(300)
                after_resize = page.evaluate(
                    """() => document.querySelector(
                      '[data-raya-course-map-navigation]').scrollTop"""
                )
                assert abs(after_resize - manual_scroll) <= 1

                assert requested_urls == []
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_coarse_pointer_labels_are_full_height_and_targets_do_not_overlap(
    tmp_path: Path,
) -> None:
    """Hybrid/touch layouts expose full labels with 44px target geometry."""
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
                context = browser.new_context(
                    viewport={"width": 1440, "height": 900}, has_touch=True
                )
                page = context.new_page()
                page.goto(
                    f"{handle.base_url}/index.html", wait_until="networkidle"
                )
                page.wait_for_timeout(500)
                _expand_course_map_branches(page)
                state = page.evaluate(
                    """() => {
                      const navigation = document.querySelector(
                        '[data-raya-course-map-navigation]');
                      const rows = [...document.querySelectorAll(
                        '.raya-course-map-node-row')]
                        .filter((row) => row.getBoundingClientRect().width > 0);
                      const identifier = rows.find((row) => row.textContent.includes(
                        'ProjectionResidualsWithAnUnbrokenAuthorIdentifierXYZ007'));
                      const navigationRect = navigation.getBoundingClientRect();
                      const identifierRect = identifier.getBoundingClientRect();
                      const identifierLink = identifier.querySelector('a');
                      const rowRects = rows.map((row) => row.getBoundingClientRect());
                      return {
                        coarse: matchMedia('(any-pointer: coarse)').matches,
                        fullLabels: rows.every((row) => {
                          const link = row.querySelector('a');
                          return link.scrollHeight <= link.clientHeight + 1;
                        }),
                        rows: rows.map((row) => ({
                          height: row.getBoundingClientRect().height,
                          linkHeight: row.querySelector('a').getBoundingClientRect().height,
                          controlHeight: row.querySelector(
                            '[data-raya-map-node-toggle]')
                            ?.getBoundingClientRect().height ?? null,
                        })),
                        overlap: rowRects.some((rect, index) =>
                          index > 0 && rect.top < rowRects[index - 1].bottom - 1),
                        identifier: {
                          right: identifierRect.right,
                          scrollWidth: identifier.scrollWidth,
                          writingMode: getComputedStyle(identifierLink).writingMode,
                        },
                        scrollport: {
                          right: navigationRect.right,
                          clientWidth: navigation.clientWidth,
                        },
                      };
                    }"""
                )
                assert state["coarse"] is True, state
                assert state["fullLabels"] is True, state
                assert state["overlap"] is False, state
                assert all(row["height"] >= 44 for row in state["rows"]), state
                assert all(row["linkHeight"] >= 44 for row in state["rows"]), state
                assert all(
                    row["controlHeight"] is None or row["controlHeight"] >= 44
                    for row in state["rows"]
                ), state
                assert state["identifier"]["right"] <= (
                    state["scrollport"]["right"] + 1
                ), state
                assert state["identifier"]["scrollWidth"] <= (
                    state["scrollport"]["clientWidth"] + 1
                ), state
                assert state["identifier"]["writingMode"] == "horizontal-tb", state
                page.close()
                context.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_sequence_badge_shows_only_on_the_current_row(tmp_path: Path) -> None:
    """The current sequence badge remains contained in the label grid."""
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
                      const navigation = document.querySelector(
                        '[data-raya-course-map-navigation]');
                      const navigationRect = navigation.getBoundingClientRect();
                      return links.map((a) => ({
                        current: a.getAttribute('aria-current') === 'page',
                        display: getComputedStyle(a, '::before').display,
                        content: getComputedStyle(a, '::before').content,
                        rowRight: a.closest(
                          '.raya-course-map-node-row').getBoundingClientRect().right,
                        rowScrollWidth: a.closest(
                          '.raya-course-map-node-row').scrollWidth,
                        navigationRight: navigationRect.right,
                        navigationClientWidth: navigation.clientWidth,
                      }));
                    }"""
                )
                assert badges, "no visible map links"
                current = [b for b in badges if b["current"]]
                assert len(current) == 1, badges
                # Blockification (CSS Display Module Level 3): an
                # absolutely-positioned "inline-flex" box computes to "flex",
                # not "inline-flex" -- position:absolute is mandatory here
                # (see rendering.py) so the badge cannot become a block child
                # inside Task 8's -webkit-box clamp. Assert "flex" only, not
                # {"inline-flex", "flex"}: accepting "inline-flex" would also
                # accept the in-flow regression this task exists to prevent
                # (in-flow computes "inline-flex"; only out-of-flow
                # computes "flex"), which defeats the point of the check.
                assert current[0]["display"] == "flex", current[0]
                assert current[0]["content"] not in {"none", "normal"}, current[0]
                assert current[0]["rowRight"] <= current[0]["navigationRight"] + 1
                assert current[0]["rowScrollWidth"] <= (
                    current[0]["navigationClientWidth"] + 1
                )
                for badge in badges:
                    if not badge["current"]:
                        assert badge["display"] == "none", badge
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()
