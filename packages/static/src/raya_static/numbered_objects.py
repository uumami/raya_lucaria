from __future__ import annotations

import html
import re
import shlex
from dataclasses import dataclass
from pathlib import Path

from raya_schema import ValidationReport
from raya_schema.content import parse_ordered_name
from raya_schema.numbered_objects import NumberedObject, NumberedObjectConfig

DIRECTIVE_OPEN_RE = re.compile(
    r"^ {0,3}:::\s+(?P<family>[A-Za-z][A-Za-z0-9_-]*)(?:\s+(?P<attrs>\{.*\}))?\s*$"
)
DIRECTIVE_CLOSE_RE = re.compile(r"^ {0,3}:::\s*$")
REFERENCE_RE = re.compile(
    r"(?<![\\A-Za-z0-9._%+-])@(?P<object_id>[A-Za-z][A-Za-z0-9_-]*)"
)
OBJECT_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
FENCE_OPEN_RE = re.compile(
    r"^(?P<prefix>(?: {0,3}(?:[-+*]|\d+[.)])\s+)? {0,3})"
    r"(?P<marker>`{3,}|~{3,})(?P<info>.*)$"
)
FENCE_CLOSE_RE = re.compile(r"^(?P<indent> *)(?P<marker>`{3,}|~{3,})[ \t]*$")
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


@dataclass(frozen=True)
class NumberedObjectRenderItem:
    source: NumberedObjectSource
    object: NumberedObject


@dataclass(frozen=True)
class NumberedObjectRenderContext:
    items: list[NumberedObjectRenderItem]
    objects_by_id: dict[str, NumberedObject]


@dataclass(frozen=True)
class _FenceState:
    marker: str
    close_indent_max: int


@dataclass(frozen=True)
class _LinkDestinationParse:
    has_inline_title: bool


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
    elif OBJECT_ID_RE.fullmatch(attrs["id"]) is None:
        report.add_error(
            f"Invalid numbered object ID '{attrs['id']}'",
            path=source_path,
            field=f"line:{line_number}",
            next_action=(
                "Use an ID that starts with a letter and contains only letters, "
                "digits, underscores, or hyphens, such as {#pythagorean}"
            ),
        )
    return attrs


def prepare_numbered_object_markdown(
    body: str,
    *,
    report: ValidationReport,
    source_path: Path,
) -> PreparedNumberedMarkdown:
    _validate_no_reserved_placeholder_text(
        body,
        report=report,
        source_path=source_path,
    )
    output_lines: list[str] = []
    sources: list[NumberedObjectSource] = []
    lines = body.splitlines()
    index = 0
    fence_state: _FenceState | None = None
    from raya_static.proofs import is_proof_directive_open

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

        if is_proof_directive_open(line):
            output_lines.append(line)
            index += 1
            proof_fence_state: _FenceState | None = None
            while index < len(lines):
                current = lines[index]
                output_lines.append(current)
                index += 1
                if proof_fence_state is not None:
                    if _is_closing_fence(current, proof_fence_state):
                        proof_fence_state = None
                    continue
                proof_fence_opener = _fence_opener(current)
                if proof_fence_opener is not None:
                    proof_fence_state = proof_fence_opener
                    continue
                if DIRECTIVE_CLOSE_RE.match(current):
                    break
            continue

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
        output_lines.extend(["", placeholder, ""])
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


def expand_shorthand_references(
    body: str,
    *,
    context: NumberedObjectRenderContext,
    report: ValidationReport,
    source_path: Path,
) -> str:
    lines = body.splitlines(keepends=True)
    reference_definition_labels = _collect_reference_definition_labels(lines)
    expanded_lines: list[str] = []
    fence_state: _FenceState | None = None
    in_display_math = False
    reference_title_continuation_allowed = False

    for line in lines:
        if fence_state is not None:
            expanded_lines.append(line)
            if _is_closing_fence(line, fence_state):
                fence_state = None
            continue
        opener = _fence_opener(line)
        if opener is not None:
            fence_state = opener
            expanded_lines.append(line)
            continue
        if _is_display_math_delimiter(line):
            in_display_math = not in_display_math
            expanded_lines.append(line)
            continue
        if reference_title_continuation_allowed:
            if _is_reference_definition_title_continuation_line(line):
                expanded_lines.append(line)
                reference_title_continuation_allowed = False
                continue
            reference_title_continuation_allowed = False
        if _is_reference_definition_line(line):
            reference_title_continuation_allowed = (
                _reference_definition_allows_title_continuation(line)
            )
            expanded_lines.append(line)
            continue
        if (
            in_display_math
            or _is_indented_code_line(line)
        ):
            expanded_lines.append(line)
            continue
        expanded_lines.append(
            _expand_shorthand_references_in_line(
                line,
                context=context,
                report=report,
                source_path=source_path,
                reference_definition_labels=reference_definition_labels,
            )
        )

    return "".join(expanded_lines)


def _expand_shorthand_references_in_line(
    line: str,
    *,
    context: NumberedObjectRenderContext,
    report: ValidationReport,
    source_path: Path,
    reference_definition_labels: set[str],
) -> str:
    protected_ranges = (
        _code_span_ranges(line)
        + _math_span_ranges(line)
        + _markdown_link_or_image_ranges(
            line,
            reference_definition_labels=reference_definition_labels,
        )
    )
    pieces: list[str] = []
    cursor = 0
    for match in REFERENCE_RE.finditer(line):
        if _position_in_ranges(match.start(), protected_ranges) or _looks_urlish(
            line,
            match.start(),
        ):
            continue
        object_id = match.group("object_id")
        obj = context.objects_by_id.get(object_id)
        if obj is None:
            report.add_error(
                f"Unknown numbered object reference '@{object_id}'",
                path=source_path,
                field=f"ref:{object_id}",
                next_action="Use a numbered object ID defined in this course",
            )
            continue
        pieces.append(line[cursor : match.start()])
        pieces.append(
            f"[{_escape_markdown_link_label(obj.reference_text)}](raya:ref/{object_id})"
        )
        cursor = match.end()
    if not pieces:
        return line
    pieces.append(line[cursor:])
    return "".join(pieces)


def _escape_markdown_link_label(label: str) -> str:
    return (
        label.replace("\\", "\\\\")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )


def _fence_opener(line: str) -> _FenceState | None:
    match = FENCE_OPEN_RE.match(_line_without_blockquote_prefix(line))
    if match is None:
        return None
    marker = match.group("marker")
    info = match.group("info")
    if marker.startswith("`") and "`" in info:
        return None
    return _FenceState(
        marker=marker,
        close_indent_max=len(match.group("prefix")) + 3,
    )


def _is_closing_fence(line: str, fence_state: _FenceState) -> bool:
    match = FENCE_CLOSE_RE.match(_line_without_blockquote_prefix(line))
    if match is None:
        return False
    if len(match.group("indent")) > fence_state.close_indent_max:
        return False
    return _matches_closing_fence(match.group("marker"), fence_state.marker)


def _matches_closing_fence(marker: str, opening_marker: str) -> bool:
    return marker[0] == opening_marker[0] and len(marker) >= len(opening_marker)


def _validate_no_reserved_placeholder_text(
    body: str,
    *,
    report: ValidationReport,
    source_path: Path,
) -> None:
    for line_number, line in enumerate(body.splitlines(), start=1):
        if PLACEHOLDER_PREFIX not in line:
            continue
        report.add_error(
            "Reserved numbered object placeholder text",
            path=source_path,
            field=f"line:{line_number}",
            next_action=(
                f"Remove or reword text containing '{PLACEHOLDER_PREFIX}'; "
                "that prefix is reserved for generated numbered object placeholders."
            ),
        )


def _is_display_math_delimiter(line: str) -> bool:
    return _line_without_list_marker_prefix(_line_without_blockquote_prefix(line)).strip() == "$$"


def _is_indented_code_line(line: str) -> bool:
    unquoted = _line_without_blockquote_prefix(line)
    return unquoted.startswith("    ") or unquoted.startswith("\t")


def _is_reference_definition_line(line: str) -> bool:
    return _reference_definition_label(line) is not None


def _reference_definition_allows_title_continuation(line: str) -> bool:
    stripped = _line_without_blockquote_prefix(line).lstrip()
    label_end = _find_link_label_end(stripped, 0)
    if label_end == -1:
        return False
    parsed = _parse_link_destination_and_title(stripped[label_end + 2 :])
    if parsed is None:
        return False
    return not parsed.has_inline_title


def _is_reference_definition_title_continuation_line(line: str) -> bool:
    stripped = _line_without_blockquote_prefix(line)
    return _starts_reference_title(stripped.lstrip())


def _starts_reference_title(value: str) -> bool:
    return value.startswith(('"', "'", "("))


def _line_without_blockquote_prefix(line: str) -> str:
    value = line
    while True:
        match = re.match(r"^ {0,3}>\s?", value)
        if match is None:
            return value
        value = value[match.end() :]


def _line_without_list_marker_prefix(line: str) -> str:
    match = re.match(r"^(?: {0,3}(?:[-+*]|\d+[.)])\s+)?(.*)$", line)
    if match is None:
        return line
    return match.group(1)


def _code_span_ranges(line: str) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    cursor = 0
    while cursor < len(line):
        start = line.find("`", cursor)
        if start == -1:
            break
        tick_count = 1
        while start + tick_count < len(line) and line[start + tick_count] == "`":
            tick_count += 1
        marker = "`" * tick_count
        end = line.find(marker, start + tick_count)
        if end == -1:
            break
        ranges.append((start, end + tick_count))
        cursor = end + tick_count
    return ranges


def _math_span_ranges(line: str) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    cursor = 0
    while cursor < len(line):
        start = _find_unescaped_single_dollar(line, cursor)
        if start == -1:
            break
        end = _find_unescaped_single_dollar(line, start + 1)
        if end == -1:
            break
        ranges.append((start, end + 1))
        cursor = end + 1
    return ranges


def _markdown_link_or_image_ranges(
    line: str,
    *,
    reference_definition_labels: set[str],
) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    cursor = 0
    while cursor < len(line):
        label_start = line.find("[", cursor)
        if label_start == -1:
            break
        start = (
            label_start - 1
            if label_start > 0 and line[label_start - 1] == "!"
            else label_start
        )
        label_end = _find_link_label_end(line, label_start)
        if label_end == -1:
            cursor = label_start + 1
            continue
        if label_end + 1 >= len(line):
            if _normalize_reference_label(
                line[label_start + 1 : label_end]
            ) in reference_definition_labels:
                ranges.append((start, label_end + 1))
            cursor = label_end + 1
            continue
        next_char = line[label_end + 1]
        if next_char == "[":
            reference_end = _find_link_label_end(line, label_end + 1)
            if reference_end == -1:
                cursor = label_end + 2
                continue
            ranges.append((start, reference_end + 1))
            cursor = reference_end + 1
            continue
        if next_char != "(":
            if _normalize_reference_label(
                line[label_start + 1 : label_end]
            ) in reference_definition_labels:
                ranges.append((start, label_end + 1))
            cursor = label_end + 1
            continue
        inline_link_end = _find_inline_link_end(line, label_end + 1)
        if inline_link_end == -1:
            cursor = label_end + 2
            continue
        ranges.append((start, inline_link_end + 1))
        cursor = inline_link_end + 1
    return ranges


def _collect_reference_definition_labels(lines: list[str]) -> set[str]:
    labels: set[str] = set()
    fence_state: _FenceState | None = None
    in_display_math = False
    for line in lines:
        if fence_state is not None:
            if _is_closing_fence(line, fence_state):
                fence_state = None
            continue
        opener = _fence_opener(line)
        if opener is not None:
            fence_state = opener
            continue
        if _is_display_math_delimiter(line):
            in_display_math = not in_display_math
            continue
        if in_display_math or _is_indented_code_line(line):
            continue
        label = _reference_definition_label(line)
        if label is not None:
            labels.add(_normalize_reference_label(label))
    return labels


def _reference_definition_label(line: str) -> str | None:
    stripped = _line_without_blockquote_prefix(line).lstrip()
    if not stripped.startswith("[") or stripped.startswith("[^"):
        return None
    label_end = _find_link_label_end(stripped, 0)
    if label_end == -1:
        return None
    if label_end + 1 >= len(stripped) or stripped[label_end + 1] != ":":
        return None
    if _parse_link_destination_and_title(stripped[label_end + 2 :]) is None:
        return None
    return stripped[1:label_end]


def _normalize_reference_label(label: str) -> str:
    return re.sub(r"\s+", " ", label.strip()).casefold()


def _find_inline_link_end(line: str, open_paren: int) -> int:
    cursor = open_paren + 1
    while cursor < len(line):
        if line[cursor] == ")" and not _is_escaped(line, cursor):
            if _parse_link_destination_and_title(
                line[open_paren + 1 : cursor],
                allow_empty=True,
            ):
                return cursor
        cursor += 1
    return -1


def _parse_link_destination_and_title(
    raw: str,
    *,
    allow_empty: bool = False,
) -> _LinkDestinationParse | None:
    value = raw.strip()
    if not value:
        if allow_empty:
            return _LinkDestinationParse(has_inline_title=False)
        return None
    if value.startswith("<"):
        destination_end = _find_closing_angle_destination(value)
        if destination_end == -1:
            return None
    else:
        destination_end = _find_bare_destination_end(value)
        if destination_end == -1:
            return None
    remainder = value[destination_end:].strip()
    if not remainder:
        return _LinkDestinationParse(has_inline_title=False)
    if _parse_link_title(remainder):
        return _LinkDestinationParse(has_inline_title=True)
    return None


def _find_closing_angle_destination(value: str) -> int:
    cursor = 1
    while cursor < len(value):
        char = value[cursor]
        if char == ">" and not _is_escaped(value, cursor):
            return cursor + 1
        if char in {"\n", "\r"}:
            return -1
        cursor += 1
    return -1


def _find_bare_destination_end(value: str) -> int:
    cursor = 0
    paren_depth = 0
    while cursor < len(value):
        char = value[cursor]
        if _is_escaped(value, cursor):
            cursor += 1
            continue
        if char.isspace():
            break
        if char == "<":
            return -1
        if char == "(":
            paren_depth += 1
        elif char == ")":
            if paren_depth == 0:
                break
            paren_depth -= 1
        cursor += 1
    if cursor == 0 or paren_depth != 0:
        return -1
    return cursor


def _parse_link_title(value: str) -> bool:
    if value.startswith('"') or value.startswith("'"):
        delimiter = value[0]
        close = _find_unescaped_delimiter(value, delimiter, 1)
        return close != -1 and not value[close + 1 :].strip()
    if value.startswith("("):
        close = _find_unescaped_delimiter(value, ")", 1)
        return close != -1 and not value[close + 1 :].strip()
    return False


def _find_unescaped_delimiter(value: str, delimiter: str, start: int) -> int:
    cursor = start
    while cursor < len(value):
        if value[cursor] == delimiter and not _is_escaped(value, cursor):
            return cursor
        cursor += 1
    return -1


def _find_link_label_end(line: str, label_start: int) -> int:
    depth = 0
    cursor = label_start
    while cursor < len(line):
        char = line[cursor]
        if _is_escaped(line, cursor):
            cursor += 1
            continue
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return cursor
        cursor += 1
    return -1


def _find_unescaped_single_dollar(line: str, start: int) -> int:
    cursor = start
    while cursor < len(line):
        position = line.find("$", cursor)
        if position == -1:
            return -1
        if _is_escaped(line, position) or _is_double_dollar(line, position):
            cursor = position + 1
            continue
        return position
    return -1


def _is_escaped(line: str, position: int) -> bool:
    backslashes = 0
    cursor = position - 1
    while cursor >= 0 and line[cursor] == "\\":
        backslashes += 1
        cursor -= 1
    return backslashes % 2 == 1


def _is_double_dollar(line: str, position: int) -> bool:
    return (
        (position > 0 and line[position - 1] == "$")
        or (position + 1 < len(line) and line[position + 1] == "$")
    )


def _position_in_ranges(position: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= position < end for start, end in ranges)


def _looks_urlish(line: str, position: int) -> bool:
    prefix = line[:position]
    token_start = max(prefix.rfind(" "), prefix.rfind("\t")) + 1
    token = prefix[token_start:]
    return "://" in token or token.endswith("/")


def page_number_prefix_from_source_path(source_path: str) -> str:
    path = Path(source_path)
    labels: list[str] = []
    for part in path.parts[:-1]:
        ordered = parse_ordered_name(part)
        if ordered is not None:
            labels.append(ordered.label)

    ordered_file = parse_ordered_name(path.stem)
    if (
        ordered_file is not None
        and (ordered_file.order != 0 or ordered_file.slug != "index")
    ):
        labels.append(ordered_file.label)
    return ".".join(labels)


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
