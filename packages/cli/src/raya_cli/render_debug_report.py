from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


RENDER_DEBUG_VIEWPORT_NAMES = ("desktop", "mobile")
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
SUPPORT_TEXT_TAGS = {"script", "style", "code", "pre", "kbd", "samp", "textarea"}
VOID_HTML_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}
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
READER_UX_STATIC_ENVIRONMENTS = {
    "hint": {
        "id": "raya-static-environment-hint-orthogonal-activity",
        "class": "raya-static-environment--hint",
        "heading": "Hint for Activity 4.1",
        "text": "before expanding the matrix product.",
    },
    "solution": {
        "id": "raya-static-environment-solution-orthogonal-activity",
        "class": "raya-static-environment--solution",
        "heading": "Solution of Activity 4.1",
        "text": "Scaling the direction vector changes the projection coefficient",
    },
    "answer": {
        "id": "raya-static-environment-answer-orthogonal-activity",
        "class": "raya-static-environment--answer",
        "heading": "Answer to Activity 4.1",
        "text": "The residual vector is orthogonal to the direction vector.",
    },
}
LEARNING_SHELL_REGIONS = (
    "raya-learning-shell",
    "raya-course-map",
    "raya-course-map-header",
    "raya-course-map-navigation",
    "raya-course-actions",
    "raya-course-content",
    "raya-course-map-footer",
    "raya-course-map-mini",
    "raya-main-article",
    "raya-learning-rail",
)
LEARNING_SHELL_IDS = (
    "raya-content",
    "raya-article",
)
LEARNING_SHELL_SELECTORS = (
    "main#raya-content.raya-learning-shell",
    "nav#raya-course-map.raya-course-map",
    "nav.raya-course-map",
    "header.raya-course-map-header",
    "div#raya-course-map-body.raya-course-map-body",
    "div.raya-course-map-navigation",
    "[data-raya-course-map-navigation]",
    "section.raya-course-actions",
    "section.raya-course-content",
    "footer.raya-course-map-footer",
    "div.raya-course-map-mini",
    "[data-raya-course-map-mini]",
    "button.raya-course-map-collapse",
    "[data-raya-course-map-collapse]",
    "button.raya-course-map-expand",
    "[data-raya-course-map-expand]",
    "[data-raya-course-map-toggle]",
    "article#raya-article.raya-main-article",
    "aside#raya-learning-rail.raya-learning-rail",
)
DISCOVERY_COMMAND_BAR_CLASS = "raya-discovery-command-bar"
FORBIDDEN_READER_TOP_BAR_CLASS = "raya-top-command-bar"
FORBIDDEN_READER_TOP_BAR_DIAGNOSTIC = (
    "reader page must not render .raya-top-command-bar"
)
COURSE_TREE_SCENARIO_IDS = {
    "course-tree-current-path-expanded",
    "course-tree-peer-accordion-expanded",
    "course-tree-long-label",
    "course-tree-long-label-1280",
    "course-tree-long-label-1312",
    "course-rail-mini-full-height",
    "course-tree-phone-drawer",
}
COURSE_TREE_SCENARIO_FIELDS = {
    "viewport",
    "input_modality",
    "rail_rect",
    "tree_rect",
    "active_branch_ids",
    "focus_owner",
    "overflow_owners",
    "screenshot",
}
COURSE_TREE_RESPONSIVE_RAIL_BOUNDARIES = {
    "course-tree-long-label-1280": {"viewport": 1280, "rail": 256},
    "course-tree-long-label-1312": {"viewport": 1312, "rail": 288},
}
COURSE_TREE_RESPONSIVE_RAIL_FIELDS = {
    "article_rect",
    "document_overflow",
    "title_containment",
}
TITLE_CONTAINMENT_FIELDS = {
    "aria_current",
    "text",
    "contained",
    "right",
    "scrollport_right",
    "scroll_width",
    "scrollport_width",
}
RECT_FIELDS = {"top", "right", "bottom", "left", "width", "height"}


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
        "scenarios": {},
    }

    summary = _read_summary(summary_path, report)
    captures = _capture_items(summary, summary_path, report)
    _inspect_course_tree_scenarios(summary, summary_path, debug_root, report)
    _inspect_captures(site_root, debug_root, captures, report)
    _inspect_capture_skins(site_root, captures, report, context="site")
    numbered_index = _read_numbered_index(
        site_root,
        report,
        required=_captures_need_numbered_index(captures),
    )
    _inspect_numbered_content(captures, numbered_index, report)
    _inspect_static_environment_content(site_root, captures, report)
    _inspect_static_site(site_root, report, context="site")
    _inspect_learning_shell(site_root, report, context="site")
    if copied_site_root is not None:
        _inspect_copied_site(site_root, copied_site_root, report)
        _inspect_capture_skins(
            copied_site_root,
            captures,
            report,
            context="copied-site",
        )
        _inspect_learning_shell(copied_site_root, report, context="copied-site")
        _add_check(
            report,
            check_id="site:copied-site",
            status="pass",
            path=copied_site_root,
            message=f"copied-site parity inspected at {copied_site_root}",
        )

    report["ok"] = not report["diagnostics"]
    write_render_debug_report(debug_root, report)
    return report


def copy_static_site(site_dir: str | Path, destination: str | Path) -> Path:
    source = Path(site_dir)
    target = Path(destination)
    if not source.is_dir():
        raise ValueError("static site source must be an existing directory")
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
    try:
        source_resolved.relative_to(target_resolved)
    except ValueError:
        pass
    else:
        raise ValueError("static site copy destination must not contain source")
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    return target


def merge_course_tree_scenarios(
    debug_dir: str | Path,
    scenario_debug_dir: str | Path,
) -> Path:
    debug_root = Path(debug_dir)
    scenario_debug_root = Path(scenario_debug_dir)
    summary_path = debug_root / "summary.json"
    scenario_summary_path = scenario_debug_root / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    scenario_summary = json.loads(scenario_summary_path.read_text(encoding="utf-8"))
    if not isinstance(summary, dict) or not isinstance(scenario_summary, dict):
        raise ValueError("render debug summaries must contain objects")
    scenarios = scenario_summary.get("scenarios")
    if not isinstance(scenarios, dict):
        raise ValueError("scenario render debug summary must contain a scenarios object")

    normalized: dict[str, dict[str, Any]] = {}
    for scenario_id, raw_scenario in scenarios.items():
        if not isinstance(scenario_id, str) or not isinstance(raw_scenario, dict):
            raise ValueError("course-tree scenarios must map string ids to objects")
        screenshot = raw_scenario.get("screenshot")
        if not isinstance(screenshot, str) or not screenshot:
            raise ValueError(f"course-tree scenario {scenario_id!r} needs a screenshot")
        screenshot_name = Path(screenshot).name
        screenshot_source = scenario_debug_root / screenshot_name
        if not screenshot_source.is_file():
            raise ValueError(
                f"course-tree scenario screenshot does not exist: {screenshot_source}"
            )
        shutil.copy2(screenshot_source, debug_root / screenshot_name)
        normalized[scenario_id] = {**raw_scenario, "screenshot": screenshot_name}

    summary["scenarios"] = normalized
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary_path


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


def _inspect_course_tree_scenarios(
    summary: dict[str, Any],
    summary_path: Path,
    debug_dir: Path,
    report: dict[str, Any],
) -> None:
    raw_scenarios = summary.get("scenarios")
    if raw_scenarios is None:
        return
    if not isinstance(raw_scenarios, dict):
        _add_check(
            report,
            check_id="summary:course-tree-scenarios",
            status="fail",
            path=summary_path,
            message="summary.json scenarios must be an object",
            next_action="Regenerate the course-tree render-debug scenarios.",
        )
        return

    missing = sorted(COURSE_TREE_SCENARIO_IDS - set(raw_scenarios))
    _add_check(
        report,
        check_id="summary:course-tree-scenarios",
        status="fail" if missing else "pass",
        path=summary_path,
        message=(
            f"course-tree scenario evidence contains {len(raw_scenarios)} state(s)"
            if not missing
            else f"course-tree scenario evidence is missing {missing}"
        ),
        next_action=(
            "Regenerate the course-tree render-debug scenarios."
            if missing
            else None
        ),
        details={"required": sorted(COURSE_TREE_SCENARIO_IDS), "missing": missing},
    )

    for scenario_id, raw_scenario in sorted(raw_scenarios.items()):
        failures: list[str] = []
        if not isinstance(raw_scenario, dict):
            failures.append(f"scenario {scenario_id!r} must be an object")
            scenario: dict[str, Any] = {}
        else:
            scenario = dict(raw_scenario)
            required_fields = COURSE_TREE_SCENARIO_FIELDS
            if scenario_id in COURSE_TREE_RESPONSIVE_RAIL_BOUNDARIES:
                required_fields = (
                    required_fields | COURSE_TREE_RESPONSIVE_RAIL_FIELDS
                )
            missing_fields = sorted(required_fields - set(scenario))
            if missing_fields:
                failures.append(
                    f"scenario {scenario_id!r} is missing fields {missing_fields}"
                )

        viewport = scenario.get("viewport")
        if not isinstance(viewport, dict) or not all(
            isinstance(viewport.get(name), (int, float)) and viewport[name] > 0
            for name in ("width", "height")
        ):
            failures.append(f"scenario {scenario_id!r} has an invalid viewport")
        if scenario.get("input_modality") not in {"fine", "coarse", "hybrid"}:
            failures.append(f"scenario {scenario_id!r} has an invalid input modality")
        for field in ("rail_rect", "tree_rect"):
            rect = scenario.get(field)
            if not isinstance(rect, dict) or not all(
                isinstance(rect.get(name), (int, float)) for name in RECT_FIELDS
            ):
                failures.append(f"scenario {scenario_id!r} has an invalid {field}")
        responsive_boundary = COURSE_TREE_RESPONSIVE_RAIL_BOUNDARIES.get(scenario_id)
        if responsive_boundary is not None:
            _validate_responsive_course_rail_scenario(
                scenario_id,
                scenario,
                responsive_boundary,
                failures,
            )
        for field in ("active_branch_ids", "overflow_owners"):
            values = scenario.get(field)
            if not isinstance(values, list) or not all(
                isinstance(value, str) for value in values
            ):
                failures.append(f"scenario {scenario_id!r} has an invalid {field}")
        if not isinstance(scenario.get("focus_owner"), str):
            failures.append(f"scenario {scenario_id!r} has an invalid focus owner")

        screenshot_value = scenario.get("screenshot")
        screenshot = debug_dir / f"{scenario_id}.png"
        if isinstance(screenshot_value, str):
            declared = Path(screenshot_value)
            if not declared.is_absolute():
                declared = debug_dir / declared
            declared = declared.resolve()
            try:
                declared.relative_to(debug_dir.resolve())
            except ValueError:
                failures.append(
                    f"scenario {scenario_id!r} screenshot is outside debug directory"
                )
            else:
                screenshot = declared
                scenario["screenshot"] = declared.name
        else:
            failures.append(f"scenario {scenario_id!r} has an invalid screenshot")
        if not screenshot.is_file() or screenshot.stat().st_size <= 0:
            failures.append(
                f"scenario {scenario_id!r} screenshot is missing or empty: {screenshot}"
            )

        report["scenarios"][str(scenario_id)] = scenario
        _add_check(
            report,
            check_id=f"course-tree-scenario:{scenario_id}",
            status="fail" if failures else "pass",
            path=screenshot,
            message=(
                f"course-tree scenario {scenario_id!r} captured"
                if not failures
                else "; ".join(failures)
            ),
            next_action=(
                "Regenerate the course-tree render-debug scenarios."
                if failures
                else None
            ),
            details={
                "page": scenario_id,
                "viewport": (
                    viewport.get("width") if isinstance(viewport, dict) else ""
                ),
                "screenshot": screenshot.name,
                "failures": failures,
            },
        )


def _validate_responsive_course_rail_scenario(
    scenario_id: str,
    scenario: dict[str, Any],
    boundary: dict[str, int],
    failures: list[str],
) -> None:
    viewport = scenario.get("viewport")
    if not isinstance(viewport, dict) or viewport.get("width") != boundary["viewport"]:
        failures.append(
            f"scenario {scenario_id!r} must use viewport width "
            f"{boundary['viewport']}"
        )

    rail_rect = scenario.get("rail_rect")
    if not isinstance(rail_rect, dict) or rail_rect.get("width") != boundary["rail"]:
        failures.append(
            f"scenario {scenario_id!r} must have rail width {boundary['rail']}"
        )

    article_rect = scenario.get("article_rect")
    if not isinstance(article_rect, dict) or not all(
        isinstance(article_rect.get(name), (int, float)) for name in RECT_FIELDS
    ):
        failures.append(f"scenario {scenario_id!r} has an invalid article_rect")
    elif article_rect["width"] < 672:
        failures.append(
            f"scenario {scenario_id!r} article width must be at least 672"
        )

    document_overflow = scenario.get("document_overflow")
    if not isinstance(document_overflow, (int, float)):
        failures.append(f"scenario {scenario_id!r} has an invalid document_overflow")
    elif document_overflow > 1:
        failures.append(
            f"scenario {scenario_id!r} document overflow must be at most 1"
        )

    title_containment = scenario.get("title_containment")
    if not isinstance(title_containment, dict):
        failures.append(f"scenario {scenario_id!r} has an invalid title_containment")
        return
    missing_fields = sorted(TITLE_CONTAINMENT_FIELDS - set(title_containment))
    if missing_fields:
        failures.append(
            f"scenario {scenario_id!r} title_containment is missing fields "
            f"{missing_fields}"
        )
        return
    if title_containment["aria_current"] != "page":
        failures.append(
            f"scenario {scenario_id!r} title_containment must describe the current page"
        )
    if not isinstance(title_containment["text"], str) or not title_containment["text"]:
        failures.append(f"scenario {scenario_id!r} has an invalid current title text")
    if title_containment["contained"] is not True:
        failures.append(f"scenario {scenario_id!r} current title must be contained")
    for field in (
        "right",
        "scrollport_right",
        "scroll_width",
        "scrollport_width",
    ):
        if not isinstance(title_containment[field], (int, float)):
            failures.append(
                f"scenario {scenario_id!r} has an invalid title_containment {field}"
            )
            return
    if title_containment["right"] > title_containment["scrollport_right"] + 1:
        failures.append(f"scenario {scenario_id!r} current title exceeds its scrollport")
    if title_containment["scroll_width"] > title_containment["scrollport_width"] + 1:
        failures.append(f"scenario {scenario_id!r} current title row overflows its scrollport")


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
            screenshots = _capture_screenshot_details(capture)
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
                    "screenshots": screenshots,
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
    screenshots = capture.get("screenshots")
    if screenshots is not None:
        if not isinstance(screenshots, dict):
            failures.append(
                "screenshots must be an object in capture "
                f"page={page!r} viewport={viewport_name!r}"
            )
        else:
            for name, value in sorted(screenshots.items()):
                declared_screenshot = Path(str(value))
                if not declared_screenshot.is_absolute():
                    declared_screenshot = debug_dir / declared_screenshot
                declared_screenshot = declared_screenshot.resolve()
                try:
                    declared_screenshot.relative_to(debug_dir.resolve())
                except ValueError:
                    failures.append(
                        "screenshot path is outside debug directory "
                        f"for name={name!r} page={page!r} "
                        f"viewport={viewport_name!r}: {declared_screenshot}"
                    )
                    continue
                if (
                    not declared_screenshot.is_file()
                    or declared_screenshot.stat().st_size <= 0
                ):
                    failures.append(
                        "missing or empty declared screenshot "
                        f"{name!r}: {declared_screenshot}"
                    )
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


def _capture_screenshot_details(capture: dict[str, Any]) -> dict[str, str]:
    screenshots = capture.get("screenshots")
    if not isinstance(screenshots, dict):
        return {}
    return {
        str(name): Path(str(value)).name
        for name, value in sorted(screenshots.items())
    }


def _inspect_capture_skins(
    site_dir: Path,
    captures: list[dict[str, Any]],
    report: dict[str, Any],
    *,
    context: str,
) -> None:
    css_path = site_dir / "_raya" / "render" / "skin.css"
    css = css_path.read_text(encoding="utf-8") if css_path.is_file() else ""
    for capture in captures:
        page = capture.get("page")
        viewport = capture.get("viewport")
        viewport_name = viewport.get("name") if isinstance(viewport, dict) else None
        if not isinstance(page, str) or not isinstance(viewport_name, str):
            continue
        skin = capture.get("skin")
        skin_id = skin.strip() if isinstance(skin, str) else ""
        expected_selector = _skin_selector_for_id(skin_id) if skin_id else ""
        page_url = str(capture.get("url") or page)
        screenshot = Path(str(capture.get("screenshot", "")))
        failures = []
        if not skin_id:
            failures.append(f"missing active skin for page {page_url}")
        elif expected_selector not in css:
            failures.append(
                f"skin.css at {css_path} does not define selector "
                f"{expected_selector!r} for captured skin {skin_id!r}"
            )
        check_prefix = "" if context == "site" else f"{context}:"
        _add_check(
            report,
            check_id=f"{check_prefix}capture-skin:{page}:{viewport_name}",
            status="fail" if failures else "pass",
            path=screenshot,
            message=(
                f"active skin {skin_id!r} captured for page {page_url} "
                f"and selector {expected_selector!r} exists in {css_path}"
                if not failures
                else "; ".join(failures)
            ),
            next_action=(
                "Regenerate render debug capture artifacts after rebuilding the site."
                if failures
                else None
            ),
            details={
                "skin": skin_id,
                "page_url": page_url,
                "skin_css": str(css_path),
                "expected_selector": expected_selector,
                "failures": failures,
            },
        )


def _skin_selector_for_id(skin_id: str) -> str:
    return f'[data-raya-skin="{skin_id}"]'


def _read_numbered_index(
    site_dir: Path,
    report: dict[str, Any],
    *,
    required: bool,
) -> dict[str, Any]:
    index_path = _numbered_index_path(site_dir)
    if not index_path.exists():
        if required:
            _add_check(
                report,
                check_id="numbered-content:index",
                status="fail",
                path=index_path,
                message=f"data/numbered-objects.json is missing at {index_path}",
                next_action=(
                    "Rebuild the static site so data/numbered-objects.json exists."
                ),
            )
        return {"objects": [], "by_reference_text": {}}
    try:
        numbered_index = json.loads(index_path.read_text(encoding="utf-8"))
    except Exception as exc:
        _add_check(
            report,
            check_id="numbered-content:index",
            status="fail",
            path=index_path,
            message=f"missing or malformed numbered object index at {index_path}: {exc}",
            next_action="Rebuild the static site so data/numbered-objects.json is valid.",
        )
        return {"objects": [], "by_reference_text": {}}

    objects = numbered_index.get("objects")
    if not isinstance(objects, list):
        _add_check(
            report,
            check_id="numbered-content:index",
            status="fail",
            path=index_path,
            message=f"numbered object index must contain an objects list at {index_path}",
            next_action="Rebuild the static site so data/numbered-objects.json is valid.",
        )
        return {"objects": [], "by_reference_text": {}}

    by_reference_text = {
        item["reference_text"]: item
        for item in objects
        if isinstance(item, dict) and isinstance(item.get("reference_text"), str)
    }
    _add_check(
        report,
        check_id="numbered-content:index",
        status="pass",
        path=index_path,
        message=f"numbered object index contains {len(objects)} object(s)",
        details={"object_count": len(objects)},
    )
    return {"objects": objects, "by_reference_text": by_reference_text}


def _numbered_index_path(site_dir: Path) -> Path:
    site_data_path = site_dir / "data" / "numbered-objects.json"
    if site_data_path.exists():
        return site_data_path
    artifact_data_path = site_dir.parent / "data" / "numbered-objects.json"
    if artifact_data_path.exists():
        return artifact_data_path
    return site_data_path


def _captures_need_numbered_index(captures: list[dict[str, Any]]) -> bool:
    for capture in captures:
        numbered_content = capture.get("numbered_content")
        if not isinstance(numbered_content, dict):
            continue
        objects = _numbered_evidence_items(numbered_content.get("objects"))
        references = _numbered_evidence_items(numbered_content.get("references"))
        if objects or references:
            return True
        proofs = _numbered_evidence_items(numbered_content.get("proofs"))
        if any(proof.get("target_text") for proof in proofs):
            return True
    return False


def _inspect_numbered_content(
    captures: list[dict[str, Any]],
    numbered_index: dict[str, Any],
    report: dict[str, Any],
) -> None:
    by_reference_text = numbered_index.get("by_reference_text")
    if not isinstance(by_reference_text, dict):
        by_reference_text = {}

    for capture in captures:
        page = capture.get("page")
        viewport = capture.get("viewport")
        viewport_name = viewport.get("name") if isinstance(viewport, dict) else None
        if not isinstance(page, str) or not isinstance(viewport_name, str):
            continue
        numbered_content = capture.get("numbered_content")
        if not isinstance(numbered_content, dict):
            _add_check(
                report,
                check_id=f"numbered-content:{page}:{viewport_name}",
                status="fail",
                path=Path(str(capture.get("screenshot", ""))),
                message=(
                    f"missing numbered content evidence for page={page!r} "
                    f"viewport={viewport_name!r}"
                ),
                next_action="Regenerate render debug capture artifacts.",
            )
            continue

        objects = _numbered_evidence_items(numbered_content.get("objects"))
        references = _numbered_evidence_items(numbered_content.get("references"))
        proofs = _numbered_evidence_items(numbered_content.get("proofs"))
        proof_targets = []
        failures = []
        for proof in proofs:
            target_text = proof.get("target_text")
            target = (
                by_reference_text.get(target_text)
                if isinstance(target_text, str)
                else None
            )
            if isinstance(target_text, str) and target_text and target is None:
                failures.append(
                    "proof target text "
                    f"{target_text!r} could not be resolved from "
                    "data/numbered-objects.json"
                )
            proof_targets.append(
                {
                    "proof_id": str(proof.get("id", "")),
                    "target_id": (
                        str(target.get("id", ""))
                        if isinstance(target, dict)
                        else str(proof.get("target_id", ""))
                    ),
                    "target_text": target_text or "",
                }
            )

        _add_check(
            report,
            check_id=f"numbered-content:{page}:{viewport_name}",
            status="fail" if failures else "pass",
            path=Path(str(capture.get("screenshot", ""))),
            message=(
                "numbered content proof target inspection failed for "
                f"page={page!r} viewport={viewport_name!r}"
                if failures
                else (
                    f"numbered content evidence for page={page!r} "
                    f"viewport={viewport_name!r}"
                )
            ),
            next_action=(
                "Rebuild the static site and regenerate render debug capture artifacts."
                if failures
                else None
            ),
            details={
                "object_count": len(objects),
                "reference_count": len(references),
                "proof_count": len(proofs),
                "proof_targets": proof_targets,
                "failures": failures,
            },
        )


def _numbered_evidence_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _inspect_static_environment_content(
    site_dir: Path,
    captures: list[dict[str, Any]],
    report: dict[str, Any],
) -> None:
    if not (site_dir / "reader-ux" / "index.html").is_file():
        return

    by_viewport: dict[str, dict[str, Any]] = {}
    for capture in captures:
        if capture.get("page") != "reader-ux":
            continue
        viewport = capture.get("viewport")
        viewport_name = viewport.get("name") if isinstance(viewport, dict) else None
        if isinstance(viewport_name, str):
            by_viewport[viewport_name] = capture

    for viewport_name in RENDER_DEBUG_VIEWPORT_NAMES:
        capture = by_viewport.get(viewport_name)
        screenshot = Path(str(capture.get("screenshot", ""))) if capture else Path()
        for kind, expected in READER_UX_STATIC_ENVIRONMENTS.items():
            failures = (
                _static_environment_failures(capture, expected)
                if capture is not None
                else [f"missing reader-ux {viewport_name} capture"]
            )
            _add_check(
                report,
                check_id=f"static-environment:reader-ux:{viewport_name}:{kind}",
                status="fail" if failures else "pass",
                path=screenshot,
                message=(
                    "Reader UX render-debug evidence includes targeted "
                    f"{kind} for {viewport_name}"
                ),
                next_action=(
                    "Regenerate render debug capture artifacts for reader-ux."
                    if failures
                    else None
                ),
                details={"failures": failures},
            )


def _static_environment_failures(
    capture: dict[str, Any],
    expected: dict[str, str],
) -> list[str]:
    static_environments = capture.get("staticEnvironments")
    if not isinstance(static_environments, list):
        return ["missing staticEnvironments evidence"]
    expected_id = expected["id"]
    matching = [
        item
        for item in static_environments
        if isinstance(item, dict) and item.get("id") == expected_id
    ]
    if not matching:
        return [f"missing static environment id {expected_id!r}"]
    item = matching[0]
    failures = []
    class_name = str(item.get("className", ""))
    if expected["class"] not in class_name.split():
        failures.append(
            f"static environment {expected_id!r} missing class {expected['class']!r}"
        )
    heading = str(item.get("heading", ""))
    if expected["heading"] not in heading:
        failures.append(
            f"static environment {expected_id!r} missing heading {expected['heading']!r}"
        )
    text = str(item.get("text", ""))
    if expected["text"] not in text:
        failures.append(
            f"static environment {expected_id!r} missing text {expected['text']!r}"
        )
    return failures


def _inspect_static_site(
    site_dir: Path,
    report: dict[str, Any],
    *,
    context: str,
) -> None:
    _inspect_skin_css(site_dir, report, context=context)
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
        raw_tex_markers = _raw_tex_markers_from_text(_visible_text_from_html(text))
        _add_check(
            report,
            check_id=f"{check_prefix}:raw-tex:{_relative_id(site_dir, html_path)}",
            status="fail" if raw_tex_markers else "pass",
            path=html_path,
            message=(
                f"raw visible TeX in {html_path}: {raw_tex_markers}"
                if raw_tex_markers
                else f"no raw visible TeX in {html_path}"
            ),
            next_action=(
                "Inspect generated HTML and fix build-time math diagnostics."
                if raw_tex_markers
                else None
            ),
        )

    if math_present:
        _inspect_local_mathjax_resources(site_dir, report, context=context)


def _inspect_learning_shell(
    site_dir: Path,
    report: dict[str, Any],
    *,
    context: str,
) -> None:
    html_paths = [
        path
        for path in sorted(site_dir.rglob("*.html")) if site_dir.is_dir()
        if "_raya" not in path.relative_to(site_dir).parts
    ]
    for html_path in html_paths:
        text = html_path.read_text(encoding="utf-8")
        elements = _element_markers_from_html(text)
        if DISCOVERY_COMMAND_BAR_CLASS in elements["classes"]:
            continue
        missing_classes = [
            region
            for region in LEARNING_SHELL_REGIONS
            if region not in elements["classes"]
        ]
        missing_ids = [
            region for region in LEARNING_SHELL_IDS if region not in elements["ids"]
        ]
        missing_selectors = [
            selector
            for selector in LEARNING_SHELL_SELECTORS
            if selector not in elements["selectors"]
        ]
        if FORBIDDEN_READER_TOP_BAR_CLASS in elements["classes"]:
            missing_selectors.append(FORBIDDEN_READER_TOP_BAR_DIAGNOSTIC)
        ownership_failures = elements["ownership_failures"]
        missing = (
            missing_classes
            + missing_ids
            + missing_selectors
            + ownership_failures
        )
        _add_check(
            report,
            check_id=(
                f"{context}:learning-shell:"
                f"{_learning_shell_page_id(site_dir, html_path)}"
            ),
            status="fail" if missing else "pass",
            path=html_path,
            message=(
                f"missing learning shell region(s) in {html_path}: "
                f"{', '.join(missing)}"
                if missing
                else f"learning shell regions exist in {html_path}"
            ),
            next_action=(
                "Rebuild the static site with the Raya learning shell regions."
                if missing
                else None
            ),
            details={
                "missing_classes": missing_classes,
                "missing_ids": missing_ids,
                "missing_selectors": missing_selectors,
                "ownership_failures": ownership_failures,
            },
        )


def _learning_shell_page_id(site_dir: Path, html_path: Path) -> str:
    relative = html_path.relative_to(site_dir)
    if relative == Path("index.html"):
        return "index"
    return _path_id(relative)


def _element_markers_from_html(text: str) -> dict[str, Any]:
    parser = _ElementMarkerParser()
    parser.feed(text)
    parser.close()
    return {
        "classes": parser.classes,
        "ids": parser.ids,
        "selectors": parser.selectors,
        "ownership_failures": parser.course_map_ownership_failures(),
    }


class _ElementMarkerParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.classes: set[str] = set()
        self.ids: set[str] = set()
        self.selectors: set[str] = set()
        self.nodes: list[dict[str, Any]] = []
        self.stack: list[int] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = {name.lower(): value or "" for name, value in attrs}
        class_name = attributes.get("class")
        class_tokens = class_name.split() if class_name else []
        tag_lower = tag.lower()
        parent = self.stack[-1] if self.stack else None
        node_index = len(self.nodes)
        self.nodes.append(
            {
                "tag": tag_lower,
                "attributes": attributes,
                "classes": set(class_tokens),
                "parent": parent,
                "children": [],
            }
        )
        if parent is not None:
            self.nodes[parent]["children"].append(node_index)
        if tag_lower not in VOID_HTML_TAGS:
            self.stack.append(node_index)
        for name in attributes:
            self.selectors.add(f"[{name}]")
        if class_name:
            self.classes.update(class_tokens)
        element_id = attributes.get("id")
        if element_id:
            self.ids.add(element_id)
        for class_token in class_tokens:
            self.selectors.add(f".{class_token}")
            self.selectors.add(f"{tag_lower}.{class_token}")
        if element_id:
            self.selectors.add(f"{tag_lower}#{element_id}")
            for class_token in class_tokens:
                self.selectors.add(f"{tag_lower}#{element_id}.{class_token}")

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        for stack_index in range(len(self.stack) - 1, -1, -1):
            node_index = self.stack[stack_index]
            if self.nodes[node_index]["tag"] == tag_lower:
                del self.stack[stack_index:]
                return

    def course_map_ownership_failures(self) -> list[str]:
        map_node = self._first_node(
            lambda node: node["attributes"].get("id") == "raya-course-map"
        )
        if map_node is None:
            return []

        header = self._first_node(
            lambda node: "raya-course-map-header" in node["classes"]
        )
        body = self._first_node(
            lambda node: node["attributes"].get("id") == "raya-course-map-body"
        )
        navigation = self._first_node(
            lambda node: "data-raya-course-map-navigation"
            in node["attributes"]
        )
        actions = self._first_node(
            lambda node: "raya-course-actions" in node["classes"]
        )
        content = self._first_node(
            lambda node: "raya-course-content" in node["classes"]
        )
        footer = self._first_node(
            lambda node: "raya-course-map-footer" in node["classes"]
        )
        mini = self._first_node(
            lambda node: "data-raya-course-map-mini" in node["attributes"]
        )
        collapse = self._first_node(
            lambda node: "data-raya-course-map-collapse" in node["attributes"]
        )
        expand = self._first_node(
            lambda node: "data-raya-course-map-expand" in node["attributes"]
        )
        failures: list[str] = []

        if header is not None and self.nodes[header]["parent"] != map_node:
            failures.append(
                "course map header must be a direct child of #raya-course-map"
            )
        if body is not None and self.nodes[body]["parent"] != map_node:
            failures.append(
                "course map body must be a direct child of #raya-course-map"
            )
        if mini is not None and self.nodes[mini]["parent"] != map_node:
            failures.append(
                "course map mini rail must be a direct child of #raya-course-map"
            )
        if collapse is not None and (
            header is None or not self._is_descendant(collapse, header)
        ):
            failures.append(
                "course map collapse control must be inside the course map header"
            )

        if header is not None and body is not None and mini is not None:
            if self.nodes[map_node]["children"] != [header, body, mini]:
                failures.append(
                    "course map direct children must be ordered header, body, mini rail"
                )
        if body is not None and navigation is not None and footer is not None:
            if self.nodes[body]["children"] != [navigation, footer]:
                failures.append(
                    "course map body direct children must be ordered navigation, footer"
                )
        if navigation is not None and actions is not None and content is not None:
            if self.nodes[navigation]["children"] != [actions, content]:
                failures.append(
                    "course map navigation direct children must be ordered actions, content"
                )

        for selector, owned_node, owner, owner_label in (
            (
                "[data-raya-course-map-navigation]",
                navigation,
                body,
                "course map body",
            ),
            (
                ".raya-course-map-footer",
                footer,
                body,
                "course map body",
            ),
            (
                ".raya-course-actions",
                actions,
                navigation,
                "course map navigation",
            ),
            (
                ".raya-course-content",
                content,
                navigation,
                "course map navigation",
            ),
            (
                "[data-raya-course-map-filter]",
                self._first_node(
                    lambda node: "data-raya-course-map-filter"
                    in node["attributes"]
                ),
                content,
                "course map content",
            ),
            (
                "#raya-course-map-list",
                self._first_node(
                    lambda node: node["attributes"].get("id")
                    == "raya-course-map-list"
                ),
                content,
                "course map content",
            ),
            (
                "[data-raya-course-map-expand]",
                expand,
                mini,
                "course map mini rail",
            ),
        ):
            if owner is None or owned_node is None or not self._is_descendant(
                owned_node, owner
            ):
                failures.append(f"{owner_label} must own {selector}")
        return failures

    def _first_node(self, predicate: Any) -> int | None:
        for node_index, node in enumerate(self.nodes):
            if predicate(node):
                return node_index
        return None

    def _is_descendant(self, node_index: int, ancestor_index: int) -> bool:
        parent = self.nodes[node_index]["parent"]
        while parent is not None:
            if parent == ancestor_index:
                return True
            parent = self.nodes[parent]["parent"]
        return False


def _inspect_skin_css(
    site_dir: Path,
    report: dict[str, Any],
    *,
    context: str,
) -> None:
    css_path = site_dir / "_raya" / "render" / "skin.css"
    if not css_path.is_file() or css_path.stat().st_size <= 0:
        _add_check(
            report,
            check_id=f"{context}:skin:css",
            status="fail",
            path=css_path,
            message=f"missing or empty local skin.css at {css_path}",
            next_action="Rebuild the artifact so skin.css is copied under _raya/render/.",
        )
        return
    _add_check(
        report,
        check_id=f"{context}:skin:css",
        status="pass",
        path=css_path,
        message=f"local skin.css exists at {css_path}",
        details={"bytes": css_path.stat().st_size},
    )


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


def _visible_text_from_html(text: str) -> str:
    parser = _VisibleTextParser()
    parser.feed(text)
    parser.close()
    return " ".join(parser.text_parts)


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text_parts: list[str] = []
        self._support_depth = 0

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],  # noqa: ARG002
    ) -> None:
        if tag.lower() in SUPPORT_TEXT_TAGS:
            self._support_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in SUPPORT_TEXT_TAGS and self._support_depth > 0:
            self._support_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._support_depth == 0:
            self.text_parts.append(data)


def _raw_tex_markers_from_text(visible_text: str) -> list[str]:
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


def _expected_page_names(site_dir: Path) -> list[str]:
    page_names = ["index"]
    if (site_dir / "static-path" / "index.html").is_file():
        page_names.append("static-path")
    if (site_dir / "math-authoring" / "index.html").is_file():
        page_names.append("math-authoring")
    if (site_dir / "numbered-objects" / "index.html").is_file():
        page_names.append("numbered-objects")
    elif (site_dir / "3_numbered_objects" / "index.html").is_file():
        page_names.append("3_numbered_objects")
    if (site_dir / "reader-ux" / "index.html").is_file():
        page_names.append("reader-ux")
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
    copied_site = report.get("copied_site_dir")
    copied_site_line = (
        f"  <p>Copied site: <code>{html.escape(str(copied_site))}</code></p>\n"
        if copied_site
        else ""
    )
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
{copied_site_line.rstrip()}
  <p>Summary: <code>{html.escape(str(report["summary_path"]))}</code></p>
  <h2>Screenshots</h2>
  <div class="screenshots">
{screenshot_links}
  </div>
  <h2>Checks</h2>
  <table>
    <thead><tr><th>ID</th><th>Status</th><th>Path</th><th>Message</th><th>Details</th></tr></thead>
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
    details = check.get("details")
    details_html = ""
    if details:
        details_html = (
            "<pre>"
            + html.escape(json.dumps(details, indent=2, sort_keys=True))
            + "</pre>"
        )
    return (
        "      <tr>"
        f"<td><code>{html.escape(str(check['id']))}</code></td>"
        f"<td>{html.escape(str(check['status']))}</td>"
        f"<td><code>{html.escape(str(check['path']))}</code></td>"
        f"<td>{html.escape(str(check['message']))}</td>"
        f"<td>{details_html}</td>"
        "</tr>"
    )


def _render_screenshot_link(check: dict[str, Any]) -> str:
    details = check.get("details")
    if not isinstance(details, dict):
        return ""
    screenshots = details.get("screenshots")
    if isinstance(screenshots, dict) and screenshots:
        page = details.get("page", "")
        return "\n".join(
            f'    <a href="{html.escape(str(screenshot))}">'
            f"{html.escape(f'{name} {page}'.strip())}</a>"
            for name, screenshot in sorted(screenshots.items())
        )
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
    parser.add_argument("--scenario-debug-dir")
    args = parser.parse_args(argv)
    if args.scenario_debug_dir is not None:
        merge_course_tree_scenarios(args.debug_dir, args.scenario_debug_dir)
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
            f"{diagnostic['message']} ({diagnostic['path']})",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
