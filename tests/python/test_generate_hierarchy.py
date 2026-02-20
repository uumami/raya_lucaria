"""Tests for hierarchy generation."""
import sys
sys.path.insert(0, 'src')

from preprocessing.extract_metadata import extract_all_metadata
from preprocessing.generate_hierarchy import generate_hierarchy


def test_generate_hierarchy(tmp_content):
    metadata = extract_all_metadata(tmp_content, exclude=[])
    hierarchy = generate_hierarchy(tmp_content, metadata, exclude=[])

    assert hierarchy["type"] == "root"
    assert len(hierarchy["children"]) >= 3  # 01_intro, 02_advanced, a_appendix

    # Check ordering
    names = [c["name"] for c in hierarchy["children"]]
    assert names.index("01_intro") < names.index("02_advanced")
    assert names.index("02_advanced") < names.index("a_appendix")


def test_hierarchy_has_index(tmp_content):
    metadata = extract_all_metadata(tmp_content, exclude=[])
    hierarchy = generate_hierarchy(tmp_content, metadata, exclude=[])

    intro = next(c for c in hierarchy["children"] if c["name"] == "01_intro")
    assert intro["has_index"] is True
    assert intro["title"] == "Introduction"


def test_hierarchy_excludes_index_from_children(tmp_content):
    metadata = extract_all_metadata(tmp_content, exclude=[])
    hierarchy = generate_hierarchy(tmp_content, metadata, exclude=[])

    intro = next(c for c in hierarchy["children"] if c["name"] == "01_intro")
    child_names = [c["name"] for c in intro["children"]]
    assert "00_index.md" not in child_names
