from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from raya_schema import ValidationReport


ROOT = Path(__file__).resolve().parents[4]
RENDER_SCRIPT = ROOT / "packages" / "static" / "scripts" / "render_math.mjs"
_MATHJAX_MARKER = "mjx-container"
_DETAIL_LIMIT = 180


@dataclass(frozen=True)
class MathItem:
    id: str
    tex: str
    display: bool
    source_path: Path


@dataclass(frozen=True)
class MathRenderResult:
    html_by_id: dict[str, str]
    css: str


class MathRenderer:
    def __init__(
        self,
        node: str = "node",
        script: Path = RENDER_SCRIPT,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.node = node
        self.script = script
        self.timeout_seconds = timeout_seconds

    def render_many(
        self,
        items: list[MathItem],
        *,
        report: ValidationReport,
    ) -> MathRenderResult:
        if not items:
            return MathRenderResult(html_by_id={}, css="")

        if not _validate_item_ids(items, report):
            return MathRenderResult(html_by_id={}, css="")

        payload = {
            "items": [
                {"id": item.id, "tex": item.tex, "display": item.display}
                for item in items
            ]
        }
        command = [self.node, str(self.script)]

        try:
            process = subprocess.run(
                command,
                input=json.dumps(payload),
                text=True,
                encoding="utf-8",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as error:
            _add_item_errors(
                report,
                items,
                "Math renderer process timed out",
                _timeout_next_action(command, error, self.timeout_seconds),
            )
            return MathRenderResult(html_by_id={}, css="")
        except OSError as error:
            _add_item_errors(
                report,
                items,
                "Math renderer process failed",
                (
                    "Check that the renderer process command is available "
                    f"({command[0]}): {_truncate(str(error))}"
                ),
            )
            return MathRenderResult(html_by_id={}, css="")

        if process.stdout == "":
            _add_item_errors(
                report,
                items,
                "Math renderer produced no output",
                _process_next_action(process),
            )
            return MathRenderResult(html_by_id={}, css="")

        try:
            output = json.loads(process.stdout)
        except json.JSONDecodeError as error:
            _add_item_errors(
                report,
                items,
                "Math renderer returned invalid JSON",
                _invalid_json_next_action(process, error),
            )
            return MathRenderResult(html_by_id={}, css="")

        parsed = _parse_renderer_output(output, items, report)
        if parsed is None:
            return MathRenderResult(html_by_id={}, css="")

        html_by_id, errors, css = parsed
        if errors:
            _add_renderer_errors(report, items, errors)
            return MathRenderResult(html_by_id={}, css="")

        if process.returncode != 0:
            _add_item_errors(
                report,
                items,
                "Math renderer process failed",
                _process_next_action(process),
            )
            return MathRenderResult(html_by_id={}, css="")

        requested_ids = {item.id for item in items}
        missing_ids = requested_ids - set(html_by_id)
        if missing_ids:
            by_id = {item.id: item for item in items}
            for item_id in sorted(missing_ids):
                item = by_id[item_id]
                report.add_error(
                    "Math renderer returned missing output",
                    path=item.source_path,
                    field=f"math:{item.id}",
                    next_action=(
                        "Check the MathJax renderer contract. "
                        f"No rendered HTML was returned for {item.id}."
                    ),
                )
            return MathRenderResult(html_by_id={}, css="")

        return MathRenderResult(html_by_id=html_by_id, css=css)


def _parse_renderer_output(
    output: Any,
    items: list[MathItem],
    report: ValidationReport,
) -> tuple[dict[str, str], list[dict[str, str]], str] | None:
    if not isinstance(output, dict):
        _add_malformed_output_errors(report, items)
        return None

    by_id = {item.id: item for item in items}
    requested_ids = set(by_id)
    raw_rendered = output.get("rendered")
    raw_errors = output.get("errors")
    css = output.get("css")
    if not isinstance(raw_rendered, list) or not isinstance(raw_errors, list):
        _add_malformed_output_errors(report, items)
        return None
    if not isinstance(css, str):
        _add_malformed_output_errors(report, items)
        return None
    if not css or _MATHJAX_MARKER not in css:
        _add_malformed_output_errors(report, items)
        return None

    html_by_id: dict[str, str] = {}
    for rendered in raw_rendered:
        if not isinstance(rendered, dict):
            _add_malformed_output_errors(report, items)
            return None
        item_id = rendered.get("id")
        html = rendered.get("html")
        if not isinstance(item_id, str) or not isinstance(html, str):
            _add_malformed_output_errors(report, items)
            return None
        if item_id not in requested_ids or item_id in html_by_id:
            _add_malformed_output_errors(report, items)
            return None
        if not html or _MATHJAX_MARKER not in html:
            _add_renderer_contract_error(
                report,
                by_id[item_id],
                (
                    "Check the MathJax renderer contract. Rendered HTML must "
                    "be non-empty MathJax output containing mjx-container."
                ),
            )
            return None
        html_by_id[item_id] = html

    errors: list[dict[str, str]] = []
    for error in raw_errors:
        if not isinstance(error, dict):
            _add_malformed_output_errors(report, items)
            return None
        item_id = error.get("id")
        message = error.get("message")
        if not isinstance(item_id, str) or not isinstance(message, str):
            _add_malformed_output_errors(report, items)
            return None
        if item_id not in requested_ids:
            _add_malformed_output_errors(report, items)
            return None
        errors.append({"id": item_id, "message": message})

    return html_by_id, errors, css


def _validate_item_ids(items: list[MathItem], report: ValidationReport) -> bool:
    seen: set[str] = set()
    valid = True
    for item in items:
        if item.id == "":
            report.add_error(
                "Invalid math item id",
                path=item.source_path,
                field="math:",
                next_action="Assign a non-empty stable ID before invoking MathJax.",
            )
            valid = False
            continue
        if item.id in seen:
            report.add_error(
                "Duplicate math item id",
                path=item.source_path,
                field=f"math:{item.id}",
                next_action=(
                    "Assign unique stable math IDs before invoking MathJax. "
                    f"The duplicate ID is {item.id}."
                ),
            )
            valid = False
            continue
        seen.add(item.id)
    return valid


def _add_renderer_errors(
    report: ValidationReport,
    items: list[MathItem],
    errors: list[dict[str, str]],
) -> None:
    by_id = {item.id: item for item in items}
    for error in errors:
        item = by_id[error["id"]]
        report.add_error(
            "Math rendering failed",
            path=item.source_path,
            field=f"math:{item.id}",
            next_action=(
                f"Fix the TeX for {item.id} near `{_tex_excerpt(item.tex)}`: "
                f"{error['message']}"
            ),
        )


def _add_malformed_output_errors(
    report: ValidationReport,
    items: list[MathItem],
) -> None:
    _add_item_errors(
        report,
        items,
        "Math renderer returned malformed output",
        "Check the MathJax renderer JSON contract for rendered, errors, and css.",
    )


def _add_renderer_contract_error(
    report: ValidationReport,
    item: MathItem,
    next_action: str,
) -> None:
    report.add_error(
        "Math renderer returned malformed output",
        path=item.source_path,
        field=f"math:{item.id}",
        next_action=next_action,
    )


def _add_item_errors(
    report: ValidationReport,
    items: list[MathItem],
    message: str,
    next_action: str,
) -> None:
    for item in items:
        report.add_error(
            message,
            path=item.source_path,
            field=f"math:{item.id}",
            next_action=next_action,
        )


def _process_next_action(process: subprocess.CompletedProcess[str]) -> str:
    details = []
    if process.returncode != 0:
        details.append(f"exit code {process.returncode}")
    if process.stderr.strip():
        details.append(f"stderr: {_truncate(process.stderr.strip())}")
    if process.stdout.strip():
        details.append(f"stdout: {_truncate(process.stdout.strip())}")
    if not details:
        details.append("no renderer details were reported")
    return "Check the Node MathJax renderer process: " + "; ".join(details)


def _timeout_next_action(
    command: list[str],
    error: subprocess.TimeoutExpired,
    timeout_seconds: float,
) -> str:
    details = [
        f"timeout after {timeout_seconds:g}s",
        f"command: {_truncate(' '.join(command))}",
    ]
    if error.stdout:
        details.append(f"stdout: {_truncate(_decode_timeout_output(error.stdout))}")
    if error.stderr:
        details.append(f"stderr: {_truncate(_decode_timeout_output(error.stderr))}")
    return "Check the MathJax renderer process: " + "; ".join(details)


def _invalid_json_next_action(
    process: subprocess.CompletedProcess[str],
    error: json.JSONDecodeError,
) -> str:
    details = [f"JSON parse failed at character {error.pos}: {error.msg}"]
    if process.stderr.strip():
        details.append(f"stderr: {_truncate(process.stderr.strip())}")
    if process.stdout.strip():
        details.append(f"stdout: {_truncate(process.stdout.strip())}")
    return "Check renderer stdout. " + "; ".join(details)


def _decode_timeout_output(value: str | bytes) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _tex_excerpt(tex: str) -> str:
    normalized = " ".join(tex.split())
    if len(normalized) <= 80:
        return normalized
    return normalized[:77] + "..."


def _truncate(value: str, limit: int = _DETAIL_LIMIT) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + "...[truncated]"
