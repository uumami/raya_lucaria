from __future__ import annotations

import shutil
from pathlib import Path

from raya_schema import (
    inspect_artifact,
    validate_artifact_manifest,
    validate_links_index,
    validate_official_index,
    validate_pages_index,
    validate_quanta_index,
)
from raya_static import build_course


ROOT = Path(__file__).resolve().parents[2]
MINIMAL = ROOT / "examples" / "courses" / "minimal"


def test_valid_artifact_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        """{
  "artifact_version": "0.1",
  "course_id": "minimal-course",
  "course_version_id": "fixture",
  "generated_at": "2026-06-02T00:00:00Z",
  "source_schema_version": "0.1",
  "static_site_root": "site",
  "data": {
    "pages": "data/pages.json",
    "quanta": "data/quanta.json",
    "links": "data/links.json",
    "official": "data/official.json"
  }
}
""",
        encoding="utf-8",
    )

    report = validate_artifact_manifest(manifest)
    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]


def test_invalid_artifact_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")

    report = validate_artifact_manifest(manifest)
    assert not report.ok
    assert any("required" in item.message for item in report.diagnostics)


def test_generated_artifact_indexes_validate(tmp_path: Path) -> None:
    pages = tmp_path / "pages.json"
    pages.write_text(
        '{"course_id":"minimal-course","pages":[{"path":"00_index.md","url":"/","title":"Home","quantum_id":"course-root"}]}',
        encoding="utf-8",
    )
    quanta = tmp_path / "quanta.json"
    quanta.write_text(
        '{"course_id":"minimal-course","quanta":[{"id":"course-root","type":"page","path":"00_index.md"}]}',
        encoding="utf-8",
    )
    links = tmp_path / "links.json"
    links.write_text(
        '{"course_id":"minimal-course","links":[{"from":"course-root","to":"first-topic","kind":"internal"}]}',
        encoding="utf-8",
    )
    official = tmp_path / "official.json"
    official.write_text(
        '{"course_id":"minimal-course","objects":[{"id":"card-1","type":"card","authority":"official","scope":{"quantum":"course-root"},"content":{"front":"Q","back":"A"}}]}',
        encoding="utf-8",
    )

    for report in (
        validate_pages_index(pages),
        validate_quanta_index(quanta),
        validate_links_index(links),
        validate_official_index(official),
    ):
        assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]


def test_inspect_built_artifact_succeeds(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    build_report = build_course(course)
    assert build_report.ok, [diagnostic.format() for diagnostic in build_report.diagnostics]

    report = inspect_artifact(course / "artifact")

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert course / "artifact" / "manifest.json" in report.files_read
    assert course / "artifact" / "data" / "pages.json" in report.files_read
    assert not report.outputs_written
    assert any("Artifact inspection passed" in item.message for item in report.diagnostics)


def test_inspect_artifact_fails_for_missing_required_paths(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact"
    artifact.mkdir()

    report = inspect_artifact(artifact)

    assert not report.ok
    messages = [item.message for item in report.diagnostics]
    assert "Artifact manifest is missing" in messages
    assert "Artifact site directory is missing" in messages
    assert "Artifact data directory is missing" in messages
    assert "Artifact assets directory is missing" in messages


def test_inspect_artifact_fails_for_missing_manifest_declared_index(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    build_report = build_course(course)
    assert build_report.ok, [diagnostic.format() for diagnostic in build_report.diagnostics]
    (course / "artifact" / "data" / "pages.json").unlink()

    report = inspect_artifact(course / "artifact")

    assert not report.ok
    assert any("Artifact data index does not exist" in item.message for item in report.diagnostics)
    assert not report.outputs_written


def _copy_minimal(tmp_path: Path) -> Path:
    course = tmp_path / "course"
    shutil.copytree(MINIMAL, course, ignore=shutil.ignore_patterns("artifact"))
    return course
