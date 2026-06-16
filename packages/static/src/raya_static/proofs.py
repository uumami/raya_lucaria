from __future__ import annotations

import re
import shlex
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

STATIC_ENVIRONMENT_KINDS = ("proof", "solution", "hint", "answer")
_STATIC_ENVIRONMENT_KIND_PATTERN = "|".join(STATIC_ENVIRONMENT_KINDS)
PLACEHOLDER_PREFIX = "RAYA_STATIC_ENVIRONMENT_"
STATIC_ENVIRONMENT_OPEN_RE = re.compile(
    rf"^ {{0,3}}:::[ \t]+(?P<kind>{_STATIC_ENVIRONMENT_KIND_PATTERN})"
    r"(?:[ \t]+(?P<attrs>\S.*?))?[ \t]*$"
)
PROOF_OPEN_RE = re.compile(
    r"^ {0,3}:::[ \t]+proof(?:[ \t]+(?P<attrs>\S.*?))?[ \t]*$"
)


def is_static_environment_directive_open(line: str) -> bool:
    return STATIC_ENVIRONMENT_OPEN_RE.match(line) is not None


def is_proof_directive_open(line: str) -> bool:
    return PROOF_OPEN_RE.match(line) is not None


@dataclass(frozen=True)
class StaticEnvironmentSource:
    placeholder: str
    kind: str
    id: str | None
    of_id: str | None
    title: str | None
    body: str
    source_path: Path
    start_line: int


ProofSource = StaticEnvironmentSource


@dataclass(frozen=True)
class PreparedStaticEnvironmentMarkdown:
    body: str
    sources: list[StaticEnvironmentSource]


PreparedProofMarkdown = PreparedStaticEnvironmentMarkdown


@dataclass(frozen=True)
class StaticEnvironmentRenderItem:
    source: StaticEnvironmentSource
    target: NumberedObject | None


ProofRenderItem = StaticEnvironmentRenderItem


@dataclass(frozen=True)
class StaticEnvironmentRenderContext:
    items: list[StaticEnvironmentRenderItem]
    objects_by_id: dict[str, NumberedObject]


ProofRenderContext = StaticEnvironmentRenderContext


def prepare_static_environment_markdown(
    body: str,
    *,
    report: ValidationReport,
    source_path: Path,
) -> PreparedStaticEnvironmentMarkdown:
    _validate_no_reserved_placeholder_text(body, report=report, source_path=source_path)
    output_lines: list[str] = []
    sources: list[StaticEnvironmentSource] = []
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

        environment_opened = STATIC_ENVIRONMENT_OPEN_RE.match(line)
        if environment_opened is None:
            output_lines.append(line)
            index += 1
            continue

        start_line = index + 1
        kind = environment_opened.group("kind")
        attrs = _parse_attrs(
            environment_opened.group("attrs"),
            report,
            source_path,
            start_line,
            kind=kind,
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
                label = _kind_label(kind)
                report.add_error(
                    f"{label} directive contains nested directive",
                    path=source_path,
                    field=f"line:{index + 1}",
                    next_action=f"Close the {kind} before starting another directive block",
                )
            if DIRECTIVE_CLOSE_RE.match(current):
                closed = True
                index += 1
                break
            content_lines.append(current)
            index += 1

        if not closed:
            label = _kind_label(kind)
            report.add_error(
                f"{label} directive is missing a closing ::: line",
                path=source_path,
                field=f"line:{start_line}",
                next_action=f"Add a closing ::: line after the {kind} body",
            )

        placeholder = f"{PLACEHOLDER_PREFIX}{len(sources)}"
        output_lines.extend(["", placeholder, ""])
        sources.append(
            StaticEnvironmentSource(
                placeholder=placeholder,
                kind=kind,
                id=attrs.get("id"),
                of_id=attrs.get("of"),
                title=attrs.get("title"),
                body="\n".join(content_lines).strip("\n"),
                source_path=source_path,
                start_line=start_line,
            )
        )

    trailing_newline = "\n" if body.endswith("\n") else ""
    return PreparedStaticEnvironmentMarkdown(
        body="\n".join(output_lines) + trailing_newline,
        sources=sources,
    )


def prepare_proof_markdown(
    body: str,
    *,
    report: ValidationReport,
    source_path: Path,
) -> PreparedProofMarkdown:
    return prepare_static_environment_markdown(
        body,
        report=report,
        source_path=source_path,
    )


def _parse_attrs(
    raw: str | None,
    report: ValidationReport,
    source_path: Path,
    line_number: int,
    *,
    kind: str,
) -> dict[str, str]:
    if raw is None:
        return {}
    label = _kind_label(kind)
    stripped = raw.strip()
    if not stripped.startswith("{") or not stripped.endswith("}"):
        report.add_error(
            f"{label} directive attributes must use braces",
            path=source_path,
            field=f"line:{line_number}",
            next_action=f'Use attributes such as {{#{kind}-id of="theorem-id"}}',
        )
        return {}
    try:
        tokens = shlex.split(stripped[1:-1])
    except ValueError as error:
        report.add_error(
            f"Could not parse {kind} attributes: {error}",
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
                f"Unknown {kind} attribute '{token}'",
                path=source_path,
                field=f"line:{line_number}",
                next_action='Use #id, of="object-id", or title="Optional title"',
            )
            continue
        key, value = token.split("=", 1)
        if key not in {"of", "title"}:
            report.add_error(
                f"Unknown {kind} attribute '{key}'",
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
            noun = f"{kind} ID" if attr_name == "id" else f"{kind} target ID"
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


def _kind_label(kind: str) -> str:
    return kind.capitalize()


def _validate_no_reserved_placeholder_text(
    body: str,
    *,
    report: ValidationReport,
    source_path: Path,
) -> None:
    for line_number, line in enumerate(body.splitlines(), start=1):
        if PLACEHOLDER_PREFIX in line:
            report.add_error(
                "Reserved static environment placeholder text",
                path=source_path,
                field=f"line:{line_number}",
                next_action=f"Remove text that starts with {PLACEHOLDER_PREFIX}",
            )
