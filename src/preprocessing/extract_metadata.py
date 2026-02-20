"""Extract metadata from markdown files.

Extracts YAML frontmatter and :::component markers.
"""
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

import yaml

from preprocessing.logger import get_logger
from preprocessing.utils import (
    title_from_name, get_sort_key, parse_attributes, is_excluded, is_wip,
)
from preprocessing.schemas.metadata import FileMetadata, ComponentData

log = get_logger()

COMPONENT_TYPES = {'homework', 'exercise', 'prompt', 'example', 'exam', 'project', 'quiz', 'embed'}


def parse_frontmatter(content: str) -> tuple:
    """Parse YAML frontmatter from markdown content.

    Returns (frontmatter_dict, remaining_content).
    """
    if not content.startswith('---'):
        return {}, content

    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return {}, content

    try:
        frontmatter = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        frontmatter = {}

    return frontmatter, content[match.end():]


def extract_components(content: str) -> List[ComponentData]:
    """Extract :::component blocks from markdown content.

    Tracks line numbers for validation error reporting.
    """
    components = []
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        # Match opening :::type{attrs}
        match = re.match(r'^:::(\w+)(?:\{([^}]*)\})?\s*$', line)
        if match and match.group(1) in COMPONENT_TYPES:
            comp_type = match.group(1)
            attrs_str = match.group(2) or ''
            attrs = parse_attributes(attrs_str)
            line_number = i + 1
            # Collect body until closing :::
            body_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() != ':::':
                body_lines.append(lines[i])
                i += 1
            body = '\n'.join(body_lines).strip()
            components.append(ComponentData(
                type=comp_type,
                attrs=attrs,
                content_preview=body[:200] if body else '',
                line_number=line_number,
            ))
        i += 1
    return components


def extract_h1_title(content: str) -> Optional[str]:
    """Extract first H1 header from markdown content."""
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    return match.group(1).strip() if match else None


def get_order_from_name(name: str) -> int:
    """Extract sort order number from filename."""
    match = re.match(r'^(\d+)', name)
    if match:
        return int(match.group(1))
    match = re.match(r'^([a-z])_', name, re.IGNORECASE)
    if match:
        return 100 + ord(match.group(1).upper()) - ord('A')
    return 999


def extract_file_metadata(filepath: Path, base_dir: Path) -> Optional[FileMetadata]:
    """Extract metadata from a single markdown file."""
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        log.warning(f"Could not read {filepath}: {e}")
        return None

    frontmatter, body = parse_frontmatter(content)
    components = extract_components(body)

    title = (
        frontmatter.get('title')
        or extract_h1_title(body)
        or title_from_name(filepath.name)
    )

    rel_path = str(filepath.relative_to(base_dir))

    return FileMetadata(
        path=rel_path,
        title=title,
        type=frontmatter.get('type', 'lesson'),
        order=frontmatter.get('order', get_order_from_name(filepath.name)),
        summary=frontmatter.get('summary'),
        tags=frontmatter.get('tags', []),
        components=[c for c in components],
        has_frontmatter=bool(frontmatter),
    )


def extract_all_metadata(
    content_dir: Path,
    exclude: List[str],
    verbose: bool = False,
) -> Dict[str, dict]:
    """Extract metadata from all markdown files.

    Returns dict mapping relative file paths to metadata dicts.
    """
    metadata = {}
    content_path = Path(content_dir)

    if not content_path.exists():
        log.warning(f"Content directory {content_dir} does not exist")
        return metadata

    for filepath in sorted(content_path.rglob('*.md')):
        rel_path = str(filepath.relative_to(content_path))

        if is_excluded(rel_path, exclude):
            if verbose:
                log.debug(f"Skipping excluded: {rel_path}")
            continue

        if is_wip(filepath.name) or any(is_wip(p) for p in filepath.parts):
            if verbose:
                log.debug(f"Skipping WIP: {rel_path}")
            continue

        file_meta = extract_file_metadata(filepath, content_path)
        if file_meta:
            # Convert dataclass to dict for JSON serialization
            metadata[rel_path] = {
                'path': file_meta.path,
                'title': file_meta.title,
                'type': file_meta.type,
                'order': file_meta.order,
                'summary': file_meta.summary,
                'tags': file_meta.tags,
                'components': [
                    {
                        'type': c.type,
                        'attrs': c.attrs,
                        'content_preview': c.content_preview,
                        'line_number': c.line_number,
                    }
                    for c in file_meta.components
                ],
                'has_frontmatter': file_meta.has_frontmatter,
            }
            if verbose:
                log.debug(f"Processed: {rel_path}")

    return metadata
