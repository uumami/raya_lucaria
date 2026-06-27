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


def _visible_graph_label_bounds(page) -> list[dict]:
    return page.locator("#raya-graph-canvas").evaluate(
        """(svg) => {
          const svgBox = svg.getBoundingClientRect();
          return Array.from(svg.querySelectorAll('.raya-graph-node-label'))
            .filter((label) => {
              const style = getComputedStyle(label);
              return style.visibility !== 'hidden' && Number(style.opacity) > 0;
            })
            .map((label) => {
              const box = label.getBoundingClientRect();
              return {
                text: label.textContent.trim(),
                left: box.left,
                right: box.right,
                svgLeft: svgBox.left,
                svgRight: svgBox.right,
              };
            });
        }"""
    )


def _assert_visible_graph_labels_inside_canvas(page) -> None:
    visible_label_bounds = _visible_graph_label_bounds(page)
    assert visible_label_bounds
    assert all(
        label["left"] >= label["svgLeft"] - 1
        and label["right"] <= label["svgRight"] + 1
        for label in visible_label_bounds
    )


def _click_graph_node_group(page, node_id: str, *, click_count: int = 1) -> None:
    node = page.locator(
        f'#raya-graph-canvas [data-raya-graph-node="{node_id}"] '
        ".raya-graph-node-hit"
    )
    node.scroll_into_view_if_needed()
    box = node.bounding_box()
    assert box is not None
    x = box["x"] + box["width"] / 2
    y = box["y"] + box["height"] / 2
    assert (
        page.evaluate(
            """([x, y, nodeId]) => document
              .elementFromPoint(x, y)
              ?.closest("[data-raya-graph-node]")
              ?.getAttribute("data-raya-graph-node") === nodeId""",
            [x, y, node_id],
        )
        is True
    )
    if click_count == 2:
        page.mouse.click(x, y, click_count=2)
    else:
        page.mouse.click(x, y)


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


def test_graph_workspace_renders_selected_detail_navigator(
    tmp_path: Path,
) -> None:
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        assert handle.base_url is not None
        graph_html = _fetch_text(f"{handle.base_url}/_raya/graph/index.html")

        assert "data-raya-graph-detail-nav" in graph_html
        for target, label in (
            ("summary", "Summary"),
            ("relationships", "Relationships"),
            ("study", "Study"),
            ("sequence", "Sequence"),
            ("links", "Links"),
        ):
            assert (
                '<button type="button" class="raya-graph-detail-nav-button" '
                f'data-raya-graph-detail-nav-target="{target}">{label}</button>'
            ) in graph_html
    finally:
        handle.close()


def test_preview_reader_official_quiz_renders_page_local_controls(
    tmp_path: Path,
) -> None:
    from raya_cli.preview import create_preview

    course = tmp_path / "minimal"
    shutil.copytree(MINIMAL, course, ignore=shutil.ignore_patterns("artifact"))

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [
            diagnostic.format() for diagnostic in handle.report.diagnostics
        ]
        assert handle.base_url is not None
        html_text = _fetch_text(f"{handle.base_url}/unit/topic/index.html")

        assert 'data-raya-official-quiz-state="ready"' in html_text
        assert '<button type="button" class="raya-official-option"' in html_text
        assert "data-raya-official-quiz-option" in html_text
        assert 'data-raya-official-quiz-correct="true"' in html_text
        assert "data-raya-official-quiz-feedback" in html_text
        assert (
            '<button type="button" class="raya-official-quiz-reset" '
            "data-raya-official-quiz-reset hidden>"
        ) in html_text
        assert "<summary>Reveal correct option</summary>" in html_text
    finally:
        handle.close()


def test_preview_reader_official_quiz_checks_and_resets_locally(
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
        shell_js = _fetch_text(f"{handle.base_url}/_raya/render/shell.js")
        assert "fetch(" not in shell_js
        assert "XMLHttpRequest" not in shell_js
        assert "localStorage" not in shell_js
        assert "sessionStorage" not in shell_js

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
                    quiz = page.locator("#raya-official-first-topic-quiz")
                    question = quiz.locator(
                        "[data-raya-official-quiz-question]"
                    ).first
                    wrong = question.locator(
                        "[data-raya-official-quiz-option]"
                        '[data-raya-official-quiz-correct="false"]'
                    ).first
                    correct = question.locator(
                        "[data-raya-official-quiz-option]"
                        '[data-raya-official-quiz-correct="true"]'
                    ).first
                    reset = question.locator("[data-raya-official-quiz-reset]")
                    feedback = question.locator(
                        "[data-raya-official-quiz-feedback]"
                    )

                    assert (
                        question.get_attribute("data-raya-official-quiz-state")
                        == "ready"
                    )
                    wrong.click()
                    assert (
                        question.get_attribute("data-raya-official-quiz-state")
                        == "answered"
                    )
                    assert (
                        wrong.get_attribute("data-raya-official-quiz-result")
                        == "incorrect"
                    )
                    assert (
                        correct.get_attribute("data-raya-official-quiz-result")
                        == "correct"
                    )
                    assert "Try again" in feedback.inner_text()
                    assert reset.is_visible()

                    reset.click()
                    assert (
                        question.get_attribute("data-raya-official-quiz-state")
                        == "ready"
                    )
                    assert wrong.get_attribute("data-raya-official-quiz-result") is None
                    assert (
                        correct.get_attribute("data-raya-official-quiz-result")
                        is None
                    )

                    correct.click()
                    assert (
                        question.get_attribute("data-raya-official-quiz-state")
                        == "answered"
                    )
                    assert (
                        correct.get_attribute("data-raya-official-quiz-result")
                        == "correct"
                    )
                    assert "Correct." in feedback.inner_text()
                    reset.click()
                    assert (
                        question.get_attribute("data-raya-official-quiz-state")
                        == "ready"
                    )
                    assert (
                        correct.get_attribute("data-raya-official-quiz-result")
                        is None
                    )
                    assert requested_urls == []
                    assert page.evaluate("() => localStorage.length") == 0
                    assert page.evaluate("() => sessionStorage.length") == 0
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
                    {"width": 820, "height": 900},
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


def test_render_fixture_local_images_open_static_asset_inspector(
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
                    page.goto(f"{base_url}/index.html", wait_until="networkidle")
                    _assert_no_horizontal_overflow(page)
                    inspect = page.locator("[data-raya-asset-inspect]").first
                    assert inspect.is_visible()
                    assert inspect.get_attribute("aria-haspopup") == "dialog"
                    inspect.click()

                    dialog = page.locator("[data-raya-asset-inspector]")
                    assert dialog.is_visible()
                    assert dialog.get_attribute("aria-hidden") == "false"
                    assert (
                        dialog.locator("[data-raya-asset-inspector-title]").inner_text()
                        == "Static path image fixture"
                    )
                    preview = dialog.locator("[data-raya-asset-inspector-image]")
                    assert preview.get_attribute("alt") == "Static path image fixture"
                    assert preview.get_attribute("src") == (
                        "_raya/assets/_source/_local/diagrams/static-path.svg"
                    )
                    assert (
                        dialog.locator("[data-raya-asset-inspector-open]")
                        .get_attribute("href")
                        == "_raya/assets/_source/_local/diagrams/static-path.svg"
                    )
                    assert external_requests == []

                    page.keyboard.press("Escape")
                    assert dialog.is_hidden()
                    assert dialog.get_attribute("aria-hidden") == "true"
                    assert page.evaluate(
                        "() => document.activeElement?.matches('[data-raya-asset-inspect]')"
                    )

                    inspect.click()
                    assert dialog.is_visible()
                    dialog.locator("[data-raya-asset-inspector-close]").click()
                    assert dialog.is_hidden()
                    assert page.evaluate(
                        "() => document.activeElement?.matches('[data-raya-asset-inspect]')"
                    )

                    inspect.click()
                    assert dialog.is_visible()
                    dialog.click(position={"x": 8, "y": 8})
                    assert dialog.is_hidden()
                    assert page.evaluate(
                        "() => document.activeElement?.matches('[data-raya-asset-inspect]')"
                    )
                finally:
                    page.close()
                mobile = browser.new_page(viewport={"width": 390, "height": 844})
                try:
                    mobile.goto(
                        f"{handle.base_url}/_raya/graph/index.html",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(mobile)
                    mobile.click('[data-raya-graph-toggle-panel="list"]')
                    mobile.click('[data-raya-graph-toggle-panel="inspector"]')
                    mobile.wait_for_function(
                        """() => {
                          const root = document.querySelector('[data-raya-graph-page]');
                          return root?.getAttribute('data-raya-graph-list-state') === 'collapsed'
                            && root?.getAttribute('data-raya-graph-inspector-state') === 'collapsed';
                        }"""
                    )
                    _assert_no_horizontal_overflow(mobile)
                    assert mobile.locator(
                        "[data-raya-graph-panel-body='list']"
                    ).is_hidden()
                    assert mobile.locator(
                        "[data-raya-graph-panel-body='inspector']"
                    ).is_hidden()
                    assert (
                        mobile.locator("[data-raya-graph-toggle-panel='list']")
                        .inner_text()
                        .strip()
                        == "Open"
                    )
                    assert (
                        mobile.locator("[data-raya-graph-toggle-panel='inspector']")
                        .inner_text()
                        .strip()
                        == "Open"
                    )
                finally:
                    mobile.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_section_landing_cards_are_static_navigation(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    root_source = course / "course" / "0_index.md"
    root_source.write_text(
        root_source.read_text(encoding="utf-8").replace(
            "# Raya Lucaria Render Fixture\n",
            "# Raya Lucaria Render Fixture\n\n"
            "## Course Index\n\n"
            "Authored heading that intentionally collides with the generated "
            "index label.\n",
            1,
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
                        generated_heading = page.locator(
                            "#raya-generated-course-index"
                        )
                        assert generated_heading.is_visible()
                        assert page.locator("#course-index").is_visible()
                        assert (
                            page.locator(
                                '.raya-page-toc a[href="#raya-generated-course-index"]'
                            ).count()
                            == 1
                        )
                        page.evaluate(
                            """() => {
                              document
                                .getElementById('raya-generated-course-index')
                                ?.scrollIntoView({ block: 'start' });
                              window.dispatchEvent(new Event('scroll'));
                            }"""
                        )
                        page.wait_for_function(
                            """() => document
                              .querySelector('.raya-page-toc a[aria-current="location"]')
                              ?.getAttribute('href') === '#raya-generated-course-index'"""
                        )
                        current_sections = page.evaluate(
                            """() => ({
                              rail: {
                                href: document
                                  .querySelector('.raya-current-section-link')
                                  ?.getAttribute('href'),
                                text: document
                                  .querySelector('.raya-current-section-link')
                                  ?.textContent
                                  ?.trim(),
                                label: document
                                  .querySelector('.raya-current-section-link')
                                  ?.getAttribute('aria-label') || '',
                              },
                              command: {
                                href: document
                                  .querySelector('.raya-reading-context-section')
                                  ?.getAttribute('href'),
                                text: document
                                  .querySelector('.raya-reading-context-section')
                                  ?.textContent
                                  ?.trim(),
                                visibleLabel: document
                                  .querySelector('.raya-reading-context-section-label')
                                  ?.textContent
                                  ?.trim(),
                                label: document
                                  .querySelector('.raya-reading-context-section')
                                  ?.getAttribute('aria-label') || '',
                              },
                            })"""
                        )
                        assert current_sections["rail"] == {
                            "href": "#course-index",
                            "text": "Course Index",
                            "label": "Course Index",
                        }
                        assert current_sections["command"] == {
                            "href": "#course-index",
                            "text": "Now Course Index",
                            "visibleLabel": "Course Index",
                            "label": "Current section: Course Index",
                        }
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
    from playwright.sync_api import expect, sync_playwright
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
                        assert page.locator(
                            '.raya-graph-toolbar-group[aria-label="Find pages"]'
                        ).is_visible()
                        assert page.locator(
                            '.raya-graph-toolbar-group[aria-label="Canvas view"]'
                        ).is_visible()
                        pan_boxes = page.locator(
                            "[data-raya-graph-pan]"
                        ).evaluate_all(
                            """buttons => buttons.map((button) => {
                              const box = button.getBoundingClientRect();
                              return {
                                width: box.width,
                                height: box.height,
                                text: button.textContent.trim(),
                              };
                            })"""
                        )
                        assert [item["text"] for item in pan_boxes] == [
                            "←",
                            "→",
                            "↑",
                            "↓",
                        ]
                        for item in pan_boxes:
                            assert item["width"] >= 34
                            assert item["height"] >= 34
                            assert abs(item["width"] - item["height"]) <= 12
                        reading_keys = page.locator("[data-raya-graph-reading-keys]")
                        assert reading_keys.is_visible()
                        reading_keys_box = reading_keys.bounding_box()
                        canvas_box = page.locator("#raya-graph-canvas").bounding_box()
                        orientation_box = page.locator(
                            "[data-raya-graph-orientation]"
                        ).bounding_box()
                        assert reading_keys_box is not None
                        assert canvas_box is not None
                        assert orientation_box is not None
                        assert reading_keys_box["y"] < canvas_box["y"]
                        assert reading_keys_box["y"] < orientation_box["y"]
                        assert reading_keys_box["height"] <= 140
                        assert reading_keys_box["y"] < viewport["height"]
                        assert (
                            reading_keys_box["y"] + reading_keys_box["height"]
                            <= viewport["height"]
                        )
                        for key in ("pages", "arrows", "selection", "filters"):
                            assert page.locator(
                                f'[data-raya-graph-reading-key="{key}"]'
                            ).is_visible()
                        reading_text = reading_keys.inner_text().lower()
                        for forbidden in (
                            "progress",
                            "mastery",
                            "ranking",
                            "recommendation",
                            "personalization",
                        ):
                            assert forbidden not in reading_text
                        graph_guide = page.locator("[data-raya-graph-guide]")
                        assert graph_guide.evaluate("node => node.tagName") == "DETAILS"
                        assert graph_guide.evaluate(
                            "node => node.hasAttribute('open')"
                        ) is False
                        expect(graph_guide.locator("summary")).to_be_visible()
                        expect(
                            graph_guide.locator(".raya-graph-guide-card").first
                        ).to_be_hidden()
                        graph_guide.locator("summary").click()
                        expect(
                            graph_guide.locator(".raya-graph-guide-card").first
                        ).to_be_visible()
                        assert page.locator(".raya-discovery-command-bar").is_visible()
                        assert page.locator(
                            ".raya-discovery-command-bar .raya-command-home"
                        ).is_visible()
                        graph_icons = page.evaluate(
                            """() => Object.fromEntries(
                              Array.from(
                                document.querySelectorAll(
                                  '.raya-discovery-command-bar .raya-command'
                                )
                              ).map((node) => [
                                Array.from(node.classList)
                                  .find((name) => name.startsWith('raya-command-')),
                                (() => {
                                  const icon = node.querySelector('.raya-command-icon');
                                  const labelNode = node.querySelector('.raya-command-label');
                                  const shape = icon?.querySelector('path, circle');
                                  return {
                                    iconCount: node.querySelectorAll('.raya-command-icon').length,
                                    iconBeforeLabel: !!icon && !!labelNode
                                      && !!(
                                        icon.compareDocumentPosition(labelNode)
                                        & Node.DOCUMENT_POSITION_FOLLOWING
                                      ),
                                    tagName: icon?.tagName,
                                    icon: icon?.getAttribute('data-raya-command-icon'),
                                    ariaHidden: icon?.getAttribute('aria-hidden'),
                                    focusable: icon?.getAttribute('focusable'),
                                    viewBox: icon?.getAttribute('viewBox'),
                                    label: labelNode?.textContent?.trim(),
                                    before: getComputedStyle(node, '::before').content,
                                    shapeFill: shape ? getComputedStyle(shape).fill : null,
                                    shapeStroke: shape ? getComputedStyle(shape).stroke : null,
                                  };
                                })()
                              ])
                            )"""
                        )
                        expected_graph_icons = {
                            "raya-command-home": ("home", "Course"),
                            "raya-command-search": ("search", "Search"),
                            "raya-command-practice": ("practice", "Practice"),
                            "raya-command-tasks": ("tasks", "Tasks"),
                            "raya-command-schedule": ("schedule", "Schedule"),
                            "raya-command-size": ("text-size", "Text size"),
                            "raya-command-font": ("font", "OpenDyslexic"),
                        }
                        for command_class, (icon_name, label) in expected_graph_icons.items():
                            icon = graph_icons[command_class]
                            assert icon["tagName"] == "svg"
                            assert icon["iconCount"] == 1
                            assert icon["iconBeforeLabel"] is True
                            assert icon["icon"] == icon_name
                            assert icon["ariaHidden"] == "true"
                            assert icon["focusable"] == "false"
                            assert icon["viewBox"] == "0 0 24 24"
                            assert icon["label"] == label
                            assert icon["before"] == "none"
                            if icon_name not in {"text-size", "font"}:
                                assert icon["shapeFill"] == "none"
                                assert icon["shapeStroke"] != "none"
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
                        if viewport["width"] < 1280:
                            assert (
                                page.locator("[data-raya-graph-page]").get_attribute(
                                    "data-raya-graph-list-state"
                                )
                                == "collapsed"
                            )
                            assert page.locator(
                                '[data-raya-graph-panel-rail-summary="list"]'
                            ).is_visible()
                            page.locator(
                                '[data-raya-graph-toggle-panel="list"]'
                            ).click()
                            expect(
                                page.locator('[data-raya-graph-panel-body="list"]')
                            ).to_have_attribute("aria-hidden", "false")
                            assert (
                                page.locator("[data-raya-graph-page]").get_attribute(
                                    "data-raya-graph-inspector-state"
                                )
                                == "collapsed"
                            )
                            assert page.locator(
                                '[data-raya-graph-panel-rail-summary="inspector"]'
                            ).is_visible()
                            page.locator(
                                '[data-raya-graph-toggle-panel="inspector"]'
                            ).click()
                            expect(
                                page.locator(
                                    '[data-raya-graph-panel-body="inspector"]'
                                )
                            ).to_have_attribute("aria-hidden", "false")
                        assert page.locator(".raya-graph-legend").is_visible()
                        assert page.locator(".raya-graph-workspace").is_visible()
                        assert page.locator(".raya-graph-map-panel").is_visible()
                        assert page.locator(".raya-graph-list-panel").is_visible()
                        list_card_probe = page.evaluate(
                            """() => {
                              const item = document.querySelector(
                                '#raya-graph-list [data-raya-graph-node="reader-ux"]'
                              );
                              const titleRow = item?.querySelector('.raya-graph-list-title-row');
                              const metrics = item?.querySelector('.raya-graph-list-metrics');
                              const summary = item?.querySelector('.raya-graph-list-summary');
                              const status = item?.querySelector('.raya-graph-list-status');
                              const box = (node) => {
                                const rect = node?.getBoundingClientRect();
                                return rect
                                  ? {
                                      top: rect.top,
                                      left: rect.left,
                                      width: rect.width,
                                      height: rect.height,
                                    }
                                  : null;
                              };
                              return {
                                titleRow: box(titleRow),
                                metrics: box(metrics),
                                summary: box(summary),
                                status: box(status),
                                titleDisplay: getComputedStyle(titleRow).display,
                                metricsDisplay: getComputedStyle(metrics).display,
                                summaryDisplay: getComputedStyle(summary).display,
                                statusText: status?.textContent?.trim(),
                                summaryText: summary?.textContent?.trim(),
                              };
                            }"""
                        )
                        assert list_card_probe["titleDisplay"] == "flex"
                        assert list_card_probe["metricsDisplay"] in {"flex", "grid"}
                        assert list_card_probe["summaryDisplay"] == "block"
                        assert list_card_probe["statusText"] == "ready"
                        assert "projection residuals" in list_card_probe["summaryText"]
                        assert (
                            list_card_probe["metrics"]["top"]
                            > list_card_probe["titleRow"]["top"]
                        )
                        assert (
                            list_card_probe["summary"]["top"]
                            > list_card_probe["metrics"]["top"]
                        )
                        assert list_card_probe["status"]["width"] >= 42
                        assert page.locator(".raya-graph-inspector-panel").is_visible()
                        preview = page.locator(
                            "[data-raya-graph-inspection-preview]"
                        )
                        assert preview.is_hidden()
                        assert (
                            page.locator("#graph-layout").input_value() == "connections"
                        )
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-layout"
                            )
                            == "connections"
                        )
                        if viewport["width"] < 1280:
                            continue
                        root_x, _ = _graph_node_translate(page, "render-root")
                        static_x, _ = _graph_node_translate(page, "static-path")
                        math_x, _ = _graph_node_translate(page, "math-authoring")
                        reader_x, _ = _graph_node_translate(page, "reader-ux")
                        matrix_x, _ = _graph_node_translate(page, "authoring-matrix")
                        assert root_x < static_x
                        assert root_x < reader_x
                        assert root_x < matrix_x
                        assert math_x < matrix_x
                        page.locator(
                            '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
                        ).focus()
                        page.wait_for_selector(
                            "[data-raya-graph-inspection-preview]:not([hidden])"
                        )
                        assert "Authoring Matrix Fixture" in preview.locator(
                            "[data-raya-graph-inspection-preview-title]"
                        ).inner_text()
                        assert (
                            "Combined fixture page for copyable authoring patterns"
                            in preview.locator(
                                "[data-raya-graph-inspection-preview-summary]"
                            ).inner_text()
                        )
                        assert "ready" in preview.locator(
                            "[data-raya-graph-inspection-preview-meta]"
                        ).inner_text().lower()
                        preview_counts = preview.locator(
                            "[data-raya-graph-inspection-preview-counts]"
                        ).inner_text()
                        assert "4 outgoing" in preview_counts
                        assert "2 incoming" in preview_counts
                        assert "4 connected" in preview_counts
                        assert page.locator("[data-raya-graph-detail-empty]").is_visible()
                        preview.locator(
                            "[data-raya-graph-inspection-preview-select]"
                        ).click()
                        page.wait_for_selector(
                            "[data-raya-graph-detail-panel]:not([hidden])"
                        )
                        assert "Authoring Matrix Fixture" in page.locator(
                            "[data-raya-graph-detail-title]"
                        ).inner_text()
                        assert preview.locator(
                            "[data-raya-graph-inspection-preview-open]"
                        ).get_attribute("href") == page.locator(
                            '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
                        ).get_attribute("href")
                        page.click("#graph-reset")
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-inspection-preview]')
                              ?.hasAttribute('hidden')"""
                        )
                        assert preview.is_hidden()
                        page.locator(
                            '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
                        ).focus()
                        page.wait_for_selector(
                            "[data-raya-graph-inspection-preview]:not([hidden])"
                        )
                        page.locator(
                            'section[aria-label="Graph groups"] '
                            '[data-raya-graph-group-filter="authoring-matrix"]'
                        ).dispatch_event("click")
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-inspection-preview]')
                              ?.hasAttribute('hidden')"""
                        )
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-preview-bubble]')
                              ?.hasAttribute('hidden')"""
                        )
                        assert preview.is_hidden()
                        assert page.locator(
                            "[data-raya-graph-preview-bubble]"
                        ).is_hidden()
                        page.wait_for_timeout(500)
                        assert preview.is_hidden()
                        assert page.locator(
                            "[data-raya-graph-preview-bubble]"
                        ).is_hidden()
                        assert (
                            page.locator("[data-raya-graph-hover-status]")
                            .inner_text()
                            .strip()
                            == ""
                        )
                        page.click(
                            'section[aria-label="Graph groups"] '
                            '[data-raya-graph-group-filter="authoring-matrix"]'
                        )
                        page.wait_for_selector(
                            '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
                        )
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
                        query_rows = page.locator(
                            "#raya-graph-list [data-raya-graph-node]:visible"
                        ).evaluate_all(
                            """rows => rows.map((row) => ({
                              id: row.getAttribute('data-raya-graph-node'),
                              isMatch: row.classList.contains('is-match'),
                              badge: row.querySelector('[data-raya-graph-list-search-role]')?.textContent?.trim() || '',
                              badgeHidden: row.querySelector('[data-raya-graph-list-search-role]')?.hidden ?? true,
                            }))"""
                        )
                        assert query_rows
                        first_context_index = next(
                            (
                                index
                                for index, row in enumerate(query_rows)
                                if not row["isMatch"]
                            ),
                            len(query_rows),
                        )
                        assert all(
                            row["isMatch"] for row in query_rows[:first_context_index]
                        )
                        assert all(
                            not row["isMatch"] for row in query_rows[first_context_index:]
                        )
                        assert [
                            row["id"] for row in query_rows if row["isMatch"]
                        ] == ["numbered-objects", "authoring-matrix"]
                        assert {
                            row["badge"] for row in query_rows if row["isMatch"]
                        } == {"Search match"}
                        assert {
                            row["badge"] for row in query_rows if not row["isMatch"]
                        } == {"Connected context"}
                        assert all(not row["badgeHidden"] for row in query_rows)
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
                        assert page.locator(
                            "#raya-graph-list [data-raya-graph-list-search-role]:visible"
                        ).count() == 0
                        restored_order = page.locator(
                            "#raya-graph-list [data-raya-graph-node]:visible"
                        ).evaluate_all(
                            """rows => {
                              const payload = JSON.parse(
                                document.getElementById('raya-graph-data').textContent
                              );
                              const orderById = new Map(
                                payload.nodes.map((node) => [
                                  node.id,
                                  Number(node.order || 0),
                                ])
                              );
                              const ids = rows.map((row) =>
                                row.getAttribute('data-raya-graph-node')
                              );
                              return {
                                firstId: ids[0],
                                courseOrdered: ids.every((id, index) =>
                                  index === 0 ||
                                  orderById.get(ids[index - 1]) <= orderById.get(id)
                                ),
                              };
                            }"""
                        )
                        assert restored_order == {
                            "firstId": "render-root",
                            "courseOrdered": True,
                        }
                        if viewport["width"] >= 520:
                            page.locator(
                                '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"] '
                                ".raya-graph-node-hit"
                            ).hover()
                        else:
                            page.locator(
                                '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
                            ).focus()
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
                        page.click("#graph-reset")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#graph-layout')
                              ?.value === 'connections'"""
                        )
                        if viewport["width"] >= 1280:
                            active_state = page.locator(
                                "[data-raya-graph-active-state]"
                            )
                            arrangement_status = page.locator(
                                "[data-raya-graph-arrangement-status]"
                            )
                            assert arrangement_status.is_hidden()
                            drag_target = "authoring-matrix"
                            drag_edge = page.locator(
                                "#raya-graph-canvas "
                                f'.raya-graph-edge[data-raya-graph-from="{drag_target}"], '
                                "#raya-graph-canvas "
                                f'.raya-graph-edge[data-raya-graph-to="{drag_target}"]'
                            ).first
                            drag_edge_before = drag_edge.evaluate(
                                """node => ({
                                  x1: Number(node.getAttribute('x1')),
                                  y1: Number(node.getAttribute('y1')),
                                  x2: Number(node.getAttribute('x2')),
                                  y2: Number(node.getAttribute('y2')),
                                })"""
                            )
                            graph_data_before_drag = page.locator(
                                "#raya-graph-data"
                            ).text_content()
                            drag_start = _graph_node_translate(page, drag_target)
                            drag_hit_box = page.locator(
                                f'#raya-graph-canvas [data-raya-graph-node="{drag_target}"] '
                                ".raya-graph-node-hit"
                            )
                            drag_hit_box.scroll_into_view_if_needed()
                            drag_box = drag_hit_box.bounding_box()
                            assert drag_box is not None
                            graph_url_before_drag = page.url
                            drag_start_client = {
                                "x": drag_box["x"] + drag_box["width"] / 2,
                                "y": drag_box["y"] + drag_box["height"] / 2,
                            }
                            drag_end_client = {
                                "x": drag_start_client["x"] + 150,
                                "y": drag_start_client["y"] + 90,
                            }
                            page.mouse.move(
                                drag_start_client["x"],
                                drag_start_client["y"],
                            )
                            page.mouse.down()
                            page.mouse.move(
                                drag_end_client["x"],
                                drag_end_client["y"],
                                steps=6,
                            )
                            page.mouse.up()
                            drag_after = _graph_node_translate(page, drag_target)
                            assert drag_after != drag_start
                            assert drag_after[0] > drag_start[0] + 20
                            assert drag_after[1] > drag_start[1] + 15
                            assert page.url == graph_url_before_drag
                            assert arrangement_status.is_visible()
                            assert "Manual arrangement" in arrangement_status.inner_text()
                            assert "Reset graph" in arrangement_status.inner_text()
                            assert "manual layout" in active_state.inner_text().lower()
                            assert (
                                page.locator("#raya-graph-data").text_content()
                                == graph_data_before_drag
                            )
                            drag_edge_after = drag_edge.evaluate(
                                """node => ({
                                  x1: Number(node.getAttribute('x1')),
                                  y1: Number(node.getAttribute('y1')),
                                  x2: Number(node.getAttribute('x2')),
                                  y2: Number(node.getAttribute('y2')),
                                })"""
                            )
                            assert drag_edge_after != drag_edge_before
                            page.click("#graph-fit")
                            assert _graph_node_translate(page, drag_target) == drag_after
                            assert arrangement_status.is_visible()
                            assert (
                                drag_edge.evaluate(
                                    """node => ({
                                      x1: Number(node.getAttribute('x1')),
                                      y1: Number(node.getAttribute('y1')),
                                      x2: Number(node.getAttribute('x2')),
                                      y2: Number(node.getAttribute('y2')),
                                    })"""
                                )
                                == drag_edge_after
                            )
                            page.fill("#graph-search", "matrix")
                            page.wait_for_function(
                                """nodeId => {
                                  const canvas = document.querySelector('#raya-graph-canvas');
                                  const group = document
                                    .querySelector(
                                      `#raya-graph-canvas [data-raya-graph-node="${nodeId}"] g`
                                    );
                                  if (!canvas || !group) return false;
                                  const viewBox = canvas
                                    .getAttribute('viewBox')
                                    .split(/\\s+/)
                                    .map(Number);
                                  const transform = group.getAttribute('transform') || '';
                                  const match = transform.match(
                                    /translate\\(([-0-9.]+)\\s+([-0-9.]+)\\)/
                                  );
                                  if (!match) return false;
                                  const x = Number(match[1]);
                                  const y = Number(match[2]);
                                  return x >= viewBox[0] + 35.99 &&
                                    x <= viewBox[0] + viewBox[2] - 35.99 &&
                                    y >= viewBox[1] + 35.99 &&
                                    y <= viewBox[1] + viewBox[3] - 35.99;
                                }""",
                                arg=drag_target,
                            )
                            assert arrangement_status.is_visible()
                            page.click("#graph-reset")
                            page.wait_for_function(
                                """() => document
                                  .querySelector('#graph-search')
                                  ?.value === ''"""
                            )
                            assert arrangement_status.is_hidden()
                            assert active_state.inner_text() == "Ready: full graph"
                            assert page.evaluate(
                                "() => [Object.keys(localStorage), Object.keys(sessionStorage)]"
                            ) == [[], []]
                            touch_state = page.locator(
                                f'#raya-graph-canvas [data-raya-graph-node="{drag_target}"]'
                            ).evaluate(
                                """node => {
                                  const canvas = document.querySelector('#raya-graph-canvas');
                                  const before = canvas.classList.contains('is-dragging-node');
                                  const event = new PointerEvent('pointerdown', {
                                    bubbles: true,
                                    cancelable: true,
                                    pointerId: 71,
                                    pointerType: 'touch',
                                    button: 0,
                                    clientX: node.getBoundingClientRect().left + 4,
                                    clientY: node.getBoundingClientRect().top + 4,
                                  });
                                  const dispatched = node.dispatchEvent(event);
                                  return {
                                    before,
                                    after: canvas.classList.contains('is-dragging-node'),
                                    defaultPrevented: event.defaultPrevented,
                                    dispatched,
                                  };
                                }"""
                            )
                            assert touch_state == {
                                "before": False,
                                "after": False,
                                "defaultPrevented": False,
                                "dispatched": True,
                            }
                            compatibility_mouse_state = page.locator(
                                f'#raya-graph-canvas [data-raya-graph-node="{drag_target}"]'
                            ).evaluate(
                                """node => {
                                  const canvas = document.querySelector('#raya-graph-canvas');
                                  const hit = node.querySelector('.raya-graph-node-hit') || node;
                                  const box = hit.getBoundingClientRect();
                                  const touch = new PointerEvent('pointerdown', {
                                    bubbles: true,
                                    cancelable: true,
                                    pointerId: 73,
                                    pointerType: 'touch',
                                    button: 0,
                                    clientX: box.left + box.width / 2,
                                    clientY: box.top + box.height / 2,
                                  });
                                  node.dispatchEvent(touch);
                                  const mouse = new MouseEvent('mousedown', {
                                    bubbles: true,
                                    cancelable: true,
                                    button: 0,
                                    clientX: box.left + box.width / 2,
                                    clientY: box.top + box.height / 2,
                                  });
                                  const dispatched = node.dispatchEvent(mouse);
                                  const afterMouseDown = canvas.classList.contains('is-dragging-node');
                                  return {
                                    afterMouseDown,
                                    afterPanStart: canvas.classList.contains('is-panning'),
                                    mouseDefaultPrevented: mouse.defaultPrevented,
                                    dispatched,
                                  };
                                }"""
                            )
                            assert compatibility_mouse_state == {
                                "afterMouseDown": False,
                                "afterPanStart": False,
                                "mouseDefaultPrevented": False,
                                "dispatched": True,
                            }
                            page.wait_for_timeout(750)
                            clamp_drag_box = drag_hit_box.bounding_box()
                            assert clamp_drag_box is not None
                            clamp_start_client = {
                                "x": clamp_drag_box["x"] + clamp_drag_box["width"] / 2,
                                "y": clamp_drag_box["y"] + clamp_drag_box["height"] / 2,
                            }
                            clamp_end_client = {
                                "x": clamp_start_client["x"] + 10000,
                                "y": clamp_start_client["y"] + 10000,
                            }
                            page.mouse.move(
                                clamp_start_client["x"],
                                clamp_start_client["y"],
                            )
                            page.mouse.down()
                            page.mouse.move(
                                clamp_end_client["x"],
                                clamp_end_client["y"],
                                steps=8,
                            )
                            page.mouse.up()
                            page.wait_for_function(
                                """nodeId => {
                                  const canvas = document.querySelector('#raya-graph-canvas');
                                  const group = document
                                    .querySelector(
                                      `#raya-graph-canvas [data-raya-graph-node="${nodeId}"] g`
                                    );
                                  if (!canvas || !group) return false;
                                  const viewBox = canvas
                                    .getAttribute('viewBox')
                                    .split(/\\s+/)
                                    .map(Number);
                                  const transform = group.getAttribute('transform') || '';
                                  const match = transform.match(
                                    /translate\\(([-0-9.]+)\\s+([-0-9.]+)\\)/
                                  );
                                  if (!match) return false;
                                  const x = Number(match[1]);
                                  const y = Number(match[2]);
                                  return x >= viewBox[0] + 35.99 &&
                                    x <= viewBox[0] + viewBox[2] - 35.99 &&
                                    y >= viewBox[1] + 35.99 &&
                                    y <= viewBox[1] + viewBox[3] - 35.99;
                                }""",
                                arg=drag_target,
                            )
                            page.select_option("#graph-layout", "topology")
                            assert arrangement_status.is_hidden()
                            page.wait_for_function(
                                """nodeId => {
                                  const transform = document
                                    .querySelector(
                                      `#raya-graph-canvas [data-raya-graph-node="${nodeId}"] g`
                                    )
                                    ?.getAttribute('transform') || '';
                                  const match = transform.match(
                                    /translate\\(([-0-9.]+)\\s+([-0-9.]+)\\)/
                                  );
                                  if (!match) return false;
                                  return Math.abs(Number(match[1]) - 36) > 0.01 ||
                                    Math.abs(Number(match[2]) - 36) > 0.01;
                                }""",
                                arg=drag_target,
                            )
                            page.select_option("#graph-layout", "connections")
                            page.wait_for_function(
                                """([nodeId, expected]) => {
                                  if (document
                                    .querySelector('#graph-layout')
                                    ?.value !== 'connections') {
                                    return false;
                                  }
                                  const transform = document
                                    .querySelector(
                                      `#raya-graph-canvas [data-raya-graph-node="${nodeId}"] g`
                                    )
                                    ?.getAttribute('transform') || '';
                                  const match = transform.match(
                                    /translate\\(([-0-9.]+)\\s+([-0-9.]+)\\)/
                                  );
                                  return !!match &&
                                    Math.abs(Number(match[1]) - expected[0]) < 0.01 &&
                                    Math.abs(Number(match[2]) - expected[1]) < 0.01;
                                }""",
                                arg=[drag_target, list(drag_start)],
                            )
                            page.click("#graph-reset")
                            page.wait_for_function(
                                """([nodeId, expected]) => {
                                  const transform = document
                                    .querySelector(
                                      `#raya-graph-canvas [data-raya-graph-node="${nodeId}"] g`
                                    )
                                    ?.getAttribute('transform') || '';
                                  const match = transform.match(
                                    /translate\\(([-0-9.]+)\\s+([-0-9.]+)\\)/
                                  );
                                  return !!match &&
                                    Math.abs(Number(match[1]) - expected[0]) < 0.01 &&
                                    Math.abs(Number(match[2]) - expected[1]) < 0.01;
                                }""",
                                arg=[drag_target, list(drag_start)],
                            )
                            assert _graph_node_translate(page, drag_target) == drag_start
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
                        if viewport["width"] >= 520:
                            page.locator(
                                '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"] '
                                ".raya-graph-node-hit"
                            ).hover()
                        else:
                            page.locator(
                                '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
                            ).focus()
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
                            '#raya-graph-list [data-raya-graph-node="authoring-matrix"]:visible a'
                        ).focus()
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-hover-status]')
                              ?.textContent
                              ?.includes('Inspecting Authoring Matrix Fixture')"""
                        )
                        page.locator(
                            '#raya-graph-list [data-raya-graph-node="static-path"]:visible a'
                        ).focus()
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-hover-status]')
                              ?.textContent
                              ?.includes('Static Path')"""
                        )
                        list_focus_over_hover = page.locator(
                            '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
                        ).evaluate(
                            """node => {
                              const target = node.querySelector('.raya-graph-node-hit') || node;
                              target.dispatchEvent(new MouseEvent('mouseenter', {
                                bubbles: true,
                                cancelable: true,
                              }));
                              return {
                                activeNode: document.activeElement
                                  ?.closest('[data-raya-graph-node]')
                                  ?.getAttribute('data-raya-graph-node'),
                                hoverStatus: document
                                  .querySelector('[data-raya-graph-hover-status]')
                                  ?.textContent,
                                inspectedListNodes: Array.from(
                                  document.querySelectorAll(
                                    '#raya-graph-list [data-raya-graph-node].is-inspected'
                                  )
                                ).map((item) => item.getAttribute('data-raya-graph-node')),
                              };
                            }"""
                        )
                        assert list_focus_over_hover["activeNode"] == "static-path"
                        assert "Static Path" in list_focus_over_hover["hoverStatus"]
                        assert list_focus_over_hover["inspectedListNodes"] == [
                            "static-path"
                        ]
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
                            "#raya-graph-canvas [data-raya-graph-node] "
                            ".raya-graph-node-hit"
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
                        _click_graph_node_group(page, "authoring-matrix")
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
                        page.locator("#raya-graph-canvas").evaluate(
                            """(svg) => {
                              svg.style.width = '360px';
                              svg.style.height = '620px';
                              svg.style.maxWidth = 'none';
                            }"""
                        )
                        off_center_anchor = page.locator(
                            "#raya-graph-canvas"
                        ).evaluate(
                            """(svg) => {
                              const [x, y, width, height] = svg
                                .getAttribute('viewBox')
                                .split(/\\s+/)
                                .map(Number);
                              const svgPoint = svg.createSVGPoint();
                              svgPoint.x = x + width * 0.54;
                              svgPoint.y = y + height * 0.70;
                              const matrix = svg.getScreenCTM();
                              if (!matrix) return null;
                              const mapped = svgPoint.matrixTransform(matrix);
                              return { x: mapped.x, y: mapped.y };
                            }"""
                        )
                        assert off_center_anchor is not None
                        svg_point_at_anchor = """(svg, point) => {
                          const svgPoint = svg.createSVGPoint();
                          svgPoint.x = point.x;
                          svgPoint.y = point.y;
                          const matrix = svg.getScreenCTM();
                          if (!matrix) return null;
                          const mapped = svgPoint.matrixTransform(matrix.inverse());
                          return { x: mapped.x, y: mapped.y };
                        }"""
                        anchor_before_zoom = page.locator(
                            "#raya-graph-canvas"
                        ).evaluate(svg_point_at_anchor, off_center_anchor)
                        assert anchor_before_zoom is not None
                        page.locator("#raya-graph-canvas").dispatch_event(
                            "wheel",
                            {
                                "deltaY": -140,
                                "clientX": off_center_anchor["x"],
                                "clientY": off_center_anchor["y"],
                            },
                        )
                        anchor_after_zoom = page.locator(
                            "#raya-graph-canvas"
                        ).evaluate(svg_point_at_anchor, off_center_anchor)
                        assert anchor_after_zoom is not None
                        assert abs(
                            anchor_after_zoom["x"] - anchor_before_zoom["x"]
                        ) < 0.5
                        assert abs(
                            anchor_after_zoom["y"] - anchor_before_zoom["y"]
                        ) < 0.5
                        zero_delta_viewbox = page.locator(
                            "#raya-graph-canvas"
                        ).get_attribute("viewBox")
                        page.locator("#raya-graph-canvas").dispatch_event(
                            "wheel",
                            {
                                "deltaX": 120,
                                "deltaY": 0,
                                "clientX": off_center_anchor["x"],
                                "clientY": off_center_anchor["y"],
                            },
                        )
                        assert (
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                            == zero_delta_viewbox
                        )
                        page.locator("#raya-graph-canvas").evaluate(
                            """(svg) => {
                              svg.style.width = '';
                              svg.style.height = '';
                              svg.style.maxWidth = '';
                            }"""
                        )
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
                        _click_graph_node_group(page, "authoring-matrix")
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-state-selected]')
                              ?.textContent
                              ?.includes('authoring-matrix')"""
                        )
                        page.fill("#graph-search", "matrix")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#graph-status')
                              ?.textContent
                              ?.includes('match(es)')"""
                        )
                        selected_before_wheel = page.locator(
                            "[data-raya-graph-state-selected]"
                        ).inner_text()
                        wheel_start_viewbox = page.locator(
                            "#raya-graph-canvas"
                        ).get_attribute("viewBox")
                        canvas_box = page.locator("#raya-graph-canvas").bounding_box()
                        assert canvas_box is not None
                        page.locator("#raya-graph-canvas").dispatch_event(
                            "wheel",
                            {
                                "deltaY": -180,
                                "clientX": canvas_box["x"] + canvas_box["width"] / 2,
                                "clientY": canvas_box["y"] + canvas_box["height"] / 2,
                            },
                        )
                        wheel_zoomed_viewbox = page.locator(
                            "#raya-graph-canvas"
                        ).get_attribute("viewBox")
                        assert wheel_zoomed_viewbox != wheel_start_viewbox
                        assert _viewbox_width(wheel_zoomed_viewbox) < _viewbox_width(
                            wheel_start_viewbox
                        )
                        assert page.input_value("#graph-search") == "matrix"
                        assert (
                            page.locator(
                                "[data-raya-graph-state-selected]"
                            ).inner_text()
                            == selected_before_wheel
                        )
                        assert page.locator(
                            "[data-raya-graph-detail-panel]"
                        ).is_visible()
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
                        page.fill("#graph-search", "zzzz-no-match")
                        page.wait_for_selector("[data-raya-graph-empty]:visible")
                        assert (
                            "No graph pages match"
                            in page.locator("[data-raya-graph-empty]").inner_text()
                        )
                        assert "zzzz-no-match" in page.locator(
                            "[data-raya-graph-empty]"
                        ).inner_text()
                        assert page.locator(
                            "[data-raya-graph-empty] [data-raya-graph-clear-search]"
                        ).is_visible()
                        page.locator(
                            "[data-raya-graph-empty] [data-raya-graph-clear-search]"
                        ).click()
                        page.wait_for_function(
                            """() => document.querySelector('#graph-search')?.value === ''"""
                        )
                        assert (
                            page.locator("[data-raya-graph-empty]:visible").count()
                            == 0
                        )
                        page.click('[data-raya-graph-toggle-panel="list"]')
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-list-state"
                            )
                            == "collapsed"
                        )
                        page.fill("#graph-search", "zzzz-no-match")
                        page.wait_for_selector(
                            "[data-raya-graph-empty]", state="attached"
                        )
                        assert (
                            page.locator(
                                "[data-raya-graph-empty] [data-raya-graph-clear-search]"
                            ).get_attribute("tabindex")
                            == "-1"
                        )
                        page.click('[data-raya-graph-toggle-panel="list"]')
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-list-state"
                            )
                            == "expanded"
                        )
                        assert (
                            page.locator(
                                "[data-raya-graph-empty] [data-raya-graph-clear-search]"
                            ).get_attribute("tabindex")
                            is None
                        )
                        page.locator(
                            "[data-raya-graph-empty] [data-raya-graph-clear-search]"
                        ).click()
                        page.wait_for_function(
                            """() => document.querySelector('#graph-search')?.value === ''"""
                        )
                        page.fill("#graph-search", "matrx")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#graph-status')
                              ?.textContent
                              ?.includes('visible node')"""
                        )
                        _click_graph_node_group(page, "authoring-matrix")
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-state-selected]')
                              ?.textContent
                              ?.includes('authoring-matrix')"""
                        )
                        page.click("#graph-zoom-in")
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
                            "#raya-graph-canvas [data-raya-graph-node] "
                            ".raya-graph-node-hit"
                        ).first.click()
                        page.wait_for_selector(
                            "[data-raya-graph-detail-panel]:not([hidden])"
                        )
                        page.locator(
                            '#raya-graph-canvas '
                            '[data-raya-graph-node="authoring-matrix"] '
                            ".raya-graph-node-hit"
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
                            page.locator(
                                '#raya-graph-canvas '
                                '[data-raya-graph-node="render-root"] '
                                ".raya-graph-node-label"
                            ).evaluate(
                                """node => {
                                  node.textContent =
                                    'Raya Lucaria Render Fixture With A Deliberately Long Visible Graph Label';
                                }"""
                            )
                            page.click("#graph-zoom-in")
                            _assert_visible_graph_labels_inside_canvas(page)
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
                                == "expanded"
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
                                == "expanded"
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
                            '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
                        )
                        _click_graph_node_group(page, "authoring-matrix")
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
                            '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"]'
                        ).evaluate(
                            "node => new URL(node.getAttribute('href'), document.baseURI).href"
                        )
                        with page.expect_navigation():
                            _click_graph_node_group(
                                page, "authoring-matrix", click_count=2
                            )
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
                            f"{base_url}/_raya/graph/index.html",
                            wait_until="networkidle",
                        )
                        plain_graph_viewbox = page.locator(
                            "#raya-graph-canvas"
                        ).get_attribute("viewBox")
                        plain_label_state = page.locator(
                            "#raya-graph-canvas [data-raya-graph-node]"
                        ).evaluate_all(
                            """nodes => Object.fromEntries(nodes.map((node) => {
                              const label = node.querySelector('text');
                              const style = label ? getComputedStyle(label) : null;
                              return [node.getAttribute('data-raya-graph-node'), {
                                text: label ? label.textContent.trim() : '',
                                visible: Boolean(style) && style.visibility !== 'hidden',
                              }];
                            }))"""
                        )
                        assert plain_label_state["render-root"]["visible"]
                        assert plain_label_state["authoring-matrix"]["visible"]
                        assert not plain_label_state["static-path"]["visible"]
                        _assert_visible_graph_labels_inside_canvas(page)
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
                        page_scoped_viewbox = page.locator(
                            "#raya-graph-canvas"
                        ).get_attribute("viewBox")
                        assert _viewbox_width(page_scoped_viewbox) < _viewbox_width(
                            plain_graph_viewbox
                        )
                        assert page.locator("#graph-fit-selection").is_enabled()
                        page.locator("#raya-graph-canvas").scroll_into_view_if_needed()
                        context = _visible_graph_context(
                            page, "authoring-matrix", viewport
                        )
                        assert context["selectedVisible"]
                        assert context["activeEdgeVisible"]
                        assert (
                            page.locator(
                                "[data-raya-graph-state-page-focus]"
                            ).text_content()
                            == "authoring-matrix"
                        )
                        page.click("#graph-reset-view")
                        assert (
                            page.locator("#raya-graph-canvas").get_attribute("viewBox")
                            == plain_graph_viewbox
                        )
                        assert (
                            page.locator(
                                "[data-raya-graph-state-page-focus]"
                            ).text_content()
                            == "authoring-matrix"
                        )
                        assert page.locator(
                            "[data-raya-graph-detail-panel]"
                        ).is_visible()
                        assert (
                            "Explicit links: 4 outgoing, 2 incoming, 4 connected."
                        ) in page.locator(
                            "[data-raya-graph-detail-neighborhood]"
                        ).inner_text()
                        relationship_overview = page.locator(
                            "[data-raya-graph-detail-relationship-overview]"
                        )
                        assert relationship_overview.is_visible()
                        overview_text = relationship_overview.inner_text()
                        assert "Relationship overview" in overview_text
                        assert "4 outgoing" in overview_text
                        assert "2 incoming" in overview_text
                        assert "4 connected" in overview_text
                        overview_cards = relationship_overview.locator(
                            "[data-raya-graph-relationship-overview-card]"
                        )
                        assert overview_cards.count() == 4
                        overview_card_texts = overview_cards.evaluate_all(
                            "cards => cards.map((card) => card.textContent.trim())"
                        )
                        assert any(
                            "Content from this page" in text and "3 links" in text
                            for text in overview_card_texts
                        )
                        assert any(
                            "Content to this page" in text and "1 link" in text
                            for text in overview_card_texts
                        )
                        relationship_chips = page.locator(
                            "[data-raya-graph-detail-relationship-chips]"
                        )
                        assert relationship_chips.is_visible()
                        chip_texts = relationship_chips.locator(
                            ".raya-graph-detail-relationship-chip"
                        ).evaluate_all(
                            "nodes => nodes.map((node) => node.textContent.trim())"
                        )
                        assert "Content out 3" in chip_texts
                        assert "Content in 1" in chip_texts
                        assert "Navigation in 1" in chip_texts
                        assert "Parent out 1" in chip_texts
                        assert len(chip_texts) == 4
                        assert sum(int(text.split().pop()) for text in chip_texts) == 6
                        outgoing_text = page.locator(
                            "[data-raya-graph-detail-outgoing]"
                        ).inner_text()
                        incoming_text = page.locator(
                            "[data-raya-graph-detail-incoming]"
                        ).inner_text()
                        assert "Content" in outgoing_text
                        assert "Parent" in outgoing_text
                        assert "Content" in incoming_text
                        assert "Navigation" in incoming_text
                        relationship_walkthrough = page.locator(
                            "[data-raya-graph-relationship-walkthrough]"
                        )
                        assert relationship_walkthrough.is_visible()
                        walkthrough_cards = relationship_walkthrough.locator(
                            "[data-raya-graph-relationship-walkthrough-card]"
                        )
                        assert walkthrough_cards.count() == 4
                        walkthrough_text = relationship_walkthrough.inner_text()
                        assert "Relationship walkthrough" in walkthrough_text
                        assert "Content from this page" in walkthrough_text
                        assert "Content to this page" in walkthrough_text
                        assert "Navigation to this page" in walkthrough_text
                        assert "Parent from this page" in walkthrough_text
                        assert "Use these pages to read the selected page's explicit content links." in walkthrough_text
                        assert "These pages explicitly link back to the selected page." in walkthrough_text
                        assert "This page appears after these pages in the generated course order." in walkthrough_text
                        assert "These pages are direct structural parents of the selected page." in walkthrough_text
                        content_out_chip = relationship_chips.locator(
                            '[data-raya-graph-relationship-kind="content"]'
                            '[data-raya-graph-relationship-direction="out"]'
                        )
                        assert (
                            content_out_chip.evaluate("node => node.tagName")
                            == "BUTTON"
                        )
                        assert content_out_chip.get_attribute("aria-pressed") == "false"
                        relationship_focus_url = page.url
                        overview_content_out = relationship_overview.locator(
                            '[data-raya-graph-relationship-overview-card]'
                            '[data-raya-graph-relationship-kind="content"]'
                            '[data-raya-graph-relationship-direction="out"]'
                        )
                        overview_content_out.click()
                        assert (
                            overview_content_out.get_attribute("aria-pressed")
                            == "true"
                        )
                        assert content_out_chip.get_attribute("aria-pressed") == "true"
                        assert page.url == relationship_focus_url
                        focus_summary = page.locator(
                            "[data-raya-graph-relationship-focus-summary]"
                        )
                        focus_reset = page.locator(
                            "[data-raya-graph-relationship-focus-reset]"
                        )
                        assert focus_reset.is_visible()
                        assert (
                            "Showing Content out relationships."
                            in focus_summary.inner_text()
                        )
                        assert page.evaluate(
                            "() => [Object.keys(localStorage), Object.keys(sessionStorage)]"
                        ) == [[], []]
                        visible_outgoing_items = page.locator(
                            "[data-raya-graph-detail-outgoing] li"
                        ).evaluate_all(
                            "items => items.filter((item) => !item.hidden).map((item) => item.textContent)"
                        )
                        assert visible_outgoing_items
                        assert all("Content" in text for text in visible_outgoing_items)
                        assert (
                            page.locator(
                                "[data-raya-graph-detail-incoming] li"
                            ).evaluate_all("items => items.every((item) => item.hidden)")
                            is True
                        )
                        focused_edges = page.locator(
                            "#raya-graph-canvas [data-raya-graph-edge].is-relationship-focus"
                        )
                        muted_edges = page.locator(
                            "#raya-graph-canvas [data-raya-graph-edge].is-relationship-muted"
                        )
                        selection_muted_edges = page.locator(
                            "#raya-graph-canvas [data-raya-graph-edge].is-selection-muted"
                        )
                        assert focused_edges.count() >= 1
                        assert muted_edges.count() >= 1
                        assert selection_muted_edges.count() >= 1
                        assert (
                            page.locator(
                                '#raya-graph-canvas [data-raya-graph-edge]'
                                '[data-raya-graph-from="render-root"]'
                                '[data-raya-graph-to="static-path"].is-selection-muted'
                            ).count()
                            >= 1
                        )
                        visible_cards = walkthrough_cards.evaluate_all(
                            """cards => cards
                              .filter((card) => !card.hidden)
                              .map((card) => [
                                card.getAttribute('data-raya-graph-relationship-kind'),
                                card.getAttribute('data-raya-graph-relationship-direction'),
                                card.textContent,
                              ])"""
                        )
                        assert len(visible_cards) == 1
                        assert visible_cards[0][0:2] == ["content", "out"]
                        assert "Content from this page" in visible_cards[0][2]
                        assert (
                            "Showing Content out relationships."
                            in relationship_walkthrough.inner_text()
                        )
                        content_in_chip = relationship_chips.locator(
                            '[data-raya-graph-relationship-kind="content"]'
                            '[data-raya-graph-relationship-direction="in"]'
                        )
                        content_in_chip.click()
                        assert content_out_chip.get_attribute("aria-pressed") == "false"
                        assert content_in_chip.get_attribute("aria-pressed") == "true"
                        visible_card_keys = walkthrough_cards.evaluate_all(
                            """cards => cards
                              .filter((card) => !card.hidden)
                              .map((card) => [
                                card.getAttribute('data-raya-graph-relationship-kind'),
                                card.getAttribute('data-raya-graph-relationship-direction'),
                              ])"""
                        )
                        assert visible_card_keys == [["content", "in"]]
                        active_card_focus = relationship_walkthrough.locator(
                            '[data-raya-graph-relationship-walkthrough-card]'
                            '[data-raya-graph-relationship-kind="content"]'
                            '[data-raya-graph-relationship-direction="in"] '
                            "[data-raya-graph-focus-node]"
                        ).first
                        active_card_focus_target = active_card_focus.get_attribute(
                            "data-raya-graph-focus-node"
                        )
                        assert active_card_focus_target
                        active_card_focus.click()
                        page.wait_for_function(
                            """(target) => document
                              .querySelector('[data-raya-graph-state-selected]')
                              ?.textContent === target""",
                            arg=active_card_focus_target,
                        )
                        assert (
                            relationship_chips.locator(
                                "[data-raya-graph-relationship-chip]"
                            ).evaluate_all(
                                "chips => chips.every((chip) => chip.getAttribute('aria-pressed') === 'false')"
                            )
                            is True
                        )
                        assert (
                            walkthrough_cards.evaluate_all(
                                "cards => cards.length === cards.filter((card) => !card.hidden).length"
                            )
                            is True
                        )
                        assert (
                            "Showing "
                            not in relationship_walkthrough.inner_text()
                        )
                        _click_graph_node_group(page, "authoring-matrix")
                        page.wait_for_function(
                            """() => document
                              .querySelector('[data-raya-graph-state-selected]')
                              ?.textContent === 'authoring-matrix'"""
                        )
                        content_out_chip = relationship_chips.locator(
                            '[data-raya-graph-relationship-kind="content"]'
                            '[data-raya-graph-relationship-direction="out"]'
                        )
                        graph_url_before_focus_reset = page.url
                        content_out_chip.click()
                        assert content_out_chip.get_attribute("aria-pressed") == "true"
                        assert focus_reset.is_visible()
                        focus_reset.click()
                        assert content_out_chip.get_attribute("aria-pressed") == "false"
                        assert focus_reset.is_hidden()
                        assert (
                            "All selected-page relationships are visible."
                            in focus_summary.inner_text()
                        )
                        assert page.url == graph_url_before_focus_reset
                        assert focused_edges.count() == 0
                        assert muted_edges.count() == 0
                        assert (
                            walkthrough_cards.evaluate_all(
                                "cards => cards.filter((card) => !card.hidden).length"
                            )
                            == 4
                        )
                        assert (
                            page.locator(
                                "[data-raya-graph-detail-incoming] li"
                            ).evaluate_all(
                                "items => items.some((item) => !item.hidden)"
                            )
                            is True
                        )
                        assert (
                            "Showing "
                            not in relationship_walkthrough.inner_text()
                        )
                        assert page.evaluate(
                            "() => [Object.keys(localStorage), Object.keys(sessionStorage)]"
                        ) == [[], []]
                        content_out_chip.click()
                        assert content_out_chip.get_attribute("aria-pressed") == "true"
                        page.locator(
                            '[data-raya-graph-edge-kind-filter="content"]'
                        ).click()
                        assert (
                            content_out_chip.get_attribute(
                                "data-raya-graph-relationship-hidden-by-filter"
                            )
                            == "true"
                        )
                        assert (
                            overview_content_out.get_attribute(
                                "data-raya-graph-relationship-hidden-by-filter"
                            )
                            == "true"
                        )
                        assert content_out_chip.get_attribute("aria-pressed") == "true"
                        assert (
                            overview_content_out.get_attribute("aria-pressed")
                            == "true"
                        )
                        assert focus_reset.is_visible()
                        assert (
                            "Content relationships are hidden by Relationship filters."
                            in focus_summary.inner_text()
                        )
                        assert page.evaluate(
                            "() => [Object.keys(localStorage), Object.keys(sessionStorage)]"
                        ) == [[], []]
                        focus_reset.click()
                        assert content_out_chip.get_attribute("aria-pressed") == "false"
                        assert focus_reset.is_hidden()
                        assert (
                            "Content relationships are hidden by Relationship filters."
                            in focus_summary.inner_text()
                        )
                        page.locator(
                            '[data-raya-graph-edge-kind-filter="content"]'
                        ).click()
                        assert (
                            content_out_chip.get_attribute(
                                "data-raya-graph-relationship-hidden-by-filter"
                            )
                            == "false"
                        )
                        assert (
                            "All selected-page relationships are visible."
                            in focus_summary.inner_text()
                        )
                        assert (
                            relationship_walkthrough.locator(
                                '[data-raya-graph-focus-node="math-authoring"]'
                            ).count()
                            >= 1
                        )
                        assert (
                            any(
                                href.endswith("/math-authoring/index.html")
                                for href in relationship_walkthrough.locator(
                                    "a"
                                ).evaluate_all(
                                    "links => links.map((link) => link.href)"
                                )
                            )
                        )
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
                        selected_label_state = page.locator(
                            "#raya-graph-canvas [data-raya-graph-node]"
                        ).evaluate_all(
                            """nodes => Object.fromEntries(nodes.map((node) => {
                              const label = node.querySelector('text');
                              const style = label ? getComputedStyle(label) : null;
                              return [node.getAttribute('data-raya-graph-node'), {
                                visible: Boolean(style) && style.visibility !== 'hidden',
                              }];
                            }))"""
                        )
                        assert selected_label_state["authoring-matrix"]["visible"]
                        for node_id in (
                            "render-root",
                            "math-authoring",
                            "numbered-objects",
                            "reader-ux",
                        ):
                            assert selected_label_state[node_id]["visible"]
                        assert not selected_label_state["static-path"]["visible"]
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
                        search_label_state = page.locator(
                            "#raya-graph-canvas [data-raya-graph-node]"
                        ).evaluate_all(
                            """nodes => Object.fromEntries(nodes.map((node) => {
                              const label = node.querySelector('text');
                              const style = label ? getComputedStyle(label) : null;
                              return [node.getAttribute('data-raya-graph-node'), {
                                visible: Boolean(style) && style.visibility !== 'hidden',
                              }];
                            }))"""
                        )
                        assert search_label_state["static-path"]["visible"]
                        assert search_label_state["render-root"]["visible"]
                        assert search_label_state["authoring-matrix"]["visible"]
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
                            'section[aria-label="Graph groups"] '
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
                            ).text_content()
                        )
                        assert (
                            page.locator(
                                "[data-raya-graph-state-page-focus]"
                            ).text_content()
                            == "none"
                        )
                        focus_label_state = page.locator(
                            "#raya-graph-canvas [data-raya-graph-node]"
                        ).evaluate_all(
                            """nodes => Object.fromEntries(nodes.map((node) => {
                              const label = node.querySelector('text');
                              const style = label ? getComputedStyle(label) : null;
                              return [node.getAttribute('data-raya-graph-node'), {
                                visible: Boolean(style) && style.visibility !== 'hidden',
                              }];
                            }))"""
                        )
                        assert focus_label_state["math-authoring"]["visible"]
                        assert focus_label_state["numbered-objects"]["visible"]
                        assert focus_label_state["render-root"]["visible"]
                        assert not focus_label_state["static-path"]["visible"]
                        page.click("#graph-reset")
                        assert (
                            page.locator("[data-raya-graph-page]").get_attribute(
                                "data-raya-graph-neighborhood-focus"
                            )
                            == "false"
                        )
                        assert (
                            page.locator(
                                "[data-raya-graph-state-page-focus]"
                            ).text_content()
                            == "none"
                        )
                        assert page.locator(
                            "[data-raya-graph-detail-empty]"
                        ).is_visible()
                        assert page.locator(
                            "[data-raya-graph-detail-relationship-chips]"
                        ).is_hidden()
                        assert page.locator(
                            "[data-raya-graph-relationship-walkthrough]"
                        ).is_hidden()
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
                    page.locator("#raya-graph-canvas").scroll_into_view_if_needed()
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
        base_url = handle.base_url
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
                    window.__rayaCopiedGraphUrls = [];
                    Object.defineProperty(navigator, 'clipboard', {
                      configurable: true,
                      value: {
                        writeText: async (value) => {
                          window.__rayaCopiedGraphUrls.push(String(value));
                        },
                      },
                    });
                    """
                )
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
                    orientation = page.locator("[data-raya-graph-orientation]")
                    assert orientation.is_visible()
                    orientation_box = orientation.bounding_box()
                    canvas_box = page.locator("#raya-graph-canvas").bounding_box()
                    assert orientation_box is not None
                    assert canvas_box is not None
                    assert orientation_box["y"] < canvas_box["y"]
                    assert orientation_box["y"] < 900
                    assert orientation_box["height"] <= 140
                    guide = page.locator("[data-raya-graph-guide]")
                    assert guide.is_visible()
                    guide_box = guide.bounding_box()
                    assert guide_box is not None
                    assert guide_box["y"] > orientation_box["y"]
                    assert guide_box["y"] > canvas_box["y"]
                    assert guide_box["height"] <= 220
                    guide.locator("summary").click()
                    guide_text = guide.inner_text()
                    for label in (
                        "Graph quick guide",
                        "Find",
                        "Choose a view",
                        "Inspect",
                        "Move",
                        "Filter",
                    ):
                        assert label in guide_text
                    for forbidden in (
                        "progress",
                        "mastery",
                        "ranking",
                        "recommendation",
                        "personalization",
                    ):
                        assert forbidden not in guide_text.lower()
                    assert "On desktop, drag pages to tidy the map" in guide_text
                    assert "Reset graph restores the generated layout" in guide_text
                    assert "visible page" in page.locator(
                        "[data-raya-graph-orientation-counts]"
                    ).inner_text()
                    assert "visible relationship" in page.locator(
                        "[data-raya-graph-orientation-counts]"
                    ).inner_text()
                    assert "Connections" in page.locator(
                        "[data-raya-graph-orientation-layout]"
                    ).inner_text()
                    assert "Projection Residuals" in page.locator(
                        "[data-raya-graph-orientation-selected]"
                    ).inner_text()
                    assert "Projection Residuals" in page.locator(
                        "[data-raya-graph-orientation-page-focus]"
                    ).inner_text()
                    assert "projection" in page.locator(
                        "[data-raya-graph-orientation-query]"
                    ).inner_text()
                    active_state = page.locator("[data-raya-graph-active-state]")
                    assert active_state.is_visible()
                    assert "Active" in active_state.inner_text()
                    assert "search" in active_state.inner_text().lower()
                    assert "selection" in active_state.inner_text().lower()
                    assert "All groups and relationships visible" in page.locator(
                        "[data-raya-graph-orientation-filters]"
                    ).inner_text()
                    open_from_orientation = page.locator(
                        "[data-raya-graph-orientation-open]"
                    )
                    assert open_from_orientation.is_visible()
                    assert open_from_orientation.get_attribute("href").endswith(
                        "/reader-ux/index.html"
                    )
                    details_from_orientation = page.locator(
                        "[data-raya-graph-orientation-details]"
                    )
                    assert details_from_orientation.is_visible()
                    details_from_orientation.click()
                    page.wait_for_function(
                        """() => document.activeElement?.closest(
                          '[data-raya-graph-detail-panel]'
                        ) !== null"""
                    )
                    assert "Projection Residuals" in page.locator(
                        "[data-raya-graph-detail-title]"
                    ).inner_text()
                    assert "projection" in page.locator("#graph-search").input_value()
                    assert "page=reader-ux" in page.url
                    orientation_focus = page.locator(
                        "[data-raya-graph-orientation-neighborhood-toggle]"
                    )
                    assert orientation_focus.is_visible()
                    orientation_focus.click()
                    page.wait_for_function(
                        "() => document.querySelector('[data-raya-graph-orientation-neighborhood]').textContent.includes('On')"
                    )
                    assert "neighborhood=1" in page.url
                    orientation_focus.click()
                    page.wait_for_function(
                        "() => document.querySelector('[data-raya-graph-orientation-neighborhood]').textContent.includes('Off')"
                    )
                    assert "neighborhood=1" not in page.url
                    debug = page.locator("[data-raya-graph-debug]")
                    assert debug.is_visible()
                    assert debug.get_attribute("open") is None
                    debug.locator("summary").click()
                    assert debug.get_attribute("open") == ""
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

                    page.select_option("#graph-layout", "radial")
                    page.wait_for_function(
                        """() => document
                          .querySelector('[data-raya-graph-active-state]')
                          ?.textContent.includes('layout')"""
                    )
                    assert "layout" in active_state.inner_text().lower()
                    assert "layout=radial" in page.url
                    page.select_option("#graph-layout", "connections")
                    page.wait_for_function(
                        "() => !new URL(window.location.href).searchParams.get('layout')"
                    )

                    page.click('[data-raya-graph-toggle-panel="list"]')
                    page.wait_for_function(
                        "() => new URL(window.location.href).searchParams.get('list') === '0'"
                    )
                    assert "list collapsed" in active_state.inner_text().lower()
                    assert "list=0" in page.locator(
                        "[data-raya-graph-state-url]"
                    ).inner_text()
                    list_rail_summary = page.locator(
                        '[data-raya-graph-panel-rail-summary="list"]'
                    )
                    assert list_rail_summary.is_visible()
                    assert (
                        list_rail_summary.get_attribute("aria-hidden")
                        == "false"
                    )
                    assert "visible page" in list_rail_summary.inner_text()
                    page.click('[data-raya-graph-toggle-panel="inspector"]')
                    page.wait_for_function(
                        "() => new URL(window.location.href).searchParams.get('inspector') === '0'"
                    )
                    assert "inspector=0" in page.locator(
                        "[data-raya-graph-state-url]"
                    ).inner_text()
                    inspector_rail_summary = page.locator(
                        '[data-raya-graph-panel-rail-summary="inspector"]'
                    )
                    assert inspector_rail_summary.is_visible()
                    assert (
                        inspector_rail_summary.get_attribute("aria-hidden")
                        == "false"
                    )
                    assert "Projection Residuals" in inspector_rail_summary.inner_text()
                    details_from_orientation.click()
                    page.wait_for_function(
                        """() => document
                          .querySelector('[data-raya-graph-page]')
                          ?.getAttribute('data-raya-graph-inspector-state') === 'expanded'
                          && document.activeElement?.closest(
                            '[data-raya-graph-detail-panel]'
                          ) !== null"""
                    )
                    assert "inspector=0" not in page.url
                    assert page.locator(
                        "[data-raya-graph-detail-panel]"
                    ).get_attribute("aria-labelledby") == "raya-graph-detail-title"
                    page.click('[data-raya-graph-toggle-panel="list"]')
                    page.wait_for_function(
                        """() => document
                          .querySelector('[data-raya-graph-page]')
                          ?.getAttribute('data-raya-graph-list-state') === 'expanded'
                          && document
                            .querySelector('[data-raya-graph-page]')
                            ?.getAttribute('data-raya-graph-inspector-state') === 'expanded'"""
                    )
                    assert list_rail_summary.is_hidden()
                    assert inspector_rail_summary.is_hidden()
                    assert (
                        list_rail_summary.get_attribute("aria-hidden")
                        == "true"
                    )
                    assert (
                        inspector_rail_summary.get_attribute("aria-hidden")
                        == "true"
                    )

                    page.goto(
                        f"{base_url}/_raya/graph/index.html",
                        wait_until="networkidle",
                    )
                    page.fill("#graph-search", "projection")
                    page.wait_for_function(
                        "() => new URL(window.location.href).searchParams.get('page') === 'reader-ux'"
                    )
                    page.locator("[data-raya-graph-debug] summary").click()
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
                    assert "Parent" in page.locator(
                        "[data-raya-graph-orientation-filters]"
                    ).inner_text()
                    assert "edges=" in page.url
                    assert "filters" in active_state.inner_text().lower()

                    page.locator("[data-raya-graph-group-filter]").first.click()
                    page.wait_for_function(
                        "() => new URL(window.location.href).searchParams.get('groups')"
                    )
                    assert "hidden" in page.locator(
                        "[data-raya-graph-state-hidden-groups]"
                    ).inner_text().lower()
                    assert "hidden group" in page.locator(
                        "[data-raya-graph-orientation-filters]"
                    ).inner_text().lower()
                    assert handle.base_url in page.locator(
                        "[data-raya-graph-state-url]"
                    ).inner_text()
                    assert "filters" in active_state.inner_text().lower()
                    page.click("#graph-reset")
                    page.wait_for_function(
                        """() => document
                          .querySelector('[data-raya-graph-active-state]')
                          ?.textContent.includes('Ready: full graph')"""
                    )
                    assert page.locator("#graph-search").input_value() == ""
                    assert page.locator("#graph-layout").input_value() == "connections"
                    assert "page=" not in page.url
                    assert "q=" not in page.url
                    assert "edges=" not in page.url
                    assert "groups=" not in page.url

                    page.fill("#graph-search", "projection")
                    page.wait_for_function(
                        "() => new URL(window.location.href).searchParams.get('page') === 'reader-ux'"
                    )
                    page.click('[data-raya-graph-edge-kind-filter="parent"]')
                    page.wait_for_function(
                        "() => new URL(window.location.href).searchParams.get('edges')"
                    )
                    page.locator("[data-raya-graph-group-filter]").first.click()
                    page.wait_for_function(
                        "() => new URL(window.location.href).searchParams.get('groups')"
                    )
                    copy_button = page.locator("[data-raya-graph-copy-url]")
                    assert copy_button.is_visible()
                    assert copy_button.inner_text() == "Copy URL"
                    copy_button.focus()
                    assert page.evaluate(
                        "() => document.activeElement === document.querySelector('[data-raya-graph-copy-url]')"
                    )
                    copy_button.click()
                    page.wait_for_function(
                        """() => window.__rayaCopiedGraphUrls.length === 1 &&
                          window.__rayaCopiedGraphUrls[0] === window.location.href"""
                    )
                    assert (
                        page.locator("[data-raya-graph-copy-status]").inner_text()
                        == "Copied graph URL."
                    )
                    long_query = "projection-" + "state-" * 40
                    page.goto(
                        f"{handle.base_url}/_raya/graph/index.html"
                        f"?page=reader-ux&q={long_query}",
                        wait_until="networkidle",
                    )
                    page.locator("[data-raya-graph-debug] summary").click()
                    _assert_no_horizontal_overflow(page)
                    page.evaluate(
                        """() => {
                          window.__rayaFallbackCopyAttempts = [];
                          Object.defineProperty(navigator, 'clipboard', {
                            configurable: true,
                            value: undefined,
                          });
                          document.execCommand = (command) => {
                            window.__rayaFallbackCopyAttempts.push({
                              command,
                              value: document.activeElement?.value || "",
                            });
                            return true;
                          };
                        }"""
                    )
                    page.click("[data-raya-graph-copy-url]")
                    page.wait_for_function(
                        """() => window.__rayaFallbackCopyAttempts.length === 1"""
                    )
                    assert page.evaluate(
                        "() => window.__rayaFallbackCopyAttempts[0]"
                    ) == {
                        "command": "copy",
                        "value": page.url,
                    }
                    assert (
                        page.locator("[data-raya-graph-copy-status]").inner_text()
                        == "Copied graph URL."
                    )

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


def test_render_fixture_graph_focus_mode_refits_selected_context(
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
                        f"{handle.base_url}/_raya/graph/index.html?page=reader-ux",
                        wait_until="networkidle",
                    )
                    page.wait_for_selector(
                        '#raya-graph-canvas [data-raya-graph-node="reader-ux"] '
                        ".raya-graph-node.is-selected"
                    )
                    before = page.locator("#raya-graph-canvas").bounding_box()
                    assert before is not None
                    page.click("#graph-expand")
                    page.wait_for_function(
                        """() => document
                          .querySelector('[data-raya-graph-page]')
                          ?.getAttribute('data-raya-graph-expanded') === 'true'"""
                    )
                    page.wait_for_function(
                        """() => {
                          const canvas = document.querySelector('#raya-graph-canvas');
                          if (!canvas) return false;
                          const rect = canvas.getBoundingClientRect();
                          return rect.height >= window.innerHeight * 0.8;
                        }"""
                    )
                    probe = page.evaluate(
                        """() => {
                          const canvas = document.querySelector('#raya-graph-canvas');
                          const selected = document.querySelector(
                            '#raya-graph-canvas [data-raya-graph-node="reader-ux"] g'
                          );
                          const edges = Array.from(
                            document.querySelectorAll('#raya-graph-canvas .raya-graph-edge')
                          );
                          const box = (node) => {
                            const rect = node.getBoundingClientRect();
                            return {
                              x: rect.x,
                              y: rect.y,
                              width: rect.width,
                              height: rect.height,
                            };
                          };
                          return {
                            canvas: box(canvas),
                            selected: selected ? box(selected) : null,
                            connectedEdges: edges
                              .filter((edge) => {
                                const from = edge.getAttribute('data-raya-graph-from') || '';
                                const to = edge.getAttribute('data-raya-graph-to') || '';
                                return from === 'reader-ux' || to === 'reader-ux';
                              })
                              .map(box),
                            viewport: {
                              x: 0,
                              y: 0,
                              width: window.innerWidth,
                              height: window.innerHeight,
                            },
                            rootExpanded: document
                              .querySelector('[data-raya-graph-page]')
                              ?.getAttribute('data-raya-graph-expanded'),
                            listState: document
                              .querySelector('[data-raya-graph-page]')
                              ?.getAttribute('data-raya-graph-list-state'),
                            inspectorState: document
                              .querySelector('[data-raya-graph-page]')
                              ?.getAttribute('data-raya-graph-inspector-state'),
                            storage: [
                              Object.keys(localStorage),
                              Object.keys(sessionStorage),
                            ],
                            overflow: Math.ceil(
                              document.documentElement.scrollWidth - window.innerWidth
                            ),
                          };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    visible_canvas = _intersection_box(probe["canvas"], probe["viewport"])
    assert probe["rootExpanded"] == "true"
    assert probe["listState"] == "collapsed"
    assert probe["inspectorState"] == "collapsed"
    assert probe["canvas"]["height"] >= probe["viewport"]["height"] * 0.8
    assert visible_canvas["height"] > probe["viewport"]["height"] * 0.45
    assert probe["selected"] is not None
    assert _boxes_intersect(visible_canvas, probe["selected"])
    assert any(
        _boxes_intersect(visible_canvas, edge) for edge in probe["connectedEdges"]
    )
    assert probe["storage"] == [[], []]
    assert probe["overflow"] <= 1


def test_render_fixture_graph_orientation_fit_selection_frames_context(
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
                        f"{handle.base_url}/_raya/graph/index.html?page=reader-ux",
                        wait_until="networkidle",
                    )
                    page.wait_for_selector(
                        '#raya-graph-canvas [data-raya-graph-node="reader-ux"] '
                        ".raya-graph-node.is-selected"
                    )
                    page.wait_for_selector(
                        "[data-raya-graph-detail-panel]:not([hidden])"
                    )
                    orientation_fit = page.locator(
                        "[data-raya-graph-orientation-fit-selection]"
                    )
                    assert orientation_fit.is_visible()
                    assert orientation_fit.is_enabled()
                    assert (
                        "Projection Residuals"
                        in page.locator("[data-raya-graph-detail-title]").inner_text()
                    )
                    page.fill("#graph-search", "projection")
                    page.wait_for_function(
                        """() => document
                          .querySelector('[data-raya-graph-orientation-query]')
                          ?.textContent === 'projection'"""
                    )
                    stable_url = page.url
                    before = page.locator("#raya-graph-canvas").get_attribute(
                        "viewBox"
                    )
                    page.click("#graph-zoom-in")
                    page.click('[data-raya-graph-pan="right"]')
                    page.wait_for_function(
                        """(previousViewBox) => document
                          .querySelector('#raya-graph-canvas')
                          ?.getAttribute('viewBox') !== previousViewBox""",
                        arg=before,
                    )
                    drifted = page.locator("#raya-graph-canvas").get_attribute(
                        "viewBox"
                    )
                    orientation_fit.click()
                    page.wait_for_function(
                        """(previousViewBox) => document
                          .querySelector('#raya-graph-canvas')
                          ?.getAttribute('viewBox') !== previousViewBox""",
                        arg=drifted,
                    )
                    fitted = page.locator("#raya-graph-canvas").get_attribute(
                        "viewBox"
                    )
                    context = _visible_graph_context(
                        page, "reader-ux", {"width": 1440, "height": 950}
                    )
                    state = page.evaluate(
                        """() => ({
                          detailVisible: !document
                            .querySelector('[data-raya-graph-detail-panel]')
                            ?.hasAttribute('hidden'),
                          detailTitle: document
                            .querySelector('[data-raya-graph-detail-title]')
                            ?.textContent.trim(),
                          search: document.querySelector('#graph-search')?.value,
                          selected: document
                            .querySelector('[data-raya-graph-orientation-selected]')
                            ?.textContent.trim(),
                          storage: [
                            Object.keys(localStorage),
                            Object.keys(sessionStorage),
                          ],
                          overflow: Math.ceil(
                            document.documentElement.scrollWidth - window.innerWidth
                          ),
                        })"""
                    )
                    after_fit_url = page.url
                    page.select_option("#graph-layout", "list")
                    page.wait_for_function(
                        """() => document
                          .querySelector('[data-raya-graph-page]')
                          ?.getAttribute('data-raya-graph-layout') === 'list'"""
                    )
                    list_state = page.evaluate(
                        """() => {
                          const action = document.querySelector(
                            '[data-raya-graph-orientation-fit-selection]'
                          );
                          return {
                            hidden: action?.hasAttribute('hidden'),
                            disabled: action?.hasAttribute('disabled'),
                            selected: document
                              .querySelector('[data-raya-graph-orientation-selected]')
                              ?.textContent.trim(),
                            storage: [
                              Object.keys(localStorage),
                              Object.keys(sessionStorage),
                            ],
                          };
                        }"""
                    )
                    page.select_option("#graph-layout", "connections")
                    page.wait_for_function(
                        """() => document
                          .querySelector('[data-raya-graph-page]')
                          ?.getAttribute('data-raya-graph-layout') === 'connections'"""
                    )
                    page.click("[data-raya-graph-orientation-clear]")
                    clear_state = page.evaluate(
                        """() => {
                          const action = document.querySelector(
                            '[data-raya-graph-orientation-fit-selection]'
                          );
                          return {
                            hidden: action?.hasAttribute('hidden'),
                            disabled: action?.hasAttribute('disabled'),
                            selected: document
                              .querySelector('[data-raya-graph-orientation-selected]')
                              ?.textContent.trim(),
                            storage: [
                              Object.keys(localStorage),
                              Object.keys(sessionStorage),
                            ],
                          };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert fitted != drifted
    assert fitted != before
    assert context["selectedVisible"]
    assert context["activeEdgeVisible"]
    assert state["detailVisible"] is True
    assert "Projection Residuals" in state["detailTitle"]
    assert state["selected"] == "Projection Residuals"
    assert state["search"] == "projection"
    assert after_fit_url == stable_url
    assert state["storage"] == [[], []]
    assert state["overflow"] <= 1
    assert list_state["hidden"] is True
    assert list_state["disabled"] is True
    assert list_state["selected"] == "Projection Residuals"
    assert list_state["storage"] == [[], []]
    assert clear_state["hidden"] is True
    assert clear_state["disabled"] is True
    assert clear_state["selected"] == "None"
    assert clear_state["storage"] == [[], []]


def test_render_fixture_graph_detail_shows_public_section_jumps(
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
                        f"{handle.base_url}/_raya/graph/index.html?page=authoring-matrix",
                        wait_until="networkidle",
                    )
                    page.wait_for_selector(
                        '#raya-graph-canvas '
                        '[data-raya-graph-node="authoring-matrix"] '
                        ".raya-graph-node.is-selected"
                    )
                    page.wait_for_selector(
                        "[data-raya-graph-detail-panel]:not([hidden])"
                    )
                    section_block = page.locator(
                        "[data-raya-graph-detail-sections]"
                    )
                    assert section_block.is_visible()
                    section_link = section_block.locator("a").filter(
                        has_text="Matrix norm fixture"
                    ).first
                    assert section_link.is_visible()
                    state = page.evaluate(
                        """() => {
                          const detail = document.querySelector(
                            '[data-raya-graph-detail-panel]'
                          );
                          const sectionBlock = document.querySelector(
                            '[data-raya-graph-detail-sections]'
                          );
                          const sectionLink = Array.from(
                            sectionBlock?.querySelectorAll('a') || []
                          ).find((link) =>
                            link.textContent.includes('Matrix norm fixture')
                          );
                          return {
                            detailTitle: document
                              .querySelector('[data-raya-graph-detail-title]')
                              ?.textContent.trim(),
                            sectionHref: sectionLink?.getAttribute('href') || '',
                            sectionText: sectionLink?.textContent.trim() || '',
                            pageParam: new URL(window.location.href)
                              .searchParams.get('page'),
                            detailHtml: detail?.innerHTML || '',
                            storage: [
                              Object.keys(localStorage),
                              Object.keys(sessionStorage),
                            ],
                            overflow: Math.ceil(
                              document.documentElement.scrollWidth - window.innerWidth
                            ),
                          };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert state["detailTitle"] == "Authoring Matrix Fixture"
    assert "Matrix norm fixture" in state["sectionText"]
    assert state["sectionHref"].endswith(
        "/authoring-matrix/index.html#raya-object-authoring-theorem"
    )
    assert state["pageParam"] == "authoring-matrix"
    assert state["storage"] == [[], []]
    assert state["overflow"] <= 1
    detail_html = state["detailHtml"].lower()
    for forbidden in (
        "_official",
        "_reviewed",
        "_assets",
        "source_path",
        "artifact",
        "mjx-container",
        "\\begin",
        "progress",
        "recommend",
        "mastery",
    ):
        assert forbidden not in detail_html


def test_render_fixture_graph_minimap_tracks_viewport(tmp_path: Path) -> None:
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
        base_url = handle.base_url
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
                        f"{base_url}/_raya/graph/index.html?page=reader-ux",
                        wait_until="networkidle",
                    )
                    page.wait_for_selector(
                        '#raya-graph-canvas [data-raya-graph-node="reader-ux"] '
                        ".raya-graph-node.is-selected"
                    )
                    page.wait_for_selector(
                        "#raya-graph-minimap [data-raya-graph-minimap-node]"
                    )
                    before = page.evaluate(
                        """() => {
                          const minimap = document.querySelector('#raya-graph-minimap');
                          const viewport = minimap?.querySelector(
                            '[data-raya-graph-minimap-viewport]'
                          );
                          const selected = document.querySelector(
                            '#raya-graph-canvas [data-raya-graph-node="reader-ux"] '
                            + '.raya-graph-node.is-selected'
                          );
                          const box = (node) => {
                            const rect = node.getBoundingClientRect();
                            return {
                              x: rect.x,
                              y: rect.y,
                              width: rect.width,
                              height: rect.height,
                            };
                          };
                          return {
                            minimap: box(minimap),
                            viewport: box(viewport),
                            viewportX: Number(viewport?.getAttribute('x') || '0'),
                            viewBox: minimap?.getAttribute('viewBox'),
                            nodes: minimap?.querySelectorAll(
                              '[data-raya-graph-minimap-node]'
                            ).length,
                            edges: minimap?.querySelectorAll(
                              '[data-raya-graph-minimap-edge]'
                            ).length,
                            selected: Boolean(selected),
                            storage: [
                              Object.keys(localStorage),
                              Object.keys(sessionStorage),
                            ],
                            overflow: Math.ceil(
                              document.documentElement.scrollWidth - window.innerWidth
                            ),
                          };
                        }"""
                    )
                    requested_urls.clear()
                    page.click("#graph-zoom-in")
                    page.click('[data-raya-graph-pan="right"]')
                    page.wait_for_function(
                        """(beforeX) => {
                          const viewport = document.querySelector(
                            '#raya-graph-minimap [data-raya-graph-minimap-viewport]'
                          );
                          if (!viewport) return false;
                          const x = Number(viewport.getAttribute('x') || '0');
                          return Math.abs(x - beforeX) > 0.01;
                        }""",
                        arg=before["viewportX"],
                    )
                    after = page.evaluate(
                        """() => {
                          const canvas = document.querySelector('#raya-graph-canvas');
                          const viewport = document.querySelector(
                            '#raya-graph-minimap [data-raya-graph-minimap-viewport]'
                          );
                          const selected = document.querySelector(
                            '#raya-graph-canvas [data-raya-graph-node="reader-ux"] '
                            + '.raya-graph-node.is-selected'
                          );
                          const rect = viewport.getBoundingClientRect();
                          return {
                            viewport: {
                              x: rect.x,
                              y: rect.y,
                              width: rect.width,
                              height: rect.height,
                            },
                            canvasViewBox: canvas?.getAttribute('viewBox'),
                            viewportX: Number(viewport.getAttribute('x') || '0'),
                            selected: Boolean(selected),
                            storage: [
                              Object.keys(localStorage),
                              Object.keys(sessionStorage),
                            ],
                          };
                        }"""
                    )
                    minimap = page.locator("#raya-graph-minimap")
                    minimap.scroll_into_view_if_needed()
                    minimap_box = minimap.bounding_box()
                    assert minimap_box is not None
                    requested_urls.clear()
                    minimap.click(
                        position={
                            "x": minimap_box["width"] * 0.18,
                            "y": minimap_box["height"] * 0.5,
                        }
                    )
                    page.wait_for_function(
                        """(previousViewBox) => {
                          const canvas = document.querySelector('#raya-graph-canvas');
                          return canvas?.getAttribute('viewBox') !== previousViewBox;
                        }""",
                        arg=after["canvasViewBox"],
                    )
                    clicked = page.evaluate(
                        """() => {
                          const canvas = document.querySelector('#raya-graph-canvas');
                          const minimap = document.querySelector('#raya-graph-minimap');
                          const viewport = minimap?.querySelector(
                            '[data-raya-graph-minimap-viewport]'
                          );
                          const selected = document.querySelector(
                            '#raya-graph-canvas [data-raya-graph-node="reader-ux"] '
                            + '.raya-graph-node.is-selected'
                          );
                          return {
                            canvasViewBox: canvas?.getAttribute('viewBox'),
                            viewportX: Number(viewport?.getAttribute('x') || '0'),
                            selected: Boolean(selected),
                            storage: [
                              Object.keys(localStorage),
                              Object.keys(sessionStorage),
                            ],
                            role: minimap?.getAttribute('role'),
                            tabIndex: minimap?.getAttribute('tabindex'),
                            label: minimap?.getAttribute('aria-label'),
                            overflow: Math.ceil(
                              document.documentElement.scrollWidth - window.innerWidth
                            ),
                          };
                        }"""
                    )
                    requested_urls.clear()
                    page.click('[data-raya-graph-pan="right"]')
                    keyboard_before = page.locator("#raya-graph-canvas").get_attribute(
                        "viewBox"
                    )
                    minimap.focus()
                    page.keyboard.press("Enter")
                    page.wait_for_function(
                        """(previousViewBox) => {
                          const canvas = document.querySelector('#raya-graph-canvas');
                          return canvas?.getAttribute('viewBox') !== previousViewBox;
                        }""",
                        arg=keyboard_before,
                    )
                    keyboarded = page.evaluate(
                        """() => {
                          const canvas = document.querySelector('#raya-graph-canvas');
                          const minimap = document.querySelector('#raya-graph-minimap');
                          const viewport = minimap?.querySelector(
                            '[data-raya-graph-minimap-viewport]'
                          );
                          const selected = document.querySelector(
                            '#raya-graph-canvas [data-raya-graph-node="reader-ux"] '
                            + '.raya-graph-node.is-selected'
                          );
                          return {
                            canvasViewBox: canvas?.getAttribute('viewBox'),
                            viewportX: Number(viewport?.getAttribute('x') || '0'),
                            selected: Boolean(selected),
                            storage: [
                              Object.keys(localStorage),
                              Object.keys(sessionStorage),
                            ],
                          };
                        }"""
                    )
                    page.select_option("#graph-layout", "list")
                    page.wait_for_function(
                        """() => document
                          .querySelector('[data-raya-graph-page]')
                          ?.getAttribute('data-raya-graph-layout') === 'list'"""
                    )
                    list_state = page.evaluate(
                        """() => {
                          const canvas = document.querySelector('#raya-graph-canvas');
                          const minimap = document.querySelector('#raya-graph-minimap');
                          const selected = document.querySelector(
                            '#raya-graph-list [data-raya-graph-node="reader-ux"].is-active'
                          );
                          return {
                            canvasHidden: canvas?.hasAttribute('hidden'),
                            minimapChildren: minimap?.children.length,
                            ariaDisabled: minimap?.getAttribute('aria-disabled'),
                            tabIndex: minimap?.getAttribute('tabindex'),
                            selected: Boolean(selected),
                            storage: [
                              Object.keys(localStorage),
                              Object.keys(sessionStorage),
                            ],
                          };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert before["minimap"]["width"] >= 120
    assert before["minimap"]["height"] >= 80
    assert before["viewBox"]
    assert before["nodes"] >= 3
    assert before["edges"] >= 1
    assert before["viewport"]["width"] > 0
    assert before["viewport"]["height"] > 0
    assert before["selected"] is True
    assert after["selected"] is True
    assert after["viewportX"] != before["viewportX"]
    assert after["viewport"] != before["viewport"]
    assert clicked["selected"] is True
    assert clicked["canvasViewBox"] != after["canvasViewBox"]
    assert clicked["viewportX"] != after["viewportX"]
    assert clicked["role"] == "button"
    assert clicked["tabIndex"] == "0"
    assert "center the graph view" in clicked["label"]
    assert keyboarded["selected"] is True
    assert keyboarded["canvasViewBox"] != keyboard_before
    assert keyboarded["viewportX"] != clicked["viewportX"]
    assert list_state["canvasHidden"] is True
    assert list_state["minimapChildren"] == 0
    assert list_state["ariaDisabled"] == "true"
    assert list_state["tabIndex"] == "-1"
    assert list_state["selected"] is True
    assert before["storage"] == [[], []]
    assert after["storage"] == [[], []]
    assert clicked["storage"] == [[], []]
    assert keyboarded["storage"] == [[], []]
    assert list_state["storage"] == [[], []]
    assert before["overflow"] <= 1
    assert clicked["overflow"] <= 1
    assert all(url.startswith(f"{base_url}/") for url in requested_urls)


def test_render_fixture_graph_search_matches_key_object_text(tmp_path: Path) -> None:
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
        base_url = handle.base_url
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
                        f"{base_url}/_raya/graph/index.html",
                        wait_until="networkidle",
                    )
                    page.fill("#graph-search", "projection triangle")
                    page.wait_for_function(
                        "() => new URL(window.location.href).searchParams.get('page') === 'reader-ux'"
                    )
                    state = page.evaluate(
                        """() => ({
                          selected: document
                            .querySelector('[data-raya-graph-state-selected]')
                            ?.textContent.trim() || '',
                          title: document
                            .querySelector('[data-raya-graph-detail-title]')
                            ?.textContent.trim() || '',
                          keyObjects: Array.from(
                            document.querySelectorAll('[data-raya-graph-detail-key-objects] a')
                          ).map((link) => ({
                            text: link.textContent.trim(),
                            href: link.getAttribute('href') || '',
                          })),
                          activeListText: document
                            .querySelector('#raya-graph-list [data-raya-graph-node="reader-ux"]')
                            ?.textContent.trim() || '',
                          storage: [
                            Object.keys(localStorage),
                            Object.keys(sessionStorage),
                          ],
                          overflow: Math.ceil(
                            document.documentElement.scrollWidth - window.innerWidth
                          ),
                        })"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert "reader-ux" in state["selected"]
    assert state["title"] == "Projection Residuals"
    assert "Projection Residuals" in state["activeListText"]
    assert any(
        item["text"].startswith("Figure 4.1 Projection triangle")
        and item["href"].endswith(
            "/reader-ux/index.html#raya-object-orthogonal-figure"
        )
        for item in state["keyObjects"]
    )
    assert state["storage"] == [[], []]
    assert state["overflow"] <= 1
    assert requested_urls
    assert all(url.startswith(f"{base_url}/") for url in requested_urls)


def test_render_fixture_graph_relationship_edges_are_inspectable(
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
                requested_urls: list[str] = []
                page.on("request", lambda request: requested_urls.append(request.url))
                try:
                    page.goto(
                        f"{handle.base_url}/_raya/graph/index.html",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(page)
                    edge_info = page.evaluate(
                        """() => {
                          const hit = document.querySelector('[data-raya-graph-edge-hit]');
                          const payload = JSON.parse(
                            document.getElementById('raya-graph-data').textContent
                          );
                          const from = hit?.getAttribute('data-raya-graph-from') || '';
                          const to = hit?.getAttribute('data-raya-graph-to') || '';
                          const kind = hit?.getAttribute('data-raya-graph-kind') || '';
                          const nodeById = new Map(payload.nodes.map((node) => [node.id, node]));
                          return {
                            from,
                            to,
                            kind,
                            kindLabel: hit?.getAttribute('aria-label')?.split(':')[0] || kind,
                            fromTitle: nodeById.get(from)?.title || from,
                            toTitle: nodeById.get(to)?.title || to,
                          };
                        }"""
                    )
                    assert edge_info["from"]
                    assert edge_info["to"]
                    edge = page.locator("[data-raya-graph-edge-hit]").first
                    edge.focus()
                    preview = page.locator("[data-raya-graph-relationship-preview]")
                    page.wait_for_function(
                        """() => !document
                          .querySelector('[data-raya-graph-relationship-preview]')
                          ?.hasAttribute('hidden')"""
                    )
                    assert preview.is_visible()
                    preview_text = preview.inner_text()
                    assert edge_info["fromTitle"] in preview_text
                    assert edge_info["toTitle"] in preview_text
                    assert edge_info["kind"] in preview_text.lower()
                    assert "source to target" in preview_text.lower()
                    assert page.locator(
                        "#raya-graph-canvas [data-raya-graph-edge].is-edge-inspected"
                    ).count() == 1
                    assert page.locator(
                        "#raya-graph-canvas .raya-graph-node.is-edge-endpoint"
                    ).count() >= 2

                    page.locator(
                        "[data-raya-graph-relationship-preview-source-action]"
                    ).click()
                    page.wait_for_function(
                        """title => document
                          .querySelector('[data-raya-graph-orientation-selected]')
                          ?.textContent.includes(title)""",
                        arg=edge_info["fromTitle"],
                    )
                    assert edge_info["from"] in page.url

                    edge.focus()
                    page.wait_for_function(
                        """() => !document
                          .querySelector('[data-raya-graph-relationship-preview]')
                          ?.hasAttribute('hidden')"""
                    )
                    target_info = page.evaluate(
                        """() => {
                          const hit = document.activeElement?.matches('[data-raya-graph-edge-hit]')
                            ? document.activeElement
                            : document.querySelector('[data-raya-graph-edge-hit]');
                          const payload = JSON.parse(
                            document.getElementById('raya-graph-data').textContent
                          );
                          const to = hit?.getAttribute('data-raya-graph-to') || '';
                          const nodeById = new Map(payload.nodes.map((node) => [node.id, node]));
                          return {
                            to,
                            toTitle: nodeById.get(to)?.title || to,
                          };
                        }"""
                    )
                    page.locator(
                        "[data-raya-graph-relationship-preview-target-action]"
                    ).click()
                    page.wait_for_function(
                        """title => document
                          .querySelector('[data-raya-graph-orientation-selected]')
                          ?.textContent.includes(title)""",
                        arg=target_info["toTitle"],
                    )
                    assert target_info["to"] in page.url
                    edge.focus()
                    page.wait_for_function(
                        """() => !document
                          .querySelector('[data-raya-graph-relationship-preview]')
                          ?.hasAttribute('hidden')"""
                    )
                    page.locator(
                        "[data-raya-graph-relationship-preview-kind-action]"
                    ).click()
                    focus_summary = page.locator(
                        "[data-raya-graph-relationship-focus-summary]"
                    )
                    page.wait_for_function(
                        """kindLabel => document
                          .querySelector('[data-raya-graph-relationship-focus-summary]')
                          ?.textContent.includes(`Showing ${kindLabel} out relationships.`)""",
                        arg=edge_info["kindLabel"],
                    )
                    assert page.locator(
                        "[data-raya-graph-relationship-focus-reset]"
                    ).is_visible()
                    assert (
                        f"Showing {edge_info['kindLabel']} out relationships."
                        in focus_summary.inner_text()
                    )
                    assert edge_info["from"] in page.url
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


def test_render_fixture_graph_guide_uses_viewport_specific_movement_guidance(
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
                desktop = browser.new_page(viewport={"width": 1440, "height": 950})
                mobile = browser.new_page(viewport={"width": 390, "height": 844})
                try:
                    desktop.goto(
                        f"{handle.base_url}/_raya/graph/index.html",
                        wait_until="networkidle",
                    )
                    mobile.goto(
                        f"{handle.base_url}/_raya/graph/index.html",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(desktop)
                    _assert_no_horizontal_overflow(mobile)
                    assert mobile.locator(
                        "[data-raya-graph-shortcut='search']"
                    ).is_visible()
                    assert mobile.locator(
                        "[data-raya-graph-shortcut='fit']"
                    ).is_visible()
                    assert mobile.locator(
                        "[data-raya-graph-shortcut='reset']"
                    ).is_visible()
                    assert mobile.locator(".raya-graph-canvas-hint").is_visible()

                    desktop_guide = desktop.locator("[data-raya-graph-guide]")
                    mobile_guide = mobile.locator("[data-raya-graph-guide]")
                    desktop_guide.locator("summary").click()
                    mobile_guide.locator("summary").click()
                    desktop_guide_text = desktop_guide.inner_text()
                    mobile_guide_text = mobile_guide.inner_text()

                    assert (
                        "On desktop, drag pages to tidy the map" in desktop_guide_text
                    )
                    assert "Use Fit, zoom, and pan controls" not in desktop_guide_text
                    assert (
                        "On desktop, drag pages to tidy the map"
                        not in mobile_guide_text
                    )
                    assert "Use Fit, zoom, and pan controls" in mobile_guide_text
                    assert (
                        "Reset graph restores the generated layout"
                        in mobile_guide_text
                    )
                finally:
                    desktop.close()
                    mobile.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_graph_keyboard_shortcuts_control_workspace(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.base_url is not None
        graph_html = _fetch_text(f"{handle.base_url}/_raya/graph/index.html")
        assert "Keyboard shortcuts" in graph_html
        assert "/ focuses graph search" in graph_html
        assert "F fits the current graph view" in graph_html
        assert "R resets graph filters and selection" in graph_html

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 950})
                page.goto(
                    f"{handle.base_url}/_raya/graph/index.html",
                    wait_until="networkidle",
                )
                assert page.locator("[data-raya-graph-shortcut='search']").is_visible()
                assert page.locator("[data-raya-graph-shortcut='fit']").is_visible()
                assert page.locator("[data-raya-graph-shortcut='reset']").is_visible()
                assert page.locator(".raya-graph-canvas-hint").is_visible()
                _assert_no_horizontal_overflow(page)
                page.locator("#raya-graph-canvas").focus()
                page.keyboard.press("/")
                page.wait_for_function(
                    "() => document.activeElement?.id === 'graph-search'"
                )
                page.keyboard.type("matrix")
                assert page.locator("#graph-search").input_value() == "matrix"
                page.keyboard.press("r")
                assert page.locator("#graph-search").input_value() == "matrixr"
                page.fill("#graph-search", "matrix")

                page.locator("#graph-reset-view").focus()
                page.keyboard.press("r")
                assert page.locator("#graph-search").input_value() == "matrix"

                page.locator("#raya-graph-canvas").focus()
                page.click("#graph-zoom-in")
                zoomed_viewbox = page.locator("#raya-graph-canvas").get_attribute(
                    "viewBox"
                )
                page.locator("#raya-graph-canvas").focus()
                page.keyboard.press("f")
                page.wait_for_function(
                    """(previous) => document
                      .querySelector('#raya-graph-canvas')
                      ?.getAttribute('viewBox') !== previous""",
                    arg=zoomed_viewbox,
                )

                page.click('[data-raya-graph-group-filter="reader-ux"]')
                assert (
                    page.locator('[data-raya-graph-group-filter="reader-ux"]')
                    .get_attribute("aria-pressed")
                    == "false"
                )
                page.click('[data-raya-graph-edge-kind-filter="content"]')
                assert (
                    page.locator('[data-raya-graph-edge-kind-filter="content"]')
                    .get_attribute("aria-pressed")
                    == "false"
                )
                _click_graph_node_group(page, "authoring-matrix")
                page.wait_for_function(
                    """() => document
                      .querySelector('[data-raya-graph-orientation-selected]')
                      ?.textContent
                      ?.includes('Authoring Matrix Fixture')"""
                )
                page.locator("#raya-graph-canvas").focus()
                page.keyboard.press("r")
                page.wait_for_function(
                    "() => document.querySelector('#graph-search')?.value === ''"
                )
                assert (
                    page.locator("[data-raya-graph-page]").get_attribute(
                        "data-raya-graph-layout"
                    )
                    == "connections"
                )
                assert (
                    page.locator('[data-raya-graph-group-filter="reader-ux"]')
                    .get_attribute("aria-pressed")
                    == "true"
                )
                assert (
                    page.locator('[data-raya-graph-edge-kind-filter="content"]')
                    .get_attribute("aria-pressed")
                    == "true"
                )
                assert (
                    page.locator(
                        "[data-raya-graph-orientation-selected]"
                    ).inner_text()
                    == "None"
                )
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_graph_focus_route_affordances_are_explicit(
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
                        f"{handle.base_url}/_raya/graph/index.html",
                        wait_until="networkidle",
                    )
                    page.locator(
                        '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"] '
                        ".raya-graph-node-hit"
                    ).hover()
                    page.wait_for_function(
                        """() => document
                          .querySelector('#raya-graph-canvas .raya-graph-node.is-focus-origin') !== null"""
                    )
                    route_state = page.evaluate(
                        """() => {
                          const nodeClass = (id) => Array.from(document
                            .querySelector(
                              `#raya-graph-canvas [data-raya-graph-node="${id}"] g`
                            )
                            ?.classList || []);
                          const focusRoutes = Array.from(document.querySelectorAll(
                            '#raya-graph-canvas .raya-graph-edge.is-focus-route'
                          ));
                          const dimmedRoutes = focusRoutes.filter((edge) =>
                            edge.classList.contains('is-dimmed')
                          );
                          const markerStates = focusRoutes.map((edge) => {
                            const markerId = edge
                              .getAttribute('marker-end')
                              ?.replace(/^url\\(#/, '')
                              ?.replace(/\\)$/, '');
                            const marker = markerId ? document.getElementById(markerId) : null;
                            return Boolean(marker?.classList.contains('is-focus-route'));
                          });
                          const routeStyles = focusRoutes.map((edge) => {
                            const style = getComputedStyle(edge);
                            return {
                              strokeWidth: Number.parseFloat(style.strokeWidth || '0'),
                              opacity: Number.parseFloat(style.strokeOpacity || '0'),
                            };
                          });
                          return {
                            origin: nodeClass('authoring-matrix'),
                            renderRoot: nodeClass('render-root'),
                            mathAuthoring: nodeClass('math-authoring'),
                            staticPath: nodeClass('static-path'),
                            focusRouteCount: focusRoutes.length,
                            dimmedRouteCount: dimmedRoutes.length,
                            markerStates,
                            routeStyles,
                          };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert "is-focus-origin" in route_state["origin"]
    assert "is-focus-endpoint" in route_state["renderRoot"]
    assert "is-focus-endpoint" in route_state["mathAuthoring"]
    assert "is-focus-endpoint" not in route_state["staticPath"]
    assert "is-dimmed" in route_state["staticPath"]
    assert route_state["focusRouteCount"] >= 4
    assert route_state["dimmedRouteCount"] == 0
    assert all(route_state["markerStates"])
    assert all(style["strokeWidth"] >= 3.4 for style in route_state["routeStyles"])
    assert all(style["opacity"] >= 0.88 for style in route_state["routeStyles"])


def test_render_fixture_graph_selection_mutes_unrelated_edges(
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
                        f"{handle.base_url}/_raya/graph/index.html",
                        wait_until="networkidle",
                    )
                    page.locator(
                        '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"] '
                        ".raya-graph-node-hit"
                    ).click()
                    page.wait_for_function(
                        """() => document
                          .querySelector('#raya-graph-canvas .raya-graph-edge.is-active') !== null"""
                    )
                    edge_state = page.evaluate(
                        """() => {
                          const classesForEdge = (from, to) => Array.from(document
                            .querySelector(
                              `#raya-graph-canvas .raya-graph-edge[data-raya-graph-from="${from}"][data-raya-graph-to="${to}"]`
                            )
                            ?.classList || []);
                          const markerForEdge = (from, to) => Array.from(document
                            .querySelector(
                              `#raya-graph-canvas .raya-graph-arrow-marker[data-raya-graph-from="${from}"][data-raya-graph-to="${to}"]`
                            )
                            ?.classList || []);
                          const connectedEdge = document.querySelector(
                            '#raya-graph-canvas .raya-graph-edge[data-raya-graph-from="authoring-matrix"][data-raya-graph-to="math-authoring"]'
                          );
                          const mutedEdge = document.querySelector(
                            '#raya-graph-canvas .raya-graph-edge[data-raya-graph-from="render-root"][data-raya-graph-to="static-path"]'
                          );
                          const connectedStyle = connectedEdge ? getComputedStyle(connectedEdge) : null;
                          const mutedStyle = mutedEdge ? getComputedStyle(mutedEdge) : null;
                          return {
                            connected: classesForEdge('authoring-matrix', 'math-authoring'),
                            unrelated: classesForEdge('render-root', 'static-path'),
                            unrelatedMarker: markerForEdge('render-root', 'static-path'),
                            connectedOpacity: connectedStyle
                              ? Number.parseFloat(connectedStyle.strokeOpacity || '0')
                              : 0,
                            mutedOpacity: mutedStyle
                              ? Number.parseFloat(mutedStyle.strokeOpacity || '0')
                              : 0,
                          };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert "is-active" in edge_state["connected"]
    assert "is-selection-muted" not in edge_state["connected"]
    assert "is-selection-muted" in edge_state["unrelated"]
    assert "is-selection-muted" in edge_state["unrelatedMarker"]
    assert edge_state["mutedOpacity"] < edge_state["connectedOpacity"]


def test_render_fixture_graph_layers_muted_edges_below_emphasized_edges(
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
                        f"{handle.base_url}/_raya/graph/index.html",
                        wait_until="networkidle",
                    )
                    page.locator(
                        '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"] '
                        ".raya-graph-node-hit"
                    ).click()
                    page.wait_for_function(
                        """() => document
                          .querySelector('#raya-graph-canvas .raya-graph-edge.is-active') !== null"""
                    )
                    edge_order = page.evaluate(
                        """() => Array.from(
                          document.querySelectorAll('#raya-graph-canvas .raya-graph-edge')
                        ).map((edge, index) => ({
                          index,
                          from: edge.getAttribute('data-raya-graph-from'),
                          to: edge.getAttribute('data-raya-graph-to'),
                          markerMatches: (() => {
                            const markerId = (edge.getAttribute('marker-end') || '')
                              .replace(/^url\\(#/, '')
                              .replace(/\\)$/, '');
                            const marker = document.getElementById(markerId);
                            return Boolean(marker) &&
                              marker.getAttribute('data-raya-graph-from') === edge.getAttribute('data-raya-graph-from') &&
                              marker.getAttribute('data-raya-graph-to') === edge.getAttribute('data-raya-graph-to') &&
                              marker.getAttribute('data-raya-graph-kind') === edge.getAttribute('data-raya-graph-kind');
                          })(),
                          classes: Array.from(edge.classList),
                        }))"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    muted_indexes = [
        edge["index"]
        for edge in edge_order
        if "is-selection-muted" in edge["classes"]
    ]
    emphasized_indexes = [
        edge["index"]
        for edge in edge_order
        if "is-active" in edge["classes"]
    ]
    assert muted_indexes
    assert emphasized_indexes
    assert max(muted_indexes) < min(emphasized_indexes)
    assert all(edge["markerMatches"] for edge in edge_order)


def test_render_fixture_graph_reorders_edges_after_hover_inspection(
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
                        f"{handle.base_url}/_raya/graph/index.html",
                        wait_until="networkidle",
                    )
                    page.locator(
                        '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"] '
                        ".raya-graph-node-hit"
                    ).hover()
                    page.wait_for_function(
                        """() => document
                          .querySelector('#raya-graph-canvas .raya-graph-edge.is-focus-route') !== null"""
                    )
                    edge_order = page.evaluate(
                        """() => Array.from(
                          document.querySelectorAll('#raya-graph-canvas .raya-graph-edge')
                        ).map((edge, index) => ({
                          index,
                          classes: Array.from(edge.classList),
                        }))"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    dimmed_indexes = [
        edge["index"] for edge in edge_order if "is-dimmed" in edge["classes"]
    ]
    focus_indexes = [
        edge["index"] for edge in edge_order if "is-focus-route" in edge["classes"]
    ]
    assert dimmed_indexes
    assert focus_indexes
    assert max(dimmed_indexes) < min(focus_indexes)


def test_render_fixture_graph_visual_depth_styles_are_rendered(
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
                        f"{handle.base_url}/_raya/graph/index.html",
                        wait_until="networkidle",
                    )
                    page.locator(
                        '#raya-graph-canvas [data-raya-graph-node="authoring-matrix"] '
                        ".raya-graph-node-hit"
                    ).click()
                    page.wait_for_function(
                        """() => document
                          .querySelector('#raya-graph-canvas .raya-graph-node.is-selected') !== null"""
                    )
                    visual_state = page.evaluate(
                        """() => {
                          const canvas = document.querySelector('#raya-graph-canvas');
                          const selectedCircle = document.querySelector(
                            '#raya-graph-canvas .raya-graph-node.is-selected .raya-graph-node-mark'
                          );
                          const selectedHit = document.querySelector(
                            '#raya-graph-canvas .raya-graph-node.is-selected .raya-graph-node-hit'
                          );
                          const selectedLabel = document.querySelector(
                            '#raya-graph-canvas .raya-graph-node.is-selected text'
                          );
                          const baseCircle = document.querySelector(
                            '#raya-graph-canvas .raya-graph-node:not(.is-selected) .raya-graph-node-mark'
                          );
                          const canvasStyle = getComputedStyle(canvas);
                          const selectedCircleStyle = getComputedStyle(selectedCircle);
                          const selectedHitStyle = getComputedStyle(selectedHit);
                          const selectedLabelStyle = getComputedStyle(selectedLabel);
                          const baseCircleStyle = getComputedStyle(baseCircle);
                          return {
                            canvasBackgroundImage: canvasStyle.backgroundImage,
                            canvasBoxShadow: canvasStyle.boxShadow,
                            selectedFilter: selectedCircleStyle.filter,
                            selectedStrokeWidth: Number.parseFloat(
                              selectedCircleStyle.strokeWidth || '0'
                            ),
                            selectedHitFill: selectedHitStyle.fill,
                            selectedHitFilter: selectedHitStyle.filter,
                            selectedHitStrokeWidth: Number.parseFloat(
                              selectedHitStyle.strokeWidth || '0'
                            ),
                            baseFilter: baseCircleStyle.filter,
                            labelPaintOrder: selectedLabelStyle.paintOrder,
                            labelStrokeWidth: Number.parseFloat(
                              selectedLabelStyle.strokeWidth || '0'
                            ),
                            labelStrokeLinejoin: selectedLabelStyle.strokeLinejoin,
                          };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert "gradient" in visual_state["canvasBackgroundImage"]
    assert visual_state["canvasBoxShadow"] != "none"
    assert visual_state["selectedFilter"] != "none"
    assert visual_state["selectedFilter"] != visual_state["baseFilter"]
    assert visual_state["selectedStrokeWidth"] >= 4
    assert visual_state["selectedHitFill"] in {"rgba(0, 0, 0, 0)", "transparent"}
    assert visual_state["selectedHitFilter"] == "none"
    assert visual_state["selectedHitStrokeWidth"] == 0
    assert visual_state["labelPaintOrder"] == "stroke"
    assert visual_state["labelStrokeWidth"] >= 3
    assert visual_state["labelStrokeLinejoin"] == "round"


def test_preview_graph_node_preview_bubble_tracks_hover_and_focus(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import expect, sync_playwright
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
                page = browser.new_page(viewport={"width": 1440, "height": 960})
                try:
                    page.goto(
                        f"{base_url}/_raya/graph/index.html",
                        wait_until="networkidle",
                    )
                    page.locator("#raya-graph-canvas").evaluate(
                        """(svg) => {
                          svg.style.width = '1000px';
                          svg.style.height = '200px';
                          svg.style.maxWidth = 'none';
                        }"""
                    )
                    bubble = page.locator("[data-raya-graph-preview-bubble]")
                    expect(bubble).to_be_hidden()

                    node = page.locator(
                        '#raya-graph-canvas [data-raya-graph-node="render-root"]'
                    )
                    node.locator(".raya-graph-node-hit").hover()
                    expect(bubble).to_be_visible()
                    expect(
                        page.locator("[data-raya-graph-preview-title]")
                    ).to_contain_text("Raya Lucaria Render Fixture")
                    expect(
                        page.locator("[data-raya-graph-preview-counts]")
                    ).to_contain_text("connected")
                    expect(
                        page.locator("[data-raya-graph-inspection-preview]")
                    ).to_be_visible()
                    node_bounds = node.bounding_box()
                    bounds = bubble.bounding_box()
                    assert node_bounds is not None
                    assert bounds is not None
                    assert bounds["x"] >= 0
                    assert bounds["x"] + bounds["width"] <= 1440
                    node_center = {
                        "x": node_bounds["x"] + node_bounds["width"] / 2,
                        "y": node_bounds["y"] + node_bounds["height"] / 2,
                    }
                    bubble_center = {
                        "x": bounds["x"] + bounds["width"] / 2,
                        "y": bounds["y"] + bounds["height"] / 2,
                    }
                    assert bubble_center["x"] >= node_center["x"]
                    assert abs(bubble_center["x"] - node_center["x"]) <= 260
                    assert abs(bubble_center["y"] - node_center["y"]) <= 140

                    page.keyboard.press("Escape")
                    expect(bubble).to_be_hidden()
                    expect(
                        page.locator("[data-raya-graph-inspection-preview]")
                    ).to_be_visible()

                    node.evaluate("node => node.focus()")
                    expect(bubble).to_be_visible()
                    _assert_no_horizontal_overflow(page)
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_preview_graph_workspace_starts_in_first_desktop_viewport(
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
                        f"{handle.base_url}/_raya/graph/index.html",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(page)
                    probe = page.evaluate(
                        """() => {
                          const workspace = document.querySelector('.raya-graph-workspace');
                          const mapPanel = document.querySelector('.raya-graph-map-panel');
                          const canvas = document.querySelector('#raya-graph-canvas');
                          const toolbar = document.querySelector('.raya-graph-toolbar');
                          const instructions = document.querySelector('.raya-graph-instructions');
                          const box = (node) => {
                            const rect = node?.getBoundingClientRect();
                            return rect
                              ? { top: rect.top, bottom: rect.bottom, height: rect.height }
                              : null;
                          };
                          return {
                            workspace: box(workspace),
                            mapPanel: box(mapPanel),
                            canvas: box(canvas),
                            toolbar: box(toolbar),
                            instructions: box(instructions),
                            viewportHeight: window.innerHeight,
                            nodes: document.querySelectorAll('#raya-graph-canvas [data-raya-graph-node]').length,
                            edges: document.querySelectorAll('#raya-graph-canvas [data-raya-graph-edge]').length,
                            rootLayout: document.querySelector('[data-raya-graph-page]')
                              ?.getAttribute('data-raya-graph-layout'),
                          };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert probe["rootLayout"] == "connections"
    assert probe["nodes"] >= 6
    assert probe["edges"] >= 10
    assert probe["toolbar"]["height"] <= 88
    assert probe["instructions"]["height"] <= 36
    assert probe["workspace"]["top"] < 340
    assert probe["mapPanel"]["top"] < 360
    assert probe["canvas"]["top"] < 520
    assert probe["canvas"]["bottom"] <= probe["viewportHeight"] + 260
    assert probe["canvas"]["height"] >= 420


def test_preview_graph_deeplink_keeps_orientation_controls_in_initial_viewport(
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
                    {"width": 1440, "height": 900},
                    {"width": 1024, "height": 768},
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    try:
                        page.goto(
                            f"{handle.base_url}/_raya/graph/index.html?page=reader-ux",
                            wait_until="networkidle",
                        )
                        page.wait_for_selector(
                            '#raya-graph-canvas [data-raya-graph-node="reader-ux"] '
                            ".raya-graph-node.is-selected"
                        )
                        probe = page.evaluate(
                            """() => {
                              const box = (selector) => {
                                const node = document.querySelector(selector);
                                const rect = node?.getBoundingClientRect();
                                return rect
                                  ? {
                                      top: rect.top,
                                      bottom: rect.bottom,
                                      left: rect.left,
                                      right: rect.right,
                                      width: rect.width,
                                      height: rect.height,
                                    }
                                  : null;
                              };
                              const intersectsViewport = (rect) => Boolean(
                                rect &&
                                rect.bottom > 0 &&
                                rect.right > 0 &&
                                rect.top < window.innerHeight &&
                                rect.left < window.innerWidth
                              );
                              const parseTranslate = (value) => {
                                const match = String(value || '').match(
                                  /translate\\(([-0-9.]+)\\s+([-0-9.]+)\\)/
                                );
                                return match
                                  ? { x: Number(match[1]), y: Number(match[2]) }
                                  : null;
                              };
                              const parseViewBox = (value) => {
                                const parts = String(value || '')
                                  .trim()
                                  .split(/\\s+/)
                                  .map(Number);
                                return parts.length === 4 && parts.every(Number.isFinite)
                                  ? {
                                      x: parts[0],
                                      y: parts[1],
                                      width: parts[2],
                                      height: parts[3],
                                      right: parts[0] + parts[2],
                                      bottom: parts[1] + parts[3],
                                    }
                                  : null;
                              };
                              const inBox = (point, viewBox) => Boolean(
                                point &&
                                viewBox &&
                                point.x >= viewBox.x &&
                                point.x <= viewBox.right &&
                                point.y >= viewBox.y &&
                                point.y <= viewBox.bottom
                              );
                              const canvas = document.querySelector('#raya-graph-canvas');
                              const viewBox = parseViewBox(canvas?.getAttribute('viewBox'));
                              const graphPoints = Array.from(
                                document.querySelectorAll(
                                  '#raya-graph-canvas [data-raya-graph-node] g'
                                )
                              )
                                .map((node) => parseTranslate(node.getAttribute('transform')))
                                .filter(Boolean);
                              const selectedPoint = parseTranslate(
                                document
                                  .querySelector(
                                    '#raya-graph-canvas [data-raya-graph-node="reader-ux"] g'
                                  )
                                  ?.getAttribute('transform')
                              );
                              const graphSpan = graphPoints.length
                                ? {
                                    x: Math.max(...graphPoints.map((point) => point.x)) -
                                      Math.min(...graphPoints.map((point) => point.x)),
                                    y: Math.max(...graphPoints.map((point) => point.y)) -
                                      Math.min(...graphPoints.map((point) => point.y)),
                                  }
                                : null;
                              const focusedEdgeVisible = Array.from(
                                document.querySelectorAll(
                                  '#raya-graph-canvas .raya-graph-edge.is-active'
                                )
                              ).some((edge) => {
                                const from = {
                                  x: Number(edge.getAttribute('x1')),
                                  y: Number(edge.getAttribute('y1')),
                                };
                                const to = {
                                  x: Number(edge.getAttribute('x2')),
                                  y: Number(edge.getAttribute('y2')),
                                };
                                return inBox(from, viewBox) || inBox(to, viewBox);
                              });
                              const activeEdgeIntersectsViewport = Array.from(
                                document.querySelectorAll(
                                  '#raya-graph-canvas .raya-graph-edge.is-active'
                                )
                              ).some((edge) =>
                                intersectsViewport(edge.getBoundingClientRect())
                              );
                              return {
                                scrollY: window.scrollY,
                                orientation: box('[data-raya-graph-orientation]'),
                                toolbar: box('.raya-graph-toolbar'),
                                canvas: box('#raya-graph-canvas'),
                                selected: box(
                                  '#raya-graph-canvas [data-raya-graph-node="reader-ux"] g'
                                ),
                                detailTitle: document
                                  .querySelector('[data-raya-graph-detail-title]')
                                  ?.textContent
                                  ?.trim() || '',
                                selectedState: document
                                  .querySelector('[data-raya-graph-state-selected]')
                                  ?.textContent
                                  ?.trim() || '',
                                orientationVisible: intersectsViewport(
                                  box('[data-raya-graph-orientation]')
                                ),
                                toolbarVisible: intersectsViewport(
                                  box('.raya-graph-toolbar')
                                ),
                                canvasIntersectsViewport: intersectsViewport(
                                  box('#raya-graph-canvas')
                                ),
                                selectedIntersectsViewport: intersectsViewport(
                                  box(
                                    '#raya-graph-canvas [data-raya-graph-node="reader-ux"] g'
                                  )
                                ),
                                selectedPointInViewBox: inBox(selectedPoint, viewBox),
                                focusedEdgeVisible,
                                activeEdgeIntersectsViewport,
                                viewBoxIsFocused: Boolean(
                                  viewBox &&
                                  graphSpan &&
                                  viewBox.width < graphSpan.x &&
                                  viewBox.height < graphSpan.y
                                ),
                                localStorageKeys: Object.keys(localStorage),
                                sessionStorageKeys: Object.keys(sessionStorage),
                              };
                            }"""
                        )
                    finally:
                        page.close()

                    assert probe["selected"] is not None
                    assert "Projection Residuals" in probe["detailTitle"]
                    assert probe["selectedState"] == "reader-ux"
                    assert probe["orientationVisible"] or probe["toolbarVisible"], (
                        viewport,
                        probe,
                    )
                    assert probe["canvasIntersectsViewport"], (viewport, probe)
                    assert probe["selectedIntersectsViewport"], (viewport, probe)
                    assert probe["activeEdgeIntersectsViewport"], (viewport, probe)
                    if viewport["width"] >= 1280:
                        assert probe["canvas"]["height"] >= viewport["height"] * 0.48, (
                            viewport,
                            probe,
                        )
                    else:
                        assert probe["canvas"]["height"] >= min(
                            360, viewport["height"] * 0.42
                        ), (viewport, probe)
                    assert probe["canvas"]["height"] <= viewport["height"] * 0.78, (
                        viewport,
                        probe,
                    )
                    assert probe["scrollY"] < viewport["height"] * 0.5, (
                        viewport,
                        probe,
                    )
                    assert probe["selectedPointInViewBox"], (viewport, probe)
                    assert probe["focusedEdgeVisible"], (viewport, probe)
                    assert probe["viewBoxIsFocused"], (viewport, probe)
                    assert probe["localStorageKeys"] == []
                    assert probe["sessionStorageKeys"] == []
            finally:
                browser.close()
    finally:
        handle.close()


def test_preview_graph_mobile_workspace_prioritizes_map_panel(
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
                    {"width": 1440, "height": 900},
                    {"width": 1024, "height": 768},
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    try:
                        page.goto(
                            f"{handle.base_url}/_raya/graph/index.html?page=reader-ux",
                            wait_until="networkidle",
                        )
                        page.wait_for_selector(
                            '#raya-graph-canvas [data-raya-graph-node="reader-ux"] '
                            ".raya-graph-node.is-selected"
                        )
                        probe = page.evaluate(
                            """() => {
                              const box = (selector) => {
                                const node = document.querySelector(selector);
                                const rect = node?.getBoundingClientRect();
                                return rect
                                  ? {
                                      top: rect.top,
                                      bottom: rect.bottom,
                                      left: rect.left,
                                      right: rect.right,
                                      height: rect.height,
                                      width: rect.width,
                                    }
                                  : null;
                              };
                              return {
                                list: box('.raya-graph-list-panel'),
                                map: box('.raya-graph-map-panel'),
                                inspector: box('.raya-graph-inspector-panel'),
                                selectedState: document
                                  .querySelector('[data-raya-graph-state-selected]')
                                  ?.textContent
                                  ?.trim() || '',
                                localStorageKeys: Object.keys(localStorage),
                                sessionStorageKeys: Object.keys(sessionStorage),
                              };
                            }"""
                        )
                    finally:
                        page.close()

                    assert probe["list"] is not None
                    assert probe["map"] is not None
                    assert probe["inspector"] is not None
                    assert probe["selectedState"] == "reader-ux"
                    if viewport["width"] >= 1280:
                        assert probe["list"]["left"] < probe["map"]["left"], (
                            viewport,
                            probe,
                        )
                    else:
                        assert probe["map"]["top"] < probe["list"]["top"], (
                            viewport,
                            probe,
                        )
                        assert probe["map"]["top"] < probe["inspector"]["top"], (
                            viewport,
                            probe,
                        )
                        assert probe["map"]["top"] < viewport["height"], (
                            viewport,
                            probe,
                        )
                    assert probe["localStorageKeys"] == []
                    assert probe["sessionStorageKeys"] == []
            finally:
                browser.close()
    finally:
        handle.close()


def test_preview_graph_mobile_toolbar_uses_compact_command_strip(
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
                        f"{handle.base_url}/_raya/graph/index.html?page=reader-ux",
                        wait_until="networkidle",
                    )
                    page.wait_for_selector(
                        '#raya-graph-canvas [data-raya-graph-node="reader-ux"] '
                        ".raya-graph-node.is-selected"
                    )
                    _assert_no_horizontal_overflow(page)
                    probe = page.evaluate(
                        """() => {
                          const box = (selector) => {
                            const node = document.querySelector(selector);
                            const rect = node?.getBoundingClientRect();
                            return rect
                              ? {
                                  top: rect.top,
                                  bottom: rect.bottom,
                                  left: rect.left,
                                  right: rect.right,
                                  height: rect.height,
                                  width: rect.width,
                                }
                              : null;
                          };
                          const toolbar = document.querySelector('.raya-graph-toolbar');
                          const groups = Array.from(
                            document.querySelectorAll('.raya-graph-toolbar-group')
                          ).map((group) => {
                            const rect = group.getBoundingClientRect();
                            return {
                              label: group.getAttribute('aria-label') || '',
                              top: rect.top,
                              bottom: rect.bottom,
                              left: rect.left,
                              right: rect.right,
                              width: rect.width,
                              height: rect.height,
                            };
                          });
                          const contentFilter = document.querySelector(
                            '[data-raya-graph-edge-kind-filter="content"]'
                          );
                          const fitSelection = document.querySelector(
                            '#graph-fit-selection'
                          );
                          const panRight = document.querySelector(
                            '[data-raya-graph-pan="right"]'
                          );
                          const initialContentFilterRight = contentFilter
                            ?.getBoundingClientRect()
                            ?.right || 0;
                          if (toolbar) {
                            panRight?.scrollIntoView({
                              block: 'nearest',
                              inline: 'center',
                            });
                          }
                          panRight?.focus();
                          const toolbarRect = toolbar?.getBoundingClientRect();
                          const panRightRect = panRight?.getBoundingClientRect();
                          const panRightStyle = panRight
                            ? getComputedStyle(panRight)
                            : null;
                          return {
                            toolbar: box('.raya-graph-toolbar'),
                            toolbarClientWidth: toolbar?.clientWidth || 0,
                            toolbarScrollWidth: toolbar?.scrollWidth || 0,
                            toolbarScrollLeft: toolbar?.scrollLeft || 0,
                            groups,
                            search: box('#graph-search'),
                            layout: box('#graph-layout'),
                            contentFilterExists: Boolean(contentFilter),
                            fitSelectionExists: Boolean(fitSelection),
                            panRightExists: Boolean(panRight),
                            initialContentFilterRight,
                            panRightVisibleAfterScroll: Boolean(
                              toolbarRect &&
                              panRightRect &&
                              panRightRect.left >= toolbarRect.left &&
                              panRightRect.right <= toolbarRect.right
                            ),
                            panRightFocused: document.activeElement === panRight,
                            panRightOutlineStyle: panRightStyle?.outlineStyle || '',
                            panRightOutlineWidth: panRightStyle?.outlineWidth || '',
                            panRightOutlineOffset: panRightStyle?.outlineOffset || '',
                            map: box('.raya-graph-map-panel'),
                            list: box('.raya-graph-list-panel'),
                            selectedState: document
                              .querySelector('[data-raya-graph-state-selected]')
                              ?.textContent
                              ?.trim() || '',
                            localStorageKeys: Object.keys(localStorage),
                            sessionStorageKeys: Object.keys(sessionStorage),
                          };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert probe["toolbar"] is not None
    assert probe["toolbar"]["height"] <= 120
    assert probe["toolbarScrollWidth"] > probe["toolbarClientWidth"]
    assert probe["toolbarScrollLeft"] > 0
    assert len(probe["groups"]) >= 5
    assert abs(probe["groups"][0]["top"] - probe["groups"][1]["top"]) <= 4
    assert probe["search"] is not None
    assert probe["layout"] is not None
    assert probe["contentFilterExists"]
    assert probe["fitSelectionExists"]
    assert probe["panRightExists"]
    assert probe["initialContentFilterRight"] > probe["toolbarClientWidth"]
    assert probe["panRightVisibleAfterScroll"]
    assert probe["panRightFocused"]
    assert probe["panRightOutlineStyle"] == "solid"
    assert probe["panRightOutlineWidth"] == "3px"
    assert probe["panRightOutlineOffset"].startswith("-")
    assert probe["map"]["top"] < probe["list"]["top"]
    assert probe["selectedState"] == "reader-ux"
    assert probe["localStorageKeys"] == []
    assert probe["sessionStorageKeys"] == []


def test_preview_graph_mobile_keeps_canvas_in_first_viewport(
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
                        f"{handle.base_url}/_raya/graph/index.html?page=reader-ux",
                        wait_until="networkidle",
                    )
                    page.wait_for_selector(
                        '#raya-graph-canvas [data-raya-graph-node="reader-ux"] '
                        ".raya-graph-node.is-selected"
                    )
                    probe = page.evaluate(
                        """() => {
                          const box = (selector) => {
                            const node = document.querySelector(selector);
                            const rect = node?.getBoundingClientRect();
                            return rect
                              ? {
                                  top: rect.top,
                                  bottom: rect.bottom,
                                  height: rect.height,
                                  width: rect.width,
                                }
                              : null;
                          };
                          const toolbar = document.querySelector('.raya-graph-toolbar');
                          return {
                            readingKeys: box('[data-raya-graph-reading-keys]'),
                            readingKeyCount: document.querySelectorAll(
                              '[data-raya-graph-reading-key]'
                            ).length,
                            instructions: box('.raya-graph-instructions'),
                            orientation: box('[data-raya-graph-orientation]'),
                            orientationMeta: box('.raya-graph-orientation-meta'),
                            orientationActions: box('.raya-graph-orientation-actions'),
                            canvas: box('#raya-graph-canvas'),
                            toolbarScrollWidth: toolbar?.scrollWidth || 0,
                            toolbarClientWidth: toolbar?.clientWidth || 0,
                            overflow: Math.ceil(
                              document.documentElement.scrollWidth - window.innerWidth
                            ),
                            selectedState: document
                              .querySelector('[data-raya-graph-state-selected]')
                              ?.textContent
                              ?.trim() || '',
                            orientationLabels: Array.from(
                              document.querySelectorAll(
                                '.raya-graph-orientation-meta dt'
                              )
                            ).map((node) => node.textContent.trim()),
                            orientationActionCount: Array.from(
                              document.querySelectorAll(
                                '.raya-graph-orientation-actions > *'
                              )
                            ).filter((node) => !node.hidden).length,
                          };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert probe["readingKeys"] is not None
    assert probe["instructions"] is not None
    assert probe["orientation"] is not None
    assert probe["orientationMeta"] is not None
    assert probe["orientationActions"] is not None
    assert probe["canvas"] is not None
    assert probe["readingKeyCount"] == 4
    assert probe["readingKeys"]["height"] <= 48
    assert probe["instructions"]["height"] <= 40
    assert probe["orientation"]["height"] <= 100
    assert probe["canvas"]["top"] <= 620
    assert probe["canvas"]["top"] < 844
    assert probe["toolbarScrollWidth"] > probe["toolbarClientWidth"]
    assert probe["overflow"] <= 1
    assert probe["selectedState"] == "reader-ux"
    assert probe["orientationLabels"] == [
        "Layout",
        "Page focus",
        "Search",
        "Filters",
        "Neighborhood",
    ]
    assert probe["orientationActionCount"] >= 3


def test_preview_graph_mobile_defaults_to_compact_panels(
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
                mobile = browser.new_page(viewport={"width": 390, "height": 844})
                try:
                    mobile.goto(
                        f"{handle.base_url}/_raya/graph/index.html?page=reader-ux",
                        wait_until="networkidle",
                    )
                    mobile.wait_for_selector(
                        '#raya-graph-canvas [data-raya-graph-node="reader-ux"] '
                        ".raya-graph-node.is-selected"
                    )
                    mobile_probe = mobile.evaluate(
                        """() => {
                          const root = document.querySelector('[data-raya-graph-page]');
                          const box = (selector) => {
                            const node = document.querySelector(selector);
                            const rect = node?.getBoundingClientRect();
                            return rect
                              ? { top: rect.top, height: rect.height, width: rect.width }
                              : null;
                          };
                          const listLink = document.querySelector(
                            '#raya-graph-list [data-raya-graph-node] a'
                          );
                          const inspectorButton = document.querySelector(
                            '[data-raya-graph-detail-clear]'
                          );
                          return {
                            listState: root?.getAttribute('data-raya-graph-list-state'),
                            inspectorState: root?.getAttribute(
                              'data-raya-graph-inspector-state'
                            ),
                            listBodyHidden: document
                              .querySelector('[data-raya-graph-panel-body="list"]')
                              ?.getAttribute('aria-hidden'),
                            inspectorBodyHidden: document
                              .querySelector('[data-raya-graph-panel-body="inspector"]')
                              ?.getAttribute('aria-hidden'),
                            listPanel: box('.raya-graph-list-panel'),
                            inspectorPanel: box('.raya-graph-inspector-panel'),
                            listSummaryVisible: Boolean(
                              document
                                .querySelector(
                                  '[data-raya-graph-panel-rail-summary="list"]'
                                )
                                ?.checkVisibility()
                            ),
                            inspectorSummaryVisible: Boolean(
                              document
                                .querySelector(
                                  '[data-raya-graph-panel-rail-summary="inspector"]'
                                )
                                ?.checkVisibility()
                            ),
                            listSummary: document
                              .querySelector('[data-raya-graph-panel-rail-summary="list"]')
                              ?.textContent
                              ?.trim() || '',
                            inspectorSummary: document
                              .querySelector(
                                '[data-raya-graph-panel-rail-summary="inspector"]'
                              )
                              ?.textContent
                              ?.trim() || '',
                            listButton: document
                              .querySelector('[data-raya-graph-toggle-panel="list"]')
                              ?.textContent
                              ?.trim() || '',
                            inspectorButton: document
                              .querySelector('[data-raya-graph-toggle-panel="inspector"]')
                              ?.textContent
                              ?.trim() || '',
                            listLinkTabindex: listLink?.getAttribute('tabindex'),
                            inspectorButtonTabindex: inspectorButton?.getAttribute(
                              'tabindex'
                            ),
                            url: window.location.href,
                            overflow: Math.ceil(
                              document.documentElement.scrollWidth - window.innerWidth
                            ),
                          };
                        }"""
                    )
                    mobile.click('[data-raya-graph-toggle-panel="list"]')
                    mobile.click('[data-raya-graph-toggle-panel="inspector"]')
                    mobile.wait_for_function(
                        """() => {
                          const root = document.querySelector('[data-raya-graph-page]');
                          return root?.getAttribute('data-raya-graph-list-state') === 'expanded'
                            && root?.getAttribute('data-raya-graph-inspector-state') === 'expanded';
                        }"""
                    )
                    expanded_mobile_probe = mobile.evaluate(
                        """() => ({
                          listBodyHidden: document
                            .querySelector('[data-raya-graph-panel-body="list"]')
                            ?.getAttribute('aria-hidden'),
                          inspectorBodyHidden: document
                            .querySelector('[data-raya-graph-panel-body="inspector"]')
                            ?.getAttribute('aria-hidden'),
                          listButton: document
                            .querySelector('[data-raya-graph-toggle-panel="list"]')
                            ?.textContent
                            ?.trim() || '',
                          inspectorButton: document
                            .querySelector('[data-raya-graph-toggle-panel="inspector"]')
                            ?.textContent
                            ?.trim() || '',
                          listLinkTabindex: document
                            .querySelector('#raya-graph-list [data-raya-graph-node] a')
                            ?.getAttribute('tabindex'),
                          inspectorButtonTabindex: document
                            .querySelector('[data-raya-graph-detail-clear]')
                            ?.getAttribute('tabindex'),
                          url: window.location.href,
                        })"""
                    )
                    mobile.click("#graph-reset")
                    mobile.wait_for_function(
                        """() => {
                          const root = document.querySelector('[data-raya-graph-page]');
                          return root?.getAttribute('data-raya-graph-list-state') === 'collapsed'
                            && root?.getAttribute('data-raya-graph-inspector-state') === 'collapsed';
                        }"""
                    )
                    reset_mobile_probe = mobile.evaluate(
                        """() => ({
                          listBodyHidden: document
                            .querySelector('[data-raya-graph-panel-body="list"]')
                            ?.getAttribute('aria-hidden'),
                          inspectorBodyHidden: document
                            .querySelector('[data-raya-graph-panel-body="inspector"]')
                            ?.getAttribute('aria-hidden'),
                          url: window.location.href,
                        })"""
                    )
                    mobile.click("#graph-expand")
                    mobile.wait_for_function(
                        """() => document
                          .querySelector('[data-raya-graph-page]')
                          ?.getAttribute('data-raya-graph-expanded') === 'true'"""
                    )
                    mobile.click('[data-raya-graph-toggle-panel="list"]')
                    mobile.wait_for_function(
                        """() => document
                          .querySelector('[data-raya-graph-page]')
                          ?.getAttribute('data-raya-graph-expanded') === 'false'"""
                    )
                    mobile_focus_exit_probe = mobile.evaluate(
                        """() => {
                          const root = document.querySelector('[data-raya-graph-page]');
                          return {
                            listState: root?.getAttribute('data-raya-graph-list-state'),
                            inspectorState: root?.getAttribute(
                              'data-raya-graph-inspector-state'
                            ),
                            listBodyHidden: document
                              .querySelector('[data-raya-graph-panel-body="list"]')
                              ?.getAttribute('aria-hidden'),
                            inspectorBodyHidden: document
                              .querySelector('[data-raya-graph-panel-body="inspector"]')
                              ?.getAttribute('aria-hidden'),
                            url: window.location.href,
                          };
                        }"""
                    )
                finally:
                    mobile.close()

                mobile_explicit = browser.new_page(viewport={"width": 390, "height": 844})
                try:
                    mobile_explicit.goto(
                        f"{handle.base_url}/_raya/graph/index.html"
                        "?page=reader-ux&list=1&inspector=1",
                        wait_until="networkidle",
                    )
                    explicit_probe = mobile_explicit.evaluate(
                        """() => {
                          const root = document.querySelector('[data-raya-graph-page]');
                          return {
                            listState: root?.getAttribute('data-raya-graph-list-state'),
                            inspectorState: root?.getAttribute(
                              'data-raya-graph-inspector-state'
                            ),
                            listBodyHidden: document
                              .querySelector('[data-raya-graph-panel-body="list"]')
                              ?.getAttribute('aria-hidden'),
                            inspectorBodyHidden: document
                              .querySelector('[data-raya-graph-panel-body="inspector"]')
                              ?.getAttribute('aria-hidden'),
                            url: window.location.href,
                          };
                        }"""
                    )
                finally:
                    mobile_explicit.close()

                desktop = browser.new_page(viewport={"width": 1440, "height": 950})
                try:
                    desktop.goto(
                        f"{handle.base_url}/_raya/graph/index.html?page=reader-ux",
                        wait_until="networkidle",
                    )
                    desktop_probe = desktop.evaluate(
                        """() => {
                          const root = document.querySelector('[data-raya-graph-page]');
                          return {
                            listState: root?.getAttribute('data-raya-graph-list-state'),
                            inspectorState: root?.getAttribute(
                              'data-raya-graph-inspector-state'
                            ),
                            listBodyHidden: document
                              .querySelector('[data-raya-graph-panel-body="list"]')
                              ?.getAttribute('aria-hidden'),
                            inspectorBodyHidden: document
                              .querySelector('[data-raya-graph-panel-body="inspector"]')
                              ?.getAttribute('aria-hidden'),
                            url: window.location.href,
                          };
                        }"""
                    )
                    desktop.click("#graph-expand")
                    desktop.wait_for_function(
                        """() => document
                          .querySelector('[data-raya-graph-page]')
                          ?.getAttribute('data-raya-graph-expanded') === 'true'"""
                    )
                    desktop.click('[data-raya-graph-toggle-panel="list"]')
                    desktop.wait_for_function(
                        """() => document
                          .querySelector('[data-raya-graph-page]')
                          ?.getAttribute('data-raya-graph-expanded') === 'false'"""
                    )
                    desktop_focus_exit_probe = desktop.evaluate(
                        """() => {
                          const root = document.querySelector('[data-raya-graph-page]');
                          return {
                            listState: root?.getAttribute('data-raya-graph-list-state'),
                            inspectorState: root?.getAttribute(
                              'data-raya-graph-inspector-state'
                            ),
                            listBodyHidden: document
                              .querySelector('[data-raya-graph-panel-body="list"]')
                              ?.getAttribute('aria-hidden'),
                            inspectorBodyHidden: document
                              .querySelector('[data-raya-graph-panel-body="inspector"]')
                              ?.getAttribute('aria-hidden'),
                            url: window.location.href,
                          };
                        }"""
                    )
                finally:
                    desktop.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert mobile_probe["listState"] == "collapsed"
    assert mobile_probe["inspectorState"] == "collapsed"
    assert mobile_probe["listBodyHidden"] == "true"
    assert mobile_probe["inspectorBodyHidden"] == "true"
    assert mobile_probe["listPanel"]["height"] < 160
    assert mobile_probe["inspectorPanel"]["height"] < 180
    assert mobile_probe["listSummaryVisible"]
    assert mobile_probe["inspectorSummaryVisible"]
    assert "visible page" in mobile_probe["listSummary"]
    assert "Projection Residuals" in mobile_probe["inspectorSummary"]
    assert mobile_probe["listButton"] == "Open"
    assert mobile_probe["inspectorButton"] == "Open"
    assert mobile_probe["listLinkTabindex"] == "-1"
    assert mobile_probe["inspectorButtonTabindex"] == "-1"
    assert "list=0" not in mobile_probe["url"]
    assert "inspector=0" not in mobile_probe["url"]
    assert mobile_probe["overflow"] <= 1

    assert expanded_mobile_probe["listBodyHidden"] == "false"
    assert expanded_mobile_probe["inspectorBodyHidden"] == "false"
    assert expanded_mobile_probe["listButton"] == "Hide"
    assert expanded_mobile_probe["inspectorButton"] == "Hide"
    assert expanded_mobile_probe["listLinkTabindex"] is None
    assert expanded_mobile_probe["inspectorButtonTabindex"] is None
    assert "list=1" in expanded_mobile_probe["url"]
    assert "inspector=1" in expanded_mobile_probe["url"]

    assert reset_mobile_probe["listBodyHidden"] == "true"
    assert reset_mobile_probe["inspectorBodyHidden"] == "true"
    assert "list=1" not in reset_mobile_probe["url"]
    assert "inspector=1" not in reset_mobile_probe["url"]

    assert mobile_focus_exit_probe["listState"] == "collapsed"
    assert mobile_focus_exit_probe["inspectorState"] == "collapsed"
    assert mobile_focus_exit_probe["listBodyHidden"] == "true"
    assert mobile_focus_exit_probe["inspectorBodyHidden"] == "true"
    assert "expanded=1" not in mobile_focus_exit_probe["url"]
    assert "list=1" not in mobile_focus_exit_probe["url"]
    assert "inspector=1" not in mobile_focus_exit_probe["url"]

    assert explicit_probe["listState"] == "expanded"
    assert explicit_probe["inspectorState"] == "expanded"
    assert explicit_probe["listBodyHidden"] == "false"
    assert explicit_probe["inspectorBodyHidden"] == "false"
    assert "list=1" in explicit_probe["url"]
    assert "inspector=1" in explicit_probe["url"]

    assert desktop_probe["listState"] == "expanded"
    assert desktop_probe["inspectorState"] == "expanded"
    assert desktop_probe["listBodyHidden"] == "false"
    assert desktop_probe["inspectorBodyHidden"] == "false"
    assert "list=1" not in desktop_probe["url"]
    assert "inspector=1" not in desktop_probe["url"]

    assert desktop_focus_exit_probe["listState"] == "expanded"
    assert desktop_focus_exit_probe["inspectorState"] == "expanded"
    assert desktop_focus_exit_probe["listBodyHidden"] == "false"
    assert desktop_focus_exit_probe["inspectorBodyHidden"] == "false"
    assert "expanded=1" not in desktop_focus_exit_probe["url"]
    assert "list=0" not in desktop_focus_exit_probe["url"]
    assert "inspector=0" not in desktop_focus_exit_probe["url"]


def test_preview_graph_toolbar_remains_compact_above_label_breakpoint(
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
                page = browser.new_page(viewport={"width": 1501, "height": 950})
                try:
                    page.goto(
                        f"{handle.base_url}/_raya/graph/index.html",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(page)
                    toolbar_height = page.locator(
                        ".raya-graph-toolbar"
                    ).evaluate("node => node.getBoundingClientRect().height")
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert toolbar_height <= 88


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
                            f"{base_url}/reader-ux/index.html",
                            wait_until="networkidle",
                        )
                        _assert_no_horizontal_overflow(page)
                        page.locator("#raya-command-search-input").fill(
                            "projection residual"
                        )
                        page.locator(".raya-command-search-form").evaluate(
                            "form => form.requestSubmit()"
                        )
                        page.wait_for_url(
                            "**/_raya/search/index.html?q=projection+residual"
                        )
                        assert page.locator(
                            "[data-raya-search-result='reader-ux']"
                        ).is_visible()
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
                            storage_before = page.evaluate(
                                "() => [Object.keys(localStorage), Object.keys(sessionStorage)]"
                            )
                            controls_toggle = page.locator(
                                '[data-raya-discovery-toggle-panel="controls"]'
                            )
                            context_toggle = page.locator(
                                '[data-raya-discovery-toggle-panel="context"]'
                            )
                            assert controls_toggle.is_visible()
                            assert context_toggle.is_visible()
                            controls_toggle.click()
                            page.wait_for_function(
                                """() => document
                                  .querySelector('[data-raya-search-page]')
                                  ?.getAttribute('data-raya-discovery-controls-state') === 'collapsed'"""
                            )
                            assert (
                                controls_toggle.get_attribute("aria-expanded")
                                == "false"
                            )
                            assert (
                                page.locator(
                                    '[data-raya-discovery-panel-body="controls"]'
                                ).get_attribute("aria-hidden")
                                == "true"
                            )
                            assert (
                                page.locator(
                                    '[data-raya-discovery-panel-body="controls"]'
                                ).evaluate("node => getComputedStyle(node).display")
                                == "none"
                            )
                            assert (
                                page.locator("#raya-search-input").get_attribute(
                                    "tabindex"
                                )
                                == "-1"
                            )
                            controls_rail_summary = page.locator(
                                '[data-raya-discovery-panel-rail-summary="controls"]'
                            )
                            assert controls_rail_summary.is_visible()
                            assert (
                                "visible result"
                                in controls_rail_summary.inner_text()
                            )
                            _assert_no_horizontal_overflow(page)
                            context_title = page.locator(
                                "[data-raya-search-context-title]"
                            ).inner_text()
                            context_toggle.click()
                            page.wait_for_function(
                                """() => document
                                  .querySelector('[data-raya-search-page]')
                                  ?.getAttribute('data-raya-discovery-context-state') === 'collapsed'"""
                            )
                            assert (
                                context_toggle.get_attribute("aria-expanded")
                                == "false"
                            )
                            assert (
                                page.locator(
                                    '[data-raya-discovery-panel-body="context"]'
                                ).get_attribute("aria-hidden")
                                == "true"
                            )
                            context_rail_summary = page.locator(
                                '[data-raya-discovery-panel-rail-summary="context"]'
                            )
                            assert context_rail_summary.is_visible()
                            assert (
                                context_title
                                in context_rail_summary.inner_text()
                            )
                            _assert_no_horizontal_overflow(page)
                            assert (
                                page.evaluate(
                                    "() => [Object.keys(localStorage), Object.keys(sessionStorage)]"
                                )
                                == storage_before
                            )
                            context_toggle.click()
                            controls_toggle.click()
                            page.wait_for_function(
                                """() => {
                                  const root = document.querySelector('[data-raya-search-page]');
                                  return root?.getAttribute('data-raya-discovery-controls-state') === 'expanded'
                                    && root?.getAttribute('data-raya-discovery-context-state') === 'expanded';
                                }"""
                            )
                            assert (
                                controls_toggle.get_attribute("aria-expanded")
                                == "true"
                            )
                            assert (
                                page.locator("#raya-search-input").get_attribute(
                                    "tabindex"
                                )
                                is None
                            )
                            assert (
                                context_toggle.get_attribute("aria-expanded")
                                == "true"
                            )
                            assert controls_rail_summary.is_hidden()
                            assert context_rail_summary.is_hidden()
                        if viewport["width"] < 520:
                            discovery_box = page.locator(
                                ".raya-discovery-command-bar"
                            ).bounding_box()
                            assert discovery_box is not None
                            assert discovery_box["height"] <= 150
                            mobile_controls_toggle = page.locator(
                                '[data-raya-discovery-toggle-panel="controls"]'
                            )
                            assert mobile_controls_toggle.is_visible()
                            mobile_storage_before = page.evaluate(
                                "() => [Object.keys(localStorage), Object.keys(sessionStorage)]"
                            )
                            mobile_controls_toggle.click()
                            page.wait_for_function(
                                """() => document
                                  .querySelector('[data-raya-search-page]')
                                  ?.getAttribute('data-raya-discovery-controls-state') === 'collapsed'"""
                            )
                            assert (
                                mobile_controls_toggle.get_attribute("aria-expanded")
                                == "false"
                            )
                            assert (
                                page.locator(
                                    '[data-raya-discovery-panel-body="controls"]'
                                ).get_attribute("aria-hidden")
                                == "true"
                            )
                            assert (
                                page.locator("#raya-search-input").get_attribute(
                                    "tabindex"
                                )
                                == "-1"
                            )
                            assert page.locator(
                                '[data-raya-discovery-panel-rail-summary="controls"]'
                            ).is_visible()
                            assert (
                                page.evaluate(
                                    "() => [Object.keys(localStorage), Object.keys(sessionStorage)]"
                                )
                                == mobile_storage_before
                            )
                            mobile_controls_toggle.click()
                            page.wait_for_function(
                                """() => document
                                  .querySelector('[data-raya-search-page]')
                                  ?.getAttribute('data-raya-discovery-controls-state') === 'expanded'"""
                            )
                            assert (
                                page.locator("#raya-search-input").get_attribute(
                                    "tabindex"
                                )
                                is None
                            )
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
                        search_context_actions = page.locator(
                            "[data-raya-search-context-actions]"
                        )
                        assert (
                            page.locator(
                                '#raya-search-results [data-raya-search-active="true"]'
                            ).count()
                            == 0
                        )
                        assert search_context_actions.is_hidden()
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
                        assert search_context_actions.is_visible()
                        search_context_open = search_context_actions.locator(
                            "a", has_text="Open page"
                        )
                        assert (
                            search_context_open.evaluate(
                                "node => { node.focus(); return document.activeElement === node; }"
                            )
                            is True
                        )
                        assert (
                            "Authoring Matrix Fixture"
                            in search_context_open.get_attribute("aria-label")
                        )
                        assert (
                            search_context_open.evaluate("node => node.href").endswith(
                                "/authoring-matrix/index.html"
                            )
                        )
                        assert (
                            search_context_actions.locator("a", has_text="View graph")
                            .evaluate("node => node.href")
                            .endswith("/_raya/graph/index.html?page=authoring-matrix")
                        )
                        assert (
                            search_context_actions.locator("a", has_text="Open practice")
                            .evaluate("node => node.href")
                            .endswith(
                                "/_raya/practice/index.html?page=authoring-matrix"
                            )
                        )
                        assert (
                            search_context_actions.locator("a", has_text="Open tasks")
                            .evaluate("node => node.href")
                            .endswith("/_raya/tasks/index.html?page=authoring-matrix")
                        )
                        assert (
                            search_context_actions.locator("a", has_text="Open schedule")
                            .evaluate("node => node.href")
                            .endswith(
                                "/_raya/schedule/index.html?page=authoring-matrix"
                            )
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
                        with page.expect_navigation():
                            search_context_open.click()
                        assert page.url.endswith("/authoring-matrix/index.html")
                        page.goto(
                            f"{base_url}/_raya/search/index.html",
                            wait_until="networkidle",
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
                        page.fill("#raya-search-input", "matrx fixture")
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
                        assert page.locator(
                            "[data-raya-search-context-actions]"
                        ).is_hidden()
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
                            f"{base_url}/_raya/search/index.html?q=matrix%20norm%20fixture",
                            wait_until="networkidle",
                        )
                        prose_card = page.locator(
                            '[data-raya-search-result="authoring-matrix"]'
                        )
                        page.wait_for_selector(
                            '[data-raya-search-result="authoring-matrix"]:not([hidden])'
                        )
                        assert prose_card.is_visible()
                        section_link = prose_card.locator(
                            '.raya-search-result-section '
                            'a[href="../../authoring-matrix/index.html#raya-object-authoring-theorem"]'
                        )
                        assert section_link.is_visible()
                        assert section_link.inner_text() == "Matrix norm fixture"
                        assert (
                            "Match text:"
                            in page.locator(
                                "[data-raya-search-context-meta]"
                            ).inner_text()
                        )
                        assert (
                            "Section matches:"
                            in page.locator(
                                "[data-raya-search-context-meta]"
                            ).inner_text()
                        )
                        page.locator("#raya-search-input").focus()
                        page.press("#raya-search-input", "ArrowDown")
                        section_active = page.locator(
                            '#raya-search-results [data-raya-search-active="true"]'
                        )
                        assert (
                            section_active.get_attribute("data-raya-search-result")
                            == "authoring-matrix"
                        )
                        with page.expect_navigation():
                            page.press("#raya-search-input", "Enter")
                        assert page.url.endswith(
                            "/authoring-matrix/index.html#raya-object-authoring-theorem"
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
                        search_focus_notice = page.locator(
                            "[data-raya-search-page-focus]"
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
                        assert search_focus_notice.is_visible()
                        assert "Focused on page" in search_focus_notice.inner_text()
                        assert (
                            "Authoring Matrix Fixture"
                            in search_focus_notice.inner_text()
                        )
                        assert "1 visible result" in search_focus_notice.inner_text()
                        exact_card.locator("a").first.focus()
                        page.keyboard.press("Escape")
                        page.wait_for_function(
                            """() => document.activeElement?.id === 'raya-search-input'
                              && document
                                .querySelector('#raya-search-status')
                                ?.textContent
                                ?.includes('visible result')"""
                        )
                        assert (
                            page.locator(
                                "#raya-search-results [data-raya-search-result]:visible"
                            ).count()
                            > 1
                        )
                        assert (
                            page.locator(
                                '#raya-search-results [data-raya-search-active="true"]'
                            ).count()
                            == 0
                        )
                        assert page.locator(
                            "[data-raya-search-context-actions]"
                        ).is_hidden()
                        assert search_focus_notice.is_hidden()
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
                        assert search_focus_notice.is_hidden()
                        assert page.locator(
                            '[data-raya-search-result="matrix-reference"]'
                        ).is_visible()
                        page.goto(
                            f"{base_url}/_raya/search/index.html?page=missing-page",
                            wait_until="networkidle",
                        )
                        assert page.locator("#raya-search-empty").is_visible()
                        assert page.locator(
                            "[data-raya-search-page-focus]"
                        ).is_hidden()
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
                        practice_context_actions = page.locator(
                            "[data-raya-practice-context-actions]"
                        )
                        assert (
                            page.locator('[data-raya-practice-active="true"]').count()
                            == 0
                        )
                        assert practice_context_actions.is_hidden()
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
                        assert practice_context_actions.is_visible()
                        practice_context_open = practice_context_actions.locator(
                            "a", has_text="Open page"
                        )
                        assert (
                            practice_context_open.evaluate(
                                "node => { node.focus(); return document.activeElement === node; }"
                            )
                            is True
                        )
                        assert (
                            practice_context_open.get_attribute("aria-label").startswith(
                                "Open page: "
                            )
                        )
                        assert (
                            "/unit/topic/index.html#raya-official-first-topic-"
                            in practice_context_open.evaluate("node => node.href")
                        )
                        assert (
                            practice_context_actions.locator(
                                "a", has_text="View graph"
                            )
                            .evaluate("node => node.href")
                            .endswith("/_raya/graph/index.html?page=first-topic")
                        )
                        assert (
                            "No visible"
                            not in page.locator(
                                "[data-raya-practice-context-title]"
                            ).inner_text()
                        )
                        active_open_href = practice_context_open.evaluate(
                            "node => node.href"
                        )
                        with page.expect_navigation():
                            practice_context_open.click()
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
                        assert page.locator(
                            "[data-raya-practice-context-actions]"
                        ).is_hidden()
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
                        page.click("#raya-practice-clear")
                        page.fill("#raya-practice-search", "retrievel")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-practice-status')
                              ?.textContent
                              ?.includes('1 visible practice object')"""
                        )
                        assert page.locator(
                            '[data-raya-practice-object="first-topic-prompt"]'
                        ).is_visible()
                        assert page.locator(
                            '[data-raya-practice-object="first-topic-card"]'
                        ).is_hidden()
                        page.click("#raya-practice-clear")
                        page.fill("#raya-practice-search", "retrievel practice")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-practice-status')
                              ?.textContent
                              ?.includes('1 visible practice object')"""
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
                        assert page.locator(
                            "[data-raya-practice-context-actions]"
                        ).is_hidden()

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
                        practice_focus_notice = page.locator(
                            "[data-raya-practice-page-focus]"
                        )
                        assert practice_focus_notice.is_visible()
                        assert "Focused on page" in practice_focus_notice.inner_text()
                        assert "First Topic" in practice_focus_notice.inner_text()
                        assert (
                            "3 visible practice object"
                            in practice_focus_notice.inner_text()
                        )
                        assert (
                            page.locator('[data-raya-practice-active="true"]').count()
                            == 1
                        )
                        practice_context_actions = page.locator(
                            "[data-raya-practice-context-actions]"
                        )
                        assert practice_context_actions.is_visible()
                        assert practice_context_actions.locator(
                            "a", has_text="Open page"
                        ).evaluate("node => node.href").endswith(
                            "/unit/topic/index.html#raya-official-first-topic-card"
                        )
                        assert practice_context_actions.locator(
                            "a", has_text="View graph"
                        ).evaluate("node => node.href").endswith(
                            "/_raya/graph/index.html?page=first-topic"
                        )
                        assert (
                            page.evaluate(
                                "() => [Object.keys(localStorage), Object.keys(sessionStorage)]"
                            )
                            == [[], []]
                        )
                        page.click('[data-raya-practice-filter="quiz"]')
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-practice-status')
                              ?.textContent
                              ?.includes('1 visible practice object')"""
                        )
                        assert page.locator(
                            '[data-raya-practice-object="first-topic-card"]'
                        ).is_hidden()
                        assert page.locator(
                            '[data-raya-practice-object="first-topic-quiz"]'
                        ).is_visible()
                        page.locator(
                            '[data-raya-practice-object="first-topic-quiz"] '
                            ".raya-practice-open"
                        ).focus()
                        page.keyboard.press("Escape")
                        page.wait_for_function(
                            """() => document.activeElement?.id === 'raya-practice-search'
                              && document
                                .querySelector('#raya-practice-status')
                                ?.textContent
                                ?.includes('3 visible practice object')"""
                        )
                        assert practice_focus_notice.is_hidden()
                        assert (
                            page.locator('[data-raya-practice-active="true"]').count()
                            == 0
                        )
                        assert (
                            page.locator(
                                '[data-raya-practice-filter="all"]'
                            ).get_attribute("aria-pressed")
                            == "true"
                        )
                        assert page.locator(
                            '[data-raya-practice-object="first-topic-card"]'
                        ).is_visible()
                        assert practice_context_actions.is_hidden()
                        page.click("#raya-practice-clear")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-practice-status')
                              ?.textContent
                              ?.includes('3 visible practice object')"""
                        )
                        assert practice_focus_notice.is_hidden()
                        assert (
                            page.locator('[data-raya-practice-active="true"]').count()
                            == 0
                        )
                        assert practice_context_actions.is_hidden()
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
                        practice_focus_notice = page.locator(
                            "[data-raya-practice-page-focus]"
                        )
                        assert practice_focus_notice.is_visible()
                        page.locator("#raya-practice-search").focus()
                        page.press("#raya-practice-search", "Escape")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-practice-status')
                              ?.textContent
                              ?.includes('3 visible practice object')"""
                        )
                        assert practice_focus_notice.is_hidden()

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
                        assert page.locator(
                            "[data-raya-practice-page-focus]"
                        ).is_hidden()
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
                            tasks_focus_notice = scoped_tasks.locator(
                                "[data-raya-tasks-page-focus]"
                            )
                            assert tasks_focus_notice.is_visible()
                            assert (
                                "Focused on page"
                                in tasks_focus_notice.inner_text()
                            )
                            assert "First Topic" in tasks_focus_notice.inner_text()
                            assert "4 visible tasks" in tasks_focus_notice.inner_text()
                            assert (
                                scoped_tasks.locator(
                                    '[data-raya-task-active="true"]'
                                ).count()
                                == 1
                            )
                            scoped_task_actions = scoped_tasks.locator(
                                "[data-raya-tasks-context-actions]"
                            )
                            assert scoped_task_actions.is_visible()
                            assert scoped_task_actions.locator(
                                "a", has_text="Open page"
                            ).evaluate("node => node.href").endswith(
                                "/unit/topic/index.html#raya-official-unit-assignment"
                            )
                            assert scoped_task_actions.locator(
                                "a", has_text="View graph"
                            ).evaluate("node => node.href").endswith(
                                "/_raya/graph/index.html?page=first-topic"
                            )
                            assert scoped_tasks.evaluate("() => localStorage.length") == 0
                            assert scoped_tasks.evaluate("() => sessionStorage.length") == 0
                            scoped_tasks.click('[data-raya-task-filter="assignment"]')
                            scoped_tasks.wait_for_function(
                                """() => document
                                  .querySelector('#raya-tasks-status')
                                  ?.textContent
                                  ?.includes('1 visible task')"""
                            )
                            assert scoped_tasks.locator(
                                '[data-raya-task-object="unit-project"]'
                            ).is_hidden()
                            scoped_tasks.select_option("#raya-tasks-sort", "due")
                            scoped_tasks.locator(
                                '[data-raya-task-object="unit-assignment"] '
                                ".raya-task-open"
                            ).focus()
                            scoped_tasks.keyboard.press("Escape")
                            scoped_tasks.wait_for_function(
                                """() => document.activeElement?.id === 'raya-tasks-search'
                                  && document
                                    .querySelector('#raya-tasks-status')
                                    ?.textContent
                                    ?.includes('5 visible tasks')"""
                            )
                            assert scoped_tasks.input_value("#raya-tasks-search") == ""
                            assert (
                                scoped_tasks.locator("#raya-tasks-sort").input_value()
                                == "course"
                            )
                            assert (
                                scoped_tasks.locator(
                                    '[data-raya-task-filter="all"]'
                                ).get_attribute("aria-pressed")
                                == "true"
                            )
                            assert scoped_tasks.locator(
                                '[data-raya-task-object="extension-assignment"]'
                            ).is_visible()
                            assert scoped_tasks.locator(
                                '[data-raya-task-object="unit-project"]'
                            ).is_visible()
                            assert tasks_focus_notice.is_hidden()
                            assert (
                                scoped_tasks.locator(
                                    '[data-raya-task-active="true"]'
                                ).count()
                                == 0
                            )
                            assert scoped_task_actions.is_hidden()
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
                            tasks_focus_notice = scoped_tasks.locator(
                                "[data-raya-tasks-page-focus]"
                            )
                            assert tasks_focus_notice.is_visible()
                            scoped_tasks.locator("#raya-tasks-search").focus()
                            scoped_tasks.press("#raya-tasks-search", "Escape")
                            scoped_tasks.wait_for_function(
                                """() => document
                                  .querySelector('#raya-tasks-status')
                                  ?.textContent
                                  ?.includes('5 visible tasks')"""
                            )
                            assert scoped_tasks.locator(
                                '[data-raya-task-object="extension-assignment"]'
                            ).is_visible()
                            assert tasks_focus_notice.is_hidden()
                            assert (
                                scoped_tasks.locator(
                                    '[data-raya-task-active="true"]'
                                ).count()
                                == 0
                            )
                            assert scoped_task_actions.is_hidden()
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
                            tasks_focus_notice = scoped_tasks.locator(
                                "[data-raya-tasks-page-focus]"
                            )
                            assert tasks_focus_notice.is_visible()
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
                            assert tasks_focus_notice.is_hidden()
                            scoped_tasks.goto(
                                f"{base_url}/_raya/tasks/index.html?page=missing-page",
                                wait_until="networkidle",
                            )
                            scoped_tasks.wait_for_function(
                                """() => document
                                  .querySelector('#raya-tasks-status')
                                  ?.textContent
                                  ?.includes('0 visible tasks')"""
                            )
                            assert scoped_tasks.locator(
                                "[data-raya-tasks-page-focus]"
                            ).is_hidden()
                            assert scoped_tasks.locator(
                                "[data-raya-tasks-context-actions]"
                            ).is_hidden()
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
                        page.click("#raya-tasks-clear")
                        page.fill("#raya-tasks-search", "retrievel")
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
                            '[data-raya-task-object="unit-project"]'
                        ).is_visible()
                        page.click("#raya-tasks-clear")
                        page.fill("#raya-tasks-search", "retrievel plan")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-tasks-status')
                              ?.textContent
                              ?.includes('1 visible task')"""
                        )
                        assert page.locator(
                            '[data-raya-task-object="unit-assignment"]'
                        ).is_hidden()
                        assert page.locator(
                            '[data-raya-task-object="unit-project"]'
                        ).is_visible()
                        page.click("#raya-tasks-clear")
                        page.fill("#raya-tasks-search", "retrieval")
                        page.wait_for_function(
                            """() => document
                              .querySelector('#raya-tasks-status')
                              ?.textContent
                              ?.includes('2 visible tasks')"""
                        )
                        page.select_option("#raya-tasks-sort", "due")
                        task_context_actions = page.locator(
                            "[data-raya-tasks-context-actions]"
                        )
                        assert (
                            page.locator('[data-raya-task-active="true"]').count()
                            == 0
                        )
                        assert task_context_actions.is_hidden()
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
                        assert task_context_actions.is_visible()
                        task_context_open = task_context_actions.locator(
                            "a", has_text="Open page"
                        )
                        assert (
                            task_context_open.evaluate(
                                "node => { node.focus(); return document.activeElement === node; }"
                            )
                            is True
                        )
                        assert (
                            "Build a retrieval plan"
                            in task_context_open.get_attribute("aria-label")
                        )
                        assert (
                            task_context_open.evaluate("node => node.href").endswith(
                                "/unit/topic/index.html#raya-official-unit-project"
                            )
                        )
                        assert (
                            task_context_actions.locator("a", has_text="View graph")
                            .evaluate("node => node.href")
                            .endswith("/_raya/graph/index.html?page=first-topic")
                        )
                        active_open_href = task_context_open.evaluate(
                            "node => node.href"
                        )
                        with page.expect_navigation():
                            task_context_open.click()
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
                                schedule_focus_notice = scoped_schedule.locator(
                                    "[data-raya-schedule-page-focus]"
                                )
                                assert schedule_focus_notice.is_visible()
                                assert (
                                    "Focused on page"
                                    in schedule_focus_notice.inner_text()
                                )
                                assert (
                                    "First Topic"
                                    in schedule_focus_notice.inner_text()
                                )
                                assert (
                                    "3 visible schedule item"
                                    in schedule_focus_notice.inner_text()
                                )
                                assert (
                                    scoped_schedule.locator(
                                        '[data-raya-schedule-active="true"]'
                                    ).count()
                                    == 1
                                )
                                scoped_schedule_actions = scoped_schedule.locator(
                                    "[data-raya-schedule-context-actions]"
                                )
                                assert scoped_schedule_actions.is_visible()
                                assert scoped_schedule_actions.locator(
                                    "a", has_text="Open page"
                                ).evaluate("node => node.href").endswith(
                                    "/unit/topic/index.html#raya-official-unit-assignment"
                                )
                                assert scoped_schedule_actions.locator(
                                    "a", has_text="View graph"
                                ).evaluate("node => node.href").endswith(
                                    "/_raya/graph/index.html?page=first-topic"
                                )
                                scoped_schedule.click(
                                    '[data-raya-schedule-kind-filter="due"]'
                                )
                                scoped_schedule.click(
                                    '[data-raya-schedule-type-filter="assignment"]'
                                )
                                scoped_schedule.wait_for_function(
                                    """() => document
                                      .querySelector('#raya-schedule-status')
                                      ?.textContent
                                      ?.includes('1 visible schedule item')"""
                                )
                                assert scoped_schedule.locator(
                                    '[data-raya-schedule-item="unit-project"]'
                                ).is_hidden()
                                scoped_schedule.locator(
                                    '[data-raya-schedule-item="unit-assignment"] '
                                    ".raya-schedule-open"
                                ).focus()
                                scoped_schedule.keyboard.press("Escape")
                                scoped_schedule.wait_for_function(
                                    """() => document.activeElement?.id === 'raya-schedule-search'
                                      && document
                                        .querySelector('#raya-schedule-status')
                                        ?.textContent
                                        ?.includes('4 visible schedule items')"""
                                )
                                assert scoped_schedule.input_value(
                                    "#raya-schedule-search"
                                ) == ""
                                assert scoped_schedule.locator(
                                    '[data-raya-schedule-item="extension-assignment"]'
                                ).is_visible()
                                assert scoped_schedule.locator(
                                    '[data-raya-schedule-item="unit-project"]'
                                ).is_visible()
                                assert (
                                    scoped_schedule.locator(
                                        '[data-raya-schedule-kind-filter="all"]'
                                    ).get_attribute("aria-pressed")
                                    == "true"
                                )
                                assert (
                                    scoped_schedule.locator(
                                        '[data-raya-schedule-type-filter="all"]'
                                    ).get_attribute("aria-pressed")
                                    == "true"
                                )
                                assert schedule_focus_notice.is_hidden()
                                assert (
                                    scoped_schedule.locator(
                                        '[data-raya-schedule-active="true"]'
                                    ).count()
                                    == 0
                                )
                                assert scoped_schedule_actions.is_hidden()
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
                                schedule_focus_notice = scoped_schedule.locator(
                                    "[data-raya-schedule-page-focus]"
                                )
                                assert schedule_focus_notice.is_visible()
                                scoped_schedule.click("#raya-schedule-clear")
                                scoped_schedule.wait_for_function(
                                    """() => document
                                      .querySelector('#raya-schedule-status')
                                      ?.textContent
                                      ?.includes('4 visible schedule items')"""
                                )
                                assert scoped_schedule.locator(
                                    '[data-raya-schedule-item="extension-assignment"]'
                                ).is_visible()
                                assert schedule_focus_notice.is_hidden()
                                assert (
                                    scoped_schedule.locator(
                                        '[data-raya-schedule-active="true"]'
                                    ).count()
                                    == 0
                                )
                                assert scoped_schedule_actions.is_hidden()
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
                                schedule_focus_notice = scoped_schedule.locator(
                                    "[data-raya-schedule-page-focus]"
                                )
                                assert schedule_focus_notice.is_visible()
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
                                assert schedule_focus_notice.is_hidden()
                                scoped_schedule.goto(
                                    f"{base_url}/_raya/schedule/index.html?page=missing-page",
                                    wait_until="networkidle",
                                )
                                scoped_schedule.wait_for_function(
                                    """() => document
                                      .querySelector('#raya-schedule-status')
                                      ?.textContent
                                      ?.includes('0 visible schedule items')"""
                                )
                                assert scoped_schedule.locator(
                                    "[data-raya-schedule-page-focus]"
                                ).is_hidden()
                                assert scoped_schedule.locator(
                                    "[data-raya-schedule-context-actions]"
                                ).is_hidden()
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
                            schedule.click("#raya-schedule-clear")
                            schedule.fill("#raya-schedule-search", "retrievel")
                            schedule.wait_for_function(
                                """() => document
                                  .querySelector('#raya-schedule-status')
                                  ?.textContent
                                  ?.includes('2 visible schedule items')"""
                            )
                            assert schedule.locator(
                                '[data-raya-schedule-item="unit-assignment"]'
                            ).is_visible()
                            assert schedule.locator(
                                '[data-raya-schedule-item="unit-project"]'
                            ).is_visible()
                            schedule.click("#raya-schedule-clear")
                            schedule.fill("#raya-schedule-search", "retrievel plan")
                            schedule.wait_for_function(
                                """() => document
                                  .querySelector('#raya-schedule-status')
                                  ?.textContent
                                  ?.includes('1 visible schedule item')"""
                            )
                            assert schedule.locator(
                                '[data-raya-schedule-item="unit-assignment"]'
                            ).is_hidden()
                            assert schedule.locator(
                                '[data-raya-schedule-item="unit-project"]'
                            ).is_visible()
                            schedule.click("#raya-schedule-clear")
                            schedule_context_actions = schedule.locator(
                                "[data-raya-schedule-context-actions]"
                            )
                            assert (
                                schedule.locator(
                                    '[data-raya-schedule-active="true"]'
                                ).count()
                                == 0
                            )
                            assert schedule_context_actions.is_hidden()
                            schedule.locator("#raya-schedule-search").focus()
                            schedule.press("#raya-schedule-search", "ArrowDown")
                            active_item = schedule.locator(
                                '[data-raya-schedule-active="true"]'
                            )
                            assert active_item.count() == 1
                            assert schedule_context_actions.is_visible()
                            schedule_context_open = schedule_context_actions.locator(
                                "a", has_text="Open page"
                            )
                            assert (
                                schedule_context_open.evaluate(
                                    "node => { node.focus(); return document.activeElement === node; }"
                                )
                                is True
                            )
                            assert (
                                "Problem Set 1"
                                in schedule_context_open.get_attribute("aria-label")
                            )
                            assert (
                                schedule_context_open
                                .evaluate("node => node.href")
                                .endswith(
                                    "/unit/topic/index.html#raya-official-unit-assignment"
                                )
                            )
                            assert (
                                schedule_context_actions.locator(
                                    "a", has_text="View graph"
                                )
                                .evaluate("node => node.href")
                                .endswith("/_raya/graph/index.html?page=first-topic")
                            )
                            assert (
                                "2026-09-15"
                                in schedule.locator(
                                    "[data-raya-schedule-context-meta]"
                                ).inner_text()
                            )
                            assert schedule.evaluate("() => localStorage.length") == 0
                            assert schedule.evaluate("() => sessionStorage.length") == 0
                            schedule_open_href = schedule_context_open.evaluate(
                                "node => node.href"
                            )
                            with schedule.expect_navigation():
                                schedule_context_open.click()
                            assert schedule.url == schedule_open_href
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
        volatile_surface_html = {
            "graph": _fetch_text(f"{base_url}/_raya/graph/index.html"),
            "search": _fetch_text(f"{base_url}/_raya/search/index.html"),
            "practice": _fetch_text(f"{base_url}/_raya/practice/index.html"),
            "tasks": _fetch_text(f"{base_url}/_raya/tasks/index.html"),
            "schedule": _fetch_text(f"{base_url}/_raya/schedule/index.html"),
        }
        rich_css = _fetch_text(f"{base_url}/_raya/render/rich.css")
        accessibility_css = _fetch_text(
            f"{base_url}/_raya/render/accessibility/open-dyslexic.css"
        )
        accessibility_js = _fetch_text(
            f"{base_url}/_raya/render/accessibility/open-dyslexic-toggle.js"
        )
        comfort_prepaint_js = _fetch_text(
            f"{base_url}/_raya/render/accessibility/comfort-prepaint.js"
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
    assert 'src="_raya/render/accessibility/comfort-prepaint.js"' in index_html
    assert 'src="_raya/render/accessibility/open-dyslexic-toggle.js"' in index_html
    assert 'localStorage.getItem("raya:open-dyslexic")' not in index_html
    assert 'localStorage.getItem("raya:text-size")' not in index_html
    assert index_html.index('src="_raya/render/accessibility/comfort-prepaint.js"') < (
        index_html.index('href="_raya/render/rich.css"')
    )
    for surface_name, surface_html in volatile_surface_html.items():
        assert (
            'localStorage.getItem("raya:open-dyslexic")' not in surface_html
        ), surface_name
        assert 'localStorage.getItem("raya:text-size")' not in surface_html, (
            surface_name
        )
    assert "@font-face" in accessibility_css
    assert "OpenDyslexic" in accessibility_css
    assert 'localStorage.getItem("raya:open-dyslexic")' in comfort_prepaint_js
    assert 'localStorage.getItem("raya:text-size")' in comfort_prepaint_js
    assert "fetch(" not in comfort_prepaint_js
    assert "localStorage" in accessibility_js
    assert "data-raya-open-dyslexic" in accessibility_js
    assert 'data-raya-course-map="expanded"' in index_html
    assert 'aria-expanded="true" aria-label="Collapse course map">' in index_html
    assert 'data-raya-command-icon="map"' in index_html
    assert '<span class="raya-command-label">Course map</span>' in index_html
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
        "grid-template-columns: 5.5rem minmax(48rem, 1fr) minmax(15rem, 15rem)"
        in rich_css
    )
    assert "transition: grid-template-columns 220ms ease" in rich_css
    assert ".raya-course-map-toggle:focus-visible" in rich_css
    assert ".raya-rail-toggle:focus-visible" in rich_css
    assert "outline: 3px solid var(--raya-color-accent)" in rich_css
    assert "@media (max-width: 1279px)" in rich_css


def test_render_fixture_skin_toggle_cycles_local_override(tmp_path: Path) -> None:
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
                    initial = page.evaluate(
                        """() => {
                          const root = document.documentElement;
                          const body = document.body;
                          const button = document.querySelector('.raya-skin-toggle');
                          return {
                            authoredSkin: body.getAttribute('data-raya-skin'),
                            override: root.getAttribute('data-raya-skin-override'),
                            active: button?.getAttribute('data-raya-skin-active'),
                            label: button?.getAttribute('aria-label'),
                            pressed: button?.getAttribute('aria-pressed'),
                            accent: getComputedStyle(body)
                              .getPropertyValue('--raya-color-accent')
                              .trim(),
                          };
                        }"""
                    )
                    assert initial == {
                        "authoredSkin": "practice-lab",
                        "override": None,
                        "active": "authored",
                        "label": "Skin: authored",
                        "pressed": "false",
                        "accent": initial["accent"],
                    }

                    page.click(".raya-skin-toggle")
                    switched = page.evaluate(
                        """() => {
                          const root = document.documentElement;
                          const body = document.body;
                          const button = document.querySelector('.raya-skin-toggle');
                          return {
                            authoredSkin: body.getAttribute('data-raya-skin'),
                            override: root.getAttribute('data-raya-skin-override'),
                            active: button?.getAttribute('data-raya-skin-active'),
                            label: button?.getAttribute('aria-label'),
                            pressed: button?.getAttribute('aria-pressed'),
                            stored: localStorage.getItem('raya:skin-override'),
                            accent: getComputedStyle(body)
                              .getPropertyValue('--raya-color-accent')
                              .trim(),
                          };
                        }"""
                    )
                    assert switched["authoredSkin"] == "practice-lab"
                    assert switched["override"]
                    assert switched["active"] == switched["override"]
                    assert switched["pressed"] == "true"
                    assert switched["stored"] == switched["override"]
                    assert switched["accent"] != initial["accent"]
                    assert switched["label"].startswith("Skin: ")
                    assert switched["label"] != "Skin: authored"

                    page.reload(wait_until="networkidle")
                    restored = page.evaluate(
                        """() => ({
                          authoredSkin: document.body.getAttribute('data-raya-skin'),
                          override: document.documentElement
                            .getAttribute('data-raya-skin-override'),
                          active: document.querySelector('.raya-skin-toggle')
                            ?.getAttribute('data-raya-skin-active'),
                          stored: localStorage.getItem('raya:skin-override'),
                        })"""
                    )
                    assert restored == {
                        "authoredSkin": "practice-lab",
                        "override": switched["override"],
                        "active": switched["override"],
                        "stored": switched["override"],
                    }

                    for _ in range(12):
                        page.click(".raya-skin-toggle")
                        if page.evaluate(
                            """() => !document.documentElement
                              .hasAttribute('data-raya-skin-override')"""
                        ):
                            break
                    authored = page.evaluate(
                        """() => ({
                          authoredSkin: document.body.getAttribute('data-raya-skin'),
                          override: document.documentElement
                            .getAttribute('data-raya-skin-override'),
                          active: document.querySelector('.raya-skin-toggle')
                            ?.getAttribute('data-raya-skin-active'),
                          label: document.querySelector('.raya-skin-toggle')
                            ?.getAttribute('aria-label'),
                          pressed: document.querySelector('.raya-skin-toggle')
                            ?.getAttribute('aria-pressed'),
                          stored: localStorage.getItem('raya:skin-override'),
                        })"""
                    )
                    assert authored == {
                        "authoredSkin": "practice-lab",
                        "override": None,
                        "active": "authored",
                        "label": "Skin: authored",
                        "pressed": "false",
                        "stored": None,
                    }
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


def test_reader_comfort_labels_are_visible_on_desktop_only(
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
                page = browser.new_page(viewport={"width": 1366, "height": 900})
                requested_urls: list[str] = []
                page.on("request", lambda request: requested_urls.append(request.url))
                try:
                    page.goto(
                        f"{handle.base_url}/reader-ux/index.html",
                        wait_until="networkidle",
                    )
                    requested_urls.clear()
                    _assert_no_horizontal_overflow(page)
                    desktop = page.evaluate(
                        """() => {
                          const labelBox = (selector) => {
                            const label = document.querySelector(selector);
                            const box = label.getBoundingClientRect();
                            const style = getComputedStyle(label);
                            return {
                              text: label.textContent.trim(),
                              width: box.width,
                              height: box.height,
                              position: style.position,
                              overflow: style.overflow,
                            };
                          };
                          return {
                            size: labelBox('.raya-command-size .raya-command-label'),
                            font: labelBox('.raya-command-font .raya-command-label'),
                            topBarHeight: document
                              .querySelector('.raya-top-command-bar')
                              .getBoundingClientRect().height,
                            scrollWidth: document.documentElement.scrollWidth,
                            clientWidth: document.documentElement.clientWidth,
                            localKeys: Object.keys(window.localStorage),
                            sessionKeys: Object.keys(window.sessionStorage),
                          };
                        }"""
                    )
                    assert desktop["size"]["text"] == "Text size"
                    assert desktop["font"]["text"] == "OpenDyslexic"
                    assert desktop["size"]["width"] >= 48
                    assert desktop["font"]["width"] >= 80
                    assert desktop["size"]["height"] >= 16
                    assert desktop["font"]["height"] >= 16
                    assert desktop["size"]["position"] == "static"
                    assert desktop["font"]["position"] == "static"
                    assert desktop["topBarHeight"] <= 96
                    assert desktop["scrollWidth"] <= desktop["clientWidth"]
                    assert desktop["localKeys"] == []
                    assert desktop["sessionKeys"] == []
                    assert requested_urls == []

                    page.set_viewport_size({"width": 390, "height": 844})
                    page.wait_for_function(
                        "() => document.documentElement.clientWidth === 390"
                    )
                    mobile = page.evaluate(
                        """() => {
                          const labelBox = (selector) => {
                            const label = document.querySelector(selector);
                            const box = label.getBoundingClientRect();
                            const style = getComputedStyle(label);
                            return {
                              width: box.width,
                              height: box.height,
                              position: style.position,
                              overflow: style.overflow,
                            };
                          };
                          return {
                            size: labelBox('.raya-command-size .raya-command-label'),
                            font: labelBox('.raya-command-font .raya-command-label'),
                            scrollWidth: document.documentElement.scrollWidth,
                            clientWidth: document.documentElement.clientWidth,
                          };
                        }"""
                    )
                    assert mobile["size"]["width"] <= 2
                    assert mobile["font"]["width"] <= 2
                    assert mobile["size"]["height"] <= 2
                    assert mobile["font"]["height"] <= 2
                    assert mobile["size"]["position"] == "absolute"
                    assert mobile["font"]["position"] == "absolute"
                    assert mobile["scrollWidth"] <= mobile["clientWidth"]
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


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


def test_render_fixture_restores_comfort_preferences_before_deferred_script(
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
                context.add_init_script(
                    """
                    localStorage.setItem('raya:open-dyslexic', 'true');
                    localStorage.setItem('raya:text-size', 'x-large');
                    """
                )
                page = context.new_page()
                try:
                    blocked_scripts: list[str] = []

                    def block_deferred_accessibility(route) -> None:
                        blocked_scripts.append(route.request.url)
                        route.abort()

                    page.route(
                        "**/_raya/render/accessibility/open-dyslexic-toggle.js",
                        block_deferred_accessibility,
                    )
                    page.goto(f"{base_url}/index.html", wait_until="domcontentloaded")
                    restored = page.evaluate(
                        """() => ({
                          dyslexic: document.documentElement
                            .getAttribute('data-raya-open-dyslexic'),
                          size: document.documentElement
                            .getAttribute('data-raya-text-size'),
                          bodyToken: getComputedStyle(document.body)
                            .getPropertyValue('--raya-font-body')
                            .trim(),
                          articleScale: getComputedStyle(
                            document.querySelector('.raya-main-article')
                          ).getPropertyValue('--raya-reader-text-scale').trim(),
                        })"""
                    )
                finally:
                    page.close()
                    context.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert blocked_scripts
    assert restored["dyslexic"] == "true"
    assert restored["size"] == "x-large"
    assert restored["bodyToken"] == '"OpenDyslexic"'
    assert restored["articleScale"] == "1.25"


def test_render_fixture_reader_focus_command_collapses_map_and_rail(
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
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                try:
                    page.goto(f"{handle.base_url}/reader-ux/index.html")
                    initial_url = page.url
                    focus = page.locator("[data-raya-reader-focus-toggle]")
                    assert focus.is_visible()
                    assert focus.get_attribute("aria-pressed") == "false"
                    focus.focus()
                    assert page.evaluate(
                        "() => document.activeElement === document.querySelector('[data-raya-reader-focus-toggle]')"
                    )

                    focus.click()
                    assert (
                        page.locator("html").get_attribute("data-raya-reader-focus")
                        == "active"
                    )
                    assert (
                        page.locator("#raya-course-map").get_attribute(
                            "data-raya-course-map"
                        )
                        == "collapsed"
                    )
                    assert (
                        page.locator("#raya-learning-rail").get_attribute(
                            "data-raya-learning-rail"
                        )
                        == "collapsed"
                    )
                    assert focus.get_attribute("aria-pressed") == "true"
                    assert page.url == initial_url
                    assert page.evaluate(
                        "() => [Object.keys(localStorage), Object.keys(sessionStorage)]"
                    ) == [[], []]

                    page.set_viewport_size({"width": 1100, "height": 900})
                    page.wait_for_function(
                        """() => document.documentElement.dataset.rayaReaderFocus === 'inactive'"""
                    )
                    assert focus.is_hidden()
                    assert (
                        page.locator("#raya-course-map").get_attribute(
                            "data-raya-course-map"
                        )
                        == "expanded"
                    )
                    assert (
                        page.locator("#raya-learning-rail").get_attribute(
                            "data-raya-learning-rail"
                        )
                        == "expanded"
                    )

                    page.set_viewport_size({"width": 1440, "height": 900})
                    page.wait_for_function(
                        """() => document.documentElement.dataset.rayaCourseMap === 'expanded'
                          && document.documentElement.dataset.rayaLearningRail === 'expanded'"""
                    )
                    assert focus.is_visible()
                    assert focus.get_attribute("aria-pressed") == "false"

                    focus.click()
                    page.click(".raya-command-map")
                    assert (
                        page.locator("html").get_attribute("data-raya-reader-focus")
                        == "inactive"
                    )
                    assert focus.get_attribute("aria-pressed") == "false"

                    focus.click()
                    page.click("[data-raya-learning-rail-expand]")
                    assert (
                        page.locator("html").get_attribute("data-raya-reader-focus")
                        == "inactive"
                    )
                    assert focus.get_attribute("aria-pressed") == "false"

                    focus.click()
                    focus.click()
                    assert (
                        page.locator("html").get_attribute("data-raya-reader-focus")
                        == "inactive"
                    )
                    assert (
                        page.locator("#raya-course-map").get_attribute(
                            "data-raya-course-map"
                        )
                        == "expanded"
                    )
                    assert (
                        page.locator("#raya-learning-rail").get_attribute(
                            "data-raya-learning-rail"
                        )
                        == "expanded"
                    )
                    assert focus.get_attribute("aria-pressed") == "false"
                    assert page.url == initial_url
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


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
                    {"width": 1920, "height": 900},
                    {"width": 1800, "height": 900},
                    {"width": 1440, "height": 900},
                    {"width": 640, "height": 900},
                    {"width": 521, "height": 900},
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
                              const visibleCommands = commands.filter(
                                (item) => item.getClientRects().length > 0
                              );
                              const topBar = document.querySelector('.raya-top-command-bar');
                              const commandTops = visibleCommands.map(
                                (item) => item.getBoundingClientRect().top
                              );
                              const groups = Array.from(
                                document.querySelectorAll('[data-raya-command-group]')
                              ).map((group) => ({
                                kind: group.getAttribute('data-raya-command-group'),
                                label: group.getAttribute('aria-label'),
                                role: group.getAttribute('role'),
                                classes: Array.from(
                                  group.querySelectorAll('.raya-command')
                                ).map((command) => Array.from(command.classList)
                                  .find((name) => name.startsWith('raya-command-')
                                    && name !== 'raya-command-icon'
                                    && name !== 'raya-command-label')),
                                box: (() => {
                                  const rect = group.getBoundingClientRect();
                                  return {
                                    left: rect.left,
                                    right: rect.right,
                                    width: rect.width,
                                  };
                                })(),
                              }));
                              return {
                                count: commands.length,
                                groups,
                                visibleCount: visibleCommands.length,
                                minHeights: visibleCommands.map(
                                  (item) => item.getBoundingClientRect().height
                                ),
                                topBarHeight: topBar.getBoundingClientRect().height,
                                commandTopSpread: commandTops.length
                                  ? Math.max(...commandTops) - Math.min(...commandTops)
                                  : 0,
                                topBarWidth: topBar.scrollWidth,
                                viewportWidth: document.documentElement.clientWidth,
                                formBox: (() => {
                                  const box = document
                                    .querySelector('.raya-command-search-form')
                                    ?.getBoundingClientRect();
                                  return box
                                    ? {
                                        left: box.left,
                                        right: box.right,
                                        width: box.width,
                                      }
                                      : null;
                                })(),
                                submitBox: (() => {
                                  const box = document
                                    .querySelector('.raya-command-search-submit')
                                    ?.getBoundingClientRect();
                                  return box
                                    ? {
                                        width: box.width,
                                        height: box.height,
                                      }
                                    : null;
                                })(),
                                submitLabelBox: (() => {
                                  const box = document
                                    .querySelector('.raya-command-search-submit span')
                                    ?.getBoundingClientRect();
                                  return box
                                    ? {
                                        width: box.width,
                                        height: box.height,
                                      }
                                    : null;
                                })(),
                                submitWhiteSpace: getComputedStyle(
                                  document.querySelector('.raya-command-search-submit')
                                ).whiteSpace,
                            submitLabelWhiteSpace: getComputedStyle(
                              document.querySelector('.raya-command-search-submit span')
                            ).whiteSpace,
                            commandLabelBoxes: Object.fromEntries(
                              Array.from(document.querySelectorAll('.raya-command')).map((command) => {
                                const marker = Array.from(command.classList)
                                  .find((name) => name.startsWith('raya-command-')
                                    && name !== 'raya-command-icon'
                                    && name !== 'raya-command-label');
                                const label = command.querySelector('.raya-command-label');
                                const box = label?.getBoundingClientRect();
                                return [marker, {
                                  text: label?.textContent?.trim() || '',
                                  width: box ? box.width : 0,
                                  height: box ? box.height : 0,
                                  clipped: label
                                    ? getComputedStyle(label).clip !== 'auto'
                                      || getComputedStyle(label).clipPath !== 'none'
                                    : true,
                                }];
                              })
                            ),
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
                                focusLabel: document
                                  .querySelector('.raya-command-focus')
                                  ?.getAttribute('aria-label'),
                                focusPressed: document
                                  .querySelector('.raya-command-focus')
                                  ?.getAttribute('aria-pressed'),
                                focusVisible: !!document
                                  .querySelector('.raya-command-focus')
                                  ?.getClientRects().length,
                                railContextLabel: document
                                  .querySelector('.raya-command-context')
                                  ?.getAttribute('aria-label'),
                                railContextExpanded: document
                                  .querySelector('.raya-command-context')
                                  ?.getAttribute('aria-expanded'),
                                railContextVisible: !!document
                                  .querySelector('.raya-command-context')
                                  ?.getClientRects().length,
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
                                sectionHref: document
                                  .querySelector('.raya-reading-context-section')
                                  ?.getAttribute('href') || '',
                                sectionText: document
                                  .querySelector('.raya-reading-context-section')
                                  ?.textContent
                                  ?.trim() || '',
                                sectionLabelText: document
                                  .querySelector('.raya-reading-context-section-label')
                                  ?.textContent
                                  ?.trim() || '',
                                sectionLabelVisible: (() => {
                                  const label = document
                                    .querySelector('.raya-reading-context-section-label');
                                  return !!label && label.getClientRects().length > 0
                                    && getComputedStyle(label).display !== 'none';
                                })(),
                                sectionWidth: document
                                  .querySelector('.raya-reading-context-section')
                                  ?.getBoundingClientRect()
                                  ?.width || 0,
                                prevHref: document
                                  .querySelector('.raya-reading-context-prev')
                                  ?.getAttribute('href') || '',
                                nextHref: document
                                  .querySelector('.raya-reading-context-next')
                                  ?.getAttribute('href') || '',
                          };
                        }"""
                        )
                        assert state["count"] == 11
                        assert [group["kind"] for group in state["groups"]] == [
                            "discovery",
                            "layout",
                            "comfort",
                        ]
                        assert [group["label"] for group in state["groups"]] == [
                            "Discovery workspaces",
                            "Reader layout",
                            "Reading comfort",
                        ]
                        assert [group["role"] for group in state["groups"]] == [
                            "group",
                            "group",
                            "group",
                        ]
                        assert state["groups"][0]["classes"] == [
                            "raya-command-search",
                            "raya-command-graph",
                            "raya-command-practice",
                            "raya-command-tasks",
                            "raya-command-schedule",
                        ]
                        assert state["groups"][1]["classes"] == [
                            "raya-command-map",
                            "raya-command-focus",
                            "raya-command-context",
                        ]
                        assert state["groups"][2]["classes"] == [
                            "raya-command-size",
                            "raya-command-font",
                            "raya-command-skin",
                        ]
                        for group in state["groups"]:
                            assert group["box"]["left"] >= 0
                            assert group["box"]["right"] <= state["viewportWidth"]
                            assert group["box"]["width"] > 0
                        assert state["visibleCount"] == (
                            10 if viewport["width"] >= 1280 else 8
                        )
                        assert all(height >= 36 for height in state["minHeights"])
                        assert state["topBarWidth"] <= state["viewportWidth"]
                        assert state["formBox"] is not None
                        assert state["formBox"]["left"] >= 0
                        assert state["formBox"]["right"] <= state["viewportWidth"]
                        assert state["formBox"]["width"] >= 160
                        assert state["submitBox"] is not None
                        assert state["submitLabelBox"] is not None
                        assert state["submitWhiteSpace"] == "nowrap"
                        assert state["submitLabelWhiteSpace"] == "nowrap"
                        assert state["submitBox"]["width"] >= 48
                        assert state["submitLabelBox"]["height"] < 24
                        if viewport["width"] >= 1800:
                            for command_name in (
                                "raya-command-graph",
                                "raya-command-practice",
                                "raya-command-tasks",
                                "raya-command-schedule",
                                "raya-command-map",
                                "raya-command-focus",
                                "raya-command-context",
                                "raya-command-size",
                                "raya-command-font",
                                "raya-command-skin",
                            ):
                                label_box = state["commandLabelBoxes"][command_name]
                                assert label_box["text"]
                                assert label_box["width"] > 12
                                assert label_box["height"] > 10
                                assert label_box["clipped"] is False
                        elif viewport["width"] >= 1280:
                            assert state["commandLabelBoxes"]["raya-command-font"][
                                "clipped"
                            ] is True
                        if viewport["width"] >= 1024:
                            assert state["topBarHeight"] <= 96
                            assert state["commandTopSpread"] <= 4
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
                        assert state["focusLabel"] == "Focus reading"
                        assert state["focusPressed"] == "false"
                        assert state["focusVisible"] == (viewport["width"] >= 1280)
                        assert state["railContextLabel"] == (
                            "Hide learning context"
                            if viewport["width"] >= 1280
                            else "Open learning context"
                        )
                        assert state["railContextExpanded"] == (
                            "true" if viewport["width"] >= 1280 else "false"
                        )
                        assert state["railContextVisible"] == (
                            viewport["width"] >= 1280
                        )
                        assert state["sizeLabel"] == "Text size: normal"
                        assert state["sizePressed"] == "false"
                        assert state["fontPressed"] == "false"
                        assert "Raya Lucaria Render Fixture" in state["contextText"]
                        assert "Page 1 of 6" in state["contextText"]
                        assert state["contextWidth"] > 0
                        assert state["sectionHref"] == "#rich-static-baseline"
                        assert state["sectionText"].startswith("Now")
                        assert state["sectionLabelText"] == "Rich Static Baseline"
                        assert state["sectionLabelVisible"] == (
                            viewport["width"] >= 520
                        )
                        assert state["sectionWidth"] >= 40
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

    assert len(states) == 6


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
                    {"width": 1920, "height": 900},
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
                                  const commandBarInner = document.querySelector('.raya-top-command-bar-inner');
                                  const commands = Array.from(document.querySelectorAll('.raya-command'));
                                  const visibleCommands = commands.filter(
                                    (button) => button.getClientRects().length > 0
                                  );
                                  const currentMapLink = document.querySelector('#raya-course-map a[aria-current="page"]');
                                  return {
                                    shellWidth: shell.getBoundingClientRect().width,
                                    commandBarInnerWidth: commandBarInner.getBoundingClientRect().width,
                                    mapWidth: map.getBoundingClientRect().width,
                                    articleWidth: article.getBoundingClientRect().width,
                                    railWidth: rail.getBoundingClientRect().width,
                                    commandBarHeight: commandBar.getBoundingClientRect().height,
                                    commandHeights: visibleCommands.map((button) => button.getBoundingClientRect().height),
                                    commandWidths: visibleCommands.map((button) => button.getBoundingClientRect().width),
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
                            if viewport["width"] >= 1900:
                                assert (
                                    metrics["shellWidth"]
                                    >= viewport["width"] - 32
                                )
                                assert (
                                    metrics["commandBarInnerWidth"]
                                    >= viewport["width"] - 32
                                )
                            assert metrics["commandBarHeight"] <= 96
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
                            shell_state = page.evaluate(
                                """() => {
                                  const root = document.documentElement;
                                  const shell = document.querySelector('.raya-learning-shell');
                                  const map = document.querySelector('#raya-course-map');
                                  const article = document.querySelector('#raya-article');
                                  const readableBlocks = Array.from(article.children)
                                    .filter((child) => getComputedStyle(child).maxWidth !== '100%');
                                  const rail = document.querySelector('#raya-learning-rail');
                                  const commandBar = document.querySelector('.raya-top-command-bar');
                                  return {
                                    ready: root.dataset.rayaShellReady,
                                    shellTransition: getComputedStyle(shell).transition,
                                    mapTransition: getComputedStyle(map).transition,
                                    railTransition: getComputedStyle(rail).transition,
                                    articleMaxWidth: getComputedStyle(article).maxWidth,
                                    readableBlockMaxWidths: readableBlocks.map(
                                      (child) => getComputedStyle(child).maxWidth
                                    ),
                                    commandGap: getComputedStyle(commandBar).gap,
                                  };
                                }"""
                            )
                            assert shell_state["ready"] == "true"
                            assert (
                                "grid-template-columns"
                                in shell_state["shellTransition"]
                            )
                            assert "transform" in shell_state["mapTransition"]
                            assert "transform" in shell_state["railTransition"]
                            assert shell_state["articleMaxWidth"] == "none"
                            assert any(
                                width != "none"
                                for width in shell_state["readableBlockMaxWidths"]
                            )
                            assert shell_state["commandGap"] != "normal"
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
                                    details: Object.fromEntries(links.map((link) => [
                                      link
                                        .querySelector('.raya-course-map-workspace-label')
                                        ?.textContent
                                        ?.trim() || '',
                                      Array.from(
                                        link.querySelectorAll(
                                          '[data-raya-course-map-workspace-detail]'
                                        )
                                      ).map((detail) => detail.textContent.trim()),
                                    ])),
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
                            assert workspace["badges"][1] == "2 links"
                            assert workspace["details"]["Graph"] == [
                                "0 from this page",
                                "2 links here",
                            ]
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
                                  ?.getBoundingClientRect().width <= 112"""
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
                                  ?.getBoundingClientRect().width <= 112"""
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
                                  mapButtonText: document
                                    .querySelector('#raya-course-map .raya-course-map-toggle')
                                    ?.textContent
                                    ?.trim(),
                                  railExpandText: document
                                    .querySelector('.raya-learning-rail-expand')
                                    ?.textContent
                                    ?.trim(),
                                  mapButtonWritingMode: getComputedStyle(
                                    document.querySelector('#raya-course-map .raya-course-map-toggle')
                                  ).writingMode,
                                  railButtonWritingMode: getComputedStyle(
                                    document.querySelector('.raya-learning-rail-expand')
                                  ).writingMode,
                                  articleLeft: document
                                    .querySelector('#raya-article')
                                    .getBoundingClientRect().left,
                                  articleRight: document
                                    .querySelector('#raya-article')
                                    .getBoundingClientRect().right,
                                  viewportWidth: window.innerWidth,
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
                            assert 64 <= collapsed["mapWidth"] <= 112
                            assert 64 <= collapsed["railWidth"] <= 112
                            assert collapsed["mapButtonAfter"] == '"Map"'
                            assert collapsed["railButtonAfter"] == '"Context"'
                            assert collapsed["railBodyHidden"] == "true"
                            assert collapsed["railBodyInert"] is True
                            assert collapsed["mapButtonText"] in {"Expand map", "Map"}
                            assert collapsed["railExpandText"] == "Context"
                            assert collapsed["mapButtonWritingMode"] == "horizontal-tb"
                            assert (
                                collapsed["railButtonWritingMode"] == "horizontal-tb"
                            )
                            assert collapsed["articleLeft"] >= 0
                            assert (
                                collapsed["articleRight"]
                                <= collapsed["viewportWidth"]
                            )
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
                            or "raya-command-focus" in focused
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


def test_render_fixture_shell_respects_reduced_motion(tmp_path: Path) -> None:
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
                page.emulate_media(reduced_motion="reduce")
                try:
                    page.goto(
                        f"{handle.base_url}/reader-ux/index.html",
                        wait_until="networkidle",
                    )
                    state = page.evaluate(
                        """() => ({
                          shellTransition: getComputedStyle(
                            document.querySelector('.raya-learning-shell')
                          ).transitionDuration,
                          mapTransition: getComputedStyle(
                            document.querySelector('#raya-course-map')
                          ).transitionDuration,
                          railPanelTransition: getComputedStyle(
                            document.querySelector('.raya-rail-panel-body')
                          ).transitionDuration,
                        })"""
                    )
                    assert state["shellTransition"] in {
                        "0s",
                        "0s, 0s",
                        "0s, 0s, 0s",
                    }
                    assert state["mapTransition"] in {
                        "0s",
                        "0s, 0s",
                        "0s, 0s, 0s",
                        "0s, 0s, 0s, 0s",
                        "0s, 0s, 0s, 0s, 0s",
                    }
                    assert state["railPanelTransition"] in {
                        "0s",
                        "0s, 0s",
                        "0s, 0s, 0s",
                    }
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
                    page.evaluate(
                        "() => document.fonts ? document.fonts.ready.then(() => true) : true"
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


def test_minimal_course_map_current_path_is_expanded_and_collapsible(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "minimal"
    shutil.copytree(MINIMAL, course, ignore=shutil.ignore_patterns("artifact"))
    _add_official_task_objects(course)
    branch_a = course / "course" / "2_map_branch_a"
    branch_b = course / "course" / "3_map_branch_b"
    branch_a_child = branch_a / "1_branch_a_child"
    branch_b_child = branch_b / "1_branch_b_child"
    branch_a_child.mkdir(parents=True)
    branch_b_child.mkdir(parents=True)
    (branch_a / "0_index.md").write_text(
        "---\n"
        "id: map-branch-a\n"
        "title: Map Branch A\n"
        "summary: Extra sibling branch for course-map scan tests.\n"
        "status: ready\n"
        "---\n\n"
        "# Map Branch A\n\n"
        "Sibling branch A.\n",
        encoding="utf-8",
    )
    (branch_a_child / "0_index.md").write_text(
        "---\n"
        "id: map-branch-a-child\n"
        "title: Map Branch A Child\n"
        "summary: Extra child for course-map scan tests.\n"
        "status: ready\n"
        "---\n\n"
        "# Map Branch A Child\n\n"
        "Child page A.\n",
        encoding="utf-8",
    )
    (branch_b / "0_index.md").write_text(
        "---\n"
        "id: map-branch-b\n"
        "title: Map Branch B\n"
        "summary: Extra sibling branch for course-map scan tests.\n"
        "status: ready\n"
        "---\n\n"
        "# Map Branch B\n\n"
        "Sibling branch B.\n",
        encoding="utf-8",
    )
    (branch_b_child / "0_index.md").write_text(
        "---\n"
        "id: map-branch-b-child\n"
        "title: Map Branch B Child\n"
        "summary: Extra child for course-map scan tests.\n"
        "status: ready\n"
        "---\n\n"
        "# Map Branch B Child\n\n"
        "Child page B.\n",
        encoding="utf-8",
    )
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

                    page.click('[data-raya-course-map-action="scan"]')
                    scan_start = page.evaluate(
                        """() => ({
                          scan: document
                            .querySelector('#raya-course-map')
                            ?.dataset
                            ?.rayaCourseMapScan,
                          scanPressed: document
                            .querySelector('[data-raya-course-map-action="scan"]')
                            ?.getAttribute('aria-pressed'),
                          firstUnitExpanded: document
                            .querySelector('[data-raya-map-node="first-unit"] [data-raya-map-node-toggle]')
                            ?.getAttribute('aria-expanded'),
                          branchAExpanded: document
                            .querySelector('[data-raya-map-node="map-branch-a"] [data-raya-map-node-toggle]')
                            ?.getAttribute('aria-expanded'),
                          branchBExpanded: document
                            .querySelector('[data-raya-map-node="map-branch-b"] [data-raya-map-node-toggle]')
                            ?.getAttribute('aria-expanded'),
                          currentVisible: !!document
                            .querySelector('#raya-course-map a[aria-current="page"]')
                            ?.checkVisibility(),
                          localStorageKeys: Object.keys(localStorage),
                          sessionStorageKeys: Object.keys(sessionStorage),
                        })"""
                    )
                    assert scan_start == {
                        "scan": "active",
                        "scanPressed": "true",
                        "firstUnitExpanded": "true",
                        "branchAExpanded": "false",
                        "branchBExpanded": "false",
                        "currentVisible": True,
                        "localStorageKeys": [],
                        "sessionStorageKeys": [],
                    }

                    page.click('[data-raya-map-node="map-branch-a"] [data-raya-map-node-toggle]')
                    page.click('[data-raya-map-node="map-branch-b"] [data-raya-map-node-toggle]')
                    scan_sibling_collapse = page.evaluate(
                        """() => ({
                          scan: document
                            .querySelector('#raya-course-map')
                            ?.dataset
                            ?.rayaCourseMapScan,
                          branchAExpanded: document
                            .querySelector('[data-raya-map-node="map-branch-a"] [data-raya-map-node-toggle]')
                            ?.getAttribute('aria-expanded'),
                          branchAChildrenHidden: document
                            .querySelector('[data-raya-map-node="map-branch-a"] > [data-raya-map-children]')
                            ?.hasAttribute('hidden'),
                          branchBExpanded: document
                            .querySelector('[data-raya-map-node="map-branch-b"] [data-raya-map-node-toggle]')
                            ?.getAttribute('aria-expanded'),
                          branchBChildrenHidden: document
                            .querySelector('[data-raya-map-node="map-branch-b"] > [data-raya-map-children]')
                            ?.hasAttribute('hidden'),
                          localStorageKeys: Object.keys(localStorage),
                          sessionStorageKeys: Object.keys(sessionStorage),
                        })"""
                    )
                    assert scan_sibling_collapse == {
                        "scan": "active",
                        "branchAExpanded": "false",
                        "branchAChildrenHidden": True,
                        "branchBExpanded": "true",
                        "branchBChildrenHidden": False,
                        "localStorageKeys": [],
                        "sessionStorageKeys": [],
                    }

                    page.focus(
                        '[data-raya-map-node="map-branch-b"] > .raya-course-map-node-row a'
                    )
                    page.keyboard.press("ArrowRight")
                    keyboard_branch_child = page.evaluate(
                        """() => ({
                          activeNode: document.activeElement
                            ?.closest("[data-raya-map-node]")
                            ?.getAttribute("data-raya-map-node"),
                          branchBExpanded: document
                            .querySelector('[data-raya-map-node="map-branch-b"] [data-raya-map-node-toggle]')
                            ?.getAttribute('aria-expanded'),
                        })"""
                    )
                    assert keyboard_branch_child == {
                        "activeNode": "map-branch-b-child",
                        "branchBExpanded": "true",
                    }

                    leaf_url_before_arrow = page.url
                    page.keyboard.press("ArrowRight")
                    page.wait_for_timeout(250)
                    keyboard_leaf_noop = page.evaluate(
                        """() => ({
                          activeNode: document.activeElement
                            ?.closest("[data-raya-map-node]")
                            ?.getAttribute("data-raya-map-node"),
                          url: window.location.href,
                        })"""
                    )
                    assert keyboard_leaf_noop == {
                        "activeNode": "map-branch-b-child",
                        "url": leaf_url_before_arrow,
                    }

                    page.keyboard.press("ArrowLeft")
                    keyboard_parent_focus = page.evaluate(
                        """() => ({
                          activeNode: document.activeElement
                            ?.closest("[data-raya-map-node]")
                            ?.getAttribute("data-raya-map-node"),
                          branchBExpanded: document
                            .querySelector('[data-raya-map-node="map-branch-b"] [data-raya-map-node-toggle]')
                            ?.getAttribute('aria-expanded'),
                        })"""
                    )
                    assert keyboard_parent_focus == {
                        "activeNode": "map-branch-b",
                        "branchBExpanded": "true",
                    }

                    page.keyboard.press("ArrowLeft")
                    keyboard_parent_collapse = page.evaluate(
                        """() => ({
                          activeNode: document.activeElement
                            ?.closest("[data-raya-map-node]")
                            ?.getAttribute("data-raya-map-node"),
                          branchBExpanded: document
                            .querySelector('[data-raya-map-node="map-branch-b"] [data-raya-map-node-toggle]')
                            ?.getAttribute('aria-expanded'),
                          branchBChildVisible: !!document
                            .querySelector('[data-raya-map-node="map-branch-b-child"]')
                            ?.checkVisibility(),
                        })"""
                    )
                    assert keyboard_parent_collapse == {
                        "activeNode": "map-branch-b",
                        "branchBExpanded": "false",
                        "branchBChildVisible": False,
                    }

                    page.keyboard.press("ArrowUp")
                    keyboard_previous_visible = page.evaluate(
                        """() => document.activeElement
                          ?.closest("[data-raya-map-node]")
                          ?.getAttribute("data-raya-map-node")"""
                    )
                    assert keyboard_previous_visible == "map-branch-a"

                    page.keyboard.press("ArrowDown")
                    keyboard_next_visible = page.evaluate(
                        """() => document.activeElement
                          ?.closest("[data-raya-map-node]")
                          ?.getAttribute("data-raya-map-node")"""
                    )
                    assert keyboard_next_visible == "map-branch-b"

                    page.keyboard.press("Home")
                    keyboard_first_visible = page.evaluate(
                        """() => document.activeElement
                          ?.closest("[data-raya-map-node]")
                          ?.getAttribute("data-raya-map-node")"""
                    )
                    assert keyboard_first_visible == "course-root"

                    root_url_before_collapse = page.url
                    page.keyboard.press("ArrowLeft")
                    page.wait_for_timeout(250)
                    keyboard_root_collapse = page.evaluate(
                        """() => ({
                          activeNode: document.activeElement
                            ?.closest("[data-raya-map-node]")
                            ?.getAttribute("data-raya-map-node"),
                          rootExpanded: document
                            .querySelector('[data-raya-map-node="course-root"] [data-raya-map-node-toggle]')
                            ?.getAttribute('aria-expanded'),
                          url: window.location.href,
                        })"""
                    )
                    assert keyboard_root_collapse == {
                        "activeNode": "course-root",
                        "rootExpanded": "false",
                        "url": root_url_before_collapse,
                    }

                    root_url_before_noop = page.url
                    page.keyboard.press("ArrowLeft")
                    page.wait_for_timeout(250)
                    keyboard_root_noop = page.evaluate(
                        """() => ({
                          activeNode: document.activeElement
                            ?.closest("[data-raya-map-node]")
                            ?.getAttribute("data-raya-map-node"),
                          rootExpanded: document
                            .querySelector('[data-raya-map-node="course-root"] [data-raya-map-node-toggle]')
                            ?.getAttribute('aria-expanded'),
                          url: window.location.href,
                        })"""
                    )
                    assert keyboard_root_noop == {
                        "activeNode": "course-root",
                        "rootExpanded": "false",
                        "url": root_url_before_noop,
                    }

                    page.keyboard.press("ArrowRight")
                    page.keyboard.press("End")
                    keyboard_last_visible = page.evaluate(
                        """() => document.activeElement
                          ?.closest("[data-raya-map-node]")
                          ?.getAttribute("data-raya-map-node")"""
                    )
                    assert keyboard_last_visible == "map-branch-b"

                    page.click('[data-raya-course-map-action="expand-all"]')
                    scan_exited = page.evaluate(
                        """() => ({
                          scan: document
                            .querySelector('#raya-course-map')
                            ?.dataset
                            ?.rayaCourseMapScan || '',
                          scanPressed: document
                            .querySelector('[data-raya-course-map-action="scan"]')
                            ?.getAttribute('aria-pressed'),
                          branchAExpanded: document
                            .querySelector('[data-raya-map-node="map-branch-a"] [data-raya-map-node-toggle]')
                            ?.getAttribute('aria-expanded'),
                          branchBExpanded: document
                            .querySelector('[data-raya-map-node="map-branch-b"] [data-raya-map-node-toggle]')
                            ?.getAttribute('aria-expanded'),
                        })"""
                    )
                    assert scan_exited == {
                        "scan": "",
                        "scanPressed": "false",
                        "branchAExpanded": "true",
                        "branchBExpanded": "true",
                    }

                    page.click('[data-raya-course-map-action="scan"]')
                    page.click('[data-raya-course-map-action="current"]')
                    scan_exited_by_current = page.evaluate(
                        """() => ({
                          scan: document
                            .querySelector('#raya-course-map')
                            ?.dataset
                            ?.rayaCourseMapScan || '',
                          scanPressed: document
                            .querySelector('[data-raya-course-map-action="scan"]')
                            ?.getAttribute('aria-pressed'),
                          currentVisible: !!document
                            .querySelector('#raya-course-map a[aria-current="page"]')
                            ?.checkVisibility(),
                        })"""
                    )
                    assert scan_exited_by_current == {
                        "scan": "",
                        "scanPressed": "false",
                        "currentVisible": True,
                    }

                    page.click('[data-raya-course-map-action="scan"]')
                    page.click('[data-raya-course-map-action="less"]')
                    scan_exited_by_less = page.evaluate(
                        """() => ({
                          scan: document
                            .querySelector('#raya-course-map')
                            ?.dataset
                            ?.rayaCourseMapScan || '',
                          scanPressed: document
                            .querySelector('[data-raya-course-map-action="scan"]')
                            ?.getAttribute('aria-pressed'),
                          currentVisible: !!document
                            .querySelector('#raya-course-map a[aria-current="page"]')
                            ?.checkVisibility(),
                        })"""
                    )
                    assert scan_exited_by_less == {
                        "scan": "",
                        "scanPressed": "false",
                        "currentVisible": True,
                    }

                    page.click('[data-raya-course-map-action="scan"]')
                    page.fill("#raya-course-map-filter", "topic")
                    scan_exited_by_filter = page.evaluate(
                        """() => ({
                          scan: document
                            .querySelector('#raya-course-map')
                            ?.dataset
                            ?.rayaCourseMapScan || '',
                          scanPressed: document
                            .querySelector('[data-raya-course-map-action="scan"]')
                            ?.getAttribute('aria-pressed'),
                          filterValue: document.querySelector('#raya-course-map-filter')?.value,
                        })"""
                    )
                    assert scan_exited_by_filter == {
                        "scan": "",
                        "scanPressed": "false",
                        "filterValue": "topic",
                    }

                    page.click('[data-raya-course-map-action="scan"]')
                    page.click(".raya-course-map-toggle")
                    page.wait_for_function(
                        """() => document.documentElement.dataset.rayaCourseMap === 'collapsed'"""
                    )
                    scan_exited_by_collapse = page.evaluate(
                        """() => ({
                          scan: document
                            .querySelector('#raya-course-map')
                            ?.dataset
                            ?.rayaCourseMapScan || '',
                          scanPressed: document
                            .querySelector('[data-raya-course-map-action="scan"]')
                            ?.getAttribute('aria-pressed'),
                        })"""
                    )
                    assert scan_exited_by_collapse == {
                        "scan": "",
                        "scanPressed": "false",
                    }
                    page.click(".raya-course-map-toggle")
                    page.wait_for_function(
                        """() => document.documentElement.dataset.rayaCourseMap === 'expanded'"""
                    )

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
                    page.wait_for_function(
                        """() => Array.from(document.querySelectorAll('#raya-course-map a'))
                          .filter((link) => link.checkVisibility()).length === 4"""
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
                        "visibleLinks": 4,
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
                          currentChipVisible: !!document
                            .querySelector('[data-raya-course-map-current-chip]')
                            ?.checkVisibility(),
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
                    assert initial["currentChipVisible"] is False
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
                    page.locator("#raya-course-map-list a").first.focus()
                    expanded_preview_state = page.evaluate(
                        """() => {
                          const preview = document
                            .querySelector('[data-raya-course-map-compact-preview]');
                          window.dispatchEvent(new Event('resize'));
                          return {
                            hidden: preview?.hidden,
                            text: preview?.textContent.trim(),
                          };
                        }"""
                    )
                    assert expanded_preview_state == {"hidden": True, "text": ""}

                    page.click(".raya-course-map-toggle")
                    page.wait_for_function(
                        """() => document
                          .querySelector('#raya-course-map')
                          ?.getBoundingClientRect().width < 130"""
                    )
                    page.wait_for_function(
                        """() => !document
                          .querySelector('#raya-course-map')
                          ?.dataset
                          ?.rayaCourseMapTransition"""
                    )
                    collapsed_without_focus = page.evaluate(
                        """() => {
                          const preview = document
                            .querySelector('[data-raya-course-map-compact-preview]');
                          window.dispatchEvent(new Event('resize'));
                          return {
                            hidden: preview?.hidden,
                            text: preview?.textContent.trim(),
                          };
                        }"""
                    )
                    assert collapsed_without_focus == {"hidden": True, "text": ""}
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
                          currentChip: (() => {
                            const chip = document
                              .querySelector('[data-raya-course-map-current-chip]');
                            const chipBox = chip?.getBoundingClientRect();
                            const mapBox = document
                              .querySelector('#raya-course-map')
                              ?.getBoundingClientRect();
                            return {
                              visible: !!chip?.checkVisibility(),
                              text: chip?.textContent.trim(),
                              label: chip?.getAttribute('aria-label'),
                              width: chipBox?.width,
                              mapWidth: mapBox?.width,
                              scrollWidth: chip?.scrollWidth,
                              clientWidth: chip?.clientWidth,
                            };
                          })(),
                          buttonVisualLabel: getComputedStyle(
                            document.querySelector('#raya-course-map .raya-course-map-toggle'),
                            '::after'
                          ).content,
                          buttonVisualWritingMode: getComputedStyle(
                            document.querySelector('#raya-course-map .raya-course-map-toggle'),
                            '::after'
                          ).writingMode,
                          wrappedLinkTexts: Array.from(document.querySelectorAll('#raya-course-map a'))
                            .filter((link) => link.checkVisibility())
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
                    assert 64 <= collapsed["mapWidth"] <= 112
                    assert collapsed["articleWidth"] > 760
                    assert collapsed["texts"][1] in {"Expand map", "Map"}
                    assert collapsed["buttonVisualLabel"] == '"Map"'
                    assert collapsed["buttonVisualWritingMode"] == "horizontal-tb"
                    assert collapsed["currentChip"]["visible"] is True
                    assert collapsed["currentChip"]["text"] == "Projection Residuals"
                    assert (
                        collapsed["currentChip"]["label"]
                        == "Current page: Projection Residuals"
                    )
                    assert collapsed["currentChip"]["width"] <= collapsed["mapWidth"]
                    assert (
                        collapsed["currentChip"]["scrollWidth"]
                        <= collapsed["currentChip"]["clientWidth"] + 1
                    )
                    assert collapsed["wrappedLinkTexts"] == []
                    assert collapsed["firstLinkWidth"] <= collapsed["mapWidth"]
                    assert collapsed["firstLinkPointerEvents"] == "auto"
                    assert collapsed["linkTabIndexes"]
                    assert set(collapsed["linkTabIndexes"]) == {None}
                    first_map_link = page.locator("#raya-course-map-list a").first
                    page.evaluate(
                        """() => {
                          const link = document.querySelector('#raya-course-map-list a');
                          const label = Array.from({ length: 180 }, (_, index) => `Viewport label ${index + 1}`)
                            .join(' ');
                          link.setAttribute('data-raya-map-label', label);
                        }"""
                    )
                    first_map_link.focus()
                    tall_preview = page.evaluate(
                        """() => {
                          const preview = document
                            .querySelector('[data-raya-course-map-compact-preview]');
                          const box = preview?.getBoundingClientRect();
                          const style = preview ? getComputedStyle(preview) : null;
                          return {
                            bottom: box?.bottom,
                            height: box?.height,
                            overflowY: style?.overflowY,
                            maxHeight: style?.maxHeight,
                            viewportHeight: window.innerHeight,
                          };
                        }"""
                    )
                    assert tall_preview["bottom"] <= tall_preview["viewportHeight"]
                    assert tall_preview["height"] <= tall_preview["viewportHeight"] - 16
                    assert tall_preview["overflowY"] == "auto"
                    assert tall_preview["maxHeight"] != "none"
                    page.evaluate(
                        """() => {
                          const link = document.querySelector('#raya-course-map-list a');
                          link.setAttribute('data-raya-map-label', 'Raya Lucaria Render Fixture');
                          link.blur();
                        }"""
                    )
                    first_map_link.focus()
                    page.wait_for_function(
                        """() => {
                          const preview = document
                            .querySelector('[data-raya-course-map-compact-preview]');
                          return preview
                            && !preview.hidden
                            && preview.textContent.includes('Raya Lucaria Render Fixture');
                        }"""
                    )
                    focused_label = page.evaluate(
                        """() => {
                          const row = document
                            .querySelector('#raya-course-map-list a')
                            ?.closest('.raya-course-map-node-row');
                          const map = document.querySelector('#raya-course-map');
                          const link = document.querySelector('#raya-course-map-list a');
                          const preview = document
                            .querySelector('[data-raya-course-map-compact-preview]');
                          const previewBox = preview?.getBoundingClientRect();
                          const mapBox = map?.getBoundingClientRect();
                          return {
                            mapWidth: map?.getBoundingClientRect().width,
                            linkTitle: link?.getAttribute('title'),
                            rowLabel: row?.getAttribute('data-raya-map-label'),
                            previewText: preview?.textContent.trim(),
                            previewHidden: preview?.hidden,
                            previewTop: previewBox?.top,
                            previewBottom: previewBox?.bottom,
                            previewLeft: previewBox?.left,
                            previewRight: previewBox?.right,
                            mapRight: mapBox?.right,
                            viewportWidth: window.innerWidth,
                            viewportHeight: window.innerHeight,
                            mapScrollWidth: map?.scrollWidth,
                            mapClientWidth: map?.clientWidth,
                          };
                        }"""
                    )
                    assert focused_label["mapWidth"] == collapsed["mapWidth"]
                    assert focused_label["linkTitle"] is None
                    assert focused_label["rowLabel"] == "Raya Lucaria Render Fixture"
                    assert focused_label["previewHidden"] is False
                    assert focused_label["previewText"] == "Raya Lucaria Render Fixture"
                    assert focused_label["previewTop"] >= 0
                    assert (
                        focused_label["previewBottom"]
                        <= focused_label["viewportHeight"]
                    )
                    assert focused_label["previewLeft"] > focused_label["mapRight"]
                    assert focused_label["previewRight"] <= focused_label["viewportWidth"]
                    assert (
                        focused_label["mapScrollWidth"]
                        <= focused_label["mapClientWidth"] + 1
                    )
                    mixed_trigger_state = page.evaluate(
                        """() => {
                          const links = Array.from(document.querySelectorAll('#raya-course-map-list a'));
                          const preview = document
                            .querySelector('[data-raya-course-map-compact-preview]');
                          links[0].focus();
                          links[1].dispatchEvent(new PointerEvent('pointerenter', { bubbles: true }));
                          links[1].dispatchEvent(new PointerEvent('pointerleave', { bubbles: true }));
                          return {
                            hidden: preview?.hidden,
                            text: preview?.textContent.trim(),
                            activeElementText: document.activeElement?.textContent.trim(),
                          };
                        }"""
                    )
                    assert mixed_trigger_state["activeElementText"] == "Raya Lucaria Render Fixture"
                    assert mixed_trigger_state["hidden"] is False
                    assert (
                        mixed_trigger_state["text"]
                        == mixed_trigger_state["activeElementText"]
                    )

                    page.click(".raya-course-map-toggle")
                    page.wait_for_function(
                        """() => document
                          .querySelector('#raya-course-map')
                          ?.getBoundingClientRect().width >= 220"""
                    )
                    page.wait_for_function(
                        """() => !document
                          .querySelector('#raya-course-map')
                          ?.dataset
                          ?.rayaCourseMapTransition"""
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
                          currentChipVisible: !!document
                            .querySelector('[data-raya-course-map-current-chip]')
                            ?.checkVisibility(),
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
                    assert expanded["currentChipVisible"] is False
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
                            contextChipVisible: !!document
                              .querySelector('[data-raya-learning-rail-context-chip]')
                              ?.checkVisibility(),
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
                    assert 220 <= initial["railWidth"] <= 330
                    assert initial["contextChipVisible"] is False
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
                          const chip = document
                            .querySelector('[data-raya-learning-rail-context-chip]');
                          const chipBox = chip?.getBoundingClientRect();
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
                            contextChip: {
                              visible: !!chip?.checkVisibility(),
                              text: chip?.textContent.trim(),
                              label: chip?.getAttribute('aria-label'),
                              width: chipBox?.width,
                              scrollWidth: chip?.scrollWidth,
                              clientWidth: chip?.clientWidth,
                            },
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
                    assert collapsed["contextChip"]["visible"] is True
                    assert "Projection Residuals" in collapsed["contextChip"]["text"]
                    assert "ready" in collapsed["contextChip"]["text"]
                    assert (
                        collapsed["contextChip"]["label"]
                        == "Learning context for Projection Residuals, status ready"
                    )
                    assert collapsed["contextChip"]["width"] <= collapsed["railWidth"]
                    assert (
                        collapsed["contextChip"]["scrollWidth"]
                        <= collapsed["contextChip"]["clientWidth"] + 1
                    )
                    assert collapsed["wrappedExpandText"] is False

                    page.click("[data-raya-learning-rail-expand]")
                    page.wait_for_function(
                        """() => document
                          .querySelector('#raya-learning-rail')
                          ?.getBoundingClientRect()
                          ?.width >= 220"""
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
                            contextChipVisible: !!document
                              .querySelector('[data-raya-learning-rail-context-chip]')
                              ?.checkVisibility(),
                          };
                        }"""
                    )
                    assert expanded["rootState"] == "expanded"
                    assert expanded["railState"] == "expanded"
                    assert expanded["bodyHidden"] == "false"
                    assert expanded["bodyInert"] in {False, None}
                    assert expanded["railWidth"] >= 220
                    assert expanded["contextChipVisible"] is False

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
                                expandVisible: !!expand?.checkVisibility(),
                                collapseVisible: !!collapse?.checkVisibility(),
                              };
                            }"""
                        )
                    assert resized_mobile["rootState"] == "expanded"
                    assert resized_mobile["bodyHidden"] == "false"
                    assert resized_mobile["bodyInert"] is False
                    assert resized_mobile["expandVisible"] is False
                    assert resized_mobile["collapseVisible"] is False

                    page.set_viewport_size({"width": 1280, "height": 900})
                    page.wait_for_function(
                        """() => document
                          .querySelector('#raya-learning-rail')
                          ?.getBoundingClientRect()
                          ?.width >= 220"""
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
                          const railBox = rail?.getBoundingClientRect();
                          return {
                            expandVisible: !!expand?.checkVisibility(),
                            collapseVisible: !!collapse?.checkVisibility(),
                            railWidth: railBox?.width,
                            railHeight: railBox?.height,
                          };
                        }"""
                    )
                    assert mobile_state["expandVisible"] is False
                    assert mobile_state["collapseVisible"] is False
                    assert mobile_state["railWidth"] > 300
                    assert mobile_state["railHeight"] > 100
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
                                summaryDisplay: getComputedStyle(details?.querySelector('summary')).display,
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
                        assert "Content" in preview_state["normalizedText"]
                        assert "From this page" in preview_state["normalizedText"]
                        assert (
                            "This page links to the target page through an explicit content link."
                            in preview_state["normalizedText"]
                        )
                        assert "list-item" in preview_state["summaryDisplay"]
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
                page_errors: list[str] = []
                page.on("pageerror", lambda error: page_errors.append(str(error)))
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

                    page.click('[data-raya-course-map-action="scan"]')
                    scan = page.evaluate(
                        """() => ({
                          scan: document
                            .querySelector('#raya-course-map')
                            ?.dataset
                            ?.rayaCourseMapScan,
                          scanPressed: document
                            .querySelector('[data-raya-course-map-action="scan"]')
                            ?.getAttribute('aria-pressed'),
                          currentVisible: !!document
                            .querySelector('#raya-course-map a[aria-current="page"]')
                            ?.checkVisibility(),
                        })"""
                    )
                    assert scan == {
                        "scan": "active",
                        "scanPressed": "true",
                        "currentVisible": True,
                    }
                    assert page_errors == []

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
                            shellColumnGap: parseFloat(getComputedStyle(shell).columnGap),
                            articlePaddingInline: parseFloat(articleStyle.paddingLeft),
                            articleBorderLeftWidth: parseFloat(articleStyle.borderLeftWidth),
                            articleBorderRadius: parseFloat(articleStyle.borderTopLeftRadius),
                            mapWidth: courseMap.getBoundingClientRect().width,
                            railWidth: rail.getBoundingClientRect().width,
                          };
                        }"""
                    )
                    page.set_viewport_size({"width": 1280, "height": 900})
                    page.wait_for_function(
                        """() => window.innerWidth === 1280"""
                    )
                    threshold = page.evaluate(
                        """() => {
                          const article = document.querySelector('article.raya-main-article');
                          const shell = document.querySelector('.raya-learning-shell');
                          const articleStyle = getComputedStyle(article);
                          return {
                            shellColumnGap: parseFloat(getComputedStyle(shell).columnGap),
                            articlePaddingInline: parseFloat(articleStyle.paddingLeft),
                            articleBorderLeftWidth: parseFloat(articleStyle.borderLeftWidth),
                            articleBorderRadius: parseFloat(articleStyle.borderTopLeftRadius),
                            articleRight: article.getBoundingClientRect().right,
                            viewportWidth: window.innerWidth,
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
    assert hierarchy["shellColumnGap"] >= 24
    assert hierarchy["articlePaddingInline"] >= 28
    assert hierarchy["articleBorderLeftWidth"] >= 1
    assert 4 <= hierarchy["articleBorderRadius"] <= 8
    assert threshold["shellColumnGap"] >= 24
    assert threshold["articlePaddingInline"] >= 28
    assert threshold["articleBorderLeftWidth"] >= 1
    assert 4 <= threshold["articleBorderRadius"] <= 8
    assert threshold["articleRight"] <= threshold["viewportWidth"]
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
                            shellColumnGap: parseFloat(getComputedStyle(shell).columnGap),
                            articlePaddingInline: parseFloat(articleStyle.paddingLeft),
                            articleBorderLeftWidth: parseFloat(articleStyle.borderLeftWidth),
                            articleBorderRadius: parseFloat(articleStyle.borderTopLeftRadius),
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
                    icons = page.evaluate(
                        """() => Object.fromEntries(
                          Array.from(
                            document.querySelectorAll(
                              '.raya-top-command-bar .raya-command'
                            )
                          ).map((node) => [
                            Array.from(node.classList)
                              .find((name) => name.startsWith('raya-command-')),
                            (() => {
                              const icon = node.querySelector('.raya-command-icon');
                              const labelNode = node.querySelector('.raya-command-label');
                              const shape = icon?.querySelector('path, circle');
                              return {
                                iconCount: node.querySelectorAll('.raya-command-icon').length,
                                iconBeforeLabel: !!icon && !!labelNode
                                  && !!(
                                    icon.compareDocumentPosition(labelNode)
                                    & Node.DOCUMENT_POSITION_FOLLOWING
                                  ),
                                tagName: icon?.tagName,
                                icon: icon?.getAttribute('data-raya-command-icon'),
                                ariaHidden: icon?.getAttribute('aria-hidden'),
                                focusable: icon?.getAttribute('focusable'),
                                viewBox: icon?.getAttribute('viewBox'),
                                label: labelNode?.textContent?.trim(),
                                before: getComputedStyle(node, '::before').content,
                                shapeFill: shape ? getComputedStyle(shape).fill : null,
                                shapeStroke: shape ? getComputedStyle(shape).stroke : null,
                              };
                            })()
                          ])
                        )"""
                    )
                    page.click(".raya-course-map-toggle")
                    page.click("[data-raya-learning-rail-collapse]")
                    page.wait_for_function(
                        """() => document.documentElement.dataset.rayaCourseMap === 'collapsed'
                          && document.documentElement.dataset.rayaLearningRail === 'collapsed'"""
                    )
                    page.wait_for_function(
                        """() => document.querySelector('nav.raya-course-map')
                          ?.getBoundingClientRect().width <= 112
                          && document.querySelector('aside.raya-learning-rail')
                          ?.getBoundingClientRect().width <= 112"""
                    )
                    page.wait_for_function(
                        """() => !document.querySelector('nav.raya-course-map')
                          ?.hasAttribute('data-raya-course-map-transition')
                          && !document.querySelector('aside.raya-learning-rail')
                          ?.hasAttribute('data-raya-learning-rail-transition')"""
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
    assert chrome["shellColumnGap"] >= 24
    assert chrome["articlePaddingInline"] >= 28
    assert chrome["articleBorderLeftWidth"] >= 1
    assert 4 <= chrome["articleBorderRadius"] <= 8
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
    expected_icons = {
        "raya-command-map": ("map", "Course map"),
        "raya-command-focus": ("focus", "Focus reading"),
        "raya-command-search": ("search", "Search"),
        "raya-command-graph": ("graph", "Graph"),
        "raya-command-practice": ("practice", "Practice"),
        "raya-command-tasks": ("tasks", "Tasks"),
        "raya-command-schedule": ("schedule", "Schedule"),
        "raya-command-size": ("text-size", "Text size"),
        "raya-command-font": ("font", "OpenDyslexic"),
    }
    for command_class, (icon_name, label) in expected_icons.items():
        icon = icons[command_class]
        assert icon["tagName"] == "svg"
        assert icon["iconCount"] == 1
        assert icon["iconBeforeLabel"] is True
        assert icon["icon"] == icon_name
        assert icon["ariaHidden"] == "true"
        assert icon["focusable"] == "false"
        assert icon["viewBox"] == "0 0 24 24"
        assert icon["label"] == label
        assert icon["before"] == "none"
        if icon_name not in {"text-size", "font"}:
            assert icon["shapeFill"] == "none"
            assert icon["shapeStroke"] != "none"
    assert collapsed["mapWidth"] <= 112
    assert collapsed["railWidth"] <= 112
    assert collapsed["mapLabel"] == '"Map"'
    assert collapsed["railLabel"] == '"Context"'
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


def test_render_fixture_desktop_course_map_labels_stay_scannable(
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
                    map_labels = page.evaluate(
                        """() => {
                          const lineCount = (node) => {
                            const box = node.getBoundingClientRect();
                            const style = getComputedStyle(node);
                            return box.height / parseFloat(style.lineHeight);
                          };
                          const current = document
                            .querySelector('#raya-course-map a[aria-current="page"]');
                          const workspaces = Array.from(
                            document.querySelectorAll('.raya-course-map-workspace-link')
                          );
                          return {
                            currentText: current?.textContent?.trim(),
                            currentLines: lineCount(current),
                            currentOverflowWrap: getComputedStyle(current).overflowWrap,
                            workspaceLines: workspaces.map(lineCount),
                            workspaceOverflowWrap: workspaces.map(
                              (node) => getComputedStyle(node).overflowWrap
                            ),
                          };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert "Projection Residuals" in map_labels["currentText"]
    assert map_labels["currentLines"] <= 3.5
    assert map_labels["currentOverflowWrap"] != "anywhere"
    assert max(map_labels["workspaceLines"]) <= 2
    assert all(
        overflow_wrap != "anywhere"
        for overflow_wrap in map_labels["workspaceOverflowWrap"]
    )


def test_render_fixture_course_map_keeps_emergency_breaks_for_long_labels(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    reader_page = course / "course" / "4_reader_ux" / "0_index.md"
    reader_page.write_text(
        reader_page.read_text(encoding="utf-8").replace(
            "title: Projection Residuals",
            "title: ProjectionResidualsWithAnUnbrokenAuthorIdentifierThatMustWrapSafely",
        ),
        encoding="utf-8",
    )
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
                    current_link = page.locator(
                        '#raya-course-map a[aria-current="page"]'
                    )
                    current_state = current_link.evaluate(
                        """(node) => {
                          const nodeBox = node.getBoundingClientRect();
                          const mapBox = document
                            .querySelector('#raya-course-map')
                            .getBoundingClientRect();
                          const style = getComputedStyle(node);
                          return {
                            text: node.textContent.trim(),
                            linkRight: nodeBox.right,
                            mapRight: mapBox.right,
                            overflowWrap: style.overflowWrap,
                          };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert "ProjectionResidualsWithAnUnbrokenAuthorIdentifier" in current_state["text"]
    assert current_state["linkRight"] <= current_state["mapRight"]
    assert current_state["overflowWrap"] == "break-word"


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
                    first_viewport = page.evaluate(
                        """() => {
                          const viewportBottom = window.innerHeight;
                          return Array.from(
                            document.querySelectorAll('article.raya-main-article *')
                          )
                            .filter((node) => {
                              const box = node.getBoundingClientRect();
                              const style = getComputedStyle(node);
                              return box.width > 0
                                && box.height > 0
                                && box.top < viewportBottom
                                && box.bottom > 0
                                && style.visibility !== 'hidden'
                                && style.display !== 'none';
                            })
                            .map((node) => node.textContent || '')
                            .join('\\n');
                        }"""
                    )
                    assert "Projection Residuals" in first_viewport
                    assert (
                        "What remains after projecting a vector onto a line?"
                        in first_viewport
                    )
                    assert "Try this first" in first_viewport
                    assert (
                        "This remains reader-facing fixture material"
                        not in first_viewport
                    )
                    assert "render-debug" not in first_viewport.lower()
                    assert "not canonical" not in first_viewport.lower()
                    brief_graph_link = page.locator(
                        ".raya-page-brief-connections a"
                    )
                    assert (
                        brief_graph_link.get_attribute("href")
                        == "../_raya/graph/index.html?page=reader-ux"
                    )
                    assert "graph" in brief_graph_link.inner_text().lower()
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


def test_render_fixture_reader_command_bar_is_compact_on_desktop(
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
                page = browser.new_page(viewport={"width": 1600, "height": 950})
                try:
                    page.goto(
                        f"{handle.base_url}/reader-ux/index.html",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(page)
                    metrics = page.evaluate(
                        """() => {
                          const topBar = document.querySelector('.raya-top-command-bar');
                          const article = document.querySelector('#raya-article');
                          const searchInput = document.querySelector('.raya-command-search-input');
                          const groups = Array.from(
                            document.querySelectorAll(
                              '.raya-top-command-bar:not(.raya-discovery-command-bar) .raya-command-group'
                            )
                          );
                          const visibleGroups = groups.filter((group) => {
                            const box = group.getBoundingClientRect();
                            const style = getComputedStyle(group);
                            return box.width > 0
                              && box.height > 0
                              && style.display !== 'none';
                          });
                          const visibleGroupNames = visibleGroups.map(
                            (group) => group.getAttribute('data-raya-command-group')
                          );
                          const topBox = topBar.getBoundingClientRect();
                          const articleBox = article.getBoundingClientRect();
                          return {
                            topBarHeight: topBox.height,
                            articleTop: articleBox.top,
                            searchVisible: !!searchInput
                              && searchInput.getClientRects().length > 0,
                            searchWidth: searchInput?.getBoundingClientRect().width ?? 0,
                            visibleGroupNames,
                          };
                        }"""
                    )
                    assert metrics["topBarHeight"] <= 112
                    assert metrics["articleTop"] <= 190
                    assert {
                        "discovery",
                        "layout",
                        "comfort",
                    }.issubset(set(metrics["visibleGroupNames"]))
                    assert metrics["searchVisible"] is True
                    assert metrics["searchWidth"] >= 120
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_top_context_command_toggles_right_rail_only(
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
                          mapState: document.documentElement.dataset.rayaCourseMap,
                          railState: document.documentElement.dataset.rayaLearningRail,
                          contextExpanded: document
                            .querySelector('[data-raya-learning-rail-toggle]')
                            ?.getAttribute('aria-expanded'),
                          collapseExpanded: document
                            .querySelector('[data-raya-learning-rail-collapse]')
                            ?.getAttribute('aria-expanded'),
                          expandExpanded: document
                            .querySelector('[data-raya-learning-rail-expand]')
                            ?.getAttribute('aria-expanded'),
                          commandVisible: document
                            .querySelector('[data-raya-learning-rail-toggle]')
                            ?.getClientRects().length > 0,
                          articleWidth: document
                            .querySelector('#raya-article')
                            ?.getBoundingClientRect().width,
                          railWidth: document
                            .querySelector('#raya-learning-rail')
                            ?.getBoundingClientRect().width,
                        })"""
                    )
                    assert initial["commandVisible"] is True
                    assert initial["mapState"] == "expanded"
                    assert initial["railState"] == "expanded"
                    assert initial["contextExpanded"] == "true"
                    assert initial["collapseExpanded"] == "true"
                    assert initial["expandExpanded"] == "true"
                    assert initial["articleWidth"] > 620
                    assert initial["railWidth"] >= 220

                    page.click("[data-raya-learning-rail-toggle]")
                    page.wait_for_function(
                        "() => document.documentElement.dataset.rayaLearningRail === 'collapsed'"
                    )
                    page.wait_for_function(
                        """(minimumWidth) => document
                          .querySelector('#raya-article')
                          ?.getBoundingClientRect().width > minimumWidth""",
                        arg=initial["articleWidth"] + 80,
                    )
                    collapsed = page.evaluate(
                        """() => ({
                          mapState: document.documentElement.dataset.rayaCourseMap,
                          railState: document.documentElement.dataset.rayaLearningRail,
                          contextExpanded: document
                            .querySelector('[data-raya-learning-rail-toggle]')
                            ?.getAttribute('aria-expanded'),
                          contextLabel: document
                            .querySelector('[data-raya-learning-rail-toggle]')
                            ?.getAttribute('aria-label'),
                          collapseExpanded: document
                            .querySelector('[data-raya-learning-rail-collapse]')
                            ?.getAttribute('aria-expanded'),
                          expandExpanded: document
                            .querySelector('[data-raya-learning-rail-expand]')
                            ?.getAttribute('aria-expanded'),
                          articleWidth: document
                            .querySelector('#raya-article')
                            ?.getBoundingClientRect().width,
                          railWidth: document
                            .querySelector('#raya-learning-rail')
                            ?.getBoundingClientRect().width,
                          railBodyHidden: document
                            .querySelector('#raya-learning-rail-body')
                            ?.getAttribute('aria-hidden'),
                          railBodyInert: document
                            .querySelector('#raya-learning-rail-body')?.inert,
                        })"""
                    )
                    assert collapsed["mapState"] == "expanded"
                    assert collapsed["railState"] == "collapsed"
                    assert collapsed["contextExpanded"] == "false"
                    assert collapsed["contextLabel"] == "Show learning context"
                    assert collapsed["collapseExpanded"] == "false"
                    assert collapsed["expandExpanded"] == "false"
                    assert collapsed["articleWidth"] > initial["articleWidth"] + 80
                    assert collapsed["railWidth"] <= 112
                    assert collapsed["railBodyHidden"] == "true"
                    assert collapsed["railBodyInert"] is True
                    _assert_no_horizontal_overflow(page)

                    page.click("[data-raya-learning-rail-toggle]")
                    page.wait_for_function(
                        "() => document.documentElement.dataset.rayaLearningRail === 'expanded'"
                    )
                    restored = page.evaluate(
                        """() => ({
                          contextExpanded: document
                            .querySelector('[data-raya-learning-rail-toggle]')
                            ?.getAttribute('aria-expanded'),
                          contextLabel: document
                            .querySelector('[data-raya-learning-rail-toggle]')
                            ?.getAttribute('aria-label'),
                          railBodyHidden: document
                            .querySelector('#raya-learning-rail-body')
                            ?.getAttribute('aria-hidden'),
                        })"""
                    )
                    assert restored == {
                        "contextExpanded": "true",
                        "contextLabel": "Hide learning context",
                        "railBodyHidden": "false",
                    }
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_collapsed_reader_rails_use_compact_horizontal_tabs(
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
                          articleWidth: document.querySelector('#raya-article')
                            ?.getBoundingClientRect().width,
                          mapWidth: document.querySelector('#raya-course-map')
                            ?.getBoundingClientRect().width,
                          railWidth: document.querySelector('#raya-learning-rail')
                            ?.getBoundingClientRect().width,
                        })"""
                    )
                    assert initial["articleWidth"] > 620
                    assert initial["mapWidth"] >= 210
                    assert initial["railWidth"] >= 220

                    page.click("#raya-course-map .raya-course-map-toggle")
                    map_transitioning = page.evaluate(
                        """async () => {
                          await new Promise((resolve) => window.requestAnimationFrame(resolve));
                          const map = document.querySelector('#raya-course-map');
                          const mapList = document.querySelector('#raya-course-map-list');
                          return {
                            transition: map?.getAttribute('data-raya-course-map-transition'),
                            listDisplay: mapList ? getComputedStyle(mapList).display : null,
                            listVisibility: mapList ? getComputedStyle(mapList).visibility : null,
                          };
                        }"""
                    )
                    assert map_transitioning == {
                        "transition": "collapsing",
                        "listDisplay": "block",
                        "listVisibility": "hidden",
                    }
                    page.wait_for_function(
                        """() => document.documentElement.dataset.rayaCourseMap === 'collapsed'"""
                    )
                    page.wait_for_function(
                        """(minimumWidth) => document.querySelector('#raya-article')
                          ?.getBoundingClientRect().width > minimumWidth""",
                        arg=initial["articleWidth"] + 80,
                    )
                    map_collapsed = page.evaluate(
                        """() => {
                          const map = document.querySelector('#raya-course-map');
                          const mapButton = document
                            .querySelector('#raya-course-map .raya-course-map-toggle');
                          const mapLabel = getComputedStyle(mapButton, '::after');
                          const firstMapLink = document.querySelector('#raya-course-map a');
                          return {
                            articleWidth: document.querySelector('#raya-article')
                              ?.getBoundingClientRect().width,
                            mapWidth: map?.getBoundingClientRect().width,
                            mapButtonExpanded: mapButton?.getAttribute('aria-expanded'),
                            mapButtonAriaLabel: mapButton?.getAttribute('aria-label'),
                            mapVisualLabel: mapLabel.content,
                            mapVisualWritingMode: mapLabel.writingMode,
                            mapVisualTextOrientation: mapLabel.textOrientation,
                            firstMapLinkTabIndex: firstMapLink?.getAttribute('tabindex'),
                            firstMapLinkPointerEvents: firstMapLink
                              ? getComputedStyle(firstMapLink).pointerEvents
                              : null,
                          };
                        }"""
                    )
                    assert map_collapsed["articleWidth"] > initial["articleWidth"] + 80
                    assert 64 <= map_collapsed["mapWidth"] <= 112
                    assert map_collapsed["mapButtonExpanded"] == "false"
                    assert map_collapsed["mapButtonAriaLabel"] == "Expand course map"
                    assert map_collapsed["mapVisualLabel"] == '"Map"'
                    assert map_collapsed["mapVisualWritingMode"] == "horizontal-tb"
                    assert map_collapsed["firstMapLinkTabIndex"] is None
                    assert map_collapsed["firstMapLinkPointerEvents"] == "auto"

                    page.click("[data-raya-learning-rail-toggle]")
                    rail_transitioning = page.evaluate(
                        """async () => {
                          await new Promise((resolve) => window.requestAnimationFrame(resolve));
                          const rail = document.querySelector('#raya-learning-rail');
                          const body = document.querySelector('#raya-learning-rail-body');
                          return {
                            transition: rail?.getAttribute('data-raya-learning-rail-transition'),
                            bodyDisplay: body ? getComputedStyle(body).display : null,
                            bodyVisibility: body ? getComputedStyle(body).visibility : null,
                            bodyHidden: body?.getAttribute('aria-hidden'),
                            bodyInert: body?.inert,
                          };
                        }"""
                    )
                    assert rail_transitioning == {
                        "transition": "collapsing",
                        "bodyDisplay": "block",
                        "bodyVisibility": "hidden",
                        "bodyHidden": "true",
                        "bodyInert": True,
                    }
                    page.wait_for_function(
                        """() => document.documentElement.dataset.rayaLearningRail === 'collapsed'"""
                    )
                    page.wait_for_function(
                        """(minimumWidth) => document.querySelector('#raya-article')
                          ?.getBoundingClientRect().width > minimumWidth""",
                        arg=map_collapsed["articleWidth"] + 40,
                    )
                    both_collapsed = page.evaluate(
                        """() => {
                          const expand = document
                            .querySelector('[data-raya-learning-rail-expand]');
                          const expandLabel = getComputedStyle(expand, '::after');
                          const body = document.querySelector('#raya-learning-rail-body');
                          return {
                            mapState: document.documentElement.dataset.rayaCourseMap,
                            railState: document.documentElement.dataset.rayaLearningRail,
                            articleWidth: document.querySelector('#raya-article')
                              ?.getBoundingClientRect().width,
                            railWidth: document.querySelector('#raya-learning-rail')
                              ?.getBoundingClientRect().width,
                            contextButtonExpanded: document
                              .querySelector('[data-raya-learning-rail-toggle]')
                              ?.getAttribute('aria-expanded'),
                            railExpandExpanded: expand?.getAttribute('aria-expanded'),
                            railExpandAriaLabel: expand?.getAttribute('aria-label'),
                            railVisualLabel: expandLabel.content,
                            railVisualWritingMode: expandLabel.writingMode,
                            railVisualTextOrientation: expandLabel.textOrientation,
                            railBodyHidden: body?.getAttribute('aria-hidden'),
                            railBodyInert: body?.inert,
                          };
                        }"""
                    )
                    assert both_collapsed["mapState"] == "collapsed"
                    assert both_collapsed["railState"] == "collapsed"
                    assert both_collapsed["articleWidth"] > map_collapsed["articleWidth"] + 40
                    assert 64 <= both_collapsed["railWidth"] <= 112
                    assert both_collapsed["contextButtonExpanded"] == "false"
                    assert both_collapsed["railExpandExpanded"] == "false"
                    assert both_collapsed["railExpandAriaLabel"] == "Show learning context"
                    assert both_collapsed["railVisualLabel"] == '"Context"'
                    assert both_collapsed["railVisualWritingMode"] == "horizontal-tb"
                    assert both_collapsed["railBodyHidden"] == "true"
                    assert both_collapsed["railBodyInert"] is True
                    _assert_no_horizontal_overflow(page)
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_desktop_course_map_expansion_hides_full_list_until_transition_end(
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
                    page.click("#raya-course-map .raya-course-map-toggle")
                    page.wait_for_function(
                        "() => document.documentElement.dataset.rayaCourseMap === 'collapsed'"
                    )
                    page.wait_for_function(
                        "() => !document.querySelector('#raya-course-map')?.dataset.rayaCourseMapTransition"
                    )
                    page.click("#raya-course-map .raya-course-map-toggle")
                    expanding = page.evaluate(
                        """async () => {
                          await new Promise((resolve) => requestAnimationFrame(resolve));
                          const map = document.querySelector('#raya-course-map');
                          const list = document.querySelector('#raya-course-map-list');
                          const firstLink = list?.querySelector('a[href]');
                          return {
                            rootState: document.documentElement.dataset.rayaCourseMap,
                            transition: map?.dataset.rayaCourseMapTransition,
                            width: map?.getBoundingClientRect().width,
                            listDisplay: list ? getComputedStyle(list).display : null,
                            listVisibility: list ? getComputedStyle(list).visibility : null,
                            listHidden: list?.getAttribute('aria-hidden'),
                            listInert: list?.inert,
                            firstLinkTabIndex: firstLink?.getAttribute('tabindex'),
                            overflow: Math.ceil(
                              document.documentElement.scrollWidth - window.innerWidth
                            ),
                            storage: {
                              local: Object.keys(localStorage),
                              session: Object.keys(sessionStorage),
                            },
                          };
                        }"""
                    )
                    assert expanding["rootState"] == "expanded"
                    assert expanding["transition"] == "expanding"
                    assert expanding["width"] <= 240
                    assert expanding["listDisplay"] == "grid"
                    assert expanding["listVisibility"] == "hidden"
                    assert expanding["listHidden"] == "true"
                    assert expanding["listInert"] is True
                    assert expanding["firstLinkTabIndex"] == "-1"
                    assert expanding["overflow"] <= 1
                    assert expanding["storage"] == {"local": [], "session": []}

                    page.wait_for_function(
                        "() => !document.querySelector('#raya-course-map')?.dataset.rayaCourseMapTransition"
                    )
                    expanded = page.evaluate(
                        """() => {
                          const map = document.querySelector('#raya-course-map');
                          const list = document.querySelector('#raya-course-map-list');
                          const firstLink = list?.querySelector('a[href]');
                          const firstToggle = list?.querySelector('.raya-course-map-node-toggle');
                          return {
                            width: map?.getBoundingClientRect().width,
                            listVisibility: list ? getComputedStyle(list).visibility : null,
                            listHidden: list?.getAttribute('aria-hidden'),
                            listInert: list?.inert,
                            firstLinkTabIndex: firstLink?.getAttribute('tabindex'),
                            firstToggleTabIndex: firstToggle?.getAttribute('tabindex'),
                          };
                        }"""
                    )
                    assert expanded["width"] >= 220
                    assert expanded["listVisibility"] == "visible"
                    assert expanded["listHidden"] == "false"
                    assert expanded["listInert"] is False
                    assert expanded["firstLinkTabIndex"] is None
                    assert expanded["firstToggleTabIndex"] is None
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_desktop_learning_rail_expansion_hides_body_until_transition_end(
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
                    page.click("[data-raya-learning-rail-toggle]")
                    page.wait_for_function(
                        "() => document.documentElement.dataset.rayaLearningRail === 'collapsed'"
                    )
                    page.wait_for_function(
                        "() => !document.querySelector('#raya-learning-rail')?.dataset.rayaLearningRailTransition"
                    )
                    page.click("[data-raya-learning-rail-expand]")
                    expanding = page.evaluate(
                        """async () => {
                          await new Promise((resolve) => requestAnimationFrame(resolve));
                          const rail = document.querySelector('#raya-learning-rail');
                          const body = document.querySelector('#raya-learning-rail-body');
                          const expand = document.querySelector('[data-raya-learning-rail-expand]');
                          const collapse = document.querySelector('[data-raya-learning-rail-collapse]');
                          return {
                            rootState: document.documentElement.dataset.rayaLearningRail,
                            transition: rail?.dataset.rayaLearningRailTransition,
                            width: rail?.getBoundingClientRect().width,
                            bodyDisplay: body ? getComputedStyle(body).display : null,
                            bodyVisibility: body ? getComputedStyle(body).visibility : null,
                            bodyHidden: body?.getAttribute('aria-hidden'),
                            bodyInert: body?.inert,
                            expandVisible: !!expand?.getClientRects().length,
                            collapseVisible: !!collapse?.getClientRects().length,
                            overflow: Math.ceil(
                              document.documentElement.scrollWidth - window.innerWidth
                            ),
                            storage: {
                              local: Object.keys(localStorage),
                              session: Object.keys(sessionStorage),
                            },
                          };
                        }"""
                    )
                    assert expanding["rootState"] == "expanded"
                    assert expanding["transition"] == "expanding"
                    assert expanding["width"] <= 260
                    assert expanding["bodyDisplay"] == "grid"
                    assert expanding["bodyVisibility"] == "hidden"
                    assert expanding["bodyHidden"] == "true"
                    assert expanding["bodyInert"] is True
                    assert expanding["expandVisible"] is True
                    assert expanding["collapseVisible"] is False
                    assert expanding["overflow"] <= 1
                    assert expanding["storage"] == {"local": [], "session": []}

                    page.wait_for_function(
                        "() => !document.querySelector('#raya-learning-rail')?.dataset.rayaLearningRailTransition"
                    )
                    expanded = page.evaluate(
                        """() => {
                          const rail = document.querySelector('#raya-learning-rail');
                          const body = document.querySelector('#raya-learning-rail-body');
                          const expand = document.querySelector('[data-raya-learning-rail-expand]');
                          const collapse = document.querySelector('[data-raya-learning-rail-collapse]');
                          return {
                            width: rail?.getBoundingClientRect().width,
                            bodyVisibility: body ? getComputedStyle(body).visibility : null,
                            bodyHidden: body?.getAttribute('aria-hidden'),
                            bodyInert: body?.inert,
                            expandVisible: !!expand?.getClientRects().length,
                            collapseVisible: !!collapse?.getClientRects().length,
                          };
                        }"""
                    )
                    assert expanded["width"] >= 220
                    assert expanded["bodyVisibility"] == "visible"
                    assert expanded["bodyHidden"] == "false"
                    assert expanded["bodyInert"] is False
                    assert expanded["expandVisible"] is False
                    assert expanded["collapseVisible"] is True
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_learning_rail_content_starts_in_first_viewport(
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
                    storage_calls = page.evaluate(
                        """() => {
                          const calls = [];
                          const originalLocalSet = window.localStorage.setItem;
                          const originalSessionSet = window.sessionStorage.setItem;
                          window.localStorage.setItem = function(key, value) {
                            calls.push(`local:${key}`);
                            return originalLocalSet.call(this, key, value);
                          };
                          window.sessionStorage.setItem = function(key, value) {
                            calls.push(`session:${key}`);
                            return originalSessionSet.call(this, key, value);
                          };
                          return calls;
                        }"""
                    )
                    probe = page.evaluate(
                        """() => {
                          const rail = document.querySelector('#raya-learning-rail');
                          const header = rail?.querySelector('.raya-learning-rail-header');
                          const body = rail?.querySelector('#raya-learning-rail-body');
                          const firstPanel = rail?.querySelector('.raya-rail-panel');
                          const firstPanelBody = firstPanel?.querySelector('.raya-rail-panel-body');
                          const pageContents = rail?.querySelector('.raya-page-contents');
                          const keyObjects = rail?.querySelector('.raya-page-toc-objects');
                          const currentSection = rail?.querySelector('.raya-page-current-section');
                          const currentSectionLink = rail?.querySelector('[data-raya-current-section-link]');
                          const viewportHeight = window.innerHeight;
                          const box = (node) => {
                            const rect = node?.getBoundingClientRect();
                            return rect
                              ? { top: rect.top, bottom: rect.bottom, height: rect.height }
                              : null;
                          };
                          return {
                            railText: rail?.innerText || '',
                            railTop: rail?.getBoundingClientRect().top || 0,
                            header: box(header),
                            body: box(body),
                            firstPanel: box(firstPanel),
                            firstPanelBody: box(firstPanelBody),
                            firstPanelClass: firstPanel?.className || '',
                            pageContents: box(pageContents),
                            keyObjects: box(keyObjects),
                            keyObjectText: keyObjects?.innerText || '',
                            keyObjectHrefs: Array.from(
                              keyObjects?.querySelectorAll('a') || []
                            ).map((link) => link.getAttribute('href')),
                            currentSection: box(currentSection),
                            currentSectionText: currentSectionLink?.textContent?.trim() || '',
                            currentSectionHref: currentSectionLink?.getAttribute('href') || '',
                            viewportHeight,
                            railState: rail?.getAttribute('data-raya-learning-rail'),
                            bodyHidden: body?.getAttribute('aria-hidden'),
                          };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert storage_calls == []
    assert "Learning context" in probe["railText"]
    assert "Summary" in probe["railText"]
    assert probe["railState"] == "expanded"
    assert probe["bodyHidden"] == "false"
    assert probe["header"]["top"] < 140
    assert probe["body"]["top"] < 190
    assert probe["firstPanel"]["top"] < 210
    assert probe["firstPanelBody"]["top"] < 260
    assert probe["firstPanelBody"]["bottom"] < probe["viewportHeight"]
    assert "raya-page-current-section" in probe["firstPanelClass"]
    assert probe["currentSection"]["top"] < 210
    assert probe["pageContents"]["top"] < 360
    assert probe["pageContents"]["bottom"] < probe["viewportHeight"]
    assert probe["currentSectionText"]
    assert probe["currentSectionHref"].startswith("#")
    assert "Key objects" in probe["keyObjectText"]
    assert "Definition 4.1 Orthogonal residual" in probe["keyObjectText"]
    assert "Proposition 4.2 Projection residual is orthogonal" in probe["keyObjectText"]
    assert "Equation 4.1" in probe["keyObjectText"]
    assert "Figure 4.1 Projection triangle" in probe["keyObjectText"]
    assert "Table 4.1 Projection checklist" in probe["keyObjectText"]
    assert "Problem 4.2 Reader map practice" in probe["keyObjectText"]
    assert "Activity 4.1 Check the residual" in probe["keyObjectText"]
    assert "recommend" not in probe["keyObjectText"].lower()
    assert "progress" not in probe["keyObjectText"].lower()
    assert "mastery" not in probe["keyObjectText"].lower()
    for expected_href in (
        "#raya-object-orthogonal-definition",
        "#raya-object-orthogonal-proposition",
        "#raya-proof-proof-orthogonal-proposition",
        "#raya-object-orthogonal-equation",
        "#raya-object-orthogonal-figure",
        "#raya-object-orthogonal-table",
        "#raya-object-reader-map-practice",
        "#raya-object-orthogonal-activity",
    ):
        assert expected_href in probe["keyObjectHrefs"]


def test_render_fixture_key_object_links_track_visible_object(
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
                    initial_url = page.evaluate("() => window.location.href")
                    _assert_no_horizontal_overflow(page)
                    page.locator(
                        "#raya-object-orthogonal-definition"
                    ).scroll_into_view_if_needed()
                    page.wait_for_function(
                        """() => document
                          .querySelector('.raya-page-toc-objects a[data-raya-key-object-link="raya-object-orthogonal-definition"]')
                          ?.getAttribute('aria-current') === 'location'"""
                    )
                    state = page.evaluate(
                        """() => ({
                          currentUrl: window.location.href,
                          activeObjectHref: document
                            .querySelector('.raya-page-toc-objects a[aria-current="location"]')
                            ?.getAttribute('href') || '',
                          activeObjectText: document
                            .querySelector('.raya-page-toc-objects a[aria-current="location"]')
                            ?.textContent.trim() || '',
                          currentSectionHref: document
                            .querySelector('.raya-current-section-link')
                            ?.getAttribute('href') || '',
                          storage: [
                            Object.keys(localStorage),
                            Object.keys(sessionStorage),
                          ],
                          overflow: Math.ceil(
                            document.documentElement.scrollWidth - window.innerWidth
                          ),
                        })"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert state["activeObjectHref"] == "#raya-object-orthogonal-definition"
    assert state["activeObjectText"].startswith("Definition 4.1")
    assert state["currentSectionHref"] != "#raya-object-orthogonal-definition"
    assert state["currentUrl"] == initial_url
    assert state["storage"] == [[], []]
    assert state["overflow"] <= 1


def test_render_fixture_reading_flow_panel_is_visible_in_first_viewport(
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
                    probe = page.evaluate(
                        """() => {
                          const panel = document.querySelector('.raya-page-reading-flow');
                          const previous = panel?.querySelector('[data-raya-prev-page]');
                          const next = panel?.querySelector('[data-raya-next-page]');
                          const graph = panel?.querySelector('.raya-reading-flow-graph-link');
                          const counts = panel?.querySelector('.raya-reading-flow-counts');
                          const connection = panel?.querySelector('.raya-reading-flow-connections a');
                          const kind = connection?.querySelector('.raya-reading-flow-connection-kind');
                          const direction = connection?.querySelector('.raya-reading-flow-connection-direction');
                          const title = connection?.querySelector('.raya-reading-flow-connection-title');
                          const box = (node) => {
                            const rect = node?.getBoundingClientRect();
                            return rect
                              ? { top: rect.top, bottom: rect.bottom, width: rect.width, height: rect.height }
                              : null;
                          };
                          return {
                            panel: box(panel),
                            previous: box(previous),
                            next: box(next),
                            graph: box(graph),
                            connection: box(connection),
                            kind: box(kind),
                            direction: box(direction),
                            title: box(title),
                            viewportHeight: window.innerHeight,
                            counts: counts?.innerText || '',
                            connectionKind: kind?.innerText || '',
                            connectionDirection: direction?.innerText || '',
                            connectionTitle: title?.innerText || '',
                            state: panel?.getAttribute('data-raya-rail-panel-state'),
                            hidden: panel?.querySelector('.raya-rail-panel-body')
                              ?.getAttribute('aria-hidden'),
                            graphHref: graph?.getAttribute('href'),
                            text: panel?.innerText || '',
                          };
                        }"""
                    )
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

    assert probe["state"] == "expanded"
    assert probe["hidden"] == "false"
    assert probe["panel"]["top"] < probe["viewportHeight"]
    assert probe["previous"]["width"] > 40
    assert probe["previous"]["height"] > 32
    assert probe["next"]["width"] > 40
    assert probe["next"]["height"] > 32
    assert probe["graph"]["width"] > 80
    assert probe["graph"]["height"] > 24
    assert probe["connection"]["width"] > 80
    assert probe["connection"]["height"] > 42
    assert probe["connection"]["height"] <= 72
    assert probe["kind"]["width"] > 24
    assert probe["direction"]["width"] > 40
    assert probe["title"]["width"] > 40
    assert probe["connectionKind"] == "Content"
    assert probe["connectionDirection"] in {"FROM THIS PAGE", "LINKS HERE"}
    assert probe["connectionTitle"]
    assert "from this page" in probe["counts"]
    assert "links here" in probe["counts"]
    assert probe["graphHref"] == "../_raya/graph/index.html?page=reader-ux"
    assert "Open in course graph" in probe["text"]


def test_render_fixture_study_object_families_are_visually_distinct(
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
        base_url = handle.base_url
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
                        f"{base_url}/reader-ux/index.html",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(page)
                    probe = page.evaluate(
                        """() => {
                          const styleOf = (selector) => {
                            const node = document.querySelector(selector);
                            if (!node) {
                              return null;
                            }
                            const rect = node.getBoundingClientRect();
                            const style = getComputedStyle(node);
                            return {
                              background: style.backgroundColor,
                              borderLeft: style.borderLeftColor,
                              color: style.color,
                              height: rect.height,
                              width: rect.width,
                            };
                          };
                          return {
                            practiceAction: styleOf(
                              '#raya-official-practice .raya-official-practice-open'
                            ),
                            practiceActionHref: document
                              .querySelector('#raya-official-practice .raya-official-practice-open')
                              ?.getAttribute('href'),
                            definitionBadge: styleOf(
                              '#raya-object-orthogonal-definition .raya-numbered-object-badge'
                            ),
                            problemBadge: styleOf(
                              '#raya-object-orthogonal-problem .raya-numbered-object-badge'
                            ),
                            officialCard: styleOf('.raya-official-card'),
                            officialQuiz: styleOf('.raya-official-quiz'),
                            officialCardKind: styleOf(
                              '.raya-official-card .raya-official-kind'
                            ),
                            officialQuizKind: styleOf(
                              '.raya-official-quiz .raya-official-kind'
                            ),
                          };
                        }"""
                    )
                    practice_href = page.locator(
                        "#raya-official-practice .raya-official-practice-open"
                    ).get_attribute("href")
                    assert practice_href == "../_raya/practice/index.html?page=reader-ux"
                    page.goto(f"{base_url}/_raya/practice/index.html?page=reader-ux")
                    page.wait_for_load_state("networkidle")
                    practice_focus = page.locator("[data-raya-practice-page-focus]")
                    assert practice_focus.is_visible()
                    assert "Focused on page" in practice_focus.inner_text()
                    assert "Projection Residuals" in practice_focus.inner_text()
                    visible_pages = page.locator(
                        "[data-raya-practice-object]:not([hidden])"
                    ).evaluate_all(
                        "nodes => nodes.map((node) => node.dataset.rayaPracticePage)"
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert probe["definitionBadge"] is not None
    assert probe["problemBadge"] is not None
    assert probe["practiceAction"] is not None
    assert probe["practiceActionHref"] == "../_raya/practice/index.html?page=reader-ux"
    assert probe["officialCard"] is not None
    assert probe["officialQuiz"] is not None
    assert probe["officialCardKind"] is not None
    assert probe["officialQuizKind"] is not None
    assert probe["definitionBadge"]["background"] != probe["problemBadge"]["background"]
    assert probe["officialCard"]["borderLeft"] != probe["officialQuiz"]["borderLeft"]
    assert probe["officialCardKind"]["background"] != probe["officialQuizKind"]["background"]
    assert probe["officialCardKind"]["color"] != probe["officialCardKind"]["background"]
    assert probe["officialQuizKind"]["color"] != probe["officialQuizKind"]["background"]
    assert probe["definitionBadge"]["width"] >= 80
    assert probe["definitionBadge"]["height"] >= 40
    assert probe["practiceAction"]["width"] >= 120
    assert probe["practiceAction"]["height"] >= 28
    assert probe["officialCardKind"]["width"] >= 40
    assert probe["officialCardKind"]["height"] >= 20
    assert probe["officialQuizKind"]["width"] >= 40
    assert probe["officialQuizKind"]["height"] >= 20
    assert requested_urls
    assert visible_pages == ["reader-ux", "reader-ux"]
    assert all(url.startswith(f"{base_url}/") for url in requested_urls)


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
                    visible_controls = page.locator(
                        ".raya-top-command-bar .raya-command:visible, "
                        ".raya-top-command-bar .raya-command-search-input:visible, "
                        ".raya-top-command-bar .raya-command-search-submit:visible"
                    )
                    control_boxes = visible_controls.evaluate_all(
                        """controls => controls.map((control) => {
                          const rect = control.getBoundingClientRect();
                          return {
                            label: control.getAttribute('aria-label') ||
                              control.textContent.trim(),
                            width: rect.width,
                            height: rect.height,
                          };
                        })"""
                    )
                    assert control_boxes
                    assert all(box["height"] >= 36 for box in control_boxes)
                    command_state = page.evaluate(
                        """() => ({
                          searchInput: !!document.querySelector(
                            '.raya-command-search-input'
                          )?.getClientRects().length,
                          searchSubmit: !!document.querySelector(
                            '.raya-command-search-submit'
                          )?.getClientRects().length,
                          graphLink: !!document.querySelector('.raya-command-graph')
                            ?.getClientRects().length,
                          practiceLink: !!document.querySelector(
                            '.raya-command-practice'
                          )?.getClientRects().length,
                          tasksLink: !!document.querySelector('.raya-command-tasks')
                            ?.getClientRects().length,
                          scheduleLink: !!document.querySelector(
                            '.raya-command-schedule'
                          )?.getClientRects().length,
                          mapButton: !!document.querySelector('.raya-command-map')
                            ?.getClientRects().length,
                          textSizeButton: !!document.querySelector(
                            '.raya-text-size-toggle'
                          )?.getClientRects().length,
                          fontButton: !!document.querySelector('.raya-font-toggle')
                            ?.getClientRects().length,
                          skinButton: !!document.querySelector('[data-raya-skin-toggle]')
                            ?.getClientRects().length,
                        })"""
                    )
                    assert command_state == {
                        "searchInput": True,
                        "searchSubmit": True,
                        "graphLink": True,
                        "practiceLink": True,
                        "tasksLink": True,
                        "scheduleLink": True,
                        "mapButton": True,
                        "textSizeButton": True,
                        "fontButton": True,
                        "skinButton": True,
                    }
                    topbar = _bounding_box(page, ".raya-top-command-bar")
                    first_heading = _bounding_box(page, "#raya-article h1")
                    assert topbar["height"] <= 150
                    assert first_heading["y"] <= 320
                    assert page.locator(
                        "[data-raya-learning-rail-toggle]"
                    ).first.is_hidden()
                    assert (
                        page.locator("#raya-learning-rail-body").get_attribute(
                            "aria-hidden"
                        )
                        == "false"
                    )
                    article = _bounding_box(page, "article.raya-main-article")
                    learning_rail = _bounding_box(page, "#raya-learning-rail")
                    assert article["y"] < learning_rail["y"]
                    mobile_context = page.evaluate(
                        """() => ({
                          drawerState: document.documentElement
                            .dataset
                            .rayaLearningRailDrawer,
                          scrollLock: document.documentElement
                            .dataset
                            .rayaLearningRailScrollLock,
                          commandVisible: !!document
                            .querySelector('[data-raya-learning-rail-toggle]')
                            ?.getClientRects().length,
                          commandExpanded: document
                            .querySelector('[data-raya-learning-rail-toggle]')
                            ?.getAttribute('aria-expanded'),
                          railHidden: document.querySelector('#raya-learning-rail')
                            ?.getAttribute('aria-hidden'),
                          railInert: document.querySelector('#raya-learning-rail')?.inert,
                          bodyHidden: document.querySelector('#raya-learning-rail-body')
                            ?.getAttribute('aria-hidden'),
                          bodyInert: document.querySelector('#raya-learning-rail-body')?.inert,
                        })"""
                    )
                    assert mobile_context == {
                        "drawerState": "closed",
                        "scrollLock": "false",
                        "commandVisible": False,
                        "commandExpanded": "false",
                        "railHidden": "false",
                        "railInert": False,
                        "bodyHidden": "false",
                        "bodyInert": False,
                    }
                    page.set_viewport_size({"width": 1440, "height": 900})
                    page.wait_for_function(
                        """() => document.documentElement.dataset.rayaLearningRailDrawer === 'closed'
                          && document.querySelector('[data-raya-learning-rail-toggle]')
                            ?.getAttribute('aria-expanded') === 'true'"""
                    )
                    desktop_context = page.evaluate(
                        """() => ({
                          railHidden: document.querySelector('#raya-learning-rail')
                            ?.getAttribute('aria-hidden'),
                          railInert: document.querySelector('#raya-learning-rail')?.inert,
                          bodyHidden: document.querySelector('#raya-learning-rail-body')
                            ?.getAttribute('aria-hidden'),
                          bodyInert: document.querySelector('#raya-learning-rail-body')?.inert,
                          firstRailLinkTabIndex: document
                            .querySelector('#raya-learning-rail a, #raya-learning-rail button')
                            ?.getAttribute('tabindex'),
                        })"""
                    )
                    assert desktop_context == {
                        "railHidden": "false",
                        "railInert": False,
                        "bodyHidden": "false",
                        "bodyInert": False,
                        "firstRailLinkTabIndex": None,
                    }
                    page.set_viewport_size({"width": 390, "height": 844})
                    page.wait_for_function(
                        """() => document.documentElement.dataset.rayaLearningRailDrawer === 'closed'"""
                    )
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

                    page.click('[data-raya-course-map-action="scan"]')
                    drawer_scan = page.evaluate(
                        """() => ({
                          scan: document
                            .querySelector('#raya-course-map')
                            ?.dataset
                            ?.rayaCourseMapScan,
                          scanPressed: document
                            .querySelector('[data-raya-course-map-action="scan"]')
                            ?.getAttribute('aria-pressed'),
                          currentVisible: !!document
                            .querySelector('#raya-course-map a[aria-current="page"]')
                            ?.checkVisibility(),
                        })"""
                    )
                    assert drawer_scan == {
                        "scan": "active",
                        "scanPressed": "true",
                        "currentVisible": True,
                    }

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
                          scan: document
                            .querySelector('#raya-course-map')
                            ?.dataset
                            ?.rayaCourseMapScan || '',
                          scanPressed: document
                            .querySelector('[data-raya-course-map-action="scan"]')
                            ?.getAttribute('aria-pressed'),
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
                        "scan": "",
                        "scanPressed": "false",
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
                    current_section = page.evaluate(
                        """() => ({
                          href: document
                            .querySelector('.raya-current-section-link')
                            ?.getAttribute('href'),
                          text: document
                            .querySelector('.raya-current-section-link')
                            ?.textContent
                            ?.trim(),
                          commandHref: document
                            .querySelector('.raya-reading-context-section')
                            ?.getAttribute('href'),
                          commandText: document
                            .querySelector('.raya-reading-context-section')
                            ?.textContent
                            ?.trim(),
                          commandVisibleLabel: document
                            .querySelector('.raya-reading-context-section-label')
                            ?.textContent
                            ?.trim(),
                          commandLabel: document
                            .querySelector('.raya-reading-context-section')
                            ?.getAttribute('aria-label'),
                        })"""
                    )
                    assert current_section["href"] == "#worked-example"
                    assert current_section["text"] == "Worked Example"
                    assert current_section["commandHref"] == "#worked-example"
                    assert current_section["commandText"] == "Now Worked Example"
                    assert current_section["commandVisibleLabel"] == "Worked Example"
                    assert (
                        current_section["commandLabel"]
                        == "Current section: Worked Example"
                    )
                    redundant_mutations = page.evaluate(
                        """async () => {
                          const current = document
                            .querySelector('.raya-current-section-link');
                          if (!current) {
                            return -1;
                          }
                          const originalSetAttribute = current.setAttribute.bind(current);
                          let hrefUpdates = 0;
                          current.setAttribute = (name, value) => {
                            if (name === 'href') {
                              hrefUpdates += 1;
                            }
                            return originalSetAttribute(name, value);
                          };
                          window.dispatchEvent(new Event('scroll'));
                          await new Promise((resolve) => window.requestAnimationFrame(resolve));
                          return hrefUpdates;
                        }"""
                    )
                    assert redundant_mutations == 0

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
                    page.wait_for_function(
                        """() => document
                          .querySelector('[data-raya-current-section-link]')
                          ?.getAttribute('href') === '#1-numeric-heading'"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_mobile_course_map_drawer_has_comfort_chrome(
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
                    page.click(".raya-command-map")
                    page.wait_for_function(
                        "() => document.documentElement.dataset.rayaCourseMapDrawer === 'open'"
                    )
                    state = page.evaluate(
                        """() => {
                          const root = document.documentElement;
                          const body = document.body;
                          const map = document.querySelector('#raya-course-map');
                          const backdrop = document.querySelector('[data-raya-course-map-drawer-backdrop]');
                          const opener = document.querySelector('.raya-command-map');
                          const chrome = document.querySelector('.raya-course-map-drawer-chrome');
                          const title = document.querySelector('.raya-course-map-drawer-title');
                          const grip = document.querySelector('.raya-course-map-drawer-grip');
                          const close = document.querySelector('[data-raya-course-map-close]');
                          const mapBox = map.getBoundingClientRect();
                          const backdropStyle = getComputedStyle(backdrop);
                          return {
                            drawer: root.dataset.rayaCourseMapDrawer,
                            scrollLock: root.dataset.rayaCourseMapScrollLock,
                            htmlOverflow: getComputedStyle(root).overflow,
                            bodyOverflow: getComputedStyle(body).overflow,
                            ariaHidden: map.getAttribute('aria-hidden'),
                            inert: map.inert,
                            chromeVisible: chrome && getComputedStyle(chrome).display !== 'none',
                            chromeAriaHidden: chrome && chrome.getAttribute('aria-hidden'),
                            title: title && title.textContent.trim(),
                            gripVisible: grip && getComputedStyle(grip).display !== 'none',
                            closeLabel: close && close.getAttribute('aria-label'),
                            width: mapBox.width,
                            left: mapBox.left,
                            right: mapBox.right,
                            backdropHidden: backdrop.hidden,
                            backdropDisplay: backdropStyle.display,
                            backdropBackground: backdropStyle.backgroundColor,
                            backdropFilter: backdropStyle.backdropFilter || backdropStyle.webkitBackdropFilter,
                            openerExpanded: opener.getAttribute('aria-expanded'),
                          };
                        }"""
                    )
                    assert state["drawer"] == "open"
                    assert state["scrollLock"] == "true"
                    assert state["htmlOverflow"] == "hidden"
                    assert state["bodyOverflow"] == "hidden"
                    assert state["ariaHidden"] == "false"
                    assert state["inert"] is False
                    assert state["chromeVisible"] is True
                    assert state["chromeAriaHidden"] != "true"
                    assert state["title"] == "Course map"
                    assert state["gripVisible"] is True
                    assert state["closeLabel"] == "Close course map"
                    assert 320 <= state["width"] <= 390
                    assert state["left"] == 0
                    assert state["right"] <= 390
                    assert state["backdropHidden"] is False
                    assert state["backdropDisplay"] == "block"
                    assert "rgba" in state["backdropBackground"]
                    assert state["backdropFilter"] != "none"
                    assert state["openerExpanded"] == "true"

                    page.keyboard.press("Escape")
                    page.wait_for_function(
                        "() => document.documentElement.dataset.rayaCourseMapDrawer === 'closed'"
                    )
                    closed = page.evaluate(
                        """() => ({
                          scrollLock: document.documentElement.dataset.rayaCourseMapScrollLock,
                          htmlOverflow: getComputedStyle(document.documentElement).overflow,
                          bodyOverflow: getComputedStyle(document.body).overflow,
                          focusedClass: document.activeElement && document.activeElement.className,
                        })"""
                    )
                    assert closed["scrollLock"] == "false"
                    assert closed["htmlOverflow"] != "hidden"
                    assert closed["bodyOverflow"] != "hidden"
                    assert "raya-command-map" in closed["focusedClass"]

                    page.click(".raya-command-map")
                    page.wait_for_function(
                        "() => document.documentElement.dataset.rayaCourseMapDrawer === 'open'"
                    )
                    page.set_viewport_size({"width": 1280, "height": 900})
                    page.wait_for_function(
                        "() => document.documentElement.dataset.rayaCourseMapDrawer === 'closed'"
                    )
                    resized = page.evaluate(
                        """() => {
                          const root = document.documentElement;
                          const backdrop = document.querySelector('[data-raya-course-map-drawer-backdrop]');
                          return {
                            drawer: root.dataset.rayaCourseMapDrawer,
                            scrollLock: root.dataset.rayaCourseMapScrollLock,
                            backdropHidden: backdrop.hidden,
                            backdropDisplay: getComputedStyle(backdrop).display,
                          };
                        }"""
                    )
                    assert resized == {
                        "drawer": "closed",
                        "scrollLock": "false",
                        "backdropHidden": True,
                        "backdropDisplay": "none",
                    }
                    _assert_no_horizontal_overflow(page)
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
                        title_box = page.locator("h1").bounding_box()
                        assert box is not None
                        assert title_box is not None
                        assert title_box["y"] < box["y"]
                        assert box["width"] <= viewport["width"]
                        if viewport["width"] <= 480:
                            assert box["y"] < viewport["height"]
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_render_fixture_page_brief_exposes_learning_path_actions(
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
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    requested_urls: list[str] = []
                    page.on(
                        "request", lambda request: requested_urls.append(request.url)
                    )
                    try:
                        page.goto(
                            f"{handle.base_url}/static-path/index.html",
                            wait_until="networkidle",
                        )
                        requested_urls.clear()
                        _assert_no_horizontal_overflow(page)
                        brief = page.locator(".raya-page-brief")
                        path_fact = brief.locator(".raya-page-brief-path")
                        previous = path_fact.locator("[rel='prev']")
                        next_link = path_fact.locator("[rel='next']")
                        assert path_fact.is_visible()
                        assert "learning path" in path_fact.inner_text().lower()
                        assert previous.get_attribute("data-raya-prev-page") == ""
                        assert previous.get_attribute("aria-keyshortcuts") == (
                            "ArrowLeft"
                        )
                        assert next_link.get_attribute("data-raya-next-page") == ""
                        assert next_link.get_attribute("aria-keyshortcuts") == (
                            "ArrowRight"
                        )
                        assert previous.get_attribute("href") == "../index.html"
                        assert next_link.get_attribute("href") == (
                            "../math-authoring/index.html"
                        )
                        state = path_fact.evaluate(
                            """(node) => {
                              const previous = node.querySelector('[rel="prev"]');
                              const graph = document.querySelector(
                                '.raya-page-brief-connections a'
                              );
                              const previousStyle = getComputedStyle(previous);
                              const graphStyle = getComputedStyle(graph);
                              return {
                                text: node.textContent,
                                previousDisplay: previousStyle.display,
                                previousBorderStyle: previousStyle.borderTopStyle,
                                previousBackgroundColor: previousStyle.backgroundColor,
                                previousTextDecoration: previousStyle.textDecorationLine,
                                graphDisplay: graphStyle.display,
                                graphBorderStyle: graphStyle.borderTopStyle,
                              };
                            }"""
                        )
                        assert state["previousDisplay"] in {"inline-flex", "flex"}
                        assert state["previousBorderStyle"] == "solid"
                        assert state["previousBackgroundColor"] != (
                            "rgba(0, 0, 0, 0)"
                        )
                        assert state["previousTextDecoration"] == "none"
                        assert state["graphDisplay"] in {"inline-flex", "flex"}
                        assert state["graphBorderStyle"] == "solid"
                        assert "progress" not in state["text"].lower()
                        assert "recommend" not in state["text"].lower()
                        assert "complete" not in state["text"].lower()
                        box = brief.bounding_box()
                        assert box is not None
                        assert box["width"] <= viewport["width"]
                        if viewport["width"] <= 480:
                            assert box["y"] < viewport["height"]
                        assert requested_urls == []
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


def test_render_fixture_graph_collapsed_rails_prioritize_canvas_space(
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
                        f"{handle.base_url}/_raya/graph/index.html",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(page)
                    expanded = page.evaluate(
                        """() => {
                          const box = (selector) => document
                            .querySelector(selector)
                            .getBoundingClientRect().width;
                          return {
                            list: box('.raya-graph-list-panel'),
                            map: box('.raya-graph-map-panel'),
                            inspector: box('.raya-graph-inspector-panel'),
                          };
                        }"""
                    )

                    page.click('[data-raya-graph-toggle-panel="list"]')
                    page.click('[data-raya-graph-toggle-panel="inspector"]')
                    page.wait_for_function(
                        """() => {
                          const root = document.querySelector('[data-raya-graph-page]');
                          return root?.getAttribute('data-raya-graph-list-state') === 'collapsed'
                            && root?.getAttribute('data-raya-graph-inspector-state') === 'collapsed';
                        }"""
                    )
                    collapsed = page.evaluate(
                        """() => {
                          const box = (selector) => document
                            .querySelector(selector)
                            .getBoundingClientRect().width;
                          const bodyState = (name) => {
                            const body = document.querySelector(
                              `[data-raya-graph-panel-body="${name}"]`
                            );
                            const tabbables = body
                              ? Array.from(
                                  body.querySelectorAll(
                                    'a[href], button, input, select, textarea, summary, [tabindex]'
                                  )
                                ).filter((element) => {
                                  const disabled = element.disabled
                                    || element.getAttribute('aria-disabled') === 'true';
                                  return !disabled && element.getAttribute('tabindex') !== '-1';
                                })
                              : [];
                            return {
                              ariaHidden: body?.getAttribute('aria-hidden'),
                              tabbable: tabbables.length,
                            };
                          };
                          const labelFor = (name) => {
                            const button = document.querySelector(
                              `[data-raya-graph-toggle-panel="${name}"]`
                            );
                            return {
                              text: button?.textContent.trim(),
                              ariaLabel: button?.getAttribute('aria-label'),
                              expanded: button?.getAttribute('aria-expanded'),
                            };
                          };
                          return {
                            list: box('.raya-graph-list-panel'),
                            map: box('.raya-graph-map-panel'),
                            inspector: box('.raya-graph-inspector-panel'),
                            listBody: bodyState('list'),
                            inspectorBody: bodyState('inspector'),
                            listToggle: labelFor('list'),
                            inspectorToggle: labelFor('inspector'),
                          };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert expanded["list"] >= 240
    assert expanded["inspector"] >= 260
    assert collapsed["list"] <= 96
    assert collapsed["inspector"] <= 96
    assert collapsed["map"] >= expanded["map"] + 240
    assert collapsed["listBody"] == {"ariaHidden": "true", "tabbable": 0}
    assert collapsed["inspectorBody"] == {"ariaHidden": "true", "tabbable": 0}
    assert collapsed["listToggle"] == {
        "text": "Open",
        "ariaLabel": "Open graph pages panel",
        "expanded": "false",
    }
    assert collapsed["inspectorToggle"] == {
        "text": "Open",
        "ariaLabel": "Open graph inspector panel",
        "expanded": "false",
    }


def test_graph_canvas_legend_remains_visible_when_pages_panel_collapses(
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
        base_url = handle.base_url
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
                        f"{handle.base_url}/_raya/graph/index.html",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(page)
                    page.click('[data-raya-graph-toggle-panel="list"]')
                    page.wait_for_function(
                        """() => document
                          .querySelector('[data-raya-graph-page]')
                          ?.getAttribute('data-raya-graph-list-state') === 'collapsed'"""
                    )
                    before = page.evaluate(
                        """() => {
                          const legend = document.querySelector('.raya-graph-canvas-legend');
                          const firstButton = legend?.querySelector(
                            '[data-raya-graph-group-filter]'
                          );
                          const canvas = document.querySelector('.raya-graph-canvas');
                          const listBody = document.querySelector(
                            '[data-raya-graph-panel-body="list"]'
                          );
                          const box = (node) => {
                            const rect = node?.getBoundingClientRect();
                            return rect
                              ? {
                                  top: rect.top,
                                  bottom: rect.bottom,
                                  width: rect.width,
                                  height: rect.height,
                                }
                              : null;
                          };
                          return {
                            legend: box(legend),
                            firstButton: box(firstButton),
                            canvas: box(canvas),
                            pressed: firstButton?.getAttribute('aria-pressed'),
                            group: firstButton?.getAttribute(
                              'data-raya-graph-group-filter'
                            ),
                            listHidden: listBody?.getAttribute('aria-hidden'),
                            legendText: legend?.innerText || '',
                            overflow: Math.ceil(
                              document.documentElement.scrollWidth - window.innerWidth
                            ),
                          };
                        }"""
                    )
                    page.click(
                        ".raya-graph-canvas-legend "
                        "[data-raya-graph-group-filter]"
                    )
                    page.wait_for_function(
                        """(group) => Array
                          .from(document.querySelectorAll(
                            `[data-raya-graph-group-filter="${group}"]`
                          ))
                          .every((button) => button.getAttribute('aria-pressed') === 'false')""",
                        arg=before["group"],
                    )
                    after = page.evaluate(
                        """(group) => Array
                          .from(document.querySelectorAll(
                            `[data-raya-graph-group-filter="${group}"]`
                          ))
                          .map((button) => button.getAttribute('aria-pressed'))""",
                        arg=before["group"],
                    )
                finally:
                    page.close()
                mobile = browser.new_page(viewport={"width": 390, "height": 844})
                try:
                    mobile.goto(
                        f"{base_url}/_raya/graph/index.html",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(mobile)
                    mobile_state = mobile.evaluate(
                        """() => {
                          const legend = document.querySelector('.raya-graph-canvas-legend');
                          const firstButton = legend?.querySelector(
                            '[data-raya-graph-group-filter]'
                          );
                          const canvas = document.querySelector('.raya-graph-canvas');
                          const box = (node) => {
                            const rect = node?.getBoundingClientRect();
                            return rect
                              ? {
                                  top: rect.top,
                                  bottom: rect.bottom,
                                  width: rect.width,
                                  height: rect.height,
                                }
                              : null;
                          };
                          return {
                            legend: box(legend),
                            firstButton: box(firstButton),
                            canvas: box(canvas),
                            pressed: firstButton?.getAttribute('aria-pressed'),
                            overflow: Math.ceil(
                              document.documentElement.scrollWidth - window.innerWidth
                            ),
                          };
                        }"""
                    )
                finally:
                    mobile.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert requested_urls
    assert all(url.startswith(f"{base_url}/") for url in requested_urls)
    assert before["listHidden"] == "true"
    assert before["legend"] is not None
    assert before["firstButton"] is not None
    assert before["canvas"] is not None
    assert before["pressed"] == "true"
    assert before["legend"]["top"] >= before["canvas"]["bottom"] - 4
    assert before["legend"]["height"] <= 120
    assert before["firstButton"]["width"] > 32
    assert before["firstButton"]["height"] > 24
    assert before["overflow"] <= 1
    assert "groups" in before["legendText"].lower()
    assert after
    assert set(after) == {"false"}
    assert mobile_state["legend"] is not None
    assert mobile_state["firstButton"] is not None
    assert mobile_state["canvas"] is not None
    assert mobile_state["legend"]["top"] >= mobile_state["canvas"]["bottom"] - 4
    assert mobile_state["legend"]["height"] <= 150
    assert mobile_state["firstButton"]["height"] > 24
    assert mobile_state["overflow"] <= 1


def test_graph_page_focus_exposes_return_to_reading_path(tmp_path: Path) -> None:
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
        base_url = handle.base_url
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                desktop = browser.new_page(viewport={"width": 1440, "height": 950})
                try:
                    requested_urls: list[str] = []
                    desktop.on(
                        "request", lambda request: requested_urls.append(request.url)
                    )
                    desktop.goto(
                        f"{base_url}/_raya/graph/index.html?page=reader-ux",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(desktop)
                    desktop.wait_for_selector(
                        "[data-raya-graph-detail-panel]:not([hidden])"
                    )
                    desktop_state = desktop.evaluate(
                        """() => {
                          const path = document.querySelector(
                            '[data-raya-graph-detail-reading-path]'
                          );
                          const primary = path?.querySelector(
                            '.raya-graph-detail-open-primary'
                          );
                          const previous = path?.querySelector(
                            '[data-raya-graph-detail-previous]'
                          );
                          const current = path?.querySelector(
                            '[data-raya-graph-detail-current]'
                          );
                          const next = path?.querySelector(
                            '[data-raya-graph-detail-next]'
                          );
                          const secondary = path?.querySelector(
                            '.raya-graph-detail-secondary-actions'
                          );
                          const keyObjects = document.querySelector(
                            '[data-raya-graph-detail-key-objects]'
                          );
                          const keyObjectLinks = Array.from(
                            keyObjects?.querySelectorAll(
                              '[data-raya-graph-detail-key-object-list] a'
                            ) || []
                          ).map((link) => ({
                            text: link.textContent.trim(),
                            href: link.getAttribute('href'),
                            width: link.getBoundingClientRect().width,
                          }));
                          const box = (node) => {
                            const rect = node?.getBoundingClientRect();
                            return rect
                              ? {
                                  top: rect.top,
                                  bottom: rect.bottom,
                                  width: rect.width,
                                  height: rect.height,
                                }
                              : null;
                          };
                          return {
                            path: box(path),
                            primary: box(primary),
                            previous: box(previous),
                            current: box(current),
                            next: box(next),
                            primaryText: primary?.textContent.trim() || '',
                            previousText: previous?.textContent.trim() || '',
                            currentText: current?.textContent.trim() || '',
                            nextText: next?.textContent.trim() || '',
                            secondaryText: secondary?.textContent || '',
                            keyObjects: box(keyObjects),
                            keyObjectsText: keyObjects?.innerText || '',
                            keyObjectLinks,
                            text: path?.innerText || '',
                            storage: [
                              Object.keys(localStorage),
                              Object.keys(sessionStorage),
                            ],
                            overflow: Math.ceil(
                              document.documentElement.scrollWidth - window.innerWidth
                            ),
                          };
                        }"""
                    )
                finally:
                    desktop.close()

                mobile = browser.new_page(viewport={"width": 390, "height": 844})
                try:
                    mobile.goto(
                        f"{base_url}/_raya/graph/index.html?page=reader-ux",
                        wait_until="networkidle",
                    )
                    _assert_no_horizontal_overflow(mobile)
                    mobile.click('[data-raya-graph-toggle-panel="inspector"]')
                    mobile.wait_for_selector(
                        "[data-raya-graph-detail-panel]:not([hidden])"
                    )
                    mobile_state = mobile.evaluate(
                        """() => {
                          const path = document.querySelector(
                            '[data-raya-graph-detail-reading-path]'
                          );
                          const primary = path?.querySelector(
                            '.raya-graph-detail-open-primary'
                          );
                          const sequence = path?.querySelector(
                            '.raya-graph-detail-sequence'
                          );
                          const keyObjects = document.querySelector(
                            '[data-raya-graph-detail-key-objects]'
                          );
                          const box = (node) => {
                            const rect = node?.getBoundingClientRect();
                            return rect
                              ? {
                                  top: rect.top,
                                  bottom: rect.bottom,
                                  width: rect.width,
                                  height: rect.height,
                                }
                              : null;
                          };
                          return {
                            path: box(path),
                            primary: box(primary),
                            sequence: box(sequence),
                            keyObjects: box(keyObjects),
                            keyObjectsText: keyObjects?.innerText || '',
                            text: path?.innerText || '',
                            overflow: Math.ceil(
                              document.documentElement.scrollWidth - window.innerWidth
                            ),
                          };
                        }"""
                    )
                finally:
                    mobile.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert requested_urls
    assert all(url.startswith(f"{base_url}/") for url in requested_urls)
    assert desktop_state["path"] is not None
    assert desktop_state["primary"] is not None
    assert desktop_state["previous"] is not None
    assert desktop_state["current"] is not None
    assert desktop_state["next"] is not None
    assert desktop_state["primaryText"] == "Open selected page"
    assert "Reading path" in desktop_state["text"]
    assert "Return to the selected lesson" in desktop_state["text"]
    assert "Previous:" in desktop_state["previousText"]
    assert "Numbered Objects" in desktop_state["previousText"]
    assert "Selected:" in desktop_state["currentText"]
    assert "Projection Residuals" in desktop_state["currentText"]
    assert "Next:" in desktop_state["nextText"]
    assert "Authoring Matrix Fixture" in desktop_state["nextText"]
    assert "Find in search" in desktop_state["secondaryText"]
    assert "Focus neighborhood" in desktop_state["secondaryText"]
    assert desktop_state["keyObjects"] is not None
    assert "Key objects" in desktop_state["keyObjectsText"]
    assert any(
        link["text"].startswith("Definition 4.1")
        for link in desktop_state["keyObjectLinks"]
    )
    assert any("Proof" in link["text"] for link in desktop_state["keyObjectLinks"])
    assert all(
        link["href"].startswith("../../reader-ux/index.html#")
        for link in desktop_state["keyObjectLinks"]
    )
    assert all(link["width"] <= 360 for link in desktop_state["keyObjectLinks"])
    assert "recommend" not in desktop_state["text"].lower()
    assert "progress" not in desktop_state["text"].lower()
    assert "mastery" not in desktop_state["text"].lower()
    assert desktop_state["storage"] == [[], []]
    assert desktop_state["overflow"] <= 1

    assert mobile_state["path"] is not None
    assert mobile_state["primary"] is not None
    assert mobile_state["sequence"] is not None
    assert mobile_state["keyObjects"] is not None
    assert "Reading path" in mobile_state["text"]
    assert "Key objects" in mobile_state["keyObjectsText"]
    assert mobile_state["primary"]["width"] <= 390
    assert mobile_state["sequence"]["width"] <= 390
    assert mobile_state["keyObjects"]["width"] <= 390
    assert mobile_state["overflow"] <= 1


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
    assert "Review states" in gallery_html
    assert "gallery-review-grid" in gallery_html
    assert "../courses/minimal/artifact/site/index.html" in gallery_html
    assert "../courses/minimal/artifact/site/_raya/inspect/index.html" in gallery_html
    assert (
        "../courses/execution-fixture/artifact/site/_raya/inspect/index.html"
        in gallery_html
    )
    assert "@media (max-width: 720px)" in gallery_html
    assert "overflow-wrap: anywhere" in gallery_html
    assert "<script" not in gallery_html
    assert "<iframe" not in gallery_html
    assert "https://" not in gallery_html
    assert "http://" not in gallery_html
    assert "progress" not in gallery_html.lower()
    assert "mastery" not in gallery_html.lower()


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


def test_discovery_workspace_guides_are_visible_without_overflow(
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
                    {"width": 1366, "height": 900},
                    {"width": 768, "height": 1024},
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    try:
                        kind_to_results_id = {
                            "search": "raya-search-results-panel",
                            "practice": "raya-practice-results-panel",
                            "tasks": "raya-tasks-results-panel",
                            "schedule": "raya-schedule-results-panel",
                        }
                        for workspace_path, kind in (
                            ("_raya/search/index.html", "search"),
                            ("_raya/practice/index.html", "practice"),
                            ("_raya/tasks/index.html", "tasks"),
                            ("_raya/schedule/index.html", "schedule"),
                        ):
                            page.goto(
                                f"{base_url}/{workspace_path}",
                                wait_until="networkidle",
                            )
                            _assert_no_horizontal_overflow(page)
                            guide = page.locator(
                                f'[data-raya-discovery-guide="{kind}"]'
                            )
                            assert guide.is_visible()
                            assert (
                                guide.evaluate("node => node.tagName.toLowerCase()")
                                == "details"
                            )
                            assert guide.evaluate("node => node.open") is False
                            summary = guide.locator("summary")
                            assert summary.is_visible()
                            workspace = page.locator(
                                {
                                    "search": ".raya-search-workspace",
                                    "practice": ".raya-practice-workspace",
                                    "tasks": ".raya-tasks-workspace",
                                    "schedule": ".raya-schedule-workspace",
                                }[kind]
                            )
                            workspace_box = workspace.bounding_box()
                            assert workspace_box is not None
                            assert workspace_box["y"] < viewport["height"] * 0.72
                            if viewport["width"] < 520:
                                jump = page.locator(".raya-discovery-results-jump a")
                                assert jump.is_visible()
                                assert jump.evaluate("node => new URL(node.href).hash") == (
                                    f"#{kind_to_results_id[kind]}"
                                )
                                jump.click()
                                assert page.locator(
                                    f"#{kind_to_results_id[kind]}"
                                ).evaluate("node => document.activeElement === node")
                                _assert_intersects_viewport(
                                    page, f"#{kind_to_results_id[kind]}"
                                )
                            else:
                                assert (
                                    page.locator(".raya-discovery-results-jump a")
                                    .first
                                    .is_visible()
                                    is False
                                )
                            guide_box = guide.bounding_box()
                            assert guide_box is not None
                            assert workspace_box["y"] < guide_box["y"]
                            summary.click()
                            assert guide.evaluate("node => node.open") is True
                            box = guide.bounding_box()
                            assert box is not None
                            assert box["x"] >= 0
                            assert box["x"] + box["width"] <= viewport["width"] + 1
                            cards = guide.locator(".raya-discovery-guide-card")
                            assert (
                                cards.count() == 4
                            )
                            for index in range(cards.count()):
                                card_box = cards.nth(index).bounding_box()
                                assert card_box is not None
                                assert card_box["width"] > 0
                                assert card_box["height"] > 0
                                assert card_box["x"] >= box["x"] - 1
                                assert (
                                    card_box["x"] + card_box["width"]
                                    <= box["x"] + box["width"] + 1
                                )
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_discovery_command_bar_marks_current_workspace_without_overflow(
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
                    {"width": 1366, "height": 900},
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    try:
                        for workspace_path, kind, label in (
                            ("_raya/search/index.html", "search", "Search"),
                            ("_raya/graph/index.html", "graph", "Graph"),
                            ("_raya/practice/index.html", "practice", "Practice"),
                            ("_raya/tasks/index.html", "tasks", "Tasks"),
                            ("_raya/schedule/index.html", "schedule", "Schedule"),
                        ):
                            page.goto(
                                f"{base_url}/{workspace_path}",
                                wait_until="networkidle",
                            )
                            _assert_no_horizontal_overflow(page)
                            current = page.locator(
                                '.raya-discovery-command-bar '
                                '.raya-command[aria-current="page"]'
                            )
                            assert current.count() == 1
                            assert (
                                current.get_attribute("data-raya-current-workspace")
                                == kind
                            )
                            assert label in current.inner_text()
                            box = current.bounding_box()
                            assert box is not None
                            assert box["width"] > 0
                            assert box["x"] >= 0
                            assert box["x"] + box["width"] <= viewport["width"] + 1
                            contrast = current.evaluate(
                                """element => {
                                    const parseRgb = value => {
                                        const match = value.match(/rgba?\\(([^)]+)\\)/);
                                        if (!match) return null;
                                        return match[1].split(",").slice(0, 3).map(
                                            part => Number.parseFloat(part.trim())
                                        );
                                    };
                                    const linear = channel => {
                                        const normalized = channel / 255;
                                        return normalized <= 0.03928
                                            ? normalized / 12.92
                                            : Math.pow((normalized + 0.055) / 1.055, 2.4);
                                    };
                                    const luminance = rgb =>
                                        0.2126 * linear(rgb[0]) +
                                        0.7152 * linear(rgb[1]) +
                                        0.0722 * linear(rgb[2]);
                                    const style = window.getComputedStyle(element);
                                    const foreground = parseRgb(style.color);
                                    const background = parseRgb(style.backgroundColor);
                                    if (!foreground || !background) return 0;
                                    const light = Math.max(
                                        luminance(foreground),
                                        luminance(background)
                                    );
                                    const dark = Math.min(
                                        luminance(foreground),
                                        luminance(background)
                                    );
                                    return (light + 0.05) / (dark + 0.05);
                                }"""
                            )
                            assert contrast >= 4.5
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()


def test_discovery_workspaces_render_static_course_rail_without_storage(
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
                    {"width": 1366, "height": 900},
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    requested_urls: list[str] = []
                    page.on(
                        "request",
                        lambda request: requested_urls.append(request.url),
                    )
                    try:
                        for workspace_path, kind, label in (
                            ("_raya/search/index.html", "search", "Search"),
                            ("_raya/graph/index.html", "graph", "Graph"),
                            ("_raya/practice/index.html", "practice", "Practice"),
                            ("_raya/tasks/index.html", "tasks", "Tasks"),
                            ("_raya/schedule/index.html", "schedule", "Schedule"),
                        ):
                            requested_urls.clear()
                            page.goto(
                                f"{base_url}/{workspace_path}",
                                wait_until="networkidle",
                            )
                            _assert_no_horizontal_overflow(page)
                            assert not any(
                                (
                                    url.startswith("http://")
                                    or url.startswith("https://")
                                )
                                and not url.startswith(base_url)
                                for url in requested_urls
                            )
                            rail = page.locator("[data-raya-discovery-course-rail]")
                            assert rail.is_visible()
                            current = rail.locator('[aria-current="page"]')
                            assert current.count() == 1
                            assert (
                                current.get_attribute("data-raya-workspace-link")
                                == kind
                            )
                            assert label in current.inner_text()
                            badge_text = " ".join(
                                rail.locator(
                                    ".raya-discovery-workspace-link em"
                                ).all_inner_texts()
                            ).lower()
                            for expected_badge in (
                                "pages",
                                "links",
                                "official",
                                "tasks",
                                "dated",
                            ):
                                assert expected_badge in badge_text
                            assert (
                                rail.locator(".raya-discovery-course-page-link").count()
                                >= 5
                            )
                            hrefs = rail.locator("a[href]").evaluate_all(
                                "links => links.map(link => link.getAttribute('href'))"
                            )
                            assert all(
                                href and not href.startswith("/") for href in hrefs
                            )
                            assert all("_official/" not in href for href in hrefs)
                            assert all("_drafts/" not in href for href in hrefs)
                            assert all("_partials/" not in href for href in hrefs)
                            assert page.evaluate("() => localStorage.length") == 0
                            assert page.evaluate("() => sessionStorage.length") == 0
                            if viewport["width"] >= 1000:
                                toggle = page.locator(
                                    "[data-raya-discovery-toggle-rail]"
                                )
                                assert toggle.is_visible()
                                page.wait_for_function(
                                    """() => document.querySelector('[data-raya-discovery-page]')
                                      ?.getAttribute('data-raya-discovery-rail-state') === 'expanded'"""
                                )
                                toggle.click()
                                page.wait_for_function(
                                    """() => document.querySelector('[data-raya-discovery-page]')
                                      ?.getAttribute('data-raya-discovery-rail-state') === 'collapsed'"""
                                )
                                assert (
                                    rail.locator(
                                        "[data-raya-discovery-course-rail-body]"
                                    ).get_attribute("aria-hidden")
                                    == "true"
                                )
                                assert rail.locator(
                                    ".raya-discovery-course-tab"
                                ).is_visible()
                                assert page.evaluate("() => localStorage.length") == 0
                                assert page.evaluate("() => sessionStorage.length") == 0
                                page.set_viewport_size({"width": 390, "height": 844})
                                page.wait_for_function(
                                    """() => document.querySelector('[data-raya-discovery-page]')
                                      ?.getAttribute('data-raya-discovery-rail-state') === 'expanded'"""
                                )
                                assert (
                                    rail.locator(
                                        "[data-raya-discovery-course-rail-body]"
                                    ).get_attribute("aria-hidden")
                                    == "false"
                                )
                                assert (
                                    rail.locator(
                                        ".raya-discovery-course-page-link"
                                    ).first.get_attribute("tabindex")
                                    != "-1"
                                )
                                assert toggle.is_visible() is False
                                page.set_viewport_size(viewport)
                                page.wait_for_function(
                                    """() => document.querySelector('[data-raya-discovery-page]')
                                      ?.getAttribute('data-raya-discovery-rail-state') === 'expanded'"""
                                )
                                toggle.click()
                                page.wait_for_function(
                                    """() => document.querySelector('[data-raya-discovery-page]')
                                      ?.getAttribute('data-raya-discovery-rail-state') === 'collapsed'"""
                                )
                                toggle.click()
                                page.wait_for_function(
                                    """() => document.querySelector('[data-raya-discovery-page]')
                                      ?.getAttribute('data-raya-discovery-rail-state') === 'expanded'"""
                                )
                                assert (
                                    rail.locator(
                                        "[data-raya-discovery-course-rail-body]"
                                    ).get_attribute("aria-hidden")
                                    == "false"
                                )
                            else:
                                assert (
                                    page.locator(
                                        "[data-raya-discovery-toggle-rail]"
                                    ).is_visible()
                                    is False
                                )
                        page.goto(
                            f"{base_url}/_raya/search/index.html?page=reader-ux",
                            wait_until="networkidle",
                        )
                        page.wait_for_function(
                            """() => document.querySelector('[data-raya-discovery-page]')
                              ?.getAttribute('data-raya-discovery-rail-state') === 'expanded'"""
                        )
                        focused = page.locator(
                            '[data-raya-discovery-course-page="reader-ux"]'
                        )
                        assert focused.get_attribute("data-raya-rail-page-focus") == "true"
                        focus_notice = page.locator(
                            "[data-raya-discovery-rail-page-focus]"
                        )
                        assert focus_notice.is_visible()
                        assert "Projection Residuals" in focus_notice.inner_text()
                        handoffs = page.locator(
                            "[data-raya-discovery-rail-page-handoffs] a"
                        )
                        assert handoffs.count() == 5
                        assert all(
                            "page=reader-ux"
                            in href
                            for href in handoffs.evaluate_all(
                                "links => links.map(link => link.getAttribute('href'))"
                            )
                        )
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
    for selector, minimum in (
        (".gallery-card", 6),
        (".gallery-review-card", 4),
    ):
        cards = page.locator(selector)
        boxes = [cards.nth(index).bounding_box() for index in range(cards.count())]
        visible_boxes = [box for box in boxes if box is not None]
        assert len(visible_boxes) >= minimum
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
