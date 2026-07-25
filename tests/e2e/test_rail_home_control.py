import contextlib
import os
import shutil
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RENDER_FIXTURE = ROOT / "examples" / "courses" / "render-fixture"
TWO_ROOT_FIXTURE = ROOT / "examples" / "courses" / "rail-two-root-fixture"


def _browser_executable() -> Path:
    # Local copy of tests/e2e/test_preview_static_read_path._browser_executable:
    # a cross-module `tests.e2e....` import does not resolve under pytest's
    # rootdir-relative import mode here (no tests/__init__.py package), so we
    # duplicate the small helper rather than fight import mode configuration.
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
        resolved = shutil.which(name)
        if resolved is not None:
            return Path(resolved)
    pytest.fail("A Chromium-compatible browser is required for visual/layout e2e tests")


def _rail_header_height(browser, base_url: str, width: int, rail: str) -> float:
    # rail is "course-map" or "learning-rail". Each measurement uses its own
    # page/navigation (mirrors test_render_fixture_reader_rails_share_outer_geometry's
    # expanded_state pattern) so that expanding one rail never depends on the
    # other rail's transition state finishing first.
    state_name = "rayaCourseMap" if rail == "course-map" else "rayaLearningRail"
    transition_name = (
        "rayaCourseMapTransition" if rail == "course-map" else "rayaLearningRailTransition"
    )
    rail_selector = "#raya-course-map" if rail == "course-map" else "#raya-learning-rail"
    header_selector = (
        ".raya-course-map-header" if rail == "course-map" else ".raya-learning-rail-header"
    )
    page = browser.new_page(viewport={"width": width, "height": 900})
    try:
        page.goto(
            f"{base_url}/authoring-matrix/index.html",
            wait_until="networkidle",
        )
        already_expanded = page.evaluate(
            "(stateName) => document.documentElement.dataset[stateName] === 'expanded'",
            state_name,
        )
        if not already_expanded:
            page.click(f"[data-raya-{rail}-expand]")
        # Even when already expanded on load, wait for any in-flight
        # transition (the header is display:none during the 240ms
        # expand/collapse animation window) to finish before measuring.
        page.wait_for_function(
            """([stateName, selector, transitionName]) =>
              document.documentElement.dataset[stateName] === 'expanded'
              && !document.querySelector(selector)?.dataset[transitionName]""",
            arg=[state_name, rail_selector, transition_name],
        )
        return page.evaluate(
            "(sel) => document.querySelector(sel).getBoundingClientRect().height",
            header_selector,
        )
    finally:
        page.close()


def test_rail_header_height_parity_across_widths(tmp_path):
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        assert handle.base_url is not None
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                for width in (640, 893, 894, 1280):
                    map_height = _rail_header_height(
                        browser, handle.base_url, width, "course-map"
                    )
                    rail_height = _rail_header_height(
                        browser, handle.base_url, width, "learning-rail"
                    )
                    assert abs(map_height - rail_height) <= 1, (
                        width,
                        map_height,
                        rail_height,
                    )
            finally:
                browser.close()
    finally:
        handle.close()


def test_rail_home_link_present_and_resolves_from_nested_page(tmp_path):
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        assert handle.base_url is not None
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page()
                try:
                    page.goto(
                        f"{handle.base_url}/authoring-matrix/index.html",
                        wait_until="networkidle",
                    )
                    link = page.locator(
                        ".raya-course-map-header a.raya-course-map-home"
                    )
                    assert link.count() == 1
                    assert link.get_attribute("aria-label") == "Back to course"
                    assert link.get_attribute("aria-current") is None
                    href = link.get_attribute("href")
                    assert href and "://" not in href and not href.startswith("/")
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_course_map_collapse_is_icon_with_preserved_names(tmp_path):
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        assert handle.base_url is not None
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                try:
                    page.goto(
                        f"{handle.base_url}/authoring-matrix/index.html",
                        wait_until="networkidle",
                    )
                    data = page.evaluate(
                        """() => {
                            const b = document.querySelector('[data-raya-course-map-collapse]');
                            return {
                                text: b.textContent.trim(),
                                aria: b.getAttribute('aria-label'),
                                hasIcon: !!b.querySelector(
                                    '[data-raya-command-icon="collapse"]'
                                ),
                            };
                        }"""
                    )
                    assert data["hasIcon"] is True
                    assert data["text"] == "Hide map"
                    assert data["aria"] == "Hide course map"

                    # Regression (Task 2 review): clicking the collapse toggle
                    # triggers shell.js's syncCourseMapToggleButtons(), which
                    # calls setButtonLabel() on every toggle button sharing this
                    # aria-controls target. setButtonLabel() must update only the
                    # text node, not overwrite the button's innerHTML -- doing so
                    # would destroy the icon <svg> sibling. Assert the icon
                    # survives one full sync.
                    page.click("[data-raya-course-map-collapse]")
                    page.wait_for_function(
                        """() => document.documentElement.dataset.rayaCourseMap
                          === 'collapsed'"""
                    )
                    after_toggle = page.evaluate(
                        """() => {
                            const b = document.querySelector('[data-raya-course-map-collapse]');
                            return {
                                hasIcon: !!b.querySelector(
                                    '[data-raya-command-icon="collapse"]'
                                ),
                                text: b.textContent.trim(),
                            };
                        }"""
                    )
                    assert after_toggle["hasIcon"] is True
                    assert after_toggle["text"] == "Hide map"
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_no_home_control_in_learning_rail_header(tmp_path):
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        assert handle.base_url is not None
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                try:
                    page.goto(
                        f"{handle.base_url}/authoring-matrix/index.html",
                        wait_until="networkidle",
                    )
                    # Sanity: the control does exist in the left rail header.
                    assert (
                        page.locator(
                            ".raya-course-map-header a.raya-course-map-home"
                        ).count()
                        == 1
                    )
                    # But the shared _render_rail_chrome() helper must never
                    # leak it into the learning rail's header.
                    count = page.locator(
                        ".raya-learning-rail-header a.raya-course-map-home"
                    ).count()
                    assert count == 0
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_single_aria_current_on_course_root_page(tmp_path):
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        assert handle.base_url is not None
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                try:
                    page.goto(
                        f"{handle.base_url}/index.html",
                        wait_until="networkidle",
                    )
                    # The home control never carries aria-current, so on the
                    # course root page the map tree's own root node remains
                    # the single source of "current page" truth.
                    n = page.locator(
                        '#raya-course-map a[aria-current="page"]'
                    ).count()
                    assert n == 1
                    home_link = page.locator(
                        ".raya-course-map-header a.raya-course-map-home"
                    )
                    assert home_link.count() == 1
                    assert home_link.get_attribute("aria-current") is None
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_drawer_home_before_close_and_shift_tab_wrap(tmp_path):
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        assert handle.base_url is not None
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                context = browser.new_context(viewport={"width": 390, "height": 844})
                try:
                    page = context.new_page()
                    try:
                        page.goto(
                            f"{handle.base_url}/authoring-matrix/index.html",
                            wait_until="networkidle",
                        )
                        page.click(".raya-mobile-course-map-open")
                        page.wait_for_function(
                            """() => document.documentElement
                              .dataset
                              .rayaCourseMapDrawer === 'open'"""
                        )
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-course-map')
                              ?.contains(document.activeElement)"""
                        )
                        # Initial drawer focus stays on the close button, and
                        # the home link is the first focusable element inside
                        # the trap (it precedes close in DOM: header_prefix,
                        # then header_home, then the title, then close).
                        initial = page.evaluate(
                            """() => {
                              const map = document.querySelector('#raya-course-map');
                              const focusable = Array.from(
                                map.querySelectorAll('a[href], button, input, [tabindex]')
                              ).filter((el) => el.tabIndex >= 0 && el.checkVisibility());
                              return {
                                activeIsClose: document.activeElement?.matches(
                                  '[data-raya-course-map-close]'
                                ),
                                firstFocusableIsHome: focusable[0]?.matches(
                                  '.raya-course-map-home'
                                ),
                              };
                            }"""
                        )
                        assert initial["activeIsClose"] is True
                        assert initial["firstFocusableIsHome"] is True

                        page.keyboard.press("Shift+Tab")
                        after_shift_tab = page.evaluate(
                            """() => ({
                              activeIsHome: document.activeElement?.matches(
                                '.raya-course-map-home'
                              ),
                            })"""
                        )
                        assert after_shift_tab["activeIsHome"] is True
                    finally:
                        page.close()
                finally:
                    context.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_collapsed_rail_exposes_one_visible_control(tmp_path):
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        assert handle.base_url is not None
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                try:
                    page.goto(
                        f"{handle.base_url}/authoring-matrix/index.html",
                        wait_until="networkidle",
                    )
                    page.click("[data-raya-course-map-collapse]")
                    page.wait_for_function(
                        """() => document.documentElement.dataset.rayaCourseMap
                          === 'collapsed'"""
                    )
                    page.wait_for_function(
                        """() => !document
                          .querySelector('#raya-course-map')
                          ?.dataset
                          ?.rayaCourseMapTransition"""
                    )
                    state = page.evaluate(
                        """() => {
                          const header = document.querySelector(
                            '.raya-course-map-header'
                          );
                          const home = document.querySelector(
                            '.raya-course-map-header a.raya-course-map-home'
                          );
                          const expand = document.querySelector(
                            '[data-raya-course-map-expand]'
                          );
                          return {
                            headerVisible: header.checkVisibility(),
                            homeVisible: home.checkVisibility(),
                            expandVisible: expand.checkVisibility(),
                          };
                        }"""
                    )
                    assert state["headerVisible"] is False
                    assert state["homeVisible"] is False
                    assert state["expandVisible"] is True
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


@contextlib.contextmanager
def _serve_directory(directory: Path):
    # Local re-implementation of tests/e2e/test_static_read_path._serve: a
    # plain ThreadingHTTPServer over a built site directory. This fixture's
    # site has no site/index.html (two depth-0 roots, no zero-order index),
    # and raya_cli.preview.create_preview() refuses to start a server at all
    # when the entrypoint is missing (its _validate_site() adds a hard error
    # and create_preview() returns a handle with base_url is None) -- that
    # gate is about preview's own single-landing-page contract and is
    # unrelated to the rail home-control gate under test here. Serving the
    # directory directly lets the test reach a real page in this course
    # shape without touching that unrelated preview behavior.
    handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(  # noqa: E731
        *args,
        directory=str(directory),
        **kwargs,
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_home_control_omitted_when_no_index_root(tmp_path):
    from playwright.sync_api import sync_playwright
    from raya_schema import validate_course
    from raya_static import build_course

    # rail-two-root-fixture has two depth-0 files (course/1_alpha.md,
    # course/2_beta.md) and no 0_/00_ index, so content_model.root_id stays
    # unset. Task 3's home control is gated on `root_id is not None`, so it
    # must never render here -- there is no single course landing page to
    # link back to.
    course = tmp_path / "rail-two-root-fixture"
    shutil.copytree(TWO_ROOT_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))

    validation_report = validate_course(course)
    assert validation_report.ok, [
        diagnostic.format() for diagnostic in validation_report.diagnostics
    ]
    build_report = build_course(course)
    assert build_report.ok, [
        diagnostic.format() for diagnostic in build_report.diagnostics
    ]

    site_dir = course / "artifact" / "site"
    # No single course landing page for a two-root, no-index course.
    assert not (site_dir / "index.html").is_file()

    with _serve_directory(site_dir) as base_url:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page()
                try:
                    page.goto(
                        f"{base_url}/alpha/index.html",
                        wait_until="networkidle",
                    )
                    assert page.locator("a.raya-course-map-home").count() == 0
                finally:
                    page.close()
            finally:
                browser.close()
