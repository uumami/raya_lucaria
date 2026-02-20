"""Scaffolding for new chapters and components."""
from pathlib import Path

from preprocessing.logger import get_logger

log = get_logger()

CHAPTER_INDEX_TEMPLATE = """---
title: "{title}"
---

# {title}

"""

COMPONENT_TEMPLATES = {
    'homework': ''':::homework{{id="{id}" title="{title}" due="YYYY-MM-DD" points="10"}}

Instrucciones de la tarea aqui.

:::''',
    'exercise': ''':::exercise{{title="{title}" difficulty="2"}}

Instrucciones del ejercicio aqui.

:::''',
    'prompt': ''':::prompt{{title="{title}" for="ChatGPT"}}

Tu prompt aqui.

:::''',
    'example': ''':::example{{title="{title}"}}

Contenido del ejemplo aqui.

:::''',
    'exam': ''':::exam{{id="{id}" title="{title}" date="YYYY-MM-DD" location="TBD" duration="2h"}}

Informacion del examen aqui.

:::''',
    'project': ''':::project{{id="{id}" title="{title}" due="YYYY-MM-DD" points="100"}}

Descripcion del proyecto aqui.

:::''',
    'quiz': ''':::quiz{{title="{title}"}}

- [ ] Opcion incorrecta
- [x] Opcion correcta
- [ ] Otra opcion incorrecta

:::''',
    'embed': ''':::embed{{src="https://www.youtube.com/embed/VIDEO_ID" title="{title}"}}

Descripcion opcional del recurso.

:::''',
}


def scaffold_chapter(content_dir: Path, chapter_name: str) -> Path:
    """Create a new chapter directory with 00_index.md."""
    chapter_path = content_dir / chapter_name
    if chapter_path.exists():
        log.warning(f"Directory already exists: {chapter_path}")
        return chapter_path

    chapter_path.mkdir(parents=True)

    title = chapter_name.split('_', 1)[-1].replace('_', ' ').title() if '_' in chapter_name else chapter_name

    index_path = chapter_path / '00_index.md'
    index_path.write_text(CHAPTER_INDEX_TEMPLATE.format(title=title), encoding='utf-8')

    log.info("A new path opens before you, Tarnished.")
    log.info(f"Created: {chapter_path}/00_index.md")
    return chapter_path


def scaffold_component(comp_type: str, title: str = "Nuevo", comp_id: str = "id-01") -> str:
    """Print a component template to stdout."""
    if comp_type not in COMPONENT_TEMPLATES:
        log.error(f"Unknown component type: {comp_type}")
        log.info(f"Available types: {', '.join(sorted(COMPONENT_TEMPLATES.keys()))}")
        return ""

    template = COMPONENT_TEMPLATES[comp_type].format(
        id=comp_id, title=title,
    )
    log.info("Sorcery inscribed.")
    return template
