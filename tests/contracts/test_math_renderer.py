from __future__ import annotations

import os
import sys
from pathlib import Path

from raya_schema import ValidationReport
from raya_static.math_renderer import MathItem, MathRenderer


def test_inline_and_display_math_render_through_adapter() -> None:
    report = ValidationReport(context="math")
    source = Path("course/1_vectors/0_index.md")

    result = MathRenderer().render_many(
        [
            MathItem(
                id="inline-energy",
                tex="E = mc^2",
                display=False,
                source_path=source,
            ),
            MathItem(
                id="display-integral",
                tex="\\int_0^1 x^2\\,dx = \\frac{1}{3}",
                display=True,
                source_path=source,
            ),
        ],
        report=report,
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert set(result.html_by_id) == {"inline-energy", "display-integral"}
    assert "mjx-container" in result.html_by_id["inline-energy"]
    assert "MathJax" in result.html_by_id["inline-energy"]
    assert "mjx-container" in result.html_by_id["display-integral"]
    assert "MathJax" in result.html_by_id["display-integral"]
    assert "mjx-container" in result.css


def test_broken_tex_reports_source_context_and_returns_no_html() -> None:
    report = ValidationReport(context="math")
    source = Path("course/2_limits/0_index.md")

    result = MathRenderer().render_many(
        [
            MathItem(
                id="bad-fraction",
                tex="\\frac{1}{",
                display=False,
                source_path=source,
            ),
        ],
        report=report,
    )

    assert "bad-fraction" not in result.html_by_id
    assert not report.ok
    diagnostic = report.diagnostics[0]
    assert diagnostic.message == "Math rendering failed"
    assert diagnostic.path == source
    assert diagnostic.field == "math:bad-fraction"
    assert diagnostic.next_action
    assert "\\frac" in diagnostic.next_action or "MathJax" in diagnostic.next_action


def test_unknown_control_sequence_fails_unless_defined_by_newcommand() -> None:
    source = Path("course/3_macros/0_index.md")

    valid_report = ValidationReport(context="math")
    valid = MathRenderer().render_many(
        [
            MathItem(
                id="defined-macro",
                tex="\\newcommand{\\vect}[1]{\\mathbf{#1}}\\vect{x}",
                display=False,
                source_path=source,
            ),
        ],
        report=valid_report,
    )

    assert valid_report.ok, [
        diagnostic.format() for diagnostic in valid_report.diagnostics
    ]
    assert "mjx-container" in valid.html_by_id["defined-macro"]

    invalid_report = ValidationReport(context="math")
    invalid = MathRenderer().render_many(
        [
            MathItem(
                id="unknown-macro",
                tex="\\unknownmacro",
                display=False,
                source_path=source,
            ),
        ],
        report=invalid_report,
    )

    assert "unknown-macro" not in invalid.html_by_id
    assert not invalid_report.ok
    diagnostic = invalid_report.diagnostics[0]
    assert diagnostic.message == "Math rendering failed"
    assert diagnostic.path == source
    assert diagnostic.field == "math:unknown-macro"
    assert diagnostic.next_action
    assert "Undefined control sequence" in diagnostic.next_action
    assert "\\unknownmacro" in diagnostic.next_action


def test_empty_input_does_not_invoke_subprocess(tmp_path: Path) -> None:
    report = ValidationReport(context="math")
    missing_script = tmp_path / "missing-renderer.mjs"

    result = MathRenderer(
        node="definitely-not-a-node-command",
        script=missing_script,
    ).render_many([], report=report)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert result.html_by_id == {}
    assert result.css == ""


def test_invalid_output_reports_each_source_item(tmp_path: Path) -> None:
    script = tmp_path / "invalid_renderer.py"
    script.write_text(
        "from __future__ import annotations\n"
        "print('not json from renderer')\n",
        encoding="utf-8",
    )
    os.chmod(script, 0o755)

    first_source = Path("course/4_failures/0_index.md")
    second_source = Path("course/4_failures/1_more.md")
    report = ValidationReport(context="math")

    result = MathRenderer(node=sys.executable, script=script).render_many(
        [
            MathItem(
                id="first",
                tex="x",
                display=False,
                source_path=first_source,
            ),
            MathItem(
                id="second",
                tex="y",
                display=True,
                source_path=second_source,
            ),
        ],
        report=report,
    )

    assert result.html_by_id == {}
    assert result.css == ""
    assert not report.ok
    diagnostics = report.diagnostics
    assert [diagnostic.message for diagnostic in diagnostics] == [
        "Math renderer returned invalid JSON",
        "Math renderer returned invalid JSON",
    ]
    assert [diagnostic.path for diagnostic in diagnostics] == [
        first_source,
        second_source,
    ]
    assert [diagnostic.field for diagnostic in diagnostics] == [
        "math:first",
        "math:second",
    ]
    assert all(diagnostic.next_action for diagnostic in diagnostics)


def test_process_failure_reports_each_source_item(tmp_path: Path) -> None:
    source = Path("course/5_process/0_index.md")
    report = ValidationReport(context="math")

    result = MathRenderer(
        node=str(tmp_path / "missing-node"),
        script=tmp_path / "renderer.mjs",
    ).render_many(
        [
            MathItem(
                id="first",
                tex="x",
                display=False,
                source_path=source,
            ),
            MathItem(
                id="second",
                tex="y",
                display=True,
                source_path=source,
            ),
        ],
        report=report,
    )

    assert result.html_by_id == {}
    assert result.css == ""
    assert not report.ok
    assert [diagnostic.message for diagnostic in report.diagnostics] == [
        "Math renderer process failed",
        "Math renderer process failed",
    ]
    assert [diagnostic.path for diagnostic in report.diagnostics] == [source, source]
    assert [diagnostic.field for diagnostic in report.diagnostics] == [
        "math:first",
        "math:second",
    ]
    assert all(diagnostic.next_action for diagnostic in report.diagnostics)
