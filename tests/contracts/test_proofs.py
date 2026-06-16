from pathlib import Path

from raya_schema import ValidationReport
from raya_static.numbered_objects import prepare_numbered_object_markdown
from raya_static.proofs import (
    PLACEHOLDER_PREFIX,
    STATIC_ENVIRONMENT_KINDS,
    is_static_environment_directive_open,
    prepare_proof_markdown,
    prepare_static_environment_markdown,
)


def _report() -> ValidationReport:
    return ValidationReport()


def test_prepare_proof_markdown_extracts_plain_proof() -> None:
    report = _report()
    prepared = prepare_proof_markdown(
        "Before\n\n::: proof\nUse induction.\n:::\n\nAfter\n",
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert report.ok
    assert prepared.body == f"Before\n\n\n{PLACEHOLDER_PREFIX}0\n\n\nAfter\n"
    assert len(prepared.sources) == 1
    source = prepared.sources[0]
    assert source.placeholder == f"{PLACEHOLDER_PREFIX}0"
    assert source.id is None
    assert source.of_id is None
    assert source.title is None
    assert source.body == "Use induction."
    assert source.start_line == 3


def test_prepare_proof_markdown_extracts_plain_proof_with_trailing_spaces() -> None:
    report = _report()
    prepared = prepare_proof_markdown(
        "::: proof   \nUse induction.\n:::\n",
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert report.ok
    assert len(prepared.sources) == 1
    source = prepared.sources[0]
    assert source.id is None
    assert source.of_id is None
    assert source.title is None
    assert source.body == "Use induction."


def test_prepare_proof_markdown_extracts_id_target_and_title() -> None:
    report = _report()
    prepared = prepare_proof_markdown(
        '::: proof {#proof-main of="main-theorem" title="Key steps"}\nDone.\n:::\n',
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert report.ok
    source = prepared.sources[0]
    assert source.id == "proof-main"
    assert source.of_id == "main-theorem"
    assert source.title == "Key steps"
    assert source.body == "Done."


def test_prepare_static_environment_markdown_extracts_solution_hint_and_answer() -> None:
    report = _report()
    prepared = prepare_static_environment_markdown(
        '::: solution {#solution-one of="problem-one" title="Normal equations"}\n'
        "Solve $Ax=b$.\n"
        ":::\n\n"
        '::: hint {#hint-one of="problem-one"}\n'
        "Start with the residual.\n"
        ":::\n\n"
        "::: answer\n"
        "$x=0$.\n"
        ":::\n",
        report=report,
        source_path=Path("course/4_reader_ux/0_index.md"),
    )

    assert report.ok
    assert STATIC_ENVIRONMENT_KINDS == ("proof", "solution", "hint", "answer")
    assert [source.kind for source in prepared.sources] == [
        "solution",
        "hint",
        "answer",
    ]
    assert prepared.sources[0].placeholder == f"{PLACEHOLDER_PREFIX}0"
    assert prepared.sources[0].id == "solution-one"
    assert prepared.sources[0].of_id == "problem-one"
    assert prepared.sources[0].title == "Normal equations"
    assert prepared.sources[0].body == "Solve $Ax=b$."
    assert prepared.sources[1].id == "hint-one"
    assert prepared.sources[1].of_id == "problem-one"
    assert prepared.sources[1].title is None
    assert prepared.sources[2].id is None
    assert prepared.sources[2].of_id is None
    assert prepared.sources[2].title is None
    assert prepared.body.count(PLACEHOLDER_PREFIX) == 3


def test_prepare_proof_markdown_remains_compatible_wrapper() -> None:
    report = _report()
    prepared = prepare_proof_markdown(
        '::: proof {#proof-main of="main-theorem" title="Key steps"}\nDone.\n:::\n',
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert report.ok
    assert prepared.sources[0].kind == "proof"
    assert prepared.sources[0].id == "proof-main"
    assert prepared.sources[0].of_id == "main-theorem"
    assert prepared.sources[0].title == "Key steps"


def test_static_environment_opener_detects_all_static_environment_kinds() -> None:
    assert is_static_environment_directive_open("::: proof")
    assert is_static_environment_directive_open('::: solution {of="problem"}')
    assert is_static_environment_directive_open("::: hint   ")
    assert is_static_environment_directive_open("::: answer")
    assert not is_static_environment_directive_open("::: theorem {#main}")


def test_numbered_object_parser_leaves_proof_blocks_for_proof_parser() -> None:
    report = _report()
    prepared = prepare_numbered_object_markdown(
        '::: proof {of="main-theorem"}\nText.\n:::\n',
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert report.ok
    assert prepared.sources == []
    assert '::: proof {of="main-theorem"}' in prepared.body


def test_numbered_object_parser_skips_fenced_directive_text_inside_proof() -> None:
    report = _report()
    prepared = prepare_numbered_object_markdown(
        "::: proof\n"
        "```md\n"
        "::: theorem {#not-real}\n"
        ":::\n"
        "```\n"
        "Done.\n"
        ":::\n"
        "\n"
        "::: theorem {#real}\n"
        "Real theorem.\n"
        ":::\n",
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert report.ok
    assert [source.id for source in prepared.sources] == ["real"]
    assert "not-real" in prepared.body
    assert "Real theorem." not in prepared.body


def test_numbered_object_parser_leaves_malformed_proof_for_proof_parser() -> None:
    report = _report()
    prepared = prepare_numbered_object_markdown(
        '::: proof of="main-theorem"\n'
        "::: theorem {#not-real}\n"
        "Not real.\n"
        ":::\n"
        ":::\n"
        "\n"
        "::: theorem {#real}\n"
        "Real theorem.\n"
        ":::\n",
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert report.ok
    assert [source.id for source in prepared.sources] == ["real"]
    assert "not-real" in prepared.body
    assert "Real theorem." not in prepared.body


def test_prepare_proof_markdown_rejects_invalid_id() -> None:
    report = _report()
    prepare_proof_markdown(
        "::: proof {#bad/id}\nText.\n:::\n",
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert not report.ok
    diagnostic = report.diagnostics[0]
    assert diagnostic.message == "Invalid proof ID 'bad/id'"
    assert diagnostic.field == "line:1"
    assert diagnostic.next_action.startswith("Use an ID that starts with a letter")


def test_prepare_proof_markdown_rejects_braceless_attributes() -> None:
    report = _report()
    prepared = prepare_proof_markdown(
        '::: proof of="main-theorem"\nText.\n:::\n',
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert not report.ok
    diagnostic = report.diagnostics[0]
    assert diagnostic.message == "Proof directive attributes must use braces"
    assert diagnostic.field == "line:1"
    assert diagnostic.next_action == 'Use attributes such as {#proof-id of="theorem-id"}'
    assert len(prepared.sources) == 1


def test_prepare_proof_markdown_rejects_unterminated_attribute_braces() -> None:
    report = _report()
    prepare_proof_markdown(
        "::: proof {#proof-main\nText.\n:::\n",
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert not report.ok
    diagnostic = report.diagnostics[0]
    assert diagnostic.message == "Proof directive attributes must use braces"
    assert diagnostic.field == "line:1"


def test_prepare_proof_markdown_rejects_empty_id() -> None:
    report = _report()
    prepare_proof_markdown(
        "::: proof {#}\nText.\n:::\n",
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert not report.ok
    diagnostic = report.diagnostics[0]
    assert diagnostic.message == "Invalid proof ID ''"
    assert diagnostic.field == "line:1"


def test_prepare_proof_markdown_rejects_empty_target_id() -> None:
    report = _report()
    prepare_proof_markdown(
        '::: proof {of=""}\nText.\n:::\n',
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert not report.ok
    diagnostic = report.diagnostics[0]
    assert diagnostic.message == "Invalid proof target ID ''"
    assert diagnostic.field == "line:1"


def test_prepare_proof_markdown_rejects_unknown_attribute() -> None:
    report = _report()
    prepare_proof_markdown(
        '::: proof {kind="direct"}\nText.\n:::\n',
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert not report.ok
    diagnostic = report.diagnostics[0]
    assert diagnostic.message == "Unknown proof attribute 'kind'"
    assert diagnostic.field == "line:1"
    assert (
        diagnostic.next_action
        == 'Use #id, of="object-id", or title="Optional title"'
    )


def test_prepare_proof_markdown_rejects_missing_close() -> None:
    report = _report()
    prepare_proof_markdown(
        "::: proof\nText.\n",
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert not report.ok
    diagnostic = report.diagnostics[0]
    assert diagnostic.message == "Proof directive is missing a closing ::: line"
    assert diagnostic.field == "line:1"


def test_prepare_proof_markdown_rejects_nested_proof_or_numbered_block() -> None:
    report = _report()
    prepare_proof_markdown(
        "::: proof\n::: theorem {#inner}\nNo.\n:::\n:::\n",
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert not report.ok
    diagnostic = report.diagnostics[0]
    assert diagnostic.message == "Proof directive contains nested directive"
    assert diagnostic.field == "line:2"
    assert diagnostic.next_action == "Close the proof before starting another directive block"


def test_prepare_proof_markdown_ignores_fenced_directive_text() -> None:
    report = _report()
    prepared = prepare_proof_markdown(
        "```md\n::: proof\nNot real.\n:::\n```\n",
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert report.ok
    assert prepared.sources == []
    assert "Not real." in prepared.body


def test_prepare_proof_markdown_allows_fenced_directive_text_inside_proof() -> None:
    report = _report()
    prepared = prepare_proof_markdown(
        "::: proof\n```md\n::: theorem {#not-real}\n:::\n```\nDone.\n:::\n",
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert report.ok
    assert len(prepared.sources) == 1
    assert "not-real" in prepared.sources[0].body


def test_authored_proof_placeholder_prefix_is_rejected() -> None:
    report = _report()
    prepare_proof_markdown(
        f"{PLACEHOLDER_PREFIX}0\n",
        report=report,
        source_path=Path("course/3_numbered_objects/0_index.md"),
    )

    assert not report.ok
    diagnostic = report.diagnostics[0]
    assert diagnostic.message == "Reserved proof placeholder text"
    assert diagnostic.next_action == f"Remove text that starts with {PLACEHOLDER_PREFIX}"
