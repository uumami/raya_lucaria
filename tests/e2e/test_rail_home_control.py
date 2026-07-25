import os
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RENDER_FIXTURE = ROOT / "examples" / "courses" / "render-fixture"


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
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
