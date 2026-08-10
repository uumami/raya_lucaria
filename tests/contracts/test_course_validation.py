from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from raya_schema import validate_course
from raya_schema.content import resolve_course_content
from raya_schema.numbered_objects import collect_numbered_object_source_references
from raya_schema.official import discover_official_objects
from raya_schema.diagnostics import ValidationReport
from raya_schema.yaml_io import load_yaml_file


ROOT = Path(__file__).resolve().parents[2]
MINIMAL = ROOT / "examples" / "courses" / "minimal"
REFERENCE_FIXTURE = ROOT / "examples" / "courses" / "reference-fixture"
RUNTIME_FIXTURE = ROOT / "examples" / "courses" / "runtime-fixture"
INVALID_UNSUPPORTED_RUNTIME = ROOT / "examples" / "courses" / "invalid" / "unsupported-runtime-manager"
INVALID_MISSING_RUNTIME_LOCKFILE = ROOT / "examples" / "courses" / "invalid" / "missing-runtime-lockfile"
INVALID_ESCAPING_RUNTIME_INPUT = ROOT / "examples" / "courses" / "invalid" / "escaping-runtime-input"
INVALID_UNSAFE_RUNTIME_DEFAULT = ROOT / "examples" / "courses" / "invalid" / "unsafe-runtime-default"


def test_minimal_fixture_validates() -> None:
    report = validate_course(MINIMAL)
    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert MINIMAL / "raya.yaml" in report.files_read


def test_calendar_document_is_separate_from_official_objects(tmp_path: Path) -> None:
    course = _copy_minimal_course(tmp_path)
    _set_calendar_timezone(course, "America/Mexico_City")
    _write_calendar_document(course, "1_2026-o26.yaml", events=[_session_event()])

    report = validate_course(course)

    assert report.ok, [item.format() for item in report.diagnostics]
    objects = _discover_official_objects_for_test(course)
    assert all(item["type"] != "calendar" for item in objects)


@pytest.mark.parametrize(
    ("field", "value"),
    [("due", "2026-2-03"), ("available", "tomorrow")],
)
def test_task_family_dates_must_be_iso_civil_dates(
    tmp_path: Path,
    field: str,
    value: str,
) -> None:
    course = _copy_minimal_course(tmp_path)
    _write_assignment(course, content_line=f"  {field}: '{value}'")

    report = validate_course(course)

    assert not report.ok
    assert any(item.field == f"content.{field}" for item in report.diagnostics)


def test_calendar_rejects_invalid_timezone(tmp_path: Path) -> None:
    course = _copy_minimal_course(tmp_path)
    _set_calendar_timezone(course, "Mexico/Imaginary")

    report = validate_course(course)

    assert not report.ok
    assert any(item.field == "calendar.timezone" for item in report.diagnostics)


def test_calendar_rejects_path_like_timezone_without_crashing(tmp_path: Path) -> None:
    course = _copy_minimal_course(tmp_path)
    _set_calendar_timezone(course, "/usr/share/zoneinfo/UTC")

    report = validate_course(course)

    assert not report.ok
    assert any(
        item.message == "calendar.timezone must be a valid IANA timezone"
        and item.field == "calendar.timezone"
        for item in report.diagnostics
    )


def test_calendar_rejects_blank_timezone(tmp_path: Path) -> None:
    course = _copy_minimal_course(tmp_path)
    _set_calendar_timezone(course, "   ")

    report = validate_course(course)

    assert not report.ok
    assert any(item.field == "calendar.timezone" for item in report.diagnostics)


def test_calendar_rejects_unordered_document_filename(tmp_path: Path) -> None:
    course = _copy_minimal_course(tmp_path)
    _set_calendar_timezone(course, "America/Mexico_City")
    _write_calendar_document(course, "term.yaml", events=[_session_event()])

    report = validate_course(course)

    assert not report.ok
    assert any("Unordered calendar document file" == item.message for item in report.diagnostics)


def test_calendar_rejects_duplicate_numeric_document_order(tmp_path: Path) -> None:
    course = _copy_minimal_course(tmp_path)
    _set_calendar_timezone(course, "America/Mexico_City")
    _write_calendar_document(course, "01_first.yaml", events=[_session_event()])
    _write_calendar_document(
        course,
        "1_second.yaml",
        document_id="second-term",
        events=[{**_session_event(), "id": "session-02"}],
    )

    report = validate_course(course)

    assert not report.ok
    assert any(
        item.message == "Duplicate calendar document order"
        and item.path == course / "course/_official/calendar/1_second.yaml"
        for item in report.diagnostics
    )


@pytest.mark.parametrize(
    "filename",
    ["nested/1_term.yaml", "1_term.yml"],
)
def test_calendar_rejects_unsupported_document_location_or_suffix(
    tmp_path: Path,
    filename: str,
) -> None:
    course = _copy_minimal_course(tmp_path)
    _set_calendar_timezone(course, "America/Mexico_City")
    calendar_path = _write_calendar_document(
        course,
        filename,
        events=[_session_event()],
    )

    report = validate_course(course)

    assert not report.ok
    assert any(
        item.message == "Calendar documents must be direct .yaml files"
        and item.path == calendar_path
        for item in report.diagnostics
    )


def test_calendar_rejects_duplicate_document_ids(tmp_path: Path) -> None:
    course = _copy_minimal_course(tmp_path)
    _set_calendar_timezone(course, "America/Mexico_City")
    _write_calendar_document(course, "1_first.yaml", events=[_session_event()])
    _write_calendar_document(
        course,
        "2_second.yaml",
        events=[{**_session_event(), "id": "session-02"}],
    )

    report = validate_course(course)

    assert not report.ok
    assert any("Duplicate calendar document ID" == item.message for item in report.diagnostics)


def test_calendar_rejects_duplicate_event_ids_within_document(tmp_path: Path) -> None:
    course = _copy_minimal_course(tmp_path)
    _set_calendar_timezone(course, "America/Mexico_City")
    _write_calendar_document(
        course,
        "1_term.yaml",
        events=[_session_event(), {**_session_event(), "title": "Repeated session"}],
    )

    report = validate_course(course)

    assert not report.ok
    assert any("Duplicate calendar event ID" == item.message for item in report.diagnostics)


@pytest.mark.parametrize(
    ("blank_field", "expected_field"),
    [
        ("document_id", "id"),
        ("event_id", "events.0.id"),
        ("event_title", "events.0.title"),
    ],
)
def test_calendar_rejects_whitespace_only_identifiers_and_titles(
    tmp_path: Path,
    blank_field: str,
    expected_field: str,
) -> None:
    course = _copy_minimal_course(tmp_path)
    _set_calendar_timezone(course, "America/Mexico_City")
    document_id = "'   '" if blank_field == "document_id" else "term"
    event = _session_event()
    if blank_field == "event_id":
        event["id"] = "   "
    elif blank_field == "event_title":
        event["title"] = "   "
    _write_calendar_document(
        course,
        "1_term.yaml",
        document_id=document_id,
        events=[event],
    )

    report = validate_course(course)

    assert not report.ok
    assert any(item.field == expected_field for item in report.diagnostics)


@pytest.mark.parametrize(
    "event",
    [
        {"id": "x", "kind": "meeting", "date": "2026-08-10", "title": "Bad"},
        {"id": "x", "kind": "session", "date": "2026-08-10", "end_time": "18:00", "title": "Bad"},
        {
            "id": "x",
            "kind": "session",
            "date": "2026-08-10",
            "start_time": "18:00",
            "end_time": "16:00",
            "title": "Bad",
        },
    ],
)
def test_calendar_rejects_invalid_event_semantics(
    tmp_path: Path,
    event: dict[str, str],
) -> None:
    course = _copy_minimal_course(tmp_path)
    _set_calendar_timezone(course, "America/Mexico_City")
    _write_calendar_document(course, "1_term.yaml", events=[event])

    assert not validate_course(course).ok


def test_calendar_rejects_unresolved_event_page(tmp_path: Path) -> None:
    course = _copy_minimal_course(tmp_path)
    _set_calendar_timezone(course, "America/Mexico_City")
    _write_calendar_document(
        course,
        "1_term.yaml",
        events=[{**_session_event(), "page": "missing-page"}],
    )

    report = validate_course(course)

    assert not report.ok
    assert any(item.field == "events.0.page" for item in report.diagnostics)


def test_calendar_rejects_duplicate_global_occurrence_id(tmp_path: Path) -> None:
    course = _copy_minimal_course(tmp_path)
    _set_calendar_timezone(course, "America/Mexico_City")
    _write_calendar_document(course, "1_first.yaml", events=[_session_event()])
    _write_calendar_document(course, "2_second.yaml", events=[_session_event()])

    report = validate_course(course)

    assert not report.ok
    assert any("Duplicate calendar occurrence ID" == item.message for item in report.diagnostics)


def test_calendar_accepts_valid_cancellation_event(tmp_path: Path) -> None:
    course = _copy_minimal_course(tmp_path)
    _set_calendar_timezone(course, "America/Mexico_City")
    _write_calendar_document(
        course,
        "1_term.yaml",
        events=[
            {
                "id": "cancellation-01",
                "kind": "cancellation",
                "date": "2026-08-12",
                "title": "Class cancelled",
                "summary": "Campus closure.",
            }
        ],
    )

    report = validate_course(course)

    assert report.ok, [item.format() for item in report.diagnostics]


@pytest.mark.parametrize("skin_value", ["", "   ", 123])
def test_invalid_render_skin_value_fails_course_validation(
    tmp_path: Path,
    skin_value: object,
) -> None:
    course = _copy_minimal_course(tmp_path)
    config_path = course / "raya.yaml"
    if isinstance(skin_value, str):
        skin_yaml = f'"{skin_value}"'
    else:
        skin_yaml = str(skin_value)
    config_path.write_text(
        config_path.read_text(encoding="utf-8")
        + "\n"
        + "render:\n"
        + f"  skin: {skin_yaml}\n",
        encoding="utf-8",
    )

    report = validate_course(course)

    assert not report.ok
    assert any(
        diagnostic.message == "render.skin must be a non-empty string"
        and diagnostic.path == config_path
        and diagnostic.field == "render.skin"
        for diagnostic in report.diagnostics
    )


def test_unknown_explicit_numbered_object_reference_fails_validation(
    tmp_path: Path,
) -> None:
    course = _copy_minimal_course(tmp_path)
    index = course / "course" / "0_index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\n\n"
        "See [missing theorem](raya:ref/missing-theorem).\n",
        encoding="utf-8",
    )

    report = validate_course(course)

    assert not report.ok
    assert any(
        diagnostic.message
        == "Unknown numbered object reference 'raya:ref/missing-theorem'"
        and diagnostic.path == index
        and diagnostic.field == "link:raya:ref/missing-theorem"
        and "matches a numbered object ID" in (diagnostic.next_action or "")
        for diagnostic in report.diagnostics
    )


def test_explicit_numbered_object_reference_accepts_matching_directive(
    tmp_path: Path,
) -> None:
    course = _copy_minimal_course(tmp_path)
    index = course / "course" / "0_index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\n\n"
        "::: theorem {#known-theorem}\n"
        "Known theorem body.\n"
        ":::\n\n"
        "See [known theorem](raya:ref/known-theorem).\n",
        encoding="utf-8",
    )

    report = validate_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]


def test_unique_wikilink_validates_against_course_pages(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    source.mkdir()
    (source / "0_index.md").write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n"
        "# Root\n\nRead [[First Topic|the first topic]].\n",
        encoding="utf-8",
    )
    (source / "1_unit").mkdir()
    (source / "1_unit" / "0_index.md").write_text(
        "---\nid: unit\ntitle: Unit\nsummary: Unit page.\n---\n# Unit\n",
        encoding="utf-8",
    )
    (source / "1_unit" / "1_topic").mkdir()
    (source / "1_unit" / "1_topic" / "0_index.md").write_text(
        "---\nid: first-topic\ntitle: First Topic\nsummary: Topic page.\n---\n# Topic\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]


def test_wikilinks_resolve_source_paths_and_ignore_fenced_examples(
    tmp_path: Path,
) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    source.mkdir()
    (source / "0_index.md").write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n"
        "# Root\n\n"
        "Read [[1_unit/1_topic/0_index.md|the source-path topic]].\n\n"
        "Inline examples such as `[[Missing Inline Example]]` are not links.\n\n"
        "```markdown\n"
        "[[Missing Fenced Example]]\n"
        "```\n",
        encoding="utf-8",
    )
    (source / "1_unit").mkdir()
    (source / "1_unit" / "0_index.md").write_text(
        "---\nid: unit\ntitle: Unit\nsummary: Unit page.\n---\n# Unit\n",
        encoding="utf-8",
    )
    (source / "1_unit" / "1_topic").mkdir()
    (source / "1_unit" / "1_topic" / "0_index.md").write_text(
        "---\nid: first-topic\ntitle: First Topic\nsummary: Topic page.\n---\n# Topic\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]


def test_missing_wikilink_fails_validation(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    source.mkdir()
    root = source / "0_index.md"
    root.write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n"
        "# Root\n\nRead [[Missing Topic]].\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)

    assert not report.ok
    assert any(
        diagnostic.message == "Broken wikilink reference"
        and diagnostic.path == root
        and diagnostic.field == "wikilink:Missing Topic"
        for diagnostic in report.diagnostics
    )


def test_ambiguous_wikilink_fails_validation(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    source.mkdir()
    root = source / "0_index.md"
    root.write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n"
        "# Root\n\nRead [[Shared]].\n",
        encoding="utf-8",
    )
    for index, page_id in ((1, "shared-a"), (2, "shared-b")):
        path = source / f"{index}_shared.md"
        path.write_text(
            f"---\nid: {page_id}\ntitle: Shared\nsummary: Shared page.\n---\n"
            f"# Shared {index}\n",
            encoding="utf-8",
        )

    report = validate_course(tmp_path)

    assert not report.ok
    assert any(
        diagnostic.message == "Ambiguous wikilink reference"
        and diagnostic.path == root
        and diagnostic.field == "wikilink:Shared"
        and "stable page id" in (diagnostic.next_action or "")
        for diagnostic in report.diagnostics
    )


def test_crlf_fenced_code_does_not_hide_real_numbered_ref_after_fence(
    tmp_path: Path,
) -> None:
    course = _copy_minimal_course(tmp_path)
    index = course / "course" / "0_index.md"
    body = (
        index.read_text(encoding="utf-8")
        + "\r\n\r\n"
        + "```markdown\r\n"
        + "::: theorem {#sample}\r\n"
        + "Fenced sample.\r\n"
        + "```\r\n\r\n"
        + "::: theorem {#real-crlf}\r\n"
        + "Real CRLF theorem.\r\n"
        + ":::\r\n\r\n"
        + "See [real theorem](raya:ref/real-crlf).\r\n"
    )
    index.write_text(body, encoding="utf-8", newline="")

    references = collect_numbered_object_source_references(
        body,
        source_path=index,
    )
    report = validate_course(course)

    assert [reference.id for reference in references] == ["real-crlf"]
    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]


def test_missing_source_directory_fails(tmp_path: Path) -> None:
    (tmp_path / "raya.yaml").write_text(
        "\n".join(
            [
                "course_id: invalid-course",
                "title: Invalid",
                "description: Missing source",
                "language: en",
                "source: course",
                "artifact: artifact",
                "calendar:",
                "  timezone: America/Mexico_City",
            ]
        ),
        encoding="utf-8",
    )

    report = validate_course(tmp_path)
    assert not report.ok
    assert any(
        "authored source directory is missing" in item.message
        for item in report.diagnostics
    )


def test_content_configuration_field_fails(tmp_path: Path) -> None:
    (tmp_path / "raya.yaml").write_text(
        "\n".join(
            [
                "course_id: invalid-course",
                "title: Invalid",
                "description: Unsupported content field",
                "language: en",
                "source: course",
                "content: content",
                "artifact: artifact",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "course").mkdir()

    report = validate_course(tmp_path)

    assert not report.ok
    assert any(
        item.field == "content" and "Unsupported course configuration field" in item.message
        for item in report.diagnostics
    )


def test_root_assets_configuration_field_fails(tmp_path: Path) -> None:
    (tmp_path / "raya.yaml").write_text(
        "\n".join(
            [
                "course_id: invalid-course",
                "title: Invalid",
                "description: Unsupported assets field",
                "language: en",
                "source: course",
                "artifact: artifact",
                "assets: assets",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "course").mkdir()

    report = validate_course(tmp_path)

    assert not report.ok
    assert any(
        item.field == "assets" and "Unsupported course configuration field" in item.message
        for item in report.diagnostics
    )


def test_root_code_configuration_field_fails(tmp_path: Path) -> None:
    (tmp_path / "raya.yaml").write_text(
        "\n".join(
            [
                "course_id: invalid-course",
                "title: Invalid",
                "description: Unsupported code field",
                "language: en",
                "source: course",
                "artifact: artifact",
                "code: code",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "course").mkdir()

    report = validate_course(tmp_path)

    assert not report.ok
    assert any(
        item.field == "code" and "Unsupported course configuration field" in item.message
        for item in report.diagnostics
    )


def test_root_runtime_configuration_field_fails(tmp_path: Path) -> None:
    (tmp_path / "raya.yaml").write_text(
        "\n".join(
            [
                "course_id: invalid-course",
                "title: Invalid",
                "description: Unsupported runtime field",
                "language: en",
                "source: course",
                "artifact: artifact",
                "runtime: runtime",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "course").mkdir()

    report = validate_course(tmp_path)

    assert not report.ok
    assert any(
        item.field == "runtime" and "Unsupported course configuration field" in item.message
        for item in report.diagnostics
    )


def test_runtime_fixture_validates_and_reads_metadata() -> None:
    report = validate_course(RUNTIME_FIXTURE)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert RUNTIME_FIXTURE / "runtime" / "profiles.yaml" in report.files_read
    assert RUNTIME_FIXTURE / "pyproject.toml" in report.files_read
    assert RUNTIME_FIXTURE / "uv.lock" in report.files_read
    assert RUNTIME_FIXTURE / "course" / "code" / "runtime_task.py" in report.files_read


def test_unsupported_runtime_manager_fails() -> None:
    report = validate_course(INVALID_UNSUPPORTED_RUNTIME)

    assert not report.ok
    assert any("Unsupported runtime manager" in item.message for item in report.diagnostics)


def test_missing_runtime_lockfile_fails() -> None:
    report = validate_course(INVALID_MISSING_RUNTIME_LOCKFILE)

    assert not report.ok
    assert any("Missing runtime lockfile" in item.message for item in report.diagnostics)


def test_escaping_runtime_input_fails() -> None:
    report = validate_course(INVALID_ESCAPING_RUNTIME_INPUT)

    assert not report.ok
    assert any("Runtime path escapes course root" in item.message for item in report.diagnostics)


def test_unsafe_runtime_default_fails() -> None:
    report = validate_course(INVALID_UNSAFE_RUNTIME_DEFAULT)

    assert not report.ok
    assert any("Unsafe default execution policy" in item.message for item in report.diagnostics)


def test_unreadable_frontmatter_fails(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    source.mkdir()
    (source / "0_index.md").write_text("---\ntitle: [broken\n---\n# Broken\n", encoding="utf-8")

    report = validate_course(tmp_path)
    assert not report.ok
    assert any("frontmatter" in item.message for item in report.diagnostics)


def test_duplicate_quantum_ids_fail(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    source.mkdir()
    for name in ("0_index.md", "1_other.md"):
        (source / name).write_text(
            "---\nid: duplicate\ntitle: Page\nsummary: Duplicate ID page.\n---\n# Page\n",
            encoding="utf-8",
        )

    report = validate_course(tmp_path)
    assert not report.ok
    assert any("Duplicate quantum ID" in item.message for item in report.diagnostics)


def test_local_markdown_content_link_validates(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    source.mkdir()
    (source / "0_index.md").write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n# Root\n\nContinue to [Topic](1_topic.md).\n",
        encoding="utf-8",
    )
    target = source / "1_topic.md"
    target.write_text(
        "---\nid: topic\ntitle: Topic\nsummary: Topic page.\n---\n# Topic\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert target in report.files_read


def test_broken_local_markdown_content_link_fails(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    source_dir = tmp_path / "course"
    source_dir.mkdir()
    source = source_dir / "0_index.md"
    source.write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n# Root\n\nContinue to [Missing](missing.md).\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)

    assert not report.ok
    diagnostic = next(
        item for item in report.diagnostics if item.message == "Broken local content link"
    )
    assert diagnostic.path == source
    assert diagnostic.field == "link:missing.md"
    assert diagnostic.next_action and "Create" in diagnostic.next_action


def test_markdown_links_inside_fenced_code_are_not_validated(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    source.mkdir()
    (source / "0_index.md").write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n# Root\n\n"
        "```markdown\n"
        "Example [Missing](missing.md) and [Stable](raya:missing-id).\n"
        "```\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]


@pytest.mark.parametrize(
    "fenced_markdown",
    [
        "```markdown\nSee [sample theorem](raya:ref/sample).\n```\n",
        "- ```markdown\n  See [sample theorem](raya:ref/sample).\n  ```\n",
        "> ```markdown\n> See [sample theorem](raya:ref/sample).\n> ```\n",
    ],
)
def test_explicit_numbered_refs_inside_fenced_code_are_not_validated(
    tmp_path: Path,
    fenced_markdown: str,
) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    source.mkdir()
    (source / "0_index.md").write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n# Root\n\n"
        + fenced_markdown,
        encoding="utf-8",
    )

    report = validate_course(tmp_path)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]


def test_root_colocated_asset_reference_validates_and_reads_asset(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    asset = source / "_assets" / "diagram.txt"
    asset.parent.mkdir(parents=True)
    asset.write_text("asset fixture", encoding="utf-8")
    source.mkdir(exist_ok=True)
    (source / "0_index.md").write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n# Root\n\nUse [diagram](_assets/diagram.txt).\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert asset in report.files_read


def test_missing_local_asset_reference_fails(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    source_dir = tmp_path / "course"
    source_dir.mkdir()
    source = source_dir / "0_index.md"
    source.write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n# Root\n\nUse [diagram](_assets/missing.txt).\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)

    assert not report.ok
    diagnostic = next(
        item for item in report.diagnostics if item.message == "Missing local asset reference"
    )
    assert diagnostic.path == source
    assert diagnostic.field == "link:_assets/missing.txt"
    assert diagnostic.next_action and "_assets/" in diagnostic.next_action


def test_colocated_asset_reference_validates_and_reads_asset(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    asset = source / "_assets" / "diagram.txt"
    asset.parent.mkdir(parents=True)
    asset.write_text("colocated asset fixture", encoding="utf-8")
    source.mkdir(exist_ok=True)
    (source / "0_index.md").write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n# Root\n\nUse [diagram](_assets/diagram.txt).\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert asset in report.files_read


def test_non_asset_support_link_fails(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    source.mkdir()
    blocked = source / "_official" / "cards" / "1_card.yaml"
    blocked.parent.mkdir(parents=True)
    blocked.write_text(
        "id: card\ntype: card\nauthority: official\nscope:\n  quantum: root\ncontent:\n  front: Q\n  back: A\n",
        encoding="utf-8",
    )
    page = source / "0_index.md"
    page.write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n# Root\n\nDo not link [private](_official/cards/1_card.yaml).\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)

    assert not report.ok
    assert any(
        "non-asset support material" in item.message for item in report.diagnostics
    )


def test_code_and_notebook_reference_fixture_validates_and_reads_files() -> None:
    report = validate_course(REFERENCE_FIXTURE)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert REFERENCE_FIXTURE / "course" / "code" / "shared_helper.py" in report.files_read
    assert (
        REFERENCE_FIXTURE / "course" / "notebooks" / "overview.ipynb"
        in report.files_read
    )
    assert (
        REFERENCE_FIXTURE / "course" / "1_analysis" / "scripts" / "clean_data.py"
        in report.files_read
    )
    assert (
        REFERENCE_FIXTURE
        / "course"
        / "1_analysis"
        / "labs"
        / "exploration.ipynb"
        in report.files_read
    )


def test_extension_based_code_and_notebook_references_validate(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    script = source / "scripts" / "clean.py"
    notebook = source / "labs" / "explore.ipynb"
    script.parent.mkdir(parents=True)
    notebook.parent.mkdir(parents=True)
    script.write_text("def clean() -> str:\n    return 'ok'\n", encoding="utf-8")
    _write_notebook(notebook, title="Exploration")
    source.mkdir(exist_ok=True)
    (source / "0_index.md").write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n# Root\n\n"
        "Use the [script](scripts/clean.py) and [notebook](labs/explore.ipynb).\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert script in report.files_read
    assert notebook in report.files_read


def test_code_and_notebook_folder_names_remain_valid_when_owned(
    tmp_path: Path,
) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    script = source / "code" / "helper.py"
    notebook = source / "notebooks" / "overview.ipynb"
    script.parent.mkdir(parents=True)
    notebook.parent.mkdir(parents=True)
    script.write_text("VALUE = 1\n", encoding="utf-8")
    _write_notebook(notebook, title="Overview")
    source.mkdir(exist_ok=True)
    (source / "0_index.md").write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n# Root\n\n"
        "Use the [helper](code/helper.py) and [overview](notebooks/overview.ipynb).\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert script in report.files_read
    assert notebook in report.files_read


def test_ancestor_code_reference_validates(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    shared = source / "shared" / "helper.py"
    topic = source / "1_topic"
    shared.parent.mkdir(parents=True)
    topic.mkdir(parents=True)
    shared.write_text("def shared() -> str:\n    return 'ancestor'\n", encoding="utf-8")
    (source / "0_index.md").write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n# Root\n",
        encoding="utf-8",
    )
    (topic / "0_index.md").write_text(
        "---\nid: topic\ntitle: Topic\nsummary: Topic page.\n---\n# Topic\n\n"
        "Use the ancestor [helper](../shared/helper.py).\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert shared in report.files_read


def test_missing_code_reference_fixture_fails() -> None:
    report = validate_course(ROOT / "examples" / "courses" / "invalid" / "missing-code-reference")

    assert not report.ok
    assert any(
        item.message == "Missing local code reference"
        and item.field == "link:scripts/missing.py"
        for item in report.diagnostics
    )


def test_malformed_notebook_reference_fixture_fails() -> None:
    report = validate_course(
        ROOT / "examples" / "courses" / "invalid" / "malformed-notebook-reference"
    )

    assert not report.ok
    assert any(
        item.message == "Unreadable notebook reference"
        and item.field == "link:labs/bad.ipynb"
        for item in report.diagnostics
    )


def test_descendant_quantum_code_reference_fails(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    topic = source / "1_topic"
    script = topic / "scripts" / "owned.py"
    script.parent.mkdir(parents=True)
    script.write_text("VALUE = 'descendant'\n", encoding="utf-8")
    (source / "0_index.md").write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n# Root\n\n"
        "Do not reach into a descendant [script](1_topic/scripts/owned.py).\n",
        encoding="utf-8",
    )
    (topic / "0_index.md").write_text(
        "---\nid: topic\ntitle: Topic\nsummary: Topic page.\n---\n# Topic\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)

    assert not report.ok
    assert any(
        item.message == "Local code reference crosses a learning quantum boundary"
        for item in report.diagnostics
    )


def test_escaping_code_reference_fails(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    outside = tmp_path / "outside.py"
    outside.write_text("VALUE = 'outside'\n", encoding="utf-8")
    source = tmp_path / "course"
    source.mkdir()
    (source / "0_index.md").write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n# Root\n\n"
        "Do not escape to [outside](../outside.py).\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)

    assert not report.ok
    assert any(
        item.message == "Local code reference escapes the authored source tree"
        for item in report.diagnostics
    )


@pytest.mark.parametrize(
    "target",
    [
        "_official/private.py",
        "_reviewed/execution/private/private.py",
        "_assets/private.py",
        "_drafts/private.py",
        "drafts/private.py",
        "_partials/private.py",
        "runtime/private.py",
    ],
)
def test_private_code_reference_paths_fail(tmp_path: Path, target: str) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    private_file = source / target
    private_file.parent.mkdir(parents=True)
    private_file.write_text("VALUE = 'private'\n", encoding="utf-8")
    source.mkdir(exist_ok=True)
    (source / "0_index.md").write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n# Root\n\n"
        f"Do not link [private]({target}).\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)

    assert not report.ok
    assert any(
        item.message == "Local code reference points to private support material"
        and item.field == f"link:{target}"
        for item in report.diagnostics
    )


def test_cross_quantum_code_reference_fixture_fails() -> None:
    report = validate_course(
        ROOT / "examples" / "courses" / "invalid" / "cross-quantum-code-reference"
    )

    assert not report.ok
    assert any(
        item.message == "Local code reference crosses a learning quantum boundary"
        for item in report.diagnostics
    )


def test_external_urls_and_fragment_only_links_are_ignored(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    source.mkdir()
    (source / "0_index.md").write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n# Root\n\n"
        "[Web](https://example.com/missing.md), "
        "[Mail](mailto:test@example.com), "
        "[Phone](tel:123), "
        "[Fragment](#local).\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]


def test_duplicate_official_object_ids_fail(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    source.mkdir()
    (source / "0_index.md").write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n# Root\n",
        encoding="utf-8",
    )
    official = source / "_official" / "cards"
    official.mkdir(parents=True)
    object_text = (
        "id: duplicate-card\n"
        "type: card\n"
        "authority: official\n"
        "scope:\n"
        "  quantum: root\n"
        "content:\n"
        "  front: Question\n"
        "  back: Answer\n"
    )
    (official / "1_first.yaml").write_text(object_text, encoding="utf-8")
    (official / "2_second.yaml").write_text(object_text, encoding="utf-8")

    report = validate_course(tmp_path)
    assert not report.ok
    assert any("Duplicate official learning object ID" in item.message for item in report.diagnostics)


def test_official_object_requires_official_authority(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    source.mkdir()
    (source / "0_index.md").write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n# Root\n",
        encoding="utf-8",
    )
    official = source / "_official" / "cards"
    official.mkdir(parents=True)
    (official / "1_generated.yaml").write_text(
        "id: generated-card\n"
        "type: card\n"
        "authority: generated\n"
        "scope:\n"
        "  quantum: root\n"
        "content:\n"
        "  front: Question\n"
        "  back: Answer\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)
    assert not report.ok
    assert any("official" in item.message for item in report.diagnostics)


def test_official_object_unknown_scope_fails(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    source.mkdir()
    (source / "0_index.md").write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n# Root\n",
        encoding="utf-8",
    )
    official = source / "_official" / "cards"
    official.mkdir(parents=True)
    (official / "1_bad_scope.yaml").write_text(
        "id: bad-scope\n"
        "type: card\n"
        "authority: official\n"
        "scope:\n"
        "  quantum: missing\n"
        "content:\n"
        "  front: Question\n"
        "  back: Answer\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)
    assert not report.ok
    assert any("unknown quantum scope" in item.message for item in report.diagnostics)


def test_colocated_official_object_infers_scope(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    source = tmp_path / "course"
    topic = source / "1_topic"
    official = topic / "_official" / "cards"
    official.mkdir(parents=True)
    source.mkdir(exist_ok=True)
    (source / "0_index.md").write_text(
        "---\nid: root\ntitle: Root\nsummary: Root page.\n---\n# Root\n",
        encoding="utf-8",
    )
    (topic / "0_index.md").write_text(
        "---\nid: topic\ntitle: Topic\nsummary: Topic page.\n---\n# Topic\n",
        encoding="utf-8",
    )
    (official / "1_topic_card.yaml").write_text(
        "id: topic-card\n"
        "type: card\n"
        "authority: official\n"
        "content:\n"
        "  front: Question\n"
        "  back: Answer\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]


def _write_valid_config(path: Path) -> None:
    path.joinpath("raya.yaml").write_text(
        "\n".join(
            [
                "course_id: test-course",
                "title: Test Course",
                "description: Test fixture",
                "language: en",
                "source: course",
                "artifact: artifact",
                "calendar:",
                "  timezone: America/Mexico_City",
            ]
        ),
        encoding="utf-8",
    )


def _copy_minimal_course(tmp_path: Path) -> Path:
    destination = tmp_path / "minimal"
    shutil.copytree(MINIMAL, destination)
    return destination


def _set_calendar_timezone(course: Path, timezone: str) -> None:
    config_path = course / "raya.yaml"
    config_text = config_path.read_text(encoding="utf-8")
    calendar_block = "calendar:\n"
    if calendar_block in config_text:
        before, after = config_text.split(calendar_block, maxsplit=1)
        _, remaining = after.split("\n", maxsplit=1)
        config_text = before + remaining
    config_path.write_text(
        config_text.rstrip()
        + "\ncalendar:\n"
        + f"  timezone: {timezone!r}\n",
        encoding="utf-8",
    )


def _write_calendar_document(
    course: Path,
    filename: str,
    *,
    events: list[dict[str, str]],
    document_id: str = "term",
) -> Path:
    calendar_path = course / "course" / "_official" / "calendar" / filename
    calendar_path.parent.mkdir(parents=True, exist_ok=True)
    event_lines = []
    for event in events:
        event_lines.append(
            "  - " + "\n    ".join(f"{key}: {value!r}" for key, value in event.items())
        )
    calendar_path.write_text(
        "id: " + document_id + "\n"
        "type: calendar\n"
        "authority: official\n"
        "scope:\n"
        "  quantum: course-root\n"
        "events:\n"
        + "\n".join(event_lines)
        + "\n",
        encoding="utf-8",
    )
    return calendar_path


def _session_event() -> dict[str, str]:
    return {
        "id": "session-01",
        "kind": "session",
        "date": "2026-08-10",
        "start_time": "16:00",
        "end_time": "18:00",
        "title": "Opening session",
        "page": "course-root",
    }


def _write_assignment(course: Path, *, content_line: str) -> Path:
    assignment_path = course / "course" / "_official" / "assignments" / "1_assignment.yaml"
    assignment_path.parent.mkdir(parents=True, exist_ok=True)
    assignment_path.write_text(
        "id: course-assignment\n"
        "type: assignment\n"
        "authority: official\n"
        "scope:\n"
        "  quantum: course-root\n"
        "content:\n"
        "  title: Course assignment\n"
        + content_line
        + "\n",
        encoding="utf-8",
    )
    return assignment_path


def _discover_official_objects_for_test(course: Path) -> list[dict[str, object]]:
    config = load_yaml_file(course / "raya.yaml")
    assert isinstance(config, dict)
    source_dir = course / "course"
    report = ValidationReport(context="test")
    content_model = resolve_course_content(
        course_root=course,
        content_dir=source_dir,
        course_id=str(config["course_id"]),
        config=config,
        report=report,
    )
    objects = discover_official_objects(
        course_root=course,
        course_id=str(config["course_id"]),
        source_dir=source_dir,
        content_model=content_model,
        report=report,
    )
    assert report.ok, [item.format() for item in report.diagnostics]
    return objects


def _write_notebook(path: Path, *, title: str) -> None:
    path.write_text(
        (
            "{\n"
            '  "cells": [\n'
            "    {\n"
            '      "cell_type": "markdown",\n'
            '      "metadata": {},\n'
            f'      "source": ["# {title}\\n"]\n'
            "    }\n"
            "  ],\n"
            '  "metadata": {},\n'
            '  "nbformat": 4,\n'
            '  "nbformat_minor": 5\n'
            "}\n"
        ),
        encoding="utf-8",
    )
