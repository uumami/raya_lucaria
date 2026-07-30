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
