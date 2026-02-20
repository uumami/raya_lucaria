"""Shared utilities for glintstone preprocessing.

This module is the SINGLE source of truth for:
- Title generation from filenames/dirnames
- Path normalization
- Attribute string parsing
- Sort key generation

Every other module imports from here. No duplication.
"""
import re
from pathlib import Path
from typing import Dict, Tuple


def title_from_name(name: str) -> str:
    """Generate human-readable title from a file or directory name.

    Handles: 00_index -> Index, 01_intro -> Intro, a_stack -> Stack
    """
    # Remove extension
    stem = name.rsplit('.', 1)[0] if '.' in name else name
    # Remove numeric prefix (00_, 01_, etc.)
    clean = re.sub(r'^\d+[_-]?', '', stem)
    # Remove letter prefix (a_, b_, etc.)
    clean = re.sub(r'^[a-zA-Z]_', '', clean)
    # Convert separators to spaces and title-case
    clean = clean.replace('_', ' ').replace('-', ' ')
    result = ' '.join(word.capitalize() for word in clean.split())
    return result or 'Sin titulo'


def get_sort_key(name: str) -> Tuple:
    """Generate sort key tuple for consistent ordering.

    Order: numbered (01_, 02_) -> lettered appendices (a_, b_) -> z_ docs -> other
    """
    # Numbered items: 01_, 02_, etc.
    match = re.match(r'^(\d+)[_-]', name)
    if match:
        return (0, int(match.group(1)), name.lower())

    # z_ prefixed items (documentation) - always last
    if re.match(r'^z_', name, re.IGNORECASE):
        return (3, 0, name.lower())

    # Appendices: a_, b_, etc. (letters, but not z_)
    match = re.match(r'^([a-yA-Y])_', name)
    if match:
        return (1, ord(match.group(1).upper()), name.lower())

    # Everything else
    return (2, 999, name.lower())


def get_nav_number(name: str) -> str:
    """Get navigation number/letter from a name.

    01_intro -> "1", a_stack -> "A", z_docs -> "Z"
    """
    # z_ prefix
    if re.match(r'^z_', name, re.IGNORECASE):
        return 'Z'

    # Letter prefix (a_, b_, etc.)
    match = re.match(r'^([a-zA-Z])_', name)
    if match:
        return match.group(1).upper()

    # Numeric prefix
    match = re.match(r'^(\d+)[_-]', name)
    if match:
        num = int(match.group(1))
        return str(num) if num > 0 else ''

    return ''


def parse_attributes(attr_str: str) -> Dict[str, str]:
    """Parse attribute string like {id="foo" title="bar"} into dict.

    Handles both single and double quotes.
    """
    attrs = {}
    if not attr_str:
        return attrs
    # Remove surrounding braces if present
    attr_str = attr_str.strip()
    if attr_str.startswith('{'):
        attr_str = attr_str[1:]
    if attr_str.endswith('}'):
        attr_str = attr_str[:-1]
    # Match key="value" or key='value'
    for match in re.finditer(r'(\w+)=["\']([^"\']*)["\']', attr_str):
        attrs[match.group(1)] = match.group(2)
    return attrs


def normalize_path(path: str) -> str:
    """Normalize a file path for consistent comparison."""
    return str(Path(path)).replace('\\', '/')


def get_chapter_name(file_path: str) -> str:
    """Extract chapter name from file path."""
    parts = file_path.split('/')
    if len(parts) >= 2:
        return title_from_name(parts[0])
    return 'General'


def is_wip(name: str) -> bool:
    """Check if a file/directory is work-in-progress (??_ prefix)."""
    return name.startswith('??_')


def is_index(name: str) -> bool:
    """Check if a file is an index file."""
    return name == '00_index.md'


def is_excluded(path: str, exclude_patterns: list) -> bool:
    """Check if a path matches any exclusion pattern."""
    for pattern in exclude_patterns:
        if pattern in path:
            return True
    return False
