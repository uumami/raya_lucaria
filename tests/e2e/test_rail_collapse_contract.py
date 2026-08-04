import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

import raya_static.rendering as rendering_module
from raya_static.rendering import rich_render_css
from raya_static.shell import shell_resources
from raya_static.shell_prepaint import shell_prepaint_javascript
from raya_static.shell_geometry import (
    _TOKENS,
    RAIL_APPROVED_PX,
    RAIL_EXPANDED_PX,
    RAIL_MINI_PX,
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


def test_navigation_rail_geometry_tokens_are_single_sourced():
    assert RAIL_EXPANDED_PX == 256
    assert RAIL_MINI_PX == 48
    for resource in (
        rich_render_css(),
        shell_resources().javascript,
        shell_prepaint_javascript(),
    ):
        assert "__RAYA_RAIL_EXPANDED_PX__" not in resource
        assert "__RAYA_RAIL_MINI_PX__" not in resource


def _evaluate_intermediate_derivation(course_map: str, learning_rail: str):
    script = f"""
{RAIL_EFFECTIVE_DERIVATION_JS}
const result = rayaEffectiveRailState(
  {json.dumps(course_map)},
  {json.dumps(learning_rail)},
  {{structural: true, approved: false}}
);
process.stdout.write(JSON.stringify(result));
"""
    completed = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_intermediate_effective_state_prefers_left_without_focus():
    result = _evaluate_intermediate_derivation("expanded", "expanded")
    assert result == {"courseMap": "expanded", "learningRail": "collapsed"}


def test_prepaint_uses_deterministic_boundary_state_table(tmp_path):
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    storage_key = "raya:reader-shell:v1:render-fixture"
    saved_pairs = (
        None,
        ("collapsed", "collapsed"),
        ("expanded", "collapsed"),
        ("collapsed", "expanded"),
        ("expanded", "expanded"),
    )
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                for width in (894, 893, 640, 639):
                    for saved_pair in saved_pairs:
                        page = browser.new_page(viewport={"width": width, "height": 900})
                        if saved_pair is not None:
                            record = {
                                "courseMap": saved_pair[0],
                                "learningRail": saved_pair[1],
                            }
                            serialized = json.dumps(record, separators=(",", ":"))
                            page.add_init_script(
                                "sessionStorage.setItem("
                                f"{json.dumps(storage_key)}, {json.dumps(serialized)}"
                                ");"
                            )
                        page.route("**/shell.js", lambda route: route.abort())
                        try:
                            page.goto(
                                f"{handle.base_url}/reader-ux/index.html",
                                wait_until="networkidle",
                            )
                            actual = page.evaluate(
                                """() => {
                                  const root = document.documentElement;
                                  return {
                                    prepaint: root.dataset.rayaShellPrepaint,
                                    courseMap: root.dataset.rayaCourseMap,
                                    learningRail: root.dataset.rayaLearningRail,
                                  };
                                }"""
                            )
                            if width < RAIL_STRUCTURAL_PX:
                                expected_pair = ("expanded", "expanded")
                            elif width < RAIL_APPROVED_PX:
                                requested = saved_pair or ("expanded", "collapsed")
                                expected_pair = (
                                    ("expanded", "collapsed")
                                    if requested == ("expanded", "expanded")
                                    else requested
                                )
                            else:
                                expected_pair = saved_pair or ("expanded", "expanded")
                            assert actual == {
                                "prepaint": "missing" if saved_pair is None else "valid",
                                "courseMap": expected_pair[0],
                                "learningRail": expected_pair[1],
                            }, (width, saved_pair, actual)
                        finally:
                            page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_runtime_intermediate_reconciliation_prefers_focused_rail(tmp_path):
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    storage_key = "raya:reader-shell:v1:render-fixture"
    serialized = json.dumps(
        {"courseMap": "expanded", "learningRail": "expanded"},
        separators=(",", ":"),
    )
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 894, "height": 900})
                page.add_init_script(
                    "sessionStorage.setItem("
                    f"{json.dumps(storage_key)}, {json.dumps(serialized)}"
                    ");"
                )
                try:
                    page.goto(
                        f"{handle.base_url}/reader-ux/index.html",
                        wait_until="networkidle",
                    )
                    page.focus("[data-raya-learning-rail-collapse]")
                    page.set_viewport_size({"width": 893, "height": 900})
                    page.wait_for_function(
                        """() => document.documentElement.dataset.rayaCourseMap === 'collapsed'
                          && document.documentElement.dataset.rayaLearningRail === 'expanded'"""
                    )
                    state = page.evaluate(
                        """() => ({
                          courseMap: document.documentElement.dataset.rayaCourseMap,
                          learningRail: document.documentElement.dataset.rayaLearningRail,
                          focusInLearningRail: document.querySelector(
                            '#raya-learning-rail'
                          ).contains(document.activeElement),
                        })"""
                    )
                    assert state == {
                        "courseMap": "collapsed",
                        "learningRail": "expanded",
                        "focusInLearningRail": True,
                    }
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_runtime_intermediate_reconciliation_preserves_focus_for_valid_pair(tmp_path):
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    storage_key = "raya:reader-shell:v1:render-fixture"
    serialized = json.dumps(
        {"courseMap": "collapsed", "learningRail": "expanded"},
        separators=(",", ":"),
    )
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 894, "height": 900})
                page.add_init_script(
                    "sessionStorage.setItem("
                    f"{json.dumps(storage_key)}, {json.dumps(serialized)}"
                    ");"
                )
                try:
                    page.goto(
                        f"{handle.base_url}/reader-ux/index.html",
                        wait_until="networkidle",
                    )
                    page.focus("[data-raya-course-map-expand]")
                    page.set_viewport_size({"width": 893, "height": 900})
                    page.wait_for_timeout(120)
                    state = page.evaluate(
                        """() => ({
                          courseMap: document.documentElement.dataset.rayaCourseMap,
                          learningRail: document.documentElement.dataset.rayaLearningRail,
                          focusedCourseMapExpand:
                            document.activeElement.hasAttribute(
                              'data-raya-course-map-expand'
                            ),
                        })"""
                    )
                    assert state == {
                        "courseMap": "collapsed",
                        "learningRail": "expanded",
                        "focusedCourseMapExpand": True,
                    }
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_intermediate_handoff_has_one_atomic_pair_application_path():
    javascript = shell_resources().javascript
    assert "function applyStructuralRailPair(" in javascript
    assert "const next = reconcileRailPair(" in javascript
    assert "applyStructuralRailPair(" in javascript


def test_intermediate_handoff_transition_table(tmp_path):
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    storage_key = "raya:reader-shell:v1:render-fixture"
    cases = (
        (None, None, ("expanded", "collapsed")),
        (("collapsed", "collapsed"), None, ("collapsed", "collapsed")),
        (("expanded", "collapsed"), None, ("expanded", "collapsed")),
        (("collapsed", "expanded"), None, ("collapsed", "expanded")),
        (("expanded", "expanded"), None, ("expanded", "collapsed")),
        (("expanded", "expanded"), "left", ("expanded", "collapsed")),
        (("expanded", "expanded"), "right", ("collapsed", "expanded")),
    )
    try:
        assert handle.report.ok
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                for width in (893, 640):
                    for saved_pair, focus_owner, expected in cases:
                        initial_width = 894 if focus_owner else width
                        page = browser.new_page(
                            viewport={"width": initial_width, "height": 900}
                        )
                        if saved_pair is not None:
                            serialized = json.dumps(
                                {
                                    "courseMap": saved_pair[0],
                                    "learningRail": saved_pair[1],
                                },
                                separators=(",", ":"),
                            )
                            page.add_init_script(
                                "sessionStorage.setItem("
                                f"{json.dumps(storage_key)}, {json.dumps(serialized)}"
                                ");"
                            )
                        try:
                            page.goto(
                                f"{handle.base_url}/reader-ux/index.html",
                                wait_until="networkidle",
                            )
                            if focus_owner == "left":
                                page.focus("[data-raya-course-map-collapse]")
                            elif focus_owner == "right":
                                page.focus("[data-raya-learning-rail-collapse]")
                            if focus_owner:
                                page.set_viewport_size({"width": width, "height": 900})
                            page.wait_for_function(
                                "([courseMap, learningRail]) => "
                                "document.documentElement.dataset.rayaCourseMap === courseMap "
                                "&& document.documentElement.dataset.rayaLearningRail === learningRail",
                                arg=list(expected),
                            )
                            page.wait_for_timeout(320)
                            state = page.evaluate(
                                """() => {
                                  const root = document.documentElement;
                                  const map = document.querySelector('#raya-course-map');
                                  const rail = document.querySelector('#raya-learning-rail');
                                  const article = document.querySelector('#raya-article');
                                  const mapBody = document.querySelector('#raya-course-map-body');
                                  const railBody = document.querySelector('#raya-learning-rail-body');
                                  const horizontalIntersection = (left, right) => {
                                    const a = left.getBoundingClientRect();
                                    const b = right.getBoundingClientRect();
                                    return a.left < b.right && a.right > b.left;
                                  };
                                  const active = document.activeElement;
                                  return {
                                    pair: [
                                      root.dataset.rayaCourseMap,
                                      root.dataset.rayaLearningRail,
                                    ],
                                    fullRails: [
                                      root.dataset.rayaCourseMap,
                                      root.dataset.rayaLearningRail,
                                    ].filter((value) => value === 'expanded').length,
                                    mapIntersectsArticle: horizontalIntersection(map, article),
                                    railIntersectsArticle: horizontalIntersection(rail, article),
                                    mapBodyInert: mapBody.inert,
                                    railBodyInert: railBody.inert,
                                    focusInInert: !!active?.closest('[inert]'),
                                    focusVisible: !active || active === document.body
                                      || active.checkVisibility(),
                                  };
                                }"""
                            )
                            assert state["pair"] == list(expected), (
                                width,
                                saved_pair,
                                focus_owner,
                                state,
                            )
                            assert state["fullRails"] <= 1, state
                            case_state = (width, saved_pair, focus_owner, state)
                            assert state["mapIntersectsArticle"] is False, case_state
                            assert state["railIntersectsArticle"] is False, case_state
                            assert state["mapBodyInert"] is (expected[0] == "collapsed"), state
                            assert state["railBodyInert"] is (
                                expected[1] == "collapsed"
                            ), state
                            assert state["focusInInert"] is False, state
                            assert state["focusVisible"] is True, state
                        finally:
                            page.close()
            finally:
                browser.close()
    finally:
        handle.close()


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


def _collapsed_course_map_state(page):
    return page.evaluate(
        """() => {
          const rail = document.querySelector('#raya-course-map');
          const mini = rail.querySelector('[data-raya-course-map-mini]');
          const header = rail.querySelector('.raya-course-map-header');
          const body = rail.querySelector('#raya-course-map-body');
          const article = document.querySelector('#raya-article');
          const railBox = rail.getBoundingClientRect();
          const miniBox = mini.getBoundingClientRect();
          const articleBox = article.getBoundingClientRect();
          const visibleControls = Array.from(mini.querySelectorAll('a,button')).filter(
            (control) => control.checkVisibility()
          );
          const tabbables = Array.from(
            body.querySelectorAll('a[href],button,input,select,textarea,summary,[tabindex]')
          ).filter((element) => element.tabIndex >= 0 && !element.disabled);
          return {
            railWidth: railBox.width,
            miniVisible: mini.checkVisibility(),
            miniWidth: miniBox.width,
            miniLabels: visibleControls.map(
              (control) => control.getAttribute('aria-label') || control.textContent.trim()
            ),
            bodyHidden: body.getAttribute('aria-hidden'),
            bodyInert: body.inert && body.hasAttribute('inert'),
            bodyTabbables: tabbables.length,
            headerHidden: header.getAttribute('aria-hidden'),
            headerInert: header.inert && header.hasAttribute('inert'),
            articleDoesNotIntersectMini:
              articleBox.left >= miniBox.right || articleBox.right <= miniBox.left,
          };
        }"""
    )


def test_collapsed_course_map_is_a_structural_mini_rail(tmp_path):
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
                for width in (640, 768, 894, 1280, 1440):
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                    expanded = page.evaluate(
                        """() => {
                          const mini = document.querySelector('[data-raya-course-map-mini]');
                          return {
                            display: getComputedStyle(mini).display,
                            ariaHidden: mini.getAttribute('aria-hidden'),
                            inert: mini.inert && mini.hasAttribute('inert'),
                          };
                        }"""
                    )
                    assert expanded == {
                        "display": "none",
                        "ariaHidden": "true",
                        "inert": True,
                    }, (width, expanded)
                    page.click("[data-raya-course-map-collapse]")
                    page.wait_for_function(
                        """() => document.documentElement.dataset.rayaCourseMap
                          === 'collapsed'"""
                    )
                    page.wait_for_timeout(320)
                    state = _collapsed_course_map_state(page)
                    assert 47 <= state["railWidth"] <= 49, (width, state)
                    assert 47 <= state["miniWidth"] <= 49, (width, state)
                    assert state["miniVisible"] is True, (width, state)
                    assert state["miniLabels"] == [
                        "Back to course",
                        "Expand course map",
                        "Text size: normal",
                        "Toggle OpenDyslexic font",
                    ], (width, state)
                    assert state["bodyHidden"] == "true", (width, state)
                    assert state["bodyInert"] is True, (width, state)
                    assert state["bodyTabbables"] == 0, (width, state)
                    assert state["headerHidden"] == "true", (width, state)
                    assert state["headerInert"] is True, (width, state)
                    assert state["articleDoesNotIntersectMini"] is True, (width, state)

                    mini_snapshot = page.locator(
                        "[data-raya-course-map-mini]"
                    ).aria_snapshot()
                    body_snapshot = page.locator("#raya-course-map-body").aria_snapshot()
                    for label in state["miniLabels"]:
                        assert label in mini_snapshot, (width, mini_snapshot)
                    assert body_snapshot == "", (width, body_snapshot)
                    overflow = page.evaluate(
                        "() => Math.ceil(document.documentElement.scrollWidth - innerWidth)")
                    assert overflow <= 1, (width, overflow)
                    page.close()

                page = browser.new_page(viewport={"width": 639, "height": 900})
                page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                assert page.locator("[data-raya-course-map-mini]").evaluate(
                    "mini => getComputedStyle(mini).display"
                ) == "none"
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_mini_controls_have_unclipped_three_pixel_focus_indicators(tmp_path):
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=str(_browser_executable()),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 640, "height": 900})
                page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                page.click("[data-raya-course-map-collapse]")
                page.wait_for_timeout(320)
                controls = page.locator(
                    ".raya-course-map-mini > a, .raya-course-map-mini > button"
                )
                assert controls.count() == 4
                page.evaluate(
                    """() => {
                      if (document.activeElement instanceof HTMLElement) {
                        document.activeElement.blur();
                      }
                    }"""
                )
                unfocused_boxes = controls.evaluate_all(
                    """controls => controls.map((control) => {
                      if (control === document.activeElement) {
                        throw new Error('mini control remained focused before baseline');
                      }
                      const box = control.getBoundingClientRect();
                      return {
                        x: box.x,
                        y: box.y,
                        width: box.width,
                        height: box.height,
                      };
                    })"""
                )
                # Seed focus on Expand without focus-visible, then enter keyboard
                # modality and move backward so traversal starts at Home.
                controls.nth(1).focus()
                page.keyboard.press("Shift+Tab")
                for index in range(controls.count()):
                    control = controls.nth(index)
                    state = control.evaluate(
                        """control => {
                          const style = getComputedStyle(control);
                          const box = control.getBoundingClientRect();
                          const mini = control.closest('.raya-course-map-mini')
                            .getBoundingClientRect();
                          return {
                            outlineStyle: style.outlineStyle,
                            outlineWidth: parseFloat(style.outlineWidth),
                            outlineOffset: parseFloat(style.outlineOffset),
                            focused: document.activeElement === control,
                            box: {
                              x: box.x,
                              y: box.y,
                              width: box.width,
                              height: box.height,
                            },
                            contained:
                              box.left >= mini.left && box.right <= mini.right
                              && box.top >= mini.top && box.bottom <= mini.bottom,
                          };
                        }"""
                    )
                    assert state["focused"] is True, (index, state)
                    assert state["outlineStyle"] != "none", (index, state)
                    assert state["outlineWidth"] >= 3, (index, state)
                    assert state["outlineOffset"] <= -state["outlineWidth"], (
                        index,
                        state,
                    )
                    assert state["contained"] is True, (index, state)
                    assert unfocused_boxes[index] == state["box"], (
                        index,
                        unfocused_boxes[index],
                        state,
                    )
                    page.keyboard.press("Tab")
                page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_mini_and_footer_comfort_controls_stay_synchronized(tmp_path):
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
                page.evaluate("() => localStorage.clear()")
                page.click("[data-raya-course-map-collapse]")
                page.wait_for_timeout(320)
                page.click(".raya-course-map-mini .raya-text-size-toggle")
                page.click(".raya-course-map-mini .raya-font-toggle")
                state = page.evaluate("""() => {
                  const attrs = (selector) => Array.from(
                    document.querySelectorAll(selector),
                    (button) => ({
                      label: button.getAttribute('aria-label'),
                      pressed: button.getAttribute('aria-pressed'),
                    })
                  );
                  return {
                    size: attrs('#raya-course-map .raya-text-size-toggle'),
                    font: attrs('#raya-course-map .raya-font-toggle'),
                    storage: Object.keys(localStorage).sort(),
                    textSize: localStorage.getItem('raya:text-size'),
                    dyslexic: localStorage.getItem('raya:open-dyslexic'),
                  };
                }""")
                assert state["size"] == [
                    {"label": "Text size: large", "pressed": "true"},
                    {"label": "Text size: large", "pressed": "true"},
                ]
                assert state["font"] == [
                    {"label": "Toggle OpenDyslexic font", "pressed": "true"},
                    {"label": "Toggle OpenDyslexic font", "pressed": "true"},
                ]
                assert state["storage"] == ["raya:open-dyslexic", "raya:text-size"]
                assert state["textSize"] == "large"
                assert state["dyslexic"] == "true"
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


def test_course_map_navigation_keeps_usable_height_on_short_viewports(tmp_path):
    # The central navigation must retain a useful viewport between the fixed
    # header and footer. It is the only vertical scroll owner; the tree remains
    # ordinary content inside it.
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
                      const navigation = document.querySelector(
                        '.raya-course-map-navigation'
                      );
                      const list = document.querySelector('.raya-course-map-list');
                      const navigationStyle = getComputedStyle(navigation);
                      return {
                        h: Math.round(navigation.getBoundingClientRect().height),
                        navigationOverflowY: navigationStyle.overflowY,
                        navigationOverscroll: navigationStyle.overscrollBehaviorY,
                        listOverflowY: getComputedStyle(list).overflowY,
                      };
                    }""")
                    # A navigation window smaller than this cannot show even a
                    # few rows and reads as "scrolling does nothing".
                    assert geo["h"] >= 160, (height, geo)
                    assert geo["navigationOverflowY"] == "auto", (height, geo)
                    assert geo["navigationOverscroll"] == "auto", (height, geo)
                    assert geo["listOverflowY"] == "visible", (height, geo)
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()
