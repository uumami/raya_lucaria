from __future__ import annotations

from pathlib import Path

from raya_cli.course_init import init_course
from raya_schema import inspect_artifact, validate_course
from raya_static import build_course


def test_init_course_creates_expected_source_tree(tmp_path: Path) -> None:
    course = tmp_path / "intro-course"

    report = init_course(
        course,
        course_id="intro-course",
        title="Intro Course",
        description="Introductory course scaffold.",
    )

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert (course / "raya.yaml").exists()
    assert (course / "course" / "0_index.md").exists()
    assert (course / "course" / "_assets").is_dir()
    assert (course / "course" / "_official").is_dir()
    assert (course / "course" / "_official" / "cards").is_dir()
    assert (course / "course" / "_official" / "quizzes").is_dir()
    assert (course / "course" / "_official" / "prompts").is_dir()
    assert not (course / "assets").exists()
    assert course / "raya.yaml" in report.outputs_written
    assert "source: course" in (course / "raya.yaml").read_text(encoding="utf-8")


def test_initialized_course_validates_builds_and_inspects(tmp_path: Path) -> None:
    course = tmp_path / "course"
    init_report = init_course(course, course_id="test-course", title="Test Course")
    assert init_report.ok, [diagnostic.format() for diagnostic in init_report.diagnostics]

    validate_report = validate_course(course)
    assert validate_report.ok, [
        diagnostic.format() for diagnostic in validate_report.diagnostics
    ]

    build_report = build_course(course)
    assert build_report.ok, [diagnostic.format() for diagnostic in build_report.diagnostics]

    inspect_report = inspect_artifact(course / "artifact")
    assert inspect_report.ok, [
        diagnostic.format() for diagnostic in inspect_report.diagnostics
    ]


def test_init_course_refuses_non_empty_target(tmp_path: Path) -> None:
    target = tmp_path / "existing"
    target.mkdir()
    (target / "notes.txt").write_text("do not overwrite", encoding="utf-8")

    report = init_course(target)

    assert not report.ok
    assert any("not empty" in item.message for item in report.diagnostics)
    assert not (target / "raya.yaml").exists()


def test_init_course_marks_content_as_replaceable_scaffold(tmp_path: Path) -> None:
    course = tmp_path / "course"

    report = init_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    content = (course / "course" / "0_index.md").read_text(encoding="utf-8")
    assert "replaceable scaffold" in content
    assert "official canon" in content
    assert "id: course-root" in content
