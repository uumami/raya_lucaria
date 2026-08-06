"""Reader rail density and scroll-liveness contract.

Companion to tests/e2e/test_rail_collapse_contract.py. This module owns the
assertions added by docs/superpowers/plans/2026-07-29-reader-rail-density.md.
"""

import os
import re
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


def _open_course_map_drawer(page) -> None:
    page.click(".raya-mobile-course-map-open")
    page.wait_for_function(
        """() => document.documentElement.dataset.rayaCourseMapDrawer === 'open'"""
    )


def _rail_scroll_state(page) -> dict:
    return page.evaluate(
        """() => {
          const state = (selector) => {
            const node = document.querySelector(selector);
            return {
              clientHeight: node.clientHeight,
              scrollHeight: node.scrollHeight,
              scrollTop: node.scrollTop,
            };
          };
          return {
            navigation: state('[data-raya-course-map-navigation]'),
            map: state('.raya-course-map'),
            list: state('.raya-course-map-list'),
            pageY: window.scrollY,
          };
        }"""
    )


def _visible_center(page, selector: str) -> tuple[float, float]:
    box = page.locator(selector).first.bounding_box()
    assert box is not None, selector
    viewport = page.locator(
        "[data-raya-course-map-navigation]"
    ).bounding_box()
    assert viewport is not None
    left = max(box["x"], viewport["x"])
    right = min(box["x"] + box["width"], viewport["x"] + viewport["width"])
    top = max(box["y"], viewport["y"])
    bottom = min(
        box["y"] + box["height"], viewport["y"] + viewport["height"]
    )
    assert right - left > 2 and bottom - top > 2, (selector, box, viewport)
    return ((left + right) / 2, (top + bottom) / 2)


_SCROLL_ZONES = (
    ".raya-course-actions",
    ".raya-course-map-filter",
    ".raya-course-map-list .raya-course-map-node-row",
)


def test_course_rail_forbids_wheel_touch_forwarding_and_containment() -> None:
    from raya_static.rendering import rich_render_css
    from raya_static.shell import shell_resources

    javascript = shell_resources().javascript
    for forbidden in (
        'addEventListener("wheel"',
        "addEventListener('wheel'",
        'addEventListener("touchmove"',
        "addEventListener('touchmove'",
        ".onwheel =",
        ".ontouchmove =",
    ):
        assert forbidden not in javascript

    stylesheet = rich_render_css()
    rail_selectors = (
        ".raya-course-map",
        ".raya-course-map-navigation",
        ".raya-course-map-list",
    )
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", stylesheet):
        selectors, declarations = match.groups()
        if "overscroll-behavior: contain" not in declarations:
            continue
        assert not any(selector in selectors for selector in rail_selectors), (
            selectors,
            declarations,
        )


@pytest.mark.parametrize(
    ("width", "drawer"),
    [(1440, False), (894, False), (893, False), (640, False), (639, True), (390, True)],
)
def test_native_wheel_scrolls_only_central_owner_across_bands_and_zones(
    tmp_path: Path, width: int, drawer: bool
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
                if drawer:
                    _open_course_map_drawer(page)
                _expand_course_map_branches(page)

                for selector in _SCROLL_ZONES:
                    page.locator(
                        "[data-raya-course-map-navigation]"
                    ).evaluate("node => node.scrollTo({top: 0, behavior: 'instant'})")
                    page.evaluate("() => window.scrollTo(0, 0)")
                    before = _rail_scroll_state(page)
                    assert before["navigation"]["scrollHeight"] > (
                        before["navigation"]["clientHeight"] + 100
                    )
                    x, y = _visible_center(page, selector)
                    page.mouse.move(x, y)
                    page.mouse.wheel(0, 240)
                    page.wait_for_function(
                        """() => document.querySelector(
                          '[data-raya-course-map-navigation]').scrollTop > 0"""
                    )
                    after = _rail_scroll_state(page)
                    assert after["navigation"]["scrollTop"] > 0, (
                        width,
                        selector,
                        before,
                        after,
                    )
                    assert after["map"]["scrollTop"] == before["map"]["scrollTop"]
                    assert after["list"]["scrollTop"] == before["list"]["scrollTop"]
                    assert after["pageY"] == before["pageY"]
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()


@pytest.mark.parametrize("width", [1440, 894, 893, 640])
def test_native_wheel_chains_page_at_structural_scroll_boundaries(
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
                _expand_course_map_branches(page)
                page.evaluate(
                    """() => {
                      const spacer = document.createElement('div');
                      spacer.style.height = '2400px';
                      document.body.append(spacer);
                    }"""
                )
                navigation = page.locator(
                    "[data-raya-course-map-navigation]"
                )
                page.evaluate("() => window.scrollTo(0, 0)")
                x, y = _visible_center(
                    page, "[data-raya-course-map-navigation]"
                )
                page.mouse.move(x, y)
                page.wait_for_timeout(100)
                navigation.evaluate(
                    """node => new Promise((resolve) => {
                      requestAnimationFrame(() => {
                        node.scrollTo({top: node.scrollHeight, behavior: 'instant'});
                        requestAnimationFrame(() => {
                          node.scrollTo({top: node.scrollHeight, behavior: 'instant'});
                          resolve();
                        });
                      });
                    })"""
                )
                boundary = _rail_scroll_state(page)["navigation"]
                assert boundary["scrollTop"] == (
                    boundary["scrollHeight"] - boundary["clientHeight"]
                )
                page.mouse.wheel(0, 360)
                page.wait_for_function("() => window.scrollY > 0")
                bottom = _rail_scroll_state(page)
                maximum = (
                    bottom["navigation"]["scrollHeight"]
                    - bottom["navigation"]["clientHeight"]
                )
                assert abs(bottom["navigation"]["scrollTop"] - maximum) <= 1
                assert bottom["pageY"] > 0

                navigation.evaluate(
                    "node => node.scrollTo({top: 0, behavior: 'instant'})"
                )
                page.evaluate("() => window.scrollTo(0, 800)")
                before_top = page.evaluate("() => window.scrollY")
                x, y = _visible_center(
                    page, "[data-raya-course-map-navigation]"
                )
                page.mouse.move(x, y)
                page.mouse.wheel(0, -360)
                page.wait_for_function(
                    "before => window.scrollY < before", arg=before_top
                )
                top = _rail_scroll_state(page)
                assert top["navigation"]["scrollTop"] == 0
                assert top["pageY"] < before_top
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()


@pytest.mark.parametrize("width", [639, 390])
def test_native_wheel_keeps_document_locked_at_modal_boundaries(
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
                page.evaluate(
                    """() => {
                      const spacer = document.createElement('div');
                      spacer.style.height = '2400px';
                      document.body.append(spacer);
                      window.scrollTo(0, 800);
                    }"""
                )
                before_drawer = page.evaluate("() => window.scrollY")
                assert before_drawer > 0
                page.locator(".raya-mobile-course-map-open").evaluate(
                    "button => button.click()"
                )
                page.wait_for_function(
                    """() => document.documentElement.dataset
                      .rayaCourseMapDrawer === 'open'"""
                )
                locked_page_y = page.evaluate("() => window.scrollY")
                assert locked_page_y == before_drawer
                _expand_course_map_branches(page)
                navigation = page.locator(
                    "[data-raya-course-map-navigation]"
                )
                x, y = _visible_center(
                    page, "[data-raya-course-map-navigation]"
                )
                page.mouse.move(x, y)
                page.wait_for_timeout(100)
                navigation.evaluate(
                    """node => new Promise((resolve) => {
                      requestAnimationFrame(() => {
                        node.scrollTo({top: node.scrollHeight, behavior: 'instant'});
                        requestAnimationFrame(() => {
                          node.scrollTo({top: node.scrollHeight, behavior: 'instant'});
                          resolve();
                        });
                      });
                    })"""
                )
                boundary = _rail_scroll_state(page)["navigation"]
                assert boundary["scrollTop"] == (
                    boundary["scrollHeight"] - boundary["clientHeight"]
                )
                page.mouse.wheel(0, 360)
                page.wait_for_timeout(250)
                bottom = _rail_scroll_state(page)
                maximum = (
                    bottom["navigation"]["scrollHeight"]
                    - bottom["navigation"]["clientHeight"]
                )
                assert abs(bottom["navigation"]["scrollTop"] - maximum) <= 1
                assert bottom["pageY"] == locked_page_y

                navigation.evaluate(
                    "node => node.scrollTo({top: 0, behavior: 'instant'})"
                )
                page.mouse.wheel(0, -360)
                page.wait_for_timeout(250)
                top = _rail_scroll_state(page)
                assert top["navigation"]["scrollTop"] == 0
                assert top["pageY"] == locked_page_y
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()


@pytest.mark.parametrize(("width", "drawer"), [(640, False), (390, True)])
def test_native_touch_swipes_scroll_central_owner_for_all_zones(
    tmp_path: Path, width: int, drawer: bool
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
                context = browser.new_context(
                    viewport={"width": width, "height": 640},
                    has_touch=True,
                    device_scale_factor=2,
                )
                page = context.new_page()
                page.goto(
                    f"{handle.base_url}/index.html", wait_until="networkidle"
                )
                if drawer:
                    _open_course_map_drawer(page)
                _expand_course_map_branches(page)
                session = context.new_cdp_session(page)

                for selector in _SCROLL_ZONES:
                    page.locator(
                        "[data-raya-course-map-navigation]"
                    ).evaluate("node => node.scrollTo({top: 0, behavior: 'instant'})")
                    before = _rail_scroll_state(page)
                    x, y = _visible_center(page, selector)
                    session.send(
                        "Input.dispatchTouchEvent",
                        {
                            "type": "touchStart",
                            "touchPoints": [{"x": x, "y": y}],
                        },
                    )
                    for delta in (20, 40, 60, 80, 100):
                        session.send(
                            "Input.dispatchTouchEvent",
                            {
                                "type": "touchMove",
                                "touchPoints": [{"x": x, "y": y - delta}],
                            },
                        )
                        page.wait_for_timeout(20)
                    session.send(
                        "Input.dispatchTouchEvent",
                        {"type": "touchEnd", "touchPoints": []},
                    )
                    page.wait_for_function(
                        """() => document.querySelector(
                          '[data-raya-course-map-navigation]').scrollTop > 0"""
                    )
                    after = _rail_scroll_state(page)
                    assert after["navigation"]["scrollTop"] > (
                        before["navigation"]["scrollTop"]
                    ), (width, selector, before, after)
                    assert after["map"]["scrollTop"] == before["map"]["scrollTop"]
                    assert after["list"]["scrollTop"] == before["list"]["scrollTop"]
                    assert after["pageY"] == before["pageY"]
                page.close()
                context.close()
            finally:
                browser.close()
    finally:
        handle.close()


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


@pytest.mark.parametrize("height", [900, 720, 600, 520, 480])
def test_filter_and_search_action_stay_present_and_focusable_at_every_height(
    tmp_path: Path, height: int
) -> None:
    """No viewport height may remove the filter or Search action.

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


def test_long_labels_are_dense_contained_and_wrap_in_flow_for_fine_pointers(
    tmp_path: Path,
) -> None:
    """Fine pointers keep compact one-line rows and let long labels wrap."""
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
                      const identifier = links.find((link) =>
                        link.textContent.includes(
                          'ProjectionResidualsWithAnUnbrokenAuthorIdentifierXYZ007'));
                      if (!navigation || !identifier) return null;
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
                        fullLabels: links.every((link) =>
                          link.scrollHeight <= link.clientHeight + 1),
                        normalFlow: links.every((link) => {
                          const style = getComputedStyle(link);
                          return style.display === 'flex'
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
                assert state["fontSizes"] == [14], state
                assert state["oneLineRows"], state
                assert all(27 <= height <= 30 for height in state["oneLineRows"]), state
                assert max(state["lineCounts"]) > 1, state
                assert state["fullLabels"] is True, state
                assert state["normalFlow"] is True, state
                assert state["identifier"]["right"] <= (
                    state["scrollport"]["right"] + 1
                ), state
                assert state["identifier"]["scrollWidth"] <= (
                    state["scrollport"]["clientWidth"] + 1
                ), state
                assert state["identifier"]["writingMode"] == "horizontal-tb", state
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


def test_course_rail_controls_match_pointer_targets_and_keep_focus_inside(
    tmp_path: Path,
) -> None:
    """Rail controls stay operable without clipped or overlapping focus UI."""
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
                fine = browser.new_page(viewport={"width": 1440, "height": 900})
                fine.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                fine.wait_for_timeout(400)
                fine_header = fine.evaluate(
                    """() => [...document.querySelectorAll(
                      '.raya-course-map-home, [data-raya-course-map-collapse], '
                      + '[data-raya-learning-rail-collapse]')]
                      .filter((control) => control.checkVisibility())
                      .map((control) => {
                        const rect = control.getBoundingClientRect();
                        return {
                          width: rect.width,
                          height: rect.height,
                          text: control.innerText.trim(),
                          icon: !!control.querySelector('.raya-command-icon'),
                          learning: control.hasAttribute(
                            'data-raya-learning-rail-collapse'),
                        };
                      })"""
                )
                assert len(fine_header) == 3, fine_header
                assert all(
                    30 <= item[axis] <= 32
                    for item in fine_header
                    for axis in ("width", "height")
                ), fine_header
                assert all(item["icon"] is True for item in fine_header), fine_header
                learning_hide = [item for item in fine_header if item["learning"]]
                assert len(learning_hide) == 1, fine_header
                assert learning_hide[0]["text"] == "", fine_header

                focus_selectors = (
                    ".raya-course-map-home",
                    "[data-raya-course-map-collapse]",
                    ".raya-course-action",
                    ".raya-course-map-comfort",
                    ".raya-course-map-filter",
                    ".raya-course-map-node-toggle",
                    ".raya-learning-rail-collapse",
                    ".raya-rail-toggle",
                )
                for selector in focus_selectors:
                    control = fine.locator(selector).first
                    assert control.count() == 1, selector
                    control.focus()
                    focus = control.evaluate(
                        """(node) => {
                          const style = getComputedStyle(node);
                          return {
                            width: parseFloat(style.outlineWidth),
                            offset: parseFloat(style.outlineOffset),
                          };
                        }"""
                    )
                    assert focus["width"] >= 3, (selector, focus)
                    assert focus["offset"] <= -3, (selector, focus)
                fine.close()

                coarse = browser.new_context(
                    viewport={"width": 1440, "height": 900}, has_touch=True
                )
                coarse_page = coarse.new_page()
                coarse_page.goto(
                    f"{handle.base_url}/index.html", wait_until="networkidle"
                )
                coarse_page.wait_for_timeout(400)
                coarse_state = coarse_page.evaluate(
                    """() => {
                      const selectors = [
                        '.raya-course-map-home',
                        '[data-raya-course-map-collapse]',
                        '.raya-course-action',
                        '.raya-course-map-comfort',
                        '.raya-course-map-filter',
                        '.raya-course-map-node-toggle',
                        '.raya-course-map-list a',
                        '.raya-learning-rail-collapse',
                        '.raya-rail-toggle'
                      ];
                      const controls = selectors.flatMap((selector) =>
                        [...document.querySelectorAll(selector)])
                        .filter((control) => control.checkVisibility());
                      const rects = controls.map((control) => {
                        const rect = control.getBoundingClientRect();
                        return {
                          label: control.getAttribute('aria-label')
                            || control.textContent.trim(),
                          left: rect.left,
                          right: rect.right,
                          top: rect.top,
                          bottom: rect.bottom,
                          width: rect.width,
                          height: rect.height,
                        };
                      });
                      const overlaps = rects.flatMap((left, index) =>
                        rects.slice(index + 1).filter((right) =>
                          left.left < right.right - 1
                          && left.right > right.left + 1
                          && left.top < right.bottom - 1
                          && left.bottom > right.top + 1)
                          .map((right) => [left.label, right.label]));
                      return {
                        coarse: matchMedia('(any-pointer: coarse)').matches,
                        controls: rects,
                        overlaps,
                      };
                    }"""
                )
                assert coarse_state["coarse"] is True, coarse_state
                assert coarse_state["controls"], coarse_state
                assert all(
                    control["width"] >= 44 and control["height"] >= 44
                    for control in coarse_state["controls"]
                ), coarse_state
                assert coarse_state["overlaps"] == [], coarse_state
                coarse.close()

                phone = browser.new_context(
                    viewport={"width": 390, "height": 844}, has_touch=True
                )
                phone_page = phone.new_page()
                phone_page.goto(
                    f"{handle.base_url}/index.html", wait_until="networkidle"
                )
                _open_course_map_drawer(phone_page)
                close = phone_page.locator("[data-raya-course-map-close]")
                assert close.get_attribute("aria-label") == "Close course map"
                assert close.inner_text().strip() == ""
                assert (
                    close.locator('[data-raya-command-icon="close"]').count() == 1
                )
                close_box = close.bounding_box()
                assert close_box is not None
                assert close_box["width"] >= 44 and close_box["height"] >= 44
                close.focus()
                phone_page.keyboard.press("Tab")
                phone_page.keyboard.press("Shift+Tab")
                close_focus = close.evaluate(
                    """(node) => {
                      const style = getComputedStyle(node);
                      return {
                        width: parseFloat(style.outlineWidth),
                        offset: parseFloat(style.outlineOffset),
                      };
                    }"""
                )
                assert close_focus["width"] >= 3, close_focus
                assert close_focus["offset"] <= -3, close_focus
                phone.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_tree_numbers_titles_and_current_marker_do_not_overlap(tmp_path: Path) -> None:
    """Structural labels and the current marker stay out of title flow."""
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
                page.wait_for_timeout(400)
                _expand_course_map_branches(page)

                state = page.evaluate(
                    """() => {
                      const links = [...document.querySelectorAll(
                        '.raya-course-map-node-row a')]
                        .filter((a) => a.getBoundingClientRect().width > 0);
                      const navigation = document.querySelector(
                        '[data-raya-course-map-navigation]');
                      const navigationRect = navigation.getBoundingClientRect();
                      return {
                        links: links.map((link) => {
                          const row = link.closest('.raya-course-map-node-row');
                          const number = link.querySelector(
                            '.raya-course-map-node-number');
                          const title = link.querySelector(
                            '.raya-course-map-node-title');
                          const linkRect = link.getBoundingClientRect();
                          const numberRect = number?.getBoundingClientRect() ?? null;
                          const titleRect = title.getBoundingClientRect();
                          return {
                            current: link.getAttribute('aria-current') === 'page',
                            pseudo: getComputedStyle(link, '::before').content,
                            borderWidth: parseFloat(
                              getComputedStyle(link).borderInlineStartWidth),
                            linkLeft: linkRect.left,
                            linkRight: linkRect.right,
                            numberLeft: numberRect?.left ?? null,
                            numberRight: numberRect?.right ?? null,
                            titleLeft: titleRect.left,
                            titleRight: titleRect.right,
                            rowRight: row.getBoundingClientRect().right,
                            rowScrollWidth: row.scrollWidth,
                          };
                        }),
                        navigationRight: navigationRect.right,
                        navigationClientWidth: navigation.clientWidth,
                      };
                    }"""
                )
                assert state["links"], "no visible map links"
                current = [link for link in state["links"] if link["current"]]
                assert len(current) == 1, state
                assert 2 <= current[0]["borderWidth"] <= 3, current[0]
                for link in state["links"]:
                    assert link["pseudo"] in {"none", "normal"}, link
                    assert link["linkLeft"] <= link["titleLeft"], link
                    assert link["titleRight"] <= link["linkRight"] + 1, link
                    if link["numberRight"] is not None:
                        assert link["linkLeft"] <= link["numberLeft"], link
                        assert link["numberRight"] <= link["titleLeft"] + 1, link
                    assert link["rowRight"] <= state["navigationRight"] + 1, link
                    assert link["rowScrollWidth"] <= (
                        state["navigationClientWidth"] + 1
                    ), link
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_fdd_tree_guides_and_targets_match_pointer_mode(tmp_path: Path) -> None:
    """Tree indentation and targets follow the fine/coarse FDD contract."""
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
                for width in (1440, 893):
                    for has_touch in (False, True):
                        context = browser.new_context(
                            viewport={"width": width, "height": 900},
                            has_touch=has_touch,
                        )
                        page = context.new_page()
                        page.goto(
                            f"{handle.base_url}/index.html", wait_until="networkidle"
                        )
                        _expand_course_map_branches(page)
                        state = page.evaluate(
                            """() => {
                              const row = document.querySelector(
                                '.raya-course-map-node-row');
                              const group = document.querySelector(
                                '[data-raya-map-children]:not([hidden])');
                              const toggle = row.querySelector(
                                '[data-raya-map-node-toggle]');
                              const link = row.querySelector('a');
                              const icon = toggle.querySelector(
                                '.raya-command-icon');
                              const rowStyle = getComputedStyle(row);
                              const linkStyle = getComputedStyle(link);
                              const groupStyle = getComputedStyle(group);
                              const iconStyle = getComputedStyle(icon);
                              return {
                                coarse: matchMedia(
                                  '(any-pointer: coarse), (hover: none)').matches,
                                columns: rowStyle.gridTemplateColumns,
                                fontSize: linkStyle.fontSize,
                                lineHeight: linkStyle.lineHeight,
                                linkHeight: link.getBoundingClientRect().height,
                                toggleWidth: toggle.getBoundingClientRect().width,
                                toggleHeight: toggle.getBoundingClientRect().height,
                                groupMargin: groupStyle.marginInlineStart,
                                groupPadding: groupStyle.paddingInlineStart,
                                groupBorder: groupStyle.borderInlineStartWidth,
                                pseudo: getComputedStyle(
                                  link, '::before').content,
                                iconWidth: icon.getBoundingClientRect().width,
                                iconTransform: iconStyle.transform,
                              };
                            }"""
                        )
                        expected_target = 44 if has_touch else 30
                        assert state["coarse"] is has_touch, state
                        assert state["columns"].split()[0] == (
                            f"{expected_target}px"
                        ), state
                        assert state["fontSize"] == "14px", state
                        assert 19 <= float(state["lineHeight"].removesuffix("px")) <= 21
                        assert state["toggleWidth"] == expected_target, state
                        assert state["toggleHeight"] >= expected_target, state
                        assert state["groupMargin"] == "16px", state
                        assert state["groupPadding"] == "8px", state
                        assert state["groupBorder"] == "1px", state
                        assert state["pseudo"] in {"none", "normal"}, state
                        assert 12 <= state["iconWidth"] <= 14, state
                        assert state["iconTransform"] != "none", state
                        if has_touch:
                            assert state["linkHeight"] >= 44, state
                        page.close()
                        context.close()
            finally:
                browser.close()
    finally:
        handle.close()
