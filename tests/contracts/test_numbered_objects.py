from __future__ import annotations

import json

from raya_schema.numbered_objects import (
    BUILT_IN_NUMBERED_OBJECT_FAMILIES,
    BUILT_IN_NUMBERED_OBJECT_SEQUENCES,
    NUMBERED_OBJECT_INDEX_PATH,
    NumberedObject,
    build_numbered_objects_index,
    normalize_numbered_object_config,
    validate_numbered_objects_index,
)
from raya_schema.validation import ValidationReport


def test_built_in_numbered_object_defaults_group_math_and_coursework() -> None:
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["theorem"]["sequence"] == "theorem"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["lemma"]["sequence"] == "theorem"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["proposition"]["sequence"] == "theorem"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["corollary"]["sequence"] == "theorem"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["definition"]["sequence"] == "theorem"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["example"]["sequence"] == "example"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["exercise"]["sequence"] == "exercise"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["problem"]["sequence"] == "exercise"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["homework"]["sequence"] == "assignment"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["assignment"]["sequence"] == "assignment"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["project"]["sequence"] == "assignment"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["exam"]["sequence"] == "assignment"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["task"]["sequence"] == "assignment"
    assert "proof" not in BUILT_IN_NUMBERED_OBJECT_FAMILIES
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["figure"]["sequence"] == "figure"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["table"]["sequence"] == "table"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["equation"]["sequence"] == "equation"
    assert BUILT_IN_NUMBERED_OBJECT_SEQUENCES["theorem"]["style"] == "margin"
    assert BUILT_IN_NUMBERED_OBJECT_SEQUENCES["assignment"]["style"] == "banded"
    assert NUMBERED_OBJECT_INDEX_PATH == "data/numbered-objects.json"


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


def test_normalize_numbered_object_config_accepts_positional_api() -> None:
    report = ValidationReport()

    config = normalize_numbered_object_config({}, report, "raya.yaml")

    assert report.ok
    assert config.numbering == "page-hierarchy"


def test_normalize_numbered_object_config_accepts_caption_and_equation_styles() -> None:
    report = ValidationReport()
    config = normalize_numbered_object_config(
        {
            "render": {
                "numbered_objects": {
                    "sequences": {
                        "figure": {"style": "caption"},
                        "equation": {"style": "equation"},
                    }
                }
            }
        },
        report=report,
        context="raya.yaml",
    )

    assert report.ok
    assert config.sequences["figure"].style == "caption"
    assert config.sequences["equation"].style == "equation"


def test_normalize_numbered_object_config_rejects_unknown_sequence_reference() -> None:
    report = ValidationReport()

    normalize_numbered_object_config(
        {"render": {"numbered_objects": {"families": {"claim": {"sequence": "claims"}}}}},
        report=report,
        context="raya.yaml",
    )

    assert not report.ok
    assert any("claims" in issue.message and "claim" in issue.message for issue in report.issues)


def test_numbered_object_serializes_anchor_in_json_entry() -> None:
    item = NumberedObject(
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

    entry = item.to_json()

    assert entry["anchor"] == "raya-object-pythagorean"
    assert entry["reference_text"] == "Theorem 2.3.1"


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
    assert index["objects"][0]["anchor"] == "raya-object-pythagorean"
    assert index["by_id"]["pythagorean"] == 0


def test_numbered_objects_index_validation_allows_untitled_objects(tmp_path) -> None:
    index = build_numbered_objects_index(
        "demo",
        [
            NumberedObject(
                id="untitled-theorem",
                family="theorem",
                sequence="theorem",
                label="Theorem",
                number="1.1",
                title="",
                source_path="course/1_intro/0_index.md",
                page_id="intro",
                page_title="Intro",
                page_output_path="1_intro/index.html",
                href="1_intro/#raya-object-untitled-theorem",
                style="margin",
            )
        ],
    )
    index["objects"][0]["title"] = None
    path = tmp_path / "numbered-objects-null-title.json"
    path.write_text(json.dumps(index), encoding="utf-8")

    null_report = validate_numbered_objects_index(path)

    assert null_report.ok

    del index["objects"][0]["title"]
    path = tmp_path / "numbered-objects-missing-title.json"
    path.write_text(json.dumps(index), encoding="utf-8")

    missing_report = validate_numbered_objects_index(path)

    assert missing_report.ok


def test_build_numbered_objects_index_accepts_positional_api() -> None:
    index = build_numbered_objects_index("demo", [])

    assert index["course_id"] == "demo"
    assert index["objects"] == []
    assert index["by_id"] == {}


def test_numbered_objects_index_validation_accepts_all_supported_styles(tmp_path) -> None:
    objects = []
    for style in ("margin", "banded", "caption", "equation"):
        objects.append(
            NumberedObject(
                id=f"{style}-item",
                family="example",
                sequence="example",
                label="Example",
                number=f"1.{len(objects) + 1}",
                title=f"{style.title()} item",
                source_path="course/1_intro/0_index.md",
                page_id="intro",
                page_title="Intro",
                page_output_path="1_intro/index.html",
                href=f"1_intro/#raya-object-{style}-item",
                style=style,
            )
        )
    index = build_numbered_objects_index("demo", objects)
    path = tmp_path / "numbered-objects.json"
    path.write_text(json.dumps(index), encoding="utf-8")

    report = validate_numbered_objects_index(path)

    assert report.ok


def test_numbered_objects_index_validation_rejects_stale_by_id_keys(tmp_path) -> None:
    index = build_numbered_objects_index("demo", [])
    index["by_id"]["stale"] = 0
    path = tmp_path / "numbered-objects.json"
    path.write_text(json.dumps(index), encoding="utf-8")

    report = validate_numbered_objects_index(path)

    assert not report.ok
    assert any("stale" in issue.message for issue in report.issues)
