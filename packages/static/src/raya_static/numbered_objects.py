from __future__ import annotations

import html
import re
import shlex
from dataclasses import dataclass
from pathlib import Path

from raya_schema import ValidationReport
from raya_schema.numbered_objects import NumberedObject, NumberedObjectConfig

DIRECTIVE_OPEN_RE = re.compile(
    r"^ {0,3}:::\s+(?P<family>[A-Za-z][A-Za-z0-9_-]*)(?:\s+(?P<attrs>\{.*\}))?\s*$"
)
DIRECTIVE_CLOSE_RE = re.compile(r"^ {0,3}:::\s*$")
REFERENCE_RE = re.compile(
    r"(?<![\\A-Za-z0-9._%+-])@(?P<object_id>[A-Za-z][A-Za-z0-9_-]*)"
)
PLACEHOLDER_PREFIX = "RAYA_NUMBERED_OBJECT_"


@dataclass(frozen=True)
class NumberedObjectSource:
    placeholder: str
    id: str
    family: str
    title: str | None
    body: str
    source_path: Path
    start_line: int


@dataclass(frozen=True)
class PreparedNumberedMarkdown:
    body: str
    sources: list[NumberedObjectSource]


def _parse_attrs(
    raw: str | None,
    report: ValidationReport,
    source_path: Path,
    line_number: int,
) -> dict[str, str]:
    if raw is None:
        report.add_error(
            "Numbered object directive is missing attributes",
            path=source_path,
            field=f"line:{line_number}",
            next_action="Use attributes such as {#object-id title=\"Optional title\"}",
        )
        return {}

    stripped = raw.strip()
    if not stripped.startswith("{") or not stripped.endswith("}"):
        report.add_error(
            "Numbered object directive attributes must use braces",
            path=source_path,
            field=f"line:{line_number}",
            next_action="Use attributes such as {#object-id title=\"Optional title\"}",
        )
        return {}

    try:
        tokens = shlex.split(stripped[1:-1])
    except ValueError as error:
        report.add_error(
            f"Could not parse numbered object attributes: {error}",
            path=source_path,
            field=f"line:{line_number}",
            next_action="Use shell-style quoted attributes, for example title=\"Pythagorean theorem\"",
        )
        return {}

    attrs: dict[str, str] = {}
    for token in tokens:
        if token.startswith("#"):
            attrs["id"] = token[1:]
            continue
        if "=" not in token:
            report.add_error(
                f"Unknown numbered object attribute '{token}'",
                path=source_path,
                field=f"line:{line_number}",
                next_action="Use #id and key=value attributes",
            )
            continue
        key, value = token.split("=", 1)
        attrs[key] = value

    if not attrs.get("id"):
        report.add_error(
            "Numbered object directive is missing an id",
            path=source_path,
            field=f"line:{line_number}",
            next_action="Add an id attribute such as {#pythagorean}",
        )
    return attrs


def prepare_numbered_object_markdown(
    body: str,
    *,
    report: ValidationReport,
    source_path: Path,
) -> PreparedNumberedMarkdown:
    output_lines: list[str] = []
    sources: list[NumberedObjectSource] = []
    lines = body.splitlines()
    index = 0

    while index < len(lines):
        line = lines[index]
        opened = DIRECTIVE_OPEN_RE.match(line)
        if opened is None:
            output_lines.append(line)
            index += 1
            continue

        start_line = index + 1
        family = opened.group("family")
        attrs = _parse_attrs(opened.group("attrs"), report, source_path, start_line)
        content_lines: list[str] = []
        index += 1
        closed = False

        while index < len(lines):
            current = lines[index]
            if DIRECTIVE_OPEN_RE.match(current):
                report.add_error(
                    "Numbered object directive contains nested numbered object",
                    path=source_path,
                    field=f"line:{index + 1}",
                    next_action="Close the outer numbered object before starting another one",
                )
            if DIRECTIVE_CLOSE_RE.match(current):
                closed = True
                index += 1
                break
            content_lines.append(current)
            index += 1

        if not closed:
            report.add_error(
                "Numbered object directive is missing a closing ::: line",
                path=source_path,
                field=f"line:{start_line}",
                next_action="Add a closing ::: line after the numbered object body",
            )

        placeholder = f"{PLACEHOLDER_PREFIX}{len(sources)}"
        output_lines.append(placeholder)
        sources.append(
            NumberedObjectSource(
                placeholder=placeholder,
                id=attrs.get("id", ""),
                family=family,
                title=attrs.get("title"),
                body="\n".join(content_lines).strip("\n"),
                source_path=source_path,
                start_line=start_line,
            )
        )

    trailing_newline = "\n" if body.endswith("\n") else ""
    return PreparedNumberedMarkdown(
        body="\n".join(output_lines) + trailing_newline,
        sources=sources,
    )


def collect_numbered_object_sources(
    body: str,
    *,
    report: ValidationReport,
    source_path: Path,
) -> list[NumberedObjectSource]:
    return prepare_numbered_object_markdown(
        body,
        report=report,
        source_path=source_path,
    ).sources


def compute_numbered_objects_for_page(
    sources: list[NumberedObjectSource],
    *,
    config: NumberedObjectConfig,
    course_relative_source_path: str,
    page_id: str,
    page_title: str,
    page_output_path: str,
    page_number_prefix: str,
) -> list[NumberedObject]:
    counts_by_sequence: dict[str, int] = {}
    objects: list[NumberedObject] = []
    href_base = _href_base_for_page(page_output_path)

    for source in sources:
        family_config = config.families[source.family]
        sequence_id = family_config.sequence
        sequence_config = config.sequences[sequence_id]
        counts_by_sequence[sequence_id] = counts_by_sequence.get(sequence_id, 0) + 1
        sequence_number = counts_by_sequence[sequence_id]
        number = (
            f"{page_number_prefix}.{sequence_number}"
            if page_number_prefix
            else str(sequence_number)
        )
        objects.append(
            NumberedObject(
                id=source.id,
                family=source.family,
                sequence=sequence_id,
                label=family_config.label,
                number=number,
                title=source.title,
                source_path=course_relative_source_path,
                page_id=page_id,
                page_title=page_title,
                page_output_path=page_output_path,
                href=f"{href_base}#raya-object-{source.id}",
                style=sequence_config.style,
            )
        )

    return objects


def render_reference_link(object_id: str, reference_text: str, href: str) -> str:
    escaped_id = html.escape(object_id, quote=True)
    escaped_href = html.escape(href, quote=True)
    escaped_text = html.escape(reference_text)
    return (
        f'<a class="raya-object-ref" data-object-id="{escaped_id}" '
        f'href="{escaped_href}">{escaped_text}</a>'
    )


def _href_base_for_page(page_output_path: str) -> str:
    path = page_output_path.replace("\\", "/")
    if path.endswith("/index.html"):
        return path[: -len("index.html")]
    return f"{path}"
