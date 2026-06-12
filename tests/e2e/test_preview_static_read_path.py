from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

import pytest

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

    assert '<header class="raya-site-header">' in root_html
    assert '<main id="raya-content" class="raya-main">' in root_html
    assert '<article class="raya-article">' in root_html
    assert '<aside class="raya-support-stack" aria-label="Resource status">' in root_html
    assert root_html.index('<article class="raya-article">') < root_html.index(
        '<aside class="raya-support-stack"'
    )
    assert "SHA-256" not in root_html
    assert "Source path" not in root_html
    assert "SHA-256" in inspection_html
    assert "Artifact path" in inspection_html
    assert '<main class="raya-inspection-main">' in inspection_html
    assert ".raya-main" in css
    assert "grid-template-columns" in css
    assert "@media (max-width: 720px)" in css
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
                                "article.raya-article",
                                "aside.raya-support-stack",
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


def test_render_fixture_math_is_visible_and_uses_only_local_assets(
    tmp_path: Path,
) -> None:
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
                for viewport in (
                    {"width": 1280, "height": 900},
                    {"width": 390, "height": 844},
                ):
                    page = browser.new_page(viewport=viewport)
                    page.on(
                        "request",
                        lambda request: _record_external_request(
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
                        assert "a^2 + b^2 = c^2" not in visible_text
                        assert "\\rayaVec" not in visible_text
                        assert "\\argmax" not in visible_text
                        if debug_dir is not None:
                            _capture_render_debug_artifact(
                                page,
                                debug_dir=debug_dir,
                                page_name="index",
                                viewport_name=_viewport_name(viewport),
                                viewport=viewport,
                                external_requests=external_requests,
                            )

                        page.goto(
                            f"{base_url}/static-path/index.html",
                            wait_until="networkidle",
                        )
                        _assert_no_horizontal_overflow(page)
                        _assert_visible_mathjax_output(page, minimum=2)
                        if debug_dir is not None:
                            _capture_render_debug_artifact(
                                page,
                                debug_dir=debug_dir,
                                page_name="static-path",
                                viewport_name=_viewport_name(viewport),
                                viewport=viewport,
                                external_requests=external_requests,
                            )
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert external_requests == []


def test_render_fixture_debug_artifacts_are_written_when_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    debug_dir = tmp_path / "renderer-debug"
    monkeypatch.setenv("RAYA_RENDER_DEBUG_DIR", str(debug_dir))
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
                page = browser.new_page(viewport={"width": 390, "height": 844})
                page.on(
                    "request",
                    lambda request: _record_external_request(
                        request.url,
                        base_url,
                        external_requests,
                    ),
                )
                try:
                    page.goto(f"{base_url}/index.html", wait_until="networkidle")
                    _assert_no_horizontal_overflow(page)
                    _assert_visible_mathjax_output(page, minimum=6)
                    _capture_render_debug_artifact(
                        page,
                        debug_dir=debug_dir,
                        page_name="index",
                        viewport_name="mobile",
                        viewport={"width": 390, "height": 844},
                        external_requests=external_requests,
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    screenshot = debug_dir / "mobile-index.png"
    summary_path = debug_dir / "summary.json"
    assert screenshot.is_file()
    assert screenshot.stat().st_size > 0
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["captures"][0]["page"] == "index"
    assert summary["captures"][0]["viewport"]["name"] == "mobile"
    assert summary["captures"][0]["mathjax_container_count"] >= 6
    assert summary["captures"][0]["raw_tex_visible"] is False
    assert summary["captures"][0]["horizontal_overflow"] <= 1
    assert summary["captures"][0]["external_requests"] == []
    assert summary["captures"][0]["screenshot"].endswith("mobile-index.png")


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


def _assert_no_overlap(page, first_selector: str, second_selector: str) -> None:
    first = page.locator(first_selector).bounding_box()
    second = page.locator(second_selector).bounding_box()
    assert first is not None
    assert second is not None
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


def _capture_render_debug_artifact(
    page,
    *,
    debug_dir: Path,
    page_name: str,
    viewport_name: str,
    viewport: dict[str, int],
    external_requests: list[str],
) -> None:
    debug_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = debug_dir / f"{viewport_name}-{page_name}.png"
    page.screenshot(path=str(screenshot_path), full_page=True)
    visible_text = page.locator("body").inner_text()
    overflow = page.evaluate(
        "() => Math.ceil(document.documentElement.scrollWidth - window.innerWidth)"
    )
    capture = {
        "page": page_name,
        "url": page.url,
        "viewport": {
            "name": viewport_name,
            "width": viewport["width"],
            "height": viewport["height"],
        },
        "screenshot": str(screenshot_path),
        "mathjax_container_count": page.locator("mjx-container").count(),
        "raw_tex_visible": any(
            token in visible_text
            for token in ("\\rayaVec", "\\argmax", "a^2 + b^2 = c^2")
        ),
        "external_requests": sorted(set(external_requests)),
        "horizontal_overflow": overflow,
    }
    summary_path = debug_dir / "summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    else:
        summary = {"captures": []}
    summary["captures"].append(capture)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _viewport_name(viewport: dict[str, int]) -> str:
    if viewport["width"] <= 720:
        return "mobile"
    return "desktop"


def _record_external_request(url: str, base_url: str, requests: list[str]) -> None:
    if not url.startswith(base_url):
        requests.append(url)


def _boxes_overlap(first: dict[str, float], second: dict[str, float]) -> bool:
    return not (
        first["x"] + first["width"] <= second["x"]
        or second["x"] + second["width"] <= first["x"]
        or first["y"] + first["height"] <= second["y"]
        or second["y"] + second["height"] <= first["y"]
    )
