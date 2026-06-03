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


def test_local_markdown_content_link_validates(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    content = tmp_path / "content"
    content.mkdir()
    (content / "00_index.md").write_text(
        "# Root\n\nContinue to [Topic](01_topic.md).\n",
        encoding="utf-8",
    )
    target = content / "01_topic.md"
    target.write_text("# Topic\n", encoding="utf-8")

    report = validate_course(tmp_path)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert target in report.files_read


def test_broken_local_markdown_content_link_fails(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    content = tmp_path / "content"
    content.mkdir()
    source = content / "00_index.md"
    source.write_text("# Root\n\nContinue to [Missing](missing.md).\n", encoding="utf-8")

    report = validate_course(tmp_path)

    assert not report.ok
    diagnostic = next(
        item for item in report.diagnostics if item.message == "Broken local content link"
    )
    assert diagnostic.path == source
    assert diagnostic.field == "link:missing.md"
    assert diagnostic.next_action and "Create" in diagnostic.next_action


def test_local_asset_reference_validates_and_reads_asset(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    content = tmp_path / "content"
    content.mkdir()
    asset = tmp_path / "assets" / "diagram.txt"
    asset.parent.mkdir()
    asset.write_text("asset fixture", encoding="utf-8")
    (content / "00_index.md").write_text(
        "# Root\n\nUse [diagram](../assets/diagram.txt).\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert asset in report.files_read


def test_missing_local_asset_reference_fails(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    content = tmp_path / "content"
    content.mkdir()
    source = content / "00_index.md"
    source.write_text(
        "# Root\n\nUse [diagram](../assets/missing.txt).\n",
        encoding="utf-8",
    )

    report = validate_course(tmp_path)

    assert not report.ok
    diagnostic = next(
        item for item in report.diagnostics if item.message == "Missing local asset reference"
    )
    assert diagnostic.path == source
    assert diagnostic.field == "link:../assets/missing.txt"
    assert diagnostic.next_action and "asset under assets/" in diagnostic.next_action


def test_external_urls_and_fragment_only_links_are_ignored(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    content = tmp_path / "content"
    content.mkdir()
    (content / "00_index.md").write_text(
        "# Root\n\n"
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
