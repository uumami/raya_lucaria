"""Tests for metadata extraction."""
import sys
sys.path.insert(0, 'src')

from preprocessing.extract_metadata import (
    parse_frontmatter, extract_components, extract_h1_title,
    extract_all_metadata,
)


def test_parse_frontmatter():
    content = '---\ntitle: "Hello"\ntags: [a, b]\n---\n\n# Body\n'
    fm, body = parse_frontmatter(content)
    assert fm["title"] == "Hello"
    assert fm["tags"] == ["a", "b"]
    assert "# Body" in body


def test_parse_frontmatter_empty():
    fm, body = parse_frontmatter("# No frontmatter\n\nJust text.")
    assert fm == {}
    assert "No frontmatter" in body


def test_extract_components():
    content = (
        ':::homework{id="hw-01" title="Task" due="2026-03-01"}\n'
        'Do this.\n'
        ':::\n\n'
        ':::exercise{title="Practice"}\n'
        'Practice this.\n'
        ':::\n'
    )
    comps = extract_components(content)
    assert len(comps) == 2
    assert comps[0].type == "homework"
    assert comps[0].attrs["id"] == "hw-01"
    assert comps[0].line_number == 1
    assert comps[1].type == "exercise"


def test_extract_components_empty():
    assert extract_components("# Just text\n\nNo components.") == []


def test_extract_h1_title():
    assert extract_h1_title("# Hello World\n\nContent") == "Hello World"
    assert extract_h1_title("No heading here") is None


def test_extract_all_metadata(tmp_content):
    metadata = extract_all_metadata(tmp_content, exclude=["b_libros"])
    assert "01_intro/01_hello.md" in metadata
    assert metadata["01_intro/01_hello.md"]["title"] == "Hello World"
    assert len(metadata["01_intro/02_components.md"]["components"]) == 2
