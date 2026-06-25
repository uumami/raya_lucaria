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


def _viewbox_values(value: str | None) -> tuple[float, float, float, float]:
    assert value is not None
    parts = value.split()
    assert len(parts) == 4
    return tuple(float(part) for part in parts)


def _viewbox_width(value: str | None) -> float:
    return _viewbox_values(value)[2]


def _graph_node_translate(page, node_id: str) -> tuple[float, float]:
    transform = page.locator(
        f'#raya-graph-canvas [data-raya-graph-node="{node_id}"] g'
    ).get_attribute("transform")
    assert transform is not None
    match = re.search(r"translate\(([-0-9.]+)\s+([-0-9.]+)\)", transform)
    assert match is not None
    return float(match.group(1)), float(match.group(2))


def _point_distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _boxes_intersect(outer: dict, inner: dict) -> bool:
    return not (
        inner["x"] + inner["width"] < outer["x"]
        or inner["x"] > outer["x"] + outer["width"]
        or inner["y"] + inner["height"] < outer["y"]
        or inner["y"] > outer["y"] + outer["height"]
    )


def _intersection_box(left: dict, right: dict) -> dict:
    x = max(left["x"], right["x"])
    y = max(left["y"], right["y"])
    width = max(0, min(left["x"] + left["width"], right["x"] + right["width"]) - x)
    height = max(0, min(left["y"] + left["height"], right["y"] + right["height"]) - y)
    return {"x": x, "y": y, "width": width, "height": height}


def _visible_graph_context(page, node_id: str, viewport: dict[str, int]) -> dict:
    return page.evaluate(
        """({ nodeId, viewport }) => {
          const canvas = document.querySelector('#raya-graph-canvas');
          const selected = document.querySelector(
            `#raya-graph-canvas [data-raya-graph-node="${nodeId}"] g`
          );
          const canvasBox = canvas.getBoundingClientRect();
          const selectedBox = selected.getBoundingClientRect();
          const visible = {
            x: Math.max(canvasBox.x, 0),
            y: Math.max(canvasBox.y, 0),
            right: Math.min(canvasBox.right, viewport.width),
            bottom: Math.min(canvasBox.bottom, viewport.height),
          };
          visible.width = Math.max(0, visible.right - visible.x);
          visible.height = Math.max(0, visible.bottom - visible.y);
          const intersects = (box) => !(
            box.right < visible.x ||
            box.x > visible.right ||
            box.bottom < visible.y ||
            box.y > visible.bottom
          );
          const edgeVisible = Array.from(
            document.querySelectorAll('#raya-graph-canvas .raya-graph-edge.is-active')
          ).some((edge) => (
            edge.getAttribute('data-raya-graph-from') === nodeId ||
            edge.getAttribute('data-raya-graph-to') === nodeId
          ) && intersects(edge.getBoundingClientRect()));
          return {
            canvas: {
              x: canvasBox.x,
              y: canvasBox.y,
              width: canvasBox.width,
              height: canvasBox.height,
            },
            visible,
            selected: {
              x: selectedBox.x,
              y: selectedBox.y,
              width: selectedBox.width,
              height: selectedBox.height,
            },
            selectedVisible: intersects(selectedBox),
            activeEdgeVisible: edgeVisible,
          };
        }""",
        {"nodeId": node_id, "viewport": viewport},
    )


def test_preview_serves_static_pages_files_reviewed_outputs_and_inspection(
    tmp_path: Path,
) -> None:
    from raya_cli.preview import create_preview

    course = tmp_path / "execution-fixture"
    shutil.copytree(
        EXECUTION_FIXTURE, course, ignore=shutil.ignore_patterns("artifact")
    )

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        base_url = handle.base_url
        assert base_url is not None

        root_html = _fetch_text(f"{base_url}/index.html")
        inspection_html = _fetch_text(f"{base_url}/_raya/inspect/index.html")
        manual_script = _fetch_text(
            f"{base_url}/_raya/files/_source/code/manual_task.py"
        )
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


def test_minimal_fixture_official_practice_is_static_and_revealable(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "minimal"
    shutil.copytree(MINIMAL, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        base_url = handle.base_url
        assert base_url is not None

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                for viewport in (
                    {"width": 1280, "height": 900},
                    {"width": 1120, "height": 900},
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    requested_urls: list[str] = []
                    page.on(
                        "request", lambda request: requested_urls.append(request.url)
                    )
                    try:
                        page.goto(
                            f"{base_url}/unit/topic/index.html",
                            wait_until="networkidle",
                        )
                        requested_urls.clear()
                        _assert_no_horizontal_overflow(page)
                        practice = page.locator(".raya-official-practice")
                        assert practice.is_visible()
                        assert page.locator(
                            "#raya-official-first-topic-card"
                        ).is_visible()
                        assert page.locator(
                            "#raya-official-first-topic-prompt"
                        ).is_visible()
                        assert page.locator(
                            "#raya-official-first-topic-quiz"
                        ).is_visible()
                        assert (
                            page.locator(
                                "#raya-official-first-topic-card details"
                            ).get_attribute("open")
                            is None
                        )
                        page.locator(
                            "#raya-official-first-topic-card details summary"
                        ).click()
                        assert (
                            page.locator(
                                "#raya-official-first-topic-card details"
                            ).get_attribute("open")
                            == ""
                        )
                        assert (
                            "Read, retrieve, reflect, adapt, revisit, and contribute."
                            in page.locator(
                                "#raya-official-first-topic-card"
                            ).inner_text()
                        )
                        page.locator(
                            "#raya-official-first-topic-quiz details summary"
                        ).click()
                        assert (
                            page.locator(
                                "#raya-official-first-topic-quiz details"
                            ).get_attribute("open")
                            == ""
                        )
                        assert (
                            "Correct option"
                            in page.locator(
                                "#raya-official-first-topic-quiz"
                            ).inner_text()
                        )
                        assert requested_urls == []
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_preview_reader_breadcrumbs_are_static_location_links(tmp_path: Path) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "minimal"
    shutil.copytree(MINIMAL, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        base_url = handle.base_url
        assert base_url is not None

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                for viewport in (
                    {"width": 1280, "height": 900},
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    requests: list[str] = []
                    page.on("request", lambda request: requests.append(request.url))
                    try:
                        page.goto(
                            f"{base_url}/unit/topic/index.html",
                            wait_until="networkidle",
                        )
                        assert requests
                        assert all(url.startswith(f"{base_url}/") for url in requests)
                        _assert_no_horizontal_overflow(page)
                        breadcrumbs = page.locator(".raya-breadcrumbs")
                        assert breadcrumbs.is_visible()
                        assert (
                            breadcrumbs.locator(
                                ".raya-breadcrumb-current"
                            ).get_attribute("aria-current")
                            == "page"
                        )
                        assert "First Topic" in breadcrumbs.inner_text()
                        ancestor_href = breadcrumbs.locator(
                            ".raya-breadcrumb-link"
                        ).evaluate("node => node.href")
                        with page.expect_navigation():
                            breadcrumbs.locator(".raya-breadcrumb-link").click()
                        assert page.url == ancestor_href
                        page.goto(
                            f"{base_url}/unit/topic/index.html",
                            wait_until="networkidle",
                        )
                        breadcrumbs = page.locator(".raya-breadcrumbs")
                        home_href = breadcrumbs.locator(
                            ".raya-breadcrumb-home"
                        ).evaluate("node => node.href")
                        with page.expect_navigation():
                            breadcrumbs.locator(".raya-breadcrumb-home").click()
                        assert page.url == home_href
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_preview_serves_local_assets(tmp_path: Path) -> None:
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        base_url = handle.base_url
        assert base_url is not None

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                for viewport in (
                    {"width": 1280, "height": 900},
                    {"width": 1120, "height": 900},
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    requested_urls: list[str] = []
                    page.on(
                        "request", lambda request: requested_urls.append(request.url)
                    )
                    try:
                        page.goto(f"{base_url}/index.html", wait_until="networkidle")
                        requested_urls.clear()
                        _assert_no_horizontal_overflow(page)
                        cards = page.locator(".raya-section-card")
                        assert cards.count() >= 5
                        first_link = page.locator(".raya-section-card-link").first
                        assert first_link.is_visible()
                        assert (
                            first_link.locator(".raya-section-card-title")
                            .inner_text()
                            .strip()
                        )
                        assert (
                            first_link.locator(".raya-section-card-summary")
                            .inner_text()
                            .strip()
                        )
                        box = first_link.bounding_box()
                        assert box is not None
                        assert box["width"] >= 180 or viewport["width"] < 500
                        href = first_link.evaluate("node => node.href")
                        with page.expect_navigation():
                            first_link.click()
                        assert page.url == href
                        assert requested_urls
                        assert all(
                            url.startswith(f"{base_url}/") for url in requested_urls
                        )
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
    official_dir = course / "course" / "5_authoring_matrix" / "_official" / "prompts"
    official_dir.mkdir(parents=True)
    (official_dir / "1_matrix_prompt.yaml").write_text(
        "\n".join(
            [
                "id: matrix-prompt",
                "type: prompt",
                "authority: official",
                "content:",
                "  prompt: Explain why the identity matrix preserves vector norms.",
                "retrieval:",
                "  kind: reflection",
                "",
            ]
        ),
        encoding="utf-8",
    )
    assignment_dir = (
        course / "course" / "5_authoring_matrix" / "_official" / "assignments"
    )
    assignment_dir.mkdir(parents=True)
    (assignment_dir / "1_matrix_assignment.yaml").write_text(
        "\n".join(
            [
                "id: matrix-assignment",
                "type: assignment",
                "authority: official",
                "scope:",
                "  quantum: authoring-matrix",
                "content:",
                "  title: Matrix graph check",
                "  summary: Trace the graph context for matrix notation.",
                "  due: '2026-11-03'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    for index in range(6, 18):
        crowded_page = course / "course" / f"{index}_crowded_{index}" / "0_index.md"
        crowded_page.parent.mkdir(parents=True)
        crowded_page.write_text(
            "\n".join(
                [
                    "---",
                    f"id: crowded-{index}",
                    f"title: Crowded Page {index}",
                    f"summary: Crowded layout fixture page {index}.",
                    "status: ready",
                    "---",
                    "",
                    f"# Crowded Page {index}",
                    "",
                    "Crowded layout fixture content.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    for index, title in (
        (1, "Cluster Math A"),
        (2, "Cluster Math B"),
    ):
        cluster_page = (
            course
            / "course"
            / "2_math_authoring"
            / f"{index}_cluster_math_{index}"
            / "0_index.md"
        )
        cluster_page.parent.mkdir(parents=True)
        cluster_page.write_text(
            "\n".join(
                [
                    "---",
                    f"id: cluster-math-{index}",
                    f"title: {title}",
                    f"summary: Cluster layout fixture page {index}.",
                    "status: ready",
                    "---",
                    "",
                    f"# {title}",
                    "",
                    "Cluster layout fixture content.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        base_url = handle.base_url
        assert base_url is not None
        graph_url = f"{base_url}/_raya/graph/index.html"
        graph_html = _fetch_text(graph_url)
        graph_js = _fetch_text(f"{base_url}/_raya/render/graph.js")

        assert 'data-raya-surface="graph"' in graph_html
        assert "raya-graph-data" in graph_html
        assert "https://" not in graph_html
        assert "http://" not in graph_html
        assert "cytoscape" not in graph_html.lower()
        assert "window.location.href" in graph_js
        for forbidden_runtime_token in (
            "fetch(",
            "XMLHttpRequest",
            "localStorage",
            "sessionStorage",
        ):
            assert forbidden_runtime_token not in graph_js

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                for viewport in (
                    {"width": 1280, "height": 900},
                    {"width": 1120, "height": 900},
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    requested_urls: list[str] = []
                    page.on(
                        "request", lambda request: requested_urls.append(request.url)
                    )
                    try:
                        page.goto(
                            f"{base_url}/_raya/graph/index.html",
                            wait_until="networkidle",
                        )
                        requested_urls.clear()
                        _assert_no_horizontal_overflow(page)
                        toolbar_box = page.locator(
                            ".raya-graph-toolbar"
                        ).bounding_box()
                        assert toolbar_box is not None
                        assert toolbar_box["x"] >= 0
                        assert (
                            toolbar_box["x"] + toolbar_box["width"]
                            <= viewport["width"] + 1
                        )
                        assert page.locator(".raya-discovery-command-bar").is_visible()
                        assert page.locator(
                            ".raya-discovery-command-bar .raya-command-home"
                        ).is_visible()
                        assert (
                            page.locator(
                                ".raya-graph-header .raya-course-title"
                            ).count()
                            == 0
                        )
                        assert (
                            page.locator(
                                ".raya-graph-header .raya-graph-back-link"
                            ).count()
                            == 0
                        )
                        if viewport["width"] < 520:
                            discovery_box = page.locator(
                                ".raya-discovery-command-bar"
                            ).bounding_box()
                            assert discovery_box is not None
                            assert discovery_box["height"] <= 150
                        assert (
                            page.locator(".raya-command-search")
                            .evaluate("node => node.href")
                            .endswith("/_raya/search/index.html")
                        )
                        assert page.locator(".raya-command-size").is_visible()
                        assert page.locator(".raya-command-font").is_visible()
                        assert page.locator(".raya-graph-legend").is_visible()
                        assert page.locator(".raya-graph-workspace").is_visible()
                        assert page.locator(".raya-graph-map-panel").is_visible()
                        assert page.locator(".raya-graph-list-panel").is_visible()
                        assert page.locator(".raya-graph-inspector-panel").is_visible()
                        assert (
                            page.locator("#graph-layout").input_value() == "connections"
                        )
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-layout"
                            )
                            == "connections"
                        )
                        root_x, _ = _graph_node_translate(page, "render-root")
                        static_x, _ = _graph_node_translate(page, "static-path")
                        math_x, _ = _graph_node_translate(page, "math-authoring")
                        reader_x, _ = _graph_node_translate(page, "reader-ux")
                        matrix_x, _ = _graph_node_translate(page, "authoring-matrix")
                        assert root_x < static_x
                        assert root_x < reader_x
                        assert root_x < matrix_x
                        assert math_x < matrix_x
                        canvas_height = _viewbox_values(
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                        )[3]
                        canvas_width = _viewbox_values(
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                        )[2]
                        graph_node_positions = page.locator(
                            "#raya-graph-canvas [data-raya-graph-node] g"
                        ).evaluate_all(
                            """nodes => nodes.map((node) => {
                              const match = node
                                .getAttribute('transform')
                                .match(/translate\\(([-0-9.]+)\\s+([-0-9.]+)\\)/);
                              return {
                                x: Number(match[1]),
                                y: Number(match[2]),
                              };
                            })"""
                        )
                        crowded_count = page.locator(
                            '#raya-graph-canvas [data-raya-graph-node^="crowded-"] g'
                        ).count()
                        assert crowded_count == 12
                        assert all(
                            30 <= position["x"] <= canvas_width - 30
                            for position in graph_node_positions
                        )
                        assert all(
                            30 <= position["y"] <= canvas_height - 30
                            for position in graph_node_positions
                        )
                        if viewport["width"] >= 1280:
                            graph_box = page.locator(
                                ".raya-graph-map-panel"
                            ).bounding_box()
                            list_box = page.locator(
                                ".raya-graph-list-panel"
                            ).bounding_box()
                            inspector_box = page.locator(
                                ".raya-graph-inspector-panel"
                            ).bounding_box()
                            assert graph_box is not None
                            assert list_box is not None
                            assert inspector_box is not None
                            assert graph_box["width"] > list_box["width"]
                            assert graph_box["width"] > inspector_box["width"]
                            list_panel_link = page.locator(
                                "#raya-graph-list [data-raya-graph-node] a"
                            ).first
                            assert list_panel_link.get_attribute("tabindex") is None
                            page.click('[data-raya-graph-toggle-panel="list"]')
                            assert (
                                page.locator("[data-raya-graph-page]").get_attribute(
                                    "data-raya-graph-list-state"
                                )
                                == "collapsed"
                            )
                            assert (
                                page.locator(
                                    "[data-raya-graph-panel-body='list']"
                                ).get_attribute("aria-hidden")
                                == "true"
                            )
                            assert (
                                page.locator(
                                    "#raya-graph-list [data-raya-graph-node]:visible a"
                                ).count()
                                == 0
                            )
                            assert list_panel_link.get_attribute("tabindex") == "-1"
                            page.click('[data-raya-graph-toggle-panel="list"]')
                            assert (
                                page.locator("[data-raya-graph-page]").get_attribute(
                                    "data-raya-graph-list-state"
                                )
                                == "expanded"
                            )
                            assert list_panel_link.get_attribute("tabindex") is None
                            inspector_summary = page.locator(
                                "[data-raya-graph-help] summary"
                            )
                            assert inspector_summary.get_attribute("tabindex") is None
                            page.click('[data-raya-graph-toggle-panel="inspector"]')
                            assert (
                                page.locator("[data-raya-graph-page]").get_attribute(
                                    "data-raya-graph-inspector-state"
                                )
                                == "collapsed"
                            )
                            assert (
                                page.locator(
                                    "[data-raya-graph-panel-body='inspector']"
                                ).get_attribute("aria-hidden")
                                == "true"
                            )
                            assert (
                                page.locator(
                                    "[data-raya-graph-help] summary:visible"
                                ).count()
                                == 0
                            )
                            assert inspector_summary.get_attribute("tabindex") == "-1"
                            page.click('[data-raya-graph-toggle-panel="inspector"]')
                            assert (
                                page.locator("[data-raya-graph-page]").get_attribute(
                                    "data-raya-graph-inspector-state"
                                )
                                == "expanded"
                            )
                            assert inspector_summary.get_attribute("tabindex") is None
                        assert page.locator(
                            "[data-raya-graph-legend='node']"
                        ).is_visible()
                        assert page.locator(
                            "[data-raya-graph-legend='match']"
                        ).is_visible()
                        assert page.locator(
                            "[data-raya-graph-legend='selected']"
                        ).is_visible()
                        for legend_key in (
                            "edge-navigation",
                            "edge-content",
                            "edge-prerequisite",
                            "edge-parent",
                        ):
                            assert page.locator(
                                f"[data-raya-graph-legend='{legend_key}']"
                            ).is_visible()
                        for kind in (
                            "navigation",
                            "content",
                            "prerequisite",
                            "parent",
                        ):
                            button = page.locator(
                                f'[data-raya-graph-edge-kind-filter="{kind}"]'
                            )
                            assert button.is_visible()
                            assert button.get_attribute("aria-pressed") == "true"
                        assert page.locator("[data-raya-graph-help]").is_visible()
                        assert (
                            page.locator("[data-raya-graph-help]").get_attribute("open")
                            is None
                        )
                        page.locator("[data-raya-graph-help] summary").click()
                        assert (
                            "Search"
                            in page.locator("[data-raya-graph-help]").inner_text()
                        )
                        assert (
                            page.locator("#raya-graph-canvas .raya-graph-node").count()
                            > 0
                        )
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
                        assert "match" in page.locator("#graph-status").inner_text()
                        assert (
                            "2 match(es), 3 connected page(s) shown"
                            in page.locator("#graph-status").inner_text()
                        )
                        after = page.locator(
                            "#raya-graph-list [data-raya-graph-node]:visible"
                        ).count()
                        assert after < before
                        assert (
                            "matrix"
                            in page.locator("#raya-graph-list").inner_text().lower()
                        )
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-graph-list [data-raya-graph-node].is-active-result')
                              ?.getAttribute('data-raya-graph-node')"""
                        )
                        first_active = page.locator(
                            "#raya-graph-list [data-raya-graph-node].is-active-result"
                        ).get_attribute("data-raya-graph-node")
                        assert first_active
                        assert (
                            page.locator(
                                f'#raya-graph-list [data-raya-graph-node="{first_active}"] a'
                            ).get_attribute("aria-current")
                            == "true"
                        )
                        assert page.locator(
                            "[data-raya-graph-detail-panel]"
                        ).is_visible()
                        page.wait_for_function(
                            f"""() => document
                              .querySelector('#raya-graph-canvas [data-raya-graph-node="{first_active}"] g')
                              ?.classList
                              ?.contains('is-inspected')"""
                        )
                        assert page.locator(
                            f'#raya-graph-canvas [data-raya-graph-node="{first_active}"] g'
                        ).evaluate("node => node.classList.contains('is-inspected')")
                        page.press("#graph-search", "ArrowDown")
                        second_active = page.locator(
                            "#raya-graph-list [data-raya-graph-node].is-active-result"
                        ).get_attribute("data-raya-graph-node")
                        assert second_active
                        assert second_active != first_active
                        page.press("#graph-search", "ArrowDown")
                        assert (
                            page.locator(
                                "#raya-graph-list [data-raya-graph-node].is-active-result"
                            ).get_attribute("data-raya-graph-node")
                            == first_active
                        )
                        page.press("#graph-search", "ArrowUp")
                        assert (
                            page.locator(
                                "#raya-graph-list [data-raya-graph-node].is-active-result"
                            ).get_attribute("data-raya-graph-node")
                            == second_active
                        )
                        page.press("#graph-search", "ArrowUp")
                        assert (
                            page.locator(
                                "#raya-graph-list [data-raya-graph-node].is-active-result"
                            ).get_attribute("data-raya-graph-node")
                            == first_active
                        )
                        page.locator(
                            f'#raya-graph-list [data-raya-graph-node="{second_active}"] a'
                        ).focus()
                        page.wait_for_function(
                            f"""() => document
                              .querySelector('#raya-graph-canvas [data-raya-graph-node="{second_active}"] g')
                              ?.classList
                              ?.contains('is-inspected')"""
                        )
                        page.locator("#graph-search").focus()
                        page.wait_for_function(
                            f"""() => document
                              .querySelector('#raya-graph-canvas [data-raya-graph-node="{first_active}"] g')
                              ?.classList
                              ?.contains('is-inspected')"""
                        )
                        page.fill("#graph-search", "matrx")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#graph-status')
                              ?.textContent
                              ?.includes('visible node')"""
                        )
                        assert (
                            "matrix"
                            in page.locator("#raya-graph-list").inner_text().lower()
                        )
                        assert page.locator(
                            "#raya-graph-list [data-raya-graph-node].is-active-result"
                        ).count()
                        page.fill("#graph-search", "")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#graph-status')
                              ?.textContent
                              ?.includes('visible node')"""
                        )
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
                        edge_color = page.locator(
                            "#raya-graph-canvas .raya-graph-edge"
                        ).first.evaluate(
                            "node => node.style.getPropertyValue('--raya-graph-edge-color')"
                        )
                        assert edge_color.startswith("var(--raya-graph-group-")
                        for from_id, to_id, kind in (
                            ("render-root", "static-path", "navigation"),
                            ("render-root", "authoring-matrix", "content"),
                            ("reader-ux", "render-root", "prerequisite"),
                            ("static-path", "render-root", "parent"),
                        ):
                            edge = page.locator(
                                "#raya-graph-canvas "
                                f'.raya-graph-edge[data-raya-graph-from="{from_id}"]'
                                f'[data-raya-graph-to="{to_id}"]'
                                f'[data-raya-graph-kind="{kind}"]'
                            )
                            assert edge.count() >= 1
                            assert edge.first.evaluate(
                                "(node, kind) => node.classList.contains("
                                "`raya-graph-edge-kind-${kind}`)",
                                kind,
                            )
                            computed = edge.first.evaluate(
                                """node => {
                                  const style = window.getComputedStyle(node);
                                  return {
                                    color: node.style.getPropertyValue('--raya-graph-edge-color'),
                                    dash: style.strokeDasharray,
                                    opacity: style.strokeOpacity,
                                    width: style.strokeWidth,
                                  };
                                }"""
                            )
                            assert computed["color"].startswith(
                                "var(--raya-graph-group-"
                            )
                            marker_end = edge.first.get_attribute("marker-end")
                            assert marker_end is not None
                            assert marker_end.startswith("url(#raya-graph-arrow-")
                            marker_id = marker_end.removeprefix(
                                "url(#"
                            ).removesuffix(")")
                            marker = page.locator(f"#{marker_id}")
                            assert marker.count() == 1
                            assert marker.evaluate(
                                "node => node.classList.contains('raya-graph-arrow-marker')"
                            )
                            marker_path_style = marker.locator("path").evaluate(
                                "node => node.style.getPropertyValue('--raya-graph-edge-color')"
                            )
                            assert marker_path_style == computed["color"]
                            points = edge.first.evaluate(
                                """node => ({
                                  x1: Number(node.getAttribute('x1')),
                                  y1: Number(node.getAttribute('y1')),
                                  x2: Number(node.getAttribute('x2')),
                                  y2: Number(node.getAttribute('y2')),
                                })"""
                            )
                            target = _graph_node_translate(page, to_id)
                            target_distance = (
                                (target[0] - points["x2"]) ** 2
                                + (target[1] - points["y2"]) ** 2
                            ) ** 0.5
                            assert target_distance >= 18
                            assert marker.evaluate(
                                "(marker, kind) => marker.classList.contains("
                                "`raya-graph-edge-kind-${kind}`)",
                                kind,
                            )
                            if kind == "navigation":
                                assert computed["dash"] in ("none", "")
                            else:
                                assert computed["dash"] not in ("none", "")
                            if kind == "prerequisite":
                                assert float(computed["width"].replace("px", "")) > 2
                            if kind == "parent":
                                assert float(computed["opacity"]) < 0.58
                        navigation_edge = page.locator(
                            "#raya-graph-canvas "
                            '.raya-graph-edge[data-raya-graph-from="render-root"]'
                            '[data-raya-graph-to="static-path"]'
                            '[data-raya-graph-kind="navigation"]'
                        ).first
                        parent_edge = page.locator(
                            "#raya-graph-canvas "
                            '.raya-graph-edge[data-raya-graph-from="static-path"]'
                            '[data-raya-graph-to="render-root"]'
                            '[data-raya-graph-kind="parent"]'
                        ).first
                        reciprocal_points = page.evaluate(
                            """([navigation, parent]) => {
                              const attrs = (node) => ({
                                x1: Number(node.getAttribute('x1')),
                                y1: Number(node.getAttribute('y1')),
                                x2: Number(node.getAttribute('x2')),
                                y2: Number(node.getAttribute('y2')),
                              });
                              return { navigation: attrs(navigation), parent: attrs(parent) };
                            }""",
                            [navigation_edge.element_handle(), parent_edge.element_handle()],
                        )
                        assert not (
                            abs(
                                reciprocal_points["navigation"]["x1"]
                                - reciprocal_points["parent"]["x2"]
                            )
                            < 0.01
                            and abs(
                                reciprocal_points["navigation"]["y1"]
                                - reciprocal_points["parent"]["y2"]
                            )
                            < 0.01
                            and abs(
                                reciprocal_points["navigation"]["x2"]
                                - reciprocal_points["parent"]["x1"]
                            )
                            < 0.01
                            and abs(
                                reciprocal_points["navigation"]["y2"]
                                - reciprocal_points["parent"]["y1"]
                            )
                            < 0.01
                        )
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-graph-canvas .raya-graph-edge.is-inspected') !== null"""
                        )
                        assert (
                            page.locator(
                                "#raya-graph-canvas .raya-graph-edge.is-dimmed"
                            ).count()
                            > 0
                        )
                        dimmed_edge = page.locator(
                            "#raya-graph-canvas .raya-graph-edge.is-dimmed"
                        ).first
                        dimmed_marker_id = dimmed_edge.get_attribute(
                            "marker-end"
                        ).removeprefix("url(#").removesuffix(")")
                        assert page.locator(f"#{dimmed_marker_id}").evaluate(
                            "node => node.classList.contains('is-dimmed')"
                        )
                        inspected_edge = page.locator(
                            "#raya-graph-canvas .raya-graph-edge.is-inspected"
                        ).first
                        inspected_marker_id = inspected_edge.get_attribute(
                            "marker-end"
                        ).removeprefix("url(#").removesuffix(")")
                        assert page.locator(f"#{inspected_marker_id}").evaluate(
                            "node => node.classList.contains('is-inspected')"
                        )
                        content_filter = page.locator(
                            '[data-raya-graph-edge-kind-filter="content"]'
                        )
                        content_edges = page.locator(
                            "#raya-graph-canvas "
                            '.raya-graph-edge[data-raya-graph-kind="content"]'
                        )
                        content_count = content_edges.count()
                        assert content_count >= 1
                        node_count_before_filter = page.locator(
                            "#raya-graph-canvas [data-raya-graph-node]"
                        ).count()
                        pre_filter_viewbox = page.locator(
                            "#raya-graph-canvas"
                        ).get_attribute("viewBox")
                        page.click("#graph-zoom-in")
                        filter_zoomed_viewbox = page.locator(
                            "#raya-graph-canvas"
                        ).get_attribute("viewBox")
                        assert filter_zoomed_viewbox != pre_filter_viewbox
                        content_filter.click()
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-edge-kind-filter="content"]')
                              ?.getAttribute('aria-pressed') === 'false'"""
                        )
                        assert (
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                            == filter_zoomed_viewbox
                        )
                        assert content_edges.count() == 0
                        assert (
                            page.locator(
                                "#raya-graph-canvas [data-raya-graph-node]"
                            ).count()
                            == node_count_before_filter
                        )
                        assert (
                            "1 edge kind hidden"
                            in page.locator("#graph-status").inner_text()
                        )
                        assert page.locator(
                            "#raya-graph-canvas .raya-graph-arrow-marker"
                        ).count() == page.locator(
                            "#raya-graph-canvas .raya-graph-edge"
                        ).count()
                        page.click("#graph-reset")
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-edge-kind-filter="content"]')
                              ?.getAttribute('aria-pressed') === 'true'"""
                        )
                        assert page.locator(
                            "#raya-graph-canvas "
                            '.raya-graph-edge[data-raya-graph-kind="content"]'
                        ).count() == content_count
                        for toggle_kind in (
                            "navigation",
                            "prerequisite",
                            "parent",
                        ):
                            kind_filter = page.locator(
                                f'[data-raya-graph-edge-kind-filter="{toggle_kind}"]'
                            )
                            kind_edges = page.locator(
                                "#raya-graph-canvas "
                                f'.raya-graph-edge[data-raya-graph-kind="{toggle_kind}"]'
                            )
                            kind_count = kind_edges.count()
                            assert kind_count >= 1
                            kind_filter.click()
                            page.wait_for_function(
                                """(kind) => document
                                  .querySelector(
                                    `[data-raya-graph-edge-kind-filter="${kind}"]`
                                  )
                                  ?.getAttribute('aria-pressed') === 'false'""",
                                arg=toggle_kind,
                            )
                            assert kind_edges.count() == 0
                            kind_filter.click()
                            page.wait_for_function(
                                """(kind) => document
                                  .querySelector(
                                    `[data-raya-graph-edge-kind-filter="${kind}"]`
                                  )
                                  ?.getAttribute('aria-pressed') === 'true'""",
                                arg=toggle_kind,
                            )
                            assert page.locator(
                                "#raya-graph-canvas "
                                f'.raya-graph-edge[data-raya-graph-kind="{toggle_kind}"]'
                            ).count() == kind_count
                        page.locator(
                            '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
                        ).hover()
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-graph-canvas .raya-graph-node.is-dimmed') !== null"""
                        )
                        assert (
                            page.locator(
                                "#raya-graph-canvas .raya-graph-node.is-dimmed"
                            ).count()
                            > 0
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
                            '#raya-graph-list [data-raya-graph-node="static-path"] a'
                        ).focus()
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-hover-status]')
                              ?.textContent
                              ?.includes('Static Path')"""
                        )
                        assert (
                            page.locator(
                                "#raya-graph-canvas .raya-graph-node.is-dimmed"
                            ).count()
                            > 0
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
                        assert page.locator(
                            "[data-raya-graph-detail-empty]"
                        ).is_visible()
                        assert page.locator(
                            "[data-raya-graph-detail-panel]"
                        ).is_hidden()
                        assert page.locator("#graph-fit-selection").is_disabled()
                        graph_node.click()
                        page.wait_for_selector(
                            "[data-raya-graph-detail-panel]:not([hidden])"
                        )
                        initial_viewbox = page.locator(
                            "#raya-graph-canvas"
                        ).get_attribute("viewBox")
                        initial_viewbox_values = _viewbox_values(initial_viewbox)
                        assert initial_viewbox_values[2] > 0
                        assert initial_viewbox_values[3] > 0
                        assert page.get_by_role(
                            "button", name="Zoom in graph"
                        ).is_visible()
                        assert page.get_by_role(
                            "button", name="Zoom out graph"
                        ).is_visible()
                        assert page.get_by_role(
                            "button", name="Reset graph view"
                        ).is_visible()
                        page.locator(
                            '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
                        ).click()
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-state-selected]')
                              ?.textContent
                              ?.includes('authoring-matrix')"""
                        )
                        initial_viewbox = page.locator(
                            "#raya-graph-canvas"
                        ).get_attribute("viewBox")
                        fit_selection = page.locator("#graph-fit-selection")
                        assert fit_selection.is_enabled()
                        page.click("#graph-zoom-in")
                        page.click('[data-raya-graph-pan="right"]')
                        drifted_viewbox = page.locator(
                            "#raya-graph-canvas"
                        ).get_attribute("viewBox")
                        fit_selection.click()
                        fitted_viewbox = page.locator(
                            "#raya-graph-canvas"
                        ).get_attribute("viewBox")
                        assert fitted_viewbox != initial_viewbox
                        assert fitted_viewbox != drifted_viewbox
                        assert _viewbox_width(fitted_viewbox) < _viewbox_width(
                            initial_viewbox
                        )
                        context = _visible_graph_context(
                            page, "authoring-matrix", viewport
                        )
                        assert context["selectedVisible"]
                        assert context["activeEdgeVisible"]
                        assert page.input_value("#graph-search") == ""
                        assert page.locator(
                            "[data-raya-graph-detail-panel]"
                        ).is_visible()
                        page.click("#graph-fit")
                        assert (
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                            == initial_viewbox
                        )
                        page.click("#graph-zoom-in")
                        zoomed_viewbox = page.locator(
                            "#raya-graph-canvas"
                        ).get_attribute("viewBox")
                        assert zoomed_viewbox != initial_viewbox
                        assert _viewbox_width(zoomed_viewbox) < _viewbox_width(
                            initial_viewbox
                        )
                        page.click("#graph-zoom-out")
                        zoomed_out_viewbox = page.locator(
                            "#raya-graph-canvas"
                        ).get_attribute("viewBox")
                        assert _viewbox_width(zoomed_out_viewbox) > _viewbox_width(
                            zoomed_viewbox
                        )
                        page.click("#graph-fit")
                        assert (
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                            == initial_viewbox
                        )
                        page.click("#graph-zoom-in")
                        assert _viewbox_width(
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                        ) < _viewbox_width(initial_viewbox)
                        page.fill("#graph-search", "matrx")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#graph-status')
                              ?.textContent
                              ?.includes('visible node')"""
                        )
                        assert (
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                            == initial_viewbox
                        )
                        page.click("#graph-zoom-in")
                        assert _viewbox_width(
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                        ) < _viewbox_width(initial_viewbox)
                        page.click("#graph-reset-view")
                        assert (
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                            == initial_viewbox
                        )
                        assert page.input_value("#graph-search") == "matrx"
                        assert page.locator(
                            "[data-raya-graph-detail-panel]"
                        ).is_visible()
                        before_key_pan = _viewbox_values(
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                        )
                        page.locator("#raya-graph-canvas").focus()
                        page.keyboard.press("ArrowRight")
                        after_key_pan = _viewbox_values(
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                        )
                        assert after_key_pan[0] > before_key_pan[0]
                        assert page.input_value("#graph-search") == "matrx"
                        assert page.locator(
                            "[data-raya-graph-detail-panel]"
                        ).is_visible()
                        page.click('[data-raya-graph-pan="left"]')
                        after_button_pan = _viewbox_values(
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                        )
                        assert after_button_pan[0] < after_key_pan[0]
                        canvas_box = page.locator("#raya-graph-canvas").bounding_box()
                        assert canvas_box is not None
                        before_drag_pan = _viewbox_values(
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                        )
                        page.locator("#raya-graph-canvas").dispatch_event(
                            "mousedown",
                            {
                                "button": 0,
                                "clientX": canvas_box["x"] + canvas_box["width"] * 0.08,
                                "clientY": canvas_box["y"]
                                + canvas_box["height"] * 0.08,
                            },
                        )
                        page.locator("#raya-graph-canvas").dispatch_event(
                            "mousemove",
                            {
                                "clientX": canvas_box["x"] + canvas_box["width"] * 0.02,
                                "clientY": canvas_box["y"]
                                + canvas_box["height"] * 0.08,
                            },
                        )
                        page.locator("#raya-graph-canvas").dispatch_event(
                            "mouseup",
                            {
                                "clientX": canvas_box["x"] + canvas_box["width"] * 0.02,
                                "clientY": canvas_box["y"]
                                + canvas_box["height"] * 0.08,
                            },
                        )
                        after_drag_pan = _viewbox_values(
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                        )
                        assert after_drag_pan[0] > before_drag_pan[0]
                        assert page.input_value("#graph-search") == "matrx"
                        assert page.locator(
                            "[data-raya-graph-detail-panel]"
                        ).is_visible()
                        assert (
                            page.locator("[data-raya-graph-detail-title]")
                            .inner_text()
                            .strip()
                        )
                        assert page.locator(
                            "[data-raya-graph-detail-link]"
                        ).get_attribute("href")
                        sequence_labels = page.locator(
                            "[data-raya-graph-detail-sequence] a"
                        ).evaluate_all(
                            "nodes => nodes.map((node) => node.textContent.trim())"
                        )
                        assert sequence_labels == [
                            "Previous: Projection Residuals",
                            "Selected: Authoring Matrix Fixture",
                            "Next: Crowded Page 6",
                        ]
                        assert page.locator(
                            "[data-raya-graph-detail-next]"
                        ).is_visible()
                        assert page.locator(
                            "[data-raya-graph-detail-tasks-link]"
                        ).get_attribute("href") == "../tasks/index.html?page=authoring-matrix"
                        assert page.locator(
                            "[data-raya-graph-detail-schedule-link]"
                        ).get_attribute("href") == "../schedule/index.html?page=authoring-matrix"
                        study_objects = page.locator(
                            "[data-raya-graph-detail-study-objects]"
                        )
                        assert study_objects.is_visible()
                        assert study_objects.locator(
                            "a", has_text="Matrix graph check"
                        ).is_visible()
                        assert study_objects.locator(
                            "text=Assignment · Due 2026-11-03"
                        ).is_visible()
                        assert study_objects.locator(
                            "text=Trace the graph context for matrix notation."
                        ).is_visible()
                        assert study_objects.locator(
                            "a", has_text="Matrix graph check"
                        ).evaluate("node => node.href").endswith(
                            "/authoring-matrix/index.html"
                            "#raya-official-matrix-assignment"
                        )
                        page.fill("#graph-search", "matrix graph check")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#graph-status')
                              ?.textContent
                              ?.includes('match')"""
                        )
                        assert page.locator(
                            "#raya-graph-list "
                            "[data-raya-graph-node='authoring-matrix']"
                        ).is_visible()
                        assert page.locator(
                            "[data-raya-graph-detail-empty]"
                        ).is_hidden()
                        outgoing_or_incoming = (
                            page.locator("[data-raya-graph-detail-outgoing] li").count()
                            + page.locator(
                                "[data-raya-graph-detail-incoming] li"
                            ).count()
                        )
                        assert outgoing_or_incoming >= 1
                        page.fill("#graph-search", "zz-no-result")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#graph-status')
                              ?.textContent
                              ?.startsWith('0 match')"""
                        )
                        assert page.locator(
                            "[data-raya-graph-detail-empty]"
                        ).is_visible()
                        assert page.locator(
                            "[data-raya-graph-detail-panel]"
                        ).is_hidden()
                        before_no_result_url = page.url
                        page.press("#graph-search", "Enter")
                        assert page.url == before_no_result_url
                        page.fill("#graph-search", "matrx")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#graph-status')
                              ?.textContent
                              ?.includes('visible node')"""
                        )
                        page.fill("#graph-search", "matrix")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-graph-canvas [data-raya-graph-node="authoring-matrix"] g')
                              ?.classList
                              ?.contains('is-match')"""
                        )
                        assert page.locator(
                            '#raya-graph-canvas [data-raya-graph-node="render-root"] g'
                        ).evaluate(
                            "node => node.classList.contains('is-search-context')"
                        )
                        page.locator(
                            '#raya-graph-canvas [data-raya-graph-node="render-root"]'
                        ).dispatch_event("focus")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-graph-canvas [data-raya-graph-node="render-root"] g')
                              ?.classList
                              ?.contains('is-inspected')"""
                        )
                        assert not page.locator(
                            '#raya-graph-canvas [data-raya-graph-node="render-root"] g'
                        ).evaluate(
                            "node => node.classList.contains('is-search-context')"
                        )
                        assert page.locator(
                            '#raya-graph-canvas [data-raya-graph-node="static-path"] g'
                        ).evaluate(
                            "node => node.classList.contains('is-search-dimmed')"
                        )
                        assert page.locator(
                            '#raya-graph-canvas .raya-graph-edge[data-raya-graph-from="render-root"][data-raya-graph-to="authoring-matrix"]'
                        ).first.evaluate(
                            "edge => edge.classList.contains('is-search-context')"
                        )
                        assert (
                            page.locator(
                                "#raya-graph-canvas .raya-graph-edge.is-search-dimmed"
                            ).count()
                            > 0
                        )
                        page.goto(graph_url, wait_until="networkidle")
                        page.fill("#graph-search", "matrix")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-graph-list [data-raya-graph-node].is-active-result a')"""
                        )
                        target_href = page.locator(
                            "#raya-graph-list [data-raya-graph-node].is-active-result a"
                        ).evaluate("node => node.href")
                        page.press("#graph-search", "Enter")
                        page.wait_for_url(target_href)
                        page.goto(graph_url, wait_until="networkidle")
                        page.fill("#graph-search", "matrix")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-graph-canvas [data-raya-graph-node="authoring-matrix"] g')
                              ?.classList
                              ?.contains('is-match')"""
                        )
                        requested_urls.clear()
                        page.locator(
                            '#raya-graph-canvas [data-raya-graph-node="static-path"]'
                        ).dispatch_event("focus")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-graph-canvas [data-raya-graph-node="static-path"] g')
                              ?.classList
                              ?.contains('is-inspected')"""
                        )
                        assert not page.locator(
                            '#raya-graph-canvas [data-raya-graph-node="static-path"] g'
                        ).evaluate(
                            "node => node.classList.contains('is-search-dimmed')"
                        )
                        assert not page.locator(
                            "#raya-graph-canvas .raya-graph-edge.is-inspected"
                        ).first.evaluate(
                            "edge => edge.classList.contains('is-search-dimmed')"
                        )
                        page.click("#graph-reset")
                        assert (
                            page.locator(
                                "#raya-graph-canvas .raya-graph-node.is-search-dimmed"
                            ).count()
                            == 0
                        )
                        assert (
                            page.locator(
                                "#raya-graph-canvas .raya-graph-edge.is-search-dimmed"
                            ).count()
                            == 0
                        )
                        page.fill("#graph-search", "matrx")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#graph-status')
                              ?.textContent
                              ?.includes('visible node')"""
                        )
                        page.locator(
                            "#raya-graph-canvas [data-raya-graph-node]"
                        ).first.click()
                        page.wait_for_selector(
                            "[data-raya-graph-detail-panel]:not([hidden])"
                        )
                        page.locator(
                            '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
                        ).click()
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-state-selected]')
                              ?.textContent
                              ?.includes('authoring-matrix')"""
                        )
                        before_width = page.locator(
                            "#raya-graph-canvas"
                        ).bounding_box()["width"]
                        page.click("#graph-expand")
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-expanded"
                            )
                            == "true"
                        )
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-list-state"
                            )
                            == "collapsed"
                        )
                        assert (
                            page.locator(
                                "[data-raya-graph-panel-body='list']"
                            ).get_attribute("aria-hidden")
                            == "true"
                        )
                        assert (
                            page.locator(
                                "#raya-graph-list [data-raya-graph-node] a"
                            ).first.get_attribute("tabindex")
                            == "-1"
                        )
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-inspector-state"
                            )
                            == "collapsed"
                        )
                        assert (
                            page.locator(
                                "[data-raya-graph-panel-body='inspector']"
                            ).get_attribute("aria-hidden")
                            == "true"
                        )
                        assert (
                            page.locator(
                                "[data-raya-graph-detail-clear]"
                            ).get_attribute("tabindex")
                            == "-1"
                        )
                        assert page.input_value("#graph-search") == "matrx"
                        assert (
                            "authoring-matrix"
                            in page.locator(
                                "[data-raya-graph-state-selected]"
                            ).inner_text()
                        )
                        after_width = page.locator("#raya-graph-canvas").bounding_box()[
                            "width"
                        ]
                        if viewport["width"] >= 1280:
                            assert after_width > before_width
                            assert page.locator("#raya-graph-canvas").is_visible()
                            page.click('[data-raya-graph-toggle-panel="list"]')
                            assert (
                                page.locator("[data-raya-graph-page]").get_attribute(
                                    "data-raya-graph-expanded"
                                )
                                == "false"
                            )
                            assert (
                                page.locator("[data-raya-graph-page]").get_attribute(
                                    "data-raya-graph-list-state"
                                )
                                == "expanded"
                            )
                            assert (
                                page.locator(
                                    "[data-raya-graph-panel-body='list']"
                                ).get_attribute("aria-hidden")
                                == "false"
                            )
                            assert (
                                page.locator(
                                    "#raya-graph-list [data-raya-graph-node] a"
                                ).first.get_attribute("tabindex")
                                is None
                            )
                            assert (
                                page.locator("[data-raya-graph-page]").get_attribute(
                                    "data-raya-graph-inspector-state"
                                )
                                == "collapsed"
                            )
                            page.click("#graph-expand")
                            assert (
                                page.locator("[data-raya-graph-page]").get_attribute(
                                    "data-raya-graph-expanded"
                                )
                                == "true"
                            )
                            page.click('[data-raya-graph-toggle-panel="inspector"]')
                            assert (
                                page.locator("[data-raya-graph-page]").get_attribute(
                                    "data-raya-graph-expanded"
                                )
                                == "false"
                            )
                            assert (
                                page.locator("[data-raya-graph-page]").get_attribute(
                                    "data-raya-graph-inspector-state"
                                )
                                == "expanded"
                            )
                            assert (
                                page.locator(
                                    "[data-raya-graph-panel-body='inspector']"
                                ).get_attribute("aria-hidden")
                                == "false"
                            )
                            assert (
                                page.locator(
                                    "[data-raya-graph-detail-clear]"
                                ).get_attribute("tabindex")
                                is None
                            )
                            assert (
                                page.locator("[data-raya-graph-page]").get_attribute(
                                    "data-raya-graph-list-state"
                                )
                                == "collapsed"
                            )
                            page.click("#graph-expand")
                            assert (
                                page.locator("[data-raya-graph-page]").get_attribute(
                                    "data-raya-graph-expanded"
                                )
                                == "true"
                            )
                        page.click("#graph-expand")
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-expanded"
                            )
                            == "false"
                        )
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-list-state"
                            )
                            == "expanded"
                        )
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-inspector-state"
                            )
                            == "expanded"
                        )
                        assert (
                            page.locator(
                                "[data-raya-graph-panel-body='inspector']"
                            ).get_attribute("aria-hidden")
                            == "false"
                        )
                        assert (
                            page.locator(
                                "[data-raya-graph-detail-clear]"
                            ).get_attribute("tabindex")
                            is None
                        )
                        page.click("[data-raya-graph-detail-clear]")
                        assert page.locator(
                            "[data-raya-graph-detail-empty]"
                        ).is_visible()
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
                        assert page.locator("#graph-zoom-in").is_disabled()
                        assert page.locator("#graph-zoom-out").is_disabled()
                        assert page.locator("#graph-reset-view").is_disabled()
                        assert page.locator("#graph-fit-selection").is_disabled()
                        page.fill("#graph-search", "")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#graph-status')
                              ?.textContent
                              ?.includes('visible node')"""
                        )
                        page.select_option("#graph-layout", "cluster")
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-layout"
                            )
                            == "cluster"
                        )
                        cluster_root = _graph_node_translate(page, "render-root")
                        cluster_static = _graph_node_translate(page, "static-path")
                        cluster_math_root = _graph_node_translate(
                            page, "math-authoring"
                        )
                        cluster_math_a = _graph_node_translate(page, "cluster-math-1")
                        cluster_math_b = _graph_node_translate(page, "cluster-math-2")
                        assert cluster_static[0] > cluster_root[0]
                        assert cluster_static[1] > cluster_root[1]
                        assert cluster_math_root[1] < cluster_math_a[1]
                        assert cluster_math_root[1] < cluster_math_b[1]
                        assert cluster_math_a[0] > cluster_math_b[0]
                        assert _point_distance(
                            cluster_math_a, cluster_math_b
                        ) < _point_distance(cluster_math_a, cluster_static)
                        cluster_canvas_height = _viewbox_values(
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                        )[3]
                        cluster_canvas_width = _viewbox_values(
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                        )[2]
                        cluster_node_positions = page.locator(
                            "#raya-graph-canvas [data-raya-graph-node] g"
                        ).evaluate_all(
                            """nodes => nodes.map((node) => {
                              const match = node
                                .getAttribute('transform')
                                .match(/translate\\(([-0-9.]+)\\s+([-0-9.]+)\\)/);
                              return {
                                x: Number(match[1]),
                                y: Number(match[2]),
                              };
                            })"""
                        )
                        assert all(
                            30 <= position["x"] <= cluster_canvas_width - 30
                            for position in cluster_node_positions
                        )
                        assert all(
                            30 <= position["y"] <= cluster_canvas_height - 30
                            for position in cluster_node_positions
                        )
                        page.select_option("#graph-layout", "topology")
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-layout"
                            )
                            == "topology"
                        )
                        topology_root = _graph_node_translate(page, "render-root")
                        topology_matrix = _graph_node_translate(
                            page, "authoring-matrix"
                        )
                        topology_static = _graph_node_translate(page, "static-path")
                        topology_reader = _graph_node_translate(page, "reader-ux")
                        assert _point_distance(
                            topology_root, topology_matrix
                        ) < _point_distance(topology_static, topology_reader)
                        topology_viewbox = _viewbox_values(
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                        )
                        topology_node_positions = page.locator(
                            "#raya-graph-canvas [data-raya-graph-node] g"
                        ).evaluate_all(
                            """nodes => nodes.map((node) => {
                              const match = node
                                .getAttribute('transform')
                                .match(/translate\\(([-0-9.]+)\\s+([-0-9.]+)\\)/);
                              return {
                                x: Number(match[1]),
                                y: Number(match[2]),
                              };
                            })"""
                        )
                        assert all(
                            30 <= position["x"] <= topology_viewbox[2] - 30
                            for position in topology_node_positions
                        )
                        assert all(
                            30 <= position["y"] <= topology_viewbox[3] - 30
                            for position in topology_node_positions
                        )
                        before_filter_position = _graph_node_translate(
                            page, "authoring-matrix"
                        )
                        page.locator(
                            '[data-raya-graph-edge-kind-filter="content"]'
                        ).click()
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-edge-kind-filter="content"]')
                              ?.getAttribute('aria-pressed') === 'false'"""
                        )
                        after_filter_position = _graph_node_translate(
                            page, "authoring-matrix"
                        )
                        assert after_filter_position != before_filter_position
                        page.locator(
                            '[data-raya-graph-edge-kind-filter="content"]'
                        ).click()
                        page.select_option("#graph-layout", "map")
                        page.select_option("#graph-layout", "connections")
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-layout"
                            )
                            == "connections"
                        )
                        page.select_option("#graph-layout", "map")
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-layout"
                            )
                            == "map"
                        )
                        assert page.locator("#graph-zoom-in").is_enabled()
                        assert page.locator("#graph-zoom-out").is_enabled()
                        assert page.locator("#graph-reset-view").is_enabled()
                        page.click("#graph-zoom-in")
                        assert _viewbox_width(
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                        ) < _viewbox_width(initial_viewbox)
                        group_filter = page.locator(
                            "[data-raya-graph-group-filter]"
                        ).first
                        group_filter.click()
                        assert group_filter.get_attribute("aria-pressed") == "false"
                        page.click("#graph-reset")
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-layout"
                            )
                            == "connections"
                        )
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-expanded"
                            )
                            == "false"
                        )
                        assert page.locator(
                            "[data-raya-graph-detail-empty]"
                        ).is_visible()
                        assert page.input_value("#graph-search") == ""
                        assert (
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                            == initial_viewbox
                        )
                        assert (
                            page.locator(
                                "#raya-graph-canvas .raya-graph-edge.is-dimmed"
                            ).count()
                            == 0
                        )
                        assert (
                            page.locator(
                                "#raya-graph-canvas .raya-graph-node.is-dimmed"
                            ).count()
                            == 0
                        )
                        assert (
                            page.locator("[data-raya-graph-hover-status]")
                            .inner_text()
                            .strip()
                            == ""
                        )
                        assert all(
                            value == "true"
                            for value in page.locator(
                                "[data-raya-graph-group-filter]"
                            ).evaluate_all(
                                "buttons => buttons.map((button) => button.getAttribute('aria-pressed'))"
                            )
                        )
                        assert requested_urls == []
                        first_list_link = page.locator(
                            "#raya-graph-list [data-raya-graph-node]:visible a"
                        ).first
                        list_href = first_list_link.evaluate("node => node.href")
                        with page.expect_navigation():
                            first_list_link.click()
                        assert page.url == list_href
                        page.goto(
                            f"{base_url}/_raya/graph/index.html",
                            wait_until="networkidle",
                        )
                        graph_path_before_selection = page.evaluate(
                            "() => window.location.pathname"
                        )
                        first_graph_node = page.locator(
                            "#raya-graph-canvas .raya-graph-node-link"
                        ).first
                        first_graph_node.click()
                        page.wait_for_selector(
                            "[data-raya-graph-detail-panel]:not([hidden])"
                        )
                        assert (
                            page.evaluate("() => window.location.pathname")
                            == graph_path_before_selection
                        )
                        assert page.locator(
                            ".raya-graph-detail-open-primary"
                        ).is_visible()
                        assert (
                            page.locator(
                                "[data-raya-graph-detail-link]"
                            ).inner_text()
                            == "Open selected page"
                        )
                        detail_href = page.locator(
                            "[data-raya-graph-detail-link]"
                        ).evaluate("node => node.href")
                        with page.expect_navigation():
                            page.click("[data-raya-graph-detail-link]")
                        assert page.url == detail_href
                        page.goto(
                            f"{base_url}/_raya/graph/index.html",
                            wait_until="networkidle",
                        )
                        graph_href = page.locator(
                            "#raya-graph-canvas [data-raya-graph-node]"
                        ).first.evaluate(
                            "node => new URL(node.getAttribute('href'), document.baseURI).href"
                        )
                        with page.expect_navigation():
                            page.locator(
                                "#raya-graph-canvas .raya-graph-node-link"
                            ).first.dblclick()
                        assert page.url == graph_href
                        page.goto(
                            f"{base_url}/_raya/graph/index.html",
                            wait_until="networkidle",
                        )
                        keyboard_node = page.locator(
                            '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
                        )
                        keyboard_href = keyboard_node.evaluate(
                            "node => new URL(node.getAttribute('href'), document.baseURI).href"
                        )
                        with page.expect_navigation():
                            keyboard_node.focus()
                            page.keyboard.press("Enter")
                        assert page.url == keyboard_href
                        page.goto(
                            f"{base_url}/_raya/graph/index.html?page=authoring-matrix",
                            wait_until="networkidle",
                        )
                        requested_urls.clear()
                        page.wait_for_selector(
                            "[data-raya-graph-detail-panel]:not([hidden])"
                        )
                        assert (
                            "Authoring Matrix Fixture"
                            in page.locator(
                                "[data-raya-graph-detail-title]"
                            ).inner_text()
                        )
                        assert (
                            "Explicit links: 4 outgoing, 2 incoming, 4 connected."
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
                        focus_button = page.locator(
                            "[data-raya-graph-focus-neighborhood]"
                        )
                        assert focus_button.is_visible()
                        assert focus_button.inner_text() == "Focus neighborhood"
                        focus_button.click()
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-page]')
                              ?.getAttribute('data-raya-graph-neighborhood-focus') === 'true'"""
                        )
                        assert focus_button.inner_text() == "Show full graph"
                        assert (
                            "Neighborhood focus:"
                            in page.locator("#graph-status").inner_text()
                        )
                        assert page.locator(
                            '#raya-graph-list [data-raya-graph-node="authoring-matrix"]'
                        ).is_visible()
                        assert page.locator(
                            '#raya-graph-list [data-raya-graph-node="render-root"]'
                        ).is_visible()
                        assert page.locator(
                            '#raya-graph-list [data-raya-graph-node="static-path"]'
                        ).is_hidden()
                        page.fill("#graph-search", "nested")
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-page]')
                              ?.getAttribute('data-raya-graph-neighborhood-focus') === 'false'"""
                        )
                        assert page.locator(
                            "[data-raya-graph-detail-panel]"
                        ).is_visible()
                        assert page.locator(
                            "#raya-graph-list [data-raya-graph-node].is-active-result"
                        ).count()
                        assert page.locator(
                            '#raya-graph-list [data-raya-graph-node="static-path"]'
                        ).is_visible()
                        assert page.locator(
                            '#raya-graph-list [data-raya-graph-node="authoring-matrix"]'
                        ).is_hidden()
                        page.goto(
                            f"{base_url}/_raya/graph/index.html?page=authoring-matrix",
                            wait_until="networkidle",
                        )
                        requested_urls.clear()
                        page.wait_for_selector(
                            "[data-raya-graph-detail-panel]:not([hidden])"
                        )
                        focus_button = page.locator(
                            "[data-raya-graph-focus-neighborhood]"
                        )
                        focus_button.click()
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-page]')
                              ?.getAttribute('data-raya-graph-neighborhood-focus') === 'true'"""
                        )
                        page.locator(
                            '[data-raya-graph-group-filter="authoring-matrix"]'
                        ).click()
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-page]')
                              ?.getAttribute('data-raya-graph-neighborhood-focus') === 'false'"""
                        )
                        assert page.locator(
                            "[data-raya-graph-detail-empty]"
                        ).is_visible()
                        assert page.locator(
                            '#raya-graph-list [data-raya-graph-node="authoring-matrix"]'
                        ).is_hidden()
                        assert page.locator(
                            '#raya-graph-list [data-raya-graph-node="static-path"]'
                        ).is_visible()
                        page.goto(
                            f"{base_url}/_raya/graph/index.html?page=authoring-matrix",
                            wait_until="networkidle",
                        )
                        requested_urls.clear()
                        page.wait_for_selector(
                            "[data-raya-graph-detail-panel]:not([hidden])"
                        )
                        focus_button = page.locator(
                            "[data-raya-graph-focus-neighborhood]"
                        )
                        assert page.locator(
                            '#raya-graph-list [data-raya-graph-node="static-path"]'
                        ).is_visible()
                        page.locator(
                            '[data-raya-graph-focus-node="math-authoring"]'
                        ).first.click()
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-detail-title]')
                              ?.textContent
                              ?.includes('Math Authoring Fixture')"""
                        )
                        assert page.locator(
                            '#raya-graph-list [data-raya-graph-node="math-authoring"]'
                        ).evaluate("node => node.classList.contains('is-active')")
                        assert page.url.endswith(
                            "/_raya/graph/index.html?page=math-authoring"
                        )
                        assert (
                            "math-authoring"
                            in page.locator(
                                "[data-raya-graph-state-selected]"
                            ).inner_text()
                        )
                        page.click("#graph-reset")
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-neighborhood-focus"
                            )
                            == "false"
                        )
                        assert requested_urls == []
                    finally:
                        page.close()
            finally:
                browser.close()
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                try:
                    page.goto(
                        f"{base_url}/_raya/graph/index.html?page=reader-ux",
                        wait_until="networkidle",
                    )
                    page.wait_for_selector(
                        '#raya-graph-canvas [data-raya-graph-node="reader-ux"] '
                        ".raya-graph-node.is-selected"
                    )
                    canvas_box = page.locator("#raya-graph-canvas").bounding_box()
                    selected_box = page.locator(
                        '#raya-graph-canvas [data-raya-graph-node="reader-ux"] g'
                    ).bounding_box()
                    edge_boxes = page.locator(
                        "#raya-graph-canvas .raya-graph-edge"
                    ).evaluate_all(
                        """edges => edges.map((edge) => {
                          const box = edge.getBoundingClientRect();
                          return {
                            x: box.x,
                            y: box.y,
                            width: box.width,
                            height: box.height,
                          };
                        })"""
                    )
                    assert canvas_box is not None
                    assert selected_box is not None
                    visible_canvas_box = _intersection_box(
                        canvas_box,
                        {
                            "x": 0,
                            "y": 0,
                            "width": 1440,
                            "height": 900,
                        },
                    )
                    assert visible_canvas_box["width"] > 0
                    assert visible_canvas_box["height"] > 0
                    assert _boxes_intersect(visible_canvas_box, selected_box)
                    assert any(
                        _boxes_intersect(visible_canvas_box, edge_box)
                        for edge_box in edge_boxes
                    )
                    assert canvas_box["height"] <= 700
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_graph_url_state_and_debug_readout(tmp_path: Path) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        assert handle.base_url is not None
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 950})
                requested_urls: list[str] = []
                page.on("request", lambda request: requested_urls.append(request.url))
                try:
                    page.goto(
                        f"{handle.base_url}/_raya/graph/index.html"
                        "?page=reader-ux&q=projection&layout=connections",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(page)
                    assert page.locator("#graph-search").input_value() == "projection"
                    assert page.locator("#graph-layout").input_value() == "connections"
                    assert "Projection Residuals" in page.locator(
                        "[data-raya-graph-detail-title]"
                    ).inner_text()
                    assert "reader-ux" in page.locator(
                        "[data-raya-graph-state-selected]"
                    ).inner_text()
                    assert "projection" in page.locator(
                        "[data-raya-graph-state-query]"
                    ).inner_text()
                    assert "connections" in page.locator(
                        "[data-raya-graph-state-layout]"
                    ).inner_text().lower()
                    assert "visible node" in page.locator(
                        "[data-raya-graph-state-visible]"
                    ).inner_text()
                    assert "page=reader-ux" in page.url
                    assert "q=projection" in page.url
                    assert "layout=connections" not in page.url

                    page.click('[data-raya-graph-toggle-panel="list"]')
                    page.wait_for_function(
                        "() => new URL(window.location.href).searchParams.get('list') === '0'"
                    )
                    assert "list=0" in page.locator(
                        "[data-raya-graph-state-url]"
                    ).inner_text()
                    page.click('[data-raya-graph-toggle-panel="inspector"]')
                    page.wait_for_function(
                        "() => new URL(window.location.href).searchParams.get('inspector') === '0'"
                    )
                    assert "inspector=0" in page.locator(
                        "[data-raya-graph-state-url]"
                    ).inner_text()
                    page.click('[data-raya-graph-toggle-panel="inspector"]')
                    page.click('[data-raya-graph-toggle-panel="list"]')

                    page.goto(
                        f"{handle.base_url}/_raya/graph/index.html",
                        wait_until="networkidle",
                    )
                    page.fill("#graph-search", "projection")
                    page.wait_for_function(
                        "() => new URL(window.location.href).searchParams.get('page') === 'reader-ux'"
                    )
                    assert "reader-ux" in page.locator(
                        "[data-raya-graph-state-selected]"
                    ).inner_text()
                    assert "Projection Residuals" in page.locator(
                        "[data-raya-graph-detail-title]"
                    ).inner_text()

                    page.click('[data-raya-graph-edge-kind-filter="parent"]')
                    page.wait_for_function(
                        "() => new URL(window.location.href).searchParams.get('edges')"
                    )
                    assert "Parent" in page.locator(
                        "[data-raya-graph-state-hidden-edges]"
                    ).inner_text()
                    assert "edges=" in page.url

                    page.locator("[data-raya-graph-group-filter]").first.click()
                    page.wait_for_function(
                        "() => new URL(window.location.href).searchParams.get('groups')"
                    )
                    assert "hidden" in page.locator(
                        "[data-raya-graph-state-hidden-groups]"
                    ).inner_text().lower()
                    assert handle.base_url in page.locator(
                        "[data-raya-graph-state-url]"
                    ).inner_text()

                    storage_state = page.evaluate(
                        """() => ({
                          local: Object.keys(localStorage),
                          session: Object.keys(sessionStorage),
                        })"""
                    )
                    assert storage_state == {"local": [], "session": []}
                    assert requested_urls
                    assert all(
                        url.startswith(f"{handle.base_url}/")
                        for url in requested_urls
                    )
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
    official_dir = course / "course" / "5_authoring_matrix" / "_official" / "prompts"
    official_dir.mkdir(parents=True)
    (official_dir / "1_matrix_prompt.yaml").write_text(
        "\n".join(
            [
                "id: matrix-prompt",
                "type: prompt",
                "authority: official",
                "content:",
                "  prompt: Explain why the identity matrix preserves vector norms.",
                "retrieval:",
                "  kind: reflection",
                "",
            ]
        ),
        encoding="utf-8",
    )
    assignment_dir = (
        course / "course" / "5_authoring_matrix" / "_official" / "assignments"
    )
    assignment_dir.mkdir(parents=True)
    (assignment_dir / "1_matrix_assignment.yaml").write_text(
        "\n".join(
            [
                "id: matrix-assignment",
                "type: assignment",
                "authority: official",
                "scope:",
                "  quantum: authoring-matrix",
                "content:",
                "  title: Matrix graph check",
                "  summary: Trace the graph context for matrix notation.",
                "  due: '2026-11-03'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    distractor = course / "course" / "6_matrix_reference" / "0_index.md"
    distractor.parent.mkdir(parents=True)
    distractor.write_text(
        "\n".join(
            [
                "---",
                "id: matrix-reference",
                "title: Matrix Reference",
                "summary: Matrix vocabulary without authoring matrix tasks.",
                "status: ready",
                "---",
                "",
                "# Matrix Reference",
                "",
                "This page makes fuzzy matrix search broader than exact page focus.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                for viewport in (
                    {"width": 1280, "height": 900},
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    try:
                        browser_requests: list[str] = []
                        page.on(
                            "request",
                            lambda request: browser_requests.append(request.url),
                        )
                        page.goto(
                            f"{base_url}/_raya/search/index.html",
                            wait_until="networkidle",
                        )
                        assert browser_requests
                        assert all(
                            url.startswith(f"{base_url}/") for url in browser_requests
                        )
                        _assert_no_horizontal_overflow(page)
                        assert page.locator(".raya-discovery-command-bar").is_visible()
                        assert page.locator(
                            ".raya-discovery-command-bar .raya-command-home"
                        ).is_visible()
                        assert (
                            page.locator(
                                ".raya-search-header .raya-course-title"
                            ).count()
                            == 0
                        )
                        assert (
                            page.locator(
                                ".raya-search-header .raya-graph-back-link"
                            ).count()
                            == 0
                        )
                        assert page.locator(".raya-search-workspace").is_visible()
                        assert page.locator(".raya-search-control-panel").is_visible()
                        assert page.locator(".raya-search-results-panel").is_visible()
                        assert page.locator(".raya-search-context-panel").is_visible()
                        if viewport["width"] >= 1280:
                            control_box = page.locator(
                                ".raya-search-control-panel"
                            ).bounding_box()
                            results_box = page.locator(
                                ".raya-search-results-panel"
                            ).bounding_box()
                            context_box = page.locator(
                                ".raya-search-context-panel"
                            ).bounding_box()
                            assert control_box is not None
                            assert results_box is not None
                            assert context_box is not None
                            assert (
                                control_box["x"] < results_box["x"] < context_box["x"]
                            )
                        if viewport["width"] < 520:
                            discovery_box = page.locator(
                                ".raya-discovery-command-bar"
                            ).bounding_box()
                            assert discovery_box is not None
                            assert discovery_box["height"] <= 150
                        assert (
                            page.locator(".raya-command-graph")
                            .evaluate("node => node.href")
                            .endswith("/_raya/graph/index.html")
                        )
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
                        assert (
                            "visible result"
                            in page.locator(
                                "[data-raya-search-summary-count]"
                            ).inner_text()
                        )
                        after = page.locator(
                            "#raya-search-results [data-raya-search-result]:visible"
                        ).count()
                        assert after < before
                        assert (
                            "Authoring Matrix Fixture"
                            in page.locator("#raya-search-results").inner_text()
                        )
                        assert (
                            "Matrix Reference"
                            in page.locator("#raya-search-results").inner_text()
                        )
                        result_card = page.locator(
                            '[data-raya-search-result="authoring-matrix"]'
                        )
                        assert "Stable ID authoring-matrix" in result_card.inner_text()
                        assert (
                            "Authoring Matrix Fixture"
                            in page.locator(
                                "[data-raya-search-context-title]"
                            ).inner_text()
                        )
                        assert (
                            "Explicit links"
                            in page.locator(
                                "[data-raya-search-context-meta]"
                            ).inner_text()
                        )
                        result_card.hover()
                        assert (
                            result_card.get_attribute("data-raya-search-active")
                            == "true"
                        )
                        result_card.locator("a").first.focus()
                        assert (
                            result_card.get_attribute("data-raya-search-active")
                            == "true"
                        )
                        assert (
                            "Authoring Matrix Fixture"
                            in page.locator(
                                "[data-raya-search-context-title]"
                            ).inner_text()
                        )
                        assert "Explicit links" in result_card.inner_text()
                        assert (
                            "Official objects: Assignment: 1, Prompt: 1"
                            in result_card.inner_text()
                        )
                        assert (
                            result_card.locator(".raya-search-result-practice")
                            .evaluate("node => node.href")
                            .endswith(
                                "/_raya/practice/index.html?page=authoring-matrix"
                            )
                        )
                        assert (
                            result_card.locator(".raya-search-result-tasks")
                            .evaluate("node => node.href")
                            .endswith("/_raya/tasks/index.html?page=authoring-matrix")
                        )
                        assert (
                            result_card.locator(".raya-search-result-schedule")
                            .evaluate("node => node.href")
                            .endswith(
                                "/_raya/schedule/index.html?page=authoring-matrix"
                            )
                        )
                        assert page.locator("#raya-search-empty").is_hidden()
                        graph_focus_href = page.locator(
                            '[data-raya-search-result="authoring-matrix"] '
                            ".raya-search-result-graph"
                        ).get_attribute("href")
                        assert (
                            graph_focus_href
                            == "../graph/index.html?page=authoring-matrix"
                        )
                        page.fill("#raya-search-input", "matrx")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-search-status')
                              ?.textContent
                              ?.includes('visible result')"""
                        )
                        assert (
                            "Authoring Matrix Fixture"
                            in page.locator("#raya-search-results").inner_text()
                        )
                        page.press("#raya-search-input", "ArrowDown")
                        active = page.locator(
                            '#raya-search-results [data-raya-search-active="true"]'
                        )
                        assert active.count() == 1
                        active_href = active.locator("a").first.evaluate(
                            "node => node.href"
                        )
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
                        assert (
                            "No visible result"
                            in page.locator(
                                "[data-raya-search-context-title]"
                            ).inner_text()
                        )
                        page.goto(
                            f"{base_url}/_raya/search/index.html?q=Authoring%20Matrix%20Fixture",
                            wait_until="networkidle",
                        )
                        assert page.input_value("#raya-search-input") == (
                            "Authoring Matrix Fixture"
                        )
                        assert (
                            "Authoring Matrix Fixture"
                            in page.locator("#raya-search-results").inner_text()
                        )
                        page.goto(
                            f"{base_url}/_raya/search/index.html?page=authoring-matrix",
                            wait_until="networkidle",
                        )
                        assert page.input_value("#raya-search-input") == ""
                        assert (
                            page.locator(
                                "#raya-search-results [data-raya-search-result]:visible"
                            ).count()
                            == 1
                        )
                        exact_card = page.locator(
                            '[data-raya-search-result="authoring-matrix"]'
                        )
                        assert exact_card.is_visible()
                        assert (
                            exact_card.get_attribute("data-raya-search-active")
                            == "true"
                        )
                        assert page.locator(
                            '[data-raya-search-result="matrix-reference"]'
                        ).is_hidden()
                        assert (
                            "Authoring Matrix Fixture"
                            in page.locator(
                                "[data-raya-search-context-title]"
                            ).inner_text()
                        )
                        page.goto(
                            (
                                f"{base_url}/_raya/search/index.html"
                                "?page=authoring-matrix&q=Matrix"
                            ),
                            wait_until="networkidle",
                        )
                        assert page.input_value("#raya-search-input") == "Matrix"
                        assert (
                            page.locator(
                                "#raya-search-results [data-raya-search-result]:visible"
                            ).count()
                            == 1
                        )
                        assert exact_card.is_visible()
                        page.goto(
                            (
                                f"{base_url}/_raya/search/index.html"
                                "?page=authoring-matrix&q=zz-no-result"
                            ),
                            wait_until="networkidle",
                        )
                        assert page.input_value("#raya-search-input") == "zz-no-result"
                        assert page.locator("#raya-search-empty").is_visible()
                        page.click("#raya-search-clear")
                        assert (
                            page.locator(
                                "#raya-search-results [data-raya-search-result]:visible"
                            ).count()
                            > 1
                        )
                        assert page.locator(
                            '[data-raya-search-result="matrix-reference"]'
                        ).is_visible()
                        page.goto(
                            f"{base_url}/_raya/search/index.html?page=missing-page",
                            wait_until="networkidle",
                        )
                        assert page.locator("#raya-search-empty").is_visible()
                        page.press("#raya-search-input", "Escape")
                        assert page.locator("#raya-search-empty").is_hidden()
                        page.click(
                            '[data-raya-search-result="authoring-matrix"] '
                            ".raya-search-result-graph"
                        )
                        page.wait_for_url(
                            "**/_raya/graph/index.html?page=authoring-matrix"
                        )
                        page.wait_for_selector(
                            "[data-raya-graph-detail-panel]:not([hidden])"
                        )
                        assert (
                            "Authoring Matrix Fixture"
                            in page.locator(
                                "[data-raya-graph-detail-title]"
                            ).inner_text()
                        )
                        assert (
                            "Official objects: Assignment: 1, Prompt: 1"
                            in page.locator(
                                "[data-raya-graph-detail-study-counts]"
                            ).inner_text()
                        )
                        assert (
                            "Explicit links:"
                            in page.locator(
                                "[data-raya-graph-detail-neighborhood]"
                            ).inner_text()
                        )
                        assert (
                            page.locator("[data-raya-graph-detail-search-link]")
                            .evaluate("node => node.href")
                            .endswith(
                                "/_raya/search/index.html?page=authoring-matrix"
                            )
                        )
                        assert (
                            page.locator("[data-raya-graph-detail-practice-link]")
                            .evaluate("node => node.href")
                            .endswith(
                                "/_raya/practice/index.html?page=authoring-matrix"
                            )
                        )
                        page.click("[data-raya-graph-detail-search-link]")
                        page.wait_for_url(
                            "**/_raya/search/index.html?page=authoring-matrix"
                        )
                        assert (
                            page.locator(
                                "#raya-search-results [data-raya-search-result]:visible"
                            ).count()
                            == 1
                        )
                        _assert_no_horizontal_overflow(page)
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_preview_serves_static_official_practice_workspace(tmp_path: Path) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "minimal"
    shutil.copytree(MINIMAL, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        base_url = handle.base_url
        assert base_url is not None
        practice_html = _fetch_text(f"{base_url}/_raya/practice/index.html")
        practice_js = _fetch_text(f"{base_url}/_raya/render/practice.js")

        assert 'data-raya-surface="practice"' in practice_html
        assert "raya-practice-data" in practice_html
        assert "https://" not in practice_html
        assert "http://" not in practice_html
        assert "fetch(" not in practice_js
        assert "XMLHttpRequest" not in practice_js

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                for viewport in (
                    {"width": 1280, "height": 900},
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    try:
                        browser_requests: list[str] = []
                        page.on(
                            "request",
                            lambda request: browser_requests.append(request.url),
                        )
                        page.goto(
                            f"{base_url}/_raya/practice/index.html",
                            wait_until="networkidle",
                        )
                        assert browser_requests
                        assert all(
                            url.startswith(f"{base_url}/") for url in browser_requests
                        )
                        _assert_no_horizontal_overflow(page)
                        assert page.locator(".raya-discovery-command-bar").is_visible()
                        assert page.locator(
                            ".raya-discovery-command-bar .raya-command-home"
                        ).is_visible()
                        assert (
                            page.locator(
                                ".raya-practice-header .raya-course-title"
                            ).count()
                            == 0
                        )
                        assert (
                            page.locator(
                                ".raya-practice-header .raya-graph-back-link"
                            ).count()
                            == 0
                        )
                        assert page.locator(".raya-practice-workspace").is_visible()
                        assert page.locator(".raya-practice-control-panel").is_visible()
                        assert page.locator(".raya-practice-results-panel").is_visible()
                        assert page.locator(".raya-practice-context-panel").is_visible()
                        if viewport["width"] >= 1280:
                            control_box = page.locator(
                                ".raya-practice-control-panel"
                            ).bounding_box()
                            results_box = page.locator(
                                ".raya-practice-results-panel"
                            ).bounding_box()
                            context_box = page.locator(
                                ".raya-practice-context-panel"
                            ).bounding_box()
                            assert control_box is not None
                            assert results_box is not None
                            assert context_box is not None
                            assert (
                                control_box["x"] < results_box["x"] < context_box["x"]
                            )
                        assert page.locator(".raya-command-search").is_visible()
                        assert page.locator(".raya-command-graph").is_visible()
                        assert page.locator(".raya-command-size").is_visible()
                        assert page.locator(".raya-command-font").is_visible()
                        page.click(".raya-command-font")
                        assert (
                            page.locator("html").get_attribute(
                                "data-raya-open-dyslexic"
                            )
                            == "true"
                        )
                        page.click(".raya-command-size")
                        assert (
                            page.locator("html").get_attribute("data-raya-text-size")
                            == "large"
                        )
                        assert page.locator(
                            '[data-raya-practice-object="first-topic-card"]'
                        ).is_visible()
                        assert page.locator(
                            '[data-raya-practice-object="first-topic-prompt"]'
                        ).is_visible()
                        assert page.locator(
                            '[data-raya-practice-object="first-topic-quiz"]'
                        ).is_visible()
                        quiz_card = page.locator(
                            '[data-raya-practice-object="first-topic-quiz"]'
                        )
                        quiz_card.hover()
                        assert (
                            quiz_card.get_attribute("data-raya-practice-active")
                            == "true"
                        )
                        assert (
                            "Quiz"
                            in page.locator(
                                "[data-raya-practice-context-meta]"
                            ).inner_text()
                        )
                        quiz_card.locator(".raya-practice-open").focus()
                        assert (
                            quiz_card.get_attribute("data-raya-practice-active")
                            == "true"
                        )
                        page.locator("#raya-practice-search").focus()
                        page.press("#raya-practice-search", "ArrowDown")
                        active_practice = page.locator(
                            '[data-raya-practice-active="true"]'
                        )
                        assert active_practice.count() == 1
                        assert (
                            "No visible"
                            not in page.locator(
                                "[data-raya-practice-context-title]"
                            ).inner_text()
                        )
                        active_open_href = active_practice.locator(
                            ".raya-practice-open"
                        ).first.evaluate("node => node.href")
                        with page.expect_navigation():
                            page.press("#raya-practice-search", "Enter")
                        assert page.url == active_open_href
                        page.goto(
                            f"{base_url}/_raya/practice/index.html",
                            wait_until="networkidle",
                        )
                        page.mouse.move(1, 1)
                        page.locator("#raya-practice-search").focus()
                        page.press("#raya-practice-search", "ArrowDown")
                        assert (
                            page.locator('[data-raya-practice-active="true"]').count()
                            == 1
                        )

                        page.fill("#raya-practice-search", "retrieval")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-practice-status')
                              ?.textContent
                              ?.includes('1 visible practice object')"""
                        )
                        assert (
                            "1 visible practice object"
                            in page.locator(
                                "[data-raya-practice-summary-count]"
                            ).inner_text()
                        )
                        assert (
                            page.locator('[data-raya-practice-active="true"]').count()
                            == 0
                        )
                        assert (
                            "Explain how retrieval practice differs from rereading."
                            in page.locator(
                                "[data-raya-practice-context-title]"
                            ).inner_text()
                        )
                        assert page.locator(
                            '[data-raya-practice-object="first-topic-prompt"]'
                        ).is_visible()
                        assert page.locator(
                            '[data-raya-practice-object="first-topic-card"]'
                        ).is_hidden()

                        page.click('[data-raya-practice-filter="quiz"]')
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-practice-status')
                              ?.textContent
                              ?.includes('0 visible practice object')"""
                        )
                        assert page.locator("#raya-practice-empty").is_visible()
                        assert (
                            "No visible practice object"
                            in page.locator(
                                "[data-raya-practice-context-title]"
                            ).inner_text()
                        )

                        page.click("#raya-practice-clear")
                        page.click('[data-raya-practice-filter="quiz"]')
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-practice-status')
                              ?.textContent
                              ?.includes('1 visible practice object')"""
                        )
                        assert page.locator(
                            '[data-raya-practice-object="first-topic-quiz"]'
                        ).is_visible()
                        assert page.locator(
                            '[data-raya-practice-object="first-topic-card"]'
                        ).is_hidden()
                        page.locator("#raya-practice-search").focus()
                        page.press("#raya-practice-search", "ArrowDown")
                        assert (
                            page.locator('[data-raya-practice-active="true"]').count()
                            == 1
                        )
                        page.press("#raya-practice-search", "Escape")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-practice-status')
                              ?.textContent
                              ?.includes('3 visible practice object')"""
                        )
                        assert (
                            page.locator('[data-raya-practice-active="true"]').count()
                            == 0
                        )

                        page.goto(
                            f"{base_url}/_raya/practice/index.html?page=first-topic",
                            wait_until="networkidle",
                        )
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-practice-status')
                              ?.textContent
                              ?.includes('3 visible practice object')"""
                        )
                        assert (
                            page.evaluate(
                                """() => Array.from(
                                  document.querySelectorAll(
                                    '[data-raya-practice-object]:not([hidden])'
                                  )
                                ).map((item) => item.dataset.rayaPracticePage)"""
                            )
                            == ["first-topic", "first-topic", "first-topic"]
                        )
                        assert (
                            "First Topic"
                            in page.locator(
                                "[data-raya-practice-context-meta]"
                            ).inner_text()
                        )
                        assert (
                            page.evaluate(
                                "() => [Object.keys(localStorage), Object.keys(sessionStorage)]"
                            )
                            == [[], []]
                        )

                        page.goto(
                            f"{base_url}/_raya/practice/index.html?page=missing-page",
                            wait_until="networkidle",
                        )
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-practice-status')
                              ?.textContent
                              ?.includes('0 visible practice object')"""
                        )
                        assert page.locator("#raya-practice-empty").is_visible()
                        assert (
                            "No visible practice object"
                            in page.locator(
                                "[data-raya-practice-context-title]"
                            ).inner_text()
                        )
                        assert (
                            page.evaluate(
                                "() => [Object.keys(localStorage), Object.keys(sessionStorage)]"
                            )
                            == [[], []]
                        )
                        page.click("#raya-practice-clear")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-practice-status')
                              ?.textContent
                              ?.includes('3 visible practice object')"""
                        )
                        page.goto(
                            f"{base_url}/_raya/practice/index.html?page=missing-page",
                            wait_until="networkidle",
                        )
                        page.locator("#raya-practice-search").focus()
                        page.press("#raya-practice-search", "Escape")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-practice-status')
                              ?.textContent
                              ?.includes('3 visible practice object')"""
                        )

                        page.click("#raya-practice-clear")
                        open_href = page.locator(
                            '[data-raya-practice-object="first-topic-card"] '
                            ".raya-practice-open"
                        ).evaluate("node => node.href")
                        with page.expect_navigation():
                            page.click(
                                '[data-raya-practice-object="first-topic-card"] '
                                ".raya-practice-open"
                            )
                        assert page.url == open_href
                        assert page.url.endswith(
                            "/unit/topic/index.html#raya-official-first-topic-card"
                        )
                        assert page.locator(
                            "#raya-official-first-topic-card"
                        ).is_visible()
                        uncovered = page.evaluate(
                            """() => {
                              const target = document.querySelector(
                                '#raya-official-first-topic-card'
                              );
                              const bar = document.querySelector('.raya-top-command-bar');
                              if (!target || !bar) return false;
                              const targetBox = target.getBoundingClientRect();
                              const barBox = bar.getBoundingClientRect();
                              return targetBox.top >= barBox.bottom + 8;
                            }"""
                        )
                        assert uncovered
                        _assert_no_horizontal_overflow(page)
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_preview_serves_static_official_tasks_workspace(tmp_path: Path) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "minimal"
    shutil.copytree(MINIMAL, course, ignore=shutil.ignore_patterns("artifact"))
    _add_official_task_objects(course)
    extension_page = course / "course" / "2_extension" / "0_index.md"
    extension_page.parent.mkdir(parents=True)
    extension_page.write_text(
        "\n".join(
            [
                "---",
                "id: extension-topic",
                "title: Extension Topic",
                "summary: A second task page for scoped task workspace tests.",
                "status: ready",
                "---",
                "",
                "# Extension Topic",
                "",
                "This page exists so page-scoped workspace links can hide unrelated work.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    extension_assignment_dir = (
        extension_page.parent / "_official" / "assignments"
    )
    extension_assignment_dir.mkdir(parents=True)
    (extension_assignment_dir / "1_extension_assignment.yaml").write_text(
        "\n".join(
            [
                "id: extension-assignment",
                "type: assignment",
                "authority: official",
                "scope:",
                "  quantum: extension-topic",
                "content:",
                "  title: Extension assignment",
                "  summary: An unrelated dated assignment for page-scope tests.",
                "  due: '2026-12-01'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        base_url = handle.base_url
        assert base_url is not None
        tasks_html = _fetch_text(f"{base_url}/_raya/tasks/index.html")
        tasks_js = _fetch_text(f"{base_url}/_raya/render/tasks.js")
        schedule_html = _fetch_text(f"{base_url}/_raya/schedule/index.html")
        schedule_js = _fetch_text(f"{base_url}/_raya/render/schedule.js")
        script_hrefs = re.findall(r'<script src="([^"]+)"', tasks_html)

        assert 'data-raya-surface="tasks"' in tasks_html
        assert "raya-tasks-data" in tasks_html
        assert 'data-raya-surface="schedule"' in schedule_html
        assert "raya-schedule-data" in schedule_html
        assert "https://" not in tasks_html
        assert "http://" not in tasks_html
        assert "fetch(" not in tasks_js
        assert "XMLHttpRequest" not in tasks_js
        assert "localStorage" not in tasks_js
        assert "sessionStorage" not in tasks_js
        assert "fetch(" not in schedule_js
        assert "XMLHttpRequest" not in schedule_js
        assert "localStorage" not in schedule_js
        assert "sessionStorage" not in schedule_js
        assert "private-task" not in tasks_html
        assert "private-task" not in schedule_html
        assert "unit-task" not in schedule_html
        assert 'data-raya-schedule-item="unit-assignment"' in schedule_html
        assert 'data-raya-schedule-item="unit-project"' in schedule_html
        assert 'data-raya-schedule-item="unit-exam"' in schedule_html
        assert "SHOULD_NOT_LEAK" not in tasks_html
        assert "SHOULD_NOT_LEAK" not in schedule_html
        for script_href in script_hrefs:
            loaded_script = _fetch_text(urljoin(f"{base_url}/_raya/tasks/", script_href))
            assert "fetch(" not in loaded_script
            assert "XMLHttpRequest" not in loaded_script
            assert "localStorage" not in loaded_script
            assert "sessionStorage" not in loaded_script

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                for viewport in (
                    {"width": 1280, "height": 900},
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    try:
                        browser_requests: list[str] = []
                        page.on(
                            "request",
                            lambda request: browser_requests.append(request.url),
                        )
                        page.goto(
                            f"{base_url}/_raya/tasks/index.html",
                            wait_until="networkidle",
                        )
                        assert browser_requests
                        assert all(
                            url.startswith(f"{base_url}/") for url in browser_requests
                        )
                        _assert_no_horizontal_overflow(page)
                        assert page.locator(".raya-discovery-command-bar").is_visible()
                        assert page.locator(
                            ".raya-discovery-command-bar .raya-command-home"
                        ).is_visible()
                        assert (
                            page.locator(
                                ".raya-tasks-header .raya-course-title"
                            ).count()
                            == 0
                        )
                        assert (
                            page.locator(
                                ".raya-tasks-header .raya-graph-back-link"
                            ).count()
                            == 0
                        )
                        assert page.locator(".raya-tasks-workspace").is_visible()
                        assert page.locator(".raya-tasks-control-panel").is_visible()
                        assert page.locator(".raya-tasks-results-panel").is_visible()
                        assert page.locator(".raya-tasks-context-panel").is_visible()
                        if viewport["width"] >= 1280:
                            control_box = page.locator(
                                ".raya-tasks-control-panel"
                            ).bounding_box()
                            results_box = page.locator(
                                ".raya-tasks-results-panel"
                            ).bounding_box()
                            context_box = page.locator(
                                ".raya-tasks-context-panel"
                            ).bounding_box()
                            assert control_box is not None
                            assert results_box is not None
                            assert context_box is not None
                            assert (
                                control_box["x"] < results_box["x"] < context_box["x"]
                            )
                        assert page.locator(".raya-command-search").is_visible()
                        assert page.locator(".raya-command-graph").is_visible()
                        assert page.locator(".raya-command-practice").is_visible()
                        assert page.locator(".raya-command-schedule").is_visible()
                        assert page.locator(".raya-command-size").is_visible()
                        assert page.locator(".raya-command-font").is_visible()
                        page.click(".raya-command-font")
                        assert (
                            page.locator("html").get_attribute(
                                "data-raya-open-dyslexic"
                            )
                            == "true"
                        )
                        assert page.evaluate("() => localStorage.length") == 0
                        assert page.evaluate("() => sessionStorage.length") == 0
                        page.click(".raya-command-size")
                        assert (
                            page.locator("html").get_attribute("data-raya-text-size")
                            == "large"
                        )
                        assert page.evaluate("() => localStorage.length") == 0
                        assert page.evaluate("() => sessionStorage.length") == 0
                        assert page.locator(
                            '[data-raya-task-object="unit-assignment"]'
                        ).is_visible()
                        assert page.locator(
                            '[data-raya-task-object="unit-project"]'
                        ).is_visible()
                        scoped_tasks = browser.new_page(viewport=viewport)
                        try:
                            scoped_tasks.goto(
                                f"{base_url}/_raya/tasks/index.html?page=first-topic",
                                wait_until="networkidle",
                            )
                            scoped_tasks.wait_for_function(
                                """() => document
                                  .querySelector('#raya-tasks-status')
                                  ?.textContent
                                  ?.includes('4 visible tasks')"""
                            )
                            assert scoped_tasks.locator(
                                '[data-raya-task-object="unit-assignment"]'
                            ).is_visible()
                            assert scoped_tasks.locator(
                                '[data-raya-task-object="unit-project"]'
                            ).is_visible()
                            assert scoped_tasks.locator(
                                '[data-raya-task-object="extension-assignment"]'
                            ).is_hidden()
                            assert (
                                "4 visible tasks"
                                in scoped_tasks.locator(
                                    "[data-raya-tasks-summary-count]"
                                ).inner_text()
                            )
                            assert scoped_tasks.evaluate("() => localStorage.length") == 0
                            assert scoped_tasks.evaluate("() => sessionStorage.length") == 0
                            scoped_tasks.click("#raya-tasks-clear")
                            scoped_tasks.wait_for_function(
                                """() => document
                                  .querySelector('#raya-tasks-status')
                                  ?.textContent
                                  ?.includes('5 visible tasks')"""
                            )
                            assert scoped_tasks.locator(
                                '[data-raya-task-object="extension-assignment"]'
                            ).is_visible()
                        finally:
                            scoped_tasks.close()
                        page.click('[data-raya-task-filter="assignment"]')
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-tasks-status')
                              ?.textContent
                              ?.includes('2 visible tasks')"""
                        )
                        assert page.locator(
                            '[data-raya-task-object="unit-assignment"]'
                        ).is_visible()
                        assert page.locator(
                            '[data-raya-task-object="extension-assignment"]'
                        ).is_visible()
                        assert page.locator(
                            '[data-raya-task-object="unit-project"]'
                        ).is_hidden()
                        page.click("#raya-tasks-clear")
                        page.fill("#raya-tasks-search", "retrieval")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-tasks-status')
                              ?.textContent
                              ?.includes('2 visible tasks')"""
                        )
                        assert (
                            "2 visible tasks"
                            in page.locator(
                                "[data-raya-tasks-summary-count]"
                            ).inner_text()
                        )
                        page.select_option("#raya-tasks-sort", "due")
                        first_visible = page.locator(
                            '[data-raya-task-object]:not([hidden])'
                        ).first
                        assert (
                            first_visible.get_attribute("data-raya-task-object")
                            == "unit-assignment"
                        )
                        first_visible.hover()
                        assert (
                            first_visible.get_attribute("data-raya-task-active")
                            == "true"
                        )
                        assert (
                            "2026-09-15"
                            in page.locator(
                                "[data-raya-tasks-context-meta]"
                            ).inner_text()
                        )
                        page.locator("#raya-tasks-search").focus()
                        page.press("#raya-tasks-search", "ArrowDown")
                        active_task = page.locator('[data-raya-task-active="true"]')
                        assert active_task.count() == 1
                        active_open_href = active_task.locator(
                            ".raya-task-open"
                        ).first.evaluate("node => node.href")
                        with page.expect_navigation():
                            page.press("#raya-tasks-search", "Enter")
                        assert page.url == active_open_href
                        assert "/unit/topic/index.html#raya-official-unit-" in page.url
                        task_anchor = page.url.rsplit("#", 1)[1]
                        assert page.locator(f"#{task_anchor}").is_visible()
                        _assert_no_horizontal_overflow(page)

                        schedule = browser.new_page(viewport=viewport)
                        try:
                            schedule_requests: list[str] = []
                            schedule.on(
                                "request",
                                lambda request: schedule_requests.append(request.url),
                            )
                            schedule.goto(
                                f"{base_url}/_raya/schedule/index.html",
                                wait_until="networkidle",
                            )
                            assert schedule_requests
                            assert all(
                                url.startswith(f"{base_url}/")
                                for url in schedule_requests
                            )
                            _assert_no_horizontal_overflow(schedule)
                            assert schedule.locator(
                                ".raya-discovery-command-bar"
                            ).is_visible()
                            assert schedule.locator(
                                ".raya-discovery-command-bar .raya-command-home"
                            ).is_visible()
                            assert schedule.locator(
                                ".raya-schedule-header .raya-course-title"
                            ).count() == 0
                            assert schedule.locator(
                                ".raya-schedule-header .raya-graph-back-link"
                            ).count() == 0
                            assert schedule.locator(
                                ".raya-schedule-workspace"
                            ).is_visible()
                            assert schedule.locator(
                                ".raya-schedule-control-panel"
                            ).is_visible()
                            assert schedule.locator(
                                ".raya-schedule-results-panel"
                            ).is_visible()
                            assert schedule.locator(
                                ".raya-schedule-context-panel"
                            ).is_visible()
                            assert schedule.locator(
                                '[data-raya-schedule-item="unit-assignment"]'
                            ).is_visible()
                            assert schedule.locator(
                                '[data-raya-schedule-item="unit-project"]'
                            ).is_visible()
                            assert schedule.locator(
                                '[data-raya-schedule-item="unit-exam"]'
                            ).is_visible()
                            scoped_schedule = browser.new_page(viewport=viewport)
                            try:
                                scoped_schedule.goto(
                                    f"{base_url}/_raya/schedule/index.html?page=first-topic",
                                    wait_until="networkidle",
                                )
                                scoped_schedule.wait_for_function(
                                    """() => document
                                      .querySelector('#raya-schedule-status')
                                      ?.textContent
                                      ?.includes('3 visible schedule items')"""
                                )
                                assert scoped_schedule.locator(
                                    '[data-raya-schedule-item="unit-assignment"]'
                                ).is_visible()
                                assert scoped_schedule.locator(
                                    '[data-raya-schedule-item="unit-project"]'
                                ).is_visible()
                                assert scoped_schedule.locator(
                                    '[data-raya-schedule-item="extension-assignment"]'
                                ).is_hidden()
                                assert (
                                    "3 visible schedule items"
                                    in scoped_schedule.locator(
                                        "[data-raya-schedule-summary-count]"
                                    ).inner_text()
                                )
                                scoped_schedule.locator("#raya-schedule-search").focus()
                                scoped_schedule.press("#raya-schedule-search", "Escape")
                                scoped_schedule.wait_for_function(
                                    """() => document
                                      .querySelector('#raya-schedule-status')
                                      ?.textContent
                                      ?.includes('4 visible schedule items')"""
                                )
                                assert scoped_schedule.locator(
                                    '[data-raya-schedule-item="extension-assignment"]'
                                ).is_visible()
                                assert (
                                    scoped_schedule.evaluate(
                                        "() => localStorage.length"
                                    )
                                    == 0
                                )
                                assert (
                                    scoped_schedule.evaluate(
                                        "() => sessionStorage.length"
                                    )
                                    == 0
                                )
                            finally:
                                scoped_schedule.close()
                            assert schedule.locator(
                                '[data-raya-schedule-item="unit-task"]'
                            ).count() == 0
                            schedule.click('[data-raya-schedule-kind-filter="available"]')
                            schedule.wait_for_function(
                                """() => document
                                  .querySelector('#raya-schedule-status')
                                  ?.textContent
                                  ?.includes('1 visible schedule item')"""
                            )
                            assert schedule.locator(
                                '[data-raya-schedule-item="unit-exam"]'
                            ).is_visible()
                            assert schedule.locator(
                                '[data-raya-schedule-item="unit-assignment"]'
                            ).is_hidden()
                            schedule.click("#raya-schedule-clear")
                            schedule.fill("#raya-schedule-search", "retrieval")
                            schedule.wait_for_function(
                                """() => document
                                  .querySelector('#raya-schedule-status')
                                  ?.textContent
                                  ?.includes('2 visible schedule items')"""
                            )
                            schedule.locator("#raya-schedule-search").focus()
                            schedule.press("#raya-schedule-search", "ArrowDown")
                            active_item = schedule.locator(
                                '[data-raya-schedule-active="true"]'
                            )
                            assert active_item.count() == 1
                            assert (
                                "2026-09-15"
                                in schedule.locator(
                                    "[data-raya-schedule-context-meta]"
                                ).inner_text()
                            )
                            assert schedule.evaluate("() => localStorage.length") == 0
                            assert schedule.evaluate("() => sessionStorage.length") == 0
                        finally:
                            schedule.close()
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
    assert (
        '<button class="raya-command raya-command-font raya-font-toggle"' in index_html
    )
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
    assert (
        'class="raya-course-map" aria-label="Course map" data-raya-course-map="expanded"'
        in index_html
    )
    assert (
        'class="raya-course-map-list" id="raya-course-map-list" aria-hidden="false"'
        in index_html
    )
    assert 'data-raya-map-label="1 Static Path">1 Static Path</a>' in index_html
    assert "data-raya-rail-toggle" in reader_html
    assert 'data-raya-rail-panel-state="collapsed"' in reader_html
    assert 'aria-hidden="true" inert' in reader_html
    assert "background: var(--raya-color-page)" in rich_css
    assert "background: var(--raya-color-surface)" in rich_css
    assert "max-width: 116rem" in rich_css
    assert (
        "grid-template-columns: minmax(13.75rem, 16rem) minmax(0, 1fr) minmax(16rem, 18rem)"
        in rich_css
    )
    assert "@media (min-width: 1280px)" in rich_css
    assert (
        "grid-template-columns: 4.5rem minmax(48rem, 1fr) minmax(15rem, 15rem)"
        in rich_css
    )
    assert "transition: grid-template-columns 180ms ease" in rich_css
    assert ".raya-course-map-toggle:focus-visible" in rich_css
    assert ".raya-rail-toggle:focus-visible" in rich_css
    assert "outline: 3px solid var(--raya-color-accent)" in rich_css
    assert "@media (max-width: 1279px)" in rich_css


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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                    before = page.evaluate(
                        "() => getComputedStyle(document.body).fontFamily"
                    )
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                              const commandTops = commands.map(
                                (item) => Math.round(item.getBoundingClientRect().top)
                              );
                              return {
                                count: commands.length,
                                minHeights: commands.map(
                                  (item) => item.getBoundingClientRect().height
                                ),
                                topBarHeight: topBar.getBoundingClientRect().height,
                                commandRows: new Set(commandTops).size,
                                topBarWidth: topBar.scrollWidth,
                                viewportWidth: document.documentElement.clientWidth,
                                searchHref: document
                                  .querySelector('.raya-command-search')
                                  ?.getAttribute('href'),
                                graphHref: document
                                  .querySelector('.raya-command-graph')
                                  ?.getAttribute('href'),
                                practiceHref: document
                                  .querySelector('.raya-command-practice')
                                  ?.getAttribute('href'),
                                tasksHref: document
                                  .querySelector('.raya-command-tasks')
                                  ?.getAttribute('href'),
                                scheduleHref: document
                                  .querySelector('.raya-command-schedule')
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
                        assert state["count"] == 8
                        assert all(height >= 36 for height in state["minHeights"])
                        assert state["topBarWidth"] <= state["viewportWidth"]
                        if viewport["width"] >= 1024:
                            assert state["topBarHeight"] <= 96
                            assert state["commandRows"] == 1
                        else:
                            assert state["topBarHeight"] <= 220
                        assert state["searchHref"] == (
                            "_raya/search/index.html?q=Raya%20Lucaria%20Render%20Fixture"
                        )
                        assert (
                            state["graphHref"]
                            == "_raya/graph/index.html?page=render-root"
                        )
                        assert state["practiceHref"] == "_raya/practice/index.html"
                        assert state["tasksHref"] == "_raya/tasks/index.html"
                        assert state["scheduleHref"] == "_raya/schedule/index.html"
                        assert state["mapExpanded"] == (
                            "true" if viewport["width"] >= 1280 else "false"
                        )
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
                        assert collapsed_state["expanded"] == (
                            "false" if viewport["width"] >= 1280 else "true"
                        )
                        assert collapsed_state["label"] == "Course map"
                        assert collapsed_state["height"] >= 36
                        assert collapsed_state["height"] < 72
                        assert collapsed_state["width"] < 180
                        assert (
                            collapsed_state["topBarWidth"]
                            <= collapsed_state["viewportWidth"]
                        )
                        if viewport["width"] < 1280:
                            page.keyboard.press("Escape")
                            page.wait_for_function(
                                """() => document.documentElement.dataset.rayaCourseMapDrawer === 'closed'"""
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                    {"width": 1100, "height": 900},
                    {"width": 960, "height": 900},
                    {"width": 1024, "height": 900},
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    try:
                        page.goto(
                            f"{handle.base_url}/reader-ux/index.html",
                            wait_until="networkidle",
                        )
                        _assert_no_horizontal_overflow(page)
                        _assert_intersects_viewport(page, "header.raya-top-command-bar")
                        _assert_intersects_viewport(page, "article.raya-main-article")
                        if viewport["width"] >= 1280:
                            _assert_intersects_viewport(page, "nav.raya-course-map")
                            _assert_intersects_viewport(
                                page, "aside.raya-learning-rail"
                            )
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
                        if viewport["width"] >= 1280:
                            assert course_map["x"] < article["x"] < learning_rail["x"]
                            metrics = page.evaluate(
                                """() => {
                                  const shell = document.querySelector('.raya-learning-shell');
                                  const map = document.querySelector('#raya-course-map');
                                  const article = document.querySelector('#raya-article');
                                  const rail = document.querySelector('#raya-learning-rail');
                                  const commandBar = document.querySelector('.raya-top-command-bar');
                                  const commands = Array.from(document.querySelectorAll('.raya-command'));
                                  const currentMapLink = document.querySelector('#raya-course-map a[aria-current="page"]');
                                  return {
                                    shellWidth: shell.getBoundingClientRect().width,
                                    mapWidth: map.getBoundingClientRect().width,
                                    articleWidth: article.getBoundingClientRect().width,
                                    railWidth: rail.getBoundingClientRect().width,
                                    commandBarHeight: commandBar.getBoundingClientRect().height,
                                    commandHeights: commands.map((button) => button.getBoundingClientRect().height),
                                    commandWidths: commands.map((button) => button.getBoundingClientRect().width),
                                    mapIndex: currentMapLink?.getAttribute('data-raya-map-index'),
                                    mapNumber: currentMapLink
                                      ? getComputedStyle(currentMapLink, '::before').content
                                      : '',
                                    mapNumberDisplay: currentMapLink
                                      ? getComputedStyle(currentMapLink, '::before').display
                                      : '',
                                  };
                                }"""
                            )
                            assert 188 <= metrics["mapWidth"] <= 250
                            assert metrics["articleWidth"] >= 760
                            assert 220 <= metrics["railWidth"] <= 285
                            assert metrics["commandBarHeight"] <= 72
                            assert all(
                                36 <= height <= 48
                                for height in metrics["commandHeights"]
                            )
                            assert all(
                                width >= 40 for width in metrics["commandWidths"]
                            )
                            assert metrics["mapIndex"]
                            assert metrics["mapNumber"] == f'"{metrics["mapIndex"]}"'
                            assert metrics["mapNumberDisplay"] in {
                                "inline-flex",
                                "flex",
                            }
                            workspace = page.evaluate(
                                """() => {
                                  const section = document.querySelector('[data-raya-course-map-workspaces]');
                                  const links = Array.from(
                                    document.querySelectorAll('[data-raya-course-map-workspace-link]')
                                  );
                                  return {
                                    visible: !!section && getComputedStyle(section).display !== 'none',
                                    labels: links.map((link) => link
                                      .querySelector('.raya-course-map-workspace-label')
                                      ?.textContent
                                      ?.trim() || ''),
                                    badges: links.map((link) => link
                                      .querySelector('.raya-course-map-workspace-badge')
                                      ?.textContent
                                      ?.trim() || ''),
                                    hrefs: links.map((link) => link.getAttribute('href')),
                                  };
                                }"""
                            )
                            assert workspace["visible"] is True
                            assert workspace["labels"] == [
                                "Search",
                                "Graph",
                                "Practice",
                                "Tasks",
                                "Schedule",
                            ]
                            assert workspace["badges"][0] == "Course"
                            assert re.fullmatch(r"\d+ links?", workspace["badges"][1])
                            assert workspace["badges"][2] == "2 official"
                            assert workspace["badges"][3] == "Course"
                            assert workspace["badges"][4] == "Course"
                            assert any(
                                "../_raya/search/index.html?q=" in href
                                for href in workspace["hrefs"]
                            )
                            assert any(
                                "../_raya/graph/index.html?page=reader-ux" in href
                                for href in workspace["hrefs"]
                            )
                            assert (
                                "../_raya/practice/index.html?page=reader-ux"
                                in workspace["hrefs"]
                            )
                            assert any(
                                "../_raya/tasks/index.html" in href
                                for href in workspace["hrefs"]
                            )
                            assert any(
                                "../_raya/schedule/index.html" in href
                                for href in workspace["hrefs"]
                            )
                            page.click(".raya-course-map-toggle")
                            page.wait_for_function(
                                """() => document
                                  .querySelector('#raya-course-map')
                                  ?.getBoundingClientRect().width < 80"""
                            )
                            page.click("[data-raya-learning-rail-collapse]")
                            page.wait_for_function(
                                """() => document
                                  .querySelector('#raya-learning-rail-body')
                                  ?.getAttribute('aria-hidden') === 'true'"""
                            )
                            page.wait_for_function(
                                """() => document
                                  .querySelector('#raya-learning-rail')
                                  ?.getBoundingClientRect().width < 70"""
                            )
                            collapsed = page.evaluate(
                                """() => ({
                                  mapWidth: document.querySelector('#raya-course-map')
                                    .getBoundingClientRect().width,
                                  railWidth: document.querySelector('#raya-learning-rail')
                                    .getBoundingClientRect().width,
                                  mapButtonAfter: getComputedStyle(
                                    document.querySelector('#raya-course-map .raya-course-map-toggle'),
                                    '::after'
                                  ).content,
                                  railButtonAfter: getComputedStyle(
                                    document.querySelector('.raya-learning-rail-expand'),
                                    '::after'
                                  ).content,
                                  railBodyHidden: document
                                    .querySelector('#raya-learning-rail-body')
                                    .getAttribute('aria-hidden'),
                                  railBodyInert: document
                                    .querySelector('#raya-learning-rail-body')
                                    .inert,
                                  collapsedMapLinks: Array
                                    .from(document.querySelectorAll('#raya-course-map a[href]'))
                                    .filter((link) => {
                                      const rect = link.getBoundingClientRect();
                                      return rect.width > 0 && rect.height > 0;
                                    })
                                    .map((link) => {
                                      const rect = link.getBoundingClientRect();
                                      return {
                                        width: rect.width,
                                        height: rect.height,
                                        text: link.textContent.trim(),
                                      };
                                    }),
                                  workspaceDisplay: getComputedStyle(
                                    document.querySelector('[data-raya-course-map-workspaces]')
                                  ).display,
                                })"""
                            )
                            assert 64 <= collapsed["mapWidth"] <= 84
                            assert 44 <= collapsed["railWidth"] <= 64
                            assert collapsed["mapButtonAfter"] == '"Nav"'
                            assert collapsed["railButtonAfter"] == '"Info"'
                            assert collapsed["railBodyHidden"] == "true"
                            assert collapsed["railBodyInert"] is True
                            assert collapsed["workspaceDisplay"] == "none"
                            assert collapsed["collapsedMapLinks"]
                            assert all(
                                link["width"] >= 34 and link["height"] >= 34
                                for link in collapsed["collapsedMapLinks"]
                            )
                            _assert_no_horizontal_overflow(page)
                            page.set_viewport_size({"width": 1100, "height": 900})
                            page.wait_for_timeout(100)
                            resized = page.evaluate(
                                """() => {
                                  const railBody = document.querySelector('#raya-learning-rail-body');
                                  return {
                                    display: getComputedStyle(railBody).display,
                                    ariaHidden: railBody.getAttribute('aria-hidden'),
                                    inert: railBody.inert,
                                    height: railBody.getBoundingClientRect().height,
                                  };
                                }"""
                            )
                            assert resized["display"] != "none"
                            assert resized["height"] > 0
                            assert resized["ariaHidden"] == "false"
                            assert resized["inert"] is False
                            _assert_no_horizontal_overflow(page)
                            page.locator(".raya-skip-link").focus()
                        else:
                            if viewport["width"] >= 900:
                                assert article["width"] >= 700
                            assert article["y"] < learning_rail["y"]
                            drawer_state = page.evaluate(
                                """() => {
                                  const root = document.documentElement;
                                  const map = document.querySelector('#raya-course-map');
                                  const command = document.querySelector('.raya-command-map');
                                  return {
                                    drawer: root.dataset.rayaCourseMapDrawer,
                                    mapHidden: map.getAttribute('aria-hidden'),
                                    mapInert: map.inert,
                                    commandExpanded: command.getAttribute('aria-expanded'),
                                  };
                                }"""
                            )
                            assert drawer_state == {
                                "drawer": "closed",
                                "mapHidden": "true",
                                "mapInert": True,
                                "commandExpanded": "false",
                            }
                            _assert_bounded_scroll_region(
                                page, "aside.raya-learning-rail"
                            )
                            page.click(".raya-command-map")
                            page.wait_for_function(
                                """() => document.documentElement.dataset.rayaCourseMapDrawer === 'open'"""
                            )
                            _assert_bounded_scroll_region(page, "nav.raya-course-map")
                            mobile_course_list = page.locator(
                                "#raya-course-map .raya-course-map-list"
                            ).bounding_box()
                            assert mobile_course_list is not None
                            assert mobile_course_list["width"] > 100
                            assert mobile_course_list["height"] > 40
                            mobile_course_link = page.locator(
                                "#raya-course-map a"
                            ).first.bounding_box()
                            assert mobile_course_link is not None
                            assert mobile_course_link["width"] > 0
                            assert mobile_course_link["height"] > 0
                            page.keyboard.press("Escape")
                            page.wait_for_function(
                                """() => document.documentElement.dataset.rayaCourseMapDrawer === 'closed'"""
                            )
                            _assert_no_horizontal_overflow(page)
                            mobile_grid_columns = page.evaluate(
                                """() => getComputedStyle(
                                  document.querySelector('.raya-learning-shell')
                                ).gridTemplateColumns"""
                            )
                            assert len(mobile_grid_columns.split()) == 1
                        assert (
                            page.locator("button.raya-font-toggle").get_attribute(
                                "aria-label"
                            )
                            == "Toggle OpenDyslexic font"
                        )
                        page.keyboard.press("Tab")
                        focused = page.evaluate(
                            "() => document.activeElement && document.activeElement.className"
                        )
                        assert (
                            "raya-skip-link" in focused
                            or "raya-reading-context-link" in focused
                            or "raya-text-size-toggle" in focused
                            or "raya-font-toggle" in focused
                        )
                        page.locator(".raya-skip-link").focus()
                        page.keyboard.press("Enter")
                        focused_id = page.evaluate(
                            "() => document.activeElement && document.activeElement.id"
                        )
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                            currentHeight: currentRect.height,
                            mapTop: mapRect.top,
                            mapBottom: mapRect.bottom,
                            mapHeight: mapRect.height,
                            localStorageKeys: Object.keys(localStorage),
                            sessionStorageKeys: Object.keys(sessionStorage),
                          };
                        }"""
                    )
                    assert orientation is not None
                    assert orientation["oriented"] == "true"
                    assert orientation["scrollTop"] > 0
                    assert orientation["currentTop"] >= orientation["mapTop"] - 1
                    if orientation["currentHeight"] <= orientation["mapHeight"]:
                        assert (
                            orientation["currentBottom"] <= orientation["mapBottom"] + 1
                        )
                    else:
                        assert orientation["currentBottom"] >= orientation["mapTop"]
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
                            currentHeight: currentRect.height,
                            mapTop: mapRect.top,
                            mapBottom: mapRect.bottom,
                            mapHeight: mapRect.height,
                          };
                        }"""
                    )
                    assert reexpanded is not None
                    assert reexpanded["scrollTop"] > 0
                    assert reexpanded["currentTop"] >= reexpanded["mapTop"] - 1
                    if reexpanded["currentHeight"] <= reexpanded["mapHeight"]:
                        assert (
                            reexpanded["currentBottom"] <= reexpanded["mapBottom"] + 1
                        )
                    else:
                        assert reexpanded["currentBottom"] >= reexpanded["mapTop"]
                    first_toggle = page.locator("[data-raya-map-node-toggle]").first
                    before = first_toggle.get_attribute("aria-expanded")
                    first_toggle.click()
                    after = first_toggle.get_attribute("aria-expanded")
                    assert before != after
                    page.fill("#raya-course-map-filter", "matrix")
                    assert page.locator("[data-raya-map-node]:visible").count() >= 1
                    assert (
                        "matrix"
                        in page.locator("#raya-course-map-list").inner_text().lower()
                    )
                    assert page.locator("[data-raya-map-filter-empty]").is_hidden()
                    page.fill("#raya-course-map-filter", "reader-ux")
                    assert page.locator("[data-raya-map-node]:visible").count() == 0
                    assert page.locator("[data-raya-map-filter-empty]").is_visible()
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
    _add_official_task_objects(course)
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                        f"{handle.base_url}/unit/topic/index.html",
                        wait_until="networkidle",
                    )
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
                          workspaceLabels: Array.from(
                            document.querySelectorAll('[data-raya-course-map-workspace-link]')
                          ).map((link) => link
                            .querySelector('.raya-course-map-workspace-label')
                            ?.textContent
                            ?.trim() || ''),
                          workspaceBadges: Array.from(
                            document.querySelectorAll('[data-raya-course-map-workspace-link]')
                          ).map((link) => link
                            .querySelector('.raya-course-map-workspace-badge')
                            ?.textContent
                            ?.trim() || ''),
                          practiceHref: document
                            .querySelector('.raya-course-map-workspace-practice')
                            ?.getAttribute('href'),
                          tasksHref: document
                            .querySelector('.raya-course-map-workspace-tasks')
                            ?.getAttribute('href'),
                          scheduleHref: document
                            .querySelector('.raya-course-map-workspace-schedule')
                            ?.getAttribute('href'),
                        })"""
                    )
                    assert initial["firstUnitExpanded"] == "true"
                    assert initial["firstUnitChildrenHidden"] is False
                    assert initial["firstTopicVisible"] is True
                    assert initial["filterVisible"] is True
                    assert initial["workspaceLabels"] == [
                        "Search",
                        "Graph",
                        "Practice",
                        "Tasks",
                        "Schedule",
                    ]
                    assert initial["workspaceBadges"][2] == "8 official"
                    assert initial["workspaceBadges"][3] == "4 tasks"
                    assert initial["workspaceBadges"][4] == "3 dated"
                    assert initial["practiceHref"].endswith(
                        "_raya/practice/index.html?page=first-topic"
                    )
                    assert initial["tasksHref"].endswith(
                        "_raya/tasks/index.html?page=first-topic"
                    )
                    assert initial["scheduleHref"].endswith(
                        "_raya/schedule/index.html?page=first-topic"
                    )

                    page.click(
                        '[data-raya-map-node="first-unit"] [data-raya-map-node-toggle]'
                    )
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

                    page.click('[data-raya-course-map-action="expand-all"]')
                    expanded_all = page.evaluate(
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
                        })"""
                    )
                    assert expanded_all == {
                        "firstUnitExpanded": "true",
                        "firstUnitChildrenHidden": False,
                        "firstTopicVisible": True,
                    }

                    page.click('[data-raya-map-node="first-unit"] [data-raya-map-node-toggle]')
                    page.click('[data-raya-course-map-action="less"]')
                    reduced_to_current = page.evaluate(
                        """() => ({
                          firstUnitExpanded: document
                            .querySelector('[data-raya-map-node="first-unit"] [data-raya-map-node-toggle]')
                            ?.getAttribute('aria-expanded'),
                          firstTopicVisible: !!document
                            .querySelector('[data-raya-map-node="first-topic"]')
                            ?.checkVisibility(),
                          currentVisible: !!document
                            .querySelector('#raya-course-map a[aria-current="page"]')
                            ?.checkVisibility(),
                        })"""
                    )
                    assert reduced_to_current == {
                        "firstUnitExpanded": "true",
                        "firstTopicVisible": True,
                        "currentVisible": True,
                    }

                    page.fill("#raya-course-map-filter", "zz-no-match")
                    page.click('[data-raya-course-map-action="current"]')
                    current_action = page.evaluate(
                        """() => ({
                          filterValue: document.querySelector('#raya-course-map-filter')?.value,
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
                    assert current_action == {
                        "filterValue": "",
                        "firstUnitExpanded": "true",
                        "firstTopicVisible": True,
                        "emptyVisible": False,
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
                        "firstTopicVisible": True,
                        "filterVisible": False,
                        "emptyVisible": False,
                    }

                    page.click(".raya-course-map-toggle")
                    page.click(
                        '[data-raya-map-node="first-unit"] [data-raya-map-node-toggle]'
                    )
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
                        "visibleLinks": 2,
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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


def test_render_fixture_end_of_page_sequence_cards_are_static_and_responsive(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                        f"{handle.base_url}/static-path/index.html",
                        wait_until="networkidle",
                    )
                    requested_urls.clear()
                    cards = page.locator(".raya-article-sequence-cards")
                    cards.scroll_into_view_if_needed()
                    desktop_state = page.evaluate(
                        """() => {
                          const nav = document.querySelector('.raya-article-sequence-cards');
                          const previous = document.querySelector('.raya-sequence-card-prev');
                          const next = document.querySelector('.raya-sequence-card-next');
                          if (!nav || !previous || !next) return null;
                          return {
                            display: getComputedStyle(nav).display,
                            columnCount: getComputedStyle(nav).gridTemplateColumns
                              .split(' ')
                              .filter(Boolean)
                              .length,
                            previousHref: previous.getAttribute('href'),
                            nextHref: next.getAttribute('href'),
                            previousLabel: previous.textContent,
                            nextLabel: next.textContent,
                          };
                        }"""
                    )
                    assert desktop_state is not None
                    assert desktop_state["display"] == "grid"
                    assert desktop_state["columnCount"] == 2
                    assert desktop_state["previousHref"] == "../index.html"
                    assert desktop_state["nextHref"] == "../math-authoring/index.html"
                    assert "Previous page" in desktop_state["previousLabel"]
                    assert "Next page" in desktop_state["nextLabel"]
                    assert "progress" not in desktop_state["nextLabel"].lower()
                    assert "recommend" not in desktop_state["nextLabel"].lower()
                    assert requested_urls == []
                    _assert_no_horizontal_overflow(page)

                    page.set_viewport_size({"width": 390, "height": 820})
                    cards.scroll_into_view_if_needed()
                    mobile_state = page.evaluate(
                        """() => {
                          const nav = document.querySelector('.raya-article-sequence-cards');
                          if (!nav) return null;
                          return {
                            display: getComputedStyle(nav).display,
                            columns: getComputedStyle(nav).gridTemplateColumns,
                          };
                        }"""
                    )
                    assert mobile_state is not None
                    assert mobile_state["display"] == "grid"
                    assert " " not in mobile_state["columns"].strip()
                    _assert_no_horizontal_overflow(page)

                    page.set_viewport_size({"width": 1280, "height": 900})
                    page.keyboard.press("ArrowRight")
                    page.wait_for_url("**/math-authoring/index.html")
                    assert page.url.endswith("/math-authoring/index.html")
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                        page.goto(
                            f"{handle.base_url}/index.html", wait_until="networkidle"
                        )
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
                        assert copy_button.evaluate(
                            "button => document.activeElement === button"
                        )
                        copy_button.click()
                        page.wait_for_function(
                            "() => window.__rayaCopiedText.length > 0"
                        )

                        copied = page.evaluate("() => window.__rayaCopiedText")
                        assert copied == (
                            "def fixture_value() -> str:\n"
                            '    return "<rendered, not executed>"\n'
                        )
                        assert copy_button.inner_text() == "Copied"
                        assert (
                            copy_button.get_attribute("aria-label")
                            == "Code block copied"
                        )
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                    page.goto(
                        f"{handle.base_url}/reader-ux/index.html",
                        wait_until="networkidle",
                    )
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
                    after_hover = page.evaluate(
                        "() => document.documentElement.dataset.rayaCourseMap"
                    )
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
                    assert collapsed["buttonVisualLabel"] == '"Nav"'
                    assert collapsed["wrappedLinkTexts"] == []
                    assert collapsed["firstLinkWidth"] <= collapsed["mapWidth"]
                    assert collapsed["firstLinkPointerEvents"] == "auto"
                    assert collapsed["linkTabIndexes"]
                    assert set(collapsed["linkTabIndexes"]) == {None}

                    page.click(".raya-course-map-toggle")
                    page.wait_for_function(
                        """() => document
                          .querySelector('#raya-course-map')
                          ?.getBoundingClientRect().width >= 220"""
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
                    assert (
                        "raya-course-map-toggle"
                        in escape_collapsed["activeElementClass"]
                    )
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                        f"{handle.base_url}/reader-ux/index.html",
                        wait_until="networkidle",
                    )
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                    page.goto(
                        f"{handle.base_url}/reader-ux/index.html",
                        wait_until="networkidle",
                    )
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
                    assert (
                        escape_collapsed["expandWidth"] <= escape_collapsed["railWidth"]
                    )
                finally:
                    page.close()

                mobile = browser.new_page(viewport={"width": 390, "height": 844})
                try:
                    mobile.goto(
                        f"{handle.base_url}/reader-ux/index.html",
                        wait_until="networkidle",
                    )
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                          const summary = body?.querySelector('summary');
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
                            hasSummary: !!summary,
                            summaryTabIndex: summary?.getAttribute('tabindex'),
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
                    assert collapsed["hasSummary"] is True
                    assert collapsed["summaryTabIndex"] == "-1"

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
                          const summary = body?.querySelector('summary');
                          link?.focus();
                          return {
                            state: panel.dataset.rayaRailPanelState,
                            expanded: panel.querySelector('[data-raya-rail-toggle]')
                              ?.getAttribute('aria-expanded'),
                            ariaHidden: body?.getAttribute('aria-hidden'),
                            inert: body?.inert,
                            bodyHeight: body?.getBoundingClientRect().height,
                            linkTabIndex: link?.getAttribute('tabindex'),
                            summaryTabIndex: summary?.getAttribute('tabindex'),
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
                    assert expanded["summaryTabIndex"] is None
                    assert "Connections" in expanded["text"]
                    assert expanded["summaryLabels"] == [
                        "3 from this page",
                        "1 link here",
                    ]
                    assert expanded["counts"] == ["3", "1"]
                    assert "From this page" in expanded["text"]
                    assert "Links here" in expanded["text"]
                    panel.locator(
                        ".raya-connection-preview-rail summary",
                        has_text="Projection Residuals",
                    ).click()
                    graph_link = panel.locator(
                        '.raya-connection-preview-graph[href="../_raya/graph/index.html?page=reader-ux"]'
                    )
                    graph_href = graph_link.evaluate("node => node.href")
                    with page.expect_navigation():
                        graph_link.click()
                    assert page.url == graph_href
                    page.wait_for_selector(
                        "[data-raya-graph-detail-panel]:not([hidden])"
                    )
                    assert (
                        "Projection Residuals"
                        in page.locator("[data-raya-graph-detail-title]").inner_text()
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_article_page_connections_are_visible_and_static(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        assert handle.base_url is not None
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                for viewport in (
                    {"width": 1600, "height": 950},
                    {"width": 1366, "height": 900},
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    requested_urls: list[str] = []
                    page.on(
                        "request", lambda request: requested_urls.append(request.url)
                    )
                    try:
                        page.goto(
                            f"{handle.base_url}/authoring-matrix/index.html",
                            wait_until="networkidle",
                        )
                        requested_urls.clear()
                        block = page.locator(".raya-article-connections").first
                        assert block.is_visible()
                        assert page.locator(".raya-article-connections").count() == 1
                        block.scroll_into_view_if_needed()
                        _assert_intersects_viewport(page, ".raya-article-connections")
                        _assert_no_horizontal_overflow(page)
                        block_box = block.bounding_box()
                        article_box = page.locator(".raya-main-article").bounding_box()
                        sequence_box = page.locator(
                            ".raya-article-sequence"
                        ).bounding_box()
                        assert block_box is not None
                        assert article_box is not None
                        assert sequence_box is not None
                        assert block_box["width"] <= article_box["width"]
                        assert block_box["width"] > min(300, viewport["width"] - 32)
                        if viewport["width"] >= 1200:
                            assert abs(block_box["width"] - sequence_box["width"]) < 2
                        state = block.evaluate(
                            """(block) => {
                              const graphLink = block.querySelector('.raya-article-connections-graph');
                              return {
                                text: block.innerText,
                                counts: Array
                                  .from(block.querySelectorAll('.raya-article-connections-count'))
                                  .map((node) => node.innerText.trim()),
                                graphHref: graphLink?.getAttribute('href'),
                                sectionLabels: Array
                                  .from(block.querySelectorAll('.raya-article-connections-section h3'))
                                  .map((node) => node.innerText.trim()),
                                localStorageKeys: Object.keys(localStorage),
                                sessionStorageKeys: Object.keys(sessionStorage),
                              };
                            }"""
                        )
                        assert "Page connections" in state["text"]
                        assert "From this page" in state["sectionLabels"]
                        assert "Links here" in state["sectionLabels"]
                        assert state["counts"] == ["3", "1"]
                        assert (
                            state["graphHref"]
                            == "../_raya/graph/index.html?page=authoring-matrix"
                        )
                        assert "Math Authoring Fixture" in state["text"]
                        assert "Projection Residuals" in state["text"]
                        assert "recommend" not in state["text"].lower()
                        assert "progress" not in state["text"].lower()
                        assert "mastery" not in state["text"].lower()
                        assert state["localStorageKeys"] == []
                        assert state["sessionStorageKeys"] == []
                        preview = block.locator(
                            ".raya-connection-preview-article summary",
                            has_text="Math Authoring Fixture",
                        ).first
                        preview.click()
                        preview_state = block.evaluate(
                            """(block) => {
                              const details = Array
                                .from(block.querySelectorAll('.raya-connection-preview-article'))
                                .find((node) => node.querySelector('summary')?.innerText.includes('Math Authoring Fixture'));
                              return {
                                open: details?.open,
                                text: details?.innerText,
                                normalizedText: details?.innerText.replace(/\\s+/g, ' ').trim(),
                                openHref: details?.querySelector('.raya-connection-preview-open')?.getAttribute('href'),
                                graphHref: details?.querySelector('.raya-connection-preview-graph')?.getAttribute('href'),
                                localStorageKeys: Object.keys(localStorage),
                                sessionStorageKeys: Object.keys(sessionStorage),
                              };
                            }"""
                        )
                        assert preview_state["open"] is True
                        assert (
                            "Fixture page for current build-time MathJax authoring patterns."
                            in preview_state["text"]
                        )
                        assert "1 from this page" in preview_state["normalizedText"]
                        assert "2 links here" in preview_state["normalizedText"]
                        assert (
                            preview_state["openHref"] == "../math-authoring/index.html"
                        )
                        assert (
                            preview_state["graphHref"]
                            == "../_raya/graph/index.html?page=math-authoring"
                        )
                        assert "recommend" not in preview_state["text"].lower()
                        assert "progress" not in preview_state["text"].lower()
                        assert "mastery" not in preview_state["text"].lower()
                        assert preview_state["localStorageKeys"] == []
                        assert preview_state["sessionStorageKeys"] == []
                        assert requested_urls == []
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                    page.goto(
                        f"{handle.base_url}/reader-ux/index.html",
                        wait_until="networkidle",
                    )
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                    page.goto(
                        f"{handle.base_url}/reader-ux/index.html",
                        wait_until="networkidle",
                    )
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
                    assert stable["mapWidth"] >= 220
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                    page.goto(
                        f"{handle.base_url}/authoring-matrix/index.html",
                        wait_until="networkidle",
                    )
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        assert handle.base_url is not None
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1920, "height": 980})
                try:
                    page.goto(
                        f"{handle.base_url}/authoring-matrix/index.html",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(page)
                    chrome = page.evaluate(
                        """() => {
                          const rgb = (value) => value.match(/\\d+/g).slice(0, 3).map(Number);
                          const luminance = (value) => {
                            const [r, g, b] = rgb(value).map((channel) => channel / 255);
                            return 0.2126 * r + 0.7152 * g + 0.0722 * b;
                          };
                          const shadowAlpha = (value) => {
                            if (!value || value === 'none') return 0;
                            const rgba = value.match(/rgba?\\(([^)]+)\\)/);
                            if (!rgba) return 1;
                            const parts = rgba[1].split(',').map((part) => part.trim());
                            return parts.length >= 4 ? Number(parts[3]) : 1;
                          };
                          const topBar = document.querySelector('.raya-top-command-bar');
                          const article = document.querySelector('article.raya-main-article');
                          const firstParagraph = document.querySelector('article.raya-main-article > p');
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
                            paragraphWidth: firstParagraph.getBoundingClientRect().width,
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
                            courseMapShadow: courseMapStyle.boxShadow,
                            railShadow: railStyle.boxShadow,
                            courseMapShadowAlpha: shadowAlpha(courseMapStyle.boxShadow),
                            railShadowAlpha: shadowAlpha(railStyle.boxShadow),
                            topBarLuminance: luminance(topBarStyle.backgroundColor),
                            pageLuminance: luminance(bodyStyle.backgroundColor),
                          };
                        }"""
                    )
                    page.click(".raya-course-map-toggle")
                    page.click("[data-raya-learning-rail-collapse]")
                    page.wait_for_function(
                        """() => document.documentElement.dataset.rayaCourseMap === 'collapsed'
                          && document.documentElement.dataset.rayaLearningRail === 'collapsed'"""
                    )
                    page.wait_for_function(
                        """() => document.querySelector('nav.raya-course-map')
                          ?.getBoundingClientRect().width <= 82
                          && document.querySelector('aside.raya-learning-rail')
                          ?.getBoundingClientRect().width <= 64"""
                    )
                    collapsed = page.evaluate(
                        """() => {
                          const map = document.querySelector('nav.raya-course-map');
                          const rail = document.querySelector('aside.raya-learning-rail');
                          const mapToggle = document.querySelector('#raya-course-map .raya-course-map-toggle');
                          const railExpand = document.querySelector('[data-raya-learning-rail-expand]');
                          return {
                            mapWidth: map.getBoundingClientRect().width,
                            railWidth: rail.getBoundingClientRect().width,
                            mapLabel: getComputedStyle(mapToggle, '::after').content,
                            railLabel: getComputedStyle(railExpand, '::after').content,
                            mapAriaLabel: mapToggle.getAttribute('aria-label'),
                            railAriaLabel: railExpand.getAttribute('aria-label'),
                            mapToggleWidth: mapToggle.getBoundingClientRect().width,
                            railExpandWidth: railExpand.getBoundingClientRect().width,
                          };
                        }"""
                    )
                    storage_state = page.evaluate(
                        """() => ({
                          localKeys: Object.keys(window.localStorage),
                          sessionKeys: Object.keys(window.sessionStorage),
                        })"""
                    )
                    compact_links = page.evaluate(
                        """() => Array
                          .from(document.querySelectorAll('#raya-course-map a[href]'))
                          .filter((link) => link.getClientRects().length > 0)
                          .map((link) => {
                            const box = link.getBoundingClientRect();
                            link.focus();
                            return {
                              href: link.getAttribute('href'),
                              width: box.width,
                              height: box.height,
                              focused: document.activeElement === link,
                            };
                          })"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert chrome["shellWidth"] > 1700
    assert chrome["articleWidth"] >= 980
    assert chrome["articleWidth"] > chrome["mapWidth"] * 3
    assert chrome["articleWidth"] > chrome["railWidth"] * 3
    assert chrome["paragraphWidth"] >= 1000
    assert chrome["paragraphWidth"] <= 1120
    assert 180 <= chrome["mapWidth"] <= 280
    assert 200 <= chrome["railWidth"] <= 320
    assert (
        chrome["courseMapShadow"] == "none" or chrome["courseMapShadowAlpha"] <= 0.04
    )
    assert chrome["railShadow"] == "none" or chrome["railShadowAlpha"] <= 0.04
    assert chrome["topBarLuminance"] < chrome["pageLuminance"] - 0.35
    assert chrome["topBarBackground"] != chrome["bodyBackground"]
    assert chrome["topBarText"] != chrome["topBarBackground"]
    assert chrome["courseMapBackground"] != chrome["articleBackground"]
    assert chrome["railBackground"] != chrome["articleBackground"]
    assert chrome["courseMapButtonVisible"] is True
    assert chrome["fontButtonVisible"] is True
    assert collapsed["mapWidth"] <= 82
    assert collapsed["railWidth"] <= 64
    assert collapsed["mapLabel"] == '"Nav"'
    assert collapsed["railLabel"] == '"Info"'
    assert collapsed["mapAriaLabel"] == "Expand course map"
    assert collapsed["railAriaLabel"] == "Show learning context"
    assert collapsed["mapToggleWidth"] >= 40
    assert collapsed["railExpandWidth"] >= 40
    assert storage_state["localKeys"] == []
    assert storage_state["sessionKeys"] == []
    assert compact_links
    assert all(
        not link["href"].startswith(("http://", "https://"))
        for link in compact_links
    )
    assert all(link["width"] > 0 for link in compact_links)
    assert all(link["height"] >= 24 for link in compact_links)
    assert all(link["focused"] for link in compact_links)


def test_render_fixture_responsive_shell_state_remains_accessible(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                    page.goto(
                        f"{handle.base_url}/reader-ux/index.html",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(page)
                    page.focus("#raya-learning-rail a")
                    page.keyboard.press("Escape")
                    mobile_state = page.evaluate(
                        """() => {
                          const root = document.documentElement;
                          const rail = document.querySelector('#raya-learning-rail');
                          const body = document.querySelector('#raya-learning-rail-body');
                          const collapse = document.querySelector('[data-raya-learning-rail-collapse]');
                          const expand = document.querySelector('[data-raya-learning-rail-expand]');
                          return {
                            rootState: root.dataset.rayaLearningRail,
                            railState: rail?.dataset.rayaLearningRail,
                            bodyHidden: body?.getAttribute('aria-hidden'),
                            bodyInert: body?.inert,
                            bodyDisplay: body ? getComputedStyle(body).display : '',
                            collapseVisible: !!collapse && getComputedStyle(collapse).display !== 'none',
                            expandVisible: !!expand && getComputedStyle(expand).display !== 'none',
                          };
                        }"""
                    )
                    assert mobile_state["rootState"] == "expanded"
                    assert mobile_state["railState"] == "expanded"
                    assert mobile_state["bodyHidden"] == "false"
                    assert mobile_state["bodyInert"] is False
                    assert mobile_state["bodyDisplay"] != "none"
                    assert mobile_state["collapseVisible"] is False
                    assert mobile_state["expandVisible"] is False

                    page.set_viewport_size({"width": 1180, "height": 900})
                    page.wait_for_timeout(100)
                    _assert_no_horizontal_overflow(page)
                    tablet = page.evaluate(
                        """() => {
                          const article = document.querySelector('article.raya-main-article');
                          const map = document.querySelector('nav.raya-course-map');
                          const rail = document.querySelector('aside.raya-learning-rail');
                          const body = document.querySelector('#raya-learning-rail-body');
                          return {
                            articleY: article.getBoundingClientRect().y,
                            mapY: map.getBoundingClientRect().y,
                            railY: rail.getBoundingClientRect().y,
                            drawerState: document.documentElement.dataset.rayaCourseMapDrawer,
                            mapHidden: map.getAttribute('aria-hidden'),
                            mapInert: map.inert,
                            bodyHidden: body.getAttribute('aria-hidden'),
                            bodyInert: body.inert,
                          };
                        }"""
                    )
                    assert tablet["articleY"] < tablet["railY"]
                    assert tablet["drawerState"] == "closed"
                    assert tablet["mapHidden"] == "true"
                    assert tablet["mapInert"] is True
                    assert tablet["bodyHidden"] == "false"
                    assert tablet["bodyInert"] is False

                    page.set_viewport_size({"width": 1440, "height": 950})
                    page.wait_for_timeout(100)
                    page.click("[data-raya-learning-rail-collapse]")
                    page.wait_for_function(
                        "() => document.documentElement.dataset.rayaLearningRail === 'collapsed'"
                    )
                    page.set_viewport_size({"width": 390, "height": 844})
                    page.wait_for_function(
                        "() => document.documentElement.dataset.rayaLearningRail === 'expanded'"
                    )
                    restored = page.evaluate(
                        """() => {
                          const body = document.querySelector('#raya-learning-rail-body');
                          return {
                            bodyHidden: body.getAttribute('aria-hidden'),
                            bodyInert: body.inert,
                          };
                        }"""
                    )
                    assert restored["bodyHidden"] == "false"
                    assert restored["bodyInert"] is False
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_reader_ux_is_learning_showcase(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                    requested_urls: list[str] = []
                    page.on("request", lambda request: requested_urls.append(request.url))
                    page.goto(
                        f"{handle.base_url}/reader-ux/index.html",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(page)
                    assert requested_urls
                    assert all(
                        url.startswith(f"{handle.base_url}/")
                        for url in requested_urls
                    )
                    assert page.locator("h1").inner_text() == "Projection Residuals"
                    article_text = page.locator("article.raya-main-article").inner_text()
                    assert (
                        "What remains after projecting a vector onto a line?"
                        in article_text
                    )
                    assert "Try this first" in article_text
                    assert "Misconception" in article_text
                    assert (
                        "Reader UX fixture"
                        not in page.locator(".raya-page-brief").inner_text()
                    )
                    assert page.locator(
                        'img[alt="Projection residual diagram"]'
                    ).is_visible()
                    assert page.locator("#raya-official-practice").is_visible()
                    assert page.locator(".raya-official-object").count() >= 2
                    assert page.locator(
                        'a[href="../_raya/practice/index.html?page=reader-ux"]'
                    ).count() >= 1
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                    page.goto(
                        f"{handle.base_url}/reader-ux/index.html",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(page)
                    topbar = _bounding_box(page, ".raya-top-command-bar")
                    assert topbar["height"] <= 220
                    article = _bounding_box(page, "article.raya-main-article")
                    rail = _bounding_box(page, "aside.raya-learning-rail")
                    assert article["y"] < rail["y"]
                    assert not page.locator(
                        "#raya-course-map .raya-course-map-toggle"
                    ).is_visible()
                    assert (
                        page.locator(".raya-command-map").first.get_attribute(
                            "aria-expanded"
                        )
                        == "false"
                    )
                    closed_drawer = page.evaluate(
                        """() => ({
                          mapState: document.documentElement.dataset.rayaCourseMap,
                          drawerState: document.documentElement.dataset.rayaCourseMapDrawer,
                          mapHidden: document.querySelector('#raya-course-map')
                            ?.getAttribute('aria-hidden'),
                          mapInert: document.querySelector('#raya-course-map')?.inert,
                          mapTabIndex: document.querySelector('#raya-course-map')
                            ?.getAttribute('tabindex'),
                          linkTabIndexes: Array.from(document.querySelectorAll('#raya-course-map a'))
                            .map((link) => link.getAttribute('tabindex')),
                        })"""
                    )
                    assert closed_drawer["mapState"] == "expanded"
                    assert closed_drawer["drawerState"] == "closed"
                    assert closed_drawer["mapHidden"] == "true"
                    assert closed_drawer["mapInert"] is True
                    assert closed_drawer["mapTabIndex"] == "-1"
                    assert closed_drawer["linkTabIndexes"]
                    assert set(closed_drawer["linkTabIndexes"]) == {"-1"}

                    page.click(".raya-command-map")
                    page.wait_for_function(
                        """() => document.documentElement.dataset.rayaCourseMapDrawer === 'open'"""
                    )
                    assert (
                        page.locator(".raya-command-map").first.get_attribute(
                            "aria-expanded"
                        )
                        == "true"
                    )
                    _assert_no_horizontal_overflow(page)
                    opened_drawer = page.evaluate(
                        """() => ({
                          drawerState: document.documentElement.dataset.rayaCourseMapDrawer,
                          mapHidden: document.querySelector('#raya-course-map')
                            ?.getAttribute('aria-hidden'),
                          mapInert: document.querySelector('#raya-course-map')?.inert,
                          mapBox: (() => {
                            const box = document.querySelector('#raya-course-map')
                              ?.getBoundingClientRect();
                            return box ? { x: box.x, width: box.width, height: box.height } : null;
                          })(),
                          linkTabIndexes: Array.from(document.querySelectorAll('#raya-course-map a'))
                            .map((link) => link.getAttribute('tabindex')),
                        })"""
                    )
                    assert opened_drawer["drawerState"] == "open"
                    assert opened_drawer["mapHidden"] == "false"
                    assert opened_drawer["mapInert"] is False
                    assert opened_drawer["mapBox"]["x"] == 0
                    assert opened_drawer["mapBox"]["width"] >= 300
                    assert opened_drawer["mapBox"]["height"] >= 600
                    assert set(opened_drawer["linkTabIndexes"]) == {None}

                    page.keyboard.press("Shift+Tab")
                    reverse_trap = page.evaluate(
                        """() => ({
                          activeInsideMap: document
                            .querySelector('#raya-course-map')
                            ?.contains(document.activeElement),
                          activeText: document.activeElement?.textContent?.trim() || '',
                        })"""
                    )
                    assert reverse_trap["activeInsideMap"] is True
                    assert reverse_trap["activeText"]

                    for _ in range(12):
                        page.keyboard.press("Tab")
                        tab_state = page.evaluate(
                            """() => ({
                              drawerState: document.documentElement.dataset.rayaCourseMapDrawer,
                              activeInsideMap: document
                                .querySelector('#raya-course-map')
                                ?.contains(document.activeElement),
                              activeInCommandBar: !!document.activeElement
                                ?.closest('.raya-top-command-bar'),
                              activeInArticle: !!document.activeElement
                                ?.closest('article.raya-main-article'),
                              activeInRail: !!document.activeElement
                                ?.closest('#raya-learning-rail'),
                            })"""
                        )
                        assert tab_state == {
                            "drawerState": "open",
                            "activeInsideMap": True,
                            "activeInCommandBar": False,
                            "activeInArticle": False,
                            "activeInRail": False,
                        }

                    page.keyboard.press("Escape")
                    page.wait_for_function(
                        """() => document.documentElement.dataset.rayaCourseMapDrawer === 'closed'"""
                    )
                    escaped_drawer = page.evaluate(
                        """() => ({
                          drawerState: document.documentElement.dataset.rayaCourseMapDrawer,
                          mapHidden: document.querySelector('#raya-course-map')
                            ?.getAttribute('aria-hidden'),
                          mapInert: document.querySelector('#raya-course-map')?.inert,
                          commandFocused: document.activeElement?.classList
                            ?.contains('raya-command-map'),
                          railBodyHidden: document.querySelector('#raya-learning-rail-body')
                            ?.getAttribute('aria-hidden'),
                          railBodyInert: document.querySelector('#raya-learning-rail-body')?.inert,
                          linkTabIndexes: Array.from(document.querySelectorAll('#raya-course-map a'))
                            .map((link) => link.getAttribute('tabindex')),
                        })"""
                    )
                    assert escaped_drawer["linkTabIndexes"]
                    assert set(escaped_drawer.pop("linkTabIndexes")) == {"-1"}
                    assert escaped_drawer == {
                        "drawerState": "closed",
                        "mapHidden": "true",
                        "mapInert": True,
                        "commandFocused": True,
                        "railBodyHidden": "false",
                        "railBodyInert": False,
                    }

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


def test_preview_reader_page_brief_is_visible_static_and_responsive(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "minimal"
    shutil.copytree(MINIMAL, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    requested_urls: list[str] = []
                    page.on(
                        "request", lambda request: requested_urls.append(request.url)
                    )
                    try:
                        page.goto(
                            f"{handle.base_url}/unit/topic/index.html",
                            wait_until="networkidle",
                        )
                        assert requested_urls
                        assert all(
                            url.startswith(f"{handle.base_url}/")
                            for url in requested_urls
                        )
                        _assert_no_horizontal_overflow(page)
                        brief = page.locator(".raya-page-brief")
                        assert brief.is_visible()
                        assert (
                            brief.locator("#raya-page-brief-title").inner_text()
                            == "At a glance"
                        )
                        text = brief.inner_text()
                        assert (
                            "Fixture topic connected to official study objects." in text
                        )
                        assert "ready" in text
                        assert "Page 3 of 3" in text
                        assert "3 official practice objects" in text
                        assert "recommend" not in text.lower()
                        assert "progress" not in text.lower()
                        assert "mastery" not in text.lower()
                        practice_href = brief.locator(
                            'a[href="#raya-official-practice"]'
                        ).get_attribute("href")
                        assert practice_href == "#raya-official-practice"
                        box = brief.bounding_box()
                        assert box is not None
                        assert box["width"] <= viewport["width"]
                        if viewport["width"] <= 480:
                            assert box["y"] < viewport["height"]
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_preview_reader_print_view_is_static_handout(tmp_path: Path) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                        f"{handle.base_url}/reader-ux/index.html",
                        wait_until="networkidle",
                    )
                    requested_urls.clear()
                    page.emulate_media(media="print")
                    assert page.locator(".raya-main-article").is_visible()
                    assert page.locator(".raya-page-brief").is_visible()
                    assert (
                        page.locator(".raya-top-command-bar").evaluate(
                            "node => getComputedStyle(node).display"
                        )
                        == "none"
                    )
                    assert (
                        page.locator(".raya-course-map").evaluate(
                            "node => getComputedStyle(node).display"
                        )
                        == "none"
                    )
                    assert (
                        page.locator(".raya-learning-rail").evaluate(
                            "node => getComputedStyle(node).display"
                        )
                        == "none"
                    )
                    assert page.locator("mjx-container").first.is_visible()
                    assert page.locator("table").first.is_visible()
                    assert page.locator(".raya-static-environment").first.is_visible()
                    break_inside = page.locator(
                        ".raya-static-environment"
                    ).first.evaluate("node => getComputedStyle(node).breakInside")
                    assert break_inside in {"avoid", "avoid-page"}
                    assert (
                        page.locator(".raya-static-environment:not([open])").count()
                        == 0
                    )
                    assert page.locator(
                        ".raya-static-environment[open] "
                        ".raya-static-environment-body"
                    ).first.is_visible()
                    page.emulate_media(media="screen")
                    page.wait_for_function(
                        "() => document.querySelectorAll('.raya-static-environment:not([open])').length > 0"
                    )
                    assert (
                        page.locator(
                            ".raya-static-environment[data-raya-print-opened]"
                        ).count()
                        == 0
                    )
                    assert requested_urls == []

                    page.goto(
                        f"{handle.base_url}/static-path/index.html",
                        wait_until="networkidle",
                    )
                    requested_urls.clear()
                    page.emulate_media(media="print")
                    assert page.locator("pre code").first.is_visible()
                    assert (
                        page.locator(".raya-code-copy").first.evaluate(
                            "node => getComputedStyle(node).display"
                        )
                        == "none"
                    )
                    assert (
                        page.locator(".raya-course-map").evaluate(
                            "node => getComputedStyle(node).display"
                        )
                        == "none"
                    )
                    assert requested_urls == []

                    page.goto(
                        f"{handle.base_url}/_raya/graph/index.html",
                        wait_until="networkidle",
                    )
                    requested_urls.clear()
                    page.emulate_media(media="print")
                    assert page.locator(".raya-graph-list-panel").is_visible()
                    assert page.locator("#raya-graph-list").is_visible()
                    assert (
                        page.locator(".raya-graph-canvas").evaluate(
                            "node => getComputedStyle(node).display"
                        )
                        == "none"
                    )
                    assert (
                        page.locator(".raya-graph-inspector-panel").evaluate(
                            "node => getComputedStyle(node).display"
                        )
                        == "none"
                    )
                    assert requested_urls == []
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
    shutil.copytree(
        REFERENCE_FIXTURE, course, ignore=shutil.ignore_patterns("artifact")
    )

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        base_url = handle.base_url
        assert base_url is not None
        root_html = _fetch_text(f"{base_url}/index.html")
        inspection_html = _fetch_text(f"{base_url}/_raya/inspect/index.html")
        css = _fetch_text(f"{base_url}/_raya/render/rich.css")
    finally:
        handle.close()

    assert (
        '<header class="raya-top-command-bar" aria-label="Course tools">' in root_html
    )
    assert (
        '<a class="raya-skip-link" href="#raya-article">Skip to content</a>'
        in root_html
    )
    assert (
        '<main id="raya-content" class="raya-learning-shell" data-raya-course-map="expanded">'
        in root_html
    )
    assert (
        '<article id="raya-article" class="raya-main-article" tabindex="-1">'
        in root_html
    )
    assert (
        '<aside id="raya-learning-rail" class="raya-learning-rail" '
        'aria-label="Learning context" data-raya-learning-rail="expanded">'
    ) in root_html
    assert root_html.index(
        '<nav id="raya-course-map" class="raya-course-map"'
    ) < root_html.index('<article id="raya-article"')
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
    assert "@media (max-width: 1279px)" in css
    assert "overflow-wrap: anywhere" in css


def test_examples_gallery_has_reviewable_responsive_fixture_cards() -> None:
    with _serve(EXAMPLES_GALLERY.parent) as base_url:
        gallery_html = _fetch_text(f"{base_url}/gallery/index.html")

    assert "fixture material" in gallery_html
    assert (
        "Foundation docs and accepted OpenSpec specs remain the authority"
        in gallery_html
    )
    assert (
        '<section class="gallery-grid" aria-label="Fixture previews">' in gallery_html
    )
    assert "../courses/minimal/artifact/site/index.html" in gallery_html
    assert "../courses/minimal/artifact/site/_raya/inspect/index.html" in gallery_html
    assert (
        "../courses/execution-fixture/artifact/site/_raya/inspect/index.html"
        in gallery_html
    )
    assert "@media (max-width: 720px)" in gallery_html
    assert "overflow-wrap: anywhere" in gallery_html


def test_rendered_surfaces_have_no_obvious_layout_overlap_at_viewports(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "reference-fixture"
    shutil.copytree(
        REFERENCE_FIXTURE, course, ignore=shutil.ignore_patterns("artifact")
    )
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                    for viewport in (
                        {"width": 1280, "height": 900},
                        {"width": 390, "height": 844},
                    ):
                        page = browser.new_page(viewport=viewport)
                        try:
                            page.goto(
                                f"{base_url}/index.html", wait_until="networkidle"
                            )
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
                            assert page.locator(
                                "main.raya-inspection-main"
                            ).bounding_box()

                            for workspace_path in (
                                "_raya/search/index.html",
                                "_raya/graph/index.html",
                                "_raya/practice/index.html",
                                "_raya/tasks/index.html",
                                "_raya/schedule/index.html",
                            ):
                                page.goto(
                                    f"{base_url}/{workspace_path}",
                                    wait_until="networkidle",
                                )
                                _assert_no_horizontal_overflow(page)

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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
        "Projection Residuals",
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
    assert any(
        "Solution sketch of Activity 4.1" in text for text in probe["proofTexts"]
    )
    assert probe["staticEnvironmentCount"] >= 4
    assert (
        "raya-static-environment-hint-orthogonal-activity"
        in probe["staticEnvironmentIds"]
    )
    assert (
        "raya-static-environment-solution-orthogonal-activity"
        in probe["staticEnvironmentIds"]
    )
    assert (
        "raya-static-environment-answer-orthogonal-activity"
        in probe["staticEnvironmentIds"]
    )
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
                    assert closed_probe["summaryText"].startswith(
                        "Hint for Activity 4.1"
                    )
                    assert closed_probe["bodyHeight"] == 0
                    assert (
                        "Compare the projection formula"
                        in closed_probe["bodyTextContent"]
                    )
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
    assert all(capture["horizontal_overflow"] <= 1 for capture in summary["captures"])
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
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
        if capture["page"] == "reader-ux" and capture["viewport"]["name"] == "desktop"
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
        if capture["page"] == "reader-ux" and capture["viewport"]["name"] == "mobile"
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
        urljoin(page_url, href) for href in _stylesheet_hrefs(html) if href_part in href
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
        rel_values = {value.lower() for value in attributes.get("rel", "").split()}
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


def _add_official_task_objects(course: Path) -> None:
    official_dir = course / "course" / "1_unit" / "1_topic" / "_official"
    assignment_dir = official_dir / "assignments"
    project_dir = official_dir / "projects"
    exam_dir = official_dir / "exams"
    task_dir = official_dir / "tasks"
    for directory in (assignment_dir, project_dir, exam_dir, task_dir):
        directory.mkdir(parents=True, exist_ok=True)
    (assignment_dir / "1_assignment.yaml").write_text(
        "\n".join(
            [
                "id: unit-assignment",
                "type: assignment",
                "authority: official",
                "scope:",
                "  quantum: first-topic",
                "content:",
                "  title: Problem Set 1",
                "  instructions: Practice matrix multiplication and write one retrieval reflection.",
                "  due: '2026-09-15'",
                "  points: 10 pts",
                "  weight: 15%",
                "  status: published",
                "  tags:",
                "    - linear algebra",
                "    - retrieval",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (project_dir / "1_project.yaml").write_text(
        "\n".join(
            [
                "id: unit-project",
                "type: project",
                "authority: official",
                "scope:",
                "  quantum: first-topic",
                "content:",
                "  title: Build a retrieval plan",
                "  summary: Draft a short retrieval plan for reviewing the first unit.",
                "  due: '2026-10-01'",
                "  tags:",
                "    - planning",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (exam_dir / "1_exam.yaml").write_text(
        "\n".join(
            [
                "id: unit-exam",
                "type: exam",
                "authority: official",
                "scope:",
                "  quantum: first-topic",
                "content:",
                "  title: Unit checkpoint",
                "  instructions: Use the official page context before starting.",
                "  available: '2026-10-15'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (task_dir / "1_task.yaml").write_text(
        "\n".join(
            [
                "id: unit-task",
                "type: task",
                "authority: official",
                "scope:",
                "  quantum: first-topic",
                "content:",
                "  title: Prepare one question",
                "  prompt: Bring one precise question about projections.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (task_dir / "2_private_task.yaml").write_text(
        "\n".join(
            [
                "id: private-task",
                "type: task",
                "authority: official",
                "scope:",
                "  quantum: first-topic",
                "content:",
                "  title:",
                "    answer: Private support sentinel",
                "  instructions:",
                "    prompt: Public nested prompt should not be flattened.",
                "    solution: SHOULD_NOT_LEAK_TASK_SOLUTION",
                "  body:",
                "    answer: SHOULD_NOT_LEAK_TASK_ANSWER",
                "  due: '2026-11-01'",
                "  tags:",
                "    - public",
                "    - hidden: SHOULD_NOT_LEAK_TASK_TAG",
                "",
            ]
        ),
        encoding="utf-8",
    )


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
