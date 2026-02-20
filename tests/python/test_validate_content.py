"""Tests for content validation."""
import sys
sys.path.insert(0, 'src')

from pathlib import Path
from preprocessing.extract_metadata import extract_all_metadata
from preprocessing.validate_content import validate_content


def test_validate_clean_content(tmp_content):
    metadata = extract_all_metadata(tmp_content, exclude=[])
    errors = validate_content(tmp_content, metadata, exclude=[])

    # Should have no ERROR severity items
    error_count = sum(1 for e in errors if e.severity == "ERROR")
    assert error_count == 0


def test_validate_unclosed_component(tmp_path):
    content = tmp_path / "clase"
    content.mkdir()
    (content / "bad.md").write_text(
        '---\ntitle: Bad\n---\n\n'
        ':::homework{id="x" title="X"}\n'
        'Never closed.\n',
        encoding='utf-8'
    )

    metadata = extract_all_metadata(content, exclude=[])
    errors = validate_content(content, metadata, exclude=[])

    unclosed = [e for e in errors if "never closed" in e.message.lower()]
    assert len(unclosed) == 1


def test_validate_duplicate_ids(tmp_path):
    content = tmp_path / "clase"
    content.mkdir()
    (content / "file1.md").write_text(
        ':::homework{id="dup" title="A"}\nX\n:::\n', encoding='utf-8'
    )
    (content / "file2.md").write_text(
        ':::homework{id="dup" title="B"}\nY\n:::\n', encoding='utf-8'
    )

    metadata = extract_all_metadata(content, exclude=[])
    errors = validate_content(content, metadata, exclude=[])

    dup_errors = [e for e in errors if "glitch" in e.message.lower()]
    assert len(dup_errors) == 1


def test_validate_missing_index(tmp_path):
    content = tmp_path / "clase"
    ch = content / "01_chapter"
    ch.mkdir(parents=True)
    (ch / "01_page.md").write_text("# Page\n", encoding='utf-8')

    metadata = extract_all_metadata(content, exclude=[])
    errors = validate_content(content, metadata, exclude=[])

    missing_idx = [e for e in errors if "no 00_index.md" in e.message]
    assert len(missing_idx) == 1
