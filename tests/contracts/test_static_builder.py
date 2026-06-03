from __future__ import annotations

import json
import shutil
from pathlib import Path

from raya_schema import (
    validate_artifact_manifest,
    validate_links_index,
    validate_official_index,
    validate_pages_index,
    validate_quanta_index,
)
from raya_static import build_course


ROOT = Path(__file__).resolve().parents[2]
MINIMAL = ROOT / "examples" / "courses" / "minimal"


def test_build_minimal_fixture_into_temporary_course(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    artifact = course / "artifact"
    assert (artifact / "site" / "index.html").exists()
    assert (artifact / "site" / "01_unit" / "index.html").exists()
    assert (artifact / "site" / "01_unit" / "01_topic.html").exists()
    assert (artifact / "manifest.json").exists()
    assert (artifact / "data" / "pages.json").exists()
    assert (artifact / "data" / "quanta.json").exists()
    assert (artifact / "data" / "links.json").exists()
    assert (artifact / "data" / "official.json").exists()
    assert (artifact / "assets").is_dir()
    assert artifact / "manifest.json" in report.outputs_written


def test_generated_artifact_contract_validates(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    artifact = course / "artifact"

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    for validation_report in (
        validate_artifact_manifest(artifact / "manifest.json"),
        validate_pages_index(artifact / "data" / "pages.json"),
        validate_quanta_index(artifact / "data" / "quanta.json"),
        validate_links_index(artifact / "data" / "links.json"),
        validate_official_index(artifact / "data" / "official.json"),
    ):
        assert validation_report.ok, [
            diagnostic.format() for diagnostic in validation_report.diagnostics
        ]


def test_generated_html_is_escaped_and_static_linked(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    extra = course / "content" / "02_escape.md"
    extra.write_text(
        "---\n"
        "title: Escaping\n"
        "quantum:\n"
        "  id: escaping\n"
        "  type: page\n"
        "  parent: course-root\n"
        "---\n"
        "# Escaping\n\n"
        "Use <script>alert('x')</script> safely and visit [root](00_index.md).\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    html = (course / "artifact" / "site" / "02_escape.html").read_text(encoding="utf-8")
    assert "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;" in html
    assert 'href="index.html"' in html
    nested = (course / "artifact" / "site" / "01_unit" / "01_topic.html").read_text(
        encoding="utf-8"
    )
    assert 'href="../index.html"' in nested


def test_official_objects_export_without_personal_state(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    official = json.loads(
        (course / "artifact" / "data" / "official.json").read_text(encoding="utf-8")
    )
    objects = official["objects"]
    assert {item["type"] for item in objects} == {"card", "prompt", "quiz"}
    assert all(item["authority"] == "official" for item in objects)
    assert all(item["scope"]["quantum"] == "first-topic" for item in objects)
    forbidden = {"review_history", "confidence", "mastery", "spaced_repetition"}
    assert all(forbidden.isdisjoint(item.keys()) for item in objects)


def test_source_assets_are_copied(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    asset = course / "assets" / "notes" / "diagram.txt"
    asset.parent.mkdir(parents=True)
    asset.write_text("asset fixture", encoding="utf-8")

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    copied = course / "artifact" / "assets" / "notes" / "diagram.txt"
    assert copied.read_text(encoding="utf-8") == "asset fixture"


def test_rebuild_replaces_stale_artifact_output(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    stale = course / "artifact" / "site" / "stale.html"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale", encoding="utf-8")

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert not stale.exists()


def test_build_stops_when_source_validation_fails(tmp_path: Path) -> None:
    (tmp_path / "raya.yaml").write_text(
        "\n".join(
            [
                "course_id: broken-course",
                "title: Broken Course",
                "description: Missing content",
                "language: en",
                "content: content",
                "artifact: artifact",
            ]
        ),
        encoding="utf-8",
    )

    report = build_course(tmp_path)

    assert not report.ok
    assert any("content directory is missing" in item.message for item in report.diagnostics)
    assert not (tmp_path / "artifact" / "manifest.json").exists()


def _copy_minimal(tmp_path: Path) -> Path:
    course = tmp_path / "course"
    shutil.copytree(MINIMAL, course, ignore=shutil.ignore_patterns("artifact"))
    return course
