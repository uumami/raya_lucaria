from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

from raya_cli.render_debug_report import inspect_render_debug
from raya_schema import ValidationReport


RENDER_DEBUG_PAGE_NAMES = (
    "index",
    "static-path",
    "math-authoring",
    "numbered-objects",
    "reader-ux",
)
_RENDER_DEBUG_CLEANUP_PAGE_NAMES = RENDER_DEBUG_PAGE_NAMES + ("3_numbered_objects",)
RENDER_DEBUG_VIEWPORTS = (
    {"width": 1280, "height": 900},
    {"width": 390, "height": 844},
)
RENDER_RAW_TEX_MARKERS = (
    "\\rayaVec",
    "\\argmax",
    "\\renewcommand",
    "\\fixtureUnit",
    "\\vect",
    "\\ip",
    "\\orthproj",
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
    if not _reset_render_debug_dir(debug_dir, report):
        return report

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

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
        except Exception as exc:
            report.add_error(
                "Could not launch Chromium-compatible browser",
                path=browser_executable,
                next_action=(
                    "Use the reference Docker workflow or set "
                    f"RAYA_TEST_BROWSER to a working Chromium executable ({exc})"
                ),
            )
            return report
        try:
            for viewport in RENDER_DEBUG_VIEWPORTS:
                for page_name in _available_page_names(site_root):
                    external_requests: list[str] = []
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
                        try:
                            capture = _capture_render_debug_artifact(
                                page,
                                page_url=_page_url(base_url, page_name),
                                debug_dir=debug_dir,
                                page_name=page_name,
                                viewport_name=viewport_name(viewport),
                                viewport=viewport,
                                external_requests=external_requests,
                            )
                        except Exception as exc:
                            report.add_error(
                                "Renderer debug browser inspection failed",
                                path=debug_dir,
                                field=_page_url(base_url, page_name),
                                next_action=(
                                    "Inspect the generated site, browser path, "
                                    f"and render debug output directory ({exc})"
                                ),
                            )
                            continue
                        _add_capture_diagnostics(report, debug_dir, capture)
                    finally:
                        try:
                            page.close()
                        except Exception:
                            pass
        finally:
            browser.close()

    inspection = inspect_render_debug(site_dir=site_root, debug_dir=debug_dir)
    report.wrote_output(debug_dir / "summary.json")
    report.wrote_output(debug_dir / "report.json")
    report.wrote_output(debug_dir / "index.html")
    if not inspection["ok"]:
        for diagnostic in inspection["diagnostics"]:
            report.add_error(
                diagnostic["message"],
                path=Path(diagnostic["path"]),
                next_action=diagnostic.get("next_action"),
            )
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
    if (site_root / "math-authoring" / "index.html").is_file():
        page_names.append("math-authoring")
    if (site_root / "numbered-objects" / "index.html").is_file():
        page_names.append("numbered-objects")
    elif (site_root / "3_numbered_objects" / "index.html").is_file():
        page_names.append("3_numbered_objects")
    if (site_root / "reader-ux" / "index.html").is_file():
        page_names.append("reader-ux")
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
    visible_text = _visible_non_code_text(page)
    raw_tex_markers = raw_tex_markers_from_text(visible_text)
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
        "numbered_content": _numbered_content_evidence(page),
        "staticEnvironments": _static_environment_evidence(page),
    }
    _append_summary(debug_dir / "summary.json", capture)
    return capture


def _visible_non_code_text(page: Any) -> str:
    return page.evaluate(
        """() => {
            const clone = document.body.cloneNode(true);
            clone.querySelectorAll('code, pre, kbd, samp, script, style, textarea')
              .forEach((node) => node.remove());
            return clone.innerText || '';
        }"""
    )


def _numbered_content_evidence(page: Any) -> dict[str, object]:
    return page.evaluate(
        """() => {
            const objects = Array.from(document.querySelectorAll('.raya-numbered-object'))
              .map((node) => ({
                id: node.getAttribute('data-object-id') || '',
                family: Array.from(node.classList)
                  .find((name) => name.startsWith('raya-numbered-object--') &&
                    !['raya-numbered-object--margin', 'raya-numbered-object--banded',
                      'raya-numbered-object--scannable',
                      'raya-numbered-object--caption', 'raya-numbered-object--equation']
                      .includes(name))
                  ?.replace('raya-numbered-object--', '') || '',
                anchor: node.id || '',
                label: node.querySelector('.raya-numbered-object-reference')?.innerText || '',
                title: node.querySelector('.raya-numbered-object-title')?.innerText || '',
                text: node.innerText || '',
              }));
            const references = Array.from(document.querySelectorAll('a[href*="raya-object-"]'))
              .map((node) => ({
                text: node.innerText || '',
                href: node.getAttribute('href') || '',
              }));
            const proofs = Array.from(document.querySelectorAll('.raya-proof'))
              .map((node) => {
                const reference = node.querySelector('.raya-proof-reference')?.innerText || '';
                const targetText = reference.startsWith('Proof of ')
                  ? reference.slice('Proof of '.length).replace(/\\.$/, '')
                  : '';
                return {
                  id: node.id || '',
                  heading: node.querySelector('.raya-proof-heading')?.innerText || '',
                  target_text: targetText,
                  target_id: '',
                };
              });
            return {objects, references, proofs};
        }"""
    )


def _static_environment_evidence(page: Any) -> list[dict[str, str]]:
    return page.evaluate(
        """() => {
            const staticEnvironments = Array.from(document.querySelectorAll('.raya-static-environment'))
              .map((node) => ({
                id: node.id || '',
                className: node.className || '',
                heading: node.querySelector('.raya-static-environment-heading')?.innerText || '',
                text: node.innerText || '',
              }));
            return staticEnvironments;
        }"""
    )


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


def _reset_render_debug_dir(debug_dir: Path, report: ValidationReport) -> bool:
    try:
        debug_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        report.add_error(
            "Renderer debug output directory cannot be created",
            path=debug_dir,
            next_action=f"Choose a writable --render-debug directory ({exc})",
        )
        return False
    for path in debug_dir.iterdir():
        if (
            path.name in {"summary.json", "report.json", "index.html"}
            or path.name in _render_debug_screenshot_names()
        ):
            if path.is_file() or path.is_symlink():
                path.unlink()
                continue
            report.add_error(
                "Renderer debug output path blocks screenshot cleanup",
                path=path,
                next_action=(
                    "Remove the blocking directory or choose a fresh "
                    "--render-debug directory"
                ),
            )
            return False
    return True


def _render_debug_screenshot_names() -> set[str]:
    return {
        f"{viewport_name(viewport)}-{page_name}.png"
        for viewport in RENDER_DEBUG_VIEWPORTS
        for page_name in _RENDER_DEBUG_CLEANUP_PAGE_NAMES
    }


def raw_tex_markers_from_text(visible_text: str) -> list[str]:
    markers: list[str] = []
    for marker in RENDER_RAW_TEX_MARKERS:
        if marker in visible_text:
            markers.append(marker)
    dollar_pattern = r"(?<!\\)(\${1,2})(?!\s)([^$\n]{1,200}?)(?<!\s)\1"
    for match in re.finditer(dollar_pattern, visible_text):
        candidate = match.group(0)
        if _looks_like_math_payload(match.group(2)) and candidate not in markers:
            markers.append(candidate)
    for match in re.finditer(r"\\[A-Za-z]+(?=[\s{(\[])", visible_text):
        candidate = match.group(0)
        if candidate not in markers:
            markers.append(candidate)
    return markers


def _looks_like_math_payload(payload: str) -> bool:
    return bool(re.search(r"[\\^_={}]", payload))


def viewport_name(viewport: dict[str, int]) -> str:
    if viewport["width"] <= 720:
        return "mobile"
    return "desktop"


def record_external_request(url: str, base_url: str, requests: list[str]) -> None:
    if not url.startswith(base_url):
        requests.append(url)
