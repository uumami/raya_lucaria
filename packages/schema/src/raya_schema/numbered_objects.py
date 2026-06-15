from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from raya_schema.diagnostics import ValidationReport
from raya_schema.yaml_io import load_yaml_file

NUMBERED_OBJECT_INDEX_PATH = "data/numbered-objects.json"
NUMBERED_OBJECT_INDEX_VERSION = 1

BUILT_IN_NUMBERED_OBJECT_SEQUENCES: dict[str, dict[str, str]] = {
    "theorem": {"label": "Theorem", "style": "margin"},
    "example": {"label": "Example", "style": "margin"},
    "exercise": {"label": "Exercise", "style": "banded"},
    "assignment": {"label": "Assignment", "style": "banded"},
    "figure": {"label": "Figure", "style": "caption"},
    "table": {"label": "Table", "style": "caption"},
    "equation": {"label": "Equation", "style": "equation"},
}

BUILT_IN_NUMBERED_OBJECT_FAMILIES: dict[str, dict[str, str]] = {
    "theorem": {"sequence": "theorem", "label": "Theorem"},
    "lemma": {"sequence": "theorem", "label": "Lemma"},
    "proposition": {"sequence": "theorem", "label": "Proposition"},
    "corollary": {"sequence": "theorem", "label": "Corollary"},
    "definition": {"sequence": "theorem", "label": "Definition"},
    "example": {"sequence": "example", "label": "Example"},
    "exercise": {"sequence": "exercise", "label": "Exercise"},
    "problem": {"sequence": "exercise", "label": "Problem"},
    "homework": {"sequence": "assignment", "label": "Homework"},
    "assignment": {"sequence": "assignment", "label": "Assignment"},
    "project": {"sequence": "assignment", "label": "Project"},
    "exam": {"sequence": "assignment", "label": "Exam"},
    "task": {"sequence": "assignment", "label": "Task"},
    "figure": {"sequence": "figure", "label": "Figure"},
    "table": {"sequence": "table", "label": "Table"},
    "equation": {"sequence": "equation", "label": "Equation"},
}

NUMBERED_OBJECT_STYLES = {"margin", "banded", "caption", "equation"}
NUMBERING_MODES = {"page-hierarchy"}


@dataclass(frozen=True)
class NumberedObjectSequence:
    label: str
    style: str


@dataclass(frozen=True)
class NumberedObjectFamily:
    sequence: str
    label: str


@dataclass(frozen=True)
class NumberedObjectConfig:
    numbering: str
    sequences: dict[str, NumberedObjectSequence]
    families: dict[str, NumberedObjectFamily]


@dataclass(frozen=True)
class NumberedObject:
    id: str
    family: str
    sequence: str
    label: str
    number: str
    title: str | None
    source_path: str
    page_id: str
    page_title: str
    page_output_path: str
    href: str
    style: str

    @property
    def reference_text(self) -> str:
        return f"{self.label} {self.number}".strip()

    @property
    def anchor(self) -> str:
        return f"raya-object-{self.id}"

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "family": self.family,
            "sequence": self.sequence,
            "label": self.label,
            "number": self.number,
            "reference_text": self.reference_text,
            "anchor": self.anchor,
            "title": self.title,
            "source_path": self.source_path,
            "page_id": self.page_id,
            "page_title": self.page_title,
            "page_output_path": self.page_output_path,
            "href": self.href,
            "style": self.style,
        }

    def to_index_entry(self) -> dict[str, Any]:
        return self.to_json()


def normalize_numbered_object_config(
    course_config: dict[str, Any],
    report: ValidationReport,
    context: str,
) -> NumberedObjectConfig:
    sequences = {
        key: NumberedObjectSequence(
            label=value["label"],
            style=value["style"],
        )
        for key, value in BUILT_IN_NUMBERED_OBJECT_SEQUENCES.items()
    }
    families = {
        key: NumberedObjectFamily(
            sequence=value["sequence"],
            label=value["label"],
        )
        for key, value in BUILT_IN_NUMBERED_OBJECT_FAMILIES.items()
    }
    numbering = "page-hierarchy"

    raw_config = _numbered_objects_config(course_config, report=report, context=context)
    if raw_config is None:
        return NumberedObjectConfig(
            numbering=numbering,
            sequences=sequences,
            families=families,
        )

    raw_numbering = raw_config.get("numbering")
    if raw_numbering is not None:
        if raw_numbering in NUMBERING_MODES:
            numbering = raw_numbering
        else:
            report.add_error(
                f"Unknown numbered object numbering mode '{raw_numbering}' in {context}",
                field="render.numbered_objects.numbering",
                next_action="Use page-hierarchy numbering",
            )

    raw_sequences = raw_config.get("sequences", {})
    if raw_sequences is None:
        raw_sequences = {}
    if not isinstance(raw_sequences, dict):
        report.add_error(
            f"Numbered object sequences in {context} must be an object",
            field="render.numbered_objects.sequences",
            next_action="Use sequence IDs mapped to label/style objects",
        )
    else:
        _merge_sequences(sequences, raw_sequences, report=report, context=context)

    raw_families = raw_config.get("families", {})
    if raw_families is None:
        raw_families = {}
    if not isinstance(raw_families, dict):
        report.add_error(
            f"Numbered object families in {context} must be an object",
            field="render.numbered_objects.families",
            next_action="Use family IDs mapped to sequence/label objects",
        )
    else:
        _merge_families(families, raw_families, report=report, context=context)

    for family_id, family in families.items():
        if family.sequence not in sequences:
            report.add_error(
                f"Numbered object family '{family_id}' references unknown sequence '{family.sequence}' in {context}",
                field=f"render.numbered_objects.families.{family_id}.sequence",
                next_action="Define the sequence under render.numbered_objects.sequences or use a built-in sequence",
            )

    return NumberedObjectConfig(
        numbering=numbering,
        sequences=sequences,
        families=families,
    )


def build_numbered_objects_index(
    course_id: str,
    objects: list[NumberedObject],
) -> dict[str, Any]:
    entries = [item.to_json() for item in objects]
    return {
        "version": NUMBERED_OBJECT_INDEX_VERSION,
        "course_id": course_id,
        "objects": entries,
        "by_id": {item["id"]: index for index, item in enumerate(entries)},
    }


def validate_numbered_objects_index(index_path: str | Path) -> ValidationReport:
    path = Path(index_path).resolve()
    report = ValidationReport(context="numbered-objects")

    if not path.exists():
        report.add_error(
            "Numbered objects index does not exist",
            path=path,
            next_action="Build the artifact or update manifest.json",
        )
        return report

    report.read_file(path)
    try:
        data = load_yaml_file(path)
    except Exception as exc:
        report.add_error(
            f"Could not read numbered objects index: {exc}",
            path=path,
            next_action="Fix generated data syntax",
        )
        return report

    if not isinstance(data, dict):
        report.add_error(
            "Numbered objects index must be an object",
            path=path,
            next_action="Use key/value index fields",
        )
        return report

    _validate_index_shape(data, path=path, report=report)

    if report.ok:
        report.add_info("Numbered objects index validation passed", path=path)
    return report


def _numbered_objects_config(
    course_config: dict[str, Any],
    *,
    report: ValidationReport,
    context: str,
) -> dict[str, Any] | None:
    render = course_config.get("render", {})
    if render is None:
        return None
    if not isinstance(render, dict):
        report.add_error(
            f"Render configuration in {context} must be an object",
            field="render",
            next_action="Use render.numbered_objects for numbered object settings",
        )
        return None

    raw_config = render.get("numbered_objects")
    if raw_config is None:
        return None
    if not isinstance(raw_config, dict):
        report.add_error(
            f"Numbered object configuration in {context} must be an object",
            field="render.numbered_objects",
            next_action="Use numbering, sequences, and families keys",
        )
        return None
    return raw_config


def _merge_sequences(
    sequences: dict[str, NumberedObjectSequence],
    raw_sequences: dict[str, Any],
    *,
    report: ValidationReport,
    context: str,
) -> None:
    for sequence_id, raw_sequence in raw_sequences.items():
        field = f"render.numbered_objects.sequences.{sequence_id}"
        if not isinstance(sequence_id, str) or not sequence_id:
            report.add_error(
                f"Numbered object sequence ID in {context} must be a non-empty string",
                field="render.numbered_objects.sequences",
                next_action="Use stable sequence IDs",
            )
            continue
        if not isinstance(raw_sequence, dict):
            report.add_error(
                f"Numbered object sequence '{sequence_id}' in {context} must be an object",
                field=field,
                next_action="Use label and style fields",
            )
            continue

        current = sequences.get(
            sequence_id,
            NumberedObjectSequence(label=sequence_id.replace("-", " ").title(), style="margin"),
        )
        label = raw_sequence.get("label", current.label)
        style = raw_sequence.get("style", current.style)
        if not isinstance(label, str) or not label:
            report.add_error(
                f"Numbered object sequence '{sequence_id}' in {context} needs a non-empty label",
                field=f"{field}.label",
                next_action="Set a reader-facing sequence label",
            )
            label = current.label
        if style not in NUMBERED_OBJECT_STYLES:
            report.add_error(
                f"Numbered object sequence '{sequence_id}' in {context} uses unknown style '{style}'",
                field=f"{field}.style",
                next_action="Use margin, banded, caption, or equation",
            )
            style = current.style
        sequences[sequence_id] = NumberedObjectSequence(label=label, style=style)


def _merge_families(
    families: dict[str, NumberedObjectFamily],
    raw_families: dict[str, Any],
    *,
    report: ValidationReport,
    context: str,
) -> None:
    for family_id, raw_family in raw_families.items():
        field = f"render.numbered_objects.families.{family_id}"
        if not isinstance(family_id, str) or not family_id:
            report.add_error(
                f"Numbered object family ID in {context} must be a non-empty string",
                field="render.numbered_objects.families",
                next_action="Use stable family IDs",
            )
            continue
        if not isinstance(raw_family, dict):
            report.add_error(
                f"Numbered object family '{family_id}' in {context} must be an object",
                field=field,
                next_action="Use sequence and label fields",
            )
            continue

        current = families.get(
            family_id,
            NumberedObjectFamily(sequence=family_id, label=family_id.replace("-", " ").title()),
        )
        sequence = raw_family.get("sequence", current.sequence)
        label = raw_family.get("label", current.label)
        if not isinstance(sequence, str) or not sequence:
            report.add_error(
                f"Numbered object family '{family_id}' in {context} needs a non-empty sequence",
                field=f"{field}.sequence",
                next_action="Set a sequence ID",
            )
            sequence = current.sequence
        if not isinstance(label, str) or not label:
            report.add_error(
                f"Numbered object family '{family_id}' in {context} needs a non-empty label",
                field=f"{field}.label",
                next_action="Set a reader-facing family label",
            )
            label = current.label
        families[family_id] = NumberedObjectFamily(sequence=sequence, label=label)


def _validate_index_shape(data: dict[str, Any], *, path: Path, report: ValidationReport) -> None:
    if data.get("version") != NUMBERED_OBJECT_INDEX_VERSION:
        report.add_error(
            "Numbered objects index version is unsupported",
            path=path,
            field="version",
            next_action=f"Write version {NUMBERED_OBJECT_INDEX_VERSION}",
        )
    if not isinstance(data.get("course_id"), str) or not data.get("course_id"):
        report.add_error(
            "Numbered objects index requires a course_id",
            path=path,
            field="course_id",
            next_action="Write the source course ID",
        )

    objects = data.get("objects")
    if not isinstance(objects, list):
        report.add_error(
            "Numbered objects index requires an objects list",
            path=path,
            field="objects",
            next_action="Write numbered object entries in order",
        )
        return

    by_id = data.get("by_id")
    if not isinstance(by_id, dict):
        report.add_error(
            "Numbered objects index requires a by_id map",
            path=path,
            field="by_id",
            next_action="Map object IDs to positions in objects",
        )
        by_id = {}

    seen_ids: set[str] = set()
    for index, item in enumerate(objects):
        field = f"objects.{index}"
        if not isinstance(item, dict):
            report.add_error(
                "Numbered object entry must be an object",
                path=path,
                field=field,
                next_action="Write object entries with stable fields",
            )
            continue
        _validate_object_entry(item, path=path, field=field, report=report)
        object_id = item.get("id")
        if isinstance(object_id, str) and object_id:
            if object_id in seen_ids:
                report.add_error(
                    f"Duplicate numbered object ID '{object_id}'",
                    path=path,
                    field=f"{field}.id",
                    next_action="Use stable unique object IDs",
                )
            seen_ids.add(object_id)
            if by_id.get(object_id) != index:
                report.add_error(
                    f"Numbered object by_id entry for '{object_id}' must point to objects index {index}",
                    path=path,
                    field=f"by_id.{object_id}",
                    next_action="Regenerate by_id from objects",
                )
    for object_id in by_id:
        if object_id not in seen_ids:
            report.add_error(
                f"Numbered object by_id entry '{object_id}' has no matching object",
                path=path,
                field=f"by_id.{object_id}",
                next_action="Remove stale by_id entries or regenerate by_id from objects",
            )


def _validate_object_entry(
    item: dict[str, Any],
    *,
    path: Path,
    field: str,
    report: ValidationReport,
) -> None:
    required_strings = (
        "id",
        "family",
        "sequence",
        "label",
        "number",
        "reference_text",
        "anchor",
        "source_path",
        "page_id",
        "page_title",
        "page_output_path",
        "href",
        "style",
    )
    for key in required_strings:
        if not isinstance(item.get(key), str) or not item.get(key):
            report.add_error(
                f"Numbered object entry requires non-empty '{key}'",
                path=path,
                field=f"{field}.{key}",
                next_action="Regenerate numbered objects index from validated course content",
            )
    title = item.get("title")
    if title is not None and not isinstance(title, str):
        report.add_error(
            "Numbered object entry title must be a string or null when present",
            path=path,
            field=f"{field}.title",
            next_action="Use a string title, null, or omit title for untitled objects",
        )
    label = item.get("label")
    number = item.get("number")
    reference_text = item.get("reference_text")
    if (
        isinstance(label, str)
        and label
        and isinstance(number, str)
        and number
        and reference_text != f"{label} {number}"
    ):
        report.add_error(
            "Numbered object reference_text must match label and number",
            path=path,
            field=f"{field}.reference_text",
            next_action="Regenerate reference_text from label and number",
        )
    object_id = item.get("id")
    anchor = item.get("anchor")
    if (
        isinstance(object_id, str)
        and object_id
        and isinstance(anchor, str)
        and anchor != f"raya-object-{object_id}"
    ):
        report.add_error(
            "Numbered object anchor must match id",
            path=path,
            field=f"{field}.anchor",
            next_action="Regenerate anchor as raya-object-<id>",
        )
    style = item.get("style")
    if isinstance(style, str) and style and style not in NUMBERED_OBJECT_STYLES:
        report.add_error(
            f"Numbered object entry uses unknown style '{style}'",
            path=path,
            field=f"{field}.style",
            next_action="Use margin, banded, caption, or equation",
        )
