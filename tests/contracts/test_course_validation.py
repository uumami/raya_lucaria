from __future__ import annotations

from pathlib import Path

import pytest

from raya_schema import validate_course


ROOT = Path(__file__).resolve().parents[2]
MINIMAL = ROOT / "examples" / "courses" / "minimal"


def test_minimal_fixture_validates() -> None:
    report = validate_course(MINIMAL)
    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert MINIMAL / "raya.yaml" in report.files_read


def test_missing_content_directory_fails(tmp_path: Path) -> None:
    (tmp_path / "raya.yaml").write_text(
        "\n".join(
            [
                "course_id: invalid-course",
                "title: Invalid",
                "description: Missing content",
                "language: en",
                "content: content",
                "artifact: artifact",
            ]
        ),
        encoding="utf-8",
    )

    report = validate_course(tmp_path)
    assert not report.ok
    assert any("content directory is missing" in item.message for item in report.diagnostics)


def test_unreadable_frontmatter_fails(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    content = tmp_path / "content"
    content.mkdir()
    (content / "00_index.md").write_text("---\ntitle: [broken\n---\n# Broken\n", encoding="utf-8")

    report = validate_course(tmp_path)
    assert not report.ok
    assert any("frontmatter" in item.message for item in report.diagnostics)


def test_duplicate_quantum_ids_fail(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    content = tmp_path / "content"
    content.mkdir()
    for name in ("00_index.md", "01_other.md"):
        (content / name).write_text(
            "---\nquantum:\n  id: duplicate\n  type: page\n---\n# Page\n",
            encoding="utf-8",
        )

    report = validate_course(tmp_path)
    assert not report.ok
    assert any("Duplicate quantum ID" in item.message for item in report.diagnostics)


def test_duplicate_official_object_ids_fail(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    content = tmp_path / "content"
    content.mkdir()
    (content / "00_index.md").write_text("# Root\n", encoding="utf-8")
    official = tmp_path / "official" / "cards"
    official.mkdir(parents=True)
    object_text = (
        "id: duplicate-card\n"
        "type: card\n"
        "authority: official\n"
        "scope:\n"
        "  quantum: 00_index.md\n"
        "content:\n"
        "  front: Question\n"
        "  back: Answer\n"
    )
    (official / "a.yaml").write_text(object_text, encoding="utf-8")
    (official / "b.yaml").write_text(object_text, encoding="utf-8")

    report = validate_course(tmp_path)
    assert not report.ok
    assert any("Duplicate official learning object ID" in item.message for item in report.diagnostics)


def test_official_object_requires_official_authority(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    content = tmp_path / "content"
    content.mkdir()
    (content / "00_index.md").write_text("# Root\n", encoding="utf-8")
    official = tmp_path / "official" / "cards"
    official.mkdir(parents=True)
    (official / "generated.yaml").write_text(
        "id: generated-card\n"
        "type: card\n"
        "authority: generated\n"
        "scope:\n"
        "  quantum: 00_index.md\n"
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
    content = tmp_path / "content"
    content.mkdir()
    (content / "00_index.md").write_text("# Root\n", encoding="utf-8")
    official = tmp_path / "official" / "cards"
    official.mkdir(parents=True)
    (official / "bad-scope.yaml").write_text(
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


def _write_valid_config(path: Path) -> None:
    path.joinpath("raya.yaml").write_text(
        "\n".join(
            [
                "course_id: test-course",
                "title: Test Course",
                "description: Test fixture",
                "language: en",
                "content: content",
                "artifact: artifact",
            ]
        ),
        encoding="utf-8",
    )
