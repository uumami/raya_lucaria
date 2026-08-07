from __future__ import annotations

import json
from pathlib import Path

import pytest

from raya_cli.render_debug_report import (
    copy_static_site,
    inspect_render_debug,
    merge_course_tree_scenarios,
)


SOLUTION_BODY_EVIDENCE = "Scaling the direction vector changes the projection coefficient"
COURSE_TREE_SCENARIO_IDS = {
    "course-tree-current-path-expanded",
    "course-tree-peer-accordion-expanded",
    "course-tree-long-label",
    "course-tree-long-label-1280",
    "course-tree-long-label-1312",
    "course-rail-mini-full-height",
    "course-tree-phone-drawer",
}
COURSE_TREE_WIDTH_BOUNDARIES = {
    "course-tree-long-label-1280": {"viewport": 1280, "rail": 256},
    "course-tree-long-label-1312": {"viewport": 1312, "rail": 288},
}
LONG_CURRENT_TITLE = "ProjectionResidualsWithAnUnbrokenAuthorIdentifierXYZ007"


def _course_tree_scenarios(debug_dir: Path) -> dict[str, dict[str, object]]:
    scenarios: dict[str, dict[str, object]] = {}
    for scenario_id in COURSE_TREE_SCENARIO_IDS:
        boundary = COURSE_TREE_WIDTH_BOUNDARIES.get(scenario_id)
        viewport_width = boundary["viewport"] if boundary else 1280
        rail_width = boundary["rail"] if boundary else 256
        screenshot = debug_dir / f"{scenario_id}.png"
        screenshot.write_bytes(b"png")
        scenarios[scenario_id] = {
            "viewport": {"width": viewport_width, "height": 900},
            "input_modality": "fine",
            "rail_rect": {
                "top": 0,
                "right": rail_width,
                "bottom": 900,
                "left": 0,
                "width": rail_width,
                "height": 900,
            },
            "tree_rect": {
                "top": 96,
                "right": 256,
                "bottom": 852,
                "left": 0,
                "width": 256,
                "height": 756,
            },
            "active_branch_ids": ["rail-density-root"],
            "focus_owner": "body",
            "overflow_owners": ["raya-course-map-navigation"],
            "screenshot": screenshot.name,
        }
        if boundary:
            scenarios[scenario_id].update(
                {
                    "article_rect": {
                        "top": 72,
                        "right": 1000,
                        "bottom": 900,
                        "left": rail_width + 24,
                        "width": 672,
                        "height": 828,
                    },
                    "document_overflow": 0,
                    "title_containment": {
                        "aria_current": "page",
                        "text": LONG_CURRENT_TITLE,
                        "contained": True,
                        "right": rail_width - 16,
                        "scrollport_right": rail_width,
                        "scroll_width": rail_width - 24,
                        "scrollport_width": rail_width - 16,
                    },
                }
            )
    return scenarios


def _reader_static_environments(*, solution_text: str | None = None) -> list[dict[str, str]]:
    return [
        {
            "id": "raya-static-environment-hint-orthogonal-activity",
            "className": "raya-static-environment raya-static-environment--hint",
            "heading": "Hint for Activity 4.1",
            "text": (
                "Hint for Activity 4.1\n"
                "Compare the projection formula before expanding the matrix product."
            ),
        },
        {
            "id": "raya-static-environment-solution-orthogonal-activity",
            "className": "raya-static-environment raya-static-environment--solution",
            "heading": "Solution of Activity 4.1",
            "text": solution_text
            if solution_text is not None
            else (
                "Solution of Activity 4.1\n"
                f"{SOLUTION_BODY_EVIDENCE} while the projection line stays fixed."
            ),
        },
        {
            "id": "raya-static-environment-answer-orthogonal-activity",
            "className": "raya-static-environment raya-static-environment--answer",
            "heading": "Answer to Activity 4.1",
            "text": (
                "Answer to Activity 4.1\n"
                "The residual vector is orthogonal to the direction vector."
            ),
        },
    ]


def _write_reader_ux_report_fixture(
    tmp_path: Path,
    reader_captures: list[dict[str, object]],
) -> tuple[Path, Path]:
    site = tmp_path / "site"
    debug = tmp_path / "debug"
    site.mkdir()
    debug.mkdir()
    _write_skin_css(site)
    (site / "index.html").write_text("<!doctype html><html></html>", encoding="utf-8")
    reader_ux = site / "reader-ux"
    reader_ux.mkdir()
    (reader_ux / "index.html").write_text(
        "<!doctype html><html><body>Reader UX</body></html>",
        encoding="utf-8",
    )
    captures: list[dict[str, object]] = []
    for viewport in ("desktop", "mobile"):
        screenshot = debug / f"{viewport}-index.png"
        screenshot.write_bytes(b"png")
        captures.append(
            {
                "page": "index",
                "url": "http://127.0.0.1/index.html",
                "viewport": {
                    "name": viewport,
                    "width": 1280 if viewport == "desktop" else 390,
                    "height": 900 if viewport == "desktop" else 844,
                },
                "screenshot": str(screenshot),
                "mathjax_container_count": 0,
                "raw_tex_visible": False,
                "raw_tex_markers": [],
                "external_requests": [],
                "horizontal_overflow": 0,
                "skin": "warm-academic",
                "numbered_content": {"objects": [], "references": [], "proofs": []},
                "staticEnvironments": [],
            }
        )
    for capture in reader_captures:
        screenshot = Path(str(capture["screenshot"]))
        screenshot.write_bytes(b"png")
        captures.append(capture)
    (debug / "summary.json").write_text(
        json.dumps({"captures": captures}),
        encoding="utf-8",
    )
    return site, debug


def _reader_capture(
    debug: Path,
    viewport: str,
    *,
    include_static_environments: bool = True,
    static_environments: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    capture: dict[str, object] = {
        "page": "reader-ux",
        "url": "http://127.0.0.1/reader-ux/",
        "viewport": {
            "name": viewport,
            "width": 1280 if viewport == "desktop" else 390,
            "height": 900 if viewport == "desktop" else 844,
        },
        "screenshot": str(debug / f"{viewport}-reader-ux.png"),
        "mathjax_container_count": 0,
        "raw_tex_visible": False,
        "raw_tex_markers": [],
        "external_requests": [],
        "horizontal_overflow": 0,
        "skin": "practice-lab",
        "numbered_content": {"objects": [], "references": [], "proofs": []},
    }
    if include_static_environments:
        capture["staticEnvironments"] = (
            static_environments
            if static_environments is not None
            else _reader_static_environments()
        )
    return capture


def test_inspection_ignores_blocked_renderer_terms_in_prose_and_code(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        _learning_shell_html(
            """
            <p>This page documents cdn.jsdelivr.net and tex-chtml as examples.</p>
            <code>mathjax.js</code>
            <!-- startup.js appears in a comment, not a resource URL. -->
            """
        ),
    )

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    assert report["ok"] is True, report["diagnostics"]
    assert report["diagnostics"] == []


def test_render_debug_report_passes_when_skin_css_and_capture_skin_exist(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        _learning_shell_html("<p>Skin evidence fixture.</p>", skin="practice-lab"),
        skin="practice-lab",
    )

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    assert report["ok"] is True, report["diagnostics"]
    skin_checks = {
        check["id"]: check["status"]
        for check in report["checks"]
        if check["id"].startswith("site:skin")
        or check["id"].startswith("capture-skin:")
    }
    assert skin_checks == {
        "site:skin:css": "pass",
        "capture-skin:index:desktop": "pass",
        "capture-skin:index:mobile": "pass",
    }


def test_render_debug_report_preserves_valid_course_tree_scenarios(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        _learning_shell_html("<p>Course tree scenario fixture.</p>"),
    )
    summary_path = debug_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["scenarios"] = _course_tree_scenarios(debug_dir)
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    assert report["ok"] is True, report["diagnostics"]
    assert COURSE_TREE_SCENARIO_IDS <= set(report["scenarios"])
    for scenario_id in COURSE_TREE_SCENARIO_IDS:
        scenario = report["scenarios"][scenario_id]
        assert scenario["screenshot"] == f"{scenario_id}.png"
        assert scenario["overflow_owners"] == ["raya-course-map-navigation"]
        assert scenario["focus_owner"] == "body"
    for scenario_id, expected in COURSE_TREE_WIDTH_BOUNDARIES.items():
        scenario = report["scenarios"][scenario_id]
        assert scenario["viewport"]["width"] == expected["viewport"]
        assert scenario["rail_rect"]["width"] == expected["rail"]
        assert scenario["article_rect"]["width"] == 672
        assert scenario["document_overflow"] == 0
        assert scenario["title_containment"]["aria_current"] == "page"
        assert scenario["title_containment"]["text"] == LONG_CURRENT_TITLE
        assert scenario["title_containment"]["contained"] is True


@pytest.mark.parametrize(
    ("scenario_id", "mutation", "expected_failure"),
    [
        (
            "course-tree-long-label-1280",
            lambda scenario: scenario.pop("article_rect"),
            "missing fields ['article_rect']",
        ),
        (
            "course-tree-long-label-1280",
            lambda scenario: scenario.pop("document_overflow"),
            "missing fields ['document_overflow']",
        ),
        (
            "course-tree-long-label-1280",
            lambda scenario: scenario.pop("title_containment"),
            "missing fields ['title_containment']",
        ),
        (
            "course-tree-long-label-1280",
            lambda scenario: scenario["rail_rect"].update(width=255),
            "must have rail width 256",
        ),
        (
            "course-tree-long-label-1312",
            lambda scenario: scenario["rail_rect"].update(width=287),
            "must have rail width 288",
        ),
        (
            "course-tree-long-label-1280",
            lambda scenario: scenario["article_rect"].update(width=671),
            "article width must be at least 672",
        ),
        (
            "course-tree-long-label-1312",
            lambda scenario: scenario.update(document_overflow=2),
            "document overflow must be at most 1",
        ),
        (
            "course-tree-long-label-1312",
            lambda scenario: scenario["title_containment"].update(contained=False),
            "current title must be contained",
        ),
    ],
)
def test_render_debug_report_validates_responsive_course_rail_boundaries(
    tmp_path: Path,
    scenario_id: str,
    mutation: object,
    expected_failure: str,
) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        _learning_shell_html("<p>Responsive course rail scenario fixture.</p>"),
    )
    summary_path = debug_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    scenarios = _course_tree_scenarios(debug_dir)
    mutation(scenarios[scenario_id])
    summary["scenarios"] = scenarios
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    scenario_check = next(
        check
        for check in report["checks"]
        if check["id"] == f"course-tree-scenario:{scenario_id}"
    )
    assert report["ok"] is False
    assert scenario_check["status"] == "fail"
    assert expected_failure in scenario_check["message"]


def test_merge_course_tree_scenarios_copies_evidence_into_primary_debug_dir(
    tmp_path: Path,
) -> None:
    debug_dir = tmp_path / "debug"
    scenario_debug_dir = tmp_path / "scenario-debug"
    debug_dir.mkdir()
    scenario_debug_dir.mkdir()
    (debug_dir / "summary.json").write_text(
        json.dumps({"captures": [{"page": "index"}]}),
        encoding="utf-8",
    )
    scenarios = _course_tree_scenarios(scenario_debug_dir)
    (scenario_debug_dir / "summary.json").write_text(
        json.dumps({"captures": [], "scenarios": scenarios}),
        encoding="utf-8",
    )

    summary_path = merge_course_tree_scenarios(debug_dir, scenario_debug_dir)

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["captures"] == [{"page": "index"}]
    assert set(summary["scenarios"]) == COURSE_TREE_SCENARIO_IDS
    for scenario_id in COURSE_TREE_SCENARIO_IDS:
        screenshot = f"{scenario_id}.png"
        assert summary["scenarios"][scenario_id]["screenshot"] == screenshot
        assert (debug_dir / screenshot).read_bytes() == b"png"


def test_render_debug_report_fails_when_capture_skin_selector_is_missing(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        """
        <!doctype html>
        <html>
          <body data-raya-skin="practice-lab">
            <main><p>Skin selector mismatch fixture.</p></main>
          </body>
        </html>
        """,
        skin="practice-lab",
        skin_css='[data-raya-skin="warm-academic"] { --raya-color-page: #ffffff; }\n',
    )

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    assert report["ok"] is False
    skin_checks = {
        check["id"]: check
        for check in report["checks"]
        if check["id"].startswith("capture-skin:index:")
    }
    assert skin_checks["capture-skin:index:desktop"]["status"] == "fail"
    assert skin_checks["capture-skin:index:mobile"]["status"] == "fail"
    assert "practice-lab" in skin_checks["capture-skin:index:desktop"]["message"]
    assert "[data-raya-skin=\"practice-lab\"]" in skin_checks[
        "capture-skin:index:desktop"
    ]["message"]


def test_render_debug_report_fails_when_capture_skin_is_missing(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        """
        <!doctype html>
        <html>
          <body>
            <main><p>Missing skin evidence fixture.</p></main>
          </body>
        </html>
        """,
        skin="",
    )

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    assert report["ok"] is False
    skin_checks = {
        check["id"]: check
        for check in report["checks"]
        if check["id"].startswith("capture-skin:index:")
    }
    assert skin_checks["capture-skin:index:desktop"]["status"] == "fail"
    assert skin_checks["capture-skin:index:mobile"]["status"] == "fail"
    assert "missing active skin" in skin_checks[
        "capture-skin:index:desktop"
    ]["message"]
    assert "missing active skin" in skin_checks["capture-skin:index:mobile"]["message"]
    assert "http://127.0.0.1/index.html" in skin_checks[
        "capture-skin:index:desktop"
    ]["message"]


def test_render_debug_report_fails_when_learning_shell_regions_are_missing(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        """
        <!doctype html>
        <html><head><link rel="stylesheet" href="_raya/render/skin.css"></head>
          <body data-raya-skin="warm-academic">
            <main><article>Missing learning shell.</article></main>
          </body>
        </html>
        """,
        skin="warm-academic",
    )

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    checks = {check["id"]: check for check in report["checks"]}
    assert checks["site:learning-shell:index"]["status"] == "fail"
    assert "raya-course-map" in checks["site:learning-shell:index"]["message"]
    assert "raya-learning-rail" in checks["site:learning-shell:index"]["message"]


def test_render_debug_report_passes_when_learning_shell_regions_exist(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        _learning_shell_html("<p>Reader shell fixture.</p>"),
        skin="warm-academic",
    )

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    checks = {check["id"]: check for check in report["checks"]}
    assert "raya-top-command-bar" not in (site_dir / "index.html").read_text(
        encoding="utf-8"
    )
    assert checks["site:learning-shell:index"]["status"] == "pass"
    assert checks["site:learning-shell:index"]["details"]["ownership_failures"] == []


def test_render_debug_report_skips_discovery_command_bar_pages(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        _learning_shell_html("<p>Reader shell fixture.</p>"),
        skin="warm-academic",
    )
    discovery = site_dir / "discovery" / "index.html"
    discovery.parent.mkdir()
    discovery.write_text(
        """
        <!doctype html>
        <html><head><link rel="stylesheet" href="../_raya/render/skin.css"></head>
          <body data-raya-skin="warm-academic">
            <header class="raya-top-command-bar raya-discovery-command-bar"
              aria-label="Discovery tools">
                <button type="button">Search</button>
            </header>
            <main>
              <article>Discovery command surface.</article>
            </main>
          </body>
        </html>
        """,
        encoding="utf-8",
    )

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    checks = {check["id"]: check for check in report["checks"]}
    assert report["ok"] is True, report["diagnostics"]
    assert checks["site:learning-shell:index"]["status"] == "pass"
    assert checks.get("site:learning-shell:discovery:index.html") is None


def test_render_debug_report_allows_top_command_bar_mentions_in_reader_content(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        _learning_shell_html(
            """
            <!-- raya-top-command-bar is discussed as legacy markup. -->
            <p>Reader prose may mention raya-top-command-bar.</p>
            <code>class="raya-top-command-bar"</code>
            """
        ),
        skin="warm-academic",
    )

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    checks = {check["id"]: check for check in report["checks"]}
    assert report["ok"] is True, report["diagnostics"]
    assert checks["site:learning-shell:index"]["status"] == "pass"


def test_render_debug_report_requires_collapsible_shell_controls(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        """
        <!doctype html>
        <html><head><link rel="stylesheet" href="_raya/render/skin.css"></head>
          <body data-raya-skin="warm-academic">
            <main id="raya-content" class="raya-learning-shell">
              <nav id="raya-course-map" class="raya-course-map" aria-label="Course map">
                <section class="raya-course-actions" aria-label="Course actions">
                </section>
              </nav>
              <article id="raya-article" class="raya-main-article"></article>
              <aside id="raya-learning-rail" class="raya-learning-rail"
                aria-label="Learning context"></aside>
            </main>
          </body>
        </html>
        """,
        skin="warm-academic",
    )

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    checks = {check["id"]: check for check in report["checks"]}
    shell_check = checks["site:learning-shell:index"]
    assert report["ok"] is False
    assert shell_check["status"] == "fail"
    assert "div#raya-course-map-body.raya-course-map-body" in shell_check["details"][
        "missing_selectors"
    ]
    assert "div.raya-course-map-navigation" in shell_check["details"][
        "missing_selectors"
    ]
    assert "section.raya-course-content" in shell_check["details"][
        "missing_selectors"
    ]
    assert "footer.raya-course-map-footer" in shell_check["details"][
        "missing_selectors"
    ]
    assert "div.raya-course-map-mini" in shell_check["details"][
        "missing_selectors"
    ]
    assert "button.raya-course-map-collapse" in shell_check["details"][
        "missing_selectors"
    ]
    assert "[data-raya-course-map-collapse]" in shell_check["details"][
        "missing_selectors"
    ]
    assert "button.raya-course-map-expand" in shell_check["details"][
        "missing_selectors"
    ]
    assert "[data-raya-course-map-expand]" in shell_check["details"][
        "missing_selectors"
    ]
    assert "[data-raya-course-map-toggle]" in shell_check["details"][
        "missing_selectors"
    ]


@pytest.mark.parametrize(
    ("old", "new", "missing_selector"),
    (
        (
            'class="raya-course-map-header"',
            'class="missing-course-map-header"',
            "header.raya-course-map-header",
        ),
        (
            'id="raya-course-map-body" class="raya-course-map-body"',
            'class="missing-course-map-body"',
            "div#raya-course-map-body.raya-course-map-body",
        ),
        (
            'class="raya-course-map-navigation"',
            'class="missing-course-map-navigation"',
            "div.raya-course-map-navigation",
        ),
        (
            "data-raya-course-map-navigation",
            "data-missing-course-map-navigation",
            "[data-raya-course-map-navigation]",
        ),
        (
            'class="raya-course-actions"',
            'class="missing-course-actions"',
            "section.raya-course-actions",
        ),
        (
            'class="raya-course-content"',
            'class="missing-course-content"',
            "section.raya-course-content",
        ),
        (
            'class="raya-course-map-footer"',
            'class="missing-course-map-footer"',
            "footer.raya-course-map-footer",
        ),
        (
            'class="raya-course-map-mini"',
            'class="missing-course-map-mini"',
            "div.raya-course-map-mini",
        ),
        (
            "data-raya-course-map-mini",
            "data-missing-course-map-mini",
            "[data-raya-course-map-mini]",
        ),
        (
            'class="raya-course-map-collapse"',
            'class="missing-course-map-collapse"',
            "button.raya-course-map-collapse",
        ),
        (
            "data-raya-course-map-toggle data-raya-course-map-collapse",
            "data-raya-course-map-toggle",
            "[data-raya-course-map-collapse]",
        ),
        (
            'class="raya-course-map-expand"',
            'class="missing-course-map-expand"',
            "button.raya-course-map-expand",
        ),
        (
            "data-raya-course-map-toggle data-raya-course-map-expand",
            "data-raya-course-map-toggle",
            "[data-raya-course-map-expand]",
        ),
    ),
)
def test_render_debug_report_requires_each_dedicated_course_map_region(
    tmp_path: Path,
    old: str,
    new: str,
    missing_selector: str,
) -> None:
    html = _learning_shell_html("<p>Reader shell fixture.</p>")
    assert old in html
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        html.replace(old, new, 1),
        skin="warm-academic",
    )

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    checks = {check["id"]: check for check in report["checks"]}
    shell_check = checks["site:learning-shell:index"]
    assert shell_check["status"] == "fail"
    assert missing_selector in shell_check["details"]["missing_selectors"]


@pytest.mark.parametrize(
    ("layout", "expected_failure"),
    (
        (
            "expand-outside-mini",
            "course map mini rail must own [data-raya-course-map-expand]",
        ),
        (
            "collapse-outside-header",
            "course map collapse control must be inside",
        ),
        (
            "body-outside-map",
            "course map body must be a direct child",
        ),
        (
            "wrong-direct-order",
            "course map direct children must be ordered",
        ),
        (
            "navigation-outside-body",
            "course map body must own [data-raya-course-map-navigation]",
        ),
        (
            "footer-outside-body",
            "course map body must own .raya-course-map-footer",
        ),
        (
            "actions-outside-navigation",
            "course map navigation must own .raya-course-actions",
        ),
        (
            "content-outside-navigation",
            "course map navigation must own .raya-course-content",
        ),
        (
            "navigation-wrapped",
            "course map body direct children must be ordered navigation, footer",
        ),
        (
            "wrong-body-order",
            "course map body direct children must be ordered navigation, footer",
        ),
        (
            "wrong-navigation-order",
            "course map navigation direct children must be ordered actions, content",
        ),
        (
            "filter-inside-actions",
            "course map content must own [data-raya-course-map-filter]",
        ),
        (
            "tree-inside-actions",
            "course map content must own #raya-course-map-list",
        ),
        (
            "footer-inside-actions",
            "course map body direct children must be ordered navigation, footer",
        ),
    ),
)
def test_render_debug_report_rejects_invalid_course_map_ownership(
    tmp_path: Path,
    layout: str,
    expected_failure: str,
) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        _learning_shell_html(
            "<p>Reader shell fixture.</p>", course_map_layout=layout
        ),
        skin="warm-academic",
    )

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    checks = {check["id"]: check for check in report["checks"]}
    shell_check = checks["site:learning-shell:index"]
    assert shell_check["status"] == "fail"
    assert shell_check["details"]["missing_selectors"] == []
    assert any(
        expected_failure in failure
        for failure in shell_check["details"]["ownership_failures"]
    )


def test_render_debug_report_fails_when_learning_shell_ids_are_missing(
    tmp_path: Path,
) -> None:
    html = _learning_shell_html("<p>Reader shell fixture.</p>")
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        html.replace('id="raya-content"', "", 1).replace(
            'id="raya-article"', "", 1
        ),
        skin="warm-academic",
    )

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    checks = {check["id"]: check for check in report["checks"]}
    shell_check = checks["site:learning-shell:index"]
    assert shell_check["status"] == "fail"
    assert shell_check["details"]["missing_classes"] == []
    assert shell_check["details"]["missing_ids"] == [
        "raya-content",
        "raya-article",
    ]
    assert "raya-content" in shell_check["message"]
    assert "raya-article" in shell_check["message"]


def test_render_debug_report_fails_when_learning_shell_landmarks_are_malformed(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        """
        <!doctype html>
        <html><head><link rel="stylesheet" href="_raya/render/skin.css"></head>
          <body data-raya-skin="warm-academic">
            <section id="raya-content" class="raya-learning-shell">
              <div class="raya-course-map" aria-label="Course map"></div>
              <div id="raya-article" class="raya-main-article"></div>
              <section class="raya-learning-rail" aria-label="Learning context"></section>
            </section>
          </body>
        </html>
        """,
        skin="warm-academic",
    )

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    checks = {check["id"]: check for check in report["checks"]}
    shell_check = checks["site:learning-shell:index"]
    assert shell_check["status"] == "fail"
    assert shell_check["details"]["missing_selectors"] == [
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
    ]


def test_render_debug_report_rejects_learning_shell_regions_outside_elements(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        """
        <!doctype html>
        <html><head><link rel="stylesheet" href="_raya/render/skin.css"></head>
          <body data-raya-skin="warm-academic">
            <!-- raya-learning-shell raya-course-map raya-course-actions -->
            <main class="raya-learning-shell">
              <article>
                <p>raya-main-article raya-learning-rail raya-course-map-header
                  raya-course-map-navigation raya-course-content
                  raya-course-map-footer raya-course-map-mini appear only in prose.</p>
                <code>raya-course-map</code>
                <script>const ignored = "raya-learning-shell";</script>
              </article>
            </main>
          </body>
        </html>
        """,
        skin="warm-academic",
    )

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    checks = {check["id"]: check for check in report["checks"]}
    shell_check = checks["site:learning-shell:index"]
    assert shell_check["status"] == "fail"
    assert set(shell_check["details"]["missing_classes"]) == {
        "raya-course-map",
        "raya-course-map-header",
        "raya-course-map-navigation",
        "raya-course-actions",
        "raya-course-content",
        "raya-course-map-footer",
        "raya-course-map-mini",
        "raya-main-article",
        "raya-learning-rail",
    }


def test_render_debug_report_rejects_top_command_bar_on_reader_pages(
    tmp_path: Path,
) -> None:
    html = _learning_shell_html("<p>Reader page with forbidden top bar.</p>").replace(
        '<main id="raya-content" class="raya-learning-shell">',
        (
            '<header class="raya-top-command-bar" aria-label="Course tools"></header>'
            '<main id="raya-content" class="raya-learning-shell">'
        ),
    )
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        html,
        skin="warm-academic",
    )

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    checks = {check["id"]: check for check in report["checks"]}
    shell_check = checks["site:learning-shell:index"]
    assert shell_check["status"] == "fail"
    assert "reader page must not render .raya-top-command-bar" in shell_check[
        "details"
    ]["missing_selectors"]


def test_render_debug_report_fails_when_copied_site_shell_regions_are_missing(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        _learning_shell_html("<p>Original shell fixture.</p>"),
        skin="warm-academic",
    )
    copied_site = tmp_path / "copied-site"
    copied_site.mkdir()
    _write_skin_css(copied_site)
    (copied_site / "index.html").write_text(
        """
        <!doctype html>
        <html><head><link rel="stylesheet" href="_raya/render/skin.css"></head>
          <body data-raya-skin="warm-academic">
            <main class="raya-learning-shell">
              <article>Copied site missing shell regions.</article>
            </main>
          </body>
        </html>
        """,
        encoding="utf-8",
    )

    report = inspect_render_debug(
        site_dir=site_dir,
        debug_dir=debug_dir,
        copied_site_dir=copied_site,
    )

    checks = {check["id"]: check for check in report["checks"]}
    shell_check = checks["copied-site:learning-shell:index"]
    assert report["ok"] is False
    assert shell_check["status"] == "fail"
    assert "raya-course-map" in shell_check["message"]
    assert "raya-learning-rail" in shell_check["message"]


def test_render_debug_report_uses_relative_html_paths_for_shell_check_ids(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        _learning_shell_html("<p>Top page.</p>"),
        skin="warm-academic",
    )
    first = site_dir / "alpha" / "lesson"
    second = site_dir / "beta" / "lesson"
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    (first / "index.html").write_text(
        _learning_shell_html("<p>First nested lesson.</p>"),
        encoding="utf-8",
    )
    (second / "index.html").write_text(
        _learning_shell_html("<p>Second nested lesson.</p>"),
        encoding="utf-8",
    )

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    check_ids = {check["id"] for check in report["checks"]}
    assert {
        "site:learning-shell:index",
        "site:learning-shell:alpha:lesson:index.html",
        "site:learning-shell:beta:lesson:index.html",
    } <= check_ids


def test_copy_static_site_rejects_destination_under_source(tmp_path: Path) -> None:
    source = tmp_path / "site"
    source.mkdir()
    (source / "index.html").write_text("<html></html>", encoding="utf-8")

    with pytest.raises(ValueError, match="destination must not be inside source"):
        copy_static_site(source, source / "copied")


def test_inspection_fails_on_copied_site_raw_visible_tex(tmp_path: Path) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        """
        <!doctype html>
        <html>
          <body>
            <main><p>Clean generated page.</p></main>
          </body>
        </html>
        """,
    )
    copied_site = tmp_path / "copied-site"
    copied_site.mkdir()
    (copied_site / "index.html").write_text(
        """
        <!doctype html>
        <html>
          <body>
            <main>
              <p>Visible math leaked as $x^2$ in body text.</p>
              <code>$y^2$ is only a code sample.</code>
            </main>
          </body>
        </html>
        """,
        encoding="utf-8",
    )

    report = inspect_render_debug(
        site_dir=site_dir,
        debug_dir=debug_dir,
        copied_site_dir=copied_site,
    )

    raw_tex_diagnostics = [
        diagnostic
        for diagnostic in report["diagnostics"]
        if "raw visible TeX" in diagnostic["message"]
    ]
    assert report["ok"] is False
    assert raw_tex_diagnostics
    assert all(str(copied_site) in diagnostic["path"] for diagnostic in raw_tex_diagnostics)
    assert any("$x^2$" in diagnostic["message"] for diagnostic in raw_tex_diagnostics)
    assert all("$y^2$" not in diagnostic["message"] for diagnostic in raw_tex_diagnostics)


def test_inspection_fails_on_real_blocked_renderer_resource(tmp_path: Path) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        """
        <!doctype html>
        <html>
          <head>
            <script src="https://cdn.jsdelivr.net/npm/mathjax/tex-chtml.js"></script>
          </head>
          <body><main><p>Renderer dependency fixture.</p></main></body>
        </html>
        """,
    )

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    assert report["ok"] is False
    assert any(
        "browser-side or external renderer dependency" in diagnostic["message"]
        for diagnostic in report["diagnostics"]
    )


def test_render_debug_report_enriches_numbered_content_from_index(
    tmp_path: Path,
) -> None:
    site = tmp_path / "site"
    debug = tmp_path / "debug"
    site.mkdir()
    debug.mkdir()
    _write_skin_css(site)
    data = site / "data"
    data.mkdir()
    (data / "numbered-objects.json").write_text(
        json.dumps(
            {
                "version": 1,
                "course_id": "debug-demo",
                "objects": [
                    {
                        "id": "main-theorem",
                        "family": "theorem",
                        "sequence": "theorem",
                        "label": "Theorem",
                        "number": "1",
                        "reference_text": "Theorem 1",
                        "anchor": "raya-object-main-theorem",
                        "title": "Main",
                        "source_path": "course/0_index.md",
                        "page_id": "index",
                        "page_title": "Index",
                        "page_output_path": "index.html",
                        "href": "#raya-object-main-theorem",
                        "style": "margin",
                    }
                ],
                "by_id": {"main-theorem": 0},
            }
        ),
        encoding="utf-8",
    )
    (site / "index.html").write_text(
        _learning_shell_html(
            '<section class="raya-numbered-object" '
            'id="raya-object-main-theorem" data-object-id="main-theorem">'
            '<span class="raya-numbered-object-reference">Theorem 1</span>'
            '</section><section class="raya-proof" id="raya-proof-proof-main">'
            '<div class="raya-proof-heading"><span class="raya-proof-reference">'
            "Proof of Theorem 1</span></div></section>"
        ),
        encoding="utf-8",
    )
    reader_ux = site / "reader-ux"
    reader_ux.mkdir()
    (reader_ux / "index.html").write_text(
        _learning_shell_html(
            '<details class="raya-static-environment raya-static-environment--hint" '
            'id="raya-static-environment-hint-orthogonal-activity">'
            '<summary class="raya-static-environment-heading">Hint for Activity 4.1</summary>'
            '<div class="raya-static-environment-body">'
            "<p>Compare the projection formula before expanding the matrix product.</p>"
            "</div>"
            "</details>"
            '<details class="raya-static-environment raya-static-environment--solution" '
            'id="raya-static-environment-solution-orthogonal-activity">'
            '<summary class="raya-static-environment-heading">Solution of Activity 4.1</summary>'
            '<div class="raya-static-environment-body">'
            f"<p>{SOLUTION_BODY_EVIDENCE} while the projection line stays fixed.</p>"
            "</div>"
            "</details>"
            '<details class="raya-static-environment raya-static-environment--answer" '
            'id="raya-static-environment-answer-orthogonal-activity">'
            '<summary class="raya-static-environment-heading">Answer to Activity 4.1</summary>'
            '<div class="raya-static-environment-body">'
            "<p>The residual vector is orthogonal to the direction vector.</p>"
            "</div>"
            "</details>",
            skin="practice-lab",
        ),
        encoding="utf-8",
    )
    static_environments = _reader_static_environments()
    for name in (
        "desktop-index.png",
        "mobile-index.png",
        "desktop-reader-ux.png",
        "mobile-reader-ux.png",
    ):
        (debug / name).write_bytes(b"png")
    (debug / "summary.json").write_text(
        json.dumps(
            {
                "captures": [
                    {
                        "page": "index",
                        "url": "http://127.0.0.1/index.html",
                        "viewport": {"name": "desktop", "width": 1280, "height": 900},
                        "screenshot": str(debug / "desktop-index.png"),
                        "mathjax_container_count": 0,
                        "raw_tex_visible": False,
                        "raw_tex_markers": [],
                        "external_requests": [],
                        "horizontal_overflow": 0,
                        "skin": "warm-academic",
                        "numbered_content": {
                            "objects": [
                                {
                                    "id": "main-theorem",
                                    "anchor": "raya-object-main-theorem",
                                    "label": "Theorem 1",
                                    "title": "Main",
                                    "text": "Theorem 1",
                                }
                            ],
                            "references": [],
                            "proofs": [
                                {
                                    "id": "raya-proof-proof-main",
                                    "heading": "Proof of Theorem 1.",
                                    "target_text": "Theorem 1",
                                    "target_id": "",
                                }
                            ],
                        },
                        "staticEnvironments": [],
                    },
                    {
                        "page": "index",
                        "url": "http://127.0.0.1/index.html",
                        "viewport": {"name": "mobile", "width": 390, "height": 844},
                        "screenshot": str(debug / "mobile-index.png"),
                        "mathjax_container_count": 0,
                        "raw_tex_visible": False,
                        "raw_tex_markers": [],
                        "external_requests": [],
                        "horizontal_overflow": 0,
                        "skin": "warm-academic",
                        "numbered_content": {
                            "objects": [],
                            "references": [],
                            "proofs": [],
                        },
                        "staticEnvironments": [],
                    },
                    {
                        "page": "reader-ux",
                        "url": "http://127.0.0.1/reader-ux/",
                        "viewport": {"name": "desktop", "width": 1280, "height": 900},
                        "screenshot": str(debug / "desktop-reader-ux.png"),
                        "mathjax_container_count": 0,
                        "raw_tex_visible": False,
                        "raw_tex_markers": [],
                        "external_requests": [],
                        "horizontal_overflow": 0,
                        "skin": "practice-lab",
                        "numbered_content": {
                            "objects": [],
                            "references": [],
                            "proofs": [],
                        },
                        "staticEnvironments": static_environments,
                    },
                    {
                        "page": "reader-ux",
                        "url": "http://127.0.0.1/reader-ux/",
                        "viewport": {"name": "mobile", "width": 390, "height": 844},
                        "screenshot": str(debug / "mobile-reader-ux.png"),
                        "mathjax_container_count": 0,
                        "raw_tex_visible": False,
                        "raw_tex_markers": [],
                        "external_requests": [],
                        "horizontal_overflow": 0,
                        "skin": "practice-lab",
                        "numbered_content": {
                            "objects": [],
                            "references": [],
                            "proofs": [],
                        },
                        "staticEnvironments": static_environments,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    report = inspect_render_debug(site_dir=site, debug_dir=debug)

    assert report["ok"] is True, report["diagnostics"]
    numbered_check = next(
        check
        for check in report["checks"]
        if check["id"] == "numbered-content:index:desktop"
    )
    assert numbered_check["details"]["object_count"] == 1
    assert numbered_check["details"]["proof_targets"] == [
        {
            "proof_id": "raya-proof-proof-main",
            "target_id": "main-theorem",
            "target_text": "Theorem 1",
        }
    ]
    assert {check["id"] for check in report["checks"]} >= {
        "static-environment:reader-ux:desktop:hint",
        "static-environment:reader-ux:desktop:solution",
        "static-environment:reader-ux:desktop:answer",
        "static-environment:reader-ux:mobile:hint",
        "static-environment:reader-ux:mobile:solution",
        "static-environment:reader-ux:mobile:answer",
    }
    assert "Theorem 1" in (debug / "index.html").read_text(encoding="utf-8")


def test_render_debug_report_fails_when_mobile_static_environment_class_is_missing(
    tmp_path: Path,
) -> None:
    site = tmp_path / "site"
    debug = tmp_path / "debug"
    site.mkdir()
    debug.mkdir()
    (site / "index.html").write_text("<!doctype html><html></html>", encoding="utf-8")
    reader_ux = site / "reader-ux"
    reader_ux.mkdir()
    (reader_ux / "index.html").write_text(
        "<!doctype html><html><body>Reader UX</body></html>",
        encoding="utf-8",
    )
    static_environments = _reader_static_environments()
    mobile_static_environments = [
        item.copy() for item in static_environments
    ]
    mobile_static_environments[2]["className"] = "raya-static-environment"
    for name in (
        "desktop-index.png",
        "mobile-index.png",
        "desktop-reader-ux.png",
        "mobile-reader-ux.png",
    ):
        (debug / name).write_bytes(b"png")
    captures = []
    for page, viewport, screenshot, evidence in (
        ("index", "desktop", "desktop-index.png", []),
        ("index", "mobile", "mobile-index.png", []),
        ("reader-ux", "desktop", "desktop-reader-ux.png", static_environments),
        ("reader-ux", "mobile", "mobile-reader-ux.png", mobile_static_environments),
    ):
        captures.append(
            {
                "page": page,
                "url": f"http://127.0.0.1/{page}/",
                "viewport": {
                    "name": viewport,
                    "width": 1280 if viewport == "desktop" else 390,
                    "height": 900 if viewport == "desktop" else 844,
                },
                "screenshot": str(debug / screenshot),
                "mathjax_container_count": 0,
                "raw_tex_visible": False,
                "raw_tex_markers": [],
                "external_requests": [],
                "horizontal_overflow": 0,
                "numbered_content": {"objects": [], "references": [], "proofs": []},
                "staticEnvironments": evidence,
            }
        )
    (debug / "summary.json").write_text(
        json.dumps({"captures": captures}),
        encoding="utf-8",
    )

    report = inspect_render_debug(site_dir=site, debug_dir=debug)

    assert report["ok"] is False
    answer_check = next(
        check
        for check in report["checks"]
        if check["id"] == "static-environment:reader-ux:mobile:answer"
    )
    assert answer_check["status"] == "fail"
    assert any(
        "raya-static-environment--answer" in failure
        for failure in answer_check["details"]["failures"]
    )


def test_render_debug_report_fails_when_reader_ux_viewport_capture_is_missing(
    tmp_path: Path,
) -> None:
    debug = tmp_path / "debug"
    site, debug = _write_reader_ux_report_fixture(
        tmp_path,
        [_reader_capture(debug, "desktop")],
    )

    report = inspect_render_debug(site_dir=site, debug_dir=debug)

    assert report["ok"] is False
    mobile_hint = next(
        check
        for check in report["checks"]
        if check["id"] == "static-environment:reader-ux:mobile:hint"
    )
    assert mobile_hint["status"] == "fail"
    assert mobile_hint["details"]["failures"] == ["missing reader-ux mobile capture"]


def test_render_debug_report_fails_when_reader_ux_static_environments_are_empty(
    tmp_path: Path,
) -> None:
    debug = tmp_path / "debug"
    site, debug = _write_reader_ux_report_fixture(
        tmp_path,
        [
            _reader_capture(debug, "desktop"),
            _reader_capture(debug, "mobile", static_environments=[]),
        ],
    )

    report = inspect_render_debug(site_dir=site, debug_dir=debug)

    assert report["ok"] is False
    mobile_solution = next(
        check
        for check in report["checks"]
        if check["id"] == "static-environment:reader-ux:mobile:solution"
    )
    assert mobile_solution["status"] == "fail"
    assert mobile_solution["details"]["failures"] == [
        "missing static environment id "
        "'raya-static-environment-solution-orthogonal-activity'"
    ]


def test_render_debug_report_fails_when_reader_ux_static_environments_are_missing(
    tmp_path: Path,
) -> None:
    debug = tmp_path / "debug"
    site, debug = _write_reader_ux_report_fixture(
        tmp_path,
        [
            _reader_capture(debug, "desktop"),
            _reader_capture(debug, "mobile", include_static_environments=False),
        ],
    )

    report = inspect_render_debug(site_dir=site, debug_dir=debug)

    assert report["ok"] is False
    mobile_answer = next(
        check
        for check in report["checks"]
        if check["id"] == "static-environment:reader-ux:mobile:answer"
    )
    assert mobile_answer["status"] == "fail"
    assert mobile_answer["details"]["failures"] == [
        "missing staticEnvironments evidence"
    ]


def test_render_debug_report_fails_when_solution_body_evidence_is_missing(
    tmp_path: Path,
) -> None:
    debug = tmp_path / "debug"
    heading_only = _reader_static_environments(
        solution_text="Solution of Activity 4.1"
    )
    site, debug = _write_reader_ux_report_fixture(
        tmp_path,
        [
            _reader_capture(debug, "desktop"),
            _reader_capture(debug, "mobile", static_environments=heading_only),
        ],
    )

    report = inspect_render_debug(site_dir=site, debug_dir=debug)

    assert report["ok"] is False
    mobile_solution = next(
        check
        for check in report["checks"]
        if check["id"] == "static-environment:reader-ux:mobile:solution"
    )
    assert mobile_solution["status"] == "fail"
    assert any(
        SOLUTION_BODY_EVIDENCE in failure
        for failure in mobile_solution["details"]["failures"]
    )


def test_render_debug_report_fails_when_capture_lacks_numbered_content(
    tmp_path: Path,
) -> None:
    site = tmp_path / "site"
    debug = tmp_path / "debug"
    site.mkdir()
    debug.mkdir()
    (site / "index.html").write_text("<!doctype html><html></html>", encoding="utf-8")
    screenshot = debug / "desktop-index.png"
    screenshot.write_bytes(b"png")
    (debug / "summary.json").write_text(
        json.dumps(
            {
                "captures": [
                    {
                        "page": "index",
                        "url": "http://127.0.0.1/index.html",
                        "viewport": {"name": "desktop", "width": 1280, "height": 900},
                        "screenshot": str(screenshot),
                        "mathjax_container_count": 0,
                        "raw_tex_visible": False,
                        "raw_tex_markers": [],
                        "external_requests": [],
                        "horizontal_overflow": 0,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = inspect_render_debug(site_dir=site, debug_dir=debug)

    assert report["ok"] is False
    numbered_check = next(
        check
        for check in report["checks"]
        if check["id"] == "numbered-content:index:desktop"
    )
    assert numbered_check["status"] == "fail"
    assert "missing numbered content evidence" in numbered_check["message"]
    assert (
        numbered_check["next_action"]
        == "Regenerate render debug capture artifacts."
    )
    assert any(
        diagnostic["check_id"] == "numbered-content:index:desktop"
        and "missing numbered content evidence" in diagnostic["message"]
        for diagnostic in report["diagnostics"]
    )


def test_render_debug_report_requires_numbered_index_for_proof_enrichment(
    tmp_path: Path,
) -> None:
    site = tmp_path / "site"
    debug = tmp_path / "debug"
    site.mkdir()
    debug.mkdir()
    (site / "index.html").write_text("<!doctype html><html></html>", encoding="utf-8")
    for name in ("desktop-index.png", "mobile-index.png"):
        (debug / name).write_bytes(b"png")
    (debug / "summary.json").write_text(
        json.dumps(
            {
                "captures": [
                    {
                        "page": "index",
                        "url": "http://127.0.0.1/index.html",
                        "viewport": {"name": "desktop", "width": 1280, "height": 900},
                        "screenshot": str(debug / "desktop-index.png"),
                        "mathjax_container_count": 0,
                        "raw_tex_visible": False,
                        "raw_tex_markers": [],
                        "external_requests": [],
                        "horizontal_overflow": 0,
                        "numbered_content": {
                            "objects": [],
                            "references": [],
                            "proofs": [
                                {
                                    "id": "raya-proof-proof-main",
                                    "heading": "Proof of Theorem 1.",
                                    "target_text": "Theorem 1",
                                    "target_id": "",
                                }
                            ],
                        },
                    },
                    {
                        "page": "index",
                        "url": "http://127.0.0.1/index.html",
                        "viewport": {"name": "mobile", "width": 390, "height": 844},
                        "screenshot": str(debug / "mobile-index.png"),
                        "mathjax_container_count": 0,
                        "raw_tex_visible": False,
                        "raw_tex_markers": [],
                        "external_requests": [],
                        "horizontal_overflow": 0,
                        "numbered_content": {
                            "objects": [],
                            "references": [],
                            "proofs": [],
                        },
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    report = inspect_render_debug(site_dir=site, debug_dir=debug)

    assert report["ok"] is False
    index_check = next(
        check for check in report["checks"] if check["id"] == "numbered-content:index"
    )
    assert index_check["status"] == "fail"
    assert "data/numbered-objects.json is missing" in index_check["message"]
    assert (
        index_check["next_action"]
        == "Rebuild the static site so data/numbered-objects.json exists."
    )


def test_render_debug_report_fails_when_numbered_index_is_missing_for_objects(
    tmp_path: Path,
) -> None:
    site = tmp_path / "site"
    debug = tmp_path / "debug"
    site.mkdir()
    debug.mkdir()
    (site / "index.html").write_text(
        '<!doctype html><html><body><section class="raya-numbered-object" '
        'id="raya-object-main-theorem" data-object-id="main-theorem">'
        '<span class="raya-numbered-object-reference">Theorem 1</span>'
        '</section><p><a href="#raya-object-main-theorem">Theorem 1</a></p>'
        "</body></html>",
        encoding="utf-8",
    )
    (debug / "desktop-index.png").write_bytes(b"png")
    (debug / "summary.json").write_text(
        json.dumps(
            {
                "captures": [
                    {
                        "page": "index",
                        "url": "http://127.0.0.1/index.html",
                        "viewport": {"name": "desktop", "width": 1280, "height": 900},
                        "screenshot": str(debug / "desktop-index.png"),
                        "mathjax_container_count": 0,
                        "raw_tex_visible": False,
                        "raw_tex_markers": [],
                        "external_requests": [],
                        "horizontal_overflow": 0,
                        "numbered_content": {
                            "objects": [
                                {
                                    "id": "main-theorem",
                                    "reference_text": "Theorem 1",
                                    "href": "#raya-object-main-theorem",
                                }
                            ],
                            "references": [
                                {
                                    "text": "Theorem 1",
                                    "href": "#raya-object-main-theorem",
                                }
                            ],
                            "proofs": [],
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = inspect_render_debug(site_dir=site, debug_dir=debug)

    assert report["ok"] is False
    index_check = next(
        check for check in report["checks"] if check["id"] == "numbered-content:index"
    )
    assert index_check["status"] == "fail"
    assert "data/numbered-objects.json is missing" in index_check["message"]


def test_render_debug_report_fails_when_proof_target_text_is_not_in_index(
    tmp_path: Path,
) -> None:
    site = tmp_path / "site"
    debug = tmp_path / "debug"
    site.mkdir()
    debug.mkdir()
    data = site / "data"
    data.mkdir()
    (data / "numbered-objects.json").write_text(
        json.dumps(
            {
                "version": 1,
                "course_id": "debug-demo",
                "objects": [
                    {
                        "id": "main-theorem",
                        "family": "theorem",
                        "sequence": "theorem",
                        "label": "Theorem",
                        "number": "1",
                        "reference_text": "Theorem 1",
                        "anchor": "raya-object-main-theorem",
                        "title": "Main",
                        "source_path": "course/0_index.md",
                        "page_id": "index",
                        "page_title": "Index",
                        "page_output_path": "index.html",
                        "href": "#raya-object-main-theorem",
                        "style": "margin",
                    }
                ],
                "by_id": {"main-theorem": 0},
            }
        ),
        encoding="utf-8",
    )
    (site / "index.html").write_text("<!doctype html><html></html>", encoding="utf-8")
    screenshot = debug / "desktop-index.png"
    screenshot.write_bytes(b"png")
    (debug / "summary.json").write_text(
        json.dumps(
            {
                "captures": [
                    {
                        "page": "index",
                        "url": "http://127.0.0.1/index.html",
                        "viewport": {"name": "desktop", "width": 1280, "height": 900},
                        "screenshot": str(screenshot),
                        "mathjax_container_count": 0,
                        "raw_tex_visible": False,
                        "raw_tex_markers": [],
                        "external_requests": [],
                        "horizontal_overflow": 0,
                        "numbered_content": {
                            "objects": [],
                            "references": [],
                            "proofs": [
                                {
                                    "id": "raya-proof-proof-main",
                                    "heading": "Proof of Theorem 99.",
                                    "target_text": "Theorem 99",
                                    "target_id": "",
                                }
                            ],
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = inspect_render_debug(site_dir=site, debug_dir=debug)

    assert report["ok"] is False
    numbered_check = next(
        check
        for check in report["checks"]
        if check["id"] == "numbered-content:index:desktop"
    )
    assert numbered_check["status"] == "fail"
    assert any(
        "proof target text 'Theorem 99' could not be resolved from data/numbered-objects.json"
        in failure
        for failure in numbered_check["details"]["failures"]
    )
    assert any(
        diagnostic["check_id"] == "numbered-content:index:desktop"
        and "proof target text 'Theorem 99' could not be resolved"
        in diagnostic["message"]
        for diagnostic in report["diagnostics"]
    )


def test_copy_static_site_rejects_destination_containing_source(tmp_path: Path) -> None:
    work = tmp_path / "work"
    source = work / "site"
    source.mkdir(parents=True)
    sentinel = work / "sentinel.txt"
    (source / "index.html").write_text("<html></html>", encoding="utf-8")
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(ValueError, match="destination must not contain source"):
        copy_static_site(source, work)

    assert source.is_dir()
    assert (source / "index.html").is_file()
    assert sentinel.read_text(encoding="utf-8") == "keep"


def _write_debug_fixture(
    tmp_path: Path,
    index_html: str,
    *,
    skin: str = "warm-academic",
    skin_css: str | None = None,
) -> tuple[Path, Path]:
    site_dir = tmp_path / "site"
    debug_dir = tmp_path / "debug"
    site_dir.mkdir()
    debug_dir.mkdir()
    _write_skin_css(site_dir, css=skin_css)
    (site_dir / "index.html").write_text(index_html, encoding="utf-8")

    captures = []
    for viewport, screenshot in (
        ("desktop", "desktop-index.png"),
        ("mobile", "mobile-index.png"),
    ):
        screenshot_path = debug_dir / screenshot
        screenshot_path.write_bytes(b"png")
        captures.append(
            {
                "page": "index",
                "url": "http://127.0.0.1/index.html",
                "viewport": {
                    "name": viewport,
                    "width": 1280 if viewport == "desktop" else 390,
                    "height": 900 if viewport == "desktop" else 844,
                },
                "screenshot": str(screenshot_path),
                "mathjax_container_count": 0,
                "raw_tex_visible": False,
                "raw_tex_markers": [],
                "external_requests": [],
                "horizontal_overflow": 0,
                "skin": skin,
                "numbered_content": {"objects": [], "references": [], "proofs": []},
            }
        )
    (debug_dir / "summary.json").write_text(
        json.dumps({"captures": captures}),
        encoding="utf-8",
    )
    return site_dir, debug_dir


def _learning_shell_html(
    content: str,
    *,
    skin: str = "warm-academic",
    course_map_layout: str = "valid",
) -> str:
    course_map = _course_map_markup(course_map_layout)
    return f"""
    <!doctype html>
    <html><head><link rel="stylesheet" href="_raya/render/skin.css"></head>
      <body data-raya-skin="{skin}">
        <main id="raya-content" class="raya-learning-shell">
          {course_map}
          <article id="raya-article" class="raya-main-article">
            {content}
          </article>
          <aside id="raya-learning-rail" class="raya-learning-rail"
            aria-label="Learning context"></aside>
        </main>
      </body>
    </html>
    """


def _course_map_markup(layout: str) -> str:
    collapse = """
      <button class="raya-course-map-collapse" type="button"
        data-raya-course-map-toggle data-raya-course-map-collapse>
        Hide map
      </button>
    """
    header = f'<header class="raya-course-map-header">{collapse}</header>'
    empty_header = '<header class="raya-course-map-header"></header>'
    expand = """
      <button class="raya-course-map-expand" type="button"
        data-raya-course-map-toggle data-raya-course-map-expand>Map</button>
    """
    filter_control = """
      <label class="raya-course-map-filter-label"
        for="raya-course-map-filter">Filter map</label>
      <input id="raya-course-map-filter" class="raya-course-map-filter"
        data-raya-course-map-filter>
      <p class="raya-map-filter-empty" data-raya-map-filter-empty hidden>
        No map matches.
      </p>
    """
    tree = """
      <div id="raya-course-map-list" class="raya-course-map-list"></div>
    """
    footer = '<footer class="raya-course-map-footer"></footer>'
    actions = (
        '<section class="raya-course-actions" aria-label="Course actions">'
        f"{filter_control if layout == 'filter-inside-actions' else ''}"
        f"{tree if layout == 'tree-inside-actions' else ''}"
        f"{footer if layout == 'footer-inside-actions' else ''}"
        "</section>"
    )
    content = f"""
      <section class="raya-course-content" aria-label="Course content">
      {'' if layout == 'filter-inside-actions' else filter_control}
      {'' if layout == 'tree-inside-actions' else tree}
      </section>
    """
    navigation_children = (
        f"{content}{actions}"
        if layout == "wrong-navigation-order"
        else (
            f"{'' if layout == 'actions-outside-navigation' else actions}"
            f"{'' if layout == 'content-outside-navigation' else content}"
        )
    )
    navigation = (
        '<div class="raya-course-map-navigation" '
        'data-raya-course-map-navigation>'
        f"{navigation_children}"
        "</div>"
    )
    body_navigation = (
        f'<div class="course-map-navigation-wrapper">{navigation}</div>'
        if layout == "navigation-wrapped"
        else navigation
    )
    body_children = (
        f"{footer}{body_navigation}"
        if layout == "wrong-body-order"
        else (
            f"{'' if layout == 'navigation-outside-body' else body_navigation}"
            f"{actions if layout == 'actions-outside-navigation' else ''}"
            f"{content if layout == 'content-outside-navigation' else ''}"
            f"{'' if layout in {'footer-outside-body', 'footer-inside-actions'} else footer}"
        )
    )
    body = (
        '<div id="raya-course-map-body" class="raya-course-map-body">'
        f"{body_children}"
        "</div>"
    )
    mini = (
        '<div class="raya-course-map-mini" data-raya-course-map-mini>'
        f"{'' if layout == 'expand-outside-mini' else expand}"
        "</div>"
    )
    if layout == "collapse-outside-header":
        direct_children = f"{empty_header}{collapse}{body}{mini}"
    elif layout == "wrong-direct-order":
        direct_children = f"{header}{mini}{body}"
    elif layout == "body-outside-map":
        return (
            '<nav id="raya-course-map" class="raya-course-map" '
            f'aria-label="Course map">{header}{mini}</nav>{body}'
        )
    elif layout in {
        "valid",
        "expand-outside-mini",
        "navigation-outside-body",
        "footer-outside-body",
        "actions-outside-navigation",
        "content-outside-navigation",
        "navigation-wrapped",
        "wrong-body-order",
        "wrong-navigation-order",
        "filter-inside-actions",
        "tree-inside-actions",
        "footer-inside-actions",
    }:
        direct_children = (
            f"{header}{body}"
            f"{navigation if layout == 'navigation-outside-body' else ''}"
            f"{footer if layout == 'footer-outside-body' else ''}"
            f"{expand if layout == 'expand-outside-mini' else ''}"
            f"{mini}"
        )
    else:
        raise ValueError(f"unsupported course map layout: {layout}")
    return (
        '<nav id="raya-course-map" class="raya-course-map" '
        f'aria-label="Course map">{direct_children}</nav>'
    )


def _write_skin_css(site_dir: Path, *, css: str | None = None) -> None:
    skin_css = site_dir / "_raya" / "render" / "skin.css"
    skin_css.parent.mkdir(parents=True, exist_ok=True)
    skin_css.write_text(
        css
        if css is not None
        else (
            '[data-raya-skin="warm-academic"] { --raya-color-page: #ffffff; }\n'
            '[data-raya-skin="practice-lab"] { --raya-color-page: #ffffff; }\n'
        ),
        encoding="utf-8",
    )
