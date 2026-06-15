from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


RENDER_DEBUG_VIEWPORT_NAMES = ("desktop", "mobile")
BLOCKED_RENDERER_FRAGMENTS = (
    "mathjax.js",
    "tex-chtml",
    "tex-svg",
    "mml-chtml",
    "tex-mml-chtml",
    "startup.js",
    "cdn.jsdelivr.net",
    "unpkg.com",
    "cdnjs.cloudflare.com",
    "polyfill.io",
    "https://cdn",
    "http://cdn",
)
LOCAL_MATHJAX_SCRIPT_RE = re.compile(
    r"_raya/render/math/[^\"')\s>]+\.js\b",
    re.IGNORECASE,
)
CSS_URL_RE = re.compile(r"url\(\s*(?P<value>[^)]*?)\s*\)")


def inspect_render_debug(
    site_dir: str | Path,
    debug_dir: str | Path,
    copied_site_dir: str | Path | None = None,
) -> dict[str, Any]:
    site_root = Path(site_dir)
    debug_root = Path(debug_dir)
    copied_site_root = Path(copied_site_dir) if copied_site_dir is not None else None
    summary_path = debug_root / "summary.json"
    html_report_path = debug_root / "index.html"
    report: dict[str, Any] = {
        "ok": True,
        "site_dir": str(site_root),
        "copied_site_dir": str(copied_site_root) if copied_site_root else None,
        "summary_path": str(summary_path),
        "html_report_path": str(html_report_path),
        "checks": [],
        "diagnostics": [],
    }

    summary = _read_summary(summary_path, report)
    captures = _capture_items(summary, summary_path, report)
    _inspect_captures(site_root, debug_root, captures, report)
    _inspect_static_site(site_root, report, context="site")
    if copied_site_root is not None:
        _inspect_copied_site(site_root, copied_site_root, report)

    report["ok"] = not report["diagnostics"]
    write_render_debug_report(debug_root, report)
    return report


def copy_static_site(site_dir: str | Path, destination: str | Path) -> Path:
    source = Path(site_dir)
    target = Path(destination)
    source_resolved = source.resolve()
    target_resolved = target.resolve()
    if target_resolved == source_resolved:
        raise ValueError("static site copy destination must differ from source")
    try:
        target_resolved.relative_to(source_resolved)
    except ValueError:
        pass
    else:
        raise ValueError("static site copy destination must not be inside source")
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    return target


def write_render_debug_report(debug_dir: str | Path, report: dict[str, Any]) -> None:
    debug_root = Path(debug_dir)
    debug_root.mkdir(parents=True, exist_ok=True)
    json_path = debug_root / "report.json"
    html_path = debug_root / "index.html"
    report["html_report_path"] = str(html_path)
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    html_path.write_text(_render_html_report(report), encoding="utf-8")


def _read_summary(summary_path: Path, report: dict[str, Any]) -> dict[str, Any]:
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception as exc:
        _add_check(
            report,
            check_id="summary:read",
            status="fail",
            path=summary_path,
            message=f"missing or malformed summary.json at {summary_path}: {exc}",
            next_action="Run raya preview with --render-debug before inspection.",
        )
        return {"captures": []}
    if not isinstance(summary, dict):
        _add_check(
            report,
            check_id="summary:read",
            status="fail",
            path=summary_path,
            message=f"summary.json must contain an object at {summary_path}",
            next_action="Regenerate render debug capture artifacts.",
        )
        return {"captures": []}
    _add_check(
        report,
        check_id="summary:read",
        status="pass",
        path=summary_path,
        message="summary.json is readable",
    )
    return summary


def _capture_items(
    summary: dict[str, Any],
    summary_path: Path,
    report: dict[str, Any],
) -> list[dict[str, Any]]:
    captures = summary.get("captures")
    if not isinstance(captures, list):
        _add_check(
            report,
            check_id="summary:captures",
            status="fail",
            path=summary_path,
            message=f"summary.json captures must be a list at {summary_path}",
            next_action="Regenerate render debug capture artifacts.",
        )
        return []

    valid_captures: list[dict[str, Any]] = []
    for capture in captures:
        if isinstance(capture, dict):
            valid_captures.append(capture)
            continue
        _add_check(
            report,
            check_id="summary:captures",
            status="fail",
            path=summary_path,
            message=f"summary.json capture must be an object: {capture!r}",
            next_action="Regenerate render debug capture artifacts.",
        )
    _add_check(
        report,
        check_id="summary:captures",
        status="pass" if len(valid_captures) == len(captures) else "fail",
        path=summary_path,
        message=f"summary.json contains {len(valid_captures)} capture(s)",
    )
    return valid_captures


def _inspect_captures(
    site_dir: Path,
    debug_dir: Path,
    captures: list[dict[str, Any]],
    report: dict[str, Any],
) -> None:
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    for capture in captures:
        page = capture.get("page")
        viewport = capture.get("viewport")
        viewport_name = viewport.get("name") if isinstance(viewport, dict) else None
        if isinstance(page, str) and isinstance(viewport_name, str):
            seen[(page, viewport_name)] = capture

    for page_name in _expected_page_names(site_dir):
        for viewport_name in RENDER_DEBUG_VIEWPORT_NAMES:
            check_id = f"capture:{page_name}:{viewport_name}"
            screenshot_name = f"{viewport_name}-{page_name}.png"
            capture = seen.get((page_name, viewport_name))
            if capture is None:
                _add_check(
                    report,
                    check_id=check_id,
                    status="fail",
                    path=debug_dir / screenshot_name,
                    message=(
                        f"missing expected capture page={page_name!r} "
                        f"viewport={viewport_name!r}"
                    ),
                    next_action="Regenerate render debug capture artifacts.",
                )
                continue

            failures = _capture_failures(capture, debug_dir, screenshot_name)
            _add_check(
                report,
                check_id=check_id,
                status="fail" if failures else "pass",
                path=debug_dir / screenshot_name,
                message=(
                    f"capture page={page_name!r} viewport={viewport_name!r} "
                    f"uses {screenshot_name}"
                ),
                next_action=(
                    "Inspect the screenshot and generated site output."
                    if failures
                    else None
                ),
                details={
                    "page": page_name,
                    "viewport": viewport_name,
                    "screenshot": screenshot_name,
                    "failures": failures,
                },
            )


def _capture_failures(
    capture: dict[str, Any],
    debug_dir: Path,
    screenshot_name: str,
) -> list[str]:
    failures: list[str] = []
    page = capture.get("page")
    viewport = capture.get("viewport")
    viewport_name = viewport.get("name") if isinstance(viewport, dict) else None
    screenshot = debug_dir / screenshot_name
    screenshot_value = capture.get("screenshot")
    if screenshot_value:
        declared_screenshot = Path(str(screenshot_value))
        if not declared_screenshot.is_absolute():
            declared_screenshot = debug_dir / declared_screenshot
        declared_screenshot = declared_screenshot.resolve()
        try:
            declared_screenshot.relative_to(debug_dir.resolve())
        except ValueError:
            failures.append(
                "screenshot path is outside debug directory "
                f"for page={page!r} viewport={viewport_name!r}: {declared_screenshot}"
            )
        if declared_screenshot.name != screenshot_name:
            failures.append(
                "unexpected screenshot for "
                f"page={page!r} viewport={viewport_name!r}: {declared_screenshot}"
            )
    if not screenshot.is_file() or screenshot.stat().st_size <= 0:
        failures.append(f"missing or empty screenshot {screenshot}")
    if capture.get("raw_tex_visible"):
        failures.append(
            f"visible raw TeX in capture page={page!r} viewport={viewport_name!r}"
        )
    external_requests = capture.get("external_requests")
    if external_requests:
        failures.append(
            "external requests in capture "
            f"page={page!r} viewport={viewport_name!r}: {external_requests}"
        )
    overflow = capture.get("horizontal_overflow", 0)
    if isinstance(overflow, (int, float)):
        if overflow > 1:
            failures.append(
                "horizontal overflow in capture "
                f"page={page!r} viewport={viewport_name!r}: {overflow}"
            )
    else:
        failures.append(
            "horizontal_overflow must be numeric in capture "
            f"page={page!r} viewport={viewport_name!r}"
        )
    return failures


def _inspect_static_site(
    site_dir: Path,
    report: dict[str, Any],
    *,
    context: str,
) -> None:
    html_paths = sorted(site_dir.rglob("*.html")) if site_dir.is_dir() else []
    check_prefix = f"{context}:html"
    if not html_paths:
        _add_check(
            report,
            check_id=f"{check_prefix}:present",
            status="fail",
            path=site_dir,
            message=f"no generated HTML found under {site_dir}",
            next_action="Build the static site before render debug inspection.",
        )
        return
    _add_check(
        report,
        check_id=f"{check_prefix}:present",
        status="pass",
        path=site_dir,
        message=f"found {len(html_paths)} HTML file(s) under {site_dir}",
    )

    math_present = False
    for html_path in html_paths:
        text = html_path.read_text(encoding="utf-8")
        text_lower = text.lower()
        math_present = math_present or "<mjx-container" in text_lower
        failures = _blocked_renderer_failures(text, html_path)
        _add_check(
            report,
            check_id=f"{check_prefix}:renderer:{_relative_id(site_dir, html_path)}",
            status="fail" if failures else "pass",
            path=html_path,
            message=f"renderer dependency inspection for {html_path}",
            next_action=(
                "Keep MathJax rendering at build time with local CSS and fonts."
                if failures
                else None
            ),
            details={"failures": failures},
        )

    if math_present:
        _inspect_local_mathjax_resources(site_dir, report, context=context)


def _inspect_copied_site(
    site_dir: Path,
    copied_site_dir: Path,
    report: dict[str, Any],
) -> None:
    if not copied_site_dir.is_dir():
        _add_check(
            report,
            check_id="copied-site:present",
            status="fail",
            path=copied_site_dir,
            message=f"copied static site is missing at {copied_site_dir}",
            next_action="Copy the generated site before copied-site inspection.",
        )
        return
    _add_check(
        report,
        check_id="copied-site:present",
        status="pass",
        path=copied_site_dir,
        message=f"copied static site exists at {copied_site_dir}",
    )
    for html_path in sorted(site_dir.rglob("*.html")) if site_dir.is_dir() else []:
        relative = html_path.relative_to(site_dir)
        copied_path = copied_site_dir / relative
        _add_check(
            report,
            check_id=f"copied-site:html:{_path_id(relative)}",
            status="pass" if copied_path.is_file() else "fail",
            path=copied_path,
            message=f"copied site includes {relative}",
            next_action=(
                "Refresh the copied static site from the generated site."
                if not copied_path.is_file()
                else None
            ),
        )
    _inspect_static_site(copied_site_dir, report, context="copied-site")


def _inspect_local_mathjax_resources(
    site_dir: Path,
    report: dict[str, Any],
    *,
    context: str,
) -> None:
    css_path = site_dir / "_raya" / "render" / "math" / "mathjax.css"
    if not css_path.is_file() or css_path.stat().st_size <= 0:
        _add_check(
            report,
            check_id=f"{context}:math:css",
            status="fail",
            path=css_path,
            message=f"missing local MathJax CSS at {css_path}",
            next_action="Rebuild the artifact so math CSS is copied under _raya/render/math/.",
        )
        return
    css = css_path.read_text(encoding="utf-8")
    font_failures = _mathjax_font_failures(css, css_path)
    _add_check(
        report,
        check_id=f"{context}:math:css",
        status="fail" if font_failures else "pass",
        path=css_path,
        message=f"local MathJax CSS and font references for {site_dir}",
        next_action=(
            "Rebuild the artifact so MathJax font files are local."
            if font_failures
            else None
        ),
        details={"failures": font_failures},
    )


def _mathjax_font_failures(css: str, css_path: Path) -> list[str]:
    failures: list[str] = []
    urls = [match.group("value").strip("\"' ") for match in CSS_URL_RE.finditer(css)]
    if not urls:
        failures.append(f"no local MathJax font URLs found in {css_path}")
    for url in urls:
        if re.match(r"^[a-z][a-z0-9+.-]*:", url, flags=re.IGNORECASE) or url.startswith(
            "//"
        ):
            failures.append(f"external MathJax font URL {url!r} in {css_path}")
            continue
        if url.startswith("/"):
            failures.append(f"root-relative MathJax font URL {url!r} in {css_path}")
            continue
        font_path = (css_path.parent / url).resolve()
        try:
            font_path.relative_to(css_path.parent.resolve())
        except ValueError:
            failures.append(f"MathJax font URL escapes math resource directory: {url!r}")
            continue
        if not font_path.is_file() or font_path.stat().st_size <= 0:
            failures.append(f"missing local MathJax font asset {font_path}")
    return failures


def _blocked_renderer_failures(text: str, html_path: Path) -> list[str]:
    parser = _RendererResourceParser()
    parser.feed(text)
    parser.close()
    candidates = parser.resource_values
    failures: list[str] = []
    for candidate in candidates:
        candidate_lower = candidate.lower()
        for fragment in BLOCKED_RENDERER_FRAGMENTS:
            if fragment in candidate_lower:
                failures.append(
                    "browser-side or external renderer dependency "
                    f"{fragment!r} in {html_path}"
                )
        if LOCAL_MATHJAX_SCRIPT_RE.search(candidate_lower):
            failures.append(
                "browser-side or external renderer dependency "
                f"'_raya/render/math/*.js' in {html_path}"
            )
    return failures


class _RendererResourceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.resource_values: list[str] = []
        self._in_inline_script = False

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = {name.lower(): value or "" for name, value in attrs}
        tag_lower = tag.lower()
        if tag_lower == "script":
            src = attributes.get("src")
            if src:
                self.resource_values.append(src)
                return
            self._in_inline_script = True
        elif tag_lower == "link":
            href = attributes.get("href")
            if href:
                self.resource_values.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script":
            self._in_inline_script = False

    def handle_data(self, data: str) -> None:
        if self._in_inline_script:
            self.resource_values.append(data)


def _expected_page_names(site_dir: Path) -> list[str]:
    page_names = ["index"]
    if (site_dir / "static-path" / "index.html").is_file():
        page_names.append("static-path")
    return page_names


def _add_check(
    report: dict[str, Any],
    *,
    check_id: str,
    status: str,
    path: Path,
    message: str,
    next_action: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    check: dict[str, Any] = {
        "id": check_id,
        "status": status,
        "path": str(path),
        "message": message,
    }
    if next_action:
        check["next_action"] = next_action
    if details:
        check["details"] = details
    report["checks"].append(check)
    if status == "fail":
        diagnostic: dict[str, Any] = {
            "severity": "error",
            "check_id": check_id,
            "message": message,
            "path": str(path),
        }
        if next_action:
            diagnostic["next_action"] = next_action
        report["diagnostics"].append(diagnostic)
        for failure in (details or {}).get("failures", []):
            report["diagnostics"].append(
                {
                    "severity": "error",
                    "check_id": check_id,
                    "message": str(failure),
                    "path": str(path),
                    **({"next_action": next_action} if next_action else {}),
                }
            )


def _render_html_report(report: dict[str, Any]) -> str:
    status = "PASS" if report.get("ok") else "FAIL"
    check_rows = "\n".join(_render_check_row(check) for check in report["checks"])
    diagnostics = report["diagnostics"]
    diagnostic_items = "\n".join(
        "<li><code>{check}</code> {message} <span>{path}</span></li>".format(
            check=html.escape(str(item.get("check_id", ""))),
            message=html.escape(str(item.get("message", ""))),
            path=html.escape(str(item.get("path", ""))),
        )
        for item in diagnostics
    )
    if not diagnostic_items:
        diagnostic_items = "<li>No diagnostics.</li>"
    screenshot_links = "\n".join(_render_screenshot_link(check) for check in report["checks"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Render Debug Inspection Report</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d0d7de; padding: 0.5rem; text-align: left; }}
    th {{ background: #f6f8fa; }}
    code {{ background: #f6f8fa; padding: 0.1rem 0.25rem; }}
    .status {{ font-weight: 700; }}
    .pass {{ color: #116329; }}
    .fail {{ color: #b42318; }}
    .screenshots {{ display: flex; flex-wrap: wrap; gap: 0.75rem; }}
  </style>
</head>
<body>
  <h1>Render Debug Inspection Report</h1>
  <p class="status {html.escape(status.lower())}">Status: {html.escape(status)}</p>
  <p>Site: <code>{html.escape(str(report["site_dir"]))}</code></p>
  <p>Summary: <code>{html.escape(str(report["summary_path"]))}</code></p>
  <h2>Screenshots</h2>
  <div class="screenshots">
{screenshot_links}
  </div>
  <h2>Checks</h2>
  <table>
    <thead><tr><th>ID</th><th>Status</th><th>Path</th><th>Message</th></tr></thead>
    <tbody>
{check_rows}
    </tbody>
  </table>
  <h2>Diagnostics</h2>
  <ul>
{diagnostic_items}
  </ul>
</body>
</html>
"""


def _render_check_row(check: dict[str, Any]) -> str:
    return (
        "      <tr>"
        f"<td><code>{html.escape(str(check['id']))}</code></td>"
        f"<td>{html.escape(str(check['status']))}</td>"
        f"<td><code>{html.escape(str(check['path']))}</code></td>"
        f"<td>{html.escape(str(check['message']))}</td>"
        "</tr>"
    )


def _render_screenshot_link(check: dict[str, Any]) -> str:
    details = check.get("details")
    if not isinstance(details, dict):
        return ""
    screenshot = details.get("screenshot")
    if not isinstance(screenshot, str):
        return ""
    label = f"{details.get('viewport', '')} {details.get('page', '')}".strip()
    return (
        f'    <a href="{html.escape(screenshot)}">'
        f"{html.escape(label or screenshot)}</a>"
    )


def _relative_id(root: Path, path: Path) -> str:
    try:
        return _path_id(path.relative_to(root))
    except ValueError:
        return _path_id(path)


def _path_id(path: Path) -> str:
    return ":".join(path.parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect raya render debug artifacts and write an HTML/JSON report."
    )
    parser.add_argument("site_dir")
    parser.add_argument("debug_dir")
    parser.add_argument("copied_site_dir", nargs="?")
    args = parser.parse_args(argv)
    report = inspect_render_debug(
        site_dir=args.site_dir,
        debug_dir=args.debug_dir,
        copied_site_dir=args.copied_site_dir,
    )
    if report["ok"]:
        print(
            "render-debug-report: passed "
            f"({len(report['checks'])} check(s), report={report['html_report_path']})"
        )
        return 0
    for diagnostic in report["diagnostics"]:
        print(
            "render-debug-report: ERROR: "
            f"{diagnostic['message']} ({diagnostic['path']})"
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
