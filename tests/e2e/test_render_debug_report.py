from __future__ import annotations

import json
from pathlib import Path

import pytest

from raya_cli.render_debug_report import copy_static_site, inspect_render_debug


SOLUTION_BODY_EVIDENCE = "Scaling the direction vector changes the projection coefficient"


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
        """
        <!doctype html>
        <html>
          <body>
            <main>
              <p>This page documents cdn.jsdelivr.net and tex-chtml as examples.</p>
              <code>mathjax.js</code>
              <!-- startup.js appears in a comment, not a resource URL. -->
            </main>
          </body>
        </html>
        """,
    )

    report = inspect_render_debug(site_dir=site_dir, debug_dir=debug_dir)

    assert report["ok"] is True, report["diagnostics"]
    assert report["diagnostics"] == []


def test_render_debug_report_passes_when_skin_css_and_capture_skin_exist(
    tmp_path: Path,
) -> None:
    site_dir, debug_dir = _write_debug_fixture(
        tmp_path,
        """
        <!doctype html>
        <html>
          <body data-raya-skin="practice-lab">
            <main><p>Skin evidence fixture.</p></main>
          </body>
        </html>
        """,
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
        '<!doctype html><html><body><section class="raya-numbered-object" '
        'id="raya-object-main-theorem" data-object-id="main-theorem">'
        '<span class="raya-numbered-object-reference">Theorem 1</span>'
        '</section><section class="raya-proof" id="raya-proof-proof-main">'
        '<div class="raya-proof-heading"><span class="raya-proof-reference">'
        "Proof of Theorem 1</span></div></section>"
        "</body></html>",
        encoding="utf-8",
    )
    reader_ux = site / "reader-ux"
    reader_ux.mkdir()
    (reader_ux / "index.html").write_text(
        "<!doctype html><html><body>"
        '<aside class="raya-static-environment raya-static-environment--hint" '
        'id="raya-static-environment-hint-orthogonal-activity">'
        '<div class="raya-static-environment-heading">Hint for Activity 4.1</div>'
        "<p>Compare the projection formula before expanding the matrix product.</p>"
        "</aside>"
        '<aside class="raya-static-environment raya-static-environment--solution" '
        'id="raya-static-environment-solution-orthogonal-activity">'
        '<div class="raya-static-environment-heading">Solution of Activity 4.1</div>'
        f"<p>{SOLUTION_BODY_EVIDENCE} while the projection line stays fixed.</p>"
        "</aside>"
        '<aside class="raya-static-environment raya-static-environment--answer" '
        'id="raya-static-environment-answer-orthogonal-activity">'
        '<div class="raya-static-environment-heading">Answer to Activity 4.1</div>'
        "<p>The residual vector is orthogonal to the direction vector.</p>"
        "</aside>"
        "</body></html>",
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
