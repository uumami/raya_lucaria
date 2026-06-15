from __future__ import annotations

import json
import shutil
from pathlib import Path

from raya_schema import (
    inspect_artifact,
    validate_artifact_manifest,
    validate_cache_index,
    validate_execution_index,
    validate_execution_results_index,
    validate_indices_index,
    validate_links_index,
    validate_navigation_index,
    validate_official_index,
    validate_pages_index,
    validate_quanta_index,
    validate_references_index,
    validate_reviewed_outputs_index,
    validate_runtime_index,
)
from raya_static import build_course


ROOT = Path(__file__).resolve().parents[2]
MINIMAL = ROOT / "examples" / "courses" / "minimal"
REFERENCE_FIXTURE = ROOT / "examples" / "courses" / "reference-fixture"
RUNTIME_FIXTURE = ROOT / "examples" / "courses" / "runtime-fixture"
EXECUTION_FIXTURE = ROOT / "examples" / "courses" / "execution-fixture"


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
    "navigation": "data/navigation.json",
    "indices": "data/indices.json",
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


def test_artifact_manifest_rejects_non_string_numbered_objects_data_path(
    tmp_path: Path,
) -> None:
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
    "navigation": "data/navigation.json",
    "indices": "data/indices.json",
    "official": "data/official.json",
    "numbered_objects": []
  }
}
""",
        encoding="utf-8",
    )

    report = validate_artifact_manifest(manifest)

    assert not report.ok
    assert any("data.numbered_objects" in item.field for item in report.diagnostics)


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
    navigation = tmp_path / "navigation.json"
    navigation.write_text(
        '{"course_id":"minimal-course","root":"course-root","items":[{"id":"course-root","path":"0_index.md","url":"index.html","title":"Home","label":"","children":[]}]}',
        encoding="utf-8",
    )
    indices = tmp_path / "indices.json"
    indices.write_text(
        '{"course_id":"minimal-course","local":[{"id":"course-root","entries":[]}],"master":[]}',
        encoding="utf-8",
    )
    references = tmp_path / "references.json"
    references.write_text(
        '{"course_id":"minimal-course","references":[]}',
        encoding="utf-8",
    )
    reviewed_outputs = tmp_path / "reviewed-outputs.json"
    reviewed_outputs.write_text(
        '{"course_id":"minimal-course","authority":"reviewed-course-support","outputs":[]}',
        encoding="utf-8",
    )
    runtime = tmp_path / "runtime.json"
    runtime.write_text(
        '{"course_id":"minimal-course","profiles":[],"defaults":{"policy":"never"}}',
        encoding="utf-8",
    )
    execution = tmp_path / "execution.json"
    execution.write_text(
        '{"course_id":"minimal-course","targets":[]}',
        encoding="utf-8",
    )
    execution_results = tmp_path / "execution-results.json"
    execution_results.write_text(
        '{"course_id":"minimal-course","results":[]}',
        encoding="utf-8",
    )
    cache = tmp_path / "cache.json"
    cache.write_text(
        '{"course_id":"minimal-course","entries":[]}',
        encoding="utf-8",
    )

    for report in (
        validate_pages_index(pages),
        validate_quanta_index(quanta),
        validate_links_index(links),
        validate_navigation_index(navigation),
        validate_indices_index(indices),
        validate_official_index(official),
        validate_references_index(references),
        validate_reviewed_outputs_index(reviewed_outputs),
        validate_runtime_index(runtime),
        validate_execution_index(execution),
        validate_execution_results_index(execution_results),
        validate_cache_index(cache),
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


def test_inspect_reference_artifact_succeeds(tmp_path: Path) -> None:
    course = tmp_path / "reference-fixture"
    shutil.copytree(REFERENCE_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    build_report = build_course(course)
    assert build_report.ok, [diagnostic.format() for diagnostic in build_report.diagnostics]

    report = inspect_artifact(course / "artifact")

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert course / "artifact" / "data" / "references.json" in report.files_read


def test_inspect_runtime_artifact_succeeds(tmp_path: Path) -> None:
    course = tmp_path / "runtime-fixture"
    shutil.copytree(RUNTIME_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    build_report = build_course(course)
    assert build_report.ok, [diagnostic.format() for diagnostic in build_report.diagnostics]

    report = inspect_artifact(course / "artifact")

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert course / "artifact" / "data" / "runtime.json" in report.files_read
    assert course / "artifact" / "data" / "execution.json" in report.files_read
    assert course / "artifact" / "data" / "cache.json" in report.files_read


def test_inspect_reviewed_output_artifact_files(tmp_path: Path) -> None:
    course = tmp_path / "execution-fixture"
    shutil.copytree(EXECUTION_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    build_report = build_course(course)
    assert build_report.ok, [diagnostic.format() for diagnostic in build_report.diagnostics]

    report = inspect_artifact(course / "artifact")

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert course / "artifact" / "data" / "reviewed-outputs.json" in report.files_read


def test_inspect_reviewed_output_artifact_fails_when_file_missing(
    tmp_path: Path,
) -> None:
    course = tmp_path / "execution-fixture"
    shutil.copytree(EXECUTION_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    build_report = build_course(course)
    assert build_report.ok, [diagnostic.format() for diagnostic in build_report.diagnostics]
    (course / "artifact" / "reviewed" / "frozen-script" / "stdout.txt").unlink()

    report = inspect_artifact(course / "artifact")

    assert not report.ok
    assert any(
        item.message == "Referenced artifact file is missing"
        for item in report.diagnostics
    )


def test_inspect_runtime_artifact_rejects_escaping_metadata_path(tmp_path: Path) -> None:
    course = tmp_path / "runtime-fixture"
    shutil.copytree(RUNTIME_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    build_report = build_course(course)
    assert build_report.ok, [diagnostic.format() for diagnostic in build_report.diagnostics]
    cache_path = course / "artifact" / "data" / "cache.json"
    cache_path.write_text(
        cache_path.read_text(encoding="utf-8").replace(
            '"course/_assets/runtime-input.txt"',
            '"../outside.txt"',
        ),
        encoding="utf-8",
    )

    report = inspect_artifact(course / "artifact")

    assert not report.ok
    assert any(
        item.message == "Runtime metadata path must be relative and stay inside course source"
        for item in report.diagnostics
    )


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


def test_inspect_artifact_validates_manifest_declared_numbered_objects_index(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    build_report = build_course(course)
    assert build_report.ok, [diagnostic.format() for diagnostic in build_report.diagnostics]
    artifact = course / "artifact"
    manifest_path = artifact / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["data"]["numbered_objects"] = "data/numbered-objects.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    (artifact / "data" / "numbered-objects.json").write_text(
        '{"version": 2, "objects": [], "by_id": {}}',
        encoding="utf-8",
    )

    report = inspect_artifact(artifact)

    assert not report.ok
    assert any(
        "numbered objects index version must be 1" in item.message
        for item in report.diagnostics
    )


def _copy_minimal(tmp_path: Path) -> Path:
    course = tmp_path / "course"
    shutil.copytree(MINIMAL, course, ignore=shutil.ignore_patterns("artifact"))
    return course
