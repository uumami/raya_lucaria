from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from raya_schema import ValidationReport


ROOT = Path(__file__).resolve().parents[4]
RENDER_SCRIPT = ROOT / "packages" / "static" / "scripts" / "render_math.mjs"


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
    def __init__(self, node: str = "node", script: Path = RENDER_SCRIPT) -> None:
        self.node = node
        self.script = script

    def render_many(
        self,
        items: list[MathItem],
        *,
        report: ValidationReport,
    ) -> MathRenderResult:
        if not items:
            return MathRenderResult(html_by_id={}, css="")

        payload = {
            "items": [
                {"id": item.id, "tex": item.tex, "display": item.display}
                for item in items
            ]
        }

        try:
            process = subprocess.run(
                [self.node, str(self.script)],
                input=json.dumps(payload),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        except OSError as error:
            _add_item_errors(
                report,
                items,
                "Math renderer process failed",
                f"Check that Node and the MathJax renderer script are available: {error}",
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
                f"Check renderer stdout. JSON parse failed at character {error.pos}: {error.msg}.",
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

    raw_rendered = output.get("rendered")
    raw_errors = output.get("errors")
    css = output.get("css")
    if not isinstance(raw_rendered, list) or not isinstance(raw_errors, list):
        _add_malformed_output_errors(report, items)
        return None
    if not isinstance(css, str):
        _add_malformed_output_errors(report, items)
        return None

    html_by_id: dict[str, str] = {}
    requested_ids = {item.id for item in items}
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
        errors.append({"id": item_id, "message": message})

    return html_by_id, errors, css


def _add_renderer_errors(
    report: ValidationReport,
    items: list[MathItem],
    errors: list[dict[str, str]],
) -> None:
    by_id = {item.id: item for item in items}
    unknown_errors: list[str] = []
    for error in errors:
        item = by_id.get(error["id"])
        if item is None:
            unknown_errors.append(error["message"])
            continue
        report.add_error(
            "Math rendering failed",
            path=item.source_path,
            field=f"math:{item.id}",
            next_action=(
                f"Fix the TeX for {item.id} near `{_tex_excerpt(item.tex)}`: "
                f"{error['message']}"
            ),
        )

    if unknown_errors:
        _add_item_errors(
            report,
            items,
            "Math rendering failed",
            "Fix renderer input or TeX. Renderer reported: "
            + "; ".join(unknown_errors),
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
        details.append(f"stderr: {process.stderr.strip()}")
    if process.stdout.strip():
        details.append(f"stdout: {process.stdout.strip()}")
    if not details:
        details.append("no renderer details were reported")
    return "Check the Node MathJax renderer process: " + "; ".join(details)


def _tex_excerpt(tex: str) -> str:
    normalized = " ".join(tex.split())
    if len(normalized) <= 80:
        return normalized
    return normalized[:77] + "..."
