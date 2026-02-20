"""Aggregate tasks (homework, exams, projects) from content metadata."""
from datetime import datetime, date
from typing import Dict, List, Any

from preprocessing.logger import get_logger
from preprocessing.utils import get_chapter_name

log = get_logger()


def is_overdue(due_date: str) -> bool:
    """Check if a due date has passed."""
    if not due_date:
        return False
    try:
        due = datetime.strptime(str(due_date), '%Y-%m-%d').date()
        return due < date.today()
    except (ValueError, TypeError):
        return False


def aggregate_all_tasks(
    content_dir,
    metadata: Dict[str, Any],
    verbose: bool = False,
) -> Dict[str, List[Dict[str, Any]]]:
    """Aggregate all tasks from file metadata.

    Returns dict with keys: 'homework', 'exams', 'projects'
    """
    tasks = {'homework': [], 'exams': [], 'projects': []}

    for file_path, file_meta in metadata.items():
        components = file_meta.get('components', [])
        chapter = get_chapter_name(file_path)

        for comp in components:
            comp_type = comp.get('type')
            attrs = comp.get('attrs', {})

            if comp_type == 'homework':
                task = {
                    'id': attrs.get('id', ''),
                    'title': attrs.get('title', 'Tarea'),
                    'due': attrs.get('due'),
                    'points': attrs.get('points'),
                    'chapter': chapter,
                    'file': file_path,
                    'url': '/' + file_path.replace('.md', '/'),
                    'summary': comp.get('content_preview', '')[:100],
                    'overdue': is_overdue(attrs.get('due')),
                    'type': 'homework',
                }
                tasks['homework'].append(task)
                if verbose:
                    log.debug(f"Found homework: {task['title']} in {chapter}")

            elif comp_type == 'exam':
                task = {
                    'id': attrs.get('id', ''),
                    'title': attrs.get('title', 'Examen'),
                    'date': attrs.get('date'),
                    'location': attrs.get('location'),
                    'duration': attrs.get('duration'),
                    'points': attrs.get('points'),
                    'chapter': chapter,
                    'file': file_path,
                    'url': '/' + file_path.replace('.md', '/'),
                    'summary': comp.get('content_preview', '')[:100],
                    'overdue': is_overdue(attrs.get('date')),
                    'type': 'exam',
                }
                tasks['exams'].append(task)
                if verbose:
                    log.debug(f"Found exam: {task['title']} in {chapter}")

            elif comp_type == 'project':
                task = {
                    'id': attrs.get('id', ''),
                    'title': attrs.get('title', 'Proyecto'),
                    'due': attrs.get('due'),
                    'points': attrs.get('points'),
                    'team_size': attrs.get('team_size'),
                    'chapter': chapter,
                    'file': file_path,
                    'url': '/' + file_path.replace('.md', '/'),
                    'summary': comp.get('content_preview', '')[:100],
                    'overdue': is_overdue(attrs.get('due')),
                    'type': 'project',
                }
                tasks['projects'].append(task)
                if verbose:
                    log.debug(f"Found project: {task['title']} in {chapter}")

    # Sort by file path
    for key in tasks:
        tasks[key].sort(key=lambda t: t.get('file', ''))

    return tasks
