from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from raya_schema import ValidationReport
from raya_static.math_renderer import MathItem, MathRenderer


def _fake_renderer_script(
    tmp_path: Path,
    *,
    stdout: str | None,
    stderr: str = "",
    returncode: int = 0,
    sleep_seconds: float | None = None,
) -> Path:
    script = tmp_path / "fake_renderer.py"
    lines = [
        "from __future__ import annotations",
        "import sys",
        "import time",
        "sys.stdin.read()",
    ]
    if sleep_seconds is not None:
        lines.append(f"time.sleep({sleep_seconds!r})")
    if stderr:
        lines.append(f"sys.stderr.write({stderr!r})")
    if stdout is not None:
        lines.append(f"sys.stdout.write({stdout!r})")
    lines.append(f"raise SystemExit({returncode})")
    script.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(script, 0o755)
    return script


def _renderer_payload(
    *,
    rendered: list[dict[str, str]] | object | None = None,
    errors: list[dict[str, str]] | object | None = None,
    css: str | object = "mjx-container { display: inline-block; }",
) -> str:
    payload = {
        "rendered": [] if rendered is None else rendered,
        "errors": [] if errors is None else errors,
        "css": css,
    }
    return json.dumps(payload)


def _source_item(item_id: str, source_path: Path = Path("course/fake/0_index.md")) -> MathItem:
    return MathItem(id=item_id, tex="x", display=False, source_path=source_path)


def _assert_contract_failure_for(
    report: ValidationReport,
    result_ids: dict[str, str],
    *,
    message: str,
    fields: list[str],
) -> None:
    assert result_ids == {}
    assert not report.ok
    assert [diagnostic.message for diagnostic in report.diagnostics] == [
        message for _ in fields
    ]
    assert [diagnostic.field for diagnostic in report.diagnostics] == fields
    assert all(diagnostic.next_action for diagnostic in report.diagnostics)


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


def test_empty_id_does_not_invoke_subprocess(tmp_path: Path) -> None:
    report = ValidationReport(context="math")
    source = Path("course/invalid/0_index.md")

    result = MathRenderer(
        node=str(tmp_path / "missing-node"),
        script=tmp_path / "missing-renderer.mjs",
    ).render_many(
        [
            MathItem(
                id="",
                tex="x",
                display=False,
                source_path=source,
            )
        ],
        report=report,
    )

    assert result.html_by_id == {}
    assert result.css == ""
    assert not report.ok
    diagnostic = report.diagnostics[0]
    assert diagnostic.message == "Invalid math item id"
    assert diagnostic.path == source
    assert diagnostic.field == "math:"
    assert diagnostic.next_action


def test_duplicate_ids_do_not_invoke_subprocess(tmp_path: Path) -> None:
    report = ValidationReport(context="math")
    first_source = Path("course/duplicate/0_index.md")
    second_source = Path("course/duplicate/1_more.md")

    result = MathRenderer(
        node=str(tmp_path / "missing-node"),
        script=tmp_path / "missing-renderer.mjs",
    ).render_many(
        [
            _source_item("duplicate", first_source),
            _source_item("duplicate", second_source),
        ],
        report=report,
    )

    assert result.html_by_id == {}
    assert result.css == ""
    assert not report.ok
    diagnostic = report.diagnostics[0]
    assert diagnostic.message == "Duplicate math item id"
    assert diagnostic.path == second_source
    assert diagnostic.field == "math:duplicate"
    assert diagnostic.next_action


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


def test_timeout_reports_each_source_item(tmp_path: Path) -> None:
    script = _fake_renderer_script(tmp_path, stdout=None, sleep_seconds=1.0)
    source = Path("course/timeout/0_index.md")
    report = ValidationReport(context="math")

    result = MathRenderer(
        node=sys.executable,
        script=script,
        timeout_seconds=0.05,
    ).render_many(
        [
            _source_item("first", source),
            _source_item("second", source),
        ],
        report=report,
    )

    _assert_contract_failure_for(
        report,
        result.html_by_id,
        message="Math renderer process timed out",
        fields=["math:first", "math:second"],
    )
    assert result.css == ""
    assert all("timeout" in item.next_action.lower() for item in report.diagnostics)
    assert all("renderer process" in item.next_action for item in report.diagnostics)


def test_missing_stdout_reports_each_source_item(tmp_path: Path) -> None:
    script = _fake_renderer_script(tmp_path, stdout=None)
    report = ValidationReport(context="math")

    result = MathRenderer(node=sys.executable, script=script).render_many(
        [_source_item("first"), _source_item("second")],
        report=report,
    )

    _assert_contract_failure_for(
        report,
        result.html_by_id,
        message="Math renderer produced no output",
        fields=["math:first", "math:second"],
    )
    assert result.css == ""


def test_malformed_json_shape_reports_renderer_contract_failure(tmp_path: Path) -> None:
    script = _fake_renderer_script(
        tmp_path,
        stdout=_renderer_payload(rendered={"id": "first", "html": "<mjx-container />"}),
    )
    report = ValidationReport(context="math")

    result = MathRenderer(node=sys.executable, script=script).render_many(
        [_source_item("first")],
        report=report,
    )

    _assert_contract_failure_for(
        report,
        result.html_by_id,
        message="Math renderer returned malformed output",
        fields=["math:first"],
    )
    assert result.css == ""


def test_missing_requested_output_id_reports_renderer_contract_failure(tmp_path: Path) -> None:
    script = _fake_renderer_script(
        tmp_path,
        stdout=_renderer_payload(
            rendered=[{"id": "first", "html": "<mjx-container>first</mjx-container>"}]
        ),
    )
    report = ValidationReport(context="math")

    result = MathRenderer(node=sys.executable, script=script).render_many(
        [_source_item("first"), _source_item("second")],
        report=report,
    )

    assert result.html_by_id == {}
    assert result.css == ""
    assert not report.ok
    assert [diagnostic.message for diagnostic in report.diagnostics] == [
        "Math renderer returned missing output"
    ]
    assert report.diagnostics[0].field == "math:second"
    assert report.diagnostics[0].next_action


def test_empty_html_reports_renderer_contract_failure(tmp_path: Path) -> None:
    script = _fake_renderer_script(
        tmp_path,
        stdout=_renderer_payload(rendered=[{"id": "first", "html": ""}]),
    )
    report = ValidationReport(context="math")

    result = MathRenderer(node=sys.executable, script=script).render_many(
        [_source_item("first")],
        report=report,
    )

    _assert_contract_failure_for(
        report,
        result.html_by_id,
        message="Math renderer returned malformed output",
        fields=["math:first"],
    )
    assert result.css == ""


def test_empty_css_reports_renderer_contract_failure(tmp_path: Path) -> None:
    script = _fake_renderer_script(
        tmp_path,
        stdout=_renderer_payload(
            rendered=[{"id": "first", "html": "<mjx-container>first</mjx-container>"}],
            css="",
        ),
    )
    report = ValidationReport(context="math")

    result = MathRenderer(node=sys.executable, script=script).render_many(
        [_source_item("first")],
        report=report,
    )

    _assert_contract_failure_for(
        report,
        result.html_by_id,
        message="Math renderer returned malformed output",
        fields=["math:first"],
    )
    assert result.css == ""


def test_wrong_html_css_contract_reports_renderer_contract_failure(tmp_path: Path) -> None:
    script = _fake_renderer_script(
        tmp_path,
        stdout=_renderer_payload(
            rendered=[{"id": "first", "html": "<span>not mathjax</span>"}],
            css=".not-mathjax { color: red; }",
        ),
    )
    report = ValidationReport(context="math")

    result = MathRenderer(node=sys.executable, script=script).render_many(
        [_source_item("first")],
        report=report,
    )

    _assert_contract_failure_for(
        report,
        result.html_by_id,
        message="Math renderer returned malformed output",
        fields=["math:first"],
    )
    assert result.css == ""


def test_unknown_error_id_reports_renderer_contract_failure(tmp_path: Path) -> None:
    script = _fake_renderer_script(
        tmp_path,
        stdout=_renderer_payload(errors=[{"id": "unknown", "message": "bad id"}]),
        returncode=1,
    )
    report = ValidationReport(context="math")

    result = MathRenderer(node=sys.executable, script=script).render_many(
        [_source_item("first"), _source_item("second")],
        report=report,
    )

    _assert_contract_failure_for(
        report,
        result.html_by_id,
        message="Math renderer returned malformed output",
        fields=["math:first", "math:second"],
    )
    assert result.css == ""


def test_mixed_success_and_error_returns_no_html_or_css(tmp_path: Path) -> None:
    script = _fake_renderer_script(
        tmp_path,
        stdout=_renderer_payload(
            rendered=[{"id": "first", "html": "<mjx-container>first</mjx-container>"}],
            errors=[{"id": "second", "message": "Undefined control sequence \\bad"}],
        ),
        returncode=1,
    )
    report = ValidationReport(context="math")

    result = MathRenderer(node=sys.executable, script=script).render_many(
        [_source_item("first"), _source_item("second")],
        report=report,
    )

    assert result.html_by_id == {}
    assert result.css == ""
    assert not report.ok
    assert [diagnostic.message for diagnostic in report.diagnostics] == [
        "Math rendering failed"
    ]
    assert report.diagnostics[0].field == "math:second"
    assert report.diagnostics[0].next_action


def test_invalid_json_diagnostics_truncate_stdout_and_stderr(tmp_path: Path) -> None:
    script = _fake_renderer_script(
        tmp_path,
        stdout="out-" + ("x" * 1000),
        stderr="err-" + ("y" * 1000),
        returncode=2,
    )
    report = ValidationReport(context="math")

    result = MathRenderer(node=sys.executable, script=script).render_many(
        [_source_item("first")],
        report=report,
    )

    assert result.html_by_id == {}
    assert result.css == ""
    assert not report.ok
    assert report.diagnostics[0].message == "Math renderer returned invalid JSON"
    next_action = report.diagnostics[0].next_action
    assert next_action
    assert "[truncated]" in next_action
    assert len(next_action) < 700


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
