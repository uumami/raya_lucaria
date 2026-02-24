"""Knowledge graph extraction — Primeval Current.

Extracts links between content pages, builds a knowledge graph with
backlinks, and resolves wikilinks. Designed for single-repo use but
node IDs are namespaced ({repo}:{path}) for future multi-repo merging.

Functions:
    strip_code_blocks  -- remove code blocks before link extraction
    extract_links_from_file -- parse one markdown file for edges
    build_url_to_path_map -- reverse map URL -> file path
    build_wikilink_map -- resolution table for [[wikilinks]]
    build_graph -- main orchestrator, returns (graph_data, wikilink_map)
"""
import os
import re
from pathlib import Path, PurePosixPath
from typing import Dict, List, Tuple, Any, Optional

from preprocessing.logger import get_logger
from preprocessing.utils import (
    is_excluded, is_wip, title_from_name, get_sort_key, get_nav_number,
)

log = get_logger()

# Regex patterns
_MD_LINK_RE = re.compile(r'(?<!!)\[([^\]]*)\]\(([^)]+)\)')
_WIKILINK_RE = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')
_FENCED_CODE_RE = re.compile(r'```[\s\S]*?```', re.DOTALL)
_INLINE_CODE_RE = re.compile(r'`[^`]+`')


def strip_code_blocks(content: str) -> str:
    """Remove fenced code blocks and inline code before link extraction."""
    content = _FENCED_CODE_RE.sub('', content)
    content = _INLINE_CODE_RE.sub('', content)
    return content


def build_url_to_path_map(metadata: Dict[str, Any]) -> Dict[str, str]:
    """Build reverse map: URL path -> file path.

    Handles both /chapter/page/ style URLs and /chapter/00_index/ URLs.
    """
    url_to_path = {}
    for path in metadata:
        # Standard URL: path without .md extension, with leading /
        url = '/' + path.replace('.md', '') + '/'
        url_to_path[url] = path

        # Also map without trailing slash
        url_no_slash = '/' + path.replace('.md', '')
        url_to_path[url_no_slash] = path

    return url_to_path


def build_wikilink_map(
    content_dir: Path,
    metadata: Dict[str, Any],
    exclude: List[str],
) -> Tuple[Dict[str, dict], List[str]]:
    """Build resolution table for [[wikilinks]].

    Returns (resolution_map, ambiguous_list).

    Keys are lowercased for case-insensitive matching. Each value is:
        {"path": str, "url": str, "title": str}

    Resolution priority:
        1. Exact stem: "03_matematicas"
        2. Stripped prefix: "matematicas" (strips NN_ or LL_)
        3. Lowercase title from metadata
        4. Path-qualified: "02_avanzado/03_matematicas"

    Collisions on stripped/title keys -> recorded as ambiguous, not added.
    """
    resolution_map = {}
    ambiguous = []
    # Track collisions for stripped and title keys
    _stripped_seen = {}   # key -> path (first occurrence)
    _title_seen = {}      # key -> path (first occurrence)

    content_path = Path(content_dir)

    for rel_path, meta in metadata.items():
        filepath = content_path / rel_path
        # Skip excluded and WIP
        if is_excluded(rel_path, exclude):
            continue
        if any(is_wip(p) for p in Path(rel_path).parts):
            continue

        stem = Path(rel_path).stem  # e.g., "03_matematicas"
        url = '/' + rel_path.replace('.md', '') + '/'
        title = meta.get('title', title_from_name(stem))

        entry = {'path': rel_path, 'url': url, 'title': title}

        # 1. Exact stem (always unique by definition of file paths)
        exact_key = stem.lower()
        resolution_map[exact_key] = entry

        # 2. Stripped prefix: remove NN_ or LL_ prefix
        stripped = re.sub(r'^\d+[_-]', '', stem)
        stripped = re.sub(r'^[a-zA-Z]_', '', stripped)
        stripped_key = stripped.lower()
        if stripped_key and stripped_key != exact_key:
            if stripped_key in _stripped_seen:
                # Collision — remove from map if present, track as ambiguous
                if stripped_key in resolution_map:
                    del resolution_map[stripped_key]
                if stripped_key not in ambiguous:
                    ambiguous.append(stripped_key)
            else:
                _stripped_seen[stripped_key] = rel_path
                resolution_map[stripped_key] = entry

        # 3. Title key (lowercase)
        title_key = title.lower()
        if title_key and title_key != exact_key and title_key != stripped_key:
            if title_key in _title_seen:
                if title_key in resolution_map:
                    del resolution_map[title_key]
                if title_key not in ambiguous:
                    ambiguous.append(title_key)
            else:
                _title_seen[title_key] = rel_path
                resolution_map[title_key] = entry

        # 4. Path-qualified: "02_avanzado/03_matematicas"
        path_parts = PurePosixPath(rel_path)
        if len(path_parts.parts) >= 2:
            qualified = '/'.join(path_parts.parts[:-1]) + '/' + stem
            qualified_key = qualified.lower()
            resolution_map[qualified_key] = entry

    return resolution_map, ambiguous


def extract_links_from_file(
    content: str,
    file_path: str,
    all_files: set,
    url_to_path: Dict[str, str],
    wikilink_map: Optional[Dict[str, dict]] = None,
) -> List[Tuple[str, str]]:
    """Extract internal link edges from one markdown file.

    Returns list of (source_path, target_path) tuples.
    """
    cleaned = strip_code_blocks(content)
    edges = set()
    current_dir = PurePosixPath(file_path).parent

    # Standard markdown links: [text](target)
    for match in _MD_LINK_RE.finditer(cleaned):
        target = match.group(2).strip()

        # Skip external, anchors, mailto
        if target.startswith(('http://', 'https://', 'mailto:')):
            continue
        if target.startswith('#'):
            continue

        # Strip fragment
        target_no_frag = target.split('#')[0]
        if not target_no_frag:
            continue

        resolved = _resolve_md_target(target_no_frag, current_dir, all_files, url_to_path)
        if resolved and resolved != file_path:
            edges.add((file_path, resolved))

    # Wikilinks: [[target]] and [[target|text]]
    if wikilink_map:
        for match in _WIKILINK_RE.finditer(cleaned):
            raw_target = match.group(1).strip()
            # Strip fragment for edge resolution
            target_key = raw_target.split('#')[0].lower()

            resolved_entry = wikilink_map.get(target_key)
            if resolved_entry and resolved_entry['path'] != file_path:
                edges.add((file_path, resolved_entry['path']))

    return list(edges)


def _normalize_posix_path(path_str: str) -> str:
    """Normalize a POSIX path string, resolving .. and . components."""
    return os.path.normpath(path_str).replace('\\', '/')


def _resolve_md_target(
    target: str,
    current_dir: PurePosixPath,
    all_files: set,
    url_to_path: Dict[str, str],
) -> Optional[str]:
    """Resolve a markdown link target to a file path.

    Handles .md extensions, directory-style URLs, and relative paths.
    """
    # Case 1: Target ends with .md — resolve relative to current file
    if target.endswith('.md'):
        joined = (current_dir / target).as_posix()
        resolved = _normalize_posix_path(joined)
        if resolved in all_files:
            return resolved
        return None

    # Case 2: Directory-style URL (./path/ or ../path/ or /path/)
    clean_target = target.rstrip('/')
    if clean_target.startswith('.'):
        # Relative URL — resolve against current_dir
        joined = (current_dir / clean_target).as_posix()
        clean_target = '/' + _normalize_posix_path(joined)
    elif not clean_target.startswith('/'):
        # Bare relative path
        joined = (current_dir / clean_target).as_posix()
        clean_target = '/' + _normalize_posix_path(joined)

    # Look up with and without trailing slash
    result = url_to_path.get(clean_target + '/')
    if result:
        return result
    result = url_to_path.get(clean_target)
    if result:
        return result

    return None


def _build_display_title(file_path: str, metadata: Dict[str, Any]) -> str:
    """Build hierarchical display title like '1.1 Bienvenida'."""
    parts = PurePosixPath(file_path).parts
    nav_parts = []

    # Build nav number from directory path
    for part in parts[:-1]:  # directories
        num = get_nav_number(part)
        if num:
            nav_parts.append(num)

    # File nav number
    stem = PurePosixPath(file_path).stem
    file_num = get_nav_number(stem)
    if file_num:
        nav_parts.append(file_num)

    prefix = '.'.join(nav_parts)
    meta = metadata.get(file_path, {})
    title = meta.get('title', title_from_name(stem))

    if prefix:
        return f"{prefix} {title}"
    return title


def build_graph(
    content_dir: Path,
    metadata: Dict[str, Any],
    hierarchy: Dict[str, Any],
    exclude: List[str],
    repo_name: str = '',
) -> Tuple[Dict[str, Any], Dict[str, dict]]:
    """Build knowledge graph from content directory.

    Returns (graph_data, wikilink_map).

    graph_data structure:
        {
            "repo": {"name": str, "url": str},
            "nodes": [{"id": str, "path": str, "title": str, "url": str,
                        "chapter": str, "chapter_index": int, "summary": str|None}],
            "edges": [{"source": str, "target": str}],
            "backlinks": {path: [{"path": str, "url": str, "title": str}]}
        }

    Node IDs are namespaced as "{repo}:{path}" for future multi-repo support.
    """
    content_path = Path(content_dir)

    # Build resolution maps
    wikilink_map, ambiguous = build_wikilink_map(content_dir, metadata, exclude)
    url_to_path = build_url_to_path_map(metadata)

    if ambiguous:
        log.warning(f"  Ambiguous wikilink targets: {', '.join(ambiguous)}")

    # Collect all non-excluded, non-WIP file paths
    all_files = set()
    for rel_path in metadata:
        if is_excluded(rel_path, exclude):
            continue
        if any(is_wip(p) for p in Path(rel_path).parts):
            continue
        all_files.add(rel_path)

    # Build nodes
    nodes = []
    # Map chapter dir name -> (chapter_title, chapter_index)
    chapter_map = _build_chapter_map(hierarchy)

    for rel_path in sorted(all_files, key=lambda p: get_sort_key(Path(p).parts[0] if '/' in p else p)):
        meta = metadata[rel_path]
        parts = PurePosixPath(rel_path).parts
        chapter_dir = parts[0] if len(parts) >= 2 else ''
        ch_info = chapter_map.get(chapter_dir, {'title': 'General', 'index': 0})

        node_id = f"{repo_name}:{rel_path}" if repo_name else rel_path

        nodes.append({
            'id': node_id,
            'path': rel_path,
            'title': meta.get('title', title_from_name(Path(rel_path).stem)),
            'url': '/' + rel_path.replace('.md', '') + '/',
            'chapter': ch_info['title'],
            'chapter_index': ch_info['index'],
            'summary': meta.get('summary'),
        })

    # Extract edges from all files
    raw_edges = []
    for rel_path in all_files:
        filepath = content_path / rel_path
        try:
            content = filepath.read_text(encoding='utf-8')
        except Exception:
            continue

        file_edges = extract_links_from_file(
            content, rel_path, all_files, url_to_path, wikilink_map
        )
        raw_edges.extend(file_edges)

    # Deduplicate edges (and remove self-links — already handled in extract_links_from_file)
    edge_set = set()
    edges = []
    for source, target in raw_edges:
        if source == target:
            continue
        key = (source, target)
        if key not in edge_set:
            edge_set.add(key)
            src_id = f"{repo_name}:{source}" if repo_name else source
            tgt_id = f"{repo_name}:{target}" if repo_name else target
            edges.append({'source': src_id, 'target': tgt_id})

    # Build backlinks (inverted edges)
    backlinks = {}
    for source, target in edge_set:
        if target not in backlinks:
            backlinks[target] = []
        backlinks[target].append({
            'path': source,
            'url': '/' + source.replace('.md', '') + '/',
            'title': _build_display_title(source, metadata),
        })

    # Sort backlinks by course order
    for target_path in backlinks:
        backlinks[target_path].sort(
            key=lambda bl: get_sort_key(Path(bl['path']).parts[0] if '/' in bl['path'] else bl['path'])
        )

    graph_data = {
        'repo': {'name': repo_name},
        'nodes': nodes,
        'edges': edges,
        'backlinks': backlinks,
    }

    return graph_data, wikilink_map


def _build_chapter_map(hierarchy: Dict[str, Any]) -> Dict[str, dict]:
    """Extract chapter name -> {title, index} from hierarchy tree."""
    chapter_map = {}
    if not hierarchy or 'children' not in hierarchy:
        return chapter_map

    for i, child in enumerate(hierarchy.get('children', [])):
        if child.get('type') == 'directory':
            chapter_map[child['name']] = {
                'title': child.get('title', title_from_name(child['name'])),
                'index': i,
            }

    return chapter_map
