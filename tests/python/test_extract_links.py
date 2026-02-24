"""Tests for knowledge graph extraction (Primeval Current)."""
import sys
sys.path.insert(0, 'src')

import pytest
from pathlib import Path
from preprocessing.extract_links import (
    strip_code_blocks,
    extract_links_from_file,
    build_url_to_path_map,
    build_wikilink_map,
    build_graph,
)
from preprocessing.extract_metadata import extract_all_metadata
from preprocessing.generate_hierarchy import generate_hierarchy


@pytest.fixture
def graph_content(tmp_path):
    """Create content directory with cross-linked files for graph testing."""
    content = tmp_path / "clase"
    content.mkdir()

    # Root index
    (content / "00_index.md").write_text(
        "---\ntitle: Test Course\n---\n\n# Test Course\n", encoding='utf-8'
    )

    # Chapter 1
    ch1 = content / "01_intro"
    ch1.mkdir()
    (ch1 / "00_index.md").write_text(
        "---\ntitle: Introduction\n---\n\n# Introduction\n", encoding='utf-8'
    )
    (ch1 / "01_bienvenida.md").write_text(
        "---\ntitle: Bienvenida\nsummary: Welcome page\n---\n\n# Bienvenida\n\n"
        "See [advanced topics](../02_avanzado/01_funciones.md) for more.\n\n"
        "Also check [[matematicas]] for math content.\n",
        encoding='utf-8'
    )
    (ch1 / "02_setup.md").write_text(
        "---\ntitle: Setup\n---\n\n# Setup\n\n"
        "Back to [welcome](./01_bienvenida.md).\n\n"
        "External link: [Google](https://google.com)\n\n"
        "Anchor only: [top](#heading)\n\n"
        "Image: ![logo](./logo.png)\n",
        encoding='utf-8'
    )

    # Chapter 2
    ch2 = content / "02_avanzado"
    ch2.mkdir()
    (ch2 / "00_index.md").write_text(
        "---\ntitle: Avanzado\n---\n\n# Avanzado\n", encoding='utf-8'
    )
    (ch2 / "01_funciones.md").write_text(
        "---\ntitle: Funciones\n---\n\n# Funciones\n\n"
        "See [setup](../01_intro/02_setup.md) for installation.\n\n"
        "Also see [[bienvenida|the welcome page]].\n",
        encoding='utf-8'
    )
    (ch2 / "03_matematicas.md").write_text(
        "---\ntitle: Matematicas\n---\n\n# Matematicas\n\n"
        "Check [funciones](./01_funciones.md) for related content.\n",
        encoding='utf-8'
    )

    # Appendix
    appendix = content / "a_apendice"
    appendix.mkdir()
    (appendix / "00_index.md").write_text(
        "---\ntitle: Apendice\n---\n\n# Apendice\n", encoding='utf-8'
    )
    (appendix / "01_ref.md").write_text(
        "---\ntitle: Referencia\n---\n\n# Referencia\n\n"
        "See [bienvenida](../01_intro/01_bienvenida.md).\n",
        encoding='utf-8'
    )

    return content


@pytest.fixture
def graph_metadata(graph_content):
    return extract_all_metadata(graph_content, exclude=[])


@pytest.fixture
def graph_hierarchy(graph_content, graph_metadata):
    return generate_hierarchy(graph_content, graph_metadata, exclude=[])


# --- strip_code_blocks ---

def test_strip_fenced_code():
    content = "before\n```python\n[link](target.md)\n```\nafter"
    result = strip_code_blocks(content)
    assert "[link](target.md)" not in result
    assert "before" in result
    assert "after" in result


def test_strip_inline_code():
    content = "See `[link](target.md)` for details"
    result = strip_code_blocks(content)
    assert "[link](target.md)" not in result
    assert "See" in result


# --- extract_links_from_file ---

def test_extract_markdown_links_md_ext(graph_metadata):
    content = "See [hello](../01_intro/01_bienvenida.md) for more."
    url_to_path = build_url_to_path_map(graph_metadata)
    all_files = set(graph_metadata.keys())

    edges = extract_links_from_file(
        content, "02_avanzado/01_funciones.md", all_files, url_to_path
    )
    assert len(edges) == 1
    assert edges[0] == ("02_avanzado/01_funciones.md", "01_intro/01_bienvenida.md")


def test_extract_markdown_links_dir_style(graph_metadata):
    url_to_path = build_url_to_path_map(graph_metadata)
    all_files = set(graph_metadata.keys())

    content = "See [avanzado](../02_avanzado/01_funciones/) for more."
    edges = extract_links_from_file(
        content, "01_intro/01_bienvenida.md", all_files, url_to_path
    )
    targets = [e[1] for e in edges]
    assert "02_avanzado/01_funciones.md" in targets


def test_extract_wikilinks(graph_metadata):
    url_to_path = build_url_to_path_map(graph_metadata)
    all_files = set(graph_metadata.keys())
    wikilink_map, _ = build_wikilink_map(
        Path("nonexistent"),  # not used for map lookup
        graph_metadata, []
    )

    content = "Check [[matematicas]] and [[bienvenida|welcome page]]."
    edges = extract_links_from_file(
        content, "02_avanzado/01_funciones.md", all_files, url_to_path,
        wikilink_map=wikilink_map
    )
    targets = {e[1] for e in edges}
    assert "02_avanzado/03_matematicas.md" in targets
    assert "01_intro/01_bienvenida.md" in targets


def test_skip_external_links(graph_metadata):
    url_to_path = build_url_to_path_map(graph_metadata)
    all_files = set(graph_metadata.keys())

    content = "[Google](https://google.com) and [HTTP](http://example.com)"
    edges = extract_links_from_file(
        content, "01_intro/01_bienvenida.md", all_files, url_to_path
    )
    assert len(edges) == 0


def test_skip_anchor_only(graph_metadata):
    url_to_path = build_url_to_path_map(graph_metadata)
    all_files = set(graph_metadata.keys())

    content = "See [heading](#some-heading)"
    edges = extract_links_from_file(
        content, "01_intro/01_bienvenida.md", all_files, url_to_path
    )
    assert len(edges) == 0


def test_skip_image_links(graph_metadata):
    url_to_path = build_url_to_path_map(graph_metadata)
    all_files = set(graph_metadata.keys())

    content = "![alt text](./image.png)"
    edges = extract_links_from_file(
        content, "01_intro/01_bienvenida.md", all_files, url_to_path
    )
    assert len(edges) == 0


def test_skip_code_blocks(graph_metadata):
    url_to_path = build_url_to_path_map(graph_metadata)
    all_files = set(graph_metadata.keys())

    content = "```\n[link](../02_avanzado/01_funciones.md)\n```\n\nNormal text."
    edges = extract_links_from_file(
        content, "01_intro/01_bienvenida.md", all_files, url_to_path
    )
    assert len(edges) == 0


# --- build_wikilink_map ---

def test_wikilink_map_by_stem(graph_metadata):
    wikilink_map, _ = build_wikilink_map(Path("."), graph_metadata, [])
    assert "03_matematicas" in wikilink_map
    assert wikilink_map["03_matematicas"]["path"] == "02_avanzado/03_matematicas.md"


def test_wikilink_map_by_stripped(graph_metadata):
    wikilink_map, _ = build_wikilink_map(Path("."), graph_metadata, [])
    assert "matematicas" in wikilink_map
    assert wikilink_map["matematicas"]["path"] == "02_avanzado/03_matematicas.md"


def test_wikilink_map_by_title(graph_metadata):
    wikilink_map, _ = build_wikilink_map(Path("."), graph_metadata, [])
    # Title "Matematicas" should resolve (case-insensitive)
    assert "matematicas" in wikilink_map


def test_wikilink_map_path_qualified(graph_metadata):
    wikilink_map, _ = build_wikilink_map(Path("."), graph_metadata, [])
    assert "02_avanzado/03_matematicas" in wikilink_map
    assert wikilink_map["02_avanzado/03_matematicas"]["path"] == "02_avanzado/03_matematicas.md"


def test_wikilink_map_ambiguous(tmp_path):
    """Multiple files with same stripped name -> ambiguous, not in map."""
    content = tmp_path / "clase"
    content.mkdir()
    ch1 = content / "01_ch"
    ch1.mkdir()
    (ch1 / "01_index_page.md").write_text(
        "---\ntitle: Index Page A\n---\n# A\n", encoding='utf-8'
    )
    ch2 = content / "02_ch"
    ch2.mkdir()
    (ch2 / "02_index_page.md").write_text(
        "---\ntitle: Index Page B\n---\n# B\n", encoding='utf-8'
    )

    metadata = extract_all_metadata(content, exclude=[])
    wikilink_map, ambiguous = build_wikilink_map(content, metadata, [])

    # "index_page" stripped from both -> ambiguous
    assert "index_page" not in wikilink_map or "index_page" in ambiguous


def test_wikilink_with_fragment(graph_metadata):
    """[[page#heading]] should resolve to page-level edge."""
    url_to_path = build_url_to_path_map(graph_metadata)
    all_files = set(graph_metadata.keys())
    wikilink_map, _ = build_wikilink_map(Path("."), graph_metadata, [])

    content = "See [[matematicas#integrales]] for details."
    edges = extract_links_from_file(
        content, "01_intro/01_bienvenida.md", all_files, url_to_path,
        wikilink_map=wikilink_map
    )
    targets = {e[1] for e in edges}
    assert "02_avanzado/03_matematicas.md" in targets


# --- build_graph ---

def test_backlinks_inversion(graph_content, graph_metadata, graph_hierarchy):
    graph_data, _ = build_graph(graph_content, graph_metadata, graph_hierarchy, [])
    backlinks = graph_data['backlinks']

    # 01_bienvenida links to 02_avanzado/01_funciones.md
    # 02_avanzado/01_funciones links to 01_intro/02_setup.md and 01_intro/01_bienvenida.md
    # a_apendice/01_ref links to 01_intro/01_bienvenida.md
    # So bienvenida should have backlinks from funciones and ref
    bl_bienvenida = backlinks.get("01_intro/01_bienvenida.md", [])
    bl_sources = {bl['path'] for bl in bl_bienvenida}
    assert "02_avanzado/01_funciones.md" in bl_sources
    assert "a_apendice/01_ref.md" in bl_sources


def test_backlinks_sorted_by_course_order(graph_content, graph_metadata, graph_hierarchy):
    graph_data, _ = build_graph(graph_content, graph_metadata, graph_hierarchy, [])
    backlinks = graph_data['backlinks']

    bl_bienvenida = backlinks.get("01_intro/01_bienvenida.md", [])
    if len(bl_bienvenida) >= 2:
        # 02_avanzado should come before a_apendice in sort order
        paths = [bl['path'] for bl in bl_bienvenida]
        idx_avanzado = next(i for i, p in enumerate(paths) if '02_avanzado' in p)
        idx_apendice = next(i for i, p in enumerate(paths) if 'a_apendice' in p)
        assert idx_avanzado < idx_apendice


def test_self_links_excluded(graph_metadata):
    url_to_path = build_url_to_path_map(graph_metadata)
    all_files = set(graph_metadata.keys())

    content = "See [myself](./01_bienvenida.md) for more."
    edges = extract_links_from_file(
        content, "01_intro/01_bienvenida.md", all_files, url_to_path
    )
    assert len(edges) == 0


def test_empty_course_no_crash(tmp_path):
    content = tmp_path / "clase"
    content.mkdir()
    (content / "00_index.md").write_text(
        "---\ntitle: Empty\n---\n# Empty\n", encoding='utf-8'
    )

    metadata = extract_all_metadata(content, exclude=[])
    hierarchy = generate_hierarchy(content, metadata, exclude=[])
    graph_data, wikilink_map = build_graph(content, metadata, hierarchy, [])

    assert len(graph_data['edges']) == 0
    assert isinstance(graph_data['backlinks'], dict)
    assert len(graph_data['nodes']) >= 1


def test_graph_nodes_from_metadata(graph_content, graph_metadata, graph_hierarchy):
    graph_data, _ = build_graph(graph_content, graph_metadata, graph_hierarchy, [])
    node_paths = {n['path'] for n in graph_data['nodes']}

    for rel_path in graph_metadata:
        assert rel_path in node_paths


def test_graph_respects_exclude(graph_content, graph_metadata, graph_hierarchy):
    exclude = ['a_apendice']
    metadata_filtered = {k: v for k, v in graph_metadata.items()
                         if 'a_apendice' not in k}
    graph_data, _ = build_graph(
        graph_content, metadata_filtered, graph_hierarchy, exclude
    )
    node_paths = {n['path'] for n in graph_data['nodes']}
    assert not any('a_apendice' in p for p in node_paths)


def test_graph_respects_wip(tmp_path):
    content = tmp_path / "clase"
    content.mkdir()
    (content / "00_index.md").write_text(
        "---\ntitle: Course\n---\n# Course\n", encoding='utf-8'
    )
    wip = content / "??_draft"
    wip.mkdir()
    (wip / "01_page.md").write_text("# Draft\n", encoding='utf-8')

    metadata = extract_all_metadata(content, exclude=[])
    hierarchy = generate_hierarchy(content, metadata, exclude=[])
    graph_data, _ = build_graph(content, metadata, hierarchy, [])

    node_paths = {n['path'] for n in graph_data['nodes']}
    assert not any('??_' in p for p in node_paths)


def test_graph_has_repo_field(graph_content, graph_metadata, graph_hierarchy):
    """Graph data includes repo metadata for future multi-repo support."""
    graph_data, _ = build_graph(
        graph_content, graph_metadata, graph_hierarchy, [], repo_name='test-course'
    )
    assert 'repo' in graph_data
    assert graph_data['repo']['name'] == 'test-course'
    # Node IDs should be namespaced
    for node in graph_data['nodes']:
        assert node['id'].startswith('test-course:')
