from __future__ import annotations

import json

from raya_schema.numbered_objects import (
    BUILT_IN_NUMBERED_OBJECT_FAMILIES,
    BUILT_IN_NUMBERED_OBJECT_SEQUENCES,
    NumberedObject,
    build_numbered_objects_index,
    normalize_numbered_object_config,
    validate_numbered_objects_index,
)
from raya_schema.validation import ValidationReport


def test_built_in_numbered_object_defaults_group_math_and_coursework() -> None:
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["theorem"]["sequence"] == "theorem"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["lemma"]["sequence"] == "theorem"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["corollary"]["sequence"] == "theorem"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["definition"]["sequence"] == "theorem"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["example"]["sequence"] == "example"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["exercise"]["sequence"] == "exercise"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["problem"]["sequence"] == "exercise"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["homework"]["sequence"] == "assignment"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["assignment"]["sequence"] == "assignment"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["project"]["sequence"] == "assignment"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["exam"]["sequence"] == "assignment"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["figure"]["sequence"] == "figure"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["table"]["sequence"] == "table"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["equation"]["sequence"] == "equation"
    assert BUILT_IN_NUMBERED_OBJECT_SEQUENCES["theorem"]["style"] == "margin"
    assert BUILT_IN_NUMBERED_OBJECT_SEQUENCES["assignment"]["style"] == "banded"


def test_normalize_numbered_object_config_accepts_course_overrides() -> None:
    report = ValidationReport()
    config = normalize_numbered_object_config(
        {
            "render": {
                "numbered_objects": {
                    "numbering": "page-hierarchy",
                    "sequences": {
                        "assignment": {"label": "Activity", "style": "margin"},
                        "lab": {"label": "Lab", "style": "banded"},
                    },
                    "families": {
                        "lab": {"sequence": "lab", "label": "Lab"},
                        "checkpoint": {"sequence": "exercise", "label": "Checkpoint"},
                    },
                },
            }
        },
        report=report,
        context="raya.yaml",
    )

    assert report.ok
    assert config.numbering == "page-hierarchy"
    assert config.sequences["assignment"].label == "Activity"
    assert config.sequences["assignment"].style == "margin"
    assert config.sequences["lab"].label == "Lab"
    assert config.families["lab"].sequence == "lab"
    assert config.families["checkpoint"].sequence == "exercise"


def test_normalize_numbered_object_config_rejects_unknown_sequence_reference() -> None:
    report = ValidationReport()

    normalize_numbered_object_config(
        {"render": {"numbered_objects": {"families": {"claim": {"sequence": "claims"}}}}},
        report=report,
        context="raya.yaml",
    )

    assert not report.ok
    assert any("claims" in issue.message and "claim" in issue.message for issue in report.issues)


def test_numbered_objects_index_validation_requires_stable_shape(tmp_path) -> None:
    index = build_numbered_objects_index(
        course_id="demo",
        objects=[
            NumberedObject(
                id="pythagorean",
                family="theorem",
                sequence="theorem",
                label="Theorem",
                number="2.3.1",
                title="Pythagorean theorem",
                source_path="course/2_vectors/3_norms.md",
                page_id="norms",
                page_title="Norms",
                page_output_path="2_vectors/3_norms/index.html",
                href="2_vectors/3_norms/#raya-object-pythagorean",
                style="margin",
            )
        ],
    )
    path = tmp_path / "numbered-objects.json"
    path.write_text(json.dumps(index), encoding="utf-8")

    report = validate_numbered_objects_index(path)

    assert report.ok
    assert index["objects"][0]["reference_text"] == "Theorem 2.3.1"
    assert index["by_id"]["pythagorean"] == 0
