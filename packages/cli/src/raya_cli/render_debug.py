from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

from raya_schema import ValidationReport


RENDER_DEBUG_PAGE_NAMES = ("index", "static-path")
RENDER_DEBUG_VIEWPORTS = (
    {"width": 1280, "height": 900},
    {"width": 390, "height": 844},
)
RENDER_RAW_TEX_MARKERS = (
    "\\rayaVec",
    "\\argmax",
    "\\renewcommand",
    "\\fixtureUnit",
    "\\begin{bmatrix}",
    "a^2 + b^2 = c^2",
)


def capture_render_debug(
    *,
    base_url: str,
    site_dir: str | Path,
    output_dir: str | Path,
) -> ValidationReport:
    report = ValidationReport(context="preview")
    site_root = Path(site_dir)
    debug_dir = Path(output_dir)
    _reset_render_debug_dir(debug_dir)

    browser_executable = _browser_executable(report)
    if browser_executable is None:
        return report

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        report.add_error(
            "Playwright is required for renderer debug capture",
            path=debug_dir,
            next_action=(
                "Install dev dependencies with uv sync --all-packages --dev "
                "or use ./scripts/check-docker.sh"
            ),
        )
        return report

    external_requests: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=str(browser_executable),
            headless=True,
            args=["--no-sandbox"],
        )
        try:
            for viewport in RENDER_DEBUG_VIEWPORTS:
                for page_name in _available_page_names(site_root):
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
                        capture = _capture_render_debug_artifact(
                            page,
                            page_url=_page_url(base_url, page_name),
                            debug_dir=debug_dir,
                            page_name=page_name,
                            viewport_name=_viewport_name(viewport),
                            viewport=viewport,
                            external_requests=external_requests,
                        )
                        _add_capture_diagnostics(report, debug_dir, capture)
                    finally:
                        page.close()
        finally:
            browser.close()

    report.wrote_output(debug_dir / "summary.json")
    for screenshot in debug_dir.glob("*.png"):
        report.wrote_output(screenshot)
    if report.ok:
        report.add_info(
            "Renderer debug artifacts written",
            path=debug_dir,
            next_action=f"Inspect screenshots and summary={debug_dir / 'summary.json'}",
        )
    return report


def _available_page_names(site_root: Path) -> list[str]:
    page_names = ["index"]
    if (site_root / "static-path" / "index.html").is_file():
        page_names.append("static-path")
    return page_names


def _page_url(base_url: str, page_name: str) -> str:
    if page_name == "index":
        return f"{base_url}/index.html"
    return f"{base_url}/{page_name}/index.html"


def _browser_executable(report: ValidationReport) -> Path | None:
    configured = os.environ.get("RAYA_TEST_BROWSER")
    if configured:
        path = Path(configured)
        if path.exists():
            return path
        report.add_error(
            "Configured Chromium-compatible browser does not exist",
            path=path,
            field="RAYA_TEST_BROWSER",
            next_action=(
                "Set RAYA_TEST_BROWSER to an existing Chromium-compatible executable"
            ),
        )
        return None

    for name in (
        "chromium",
        "chromium-browser",
        "google-chrome-stable",
        "google-chrome",
    ):
        resolved = shutil.which(name)
        if resolved is not None:
            return Path(resolved)
    report.add_error(
        "A Chromium-compatible browser is required for renderer debug capture",
        next_action=(
            "Use the reference Docker workflow or set "
            "RAYA_TEST_BROWSER=/path/to/browser"
        ),
    )
    return None


def _capture_render_debug_artifact(
    page: Any,
    *,
    page_url: str,
    debug_dir: Path,
    page_name: str,
    viewport_name: str,
    viewport: dict[str, int],
    external_requests: list[str],
) -> dict[str, object]:
    page.goto(page_url, wait_until="networkidle")
    screenshot_path = debug_dir / f"{viewport_name}-{page_name}.png"
    page.screenshot(path=str(screenshot_path), full_page=True)
    visible_text = page.locator("body").inner_text()
    raw_tex_markers = _raw_tex_markers(visible_text)
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
        "raw_tex_visible": bool(raw_tex_markers),
        "raw_tex_markers": raw_tex_markers,
        "external_requests": sorted(set(external_requests)),
        "horizontal_overflow": overflow,
    }
    _append_summary(debug_dir / "summary.json", capture)
    return capture


def _append_summary(summary_path: Path, capture: dict[str, object]) -> None:
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    else:
        summary = {"captures": []}
    summary["captures"].append(capture)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _add_capture_diagnostics(
    report: ValidationReport,
    debug_dir: Path,
    capture: dict[str, object],
) -> None:
    if capture["raw_tex_visible"]:
        report.add_error(
            "Renderer debug found visible raw TeX",
            path=debug_dir,
            field=str(capture["page"]),
            next_action=(
                f"Inspect {capture['screenshot']} and fix build-time math diagnostics"
            ),
        )
    if capture["external_requests"]:
        report.add_error(
            "Renderer debug found external requests",
            path=debug_dir,
            field=str(capture["page"]),
            next_action="Keep renderer support files local under artifact/site/_raya/",
        )


def _reset_render_debug_dir(debug_dir: Path) -> None:
    debug_dir.mkdir(parents=True, exist_ok=True)
    for path in debug_dir.iterdir():
        if path.name == "summary.json" or path.name in _render_debug_screenshot_names():
            path.unlink()


def _render_debug_screenshot_names() -> set[str]:
    return {
        f"{_viewport_name(viewport)}-{page_name}.png"
        for viewport in RENDER_DEBUG_VIEWPORTS
        for page_name in RENDER_DEBUG_PAGE_NAMES
    }


def _raw_tex_markers(visible_text: str) -> list[str]:
    return [marker for marker in RENDER_RAW_TEX_MARKERS if marker in visible_text]


def _viewport_name(viewport: dict[str, int]) -> str:
    if viewport["width"] <= 720:
        return "mobile"
    return "desktop"


def _record_external_request(url: str, base_url: str, requests: list[str]) -> None:
    if not url.startswith(base_url):
        requests.append(url)
