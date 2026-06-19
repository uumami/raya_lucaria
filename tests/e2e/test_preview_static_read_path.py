from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import threading
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen

import pytest
from raya_cli.render_debug import (
    RENDER_DEBUG_PAGE_NAMES,
    RENDER_DEBUG_VIEWPORTS,
    _reset_render_debug_dir,
    capture_render_debug,
    raw_tex_markers_from_text,
    record_external_request,
    viewport_name,
)
from raya_schema import ValidationReport

ROOT = Path(__file__).resolve().parents[2]
EXECUTION_FIXTURE = ROOT / "examples" / "courses" / "execution-fixture"
REFERENCE_FIXTURE = ROOT / "examples" / "courses" / "reference-fixture"
RENDER_FIXTURE = ROOT / "examples" / "courses" / "render-fixture"
EXAMPLES_GALLERY = ROOT / "examples" / "gallery"


def test_preview_serves_static_pages_files_reviewed_outputs_and_inspection(
    tmp_path: Path,
) -> None:
    from raya_cli.preview import create_preview

    course = tmp_path / "execution-fixture"
    shutil.copytree(EXECUTION_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        base_url = handle.base_url
        assert base_url is not None

        root_html = _fetch_text(f"{base_url}/index.html")
        inspection_html = _fetch_text(f"{base_url}/_raya/inspect/index.html")
        manual_script = _fetch_text(f"{base_url}/_raya/files/_source/code/manual_task.py")
        reviewed_stdout = _fetch_text(
            f"{base_url}/_raya/reviewed/frozen-script/stdout.txt"
        )
    finally:
        handle.close()

    assert "Local Execution Fixture" in root_html
    assert 'href="_raya/files/_source/code/manual_task.py"' in root_html
    assert 'href="_raya/reviewed/frozen-script/stdout.txt"' in root_html
    assert 'data-raya-surface="inspection"' in inspection_html
    assert "manual execution sentinel" in manual_script
    assert reviewed_stdout == "frozen reviewed output fixture\n"
    assert not (course / "execution-side-effect.txt").exists()
    assert not (course / "artifact" / "data" / "execution-results.json").exists()


def test_preview_serves_local_assets(tmp_path: Path) -> None:
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        base_url = handle.base_url
        assert base_url is not None
        root_html = _fetch_text(f"{base_url}/index.html")
        local_asset = _fetch_text(
            f"{base_url}/_raya/assets/_source/_local/diagrams/static-path.txt"
        )
        math_css = _fetch_text(f"{base_url}/_raya/render/math/mathjax.css")
        math_font_names = _local_math_font_names_from_css(math_css)
        math_fonts = [
            _fetch_bytes(f"{base_url}/_raya/render/math/fonts/{name}")
            for name in math_font_names
        ]
    finally:
        handle.close()

    assert 'href="_raya/assets/_source/_local/diagrams/static-path.txt"' in root_html
    assert "Raya Lucaria render fixture asset" in local_asset
    assert "mjx-container" in math_css
    assert math_font_names
    assert all(len(font) > 0 for font in math_fonts)


def test_render_fixture_applies_course_and_section_skins(tmp_path: Path) -> None:
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        base_url = handle.base_url
        assert base_url is not None
        index_url = f"{base_url}/index.html"
        reader_url = f"{base_url}/reader-ux/index.html"
        authoring_url = f"{base_url}/authoring-matrix/index.html"
        index_html = _fetch_text(index_url)
        reader_html = _fetch_text(reader_url)
        authoring_html = _fetch_text(authoring_url)
        rich_css = _fetch_text(f"{base_url}/_raya/render/rich.css")
        accessibility_css = _fetch_text(
            f"{base_url}/_raya/render/accessibility/open-dyslexic.css"
        )
        accessibility_js = _fetch_text(
            f"{base_url}/_raya/render/accessibility/open-dyslexic-toggle.js"
        )
        index_skin_css = _fetch_stylesheet_containing(
            index_url,
            index_html,
            "_raya/render/skin.css",
        )
        reader_skin_css = _fetch_stylesheet_containing(
            reader_url,
            reader_html,
            "_raya/render/skin.css",
        )
    finally:
        handle.close()

    assert 'data-raya-skin="eva-unit-02"' in index_html
    assert 'data-raya-skin="practice-lab"' in reader_html
    assert 'data-raya-skin="practice-lab"' in authoring_html
    assert '[data-raya-skin="eva-unit-02"]' in index_skin_css
    assert '[data-raya-skin="eva-unit-01"]' in index_skin_css
    assert '[data-raya-skin="eva-unit-03"]' in index_skin_css
    assert '[data-raya-skin="ghost-in-the-shell"]' in index_skin_css
    assert '[data-raya-skin="practice-lab"]' in reader_skin_css
    assert '<button class="raya-font-toggle"' in index_html
    assert 'aria-pressed="false"' in index_html
    assert 'href="_raya/render/accessibility/open-dyslexic.css"' in index_html
    assert 'src="_raya/render/accessibility/open-dyslexic-toggle.js"' in index_html
    assert "@font-face" in accessibility_css
    assert "OpenDyslexic" in accessibility_css
    assert "localStorage" in accessibility_js
    assert "data-raya-open-dyslexic" in accessibility_js
    assert 'data-raya-course-map="expanded"' in index_html
    assert 'aria-expanded="true">Course map</button>' in index_html
    assert 'class="raya-learning-shell" data-raya-course-map="expanded"' in index_html
    assert 'class="raya-course-map" aria-label="Course map" data-raya-course-map="expanded"' in index_html
    assert 'class="raya-course-map-list" id="raya-course-map-list" aria-hidden="false"' in index_html
    assert 'data-raya-map-label="1 Static Path">1 Static Path</a>' in index_html
    assert 'data-raya-rail-toggle' in reader_html
    assert 'data-raya-rail-panel-state="collapsed"' in reader_html
    assert 'aria-hidden="true" inert' in reader_html
    assert "max-width: 110rem" in rich_css
    assert "grid-template-columns: minmax(4.5rem, 5.5rem) minmax(0, 1fr) minmax(14rem, 18rem)" in rich_css
    assert "@media (min-width: 901px)" in rich_css
    assert "grid-template-columns: minmax(14rem, 18rem) minmax(0, 1fr) minmax(12rem, 16rem)" in rich_css
    assert "transition: grid-template-columns 180ms ease" in rich_css
    assert ".raya-course-map-toggle:focus-visible" in rich_css
    assert ".raya-rail-toggle:focus-visible" in rich_css
    assert "outline: 3px solid var(--raya-color-accent)" in rich_css
    assert "@media (max-width: 900px)" in rich_css


def test_render_fixture_open_dyslexic_toggle_changes_computed_font(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        base_url = handle.base_url
        assert base_url is not None

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                try:
                    page.goto(f"{base_url}/index.html", wait_until="networkidle")
                    before = page.evaluate("() => getComputedStyle(document.body).fontFamily")
                    page.click(".raya-font-toggle")
                    after = page.evaluate(
                        """() => ({
                            pressed: document
                              .querySelector('.raya-font-toggle')
                              ?.getAttribute('aria-pressed'),
                            rootSetting: document.documentElement
                              .getAttribute('data-raya-open-dyslexic'),
                            bodyFont: getComputedStyle(document.body).fontFamily,
                            bodyToken: getComputedStyle(document.body)
                              .getPropertyValue('--raya-font-body')
                              .trim(),
                        })"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert "OpenDyslexic" not in before
    assert after["pressed"] == "true"
    assert after["rootSetting"] == "true"
    assert after["bodyToken"] == '"OpenDyslexic"'
    assert "OpenDyslexic" in after["bodyFont"]


def test_render_fixture_learning_shell_layout_and_accessibility(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        assert handle.base_url is not None
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                for viewport in (
                    {"width": 1280, "height": 900},
                    {"width": 960, "height": 900},
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    try:
                        page.goto(f"{handle.base_url}/reader-ux/index.html", wait_until="networkidle")
                        _assert_no_horizontal_overflow(page)
                        _assert_intersects_viewport(page, "header.raya-top-command-bar")
                        _assert_intersects_viewport(page, "article.raya-main-article")
                        if viewport["width"] > 900:
                            _assert_intersects_viewport(page, "nav.raya-course-map")
                            _assert_intersects_viewport(page, "aside.raya-learning-rail")
                        course_map = _bounding_box(page, "nav.raya-course-map")
                        article = _bounding_box(page, "article.raya-main-article")
                        learning_rail = _bounding_box(page, "aside.raya-learning-rail")
                        dom_order = page.evaluate(
                            """() => Array.from(
                                document.querySelectorAll(
                                  'nav.raya-course-map, article.raya-main-article, aside.raya-learning-rail'
                                )
                              ).map((element) => element.tagName.toLowerCase()).join('>')"""
                        )
                        assert dom_order == "nav>article>aside"
                        if viewport["width"] > 900:
                            assert course_map["x"] < article["x"] < learning_rail["x"]
                            if viewport["width"] == 960:
                                page.click(".raya-course-map-toggle")
                                _assert_no_horizontal_overflow(page)
                        else:
                            assert article["y"] < course_map["y"] < learning_rail["y"]
                            _assert_bounded_scroll_region(page, "nav.raya-course-map")
                            _assert_bounded_scroll_region(page, "aside.raya-learning-rail")
                            mobile_course_list = page.locator(
                                "#raya-course-map .raya-course-map-list"
                            ).bounding_box()
                            assert mobile_course_list is not None
                            assert mobile_course_list["width"] > 100
                            assert mobile_course_list["height"] > 40
                            mobile_course_link = page.locator("#raya-course-map a").first.bounding_box()
                            assert mobile_course_link is not None
                            assert mobile_course_link["width"] > 0
                            assert mobile_course_link["height"] > 0
                            page.click(".raya-course-map-toggle")
                            _assert_no_horizontal_overflow(page)
                            mobile_grid_columns = page.evaluate(
                                """() => getComputedStyle(
                                  document.querySelector('.raya-learning-shell')
                                ).gridTemplateColumns"""
                            )
                            assert len(mobile_grid_columns.split()) == 1
                        assert page.locator("button.raya-font-toggle").get_attribute("aria-label") == "Toggle OpenDyslexic font"
                        page.keyboard.press("Tab")
                        focused = page.evaluate("() => document.activeElement && document.activeElement.className")
                        assert "raya-skip-link" in focused or "raya-font-toggle" in focused
                        page.locator(".raya-skip-link").focus()
                        page.keyboard.press("Enter")
                        focused_id = page.evaluate("() => document.activeElement && document.activeElement.id")
                        assert focused_id == "raya-article"
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_course_map_collapses_and_expands_on_click_only(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        assert handle.base_url is not None
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 950})
                try:
                    page.goto(f"{handle.base_url}/reader-ux/index.html", wait_until="networkidle")
                    _assert_no_horizontal_overflow(page)
                    initial = page.evaluate(
                        """() => ({
                          state: document.documentElement.dataset.rayaCourseMap,
                          shellState: document.querySelector('#raya-content')?.dataset.rayaCourseMap,
                          mapState: document.querySelector('#raya-course-map')?.dataset.rayaCourseMap,
                          expanded: Array.from(document.querySelectorAll('.raya-course-map-toggle'))
                            .map((button) => button.getAttribute('aria-expanded')),
                          labels: Array.from(document.querySelectorAll('.raya-course-map-toggle'))
                            .map((button) => button.getAttribute('aria-label')),
                          texts: Array.from(document.querySelectorAll('.raya-course-map-toggle'))
                            .map((button) => button.textContent.trim()),
                          listHidden: document.querySelector('#raya-course-map-list')?.getAttribute('aria-hidden'),
                          listInert: document.querySelector('#raya-course-map-list')?.inert,
                          mapText: document.querySelector('#raya-course-map')?.innerText,
                          mapWidth: document.querySelector('#raya-course-map')?.getBoundingClientRect().width,
                          articleWidth: document.querySelector('#raya-article')?.getBoundingClientRect().width,
                          railWidth: document.querySelector('.raya-learning-rail')?.getBoundingClientRect().width,
                          linkTabIndexes: Array.from(document.querySelectorAll('#raya-course-map a'))
                            .map((link) => link.getAttribute('tabindex')),
                        })"""
                    )
                    assert initial["state"] == "expanded"
                    assert initial["shellState"] == "expanded"
                    assert initial["mapState"] == "expanded"
                    assert initial["expanded"] == ["true", "true"]
                    assert initial["labels"] == [
                        "Collapse course map",
                        "Collapse course map",
                    ]
                    assert initial["texts"] == ["Course map", "Collapse map"]
                    assert initial["listHidden"] == "false"
                    assert initial["listInert"] is False
                    assert "Toggle map" not in initial["mapText"]
                    assert "Collapse map" in initial["mapText"]
                    assert 220 <= initial["mapWidth"] <= 280
                    assert initial["articleWidth"] > 620
                    assert 240 <= initial["railWidth"] <= 320
                    assert initial["linkTabIndexes"]
                    assert set(initial["linkTabIndexes"]) == {None}

                    page.hover("#raya-course-map")
                    after_hover = page.evaluate("() => document.documentElement.dataset.rayaCourseMap")
                    assert after_hover == "expanded"

                    page.click(".raya-course-map-toggle")
                    page.wait_for_function(
                        """() => document
                          .querySelector('#raya-course-map')
                          ?.getBoundingClientRect().width < 130"""
                    )
                    collapsed = page.evaluate(
                        """() => ({
                          state: document.documentElement.dataset.rayaCourseMap,
                          shellState: document.querySelector('#raya-content')?.dataset.rayaCourseMap,
                          mapState: document.querySelector('#raya-course-map')?.dataset.rayaCourseMap,
                          expanded: Array.from(document.querySelectorAll('.raya-course-map-toggle'))
                            .map((button) => button.getAttribute('aria-expanded')),
                          labels: Array.from(document.querySelectorAll('.raya-course-map-toggle'))
                            .map((button) => button.getAttribute('aria-label')),
                          texts: Array.from(document.querySelectorAll('.raya-course-map-toggle'))
                            .map((button) => button.textContent.trim()),
                          listHidden: document.querySelector('#raya-course-map-list')?.getAttribute('aria-hidden'),
                          listInert: document.querySelector('#raya-course-map-list')?.inert,
                          mapWidth: document.querySelector('#raya-course-map')?.getBoundingClientRect().width,
                          articleWidth: document.querySelector('#raya-article')?.getBoundingClientRect().width,
                          firstLinkWidth: document.querySelector('#raya-course-map a')
                            ?.getBoundingClientRect().width,
                          buttonVisualLabel: getComputedStyle(
                            document.querySelector('#raya-course-map .raya-course-map-toggle'),
                            '::after'
                          ).content,
                          wrappedLinkTexts: Array.from(document.querySelectorAll('#raya-course-map a'))
                            .map((link) => link.innerText)
                            .filter((text) => text.includes('\\n')),
                          linkTabIndexes: Array.from(document.querySelectorAll('#raya-course-map a'))
                            .map((link) => link.getAttribute('tabindex')),
                        })"""
                    )
                    assert collapsed["state"] == "collapsed"
                    assert collapsed["shellState"] == "collapsed"
                    assert collapsed["mapState"] == "collapsed"
                    assert collapsed["expanded"] == ["false", "false"]
                    assert collapsed["labels"] == [
                        "Expand course map",
                        "Expand course map",
                    ]
                    assert collapsed["texts"] == ["Course map", "Expand map"]
                    assert collapsed["listHidden"] == "true"
                    assert collapsed["listInert"] is True
                    assert 56 <= collapsed["mapWidth"] <= 84
                    assert collapsed["articleWidth"] > 760
                    assert collapsed["texts"][1] in {"Expand map", "Map"}
                    assert collapsed["buttonVisualLabel"] == '"Map"'
                    assert collapsed["wrappedLinkTexts"] == []
                    assert collapsed["firstLinkWidth"] <= collapsed["mapWidth"]
                    assert collapsed["linkTabIndexes"]
                    assert set(collapsed["linkTabIndexes"]) == {"-1"}

                    page.click(".raya-course-map-toggle")
                    page.wait_for_function(
                        """() => document
                          .querySelector('#raya-course-map')
                          ?.getBoundingClientRect().width > 220"""
                    )
                    expanded = page.evaluate(
                        """() => ({
                          state: document.documentElement.dataset.rayaCourseMap,
                          shellState: document.querySelector('#raya-content')?.dataset.rayaCourseMap,
                          mapState: document.querySelector('#raya-course-map')?.dataset.rayaCourseMap,
                          expanded: Array.from(document.querySelectorAll('.raya-course-map-toggle'))
                            .map((button) => button.getAttribute('aria-expanded')),
                          labels: Array.from(document.querySelectorAll('.raya-course-map-toggle'))
                            .map((button) => button.getAttribute('aria-label')),
                          texts: Array.from(document.querySelectorAll('.raya-course-map-toggle'))
                            .map((button) => button.textContent.trim()),
                          listHidden: document.querySelector('#raya-course-map-list')?.getAttribute('aria-hidden'),
                          listInert: document.querySelector('#raya-course-map-list')?.inert,
                          linkTabIndexes: Array.from(document.querySelectorAll('#raya-course-map a'))
                            .map((link) => link.getAttribute('tabindex')),
                        })"""
                    )
                    assert expanded["state"] == "expanded"
                    assert expanded["shellState"] == "expanded"
                    assert expanded["mapState"] == "expanded"
                    assert expanded["expanded"] == ["true", "true"]
                    assert expanded["labels"] == [
                        "Collapse course map",
                        "Collapse course map",
                    ]
                    assert expanded["texts"] == ["Course map", "Collapse map"]
                    assert expanded["listHidden"] == "false"
                    assert expanded["listInert"] is False
                    assert set(expanded["linkTabIndexes"]) == {None}
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_learning_rail_panels_collapse_without_focus_leaks(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        assert handle.base_url is not None
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 950})
                try:
                    page.goto(f"{handle.base_url}/reader-ux/index.html", wait_until="networkidle")
                    link_panel = page.locator(".raya-page-prerequisites").first
                    collapsed = link_panel.evaluate(
                        """(panel) => {
                          const body = panel.querySelector('.raya-rail-panel-body');
                          const link = body?.querySelector('a');
                          link?.focus();
                          return {
                            state: panel.dataset.rayaRailPanelState,
                            expanded: panel.querySelector('[data-raya-rail-toggle]')
                              ?.getAttribute('aria-expanded'),
                            ariaHidden: body?.getAttribute('aria-hidden'),
                            inert: body?.inert,
                            bodyHeight: body?.getBoundingClientRect().height,
                            hasLink: !!link,
                            linkFocused: document.activeElement === link,
                          };
                        }"""
                    )
                    assert collapsed["state"] == "collapsed"
                    assert collapsed["expanded"] == "false"
                    assert collapsed["ariaHidden"] == "true"
                    assert collapsed["inert"] is True
                    assert collapsed["bodyHeight"] < 2
                    assert collapsed["hasLink"] is True
                    assert collapsed["linkFocused"] is False

                    link_panel.locator("[data-raya-rail-toggle]").click()
                    expanded = link_panel.evaluate(
                        """(panel) => {
                          const body = panel.querySelector('.raya-rail-panel-body');
                          const link = body?.querySelector('a');
                          link?.focus();
                          return {
                            state: panel.dataset.rayaRailPanelState,
                            expanded: panel.querySelector('[data-raya-rail-toggle]')
                              ?.getAttribute('aria-expanded'),
                            ariaHidden: body?.getAttribute('aria-hidden'),
                            inert: body?.inert,
                            bodyHeight: body?.getBoundingClientRect().height,
                            linkFocused: document.activeElement === link,
                          };
                        }"""
                    )
                    assert expanded["state"] == "expanded"
                    assert expanded["expanded"] == "true"
                    assert expanded["ariaHidden"] == "false"
                    assert expanded["inert"] is False
                    assert expanded["bodyHeight"] > collapsed["bodyHeight"]
                    assert expanded["linkFocused"] is True
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_course_map_works_without_storage(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        assert handle.base_url is not None
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 950})
                page.add_init_script(
                    """
                    Object.defineProperty(window, 'localStorage', {
                      configurable: true,
                      get() {
                        throw new Error('storage unavailable');
                      },
                    });
                    """
                )
                try:
                    page.goto(f"{handle.base_url}/reader-ux/index.html", wait_until="networkidle")
                    initial = page.evaluate(
                        """() => ({
                          state: document.documentElement.dataset.rayaCourseMap,
                          expanded: document.querySelector('.raya-course-map-toggle')?.getAttribute('aria-expanded'),
                          linkTabIndexes: Array.from(document.querySelectorAll('#raya-course-map a'))
                            .map((link) => link.getAttribute('tabindex')),
                        })"""
                    )
                    assert initial["state"] == "expanded"
                    assert initial["expanded"] == "true"
                    assert initial["linkTabIndexes"]
                    assert set(initial["linkTabIndexes"]) == {None}

                    page.click(".raya-course-map-toggle")
                    collapsed = page.evaluate(
                        """() => ({
                          state: document.documentElement.dataset.rayaCourseMap,
                          expanded: document.querySelector('.raya-course-map-toggle')?.getAttribute('aria-expanded'),
                          linkTabIndexes: Array.from(document.querySelectorAll('#raya-course-map a'))
                            .map((link) => link.getAttribute('tabindex')),
                        })"""
                    )
                    assert collapsed["state"] == "collapsed"
                    assert collapsed["expanded"] == "false"
                    assert set(collapsed["linkTabIndexes"]) == {"-1"}

                    page.locator("#worked-example").scroll_into_view_if_needed()
                    page.wait_for_function(
                        """() => document
                          .querySelector('.raya-page-toc a[aria-current="location"]')
                          ?.getAttribute('href') === '#worked-example'"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_course_map_ignores_saved_expanded_state_on_load(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        assert handle.base_url is not None
        shell_js = _fetch_text(f"{handle.base_url}/_raya/render/shell.js")
        assert "raya.courseMapExpanded" not in shell_js
        assert "localStorage" not in shell_js
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 950})
                page.add_init_script(
                    """
                    window.localStorage.setItem('raya.unrelatedReaderPreference', 'collapsed');
                    """
                )
                try:
                    page.goto(f"{handle.base_url}/reader-ux/index.html", wait_until="networkidle")
                    stable = page.evaluate(
                        """() => ({
                          state: document.documentElement.dataset.rayaCourseMap,
                          expanded: document.querySelector('.raya-course-map-toggle')?.getAttribute('aria-expanded'),
                          mapWidth: document.querySelector('#raya-course-map')?.getBoundingClientRect().width,
                          shellReady: document.documentElement.dataset.rayaShellReady,
                        })"""
                    )
                    assert stable["shellReady"] == "true"
                    assert stable["state"] == "expanded"
                    assert stable["expanded"] == "true"
                    assert stable["mapWidth"] > 220
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_mobile_prioritizes_article_and_tracks_active_heading(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        assert handle.base_url is not None
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 390, "height": 844})
                try:
                    page.goto(f"{handle.base_url}/reader-ux/index.html", wait_until="networkidle")
                    _assert_no_horizontal_overflow(page)
                    article = _bounding_box(page, "article.raya-main-article")
                    course_map = _bounding_box(page, "nav.raya-course-map")
                    rail = _bounding_box(page, "aside.raya-learning-rail")
                    assert article["y"] < course_map["y"] < rail["y"]
                    assert not page.locator("#raya-course-map .raya-course-map-toggle").is_visible()
                    assert page.locator(".raya-course-map-toggle").first.get_attribute("aria-expanded") == "true"
                    expanded = page.evaluate(
                        """() => ({
                          state: document.documentElement.dataset.rayaCourseMap,
                          mapTabIndex: document.querySelector('#raya-course-map')
                            ?.getAttribute('tabindex'),
                          linkTabIndexes: Array.from(document.querySelectorAll('#raya-course-map a'))
                            .map((link) => link.getAttribute('tabindex')),
                        })"""
                    )
                    assert expanded["state"] == "expanded"
                    assert expanded["mapTabIndex"] == "-1"
                    assert expanded["linkTabIndexes"]
                    assert set(expanded["linkTabIndexes"]) == {None}

                    page.click(".raya-course-map-toggle")
                    assert page.locator(".raya-course-map-toggle").first.get_attribute("aria-expanded") == "false"
                    _assert_no_horizontal_overflow(page)
                    collapsed = page.evaluate(
                        """() => ({
                          state: document.documentElement.dataset.rayaCourseMap,
                          linkTabIndexes: Array.from(document.querySelectorAll('#raya-course-map a'))
                            .map((link) => link.getAttribute('tabindex')),
                        })"""
                    )
                    assert collapsed["state"] == "collapsed"
                    assert set(collapsed["linkTabIndexes"]) == {"-1"}

                    page.locator("#worked-example").scroll_into_view_if_needed()
                    page.wait_for_function(
                        """() => document
                          .querySelector('.raya-page-toc a[aria-current="location"]')
                          ?.getAttribute('href') === '#worked-example'"""
                    )
                    active = page.evaluate(
                        """() => document.querySelector('.raya-page-toc a[aria-current="location"]')?.getAttribute('href')"""
                    )
                    assert active == "#worked-example"

                    page.evaluate(
                        """() => document
                          .getElementById('1-numeric-heading')
                          ?.scrollIntoView({ block: 'start' })"""
                    )
                    page.wait_for_function(
                        """() => document
                          .querySelector('.raya-page-toc a[aria-current="location"]')
                          ?.getAttribute('href') === '#1-numeric-heading'"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_preview_default_and_inspection_pages_have_responsive_layout_regions(
    tmp_path: Path,
) -> None:
    from raya_cli.preview import create_preview

    course = tmp_path / "reference-fixture"
    shutil.copytree(REFERENCE_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        base_url = handle.base_url
        assert base_url is not None
        root_html = _fetch_text(f"{base_url}/index.html")
        inspection_html = _fetch_text(f"{base_url}/_raya/inspect/index.html")
        css = _fetch_text(f"{base_url}/_raya/render/rich.css")
    finally:
        handle.close()

    assert '<header class="raya-top-command-bar" aria-label="Course tools">' in root_html
    assert '<a class="raya-skip-link" href="#raya-article">Skip to content</a>' in root_html
    assert '<main id="raya-content" class="raya-learning-shell" data-raya-course-map="expanded">' in root_html
    assert '<article id="raya-article" class="raya-main-article" tabindex="-1">' in root_html
    assert '<aside class="raya-learning-rail" aria-label="Learning context">' in root_html
    assert root_html.index('<nav id="raya-course-map" class="raya-course-map"') < root_html.index(
        '<article id="raya-article"'
    )
    assert root_html.index('<article id="raya-article"') < root_html.index(
        '<aside class="raya-learning-rail"'
    )
    assert "SHA-256" not in root_html
    assert "Source path" not in root_html
    assert "SHA-256" in inspection_html
    assert "Artifact path" in inspection_html
    assert '<main class="raya-inspection-main">' in inspection_html
    assert ".raya-learning-shell" in css
    assert "grid-template-columns" in css
    assert "@media (max-width: 900px)" in css
    assert "overflow-wrap: anywhere" in css


def test_examples_gallery_has_reviewable_responsive_fixture_cards() -> None:
    with _serve(EXAMPLES_GALLERY.parent) as base_url:
        gallery_html = _fetch_text(f"{base_url}/gallery/index.html")

    assert "fixture material" in gallery_html
    assert "Foundation docs and accepted OpenSpec specs remain the authority" in gallery_html
    assert '<section class="gallery-grid" aria-label="Fixture previews">' in gallery_html
    assert "../courses/minimal/artifact/site/index.html" in gallery_html
    assert "../courses/minimal/artifact/site/_raya/inspect/index.html" in gallery_html
    assert "../courses/execution-fixture/artifact/site/_raya/inspect/index.html" in gallery_html
    assert "@media (max-width: 720px)" in gallery_html
    assert "overflow-wrap: anywhere" in gallery_html


def test_rendered_surfaces_have_no_obvious_layout_overlap_at_viewports(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "reference-fixture"
    shutil.copytree(REFERENCE_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        base_url = handle.base_url
        assert base_url is not None

        with _serve(EXAMPLES_GALLERY.parent) as examples_url:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    executable_path=str(browser_executable),
                    headless=True,
                    args=["--no-sandbox"],
                )
                try:
                    for viewport in ({"width": 1280, "height": 900}, {"width": 390, "height": 844}):
                        page = browser.new_page(viewport=viewport)
                        try:
                            page.goto(f"{base_url}/index.html", wait_until="networkidle")
                            _assert_no_horizontal_overflow(page)
                            _assert_no_overlap(
                                page,
                                "article.raya-main-article",
                                "aside.raya-learning-rail",
                            )

                            page.goto(
                                f"{base_url}/_raya/inspect/index.html",
                                wait_until="networkidle",
                            )
                            _assert_no_horizontal_overflow(page)
                            assert page.locator("main.raya-inspection-main").bounding_box()

                            page.goto(
                                f"{examples_url}/gallery/index.html",
                                wait_until="networkidle",
                            )
                            _assert_no_horizontal_overflow(page)
                            _assert_gallery_cards_do_not_overlap(page)
                        finally:
                            page.close()
                finally:
                    browser.close()
    finally:
        handle.close()


def test_render_fixture_math_renders_in_browser_without_external_requests(
    tmp_path: Path,
) -> None:
    _run_render_fixture_math_check(tmp_path)


def test_render_fixture_numbered_objects_are_static_and_local(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    external_requests: list[str] = []
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        base_url = handle.base_url
        assert base_url is not None

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.on(
                    "request",
                    lambda request: record_external_request(
                        request.url,
                        base_url,
                        external_requests,
                    ),
                )
                try:
                    page.goto(
                        f"{base_url}/numbered-objects/index.html",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(page)
                    _assert_visible_mathjax_output(page, minimum=3)
                    probe = page.evaluate(
                        """() => {
                            const objectNodes = Array.from(
                              document.querySelectorAll('.raya-numbered-object')
                            );
                            const refNodes = Array.from(
                              document.querySelectorAll('a[href*="raya-object-"]')
                            );
                            return {
                              ids: objectNodes.map((node) => node.dataset.objectId),
                              text: document.body.innerText,
                              classes: objectNodes.map((node) => node.className),
                              refs: refNodes.map((node) => ({
                                text: node.innerText,
                                href: node.getAttribute('href'),
                              })),
                              mathJaxScripts: Array.from(document.scripts)
                                .map((script) => script.src || script.textContent || '')
                                .filter((value) => value.includes('MathJax')),
                              visibleRawTex: document.body.innerText.includes('\\\\begin{bmatrix}'),
                              mathjaxContainers: document.querySelectorAll('mjx-container').length,
                              proofCount: document.querySelectorAll('.raya-proof').length,
                              proofHeading: document.querySelector('.raya-proof-heading')?.textContent || '',
                              proofHasMath: Boolean(document.querySelector('.raya-proof mjx-container')),
                              proofIds: Array.from(document.querySelectorAll('.raya-proof[id]'))
                                .map((node) => node.id),
                            };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert set(probe["ids"]) >= {
        "main-theorem",
        "vector-corollary",
        "basis-definition",
        "matrix-equation",
        "fixture-figure",
        "fixture-table",
        "practice-problem",
        "homework-one",
    }
    assert set(probe["ids"]) >= {
        "main-theorem",
        "vector-corollary",
        "basis-definition",
        "matrix-equation",
        "fixture-figure",
        "fixture-table",
        "practice-problem",
        "homework-one",
        "activity-one",
        "assignment-one",
    }
    assert "Theorem 3.1" in probe["text"]
    assert "Activity 3.1" in probe["text"]
    assert "Activity 3.2" in probe["text"]
    assert "Activity 3.3" in probe["text"]
    assert any(
        ref["href"] == "index.html#raya-object-main-theorem" for ref in probe["refs"]
    )
    assert any(
        ref["href"] == "index.html#raya-object-assignment-one"
        and ref["text"] == "Activity 3.3"
        for ref in probe["refs"]
    )
    assert "Proof of Activity 3.3" in probe["text"]
    assert any("raya-numbered-object--scannable" in value for value in probe["classes"])
    assert any("raya-numbered-object--caption" in value for value in probe["classes"])
    assert any("raya-numbered-object--equation" in value for value in probe["classes"])
    assert probe["mathJaxScripts"] == []
    assert probe["visibleRawTex"] is False
    assert probe["mathjaxContainers"] >= 3
    assert probe["proofCount"] >= 2
    assert "Proof of Theorem 3.1" in probe["proofHeading"]
    assert probe["proofHasMath"]
    assert "raya-proof-proof-main" in probe["proofIds"]
    assert external_requests == []


def test_render_fixture_reader_ux_page_uses_scannable_static_numbering(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    external_requests: list[str] = []
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        base_url = handle.base_url
        assert base_url is not None

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.on(
                    "request",
                    lambda request: record_external_request(
                        request.url,
                        base_url,
                        external_requests,
                    ),
                )
                try:
                    page.goto(f"{base_url}/reader-ux/", wait_until="networkidle")
                    _assert_no_horizontal_overflow(page)
                    _assert_visible_mathjax_output(page, minimum=6)
                    probe = page.evaluate(
                        """() => {
                            const bodyText = document.body.innerText;
                            const objectNodes = Array.from(
                              document.querySelectorAll('.raya-numbered-object')
                            );
                            return {
                              ids: objectNodes.map((node) => node.dataset.objectId),
                              text: bodyText,
                              classes: objectNodes.map((node) => node.className),
                              hasBadge: Boolean(document.querySelector('.raya-numbered-object-badge')),
                              hasCaptionStyle: Boolean(document.querySelector('.raya-numbered-object--caption')),
                              hasEquation: Boolean(document.querySelector('.raya-numbered-object--equation')),
                              mathJaxScripts: Array.from(document.scripts)
                                .map((script) => script.src || script.textContent || '')
                                .filter((value) => value.includes('MathJax')),
                              visibleRawTex: bodyText.includes('\\\\begin{bmatrix}')
                                || bodyText.includes('\\\\orthproj')
                                || bodyText.includes('$$'),
                              mathjaxContainers: document.querySelectorAll('mjx-container').length,
                              proofTexts: Array.from(document.querySelectorAll('.raya-proof'))
                                .map((node) => node.innerText),
                              staticEnvironmentCount: document.querySelectorAll('.raya-static-environment').length,
                              staticEnvironmentTexts: Array.from(document.querySelectorAll('.raya-static-environment'))
                                .map((node) => node.innerText),
                              staticEnvironmentIds: Array.from(document.querySelectorAll('.raya-static-environment[id]'))
                                .map((node) => node.id),
                            };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert set(probe["ids"]) >= {
        "orthogonal-definition",
        "orthogonal-proposition",
        "orthogonal-remark",
        "orthogonal-example",
        "orthogonal-equation",
        "orthogonal-figure",
        "orthogonal-table",
        "orthogonal-problem",
        "orthogonal-activity",
    }
    for expected_text in (
        "Reader UX Fixture",
        "Remark 4.4",
        "Example 4.1",
        "Problem 4.1",
        "Activity 4.1",
        "Proof of Proposition 4.2",
        "Solution sketch of Activity 4.1",
        "reader-facing fixture material",
    ):
        assert expected_text in probe["text"]
    assert any("raya-numbered-object--scannable" in value for value in probe["classes"])
    assert any("raya-numbered-object--caption" in value for value in probe["classes"])
    assert any("raya-numbered-object--equation" in value for value in probe["classes"])
    assert probe["hasBadge"] is True
    assert probe["hasCaptionStyle"] is True
    assert probe["hasEquation"] is True
    assert probe["mathJaxScripts"] == []
    assert probe["visibleRawTex"] is False
    assert probe["mathjaxContainers"] >= 6
    assert any("Proof of Proposition 4.2" in text for text in probe["proofTexts"])
    assert any("Solution sketch of Activity 4.1" in text for text in probe["proofTexts"])
    assert probe["staticEnvironmentCount"] >= 4
    assert "raya-static-environment-hint-orthogonal-activity" in probe[
        "staticEnvironmentIds"
    ]
    assert "raya-static-environment-solution-orthogonal-activity" in probe[
        "staticEnvironmentIds"
    ]
    assert "raya-static-environment-answer-orthogonal-activity" in probe[
        "staticEnvironmentIds"
    ]
    static_environment_text = " ".join(probe["staticEnvironmentTexts"])
    assert "Hint for Activity 4.1" in static_environment_text
    assert "Solution of Activity 4.1" in static_environment_text
    assert "Answer to Activity 4.1" in static_environment_text
    assert (
        "Scaling the direction vector changes the projection coefficient"
        in static_environment_text
    )
    assert "before expanding the matrix product." in static_environment_text
    assert (
        "The residual vector is orthogonal to the direction vector."
        in static_environment_text
    )
    assert external_requests == []


def test_render_debug_cleanup_removes_stale_fallback_numbered_object_screenshots(
    tmp_path: Path,
) -> None:
    debug_dir = tmp_path / "renderer-debug"
    debug_dir.mkdir()
    stale_fallback = debug_dir / "desktop-3_numbered_objects.png"
    stale_current = debug_dir / "desktop-numbered-objects.png"
    unrelated = debug_dir / "keep.txt"
    stale_fallback.write_bytes(b"stale fallback")
    stale_current.write_bytes(b"stale current")
    unrelated.write_text("keep\n", encoding="utf-8")
    report = ValidationReport(context="preview")

    assert _reset_render_debug_dir(debug_dir, report)

    assert not stale_fallback.exists()
    assert not stale_current.exists()
    assert unrelated.exists()


def _run_render_fixture_math_check(tmp_path: Path) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()
    debug_dir_value = os.environ.get("RAYA_RENDER_DEBUG_DIR")
    debug_dir = Path(debug_dir_value) if debug_dir_value else None

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    external_requests: list[str] = []
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        base_url = handle.base_url
        assert base_url is not None

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                for viewport in RENDER_DEBUG_VIEWPORTS:
                    page = browser.new_page(viewport=viewport)
                    page.on(
                        "request",
                        lambda request: record_external_request(
                            request.url,
                            base_url,
                            external_requests,
                        ),
                    )
                    try:
                        page.goto(f"{base_url}/index.html", wait_until="networkidle")
                        _assert_no_horizontal_overflow(page)
                        _assert_visible_mathjax_output(page, minimum=6)
                        visible_text = page.locator("body").inner_text()
                        assert raw_tex_markers_from_text(visible_text) == []

                        page.goto(
                            f"{base_url}/static-path/index.html",
                            wait_until="networkidle",
                        )
                        _assert_no_horizontal_overflow(page)
                        _assert_visible_mathjax_output(page, minimum=2)

                        page.goto(
                            f"{base_url}/math-authoring/index.html",
                            wait_until="networkidle",
                        )
                        _assert_no_horizontal_overflow(page)
                        _assert_visible_mathjax_output(page, minimum=7)
                        math_authoring_text = page.locator("body").inner_text()
                        assert raw_tex_markers_from_text(math_authoring_text) == []
                        assert (
                            "Numbered objects and references are current renderer behavior"
                            in math_authoring_text
                        )
                        assert "@id shorthand references" in math_authoring_text
                        assert "raya:ref/id" in math_authoring_text
                    finally:
                        page.close()
            finally:
                browser.close()
        if debug_dir is not None:
            debug_report = capture_render_debug(
                base_url=base_url,
                site_dir=course / "artifact" / "site",
                output_dir=debug_dir,
            )
            assert debug_report.ok, [
                diagnostic.format() for diagnostic in debug_report.diagnostics
            ]
    finally:
        handle.close()

    assert external_requests == []


def test_render_fixture_debug_artifacts_are_written_when_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    debug_dir = tmp_path / "renderer-debug"
    monkeypatch.setenv("RAYA_RENDER_DEBUG_DIR", str(debug_dir))

    _run_render_fixture_math_check(tmp_path)

    expected_primary_screenshots = {
        f"{viewport_name(viewport)}-{page_name}.png"
        for viewport in RENDER_DEBUG_VIEWPORTS
        for page_name in RENDER_DEBUG_PAGE_NAMES
    }
    expected_shell_screenshots = {
        f"desktop-{state}-{page_name}.png"
        for state in ("collapsed", "expanded")
        for page_name in RENDER_DEBUG_PAGE_NAMES
    }
    expected_screenshots = expected_primary_screenshots | expected_shell_screenshots
    actual_screenshots = {path.name for path in debug_dir.glob("*.png")}
    assert actual_screenshots == expected_screenshots
    for name in expected_screenshots:
        assert (debug_dir / name).stat().st_size > 0

    summary_path = debug_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert len(summary["captures"]) == len(expected_primary_screenshots)
    captured_names = {
        Path(capture["screenshot"]).name for capture in summary["captures"]
    }
    assert captured_names == expected_primary_screenshots
    captured_shell_names = {
        Path(path).name
        for capture in summary["captures"]
        for key, path in capture.get("screenshots", {}).items()
        if key in {"desktop-collapsed", "desktop-expanded"}
    }
    assert captured_shell_names == expected_shell_screenshots
    assert all(capture["raw_tex_visible"] is False for capture in summary["captures"])
    assert all(capture["raw_tex_markers"] == [] for capture in summary["captures"])
    assert all(
        capture["horizontal_overflow"] <= 1 for capture in summary["captures"]
    )
    assert all(capture["external_requests"] == [] for capture in summary["captures"])


def test_render_fixture_debug_summary_is_reset_between_runs(
    tmp_path: Path,
) -> None:
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    debug_dir = tmp_path / "renderer-debug"
    debug_dir.mkdir()
    (debug_dir / "summary.json").write_text(
        json.dumps({"captures": [{"page": "stale"}]}) + "\n",
        encoding="utf-8",
    )

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        assert handle.base_url is not None
        result = capture_render_debug(
            base_url=handle.base_url,
            site_dir=course / "artifact" / "site",
            output_dir=debug_dir,
        )
    finally:
        handle.close()

    assert result.ok, [diagnostic.format() for diagnostic in result.diagnostics]
    summary = json.loads((debug_dir / "summary.json").read_text(encoding="utf-8"))
    assert len(summary["captures"]) == len(RENDER_DEBUG_VIEWPORTS) * len(
        RENDER_DEBUG_PAGE_NAMES
    )
    assert all(capture["page"] != "stale" for capture in summary["captures"])


def test_capture_render_debug_writes_screenshots_and_summary(tmp_path: Path) -> None:
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    debug_dir = tmp_path / "renderer-debug"

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        assert handle.base_url is not None
        result = capture_render_debug(
            base_url=handle.base_url,
            site_dir=course / "artifact" / "site",
            output_dir=debug_dir,
        )
    finally:
        handle.close()

    assert result.ok, [diagnostic.format() for diagnostic in result.diagnostics]
    expected_screenshots = {
        "desktop-index.png",
        "mobile-index.png",
        "desktop-static-path.png",
        "mobile-static-path.png",
        "desktop-math-authoring.png",
        "mobile-math-authoring.png",
        "desktop-numbered-objects.png",
        "mobile-numbered-objects.png",
        "desktop-reader-ux.png",
        "mobile-reader-ux.png",
        "desktop-collapsed-index.png",
        "desktop-expanded-index.png",
        "desktop-collapsed-static-path.png",
        "desktop-expanded-static-path.png",
        "desktop-collapsed-math-authoring.png",
        "desktop-expanded-math-authoring.png",
        "desktop-collapsed-numbered-objects.png",
        "desktop-expanded-numbered-objects.png",
        "desktop-collapsed-reader-ux.png",
        "desktop-expanded-reader-ux.png",
    }
    expected_primary_screenshots = {
        name
        for name in expected_screenshots
        if not name.startswith(("desktop-collapsed-", "desktop-expanded-"))
    }
    expected_shell_screenshots = expected_screenshots - expected_primary_screenshots
    assert {path.name for path in debug_dir.glob("*.png")} == expected_screenshots
    assert all((debug_dir / name).stat().st_size > 0 for name in expected_screenshots)

    summary = json.loads((debug_dir / "summary.json").read_text(encoding="utf-8"))
    assert len(summary["captures"]) == len(expected_primary_screenshots)
    assert {
        Path(capture["screenshot"]).name for capture in summary["captures"]
    } == expected_primary_screenshots
    assert {
        Path(path).name
        for capture in summary["captures"]
        for key, path in capture.get("screenshots", {}).items()
        if key in {"desktop-collapsed", "desktop-expanded"}
    } == expected_shell_screenshots
    assert all(capture["raw_tex_visible"] is False for capture in summary["captures"])
    assert all(capture["raw_tex_markers"] == [] for capture in summary["captures"])
    assert all(capture["external_requests"] == [] for capture in summary["captures"])
    assert all(capture["horizontal_overflow"] <= 1 for capture in summary["captures"])
    numbered_capture = next(
        capture
        for capture in summary["captures"]
        if capture["page"] == "numbered-objects"
        and capture["viewport"]["name"] == "desktop"
    )
    evidence = numbered_capture["numbered_content"]
    assert {item["id"] for item in evidence["objects"]} >= {
        "main-theorem",
        "assignment-one",
    }
    assert {item["target_text"] for item in evidence["proofs"]} >= {
        "Theorem 3.1",
        "Activity 3.3",
    }
    assert any(
        ref["text"] == "Activity 3.3"
        and ref["href"].endswith("#raya-object-assignment-one")
        for ref in evidence["references"]
    )
    reader_capture = next(
        capture
        for capture in summary["captures"]
        if capture["page"] == "reader-ux"
        and capture["viewport"]["name"] == "desktop"
    )
    reader_evidence = reader_capture["numbered_content"]
    assert {item["id"] for item in reader_evidence["objects"]} >= {
        "orthogonal-remark",
        "orthogonal-activity",
    }
    assert {item["target_text"] for item in reader_evidence["proofs"]} >= {
        "Proposition 4.2",
        "Activity 4.1",
    }
    static_environments = reader_capture["staticEnvironments"]
    assert {item["id"] for item in static_environments} >= {
        "raya-static-environment-hint-orthogonal-activity",
        "raya-static-environment-solution-orthogonal-activity",
        "raya-static-environment-answer-orthogonal-activity",
    }
    mobile_reader_capture = next(
        capture
        for capture in summary["captures"]
        if capture["page"] == "reader-ux"
        and capture["viewport"]["name"] == "mobile"
    )
    mobile_static_environments = mobile_reader_capture["staticEnvironments"]
    assert {item["id"] for item in mobile_static_environments} >= {
        "raya-static-environment-hint-orthogonal-activity",
        "raya-static-environment-solution-orthogonal-activity",
        "raya-static-environment-answer-orthogonal-activity",
    }

    report_json = json.loads((debug_dir / "report.json").read_text(encoding="utf-8"))
    report_html = (debug_dir / "index.html").read_text(encoding="utf-8")

    assert report_json["ok"] is True
    assert report_json["summary_path"].endswith("summary.json")
    assert report_json["html_report_path"].endswith("index.html")
    assert {check["id"] for check in report_json["checks"]} >= {
        "capture:index:desktop",
        "capture:index:mobile",
        "capture:static-path:desktop",
        "capture:static-path:mobile",
        "capture:math-authoring:desktop",
        "capture:math-authoring:mobile",
        "capture:numbered-objects:desktop",
        "capture:numbered-objects:mobile",
        "capture:reader-ux:desktop",
        "capture:reader-ux:mobile",
        "numbered-content:reader-ux:desktop",
        "numbered-content:reader-ux:mobile",
        "static-environment:reader-ux:desktop:hint",
        "static-environment:reader-ux:desktop:solution",
        "static-environment:reader-ux:desktop:answer",
        "static-environment:reader-ux:mobile:hint",
        "static-environment:reader-ux:mobile:solution",
        "static-environment:reader-ux:mobile:answer",
    }
    assert report_json["diagnostics"] == []
    assert "Render Debug Inspection Report" in report_html
    assert 'href="desktop-index.png"' in report_html
    assert 'href="mobile-static-path.png"' in report_html
    assert 'href="desktop-reader-ux.png"' in report_html


def test_capture_render_debug_fails_on_visible_raw_tex(tmp_path: Path) -> None:
    site = tmp_path / "site"
    site.mkdir()
    (site / "index.html").write_text(
        "<!doctype html><html><body><main>$x^2$ and \\badMacro{y}</main></body></html>",
        encoding="utf-8",
    )
    debug_dir = tmp_path / "renderer-debug"

    with _serve(site) as base_url:
        result = capture_render_debug(
            base_url=base_url,
            site_dir=site,
            output_dir=debug_dir,
        )

    assert not result.ok
    assert any(
        "Renderer debug found visible raw TeX" in diagnostic.message
        for diagnostic in result.diagnostics
    )
    summary = json.loads((debug_dir / "summary.json").read_text(encoding="utf-8"))
    markers = {
        marker
        for capture in summary["captures"]
        for marker in capture["raw_tex_markers"]
    }
    assert "$x^2$" in markers
    assert "\\badMacro" in markers


def test_capture_render_debug_reports_invalid_browser_executable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    site = tmp_path / "site"
    site.mkdir()
    (site / "index.html").write_text(
        "<!doctype html><html><body><main>No math here.</main></body></html>",
        encoding="utf-8",
    )
    fake_browser = tmp_path / "not-browser"
    fake_browser.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_browser.chmod(0o755)
    monkeypatch.setenv("RAYA_TEST_BROWSER", str(fake_browser))

    with _serve(site) as base_url:
        result = capture_render_debug(
            base_url=base_url,
            site_dir=site,
            output_dir=tmp_path / "renderer-debug",
        )

    assert not result.ok
    assert any(
        "Could not launch Chromium-compatible browser" in diagnostic.message
        for diagnostic in result.diagnostics
    )


@contextlib.contextmanager
def _serve(directory: Path):
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


def _fetch_text(url: str) -> str:
    with urlopen(url, timeout=10) as response:
        return response.read().decode("utf-8")


def _fetch_bytes(url: str) -> bytes:
    with urlopen(url, timeout=10) as response:
        return response.read()


def _fetch_stylesheet_containing(page_url: str, html: str, href_part: str) -> str:
    stylesheet_urls = [
        urljoin(page_url, href)
        for href in _stylesheet_hrefs(html)
        if href_part in href
    ]
    assert stylesheet_urls, html
    return _fetch_text(stylesheet_urls[0])


def _stylesheet_hrefs(html: str) -> list[str]:
    parser = _StylesheetParser()
    parser.feed(html)
    parser.close()
    return parser.hrefs


class _StylesheetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag.lower() != "link":
            return
        attributes = {name.lower(): value or "" for name, value in attrs}
        rel_values = {
            value.lower()
            for value in attributes.get("rel", "").split()
        }
        href = attributes.get("href", "")
        if "stylesheet" in rel_values and href:
            self.hrefs.append(href)


def _local_math_font_names_from_css(css: str) -> list[str]:
    names: set[str] = set()
    for match in re.finditer(r"url\(([^)]*)\)", css):
        raw_url = match.group(1).strip().strip("\"'")
        assert not raw_url.startswith(("http://", "https://", "//", "/"))
        path = raw_url.split("?", 1)[0].split("#", 1)[0]
        if path.startswith("./"):
            path = path[2:]
        if path.startswith("fonts/") and path.endswith(".woff2"):
            name = path.removeprefix("fonts/")
            assert "/" not in name
            names.add(name)
    return sorted(names)


def _browser_executable() -> Path:
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


def _assert_no_horizontal_overflow(page) -> None:
    overflow = page.evaluate(
        "() => Math.ceil(document.documentElement.scrollWidth - window.innerWidth)"
    )
    assert overflow <= 1


def _assert_intersects_viewport(page, selector: str) -> None:
    box = _bounding_box(page, selector)
    viewport = page.evaluate(
        "() => ({ width: window.innerWidth, height: window.innerHeight })"
    )
    assert box["x"] + box["width"] > 0, f"{selector} is left of the viewport: {box}"
    assert box["x"] < viewport["width"], f"{selector} is right of the viewport: {box}"
    assert box["y"] + box["height"] > 0, f"{selector} is above the viewport: {box}"
    assert box["y"] < viewport["height"], f"{selector} is below the viewport: {box}"


def _assert_bounded_scroll_region(page, selector: str) -> None:
    region = page.evaluate(
        """(selector) => {
            const element = document.querySelector(selector);
            if (!element) return null;
            const style = getComputedStyle(element);
            return {
              clientHeight: element.clientHeight,
              scrollHeight: element.scrollHeight,
              overflowY: style.overflowY,
            };
        }""",
        selector,
    )
    assert region is not None, f"{selector} did not render"
    assert region["clientHeight"] > 0, f"{selector} has no usable height: {region}"
    if region["scrollHeight"] > region["clientHeight"]:
        assert region["overflowY"] in {"auto", "scroll"}, (
            f"{selector} clips scrollable content without scroll overflow: {region}"
        )


def _bounding_box(page, selector: str) -> dict[str, float]:
    box = page.locator(selector).bounding_box()
    assert box is not None, f"{selector} did not render"
    return box


def _assert_no_overlap(page, first_selector: str, second_selector: str) -> None:
    first = _bounding_box(page, first_selector)
    second = _bounding_box(page, second_selector)
    assert not _boxes_overlap(first, second)


def _assert_gallery_cards_do_not_overlap(page) -> None:
    cards = page.locator(".gallery-card")
    boxes = [cards.nth(index).bounding_box() for index in range(cards.count())]
    visible_boxes = [box for box in boxes if box is not None]
    assert len(visible_boxes) >= 6
    for index, first in enumerate(visible_boxes):
        for second in visible_boxes[index + 1 :]:
            assert not _boxes_overlap(first, second)


def _assert_visible_mathjax_output(page, *, minimum: int) -> None:
    containers = page.locator("mjx-container")
    assert containers.count() >= minimum
    first_box = containers.first.bounding_box()
    assert first_box is not None
    assert first_box["width"] > 0
    assert first_box["height"] > 0


def _boxes_overlap(first: dict[str, float], second: dict[str, float]) -> bool:
    return not (
        first["x"] + first["width"] <= second["x"]
        or second["x"] + second["width"] <= first["x"]
        or first["y"] + first["height"] <= second["y"]
        or second["y"] + second["height"] <= first["y"]
    )
