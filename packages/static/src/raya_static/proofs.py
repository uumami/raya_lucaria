from __future__ import annotations

import shlex
import re
from dataclasses import dataclass
from pathlib import Path

from raya_schema import ValidationReport
from raya_schema.numbered_objects import NumberedObject
from raya_static.numbered_objects import (
    DIRECTIVE_CLOSE_RE,
    DIRECTIVE_OPEN_RE,
    OBJECT_ID_RE,
    _FenceState,
    _fence_opener,
    _is_closing_fence,
)

PLACEHOLDER_PREFIX = "RAYA_PROOF_"
PROOF_OPEN_RE = re.compile(r"^ {0,3}:::\s+proof(?:\s+(?P<attrs>.*))?\s*$")


def is_proof_directive_open(line: str) -> bool:
    return PROOF_OPEN_RE.match(line) is not None


@dataclass(frozen=True)
class ProofSource:
    placeholder: str
    id: str | None
    of_id: str | None
    title: str | None
    body: str
    source_path: Path
    start_line: int


@dataclass(frozen=True)
class PreparedProofMarkdown:
    body: str
    sources: list[ProofSource]


@dataclass(frozen=True)
class ProofRenderItem:
    source: ProofSource
    target: NumberedObject | None


@dataclass(frozen=True)
class ProofRenderContext:
    items: list[ProofRenderItem]
    objects_by_id: dict[str, NumberedObject]


def prepare_proof_markdown(
    body: str,
    *,
    report: ValidationReport,
    source_path: Path,
) -> PreparedProofMarkdown:
    _validate_no_reserved_placeholder_text(body, report=report, source_path=source_path)
    output_lines: list[str] = []
    sources: list[ProofSource] = []
    lines = body.splitlines()
    index = 0
    fence_state: _FenceState | None = None

    while index < len(lines):
        line = lines[index]
        if fence_state is not None:
            output_lines.append(line)
            if _is_closing_fence(line, fence_state):
                fence_state = None
            index += 1
            continue

        opener = _fence_opener(line)
        if opener is not None:
            fence_state = opener
            output_lines.append(line)
            index += 1
            continue

        proof_opened = PROOF_OPEN_RE.match(line)
        if proof_opened is None:
            output_lines.append(line)
            index += 1
            continue

        start_line = index + 1
        attrs = _parse_attrs(
            proof_opened.group("attrs"),
            report,
            source_path,
            start_line,
        )
        content_lines: list[str] = []
        index += 1
        closed = False

        content_fence_state: _FenceState | None = None
        while index < len(lines):
            current = lines[index]
            if content_fence_state is not None:
                content_lines.append(current)
                if _is_closing_fence(current, content_fence_state):
                    content_fence_state = None
                index += 1
                continue

            content_opener = _fence_opener(current)
            if content_opener is not None:
                content_fence_state = content_opener
                content_lines.append(current)
                index += 1
                continue

            if DIRECTIVE_OPEN_RE.match(current):
                report.add_error(
                    "Proof directive contains nested directive",
                    path=source_path,
                    field=f"line:{index + 1}",
                    next_action="Close the proof before starting another directive block",
                )
            if DIRECTIVE_CLOSE_RE.match(current):
                closed = True
                index += 1
                break
            content_lines.append(current)
            index += 1

        if not closed:
            report.add_error(
                "Proof directive is missing a closing ::: line",
                path=source_path,
                field=f"line:{start_line}",
                next_action="Add a closing ::: line after the proof body",
            )

        placeholder = f"{PLACEHOLDER_PREFIX}{len(sources)}"
        output_lines.extend(["", placeholder, ""])
        sources.append(
            ProofSource(
                placeholder=placeholder,
                id=attrs.get("id"),
                of_id=attrs.get("of"),
                title=attrs.get("title"),
                body="\n".join(content_lines).strip("\n"),
                source_path=source_path,
                start_line=start_line,
            )
        )

    trailing_newline = "\n" if body.endswith("\n") else ""
    return PreparedProofMarkdown(
        body="\n".join(output_lines) + trailing_newline,
        sources=sources,
    )


def _parse_attrs(
    raw: str | None,
    report: ValidationReport,
    source_path: Path,
    line_number: int,
) -> dict[str, str]:
    if raw is None:
        return {}
    stripped = raw.strip()
    if not stripped.startswith("{") or not stripped.endswith("}"):
        report.add_error(
            "Proof directive attributes must use braces",
            path=source_path,
            field=f"line:{line_number}",
            next_action='Use attributes such as {#proof-id of="theorem-id"}',
        )
        return {}
    try:
        tokens = shlex.split(stripped[1:-1])
    except ValueError as error:
        report.add_error(
            f"Could not parse proof attributes: {error}",
            path=source_path,
            field=f"line:{line_number}",
            next_action='Use shell-style quoted attributes, for example of="main-theorem"',
        )
        return {}

    attrs: dict[str, str] = {}
    for token in tokens:
        if token.startswith("#"):
            attrs["id"] = token[1:]
            continue
        if "=" not in token:
            report.add_error(
                f"Unknown proof attribute '{token}'",
                path=source_path,
                field=f"line:{line_number}",
                next_action='Use #id, of="object-id", or title="Optional title"',
            )
            continue
        key, value = token.split("=", 1)
        if key not in {"of", "title"}:
            report.add_error(
                f"Unknown proof attribute '{key}'",
                path=source_path,
                field=f"line:{line_number}",
                next_action='Use #id, of="object-id", or title="Optional title"',
            )
            continue
        attrs[key] = value

    for attr_name in ("id", "of"):
        if attr_name not in attrs:
            continue
        value = attrs[attr_name]
        if OBJECT_ID_RE.fullmatch(value) is None:
            noun = "proof ID" if attr_name == "id" else "proof target ID"
            report.add_error(
                f"Invalid {noun} '{value}'",
                path=source_path,
                field=f"line:{line_number}",
                next_action=(
                    "Use an ID that starts with a letter and contains only letters, "
                    "digits, underscores, or hyphens"
                ),
            )
    return attrs


def _validate_no_reserved_placeholder_text(
    body: str,
    *,
    report: ValidationReport,
    source_path: Path,
) -> None:
    for line_number, line in enumerate(body.splitlines(), start=1):
        if PLACEHOLDER_PREFIX in line:
            report.add_error(
                "Reserved proof placeholder text",
                path=source_path,
                field=f"line:{line_number}",
                next_action=f"Remove text that starts with {PLACEHOLDER_PREFIX}",
            )
