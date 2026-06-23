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
MINIMAL = ROOT / "examples" / "courses" / "minimal"
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


def test_render_fixture_section_landing_cards_are_static_navigation(
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
                for viewport in ({"width": 1280, "height": 900}, {"width": 390, "height": 844}):
                    page = browser.new_page(viewport=viewport)
                    requested_urls: list[str] = []
                    page.on("request", lambda request: requested_urls.append(request.url))
                    try:
                        page.goto(f"{base_url}/index.html", wait_until="networkidle")
                        requested_urls.clear()
                        _assert_no_horizontal_overflow(page)
                        cards = page.locator(".raya-section-card")
                        assert cards.count() >= 5
                        first_link = page.locator(".raya-section-card-link").first
                        assert first_link.is_visible()
                        assert first_link.locator(".raya-section-card-title").inner_text().strip()
                        assert first_link.locator(".raya-section-card-summary").inner_text().strip()
                        box = first_link.bounding_box()
                        assert box is not None
                        assert box["width"] >= 180 or viewport["width"] < 500
                        href = first_link.evaluate("node => node.href")
                        with page.expect_navigation():
                            first_link.click()
                        assert page.url == href
                        assert requested_urls
                        assert all(url.startswith(f"{base_url}/") for url in requested_urls)
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_preview_serves_local_visual_graph_surface(tmp_path: Path) -> None:
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
        graph_html = _fetch_text(f"{base_url}/_raya/graph/index.html")
        graph_js = _fetch_text(f"{base_url}/_raya/render/graph.js")

        assert 'data-raya-surface="graph"' in graph_html
        assert "raya-graph-data" in graph_html
        assert "https://" not in graph_html
        assert "http://" not in graph_html
        assert "cytoscape" not in graph_html.lower()
        assert "window.location.href" in graph_js

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                for viewport in ({"width": 1280, "height": 900}, {"width": 390, "height": 844}):
                    page = browser.new_page(viewport=viewport)
                    requested_urls: list[str] = []
                    page.on("request", lambda request: requested_urls.append(request.url))
                    try:
                        page.goto(f"{base_url}/_raya/graph/index.html", wait_until="networkidle")
                        requested_urls.clear()
                        _assert_no_horizontal_overflow(page)
                        assert page.locator(".raya-discovery-command-bar").is_visible()
                        if viewport["width"] < 520:
                            discovery_box = page.locator(
                                ".raya-discovery-command-bar"
                            ).bounding_box()
                            assert discovery_box is not None
                            assert discovery_box["height"] <= 150
                        assert page.locator(".raya-command-search").evaluate(
                            "node => node.href"
                        ).endswith("/_raya/search/index.html")
                        assert page.locator(".raya-command-size").is_visible()
                        assert page.locator(".raya-command-font").is_visible()
                        assert page.locator(".raya-graph-legend").is_visible()
                        assert page.locator("[data-raya-graph-legend='node']").is_visible()
                        assert page.locator("[data-raya-graph-legend='match']").is_visible()
                        assert page.locator("[data-raya-graph-legend='selected']").is_visible()
                        assert page.locator("[data-raya-graph-help]").is_visible()
                        assert page.locator("[data-raya-graph-help]").get_attribute("open") is None
                        page.locator("[data-raya-graph-help] summary").click()
                        assert "Search" in page.locator("[data-raya-graph-help]").inner_text()
                        assert page.locator("#raya-graph-canvas .raya-graph-node").count() > 0
                        before = page.locator(
                            "#raya-graph-list [data-raya-graph-node]:visible"
                        ).count()
                        page.fill("#graph-search", "matrix")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#graph-status')
                              ?.textContent
                              ?.includes('visible node')"""
                        )
                        after = page.locator(
                            "#raya-graph-list [data-raya-graph-node]:visible"
                        ).count()
                        assert after < before
                        assert "matrix" in page.locator("#raya-graph-list").inner_text().lower()
                        page.fill("#graph-search", "matrx")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#graph-status')
                              ?.textContent
                              ?.includes('visible node')"""
                        )
                        assert "matrix" in page.locator("#raya-graph-list").inner_text().lower()
                        page.locator(
                            '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
                        ).hover()
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-hover-status]')
                              ?.textContent
                              ?.includes('Inspecting Authoring Matrix Fixture')"""
                        )
                        assert page.locator(
                            '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"] g'
                        ).evaluate("node => node.classList.contains('is-inspected')")
                        for node_id in (
                            "render-root",
                            "math-authoring",
                            "numbered-objects",
                            "reader-ux",
                        ):
                            assert page.locator(
                                f'#raya-graph-canvas [data-raya-graph-node="{node_id}"] g'
                            ).evaluate(
                                "node => node.classList.contains('is-inspected-neighbor')"
                            )
                        page.locator(
                            '#raya-graph-list [data-raya-graph-node="authoring-matrix"] a'
                        ).focus()
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-hover-status]')
                              ?.textContent
                              ?.includes('Inspecting Authoring Matrix Fixture')"""
                        )
                        page.locator(
                            '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
                        ).focus()
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-hover-status]')
                              ?.textContent
                              ?.includes('Inspecting Authoring Matrix Fixture')"""
                        )
                        assert requested_urls == []
                        graph_node = page.locator(
                            "#raya-graph-canvas [data-raya-graph-node]"
                        ).first
                        graph_node.hover()
                        assert page.locator("[data-raya-graph-detail-empty]").is_visible()
                        assert page.locator("[data-raya-graph-detail-panel]").is_hidden()
                        graph_node.click()
                        page.wait_for_selector("[data-raya-graph-detail-panel]:not([hidden])")
                        assert page.locator("[data-raya-graph-detail-title]").inner_text().strip()
                        assert page.locator("[data-raya-graph-detail-link]").get_attribute("href")
                        assert page.locator("[data-raya-graph-detail-empty]").is_hidden()
                        outgoing_or_incoming = (
                            page.locator("[data-raya-graph-detail-outgoing] li").count()
                            + page.locator("[data-raya-graph-detail-incoming] li").count()
                        )
                        assert outgoing_or_incoming >= 1
                        page.fill("#graph-search", "zz-no-result")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#graph-status')
                              ?.textContent
                              ?.startsWith('0 visible node')"""
                        )
                        assert page.locator("[data-raya-graph-detail-empty]").is_visible()
                        assert page.locator("[data-raya-graph-detail-panel]").is_hidden()
                        page.fill("#graph-search", "matrx")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#graph-status')
                              ?.textContent
                              ?.includes('visible node')"""
                        )
                        page.locator("#raya-graph-canvas [data-raya-graph-node]").first.click()
                        page.wait_for_selector("[data-raya-graph-detail-panel]:not([hidden])")
                        before_height = page.locator("#raya-graph-canvas").bounding_box()["height"]
                        page.click("#graph-expand")
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-expanded"
                            )
                            == "true"
                        )
                        after_height = page.locator("#raya-graph-canvas").bounding_box()["height"]
                        assert after_height >= before_height
                        page.click("[data-raya-graph-detail-clear]")
                        assert page.locator("[data-raya-graph-detail-empty]").is_visible()
                        page.select_option("#graph-layout", "radial")
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-layout"
                            )
                            == "radial"
                        )
                        page.select_option("#graph-layout", "list")
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-layout"
                            )
                            == "list"
                        )
                        assert page.locator("#raya-graph-canvas").is_hidden()
                        page.click("#graph-reset")
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-layout"
                            )
                            == "map"
                        )
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-expanded"
                            )
                            == "false"
                        )
                        assert page.locator("[data-raya-graph-detail-empty]").is_visible()
                        assert requested_urls == []
                        first_list_link = page.locator(
                            "#raya-graph-list [data-raya-graph-node]:visible a"
                        ).first
                        list_href = first_list_link.evaluate("node => node.href")
                        with page.expect_navigation():
                            first_list_link.click()
                        assert page.url == list_href
                        page.goto(f"{base_url}/_raya/graph/index.html", wait_until="networkidle")
                        page.locator("#raya-graph-canvas .raya-graph-node-hit").first.click()
                        page.wait_for_selector("[data-raya-graph-detail-panel]:not([hidden])")
                        detail_href = page.locator(
                            "[data-raya-graph-detail-link]"
                        ).evaluate("node => node.href")
                        with page.expect_navigation():
                            page.click("[data-raya-graph-detail-link]")
                        assert page.url == detail_href
                        page.goto(f"{base_url}/_raya/graph/index.html", wait_until="networkidle")
                        graph_href = page.locator(
                            "#raya-graph-canvas [data-raya-graph-node]"
                        ).first.evaluate(
                            "node => new URL(node.getAttribute('href'), document.baseURI).href"
                        )
                        with page.expect_navigation():
                            page.locator(
                                "#raya-graph-canvas .raya-graph-node-hit"
                            ).first.dblclick()
                        assert page.url == graph_href
                        page.goto(
                            f"{base_url}/_raya/graph/index.html?page=authoring-matrix",
                            wait_until="networkidle",
                        )
                        requested_urls.clear()
                        page.wait_for_selector("[data-raya-graph-detail-panel]:not([hidden])")
                        assert "Authoring Matrix Fixture" in page.locator(
                            "[data-raya-graph-detail-title]"
                        ).inner_text()
                        assert (
                            "Neighborhood: 4 outgoing link(s), 2 incoming link(s), "
                            "4 connected page(s)."
                        ) in page.locator(
                            "[data-raya-graph-detail-neighborhood]"
                        ).inner_text()
                        assert page.locator(
                            '#raya-graph-list [data-raya-graph-node="authoring-matrix"]'
                        ).evaluate("node => node.classList.contains('is-active')")
                        assert not page.locator(
                            '#raya-graph-list [data-raya-graph-node="authoring-matrix"]'
                        ).evaluate("node => node.classList.contains('is-neighbor')")
                        assert not page.locator(
                            '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"] g'
                        ).evaluate("node => node.classList.contains('is-neighbor')")
                        for node_id in (
                            "render-root",
                            "math-authoring",
                            "numbered-objects",
                            "reader-ux",
                        ):
                            assert page.locator(
                                f'#raya-graph-list [data-raya-graph-node="{node_id}"]'
                            ).evaluate("node => node.classList.contains('is-neighbor')")
                            assert page.locator(
                                f'#raya-graph-canvas [data-raya-graph-node="{node_id}"] g'
                            ).evaluate("node => node.classList.contains('is-neighbor')")
                        assert requested_urls == []
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_preview_serves_local_course_search_surface(tmp_path: Path) -> None:
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
        search_html = _fetch_text(f"{base_url}/_raya/search/index.html")
        search_js = _fetch_text(f"{base_url}/_raya/render/search.js")

        assert 'data-raya-surface="search"' in search_html
        assert "raya-search-data" in search_html
        assert "pagefind" not in search_html.lower()
        assert "https://" not in search_html
        assert "http://" not in search_html
        assert "fetch(" not in search_js
        assert "XMLHttpRequest" not in search_js

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
                        browser_requests: list[str] = []
                        page.on("request", lambda request: browser_requests.append(request.url))
                        page.goto(f"{base_url}/_raya/search/index.html", wait_until="networkidle")
                        assert browser_requests
                        assert all(url.startswith(f"{base_url}/") for url in browser_requests)
                        _assert_no_horizontal_overflow(page)
                        assert page.locator(".raya-discovery-command-bar").is_visible()
                        if viewport["width"] < 520:
                            discovery_box = page.locator(
                                ".raya-discovery-command-bar"
                            ).bounding_box()
                            assert discovery_box is not None
                            assert discovery_box["height"] <= 150
                        assert page.locator(".raya-command-graph").evaluate(
                            "node => node.href"
                        ).endswith("/_raya/graph/index.html")
                        assert page.locator(".raya-command-size").is_visible()
                        assert page.locator(".raya-command-font").is_visible()
                        before = page.locator(
                            "#raya-search-results [data-raya-search-result]:visible"
                        ).count()
                        page.fill("#raya-search-input", "matrix")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-search-status')
                              ?.textContent
                              ?.includes('visible result')"""
                        )
                        after = page.locator(
                            "#raya-search-results [data-raya-search-result]:visible"
                        ).count()
                        assert after < before
                        assert "Authoring Matrix Fixture" in page.locator(
                            "#raya-search-results"
                        ).inner_text()
                        assert page.locator("#raya-search-empty").is_hidden()
                        page.fill("#raya-search-input", "matrx")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-search-status')
                              ?.textContent
                              ?.includes('visible result')"""
                        )
                        assert "Authoring Matrix Fixture" in page.locator(
                            "#raya-search-results"
                        ).inner_text()
                        page.press("#raya-search-input", "ArrowDown")
                        active = page.locator(
                            '#raya-search-results [data-raya-search-active="true"]'
                        )
                        assert active.count() == 1
                        active_href = active.locator("a").evaluate("node => node.href")
                        with page.expect_navigation():
                            page.press("#raya-search-input", "Enter")
                        assert page.url == active_href
                        page.goto(
                            f"{base_url}/_raya/search/index.html",
                            wait_until="networkidle",
                        )
                        page.fill("#raya-search-input", "matrix")
                        page.click("#raya-search-clear")
                        assert page.input_value("#raya-search-input") == ""
                        assert (
                            page.locator(
                                '#raya-search-results [data-raya-search-active="true"]'
                            ).count()
                            == 0
                        )
                        assert page.locator("#raya-search-empty").is_hidden()
                        page.fill("#raya-search-input", "zz-no-result")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-search-empty')
                              ?.hidden === false"""
                        )
                        page.goto(
                            f"{base_url}/_raya/search/index.html?q=Authoring%20Matrix%20Fixture",
                            wait_until="networkidle",
                        )
                        assert page.input_value("#raya-search-input") == (
                            "Authoring Matrix Fixture"
                        )
                        assert "Authoring Matrix Fixture" in page.locator(
                            "#raya-search-results"
                        ).inner_text()
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()


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
    assert '<button class="raya-command raya-command-font raya-font-toggle"' in index_html
    assert 'aria-pressed="false"' in index_html
    assert 'href="_raya/render/accessibility/open-dyslexic.css"' in index_html
    assert 'src="_raya/render/accessibility/open-dyslexic-toggle.js"' in index_html
    assert "@font-face" in accessibility_css
    assert "OpenDyslexic" in accessibility_css
    assert "localStorage" in accessibility_js
    assert "data-raya-open-dyslexic" in accessibility_js
    assert 'data-raya-course-map="expanded"' in index_html
    assert (
        'aria-expanded="true" aria-label="Collapse course map">Course map</button>'
        in index_html
    )
    assert 'class="raya-learning-shell" data-raya-course-map="expanded"' in index_html
    assert 'class="raya-course-map" aria-label="Course map" data-raya-course-map="expanded"' in index_html
    assert 'class="raya-course-map-list" id="raya-course-map-list" aria-hidden="false"' in index_html
    assert 'data-raya-map-label="1 Static Path">1 Static Path</a>' in index_html
    assert 'data-raya-rail-toggle' in reader_html
    assert 'data-raya-rail-panel-state="collapsed"' in reader_html
    assert 'aria-hidden="true" inert' in reader_html
    assert "background: var(--raya-color-page)" in rich_css
    assert "background: var(--raya-color-surface)" in rich_css
    assert "max-width: 116rem" in rich_css
    assert "grid-template-columns: minmax(13.75rem, 16rem) minmax(0, 1fr) minmax(16rem, 18rem)" in rich_css
    assert "@media (min-width: 901px)" in rich_css
    assert "grid-template-columns: 4.25rem minmax(0, 1fr) minmax(16rem, 18rem)" in rich_css
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


def test_render_fixture_text_size_toggle_changes_reader_scale(
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
                context = browser.new_context(viewport={"width": 1280, "height": 900})
                try:
                    page = context.new_page()
                    try:
                        requested_urls: list[str] = []
                        page.on(
                            "request",
                            lambda request: requested_urls.append(request.url),
                        )
                        page.goto(f"{base_url}/index.html", wait_until="networkidle")
                        requested_urls.clear()
                        before_url = page.url
                        initial = page.evaluate(
                            """() => ({
                              size: document.documentElement.getAttribute('data-raya-text-size'),
                              skin: document.body.getAttribute('data-raya-skin'),
                              label: document.querySelector('.raya-text-size-toggle')
                                ?.getAttribute('aria-label'),
                              pressed: document.querySelector('.raya-text-size-toggle')
                                ?.getAttribute('aria-pressed'),
                              articleFontSize: parseFloat(
                                getComputedStyle(document.querySelector('.raya-main-article')).fontSize
                              ),
                            })"""
                        )

                        page.click(".raya-text-size-toggle")
                        large = page.evaluate(
                            """() => ({
                              size: document.documentElement.getAttribute('data-raya-text-size'),
                              skin: document.body.getAttribute('data-raya-skin'),
                              label: document.querySelector('.raya-text-size-toggle')
                                ?.getAttribute('aria-label'),
                              pressed: document.querySelector('.raya-text-size-toggle')
                                ?.getAttribute('aria-pressed'),
                              articleFontSize: parseFloat(
                                getComputedStyle(document.querySelector('.raya-main-article')).fontSize
                              ),
                              stored: localStorage.getItem('raya:text-size'),
                              url: window.location.href,
                            })"""
                        )

                        page.click(".raya-text-size-toggle")
                        x_large = page.evaluate(
                            """() => ({
                              size: document.documentElement.getAttribute('data-raya-text-size'),
                              skin: document.body.getAttribute('data-raya-skin'),
                              label: document.querySelector('.raya-text-size-toggle')
                                ?.getAttribute('aria-label'),
                              pressed: document.querySelector('.raya-text-size-toggle')
                                ?.getAttribute('aria-pressed'),
                              articleFontSize: parseFloat(
                                getComputedStyle(document.querySelector('.raya-main-article')).fontSize
                              ),
                              stored: localStorage.getItem('raya:text-size'),
                              url: window.location.href,
                            })"""
                        )
                        text_size_click_urls = requested_urls.copy()

                        page.reload(wait_until="networkidle")
                        persisted = page.evaluate(
                            """() => ({
                              size: document.documentElement.getAttribute('data-raya-text-size'),
                              label: document.querySelector('.raya-text-size-toggle')
                                ?.getAttribute('aria-label'),
                              articleFontSize: parseFloat(
                                getComputedStyle(document.querySelector('.raya-main-article')).fontSize
                              ),
                              url: window.location.href,
                            })"""
                        )

                        requested_urls.clear()
                        page.click(".raya-text-size-toggle")
                        normal = page.evaluate(
                            """() => ({
                              size: document.documentElement.getAttribute('data-raya-text-size'),
                              skin: document.body.getAttribute('data-raya-skin'),
                              label: document.querySelector('.raya-text-size-toggle')
                                ?.getAttribute('aria-label'),
                              pressed: document.querySelector('.raya-text-size-toggle')
                                ?.getAttribute('aria-pressed'),
                              articleFontSize: parseFloat(
                                getComputedStyle(document.querySelector('.raya-main-article')).fontSize
                              ),
                              stored: localStorage.getItem('raya:text-size'),
                              url: window.location.href,
                            })"""
                        )
                        text_size_click_urls.extend(requested_urls)

                        page.evaluate(
                            "() => localStorage.setItem('raya:text-size', 'huge')"
                        )
                        page.reload(wait_until="networkidle")
                        invalid_fallback = page.evaluate(
                            """() => ({
                              size: document.documentElement.getAttribute('data-raya-text-size'),
                              label: document.querySelector('.raya-text-size-toggle')
                                ?.getAttribute('aria-label'),
                              pressed: document.querySelector('.raya-text-size-toggle')
                                ?.getAttribute('aria-pressed'),
                              articleFontSize: parseFloat(
                                getComputedStyle(document.querySelector('.raya-main-article')).fontSize
                              ),
                              url: window.location.href,
                            })"""
                        )
                    finally:
                        page.close()
                finally:
                    context.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert initial["size"] == "normal"
    assert initial["skin"] == "eva-unit-02"
    assert initial["label"] == "Text size: normal"
    assert initial["pressed"] == "false"
    assert large["size"] == "large"
    assert large["skin"] == initial["skin"]
    assert large["label"] == "Text size: large"
    assert large["pressed"] == "true"
    assert large["stored"] == "large"
    assert large["articleFontSize"] > initial["articleFontSize"]
    assert x_large["size"] == "x-large"
    assert x_large["skin"] == initial["skin"]
    assert x_large["label"] == "Text size: x-large"
    assert x_large["pressed"] == "true"
    assert x_large["stored"] == "x-large"
    assert x_large["articleFontSize"] > large["articleFontSize"]
    assert persisted["size"] == "x-large"
    assert persisted["label"] == "Text size: x-large"
    assert persisted["articleFontSize"] == x_large["articleFontSize"]
    assert normal["size"] == "normal"
    assert normal["skin"] == initial["skin"]
    assert normal["label"] == "Text size: normal"
    assert normal["pressed"] == "false"
    assert normal["stored"] == "normal"
    assert normal["articleFontSize"] == initial["articleFontSize"]
    assert invalid_fallback["size"] == "normal"
    assert invalid_fallback["label"] == "Text size: normal"
    assert invalid_fallback["pressed"] == "false"
    assert invalid_fallback["articleFontSize"] == initial["articleFontSize"]
    assert large["url"] == before_url
    assert x_large["url"] == before_url
    assert persisted["url"] == before_url
    assert normal["url"] == before_url
    assert invalid_fallback["url"] == before_url
    assert text_size_click_urls == []


def test_render_fixture_command_bar_controls_are_dense_and_operable(
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
                states = []
                for viewport in (
                    {"width": 1440, "height": 900},
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    try:
                        page.goto(f"{base_url}/index.html", wait_until="networkidle")
                        _assert_no_horizontal_overflow(page)
                        state = page.evaluate(
                            """() => {
                              const commands = Array.from(
                                document.querySelectorAll('.raya-command')
                              );
                              const topBar = document.querySelector('.raya-top-command-bar');
                              return {
                                count: commands.length,
                                minHeights: commands.map(
                                  (item) => item.getBoundingClientRect().height
                                ),
                                topBarWidth: topBar.scrollWidth,
                                viewportWidth: document.documentElement.clientWidth,
                                searchHref: document
                                  .querySelector('.raya-command-search')
                                  ?.getAttribute('href'),
                                graphHref: document
                                  .querySelector('.raya-command-graph')
                                  ?.getAttribute('href'),
                                mapExpanded: document
                                  .querySelector('.raya-command-map')
                                  ?.getAttribute('aria-expanded'),
                                sizeLabel: document
                                  .querySelector('.raya-command-size')
                                  ?.getAttribute('aria-label'),
                                sizePressed: document
                                  .querySelector('.raya-command-size')
                                  ?.getAttribute('aria-pressed'),
                                fontPressed: document
                                  .querySelector('.raya-command-font')
                                  ?.getAttribute('aria-pressed'),
                                contextText: document
                                  .querySelector('.raya-reading-context')
                                  ?.innerText,
                                contextWidth: document
                                  .querySelector('.raya-reading-context')
                                  ?.getBoundingClientRect().width,
                                prevHref: document
                                  .querySelector('.raya-reading-context-prev')
                                  ?.getAttribute('href') || '',
                                nextHref: document
                                  .querySelector('.raya-reading-context-next')
                                  ?.getAttribute('href') || '',
                          };
                        }"""
                        )
                        assert state["count"] == 5
                        assert all(height >= 36 for height in state["minHeights"])
                        assert state["topBarWidth"] <= state["viewportWidth"]
                        assert state["searchHref"] == (
                            "_raya/search/index.html?q=Raya%20Lucaria%20Render%20Fixture"
                        )
                        assert state["graphHref"] == "_raya/graph/index.html?page=render-root"
                        assert state["mapExpanded"] == "true"
                        assert state["sizeLabel"] == "Text size: normal"
                        assert state["sizePressed"] == "false"
                        assert state["fontPressed"] == "false"
                        assert "Raya Lucaria Render Fixture" in state["contextText"]
                        assert "Page 1 of 6" in state["contextText"]
                        assert state["contextWidth"] > 0
                        assert state["prevHref"] == ""
                        assert state["nextHref"] == "static-path/index.html"

                        page.click(".raya-command-map")
                        collapsed_state = page.evaluate(
                            """() => {
                              const command = document.querySelector('.raya-command-map');
                              const bounds = command.getBoundingClientRect();
                              return {
                                expanded: command.getAttribute('aria-expanded'),
                                label: command.innerText,
                                width: bounds.width,
                                height: bounds.height,
                                topBarWidth: document
                                  .querySelector('.raya-top-command-bar')
                                  .scrollWidth,
                                viewportWidth: document.documentElement.clientWidth,
                              };
                            }"""
                        )
                        assert collapsed_state["expanded"] == "false"
                        assert collapsed_state["label"] == "Course map"
                        assert collapsed_state["height"] >= 36
                        assert collapsed_state["height"] < 72
                        assert collapsed_state["width"] < 180
                        assert (
                            collapsed_state["topBarWidth"]
                            <= collapsed_state["viewportWidth"]
                        )
                        page.click(".raya-command-size")
                        after_size = page.evaluate(
                            """() => ({
                              label: document
                                .querySelector('.raya-command-size')
                                ?.getAttribute('aria-label'),
                              pressed: document
                                .querySelector('.raya-command-size')
                                ?.getAttribute('aria-pressed'),
                              rootSize: document.documentElement
                                .getAttribute('data-raya-text-size'),
                            })"""
                        )
                        assert after_size["label"] == "Text size: large"
                        assert after_size["pressed"] == "true"
                        assert after_size["rootSize"] == "large"
                        page.click(".raya-command-font")
                        after_font = page.evaluate(
                            """() => ({
                              pressed: document
                                .querySelector('.raya-command-font')
                                ?.getAttribute('aria-pressed'),
                              bodyFont: getComputedStyle(document.body).fontFamily,
                            })"""
                        )
                        assert after_font["pressed"] == "true"
                        assert "OpenDyslexic" in after_font["bodyFont"]
                        states.append(state)
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert len(states) == 2


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
                        assert (
                            "raya-skip-link" in focused
                            or "raya-text-size-toggle" in focused
                            or "raya-font-toggle" in focused
                        )
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


def test_render_fixture_course_map_hierarchy_filters_without_requests(
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
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                requested_urls: list[str] = []
                page.on("request", lambda request: requested_urls.append(request.url))
                try:
                    page.goto(
                        f"{handle.base_url}/authoring-matrix/index.html",
                        wait_until="networkidle",
                    )
                    requested_urls.clear()
                    assert page.locator("[data-raya-map-active='ancestor']").count() > 0
                    desktop_map_region = page.evaluate(
                        """() => {
                          const map = document.querySelector('.raya-course-map');
                          if (!map) return null;
                          const style = getComputedStyle(map);
                          return {
                            maxHeight: style.maxHeight,
                            overflowY: style.overflowY,
                          };
                        }"""
                    )
                    assert desktop_map_region is not None
                    assert desktop_map_region["maxHeight"] != "none"
                    assert desktop_map_region["overflowY"] in {"auto", "scroll"}
                    page.evaluate(
                        """() => {
                          const map = document.querySelector('.raya-course-map');
                          const list = document.querySelector('#raya-course-map-list');
                          const filter = document.querySelector('#raya-course-map-filter');
                          if (!map || !list || !filter) {
                            throw new Error('missing course map controls');
                          }
                          map.style.transition = 'none';
                          map.style.setProperty('max-height', '5rem', 'important');
                          map.style.setProperty('overflow', 'auto', 'important');
                          map.scrollTop = 0;
                          delete map.dataset.rayaCourseMapOriented;
                          filter.value = 'matrix';
                          window.rayaOrientCourseMapToCurrentPageAutomatic?.();
                          if (map.scrollTop !== 0) {
                            throw new Error('filtered automatic orientation scrolled');
                          }
                          filter.value = '';
                          window.rayaOrientCourseMapToCurrentPage?.();
                        }"""
                    )
                    orientation = page.evaluate(
                        """() => {
                          const map = document.querySelector('.raya-course-map');
                          const list = document.querySelector('#raya-course-map-list');
                          const current = list?.querySelector('a[aria-current="page"]');
                          if (!map || !list || !current) return null;
                          const mapRect = map.getBoundingClientRect();
                          const currentRect = current.getBoundingClientRect();
                          return {
                            oriented: map.dataset.rayaCourseMapOriented,
                            scrollTop: map.scrollTop,
                            currentTop: currentRect.top,
                            currentBottom: currentRect.bottom,
                            mapTop: mapRect.top,
                            mapBottom: mapRect.bottom,
                            localStorageKeys: Object.keys(localStorage),
                            sessionStorageKeys: Object.keys(sessionStorage),
                          };
                        }"""
                    )
                    assert orientation is not None
                    assert orientation["oriented"] == "true"
                    assert orientation["scrollTop"] > 0
                    assert orientation["currentTop"] >= orientation["mapTop"]
                    assert orientation["currentBottom"] <= orientation["mapBottom"]
                    assert orientation["localStorageKeys"] == []
                    assert orientation["sessionStorageKeys"] == []
                    page.click(".raya-course-map-toggle")
                    page.evaluate(
                        """() => {
                          const map = document.querySelector('.raya-course-map');
                          if (!map) throw new Error('missing course map');
                          map.scrollTop = 0;
                          map.dataset.rayaCourseMapOriented = 'true';
                        }"""
                    )
                    page.click(".raya-course-map-toggle")
                    page.wait_for_function(
                        """() => {
                          const map = document.querySelector('.raya-course-map');
                          return !!map && map.scrollTop > 0;
                        }"""
                    )
                    reexpanded = page.evaluate(
                        """() => {
                          const map = document.querySelector('.raya-course-map');
                          const list = document.querySelector('#raya-course-map-list');
                          const current = list?.querySelector('a[aria-current="page"]');
                          if (!map || !current) return null;
                          const mapRect = map.getBoundingClientRect();
                          const currentRect = current.getBoundingClientRect();
                          return {
                            scrollTop: map.scrollTop,
                            currentTop: currentRect.top,
                            currentBottom: currentRect.bottom,
                            mapTop: mapRect.top,
                            mapBottom: mapRect.bottom,
                          };
                        }"""
                    )
                    assert reexpanded is not None
                    assert reexpanded["scrollTop"] > 0
                    assert reexpanded["currentTop"] >= reexpanded["mapTop"]
                    assert reexpanded["currentBottom"] <= reexpanded["mapBottom"]
                    first_toggle = page.locator("[data-raya-map-node-toggle]").first
                    before = first_toggle.get_attribute("aria-expanded")
                    first_toggle.click()
                    after = first_toggle.get_attribute("aria-expanded")
                    assert before != after
                    page.fill("#raya-course-map-filter", "matrix")
                    assert page.locator("[data-raya-map-node]:visible").count() >= 1
                    assert "matrix" in page.locator("#raya-course-map-list").inner_text().lower()
                    assert page.locator("[data-raya-map-filter-empty]").is_hidden()
                    page.fill("#raya-course-map-filter", "zz-no-match")
                    assert page.locator("[data-raya-map-filter-empty]").is_visible()
                    page.fill("#raya-course-map-filter", "")
                    assert page.locator("[data-raya-map-filter-empty]").is_hidden()
                    assert requested_urls == []
                    _assert_no_horizontal_overflow(page)
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_minimal_course_map_nested_sections_are_expanded_and_collapsible(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "minimal"
    shutil.copytree(MINIMAL, course, ignore=shutil.ignore_patterns("artifact"))
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
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                requested_urls: list[str] = []
                page.on("request", lambda request: requested_urls.append(request.url))
                try:
                    page.goto(f"{handle.base_url}/unit/topic/index.html", wait_until="networkidle")
                    requested_urls.clear()
                    initial = page.evaluate(
                        """() => ({
                          firstUnitExpanded: document
                            .querySelector('[data-raya-map-node="first-unit"] [data-raya-map-node-toggle]')
                            ?.getAttribute('aria-expanded'),
                          firstUnitChildrenHidden: document
                            .querySelector('#raya-map-children-2-first-unit')
                            ?.hasAttribute('hidden'),
                          firstTopicVisible: !!document
                            .querySelector('[data-raya-map-node="first-topic"]')
                            ?.checkVisibility(),
                          filterVisible: !!document
                            .querySelector('#raya-course-map-filter')
                            ?.checkVisibility(),
                        })"""
                    )
                    assert initial == {
                        "firstUnitExpanded": "true",
                        "firstUnitChildrenHidden": False,
                        "firstTopicVisible": True,
                        "filterVisible": True,
                    }

                    page.click('[data-raya-map-node="first-unit"] [data-raya-map-node-toggle]')
                    collapsed_unit = page.evaluate(
                        """() => ({
                          firstUnitExpanded: document
                            .querySelector('[data-raya-map-node="first-unit"] [data-raya-map-node-toggle]')
                            ?.getAttribute('aria-expanded'),
                          firstUnitChildrenHidden: document
                            .querySelector('#raya-map-children-2-first-unit')
                            ?.hasAttribute('hidden'),
                          firstUnitChildrenAria: document
                            .querySelector('#raya-map-children-2-first-unit')
                            ?.getAttribute('aria-hidden'),
                          firstTopicVisible: !!document
                            .querySelector('[data-raya-map-node="first-topic"]')
                            ?.checkVisibility(),
                        })"""
                    )
                    assert collapsed_unit == {
                        "firstUnitExpanded": "false",
                        "firstUnitChildrenHidden": True,
                        "firstUnitChildrenAria": "true",
                        "firstTopicVisible": False,
                    }

                    page.click(".raya-course-map-toggle")
                    page.wait_for_function(
                        """() => document.documentElement.dataset.rayaCourseMap === 'collapsed'"""
                    )
                    compact = page.evaluate(
                        """() => ({
                          firstTopicVisible: !!document
                            .querySelector('[data-raya-map-node="first-topic"]')
                            ?.checkVisibility(),
                          filterVisible: !!document
                            .querySelector('#raya-course-map-filter')
                            ?.checkVisibility(),
                          emptyVisible: !!document
                            .querySelector('[data-raya-map-filter-empty]')
                            ?.checkVisibility(),
                        })"""
                    )
                    assert compact == {
                        "firstTopicVisible": False,
                        "filterVisible": False,
                        "emptyVisible": False,
                    }

                    page.click(".raya-course-map-toggle")
                    page.click('[data-raya-map-node="first-unit"] [data-raya-map-node-toggle]')
                    page.fill("#raya-course-map-filter", "topic")
                    filtered = page.evaluate(
                        """() => ({
                          firstUnitExpanded: document
                            .querySelector('[data-raya-map-node="first-unit"] [data-raya-map-node-toggle]')
                            ?.getAttribute('aria-expanded'),
                          firstTopicVisible: !!document
                            .querySelector('[data-raya-map-node="first-topic"]')
                            ?.checkVisibility(),
                          emptyVisible: !!document
                            .querySelector('[data-raya-map-filter-empty]')
                            ?.checkVisibility(),
                        })"""
                    )
                    assert filtered == {
                        "firstUnitExpanded": "true",
                        "firstTopicVisible": True,
                        "emptyVisible": False,
                    }
                    page.fill("#raya-course-map-filter", "zz-no-match")
                    page.click(".raya-course-map-toggle")
                    page.wait_for_function(
                        """() => document.documentElement.dataset.rayaCourseMap === 'collapsed'"""
                    )
                    compact_after_filter = page.evaluate(
                        """() => ({
                          filterValue: document.querySelector('#raya-course-map-filter')?.value,
                          visibleLinks: Array.from(document.querySelectorAll('#raya-course-map a'))
                            .filter((link) => link.checkVisibility()).length,
                          filterVisible: !!document
                            .querySelector('#raya-course-map-filter')
                            ?.checkVisibility(),
                          emptyVisible: !!document
                            .querySelector('[data-raya-map-filter-empty]')
                            ?.checkVisibility(),
                        })"""
                    )
                    assert compact_after_filter == {
                        "filterValue": "",
                        "visibleLinks": 3,
                        "filterVisible": False,
                        "emptyVisible": False,
                    }
                    assert requested_urls == []
                    _assert_no_horizontal_overflow(page)
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_keyboard_shortcuts_move_between_sequence_pages(
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
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                try:
                    page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                    page.keyboard.press("ArrowRight")
                    page.wait_for_url("**/static-path/index.html")
                    assert page.url.endswith("/static-path/index.html")

                    page.evaluate(
                        """() => {
                          const input = document.createElement('input');
                          input.id = 'keyboard-nav-guard';
                          input.type = 'text';
                          document.querySelector('#raya-article')?.prepend(input);
                        }"""
                    )
                    page.focus("#keyboard-nav-guard")
                    page.keyboard.press("ArrowRight")
                    page.wait_for_timeout(250)
                    assert page.url.endswith("/static-path/index.html")

                    page.locator("#raya-article").focus()
                    alt_arrow_not_canceled = page.evaluate(
                        """() => {
                          const event = new KeyboardEvent('keydown', {
                            key: 'ArrowRight',
                            altKey: true,
                            bubbles: true,
                            cancelable: true,
                          });
                          return document.dispatchEvent(event);
                        }"""
                    )
                    page.wait_for_timeout(250)
                    assert alt_arrow_not_canceled is True
                    assert page.url.endswith("/static-path/index.html")

                    page.keyboard.press("Alt+j")
                    page.wait_for_url("**/math-authoring/index.html")
                    assert page.url.endswith("/math-authoring/index.html")

                    page.keyboard.press("Alt+k")
                    page.wait_for_url("**/static-path/index.html")
                    assert page.url.endswith("/static-path/index.html")

                    page.keyboard.press("ArrowLeft")
                    page.wait_for_url("**/index.html")
                    assert page.url.endswith("/index.html")
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_code_copy_button_copies_code_text(tmp_path: Path) -> None:
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
                context = browser.new_context(viewport={"width": 1280, "height": 900})
                try:
                    page = context.new_page()
                    try:
                        page.goto(f"{handle.base_url}/index.html", wait_until="networkidle")
                        page.evaluate(
                            """() => {
                              window.__rayaCopiedText = "";
                              Object.defineProperty(navigator, "clipboard", {
                                configurable: true,
                                value: {
                                  writeText: async (text) => {
                                    window.__rayaCopiedText = text;
                                  },
                                },
                              });
                            }"""
                        )

                        copy_button = page.locator("[data-raya-copy-code]").first
                        copy_button.focus()
                        assert copy_button.evaluate("button => document.activeElement === button")
                        copy_button.click()
                        page.wait_for_function("() => window.__rayaCopiedText.length > 0")

                        copied = page.evaluate("() => window.__rayaCopiedText")
                        assert copied == (
                            'def fixture_value() -> str:\n'
                            '    return "<rendered, not executed>"\n'
                        )
                        assert copy_button.inner_text() == "Copied"
                        assert copy_button.get_attribute("aria-label") == "Code block copied"
                        assert page.url.endswith("/index.html")

                        page.reload(wait_until="networkidle")
                        page.evaluate(
                            """() => {
                              window.__rayaFallbackCopiedText = "";
                              Object.defineProperty(navigator, "clipboard", {
                                configurable: true,
                                value: undefined,
                              });
                              document.execCommand = (command) => {
                                if (command !== "copy") {
                                  return false;
                                }
                                const textarea = document.querySelector("textarea");
                                window.__rayaFallbackCopiedText = textarea ? textarea.value : "";
                                return true;
                              };
                            }"""
                        )
                        fallback_button = page.locator("[data-raya-copy-code]").first
                        fallback_button.click()
                        page.wait_for_function(
                            "() => window.__rayaFallbackCopiedText.length > 0"
                        )
                        fallback_copied = page.evaluate(
                            "() => window.__rayaFallbackCopiedText"
                        )
                        assert fallback_copied == copied
                        assert fallback_button.inner_text() == "Copied"
                    finally:
                        page.close()
                finally:
                    context.close()
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
                          activeElement: document.activeElement?.id,
                          mapWidth: document.querySelector('#raya-course-map')?.getBoundingClientRect().width,
                          articleWidth: document.querySelector('#raya-article')?.getBoundingClientRect().width,
                          firstLinkWidth: document.querySelector('#raya-course-map a')
                            ?.getBoundingClientRect().width,
                          firstLinkPointerEvents: getComputedStyle(
                            document.querySelector('#raya-course-map a')
                          ).pointerEvents,
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
                    assert collapsed["listHidden"] == "false"
                    assert collapsed["listInert"] is False
                    assert 56 <= collapsed["mapWidth"] <= 84
                    assert collapsed["articleWidth"] > 760
                    assert collapsed["texts"][1] in {"Expand map", "Map"}
                    assert collapsed["buttonVisualLabel"] == '"Map"'
                    assert collapsed["wrappedLinkTexts"] == []
                    assert collapsed["firstLinkWidth"] <= collapsed["mapWidth"]
                    assert collapsed["firstLinkPointerEvents"] == "auto"
                    assert collapsed["linkTabIndexes"]
                    assert set(collapsed["linkTabIndexes"]) == {None}

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

                    page.locator("#raya-course-map a").first.focus()
                    page.keyboard.press("Escape")
                    page.wait_for_function(
                        """() => document.documentElement.dataset.rayaCourseMap === 'collapsed'"""
                    )
                    escape_collapsed = page.evaluate(
                        """() => ({
                          activeElementClass: document.activeElement?.className,
                          activeElementText: document.activeElement?.textContent.trim(),
                          listHidden: document.querySelector('#raya-course-map-list')?.getAttribute('aria-hidden'),
                          listInert: document.querySelector('#raya-course-map-list')?.inert,
                          linkTabIndexes: Array.from(document.querySelectorAll('#raya-course-map a'))
                            .map((link) => link.getAttribute('tabindex')),
                        })"""
                    )
                    assert "raya-course-map-toggle" in escape_collapsed["activeElementClass"]
                    assert escape_collapsed["activeElementText"] == "Expand map"
                    assert escape_collapsed["listHidden"] == "false"
                    assert escape_collapsed["listInert"] is False
                    assert set(escape_collapsed["linkTabIndexes"]) == {None}
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
                page.add_init_script("delete HTMLElement.prototype.inert;")
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
                            linkTabIndex: link?.getAttribute('tabindex'),
                          };
                        }"""
                    )
                    assert collapsed["state"] == "collapsed"
                    assert collapsed["expanded"] == "false"
                    assert collapsed["ariaHidden"] == "true"
                    assert collapsed["inert"] is True
                    assert collapsed["bodyHeight"] < 2
                    assert collapsed["hasLink"] is True
                    assert collapsed["linkTabIndex"] == "-1"

                    link_panel.locator("[data-raya-rail-toggle]").click()
                    page.wait_for_function(
                        """() => document
                          .querySelector('.raya-page-prerequisites')
                          ?.dataset.rayaRailPanelState === 'expanded'"""
                    )
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
                            linkTabIndex: link?.getAttribute('tabindex'),
                            linkFocused: document.activeElement === link,
                          };
                        }"""
                    )
                    assert expanded["state"] == "expanded"
                    assert expanded["expanded"] == "true"
                    assert expanded["ariaHidden"] == "false"
                    assert expanded["inert"] in {False, None}
                    assert expanded["linkTabIndex"] is None
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_learning_rail_collapses_to_compact_context_tab(
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
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                try:
                    page.goto(f"{handle.base_url}/reader-ux/index.html", wait_until="networkidle")
                    _assert_no_horizontal_overflow(page)
                    initial = page.evaluate(
                        """() => {
                          const root = document.documentElement;
                          const shell = document.querySelector('#raya-content');
                          const rail = document.querySelector('#raya-learning-rail');
                          const body = document.querySelector('#raya-learning-rail-body');
                          const article = document.querySelector('#raya-article');
                          const expand = document.querySelector('[data-raya-learning-rail-expand]');
                          return {
                            rootState: root.dataset.rayaLearningRail,
                            shellState: shell?.dataset.rayaLearningRail,
                            railState: rail?.dataset.rayaLearningRail,
                            bodyHidden: body?.getAttribute('aria-hidden'),
                            bodyInert: body?.inert,
                            articleWidth: article?.getBoundingClientRect().width,
                            railWidth: rail?.getBoundingClientRect().width,
                            expandVisible: !!expand && getComputedStyle(expand).display !== 'none',
                            collapseExpanded: document
                              .querySelector('[data-raya-learning-rail-collapse]')
                              ?.getAttribute('aria-expanded'),
                          };
                        }"""
                    )
                    assert initial["rootState"] == "expanded"
                    assert initial["shellState"] == "expanded"
                    assert initial["railState"] == "expanded"
                    assert initial["bodyHidden"] == "false"
                    assert initial["bodyInert"] in {False, None}
                    assert initial["articleWidth"] > 520
                    assert 240 <= initial["railWidth"] <= 330
                    assert initial["expandVisible"] is False
                    assert initial["collapseExpanded"] == "true"

                    page.click("[data-raya-learning-rail-collapse]")
                    page.wait_for_function(
                        """() => document
                          .querySelector('#raya-learning-rail')
                          ?.getBoundingClientRect()
                          ?.width < 120"""
                    )
                    collapsed = page.evaluate(
                        """() => {
                          const root = document.documentElement;
                          const shell = document.querySelector('#raya-content');
                          const rail = document.querySelector('#raya-learning-rail');
                          const body = document.querySelector('#raya-learning-rail-body');
                          const article = document.querySelector('#raya-article');
                          const expand = document.querySelector('[data-raya-learning-rail-expand]');
                          const bodyLink = body?.querySelector('a');
                          return {
                            rootState: root.dataset.rayaLearningRail,
                            shellState: shell?.dataset.rayaLearningRail,
                            railState: rail?.dataset.rayaLearningRail,
                            bodyHidden: body?.getAttribute('aria-hidden'),
                            bodyInert: body?.inert,
                            articleWidth: article?.getBoundingClientRect().width,
                            railWidth: rail?.getBoundingClientRect().width,
                            expandVisible: !!expand && getComputedStyle(expand).display !== 'none',
                            expandExpanded: expand?.getAttribute('aria-expanded'),
                            bodyLinkTabIndex: bodyLink?.getAttribute('tabindex'),
                            wrappedExpandText: expand?.innerText.includes('\\n'),
                          };
                        }"""
                    )
                    assert collapsed["rootState"] == "collapsed"
                    assert collapsed["shellState"] == "collapsed"
                    assert collapsed["railState"] == "collapsed"
                    assert collapsed["bodyHidden"] == "true"
                    assert collapsed["bodyInert"] is True
                    assert collapsed["articleWidth"] > initial["articleWidth"]
                    assert collapsed["railWidth"] < 120
                    assert collapsed["expandVisible"] is True
                    assert collapsed["expandExpanded"] == "false"
                    assert collapsed["bodyLinkTabIndex"] == "-1"
                    assert collapsed["wrappedExpandText"] is False

                    page.click("[data-raya-learning-rail-expand]")
                    page.wait_for_function(
                        """() => document
                          .querySelector('#raya-learning-rail')
                          ?.getBoundingClientRect()
                          ?.width >= 240"""
                    )
                    expanded = page.evaluate(
                        """() => {
                          const body = document.querySelector('#raya-learning-rail-body');
                          const rail = document.querySelector('#raya-learning-rail');
                          return {
                            rootState: document.documentElement.dataset.rayaLearningRail,
                            railState: rail?.dataset.rayaLearningRail,
                            bodyHidden: body?.getAttribute('aria-hidden'),
                            bodyInert: body?.inert,
                            railWidth: rail?.getBoundingClientRect().width,
                          };
                        }"""
                    )
                    assert expanded["rootState"] == "expanded"
                    assert expanded["railState"] == "expanded"
                    assert expanded["bodyHidden"] == "false"
                    assert expanded["bodyInert"] in {False, None}
                    assert expanded["railWidth"] >= 240

                    page.click("[data-raya-learning-rail-collapse]")
                    page.wait_for_function(
                        """() => document
                          .querySelector('#raya-learning-rail')
                          ?.getBoundingClientRect()
                          ?.width < 120"""
                    )
                    page.set_viewport_size({"width": 390, "height": 844})
                    page.wait_for_function(
                        """() => document
                          .querySelector('#raya-learning-rail')
                          ?.dataset
                          ?.rayaLearningRail === 'expanded'"""
                    )
                    resized_mobile = page.evaluate(
                        """() => {
                          const body = document.querySelector('#raya-learning-rail-body');
                          const expand = document.querySelector('[data-raya-learning-rail-expand]');
                          const collapse = document.querySelector('[data-raya-learning-rail-collapse]');
                          return {
                            rootState: document.documentElement.dataset.rayaLearningRail,
                            bodyHidden: body?.getAttribute('aria-hidden'),
                            bodyInert: body?.inert,
                            expandVisible: !!expand && getComputedStyle(expand).display !== 'none',
                            collapseVisible: !!collapse && getComputedStyle(collapse).display !== 'none',
                          };
                        }"""
                    )
                    assert resized_mobile["rootState"] == "expanded"
                    assert resized_mobile["bodyHidden"] == "false"
                    assert resized_mobile["bodyInert"] in {False, None}
                    assert resized_mobile["expandVisible"] is False
                    assert resized_mobile["collapseVisible"] is False

                    page.set_viewport_size({"width": 1280, "height": 900})
                    page.wait_for_function(
                        """() => document
                          .querySelector('#raya-learning-rail')
                          ?.getBoundingClientRect()
                          ?.width >= 240"""
                    )
                    page.focus("[data-raya-learning-rail-collapse]")
                    page.keyboard.press("Escape")
                    page.wait_for_function(
                        """() => document
                          .querySelector('#raya-learning-rail')
                          ?.dataset
                          ?.rayaLearningRail === 'collapsed'"""
                    )
                    escape_collapsed = page.evaluate(
                        """() => ({
                          rootState: document.documentElement.dataset.rayaLearningRail,
                          activeControl: document.activeElement
                            ?.getAttribute('data-raya-learning-rail-expand') !== null,
                          railWidth: document
                            .querySelector('#raya-learning-rail')
                            ?.getBoundingClientRect()
                            ?.width,
                          expandWidth: document
                            .querySelector('[data-raya-learning-rail-expand]')
                            ?.getBoundingClientRect()
                            ?.width,
                        })"""
                    )
                    assert escape_collapsed["rootState"] == "collapsed"
                    assert escape_collapsed["activeControl"] is True
                    assert escape_collapsed["expandWidth"] <= escape_collapsed["railWidth"]
                finally:
                    page.close()

                mobile = browser.new_page(viewport={"width": 390, "height": 844})
                try:
                    mobile.goto(f"{handle.base_url}/reader-ux/index.html", wait_until="networkidle")
                    _assert_no_horizontal_overflow(mobile)
                    mobile_state = mobile.evaluate(
                        """() => {
                          const expand = document.querySelector('[data-raya-learning-rail-expand]');
                          const collapse = document.querySelector('[data-raya-learning-rail-collapse]');
                          const rail = document.querySelector('#raya-learning-rail');
                          const article = document.querySelector('#raya-article');
                          return {
                            expandVisible: !!expand && getComputedStyle(expand).display !== 'none',
                            collapseVisible: !!collapse && getComputedStyle(collapse).display !== 'none',
                            articleTop: article?.getBoundingClientRect().top,
                            railTop: rail?.getBoundingClientRect().top,
                          };
                        }"""
                    )
                    assert mobile_state["expandVisible"] is False
                    assert mobile_state["collapseVisible"] is False
                    assert mobile_state["articleTop"] < mobile_state["railTop"]
                finally:
                    mobile.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_graph_context_panel_collapses_without_focus_leaks(
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
                page.add_init_script("delete HTMLElement.prototype.inert;")
                try:
                    page.goto(
                        f"{handle.base_url}/authoring-matrix/index.html",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(page)
                    panel = page.locator(".raya-page-linked-pages").first
                    collapsed = panel.evaluate(
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
                            linkTabIndex: link?.getAttribute('tabindex'),
                          };
                        }"""
                    )
                    assert collapsed["state"] == "collapsed"
                    assert collapsed["expanded"] == "false"
                    assert collapsed["ariaHidden"] == "true"
                    assert collapsed["inert"] is True
                    assert collapsed["bodyHeight"] < 2
                    assert collapsed["hasLink"] is True
                    assert collapsed["linkTabIndex"] == "-1"

                    panel.locator("[data-raya-rail-toggle]").click()
                    page.wait_for_function(
                        """() => document
                          .querySelector('.raya-page-linked-pages')
                          ?.dataset.rayaRailPanelState === 'expanded'"""
                    )
                    expanded = panel.evaluate(
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
                            linkTabIndex: link?.getAttribute('tabindex'),
                            text: panel.innerText,
                            summaryLabels: Array
                              .from(panel.querySelectorAll('.raya-rail-connection-summary span'))
                              .map((node) => node.innerText.replace(/\\s+/g, ' ').trim()),
                            counts: Array
                              .from(panel.querySelectorAll('.raya-rail-count'))
                              .map((node) => node.innerText.trim()),
                          };
                        }"""
                    )
                    assert expanded["state"] == "expanded"
                    assert expanded["expanded"] == "true"
                    assert expanded["ariaHidden"] == "false"
                    assert expanded["inert"] in {False, None}
                    assert expanded["linkTabIndex"] is None
                    assert "Connections" in expanded["text"]
                    assert expanded["summaryLabels"] == [
                        "3 from this page",
                        "1 link here",
                    ]
                    assert expanded["counts"] == ["3", "1"]
                    assert "From this page" in expanded["text"]
                    assert "Links here" in expanded["text"]
                    graph_link = panel.locator(
                        '.raya-rail-context-link[href="../_raya/graph/index.html?page=reader-ux"]'
                    )
                    graph_href = graph_link.evaluate("node => node.href")
                    with page.expect_navigation():
                        graph_link.click()
                    assert page.url == graph_href
                    page.wait_for_selector("[data-raya-graph-detail-panel]:not([hidden])")
                    assert "Reader UX Fixture" in page.locator(
                        "[data-raya-graph-detail-title]"
                    ).inner_text()
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
                    assert set(collapsed["linkTabIndexes"]) == {None}

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


def test_render_fixture_balanced_workspace_visual_hierarchy(tmp_path: Path) -> None:
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
                    page.goto(f"{handle.base_url}/authoring-matrix/index.html", wait_until="networkidle")
                    _assert_no_horizontal_overflow(page)
                    hierarchy = page.evaluate(
                        """() => {
                          const bodyStyle = getComputedStyle(document.body);
                          const article = document.querySelector('article.raya-main-article');
                          const shell = document.querySelector('.raya-learning-shell');
                          const courseMap = document.querySelector('nav.raya-course-map');
                          const rail = document.querySelector('aside.raya-learning-rail');
                          const articleStyle = getComputedStyle(article);
                          return {
                            bodyBackground: bodyStyle.backgroundColor,
                            articleBackground: articleStyle.backgroundColor,
                            articleWidth: article.getBoundingClientRect().width,
                            shellWidth: shell.getBoundingClientRect().width,
                            mapWidth: courseMap.getBoundingClientRect().width,
                            railWidth: rail.getBoundingClientRect().width,
                          };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert hierarchy["articleWidth"] > hierarchy["mapWidth"] * 2
    assert hierarchy["articleWidth"] > hierarchy["railWidth"] * 2
    assert hierarchy["articleWidth"] < hierarchy["shellWidth"]
    assert hierarchy["articleBackground"] != hierarchy["bodyBackground"]
    assert not _looks_like_eva_warm_wash(hierarchy["bodyBackground"])
    assert not _looks_like_eva_warm_wash(hierarchy["articleBackground"])


def test_render_fixture_desktop_shell_has_modern_workspace_chrome(
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
                page = browser.new_page(viewport={"width": 1680, "height": 980})
                try:
                    page.goto(f"{handle.base_url}/authoring-matrix/index.html", wait_until="networkidle")
                    _assert_no_horizontal_overflow(page)
                    chrome = page.evaluate(
                        """() => {
                          const rgb = (value) => value.match(/\\d+/g).slice(0, 3).map(Number);
                          const luminance = (value) => {
                            const [r, g, b] = rgb(value).map((channel) => channel / 255);
                            return 0.2126 * r + 0.7152 * g + 0.0722 * b;
                          };
                          const topBar = document.querySelector('.raya-top-command-bar');
                          const article = document.querySelector('article.raya-main-article');
                          const courseMap = document.querySelector('nav.raya-course-map');
                          const rail = document.querySelector('aside.raya-learning-rail');
                          const shell = document.querySelector('.raya-learning-shell');
                          const bodyStyle = getComputedStyle(document.body);
                          const topBarStyle = getComputedStyle(topBar);
                          const articleStyle = getComputedStyle(article);
                          const courseMapStyle = getComputedStyle(courseMap);
                          const railStyle = getComputedStyle(rail);
                          return {
                            shellWidth: shell.getBoundingClientRect().width,
                            articleWidth: article.getBoundingClientRect().width,
                            mapWidth: courseMap.getBoundingClientRect().width,
                            railWidth: rail.getBoundingClientRect().width,
                            courseMapButtonVisible: !!document
                              .querySelector('.raya-course-map-toggle')
                              ?.getClientRects().length,
                            fontButtonVisible: !!document
                              .querySelector('.raya-font-toggle')
                              ?.getClientRects().length,
                            topBarBackground: topBarStyle.backgroundColor,
                            topBarText: topBarStyle.color,
                            bodyBackground: bodyStyle.backgroundColor,
                            articleBackground: articleStyle.backgroundColor,
                            courseMapBackground: courseMapStyle.backgroundColor,
                            railBackground: railStyle.backgroundColor,
                            topBarLuminance: luminance(topBarStyle.backgroundColor),
                            pageLuminance: luminance(bodyStyle.backgroundColor),
                          };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert chrome["shellWidth"] > 1500
    assert chrome["articleWidth"] >= 820
    assert 220 <= chrome["mapWidth"] <= 300
    assert 250 <= chrome["railWidth"] <= 330
    assert chrome["topBarLuminance"] < chrome["pageLuminance"] - 0.35
    assert chrome["topBarBackground"] != chrome["bodyBackground"]
    assert chrome["topBarText"] != chrome["topBarBackground"]
    assert chrome["courseMapBackground"] != chrome["articleBackground"]
    assert chrome["railBackground"] != chrome["articleBackground"]
    assert chrome["courseMapButtonVisible"] is True
    assert chrome["fontButtonVisible"] is True


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
                    assert set(collapsed["linkTabIndexes"]) == {None}

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
    assert (
        '<aside id="raya-learning-rail" class="raya-learning-rail" '
        'aria-label="Learning context" data-raya-learning-rail="expanded">'
    ) in root_html
    assert root_html.index('<nav id="raya-course-map" class="raya-course-map"') < root_html.index(
        '<article id="raya-article"'
    )
    assert root_html.index('<article id="raya-article"') < root_html.index(
        '<aside id="raya-learning-rail"'
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
                                .map((node) => node.textContent),
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


def test_render_fixture_optional_static_environments_are_spoiler_safe(
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
                    before_url = page.url
                    closed_probe = page.evaluate(
                        """() => {
                            const details = document.querySelector(
                              '#raya-static-environment-hint-orthogonal-activity'
                            );
                            const summary = details?.querySelector('summary');
                            const body = details?.querySelector('.raya-static-environment-body');
                            const bodyHeight = body ? body.getBoundingClientRect().height : -1;
                            return {
                              tag: details?.tagName || '',
                              open: Boolean(details?.open),
                              summaryTag: summary?.tagName || '',
                              summaryCursor: summary ? getComputedStyle(summary).cursor : '',
                              summaryText: summary?.innerText || '',
                              bodyHeight,
                              bodyTextContent: body?.textContent || '',
                              location: window.location.href,
                            };
                        }"""
                    )

                    assert closed_probe["tag"] == "DETAILS"
                    assert closed_probe["summaryTag"] == "SUMMARY"
                    assert closed_probe["open"] is False
                    assert closed_probe["summaryCursor"] == "pointer"
                    assert closed_probe["summaryText"].startswith("Hint for Activity 4.1")
                    assert closed_probe["bodyHeight"] == 0
                    assert "Compare the projection formula" in closed_probe["bodyTextContent"]
                    assert closed_probe["location"] == before_url

                    page.locator(
                        "#raya-static-environment-hint-orthogonal-activity > summary"
                    ).click()
                    opened_probe = page.evaluate(
                        """() => {
                            const details = document.querySelector(
                              '#raya-static-environment-hint-orthogonal-activity'
                            );
                            const body = details?.querySelector('.raya-static-environment-body');
                            return {
                              open: Boolean(details?.open),
                              bodyHeight: body ? body.getBoundingClientRect().height : -1,
                              bodyInnerText: body?.innerText || '',
                              location: window.location.href,
                            };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert opened_probe["open"] is True
    assert opened_probe["bodyHeight"] > 0
    assert "Compare the projection formula" in opened_probe["bodyInnerText"]
    assert opened_probe["location"] == before_url
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


def _looks_like_eva_warm_wash(color: str) -> bool:
    match = re.fullmatch(r"rgba?\((\d+), (\d+), (\d+)(?:, [^)]+)?\)", color)
    assert match is not None, f"Unexpected computed color: {color}"
    red, green, blue = (int(channel) for channel in match.groups())
    return red >= 245 and green >= 225 and blue <= 245 and red - blue >= 10


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
