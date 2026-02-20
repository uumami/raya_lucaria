"""Generate navigation hierarchy tree from content directory."""
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

from preprocessing.logger import get_logger
from preprocessing.utils import (
    title_from_name, get_sort_key, is_excluded, is_wip,
)

log = get_logger()


def build_tree(
    dir_path: Path,
    metadata: Dict[str, Any],
    base_path: Path,
    exclude: List[str],
) -> Optional[Dict[str, Any]]:
    """Recursively build hierarchy tree from a directory."""
    rel_path = str(dir_path.relative_to(base_path))
    name = dir_path.name

    # Skip excluded / WIP
    if is_excluded(name, exclude) or is_wip(name):
        return None

    node = {
        'name': name,
        'path': rel_path if rel_path != '.' else '',
        'type': 'directory',
        'title': title_from_name(name),
        'has_index': False,
        'children': [],
    }

    # Check for index file
    index_path = dir_path / '00_index.md'
    rel_index = str(index_path.relative_to(base_path)) if index_path.exists() else ''
    if rel_index and rel_index in metadata:
        node['has_index'] = True
        node['title'] = metadata[rel_index].get('title', node['title'])

    # Collect children
    children = []
    for item in sorted(dir_path.iterdir(), key=lambda x: get_sort_key(x.name)):
        if item.name.startswith('.'):
            continue
        item_rel = str(item.relative_to(base_path))
        if is_excluded(item_rel, exclude) or is_excluded(item.name, exclude):
            continue
        if is_wip(item.name):
            continue

        if item.is_dir():
            child = build_tree(item, metadata, base_path, exclude)
            if child:
                children.append(child)
        elif item.suffix == '.md' and item.name != '00_index.md':
            file_meta = metadata.get(item_rel, {})
            children.append({
                'name': item.name,
                'path': item_rel,
                'type': 'file',
                'title': file_meta.get('title', title_from_name(item.name)),
                'summary': file_meta.get('summary'),
                'children': [],
            })

    node['children'] = children
    return node


def generate_hierarchy(
    content_dir: Path,
    metadata: Dict[str, Any],
    exclude: List[str],
    verbose: bool = False,
) -> Dict[str, Any]:
    """Generate complete hierarchy tree for content directory."""
    content_path = Path(content_dir)
    if not content_path.exists():
        return {'name': 'root', 'path': '', 'type': 'root', 'title': 'Contenido', 'children': []}

    tree = {
        'name': content_path.name,
        'path': '',
        'type': 'root',
        'title': 'Contenido',
        'children': [],
    }

    for item in sorted(content_path.iterdir(), key=lambda x: get_sort_key(x.name)):
        if item.name.startswith('.'):
            continue
        if is_excluded(item.name, exclude) or is_wip(item.name):
            continue

        if item.is_dir():
            child = build_tree(item, metadata, content_path, exclude)
            if child:
                tree['children'].append(child)
                if verbose:
                    log.debug(f"Added directory: {item.name}")
        elif item.suffix == '.md' and item.name not in ('00_index.md', 'README.md'):
            rel_file = item.name
            file_meta = metadata.get(rel_file, {})
            tree['children'].append({
                'name': item.name,
                'path': rel_file,
                'type': 'file',
                'title': file_meta.get('title', title_from_name(item.name)),
                'summary': file_meta.get('summary'),
                'children': [],
            })
            if verbose:
                log.debug(f"Added file: {item.name}")

    return tree
