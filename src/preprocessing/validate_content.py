"""Content validation with file:line error reporting.

Checks:
- Missing 00_index.md in directories
- Unclosed :::component blocks
- Duplicate component IDs
- Broken internal links (.md references)
- Missing referenced images
- Invalid date formats
- Numbering gaps in directory prefixes
"""
import re
from pathlib import Path
from typing import Dict, List, Any

from preprocessing.logger import get_logger
from preprocessing.utils import is_excluded, is_wip, parse_attributes

log = get_logger()

COMPONENT_TYPES = {'homework', 'exercise', 'prompt', 'example', 'exam', 'project', 'quiz', 'embed'}


class ValidationError:
    """A single validation finding."""
    def __init__(self, file: str, line: int, severity: str, message: str):
        self.file = file
        self.line = line
        self.severity = severity  # ERROR, WARNING
        self.message = message

    def __str__(self):
        return f"{self.file}:{self.line}: {self.severity}: {self.message}"


def validate_content(
    content_dir: Path,
    metadata: Dict[str, Any],
    exclude: List[str],
    verbose: bool = False,
) -> List[ValidationError]:
    """Run all validation checks on content directory."""
    errors = []
    content_path = Path(content_dir)

    if not content_path.exists():
        return errors

    all_md_files = set()
    all_images = set()
    component_ids = {}  # id -> file_path

    # Collect all files
    for f in content_path.rglob('*.md'):
        rel = str(f.relative_to(content_path))
        if not is_excluded(rel, exclude) and not any(is_wip(p) for p in f.parts):
            all_md_files.add(rel)

    for f in content_path.rglob('*'):
        if f.suffix.lower() in ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'):
            all_images.add(str(f.relative_to(content_path)))

    # Check 1: Missing index files
    for d in content_path.rglob('*'):
        if d.is_dir() and not d.name.startswith('.'):
            rel_d = str(d.relative_to(content_path))
            if is_excluded(rel_d, exclude) or is_excluded(d.name, exclude):
                continue
            if is_wip(d.name):
                continue
            # Check for any .md files in this directory
            has_md = any(f.suffix == '.md' for f in d.iterdir() if f.is_file())
            if has_md and not (d / '00_index.md').exists():
                errors.append(ValidationError(
                    rel_d, 0, 'WARNING',
                    f"Foolish Tarnished -- directory '{d.name}' has no 00_index.md"
                ))

    # Check 2-5: Per-file checks
    for rel_path in sorted(all_md_files):
        filepath = content_path / rel_path
        try:
            content = filepath.read_text(encoding='utf-8')
        except Exception:
            continue

        lines = content.split('\n')

        # Check 2: Unclosed component blocks
        open_stack = []
        for i, line in enumerate(lines, 1):
            open_match = re.match(r'^:::(\w+)(?:\{[^}]*\})?\s*$', line)
            if open_match and open_match.group(1) in COMPONENT_TYPES:
                open_stack.append((open_match.group(1), i))
            elif line.strip() == ':::' and open_stack:
                open_stack.pop()

        for comp_type, line_num in open_stack:
            errors.append(ValidationError(
                rel_path, line_num, 'ERROR',
                f"Sorcery interrupted -- ':::{comp_type}' opened at line {line_num} but never closed"
            ))

        # Check 3: Duplicate component IDs
        for i, line in enumerate(lines, 1):
            match = re.match(r'^:::(\w+)\{([^}]*)\}', line)
            if match and match.group(1) in COMPONENT_TYPES:
                attrs = parse_attributes(match.group(2))
                comp_id = attrs.get('id')
                if comp_id:
                    if comp_id in component_ids:
                        other = component_ids[comp_id]
                        errors.append(ValidationError(
                            rel_path, i, 'ERROR',
                            f"A glitch in the Elden Ring -- component id '{comp_id}' "
                            f"used in both '{other}' and '{rel_path}'"
                        ))
                    else:
                        component_ids[comp_id] = rel_path

        # Check 4: Broken internal links
        for i, line in enumerate(lines, 1):
            for match in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', line):
                target = match.group(2)
                # Only check internal .md links
                if target.startswith('http') or target.startswith('#'):
                    continue
                if target.endswith('.md'):
                    # Resolve relative to current file's directory
                    current_dir = Path(rel_path).parent
                    resolved = (current_dir / target).as_posix()
                    # Normalize path (remove ./ and resolve ..)
                    from pathlib import PurePosixPath
                    resolved = str(PurePosixPath(resolved))
                    if resolved not in all_md_files:
                        errors.append(ValidationError(
                            rel_path, i, 'WARNING',
                            f"The path is blocked -- '{rel_path}' references "
                            f"'{target}' which does not exist"
                        ))

        # Check 5: Missing images
        for i, line in enumerate(lines, 1):
            for match in re.finditer(r'!\[[^\]]*\]\(([^)]+)\)', line):
                img = match.group(1)
                if img.startswith('http'):
                    continue
                current_dir = Path(rel_path).parent
                resolved = str((current_dir / img).as_posix())
                # Normalize
                if resolved.startswith('./'):
                    resolved = resolved[2:]
                if resolved not in all_images:
                    errors.append(ValidationError(
                        rel_path, i, 'WARNING',
                        f"Missing image: '{img}' referenced from '{rel_path}'"
                    ))

        # Check 6: Invalid dates in component attrs
        for i, line in enumerate(lines, 1):
            match = re.match(r'^:::(\w+)\{([^}]*)\}', line)
            if match and match.group(1) in COMPONENT_TYPES:
                attrs = parse_attributes(match.group(2))
                for key in ('due', 'date'):
                    if key in attrs:
                        if not re.match(r'^\d{4}-\d{2}-\d{2}$', attrs[key]):
                            errors.append(ValidationError(
                                rel_path, i, 'WARNING',
                                f"Invalid date format '{attrs[key]}' for '{key}' "
                                f"(expected YYYY-MM-DD)"
                            ))

    # Check 7: Numbering gaps
    _check_numbering_gaps(content_path, exclude, errors)

    return errors


def _check_numbering_gaps(
    content_path: Path,
    exclude: List[str],
    errors: List[ValidationError],
):
    """Check for numbering gaps in directory prefixes."""
    for d in sorted(content_path.rglob('*')):
        if not d.is_dir() or d.name.startswith('.'):
            continue
        rel_d = str(d.relative_to(content_path))
        if is_excluded(rel_d, exclude) or is_wip(d.name):
            continue

        # Collect numbered children
        numbered = []
        for child in d.iterdir():
            match = re.match(r'^(\d+)[_-]', child.name)
            if match:
                num = int(match.group(1))
                if num > 0:  # Skip 00_ index
                    numbered.append(num)

        if not numbered:
            continue

        numbered.sort()
        for i in range(len(numbered) - 1):
            if numbered[i + 1] != numbered[i] + 1:
                gap_start = numbered[i] + 1
                gap_end = numbered[i + 1] - 1
                missing = ', '.join(f'{n:02d}_' for n in range(gap_start, gap_end + 1))
                errors.append(ValidationError(
                    rel_d, 0, 'WARNING',
                    f"Numbering gap: {numbered[i]:02d}_ -> {numbered[i+1]:02d}_ "
                    f"(missing: {missing})"
                ))
