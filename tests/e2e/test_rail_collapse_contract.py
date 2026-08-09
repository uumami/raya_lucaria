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
    RAIL_STRUCTURAL_PX,
    RAIL_EFFECTIVE_DERIVATION_JS,
)

ROOT = Path(__file__).resolve().parents[2]
RENDER_FIXTURE = ROOT / "examples" / "courses" / "render-fixture"

_MIRROR_ATTR = re.compile(r"\[data-raya-(?:course-map|learning-rail)=")


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


# Exactly one media query in these files uses a rail-boundary number but is
# NOT a rail boundary: the discovery workspace shell. Its true partner is
# graph.py:1725 (`matchMedia("(max-width: 1279px)")`), which this test does
# not scan, so tokenizing it against a READER-rail constant would couple two
# unrelated subsystems and silently desync from graph.py. It is tracked as
# deferred debt item 5 instead. Allowlist entries must be exact full-line
# matches and must each reference a tracked debt item -- this is not a
# pattern-based skip, which is how the previous guardrail went vacuous.
_NON_RAIL_BOUNDARY_ALLOWLIST = {
    "rendering.py: @media (max-width: 1279px) {",  # debt item 5: discovery rail
}


def test_no_hardcoded_rail_boundaries_in_templates():
    # The presence-only boundary assertions let five literals survive the
    # single-sourcing refactor. Assert ABSENCE: every rail boundary in the
    # CSS/JS templates must be token-sourced, so changing a constant in
    # shell_geometry.py cannot leave a stale literal behind.
    import raya_static.shell as shell_module
    import raya_static.shell_prepaint as prepaint_module

    boundaries = ("640", "639", "894", "893", "1280", "1279", "768", "767")
    sources = {
        "rendering.py": Path(rendering_module.__file__).read_text(encoding="utf-8"),
        "shell.py": Path(shell_module.__file__).read_text(encoding="utf-8"),
        "shell_prepaint.py": Path(prepaint_module.__file__).read_text(encoding="utf-8"),
    }
    offenders = []
    for name, source in sources.items():
        for line in source.splitlines():
            if "min-width:" not in line and "max-width:" not in line:
                continue
            entry = f"{name}: {line.strip()}"
            if entry in _NON_RAIL_BOUNDARY_ALLOWLIST:
                continue
            for boundary in boundaries:
                if f"{boundary}px" in line:
                    offenders.append(entry)
    assert offenders == [], offenders


def test_rail_geometry_is_single_sourced_across_scripts():
    runtime = shell_resources().javascript
    prepaint = shell_prepaint_javascript()
    # No un-substituted tokens leak into emitted scripts.
    for token in ("__RAYA_STRUCTURAL_PX__", "__RAYA_APPROVED_PX__",
                  "__RAYA_DESKTOP_PX__", "__RAYA_RAIL_DERIVATION__"):
        assert token not in runtime, token
        assert token not in prepaint, token
    # Boundaries agree across scripts.
    assert f"(min-width: {RAIL_APPROVED_PX}px)" in runtime
    assert str(RAIL_APPROVED_PX) in prepaint and str(RAIL_STRUCTURAL_PX) in prepaint
    assert str(RAIL_STRUCTURAL_PX) in runtime
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
    assert f"(min-width: {RAIL_APPROVED_PX}px)" in css
    # Its complement is emitted from the same source (guards the sub-pixel gap).
    assert f"(max-width: {RAIL_APPROVED_PX - 1}px)" in css
    # The structural boundary is shared too.
    assert f"(min-width: {RAIL_STRUCTURAL_PX}px)" in css


def test_collapse_selectors_key_off_html_only():
    css = rich_render_css()
    offenders = []
    for line in css.splitlines():
        if "data-raya-course-map=" not in line and "data-raya-learning-rail=" not in line:
            continue
        if "-drawer" in line or "-preference" in line:
            continue  # drawer/preference channels are genuine element attrs
        # Element-mirror forms that go dead when the mirror write is removed.
        # NOTE: these regexes anchor on `data-raya-*=` immediately, so a
        # suffixed attribute (`data-raya-*-transition=`) never matches them.
        # The ancestor-rooted selectors that pair with each mirror are LIVE
        # during the 240ms transition window and are intentionally not caught.
        # Any selector that reads collapse state off a non-root element is a
        # mirror. Enumerating element classes (as before) missed mirrors on
        # `body`, `main`, or the article element entirely. A lookbehind-based
        # matcher does NOT work here: `(?<!html)` guards only the FIRST
        # attribute, so a chain like `html[data-raya-course-map=...]
        # [data-raya-learning-rail=...]` false-positives on the second.
        for compound in re.split(r"[,\s>+~]+", line):
            if _MIRROR_ATTR.search(compound) and compound.split("[", 1)[0] not in ("", "html"):
                offenders.append(line.strip())
                break
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


def test_transition_window_keeps_rail_chrome_painted(tmp_path):
    # The ancestor-rooted transition selectors are LIVE: they keep the expand
    # chip painted and the header/body hidden during the 240ms animation.
    # Without them the rail renders completely empty mid-expand.
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
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                # Collapse, settle, then start expanding and sample mid-flight.
                page.evaluate(
                    "() => { document.documentElement.dataset.rayaLearningRail = 'collapsed'; }")
                page.wait_for_timeout(320)
                page.click("[data-raya-learning-rail-expand]")
                page.wait_for_timeout(80)  # inside the 240ms window
                mid = page.evaluate("""() => {
                  const rail = document.querySelector('#raya-learning-rail');
                  const chip = rail.querySelector('.raya-learning-rail-expand');
                  const header = rail.querySelector('.raya-learning-rail-header');
                  return {
                    transition: rail.dataset.rayaLearningRailTransition || '',
                    chipShown: getComputedStyle(chip).display !== 'none',
                    headerShown: getComputedStyle(header).display !== 'none',
                  };
                }""")
                assert mid["transition"] == "expanding", mid
                assert mid["chipShown"] is True, mid
                assert mid["headerShown"] is False, mid
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()


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


def test_collapse_via_real_clicks_produces_clean_chips(tmp_path):
    # The dataset-driven test bypasses every toggle handler. This drives the
    # real interaction path: handler -> state -> persistence -> appearance.
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
                for width in (894, 1280, 1440):
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                    # [data-raya-course-map-toggle] matches three elements (the
                    # mobile-open button, the desktop "Hide map" collapse
                    # button, and the collapsed-state expand chip); the
                    # legacy page.click(selector) API picks the first DOM
                    # match regardless of visibility, which is the
                    # mobile-only button hidden at these widths. Target the
                    # unique, always-present desktop collapse control
                    # instead, mirroring [data-raya-learning-rail-collapse].
                    page.click("[data-raya-course-map-collapse]")
                    page.click("[data-raya-learning-rail-collapse]")
                    page.wait_for_timeout(320)  # past the 240ms transition
                    state = page.evaluate("""() => {
                      const r = document.documentElement;
                      return { map: r.dataset.rayaCourseMap,
                               rail: r.dataset.rayaLearningRail };
                    }""")
                    assert state == {"map": "collapsed", "rail": "collapsed"}, (width, state)
                    for sel in ("#raya-course-map", "#raya-learning-rail"):
                        side = _collapsed_chip(page, sel)
                        assert side["controlCount"] == 1, (width, sel, side)
                        assert side["headerShown"] is False, (width, sel, side)
                        assert side["bodyShown"] is False, (width, sel, side)
                    overflow = page.evaluate(
                        "() => Math.ceil(document.documentElement.scrollWidth - innerWidth)")
                    assert overflow <= 1, (width, overflow)
                    page.close()
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


def test_rail_state_derives_from_media_queries_not_inner_width():
    # JS must derive band membership from the SAME media queries CSS uses.
    # Deriving from innerWidth allows disagreement on engines where the
    # media-query width excludes a classic scrollbar: an innerWidth in
    # [640, 640+scrollbarWidth) puts JS in the structural band (state ->
    # collapsed) while CSS is still below it (body not hidden), which
    # renders a collapsed rail leaking its full body.
    runtime = shell_resources().javascript
    prepaint = shell_prepaint_javascript()
    for script, allowed_inner_width in ((runtime, 2), (prepaint, 0)):
        assert "function rayaRailBands()" in script
        assert "rayaRailBands())" in script
        # Substring assertions like `", innerWidth)" not in script` are a
        # false-pass hole: they do not match `, window.innerWidth)`, which is
        # the spelling used elsewhere in this file. Count instead. The only
        # permitted innerWidth reads are the two compact-preview geometry
        # calculations at shell.py:864,868 -- neither is a band decision.
        assert script.count("innerWidth") == allowed_inner_width, script


def test_rail_state_does_not_flip_after_first_paint(tmp_path):
    # Task 1 made band reads reactive to media queries. Verify that does not
    # produce a visible rail flip when content loads and a scrollbar appears.
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
                for width in (638, 640, 645, 648, 892, 894, 898):
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    page.add_init_script("""
                      window.__rayaFlips = [];
                      document.addEventListener('DOMContentLoaded', () => {
                        const r = document.documentElement;
                        new MutationObserver(() => {
                          window.__rayaFlips.push(r.dataset.rayaCourseMap);
                        }).observe(r, { attributes: true,
                                        attributeFilter: ['data-raya-course-map'] });
                      });
                    """)
                    page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                    page.wait_for_timeout(400)
                    flips = page.evaluate("() => window.__rayaFlips || []")
                    # Any change of VALUE after first paint is a visible flip.
                    assert len(set(flips)) <= 1, (width, flips)
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


@pytest.mark.parametrize("engine", ["chromium", "firefox", "webkit"])
def test_js_and_css_agree_on_band_membership_across_engines(tmp_path, engine):
    # Across the structural boundary, the state JS derives must match the
    # appearance CSS applies. A disagreement here is the exact shape of the
    # reported bug: state says "collapsed" while the body stays visible.
    #
    # Chromium has exact innerWidth/media-query agreement, so it alone cannot
    # detect a regression of the mismatch class Task 1 removed -- Firefox and
    # WebKit can (classic scrollbars shrink the media-query width but not
    # innerWidth in some engine/platform combinations).
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        with sync_playwright() as p:
            launcher = getattr(p, engine)
            if engine == "chromium":
                # Chromium must NEVER skip: a bare launcher.launch() finds no
                # Playwright-downloaded chromium in CI, so a blanket
                # try/except would make ALL THREE parametrizations skip and
                # the test would be green-by-skip from the day it lands.
                browser = launcher.launch(executable_path=str(_browser_executable()),
                                          headless=True, args=["--no-sandbox"])
            else:
                try:
                    browser = launcher.launch(headless=True)
                except Exception as exc:
                    if os.environ.get("RAYA_REQUIRE_ALL_ENGINES") == "1":
                        pytest.fail(f"{engine} required but unavailable: {exc}")
                    pytest.skip(f"{engine} unavailable: {exc}")
            try:
                divergences = []
                for width in (636, 639, 640, 641, 645, 655, 660, 893, 894, 900):
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                    page.wait_for_timeout(150)
                    result = page.evaluate("""() => {
                      const r = document.documentElement;
                      const body = document.querySelector('#raya-course-map-body');
                      return {
                        state: r.dataset.rayaCourseMap,
                        bodyShown: getComputedStyle(body).display !== 'none',
                        structuralMQ: matchMedia('(min-width: 640px)').matches,
                      };
                    }""")
                    probe = page.evaluate("""() => ({
                      mqStructural: matchMedia('(min-width: 640px)').matches,
                      iwStructural: innerWidth >= 640,
                    })""")
                    if probe["mqStructural"] != probe["iwStructural"]:
                        divergences.append((engine, width, probe))
                    # Collapsed state must always mean a hidden body inside the
                    # structural band. NOTE: only this half tests anything --
                    # the `not structuralMQ -> expanded` half is TAUTOLOGICAL
                    # after Task 1, because both sides now read the same
                    # matchMedia('(min-width: 640px)'). Do not over-trust it.
                    if result["structuralMQ"] and result["state"] == "collapsed":
                        assert result["bodyShown"] is False, (engine, width, result)
                    page.close()
                print(f"[{engine}] innerWidth/media-query divergences: {divergences}")
            finally:
                browser.close()
    finally:
        handle.close()


def test_collapsed_rail_never_exceeds_viewport_height(tmp_path):
    # At >=894 the collapsing rule re-granted display:block to the rail body,
    # overriding the collapse display:none, making the collapsed rail a
    # 44 x 10466px fixed element -- a latent full-page click-blocker.
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
                for width in (894, 1000, 1280, 1440):
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                    page.click("[data-raya-learning-rail-collapse]")
                    page.wait_for_timeout(100)  # mid-transition, the risky window
                    box = page.evaluate("""() => {
                      const r = document.querySelector('#raya-learning-rail');
                      const b = r.getBoundingClientRect();
                      return { w: Math.round(b.width), h: Math.round(b.height) };
                    }""")
                    assert box["h"] <= 900, (width, box)
                    page.wait_for_timeout(250)  # settled
                    settled = page.evaluate("""() => {
                      const r = document.querySelector('#raya-learning-rail');
                      const b = r.getBoundingClientRect();
                      return { w: Math.round(b.width), h: Math.round(b.height) };
                    }""")
                    assert settled["h"] <= 900, (width, settled)
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_course_map_tree_keeps_usable_height_on_short_viewports(tmp_path):
    # The course map's chrome (header, search + command tiles, page position,
    # filter label, filter) is ~398px of FIXED height. The section tree is the
    # only flex:1 1 auto item with min-height:0, so it absorbed the entire
    # squeeze and collapsed to 5px at a 520px-tall viewport -- making the
    # primary navigation unscrollable and giving the impression that the page
    # scrolls instead of the rail. The tree must keep a usable window; the
    # rail (already overflow:auto, max-height:calc(100vh - 2rem)) takes the
    # overflow instead.
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
                for height in (520, 600, 700, 900):
                    page = browser.new_page(viewport={"width": 1440, "height": height})
                    page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                    page.wait_for_timeout(300)
                    geo = page.evaluate("""() => {
                      const list = document.querySelector('.raya-course-map-list');
                      const cs = getComputedStyle(list);
                      return {
                        h: Math.round(list.getBoundingClientRect().height),
                        overflowY: cs.overflowY,
                        overscroll: cs.overscrollBehaviorY,
                      };
                    }""")
                    # A tree window smaller than this cannot show even a few
                    # rows and reads as "scrolling does nothing".
                    assert geo["h"] >= 160, (height, geo)
                    # The tree keeps its own scroll window at every height.
                    assert geo["overflowY"] == "auto", (height, geo)
                    # overscroll-behavior:contain was deliberately removed
                    # from .raya-course-map-list (2026-07-29
                    # reader-rail-density, Task 5): once the rail's fixed
                    # chrome got short enough, a short course's tree could
                    # fit without overflowing, and a non-overflowing
                    # overflow:auto + overscroll-behavior:contain element
                    # still gets swallowed by Chrome on wheel -- reintroducing
                    # exactly "scrolling does nothing", the failure mode this
                    # test exists to guard against. The real, user-facing
                    # property (no dead wheel zones, on both a tree that
                    # fits and one that overflows) is now enforced by
                    # tests/e2e/test_rail_density.py::
                    # test_wheel_over_any_rail_region_moves_something.
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_workspace_course_map_has_one_usable_tree_scroll_region(tmp_path):
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                for width in (1366, 390):
                    page = browser.new_page(viewport={"width": width, "height": 844})
                    try:
                        page.goto(
                            f"{handle.base_url}/_raya/search/index.html",
                            wait_until="networkidle",
                        )
                        if width == 390:
                            page.locator(".raya-mobile-course-map-open").focus()
                            page.keyboard.press("Enter")
                            page.wait_for_function(
                                "() => document.documentElement.dataset.rayaCourseMapDrawer === 'open'"
                            )
                        page.locator(
                            "#raya-course-map [data-raya-map-node-toggle]"
                        ).first.click()
                        regions = page.evaluate(
                            """() => Array.from(document.querySelectorAll(
                              '#raya-course-map .raya-course-map-list'
                            ))
                              .filter((region) => region.checkVisibility())
                              .map((region) => ({
                                clientHeight: region.clientHeight,
                                scrollHeight: region.scrollHeight,
                                overflowY: getComputedStyle(region).overflowY,
                              }))"""
                        )
                        assert len(regions) == 1, (width, regions)
                        assert regions[0]["clientHeight"] >= 80, (width, regions)
                        assert regions[0]["overflowY"] == "auto", (width, regions)
                        if regions[0]["scrollHeight"] > regions[0]["clientHeight"]:
                            scroll_top = page.locator(
                                "#raya-course-map .raya-course-map-list"
                            ).evaluate(
                                "region => { region.scrollTop = region.scrollHeight; "
                                "return region.scrollTop; }"
                            )
                            assert scroll_top > 0, (width, regions)
                        overflow = page.evaluate(
                            "() => Math.ceil(document.documentElement.scrollWidth - innerWidth)"
                        )
                        assert overflow <= 1, (width, overflow)
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()
