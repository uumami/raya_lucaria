import os
import re
import shutil
from pathlib import Path

import pytest

import raya_static.rendering as rendering_module
from raya_static.rendering import rich_render_css
from raya_static.shell import shell_resources
from raya_static.shell_prepaint import shell_prepaint_javascript
from raya_static.shell_geometry import (
    _TOKENS,
    RAIL_APPROVED_PX,
    RAIL_EFFECTIVE_DERIVATION_JS,
)

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


def test_rail_geometry_is_single_sourced_across_scripts():
    runtime = shell_resources().javascript
    prepaint = shell_prepaint_javascript()
    # No un-substituted tokens leak into emitted scripts.
    for token in ("__RAYA_STRUCTURAL_PX__", "__RAYA_APPROVED_PX__",
                  "__RAYA_DESKTOP_PX__", "__RAYA_RAIL_DERIVATION__"):
        assert token not in runtime, token
        assert token not in prepaint, token
    # Boundaries agree across scripts.
    assert "(min-width: 894px)" in runtime
    assert "894" in prepaint and "640" in prepaint and "640" in runtime
    # The pairwise derivation is byte-identical in both scripts (no rule drift).
    assert RAIL_EFFECTIVE_DERIVATION_JS in runtime
    assert RAIL_EFFECTIVE_DERIVATION_JS in prepaint


def test_css_and_js_share_the_same_rail_boundaries():
    # The approved-geometry complement token must exist in the single source
    # of truth (guards against the CSS boundary being re-hardcoded instead
    # of derived from RAIL_APPROVED_PX).
    assert _TOKENS["__RAYA_APPROVED_MINUS_PX__"] == str(RAIL_APPROVED_PX - 1)

    # Assert against the UN-SUBSTITUTED template source, not the substituted
    # output. rich_render_css() resolves tokens before returning, so checking
    # only its output can never distinguish "value happens to match" from
    # "value is sourced from the shared token" — a hardcoded literal that
    # equals the current token value would pass an output-only check and
    # silently reintroduce drift risk the next time RAIL_APPROVED_PX etc.
    # change. Reading the template source is what actually proves the
    # rail-collapse @media boundaries are token-sourced.
    source = Path(rendering_module.__file__).read_text(encoding="utf-8")
    assert "(min-width: __RAYA_STRUCTURAL_PX__px)" in source
    assert "(min-width: __RAYA_APPROVED_PX__px)" in source
    assert "(max-width: __RAYA_APPROVED_MINUS_PX__px)" in source

    # And the substituted output is still the final, token-free CSS with the
    # expected resolved boundaries (belt-and-suspenders on top of the
    # source-level check above).
    css = rich_render_css()
    for token in ("__RAYA_STRUCTURAL_PX__", "__RAYA_APPROVED_PX__",
                  "__RAYA_DESKTOP_PX__", "__RAYA_APPROVED_MINUS_PX__"):
        assert token not in css, token
    # The approved-geometry boundary appears in CSS exactly as in JS.
    assert "(min-width: 894px)" in css
    # Its complement is emitted from the same source (guards the sub-pixel gap).
    assert "(max-width: 893px)" in css
    # The structural boundary is shared too.
    assert "(min-width: 640px)" in css


def test_collapse_selectors_key_off_html_only():
    css = rich_render_css()
    offenders = []
    for line in css.splitlines():
        if "data-raya-course-map=" not in line and "data-raya-learning-rail=" not in line:
            continue
        if "-transition" in line or "-drawer" in line or "-preference" in line:
            continue  # animation/drawer/preference channels are exempt element attrs
        # Element-mirror forms that go dead when the mirror write is removed:
        if re.search(r"\.raya-course-map\[data-raya-course-map=", line) \
           or re.search(r"\.raya-learning-rail\[data-raya-learning-rail=", line) \
           or re.search(r"\.raya-learning-shell\[data-raya-course-map=", line) \
           or re.search(r"\.raya-learning-shell\[data-raya-learning-rail=", line):
            offenders.append(line.strip())
    assert offenders == [], offenders


def test_no_id_selectors_reference_collapse_state():
    css = rich_render_css()
    offenders = []
    collapse_state_markers = (
        "data-raya-course-map=",
        "data-raya-learning-rail=",
        # The prepaint-pending skeleton gates the SAME toggle/expand chip
        # elements the html-only collapse-state rules style (see
        # test_collapse_selectors_key_off_html_only), just via the
        # shell-prepaint/shell-ready temporal signal instead of the
        # collapse-state attribute directly. Every other prepaint-pending
        # rule in this file already targets these elements by class (see
        # e.g. the html[data-raya-shell-ready="true"] .raya-course-map-*
        # rules), so an #id selector here is the same specificity-cliff
        # bug the collapse-state markers above catch, just spelled
        # differently.
        "data-raya-shell-prepaint=",
        "data-raya-shell-ready=",
    )
    for line in css.splitlines():
        if "#raya-course-map" not in line and "#raya-learning-rail" not in line:
            continue
        if any(marker in line for marker in collapse_state_markers):
            offenders.append(line.strip())
    assert offenders == [], offenders


def _collapsed_chip(page, rail_sel):
    return page.evaluate(
        """(sel) => {
          const rail = document.querySelector(sel);
          const controls = Array.from(rail.querySelectorAll('a,button')).filter((el) => {
            const b = el.getBoundingClientRect();
            return b.width > 1 && b.height > 1 && getComputedStyle(el).visibility !== 'hidden';
          });
          const chip = controls[0];
          const cb = chip ? chip.getBoundingClientRect() : null;
          const header = rail.querySelector('.raya-course-map-header,.raya-learning-rail-header');
          const body = rail.querySelector('#raya-course-map-body,#raya-learning-rail-body');
          const shown = (el) => el && getComputedStyle(el).display !== 'none';
          return {
            controlCount: controls.length,
            w: cb ? Math.round(cb.width) : null,
            h: cb ? Math.round(cb.height) : null,
            top: cb ? Math.round(cb.top) : null,
            headerShown: shown(header),
            bodyShown: shown(body),
          };
        }""",
        rail_sel,
    )


def test_collapsed_rails_are_single_clean_chips(tmp_path):
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=str(_browser_executable()),
                                        headless=True, args=["--no-sandbox"])
            try:
                tops_left = []
                tops_right = []
                for width in (768, 894, 1280, 1440):
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                    # Drive both rails collapsed via their html state.
                    page.evaluate("""() => {
                      const r = document.documentElement;
                      r.dataset.rayaCourseMap = 'collapsed';
                      r.dataset.rayaLearningRail = 'collapsed';
                    }""")
                    page.wait_for_timeout(320)
                    left = _collapsed_chip(page, "#raya-course-map")
                    right = _collapsed_chip(page, "#raya-learning-rail")
                    for side in (left, right):
                        assert side["controlCount"] == 1, (width, side)
                        assert 36 <= side["w"] <= 48 and 36 <= side["h"] <= 48, (width, side)
                        assert side["headerShown"] is False, (width, side)
                        assert side["bodyShown"] is False, (width, side)
                    assert left["w"] == right["w"] and left["h"] == right["h"], (width, left, right)
                    tops_left.append(left["top"])
                    tops_right.append(right["top"])
                    overflow = page.evaluate(
                        "() => Math.ceil(document.documentElement.scrollWidth - innerWidth)")
                    assert overflow <= 1, (width, overflow)
                    page.close()
                # Chip vertical placement is width-invariant across the whole
                # >=640 band — no per-band top offset (guards against
                # reintroducing e.g. a vertically-centered desktop band).
                assert len(set(tops_left)) == 1, tops_left
                assert len(set(tops_right)) == 1, tops_right
            finally:
                browser.close()
    finally:
        handle.close()


def test_learning_rail_inert_is_width_gated_via_shared_helper():
    # Both rail bodies must derive own-state inert through ONE shared,
    # width-gated helper (isStructuralRailShell() && collapsed) — the same
    # pattern the map body already uses. Before this fix, the learning-rail
    # toggle path (setLearningRailExpanded) set inert unconditionally on
    # `!nextExpanded` with no width gate; that specific assignment is
    # unobservable from outside the module because the SAME function
    # unconditionally calls syncLearningRailDrawerState() immediately
    # afterward, which re-derives the correct width-gated value and masks
    # the bug before any external read can see it. A black-box DOM read
    # (see test_phone_right_rail_never_own_state_inert) therefore cannot
    # distinguish the buggy code from the fixed code — this source-level
    # assertion is what actually goes red for the missing refactor.
    js = shell_resources().javascript
    assert "function applyRailBodyInert(" in js, js
    assert "applyRailBodyInert(learningRailBody, !nextExpanded)" in js, js
    assert "applyRailBodyInert(mapBody, !nextExpanded)" in js, js
    # The old unconditional (non-width-gated) assignment must be gone from
    # the toggle path.
    assert "setElementInert(learningRailBody, !nextExpanded)" not in js, js


def test_phone_right_rail_never_own_state_inert(tmp_path):
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=str(_browser_executable()),
                                        headless=True, args=["--no-sandbox"])
            try:
                page = browser.new_page(viewport={"width": 390, "height": 780})
                page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                page.wait_for_timeout(120)
                state = page.evaluate("""() => {
                  const body = document.querySelector('#raya-learning-rail-body');
                  return { ariaHidden: body.getAttribute('aria-hidden'),
                           inert: body.hasAttribute('inert') };
                }""")
                # Phone: right rail body is reachable (not own-state inert), drawer closed.
                assert state["ariaHidden"] != "true", state
                assert state["inert"] is False, state
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_expanded_rails_do_not_overflow_at_894_band(tmp_path):
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=str(_browser_executable()),
                                        headless=True, args=["--no-sandbox"])
            try:
                for width in (894, 1000, 1152, 1279):
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                    page.evaluate("""() => {
                      const r = document.documentElement;
                      r.dataset.rayaCourseMap = 'expanded';
                      r.dataset.rayaLearningRail = 'expanded';
                    }""")
                    page.wait_for_timeout(120)
                    overflow = page.evaluate(
                        "() => Math.ceil(document.documentElement.scrollWidth - innerWidth)")
                    assert overflow <= 1, (width, overflow)
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
