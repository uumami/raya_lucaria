"""CLI for glintstone preprocessing.

Usage:
    python -m preprocessing build [--verbose] [--config PATH]
    python -m preprocessing validate [--verbose]
    python -m preprocessing scaffold chapter "03_advanced"
    python -m preprocessing scaffold homework
"""
import argparse
import json
import sys
from pathlib import Path

from preprocessing.logger import get_logger
from preprocessing.config import load_config, resolve_repo_info
from preprocessing.extract_metadata import extract_all_metadata
from preprocessing.generate_hierarchy import generate_hierarchy
from preprocessing.aggregate_tasks import aggregate_all_tasks
from preprocessing.validate_content import validate_content
from preprocessing.scaffold import scaffold_chapter, scaffold_component

log = get_logger()


def cmd_build(args):
    """Run full preprocessing pipeline."""
    config = load_config(args.config)
    verbose = args.verbose

    content_dir = Path(config.source.content_dir)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    exclude = config.source.exclude

    log.info("Extracting metadata from markdown files...")
    metadata = extract_all_metadata(content_dir, exclude, verbose)
    _write_json(output_dir / 'metadata.json', metadata)
    log.info(f"  {len(metadata)} file metadata records saved")

    log.info("Generating hierarchy tree...")
    hierarchy = generate_hierarchy(content_dir, metadata, exclude, verbose)
    _write_json(output_dir / 'hierarchy.json', hierarchy)
    log.info("  Hierarchy saved")

    # Generate docs hierarchy (if enabled and docs dir exists)
    docs_dir = Path('glintstone/docs')
    if config.features.docs and docs_dir.exists():
        log.info("Generating docs hierarchy...")
        docs_metadata = extract_all_metadata(docs_dir, exclude=[], verbose=verbose)
        docs_hierarchy = generate_hierarchy(docs_dir, docs_metadata, exclude=[], verbose=verbose)
        docs_hierarchy['title'] = 'Documentacion'
        _write_json(output_dir / 'hierarchy_docs.json', docs_hierarchy)
        log.info("  Docs hierarchy saved")
    else:
        _write_json(output_dir / 'hierarchy_docs.json',
            {'name': 'docs', 'path': '', 'type': 'root', 'title': 'Documentacion', 'children': []})

    log.info("Aggregating tasks...")
    tasks = aggregate_all_tasks(content_dir, metadata, verbose)
    _write_json(output_dir / 'tasks.json', tasks)
    total_tasks = sum(len(v) for v in tasks.values())
    log.info(f"  {total_tasks} tasks saved")

    log.info("Resolving repository configuration...")
    try:
        repo_info = resolve_repo_info(config, verbose)
        _write_json(output_dir / 'repo.json', repo_info)
        log.info(f"  Repository: {repo_info['repo_name']} (prefix: {repo_info['base_url']})")
    except ValueError as e:
        log.warning(str(e))
        # Write minimal repo.json so Eleventy doesn't crash
        _write_json(output_dir / 'repo.json', {
            'repo_name': '', 'org': '', 'base_url': '/', 'upstream_url': '', 'pr_compare_url': ''
        })

    # Save site config for templates
    site_data = {
        'name': config.site.name,
        'description': config.site.description,
        'language': config.site.language,
        'author': config.site.author,
    }
    _write_json(output_dir / 'site.json', site_data)

    # Save features config
    features_data = {
        'search': config.features.search,
        'theme_toggle': config.features.theme_toggle,
        'font_toggle': config.features.font_toggle,
        'copy_code_button': config.features.copy_code_button,
        'math': config.features.math,
        'mermaid': config.features.mermaid,
        'docs': config.features.docs,
    }
    _write_json(output_dir / 'features.json', features_data)

    # Save navigation config
    nav_data = {
        'show_breadcrumbs': config.navigation.show_breadcrumbs,
        'show_sidebar': config.navigation.show_sidebar,
        'show_prev_next': config.navigation.show_prev_next,
        'show_toc': config.navigation.show_toc,
    }
    _write_json(output_dir / 'navigation.json', nav_data)

    # Save task pages config
    task_pages = [
        {'type': p.type, 'title': p.title, 'slug': p.slug}
        for p in config.tasks.pages
    ]
    _write_json(output_dir / 'taskPages.json', task_pages)

    log.info("Preprocessing complete!")
    return 0


def cmd_validate(args):
    """Run content validation only."""
    config = load_config(args.config)
    content_dir = Path(config.source.content_dir)
    exclude = config.source.exclude

    log.info("Extracting metadata for validation...")
    metadata = extract_all_metadata(content_dir, exclude, args.verbose)

    log.info("Running content validation...")
    errors = validate_content(content_dir, metadata, exclude, args.verbose)

    if not errors:
        log.info("All clear, Tarnished. No issues found.")
        return 0

    # Group by severity
    err_count = sum(1 for e in errors if e.severity == 'ERROR')
    warn_count = sum(1 for e in errors if e.severity == 'WARNING')

    for error in sorted(errors, key=lambda e: (e.file, e.line)):
        print(str(error))

    print(f"\n{err_count} error(s), {warn_count} warning(s)")
    return 1 if err_count > 0 else 0


def cmd_scaffold(args):
    """Scaffold new content."""
    config = load_config(args.config)
    content_dir = Path(config.source.content_dir)

    if args.scaffold_type == 'chapter':
        if not args.name:
            log.error("Chapter name required. Example: scaffold chapter 03_advanced")
            return 1
        scaffold_chapter(content_dir, args.name)
        return 0
    else:
        # Component template
        template = scaffold_component(args.scaffold_type, args.name or "Nuevo")
        if template:
            print(template)
            return 0
        return 1


def _write_json(path: Path, data):
    """Write data as formatted JSON."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='glintstone',
        description='Glintstone preprocessing pipeline',
    )
    parser.add_argument('--config', type=Path, default=Path('glintstone.yaml'),
                        help='Path to glintstone.yaml config file')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # build
    build_parser = subparsers.add_parser('build', help='Full preprocessing pipeline')
    build_parser.add_argument('--output', type=Path,
                              default=Path('glintstone/src/eleventy/_data'),
                              help='Output directory for JSON data')

    # validate
    subparsers.add_parser('validate', help='Validate content only')

    # scaffold
    scaffold_parser = subparsers.add_parser('scaffold', help='Scaffold new content')
    scaffold_parser.add_argument('scaffold_type',
                                 choices=['chapter', 'homework', 'exercise',
                                          'prompt', 'example', 'exam', 'project',
                                          'quiz', 'embed'],
                                 help='What to scaffold')
    scaffold_parser.add_argument('name', nargs='?', default='',
                                 help='Name for the scaffolded item')

    args = parser.parse_args()

    if not args.command:
        # Default to build
        args.command = 'build'
        args.output = Path('glintstone/src/eleventy/_data')

    if args.command == 'build':
        return cmd_build(args)
    elif args.command == 'validate':
        return cmd_validate(args)
    elif args.command == 'scaffold':
        return cmd_scaffold(args)
    else:
        parser.print_help()
        return 1
