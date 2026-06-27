from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from importlib import resources
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlsplit, urlunsplit

from raya_schema import (
    ValidationReport,
    validate_artifact_manifest,
    validate_cache_index,
    validate_execution_index,
    validate_graph_index,
    validate_indices_index,
    validate_course,
    validate_links_index,
    validate_navigation_index,
    validate_official_index,
    validate_pages_index,
    validate_quanta_index,
    validate_references_index,
    validate_reviewed_outputs_index,
    validate_runtime_index,
    validate_search_index,
    validate_tasks_index,
)
from raya_schema.content import ContentModel, ContentPage, resolve_course_content
from raya_schema.course import resolve_course_source_root
from raya_schema.links import (
    colocated_asset_output_path,
    classify_markdown_target,
    extract_markdown_links,
    markdown_link_fragment,
    markdown_link_path,
    resolve_course_asset_reference,
    resolve_local_markdown_target,
    stable_markdown_id,
)
from raya_schema.numbered_objects import (
    NumberedObject,
    NumberedObjectConfig,
    build_numbered_objects_index,
    normalize_numbered_object_config,
    validate_numbered_objects_index,
)
from raya_schema.official import discover_official_objects
from raya_schema.references import (
    SourceReference,
    notebook_validation_error,
    reference_format,
    resolve_course_reference,
    source_reference_id,
)
from raya_schema.reviewed import (
    REVIEWED_ARTIFACT_DIR,
    REVIEWED_BROWSER_DIR,
    ReviewedOutput,
    discover_reviewed_outputs,
    reviewed_outputs_by_reference,
    reviewed_outputs_index,
)
from raya_schema.runtime import (
    RuntimeModel,
    cache_index,
    execution_index,
    load_runtime_model,
    reference_execution_metadata,
    runtime_index,
)
from raya_schema.wikilinks import (
    WikilinkResolver,
    build_wikilink_resolver,
    extract_wikilinks,
)
from raya_schema.yaml_io import load_yaml_file
from raya_static.accessibility import (
    ACCESSIBILITY_RESOURCE_PATH,
    COMFORT_PREPAINT_JS_NAME,
    OPEN_DYSLEXIC_CSS_NAME,
    OPEN_DYSLEXIC_JS_NAME,
    OPEN_DYSLEXIC_VOLATILE_JS_NAME,
    open_dyslexic_resources,
)
from raya_static.discovery import (
    DISCOVERY_RESOURCE_PATH,
    DISCOVERY_SCRIPT_NAME,
    discovery_resources,
)
from raya_static.graph import GRAPH_RESOURCE_PATH, GRAPH_SCRIPT_NAME, graph_resources
from raya_static.math_renderer import MathRenderer
from raya_static.numbered_objects import (
    NumberedObjectRenderContext,
    NumberedObjectRenderItem,
    NumberedObjectSource,
    compute_numbered_objects_for_page,
    page_number_prefix_from_source_path,
    prepare_numbered_object_markdown,
)
from raya_static.practice import (
    PRACTICE_RESOURCE_PATH,
    PRACTICE_SCRIPT_NAME,
    practice_resources,
)
from raya_static.proofs import (
    StaticEnvironmentRenderContext,
    StaticEnvironmentRenderItem,
    StaticEnvironmentSource,
    prepare_static_environment_markdown,
)
from raya_static.rendering import (
    RENDER_STYLESHEET_PATH,
    contains_full_latex_document,
    has_malformed_display_math_delimiters,
    has_unsupported_nested_math_delimiters,
    missing_footnote_definitions,
    render_markdown_body,
    rich_render_css,
)
from raya_static.skins import (
    SKIN_PREPAINT_JS_NAME,
    SKIN_STYLESHEET_PATH,
    SKIN_TOGGLE_JS_NAME,
    SkinContext,
    load_skin_context,
    render_skin_css,
    skin_cycle_entries,
    skin_id_for_source_path,
    skin_prepaint_script,
    skin_toggle_script,
)
from raya_static.search import (
    SEARCH_RESOURCE_PATH,
    SEARCH_SCRIPT_NAME,
    search_resources,
)
from raya_static.schedule import (
    SCHEDULE_RESOURCE_PATH,
    SCHEDULE_SCRIPT_NAME,
    schedule_resources,
)
from raya_static.shell import SHELL_RESOURCE_PATH, SHELL_SCRIPT_NAME, shell_resources
from raya_static.tasks import TASKS_RESOURCE_PATH, TASKS_SCRIPT_NAME, tasks_resources


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
ARTIFACT_VERSION = "0.1"
SOURCE_SCHEMA_VERSION = "0.1"
STATIC_RESOURCE_DIR = "_raya"
STATIC_ASSETS_PATH = Path(STATIC_RESOURCE_DIR) / "assets"
STATIC_FILES_PATH = Path(STATIC_RESOURCE_DIR) / "files"
STATIC_REVIEWED_PATH = REVIEWED_BROWSER_DIR
STATIC_INSPECTION_PATH = Path(STATIC_RESOURCE_DIR) / "inspect" / "index.html"
STATIC_GRAPH_PATH = Path(STATIC_RESOURCE_DIR) / "graph" / "index.html"
STATIC_SEARCH_PATH = Path(STATIC_RESOURCE_DIR) / "search" / "index.html"
STATIC_PRACTICE_PATH = Path(STATIC_RESOURCE_DIR) / "practice" / "index.html"
STATIC_TASKS_PATH = Path(STATIC_RESOURCE_DIR) / "tasks" / "index.html"
STATIC_SCHEDULE_PATH = Path(STATIC_RESOURCE_DIR) / "schedule" / "index.html"
MATH_STYLESHEET_PATH = Path(STATIC_RESOURCE_DIR) / "render" / "math" / "mathjax.css"
GRAPH_GROUP_COLORS = (
    "var(--raya-graph-group-1)",
    "var(--raya-graph-group-2)",
    "var(--raya-graph-group-3)",
    "var(--raya-graph-group-4)",
    "var(--raya-graph-group-5)",
    "var(--raya-graph-group-6)",
    "var(--raya-graph-group-7)",
    "var(--raya-graph-group-8)",
)
MATH_FONT_SOURCE_DIR = (
    REPOSITORY_ROOT
    / "node_modules"
    / "@mathjax"
    / "mathjax-newcm-font"
    / "chtml"
    / "woff2"
)
MATH_CSS_URL_RE = re.compile(r"url\(\s*(?P<value>[^)]*?)\s*\)")
MATH_FONT_NAME_RE = re.compile(r"[A-Za-z0-9_.-]+\.woff2")
SURFACE_STUDENT_DEFAULT = "student-default"
SURFACE_SUPPORT_PANEL = "support-panel"
SURFACE_INSPECTION = "inspection"
SURFACE_MACHINE_ONLY = "machine-only"
SURFACE_TIERS = frozenset(
    {
        SURFACE_STUDENT_DEFAULT,
        SURFACE_SUPPORT_PANEL,
        SURFACE_INSPECTION,
        SURFACE_MACHINE_ONLY,
    }
)


@dataclass(frozen=True)
class _MathRenderResources:
    css: str
    font_files: tuple[Path, ...]


@dataclass(frozen=True)
class _NumberedObjectCollection:
    objects: list[NumberedObject]
    objects_by_id: dict[str, NumberedObject]
    items_by_page_id: dict[str, list[NumberedObjectRenderItem]]
    prepared_bodies_by_page_id: dict[str, str]


@dataclass(frozen=True)
class _StaticEnvironmentCollection:
    items_by_page_id: dict[str, list[StaticEnvironmentRenderItem]]
    prepared_bodies_by_page_id: dict[str, str]


def build_course(course_path: str | Path) -> ValidationReport:
    root = Path(course_path).resolve()
    validation_report = validate_course(root)
    validation_report.context = "build"
    if not validation_report.ok:
        return validation_report

    report = ValidationReport(context="build")
    _merge_report(report, validation_report)

    config_path = root / "raya.yaml"
    config = _load_config(config_path, report)
    if config is None:
        return report

    course_id = str(config["course_id"])
    numbered_config = normalize_numbered_object_config(
        config,
        report=report,
        context=str(config_path),
    )
    if not report.ok:
        return report
    source_root = resolve_course_source_root(root=root, config=config, report=report)
    if source_root is None:
        return report
    source_dir = source_root
    runtime_model = load_runtime_model(root, report)
    if not report.ok:
        return report
    artifact_dir = (root / str(config["artifact"])).resolve()

    if _is_unsafe_artifact_dir(root, source_dir, artifact_dir):
        report.add_error(
            "Artifact directory overlaps source course truth",
            path=artifact_dir,
            field="artifact",
            next_action="Use a generated output directory such as artifact or _site",
        )
        return report

    content_model = resolve_course_content(
        course_root=root,
        content_dir=source_dir,
        course_id=course_id,
        config=config,
        report=report,
    )
    pages = content_model.pages
    official_objects = discover_official_objects(
        course_root=root,
        course_id=course_id,
        source_dir=source_dir,
        content_model=content_model,
        report=report,
    )
    if not report.ok:
        return report
    _validate_rich_markdown_inputs(pages, report)
    if not report.ok:
        return report
    skin_context = load_skin_context(
        root,
        config,
        source_root=source_dir,
        report=report,
    )
    if not report.ok:
        return report

    site_dir = artifact_dir / "site"
    data_dir = artifact_dir / "data"
    artifact_assets_dir = artifact_dir / "assets"
    artifact_files_dir = artifact_dir / "files"
    artifact_reviewed_dir = artifact_dir / REVIEWED_ARTIFACT_DIR
    site_assets_dir = site_dir / STATIC_ASSETS_PATH
    site_files_dir = site_dir / STATIC_FILES_PATH
    site_reviewed_dir = site_dir / STATIC_REVIEWED_PATH
    pages_by_source = content_model.pages_by_source
    pages_by_reference = {
        **content_model.pages_by_id,
        **content_model.pages_by_alias,
    }
    wikilink_resolver = build_wikilink_resolver(content_model)
    official_counts = _official_counts(
        official_objects,
        content_model=content_model,
        course_id=course_id,
    )
    references = _collect_source_references(
        course_id,
        content_model,
        root,
        source_dir,
        runtime_model,
        report,
    )
    reviewed_outputs = discover_reviewed_outputs(
        course_id=course_id,
        course_root=root,
        source_dir=source_dir,
        runtime_model=runtime_model,
        references=references,
        report=report,
        require_frozen=True,
    )
    if not report.ok:
        return report
    reviewed_by_reference = reviewed_outputs_by_reference(reviewed_outputs)
    references_by_page = _references_by_page(references)
    links_index = _links_index(
        course_id,
        content_model,
        pages_by_reference,
        pages_by_source,
        root,
        wikilink_resolver,
    )
    graph_index = _graph_index(course_id, content_model, links_index)
    graph_context_by_page = _graph_context_by_page(content_model, graph_index)
    official_by_page = _official_objects_by_page(
        official_objects,
        content_model=content_model,
        course_id=course_id,
    )
    math_renderer = MathRenderer()
    numbered_object_collection = _collect_numbered_objects(
        course_root=root,
        source_dir=source_dir,
        pages=pages,
        config=numbered_config,
        report=report,
    )
    if not report.ok:
        return report
    static_environment_collection = _collect_static_environments(
        pages=pages,
        prepared_bodies_by_page_id=numbered_object_collection.prepared_bodies_by_page_id,
        objects_by_id=numbered_object_collection.objects_by_id,
        report=report,
    )
    if not report.ok:
        return report
    rendered_pages: list[tuple[ContentPage, str]] = []
    search_records_by_page: dict[str, dict[str, Any]] = {}

    for page in pages:
        numbered_context = NumberedObjectRenderContext(
            items=numbered_object_collection.items_by_page_id.get(page.id, []),
            objects_by_id=numbered_object_collection.objects_by_id,
        )
        static_environment_context = StaticEnvironmentRenderContext(
            items=static_environment_collection.items_by_page_id.get(page.id, []),
            objects_by_id=numbered_object_collection.objects_by_id,
        )
        rendered_page, search_record = _render_page(
            page=page,
            body=static_environment_collection.prepared_bodies_by_page_id.get(
                page.id,
                page.body,
            ),
            numbered_objects=numbered_context,
            proofs=static_environment_context,
            content_model=content_model,
            pages_by_source=pages_by_source,
            pages_by_reference=pages_by_reference,
            course_root=root,
            source_dir=source_dir,
            course_title=str(config["title"]),
            language=str(config["language"]),
            official_counts=official_counts,
            official_objects=official_by_page.get(page.id, []),
            page_references=references_by_page.get(page.id, []),
            reviewed_by_reference=reviewed_by_reference,
            report=report,
            math_renderer=math_renderer,
            skin_context=skin_context,
            page_graph_context=graph_context_by_page.get(page.id, {}),
            wikilink_resolver=wikilink_resolver,
        )
        if not report.ok:
            return report
        rendered_pages.append((page, rendered_page))
        search_records_by_page[page.id] = search_record

    math_resources = _prepare_math_render_resources(math_renderer.css_chunks, report)
    if not report.ok:
        return report

    _replace_generated_output(artifact_dir, report)
    for directory in (
        site_dir,
        data_dir,
        artifact_assets_dir,
        artifact_files_dir,
        artifact_reviewed_dir,
        site_assets_dir,
        site_files_dir,
        site_reviewed_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)
        report.wrote_output(directory)
    _write_rich_render_resources(site_dir, report, skin_context=skin_context)
    _write_shell_resources(site_dir, report)
    _write_graph_resources(site_dir, report)
    _write_discovery_resources(site_dir, report)
    _write_search_resources(site_dir, report)
    _write_practice_resources(site_dir, report)
    _write_tasks_resources(site_dir, report)
    _write_schedule_resources(site_dir, report)
    copied_math_font_files = _write_math_render_resources(
        site_dir,
        math_resources,
        report,
    )
    if not report.ok:
        return report

    for page, rendered_page in rendered_pages:
        output_file = site_dir / page.output_path
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(rendered_page, encoding="utf-8")
        report.wrote_output(output_file)

    copied_source_assets = _copy_source_assets(
        source_dir,
        artifact_assets_dir,
        report,
    )
    copied_site_source_assets = _copy_source_assets(
        source_dir,
        site_assets_dir,
        report,
    )
    copied_reference_files = _copy_reference_files(
        references,
        artifact_files_dir,
        site_files_dir,
        report,
    )
    copied_reviewed_files = _copy_reviewed_output_files(
        reviewed_outputs,
        artifact_dir,
        site_dir,
        report,
    )

    pages_index = _pages_index(course_id, pages)
    quanta_index = _quanta_index(course_id, pages)
    navigation_index = _navigation_index(course_id, content_model)
    indices_index = _indices_index(course_id, content_model, official_counts)
    official_index = _official_index(course_id, official_objects)
    tasks_index = _browser_tasks_payload(content_model, official_by_page)
    search_index = _search_index(content_model, search_records_by_page)
    references_index = _references_index(course_id, references, reviewed_by_reference)
    reviewed_outputs_data = reviewed_outputs_index(course_id, reviewed_outputs)
    numbered_objects_index = build_numbered_objects_index(
        course_id=course_id,
        objects=numbered_object_collection.objects,
    )
    runtime_data = runtime_index(course_id, runtime_model)
    execution_data = execution_index(course_id, references, runtime_model)
    cache_data = cache_index(
        course_id,
        references,
        runtime_model,
        schema_version=SOURCE_SCHEMA_VERSION,
    )

    _write_json(data_dir / "pages.json", pages_index, report)
    _write_json(data_dir / "quanta.json", quanta_index, report)
    _write_json(data_dir / "links.json", links_index, report)
    _write_json(data_dir / "graph.json", graph_index, report)
    _write_json(data_dir / "navigation.json", navigation_index, report)
    _write_json(data_dir / "indices.json", indices_index, report)
    _write_json(data_dir / "official.json", official_index, report)
    _write_json(data_dir / "tasks.json", tasks_index, report)
    _write_json(data_dir / "search-index.json", search_index, report)
    _write_json(data_dir / "references.json", references_index, report)
    _write_json(data_dir / "reviewed-outputs.json", reviewed_outputs_data, report)
    _write_json(data_dir / "numbered-objects.json", numbered_objects_index, report)
    _write_json(data_dir / "runtime.json", runtime_data, report)
    _write_json(data_dir / "execution.json", execution_data, report)
    _write_json(data_dir / "cache.json", cache_data, report)
    _write_inspection_surface(
        site_dir=site_dir,
        site_assets_dir=site_assets_dir,
        content_model=content_model,
        course_title=str(config["title"]),
        language=str(config["language"]),
        graph_index=graph_index,
        references=references,
        reviewed_outputs=reviewed_outputs,
        report=report,
    )
    _write_graph_surface(
        site_dir=site_dir,
        content_model=content_model,
        course_title=str(config["title"]),
        language=str(config["language"]),
        graph_index=graph_index,
        official_counts=official_counts,
        official_by_page=official_by_page,
        search_records=search_records_by_page,
        skin_context=skin_context,
        report=report,
    )
    _write_search_surface(
        site_dir=site_dir,
        content_model=content_model,
        course_title=str(config["title"]),
        language=str(config["language"]),
        graph_index=graph_index,
        official_counts=official_counts,
        official_by_page=official_by_page,
        search_records=search_records_by_page,
        skin_context=skin_context,
        report=report,
    )
    _write_practice_surface(
        site_dir=site_dir,
        content_model=content_model,
        official_by_page=official_by_page,
        course_title=str(config["title"]),
        language=str(config["language"]),
        skin_context=skin_context,
        report=report,
    )
    _write_tasks_surface(
        site_dir=site_dir,
        content_model=content_model,
        official_by_page=official_by_page,
        course_title=str(config["title"]),
        language=str(config["language"]),
        skin_context=skin_context,
        report=report,
    )
    _write_schedule_surface(
        site_dir=site_dir,
        content_model=content_model,
        official_by_page=official_by_page,
        course_title=str(config["title"]),
        language=str(config["language"]),
        skin_context=skin_context,
        report=report,
    )

    manifest = {
        "artifact_version": ARTIFACT_VERSION,
        "course_id": course_id,
        "course_version_id": _source_hash(root, source_dir),
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "static_site_root": "site",
        "data": {
            "pages": "data/pages.json",
            "quanta": "data/quanta.json",
            "links": "data/links.json",
            "graph": "data/graph.json",
            "navigation": "data/navigation.json",
            "indices": "data/indices.json",
            "official": "data/official.json",
            "tasks": "data/tasks.json",
            "search_index": "data/search-index.json",
            "references": "data/references.json",
            "reviewed_outputs": "data/reviewed-outputs.json",
            "numbered_objects": "data/numbered-objects.json",
            "runtime": "data/runtime.json",
            "execution": "data/execution.json",
            "cache": "data/cache.json",
        },
        "assets": "assets",
        "files": "files",
        "generated_by": "Glintstone minimal builder",
    }
    _write_json(artifact_dir / "manifest.json", manifest, report)

    _validate_generated_artifact(artifact_dir, report)
    if report.ok:
        report.add_info(
            "Course artifact build passed",
            path=artifact_dir,
            next_action="Serve artifact/site as static files or inspect artifact/manifest.json",
        )
        if copied_source_assets:
            report.add_info(
                f"Copied {copied_source_assets} source asset file(s)",
                path=artifact_assets_dir,
            )
        if copied_site_source_assets:
            report.add_info(
                f"Copied {copied_site_source_assets} browser source asset file(s)",
                path=site_assets_dir,
            )
        if copied_reference_files:
            report.add_info(
                f"Copied {copied_reference_files} referenced code/notebook file(s)",
                path=artifact_files_dir,
            )
        if copied_reviewed_files:
            report.add_info(
                f"Copied {copied_reviewed_files} reviewed output file(s)",
                path=artifact_reviewed_dir,
            )
        if copied_math_font_files:
            report.add_info(
                f"Copied {copied_math_font_files} MathJax font file(s)",
                path=site_dir / MATH_STYLESHEET_PATH.parent / "fonts",
            )
    return report


def _load_config(path: Path, report: ValidationReport) -> dict[str, Any] | None:
    report.read_file(path)
    try:
        data = load_yaml_file(path)
    except Exception as exc:
        report.add_error(
            f"Could not read YAML: {exc}",
            path=path,
            next_action="Fix YAML syntax",
        )
        return None
    if not isinstance(data, dict):
        report.add_error(
            "YAML document must be a mapping",
            path=path,
            next_action="Use key/value configuration fields",
        )
        return None
    return data


def _is_unsafe_artifact_dir(
    root: Path,
    source_dir: Path,
    artifact_dir: Path,
) -> bool:
    source_roots = {root, source_dir}
    return artifact_dir in {path.resolve() for path in source_roots}


def _replace_generated_output(artifact_dir: Path, report: ValidationReport) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    for relative in ("site", "data", "assets", "files", "reviewed"):
        path = artifact_dir / relative
        if path.exists():
            shutil.rmtree(path)
            report.wrote_output(path)
    manifest = artifact_dir / "manifest.json"
    if manifest.exists():
        manifest.unlink()
        report.wrote_output(manifest)


def _copy_source_assets(
    source_dir: Path,
    target_assets: Path,
    report: ValidationReport,
) -> int:
    copied = 0
    for source_path in sorted(path for path in source_dir.rglob("*") if path.is_file()):
        if "_assets" not in source_path.relative_to(source_dir).parts:
            continue
        report.read_file(source_path)
        target_path = target_assets / colocated_asset_output_path(
            source_dir, source_path
        )
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        report.wrote_output(target_path)
        copied += 1
    return copied


def _collect_numbered_objects(
    *,
    course_root: Path,
    source_dir: Path,
    pages: list[ContentPage],
    config: NumberedObjectConfig,
    report: ValidationReport,
) -> _NumberedObjectCollection:
    objects: list[NumberedObject] = []
    objects_by_id: dict[str, NumberedObject] = {}
    items_by_page_id: dict[str, list[NumberedObjectRenderItem]] = {}
    prepared_bodies_by_page_id: dict[str, str] = {}
    seen_ids: dict[str, NumberedObjectSource] = {}

    for page in pages:
        prepared = prepare_numbered_object_markdown(
            page.body,
            report=report,
            source_path=page.source_path,
        )
        prepared_bodies_by_page_id[page.id] = prepared.body
        if not report.ok:
            continue

        page_sources = []
        for source in prepared.sources:
            if source.family not in config.families:
                report.add_error(
                    f"Unknown numbered object family '{source.family}'",
                    path=source.source_path,
                    field=f"line:{source.start_line}",
                    next_action="Use a built-in numbered object family or define it under render.numbered_objects.families",
                )
                continue
            if source.id in seen_ids:
                first_source = seen_ids[source.id]
                report.add_error(
                    f"Duplicate numbered object ID '{source.id}'",
                    path=source.source_path,
                    field=f"line:{source.start_line}",
                    next_action=(
                        "Use a unique ID; first seen in "
                        f"{first_source.source_path} line:{first_source.start_line}"
                    ),
                )
                continue
            seen_ids[source.id] = source
            page_sources.append(source)

        if not report.ok:
            continue

        course_relative_source_path = page.source_path.relative_to(
            course_root
        ).as_posix()
        source_relative_path = page.source_path.relative_to(source_dir).as_posix()
        page_objects = compute_numbered_objects_for_page(
            page_sources,
            config=config,
            course_relative_source_path=course_relative_source_path,
            page_id=page.id,
            page_title=page.title,
            page_output_path=page.output_path,
            page_number_prefix=page.display_label
            or page_number_prefix_from_source_path(source_relative_path),
        )
        objects.extend(page_objects)
        objects_by_id.update({obj.id: obj for obj in page_objects})
        items_by_page_id[page.id] = [
            NumberedObjectRenderItem(source=source, object=obj)
            for source, obj in zip(page_sources, page_objects)
        ]

    return _NumberedObjectCollection(
        objects=objects,
        objects_by_id=objects_by_id,
        items_by_page_id=items_by_page_id,
        prepared_bodies_by_page_id=prepared_bodies_by_page_id,
    )


def _collect_static_environments(
    *,
    pages: list[ContentPage],
    prepared_bodies_by_page_id: dict[str, str],
    objects_by_id: dict[str, NumberedObject],
    report: ValidationReport,
) -> _StaticEnvironmentCollection:
    items_by_page_id: dict[str, list[StaticEnvironmentRenderItem]] = {}
    static_environment_prepared_bodies_by_page_id: dict[str, str] = {}
    seen_ids: dict[str, StaticEnvironmentSource] = {}

    for page in pages:
        prepared = prepare_static_environment_markdown(
            prepared_bodies_by_page_id.get(page.id, page.body),
            report=report,
            source_path=page.source_path,
        )
        static_environment_prepared_bodies_by_page_id[page.id] = prepared.body
        if not report.ok:
            continue

        page_items: list[StaticEnvironmentRenderItem] = []
        for source in prepared.sources:
            if source.id:
                first_source = seen_ids.get(source.id)
                if first_source is not None:
                    if source.kind == "proof":
                        message = f"Duplicate proof ID '{source.id}'"
                        next_action = (
                            "Use a unique proof ID; first seen in "
                            f"{first_source.source_path} line:{first_source.start_line}"
                        )
                    else:
                        message = f"Duplicate static environment ID '{source.id}'"
                        next_action = (
                            "Use a unique static environment ID; first seen in "
                            f"{first_source.source_path} line:{first_source.start_line}"
                        )
                    report.add_error(
                        message,
                        path=source.source_path,
                        field=f"line:{source.start_line}",
                        next_action=next_action,
                    )
                    continue
                if source.id in objects_by_id:
                    report.add_error(
                        f"Static environment ID '{source.id}' collides with a numbered object ID",
                        path=source.source_path,
                        field=f"line:{source.start_line}",
                        next_action="Use a unique static environment ID",
                    )
                    continue
                seen_ids[source.id] = source
            target = None
            if source.of_id:
                target = objects_by_id.get(source.of_id)
                if target is None:
                    report.add_error(
                        f"Unknown {source.kind} target '{source.of_id}'",
                        path=source.source_path,
                        field=f"line:{source.start_line}",
                        next_action='Use of="object-id" with an existing numbered object ID',
                    )
                    continue
            page_items.append(StaticEnvironmentRenderItem(source=source, target=target))
        items_by_page_id[page.id] = page_items

    return _StaticEnvironmentCollection(
        items_by_page_id=items_by_page_id,
        prepared_bodies_by_page_id=static_environment_prepared_bodies_by_page_id,
    )


def _render_page(
    *,
    page: ContentPage,
    body: str,
    numbered_objects: NumberedObjectRenderContext,
    proofs: StaticEnvironmentRenderContext,
    content_model: ContentModel,
    pages_by_source: dict[Path, ContentPage],
    pages_by_reference: dict[str, ContentPage],
    course_root: Path,
    source_dir: Path,
    course_title: str,
    language: str,
    official_counts: dict[str, dict[str, int]],
    official_objects: list[dict[str, Any]],
    page_references: list[SourceReference],
    reviewed_by_reference: dict[str, ReviewedOutput],
    report: ValidationReport,
    math_renderer: MathRenderer,
    skin_context: SkinContext,
    page_graph_context: dict[str, list[dict[str, str]]],
    wikilink_resolver: WikilinkResolver,
) -> tuple[str, dict[str, str]]:
    breadcrumbs = _render_breadcrumbs(page, content_model)
    generated_index = _render_generated_index(
        page,
        content_model,
        official_counts,
    )
    stylesheet_href = _relative_href(page.output_path, RENDER_STYLESHEET_PATH)
    skin_id = skin_id_for_source_path(page.source_path, skin_context)
    skin_stylesheet_href = _relative_href(page.output_path, SKIN_STYLESHEET_PATH)
    skin_prepaint_js_href = _relative_href(
        page.output_path,
        Path(SKIN_STYLESHEET_PATH).parent / SKIN_PREPAINT_JS_NAME,
    )
    skin_toggle_js_href = _relative_href(
        page.output_path,
        Path(SKIN_STYLESHEET_PATH).parent / SKIN_TOGGLE_JS_NAME,
    )
    accessibility_css_href = _relative_href(
        page.output_path,
        f"{ACCESSIBILITY_RESOURCE_PATH}/{OPEN_DYSLEXIC_CSS_NAME}",
    )
    comfort_prepaint_js_href = _relative_href(
        page.output_path,
        f"{ACCESSIBILITY_RESOURCE_PATH}/{COMFORT_PREPAINT_JS_NAME}",
    )
    accessibility_js_href = _relative_href(
        page.output_path,
        f"{ACCESSIBILITY_RESOURCE_PATH}/{OPEN_DYSLEXIC_JS_NAME}",
    )
    shell_js_href = _relative_href(
        page.output_path,
        Path(SHELL_RESOURCE_PATH) / SHELL_SCRIPT_NAME,
    )
    search_href = _href_with_query(
        _relative_href(page.output_path, STATIC_SEARCH_PATH.as_posix()),
        {"q": page.title},
    )
    graph_href = _href_with_query(
        _relative_href(page.output_path, STATIC_GRAPH_PATH.as_posix()),
        {"page": page.id},
    )
    direct_official_count = sum(official_counts.get(page.id, {}).values())
    practice_href = _relative_href(page.output_path, STATIC_PRACTICE_PATH.as_posix())
    course_map_practice_href = practice_href
    if direct_official_count:
        course_map_practice_href = _href_with_query(
            course_map_practice_href,
            {"page": page.id},
        )
    tasks_href = _relative_href(page.output_path, STATIC_TASKS_PATH.as_posix())
    schedule_href = _relative_href(page.output_path, STATIC_SCHEDULE_PATH.as_posix())
    math_stylesheet_href = _relative_href(
        page.output_path,
        MATH_STYLESHEET_PATH.as_posix(),
    )
    reference_panel = _render_reference_panel(
        page, page_references, reviewed_by_reference
    )
    reviewed_output_panel = _render_reviewed_output_panel(
        page,
        [
            reviewed_by_reference[reference.id]
            for reference in page_references
            if reference.id in reviewed_by_reference
        ],
    )
    support_panels = "\n".join(
        panel for panel in (reference_panel, reviewed_output_panel) if panel
    )
    article_html = render_markdown_body(
        body,
        generated_index=generated_index,
        resolve_href=lambda href: _resolve_markdown_href(
            page,
            href,
            pages_by_source,
            pages_by_reference,
            numbered_objects.objects_by_id,
            course_root,
            source_dir,
            report,
        ),
        source_path=page.source_path,
        report=report,
        math_renderer=math_renderer,
        numbered_objects=numbered_objects,
        proofs=proofs,
        resolve_wikilink=lambda target: _resolve_wikilink_page_id(
            target,
            wikilink_resolver,
        ),
    )
    article_html, toc_html = _extract_page_toc(article_html)
    public_article_text = _public_article_search_text(article_html)
    public_sections = _public_article_search_sections(article_html, page_id=page.id)
    estimated_reading_time = _page_reading_time(
        page,
        public_article_text,
        content_model,
    )
    search_record = {
        "id": page.id,
        "search_text": public_article_text,
        "search_snippet": _public_search_snippet(public_article_text),
        "sections": public_sections,
    }
    article_connections_html = _render_article_connections(
        page,
        page_graph_context,
        graph_href,
    )
    official_practice_html = _render_official_practice_section(
        official_objects,
        practice_href=course_map_practice_href,
    )
    page_brief_html = _render_page_brief(
        page,
        content_model,
        _renderable_official_object_count(official_objects),
        page_graph_context,
        graph_href,
        estimated_reading_time,
    )
    learning_rail = _render_learning_rail(
        page,
        toc_html,
        public_sections,
        content_model,
        support_panels,
        page_graph_context,
        estimated_reading_time,
    )
    leading_heading_html, article_body_html = _split_leading_h1(article_html)

    rendered_page = "\n".join(
        [
            "<!doctype html>",
            (
                f'<html lang="{html.escape(language)}" '
                'data-raya-course-map="expanded" '
                'data-raya-course-map-drawer="closed">'
            ),
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{html.escape(page.title)} - {html.escape(course_title)}</title>",
            f'<script src="{html.escape(comfort_prepaint_js_href)}"></script>',
            f'<script src="{html.escape(skin_prepaint_js_href)}"></script>',
            f'<link rel="stylesheet" href="{html.escape(stylesheet_href)}">',
            f'<link rel="stylesheet" href="{html.escape(skin_stylesheet_href)}">',
            f'<link rel="stylesheet" href="{html.escape(accessibility_css_href)}">',
            f'<link rel="stylesheet" href="{html.escape(math_stylesheet_href)}">',
            "</head>",
            (
                f'<body data-raya-surface="{SURFACE_STUDENT_DEFAULT}" '
                f'data-raya-skin="{html.escape(skin_id, quote=True)}">'
            ),
            '<a class="raya-skip-link" href="#raya-article">Skip to content</a>',
            _render_top_command_bar(
                course_title,
                page,
                content_model,
                toc_html,
                search_href,
                graph_href,
                practice_href,
                tasks_href,
                schedule_href,
                skin_context,
            ),
            '<main id="raya-content" class="raya-learning-shell" data-raya-course-map="expanded">',
            _render_course_map(
                page,
                content_model,
                search_href=search_href,
                graph_href=graph_href,
                practice_href=course_map_practice_href,
                tasks_href=tasks_href,
                schedule_href=schedule_href,
                official_counts=official_counts,
                official_objects=official_objects,
                page_graph_context=page_graph_context,
            ),
            '<article id="raya-article" class="raya-main-article" tabindex="-1">',
            _render_article_sequence_nav(page, content_model),
            breadcrumbs,
            leading_heading_html,
            page_brief_html,
            article_body_html,
            article_connections_html,
            official_practice_html,
            _render_article_sequence_cards(page, content_model),
            "</article>",
            learning_rail,
            "</main>",
            f'<script src="{html.escape(accessibility_js_href)}" defer></script>',
            f'<script src="{html.escape(shell_js_href)}" defer></script>',
            f'<script src="{html.escape(skin_toggle_js_href)}" defer></script>',
            "</body>",
            "</html>",
            "",
        ]
    )
    return rendered_page, search_record


def _split_leading_h1(article_html: str) -> tuple[str, str]:
    match = re.match(r"(?s)^(\s*<h1\b[^>]*>.*?</h1>)(.*)$", article_html)
    if match is None:
        return "", article_html
    return match.group(1), match.group(2)


def _render_top_command_bar(
    course_title: str,
    page: ContentPage,
    content_model: ContentModel,
    toc_html: str,
    search_href: str,
    graph_href: str,
    practice_href: str,
    tasks_href: str,
    schedule_href: str,
    skin_context: SkinContext,
) -> str:
    return "\n".join(
        [
            '<header class="raya-top-command-bar" aria-label="Course tools">',
            '<div class="raya-top-command-bar-inner">',
            _render_reading_context(course_title, page, content_model, toc_html),
            '<div class="raya-course-tools">',
            (
                '<div class="raya-command-group raya-command-group-discovery" '
                'data-raya-command-group="discovery" '
                'role="group" '
                'aria-label="Discovery workspaces">'
            ),
            _render_command_search_form(search_href),
            _render_command_link(
                class_name="raya-command raya-command-search",
                href=search_href,
                aria_label="Open course search",
                icon="search",
                label="Search",
            ),
            _render_command_link(
                class_name="raya-command raya-command-graph",
                href=graph_href,
                aria_label="Open course graph",
                icon="graph",
                label="Graph",
            ),
            _render_command_link(
                class_name="raya-command raya-command-practice",
                href=practice_href,
                aria_label="Open official practice",
                icon="practice",
                label="Practice",
            ),
            _render_command_link(
                class_name="raya-command raya-command-tasks",
                href=tasks_href,
                aria_label="Open official tasks",
                icon="tasks",
                label="Tasks",
            ),
            _render_command_link(
                class_name="raya-command raya-command-schedule",
                href=schedule_href,
                aria_label="Open official schedule",
                icon="schedule",
                label="Schedule",
            ),
            "</div>",
            (
                '<div class="raya-command-group raya-command-group-layout" '
                'data-raya-command-group="layout" '
                'role="group" '
                'aria-label="Reader layout">'
            ),
            _render_course_map_toggle(
                "Course map",
                class_name="raya-command raya-command-map raya-course-map-toggle",
                aria_label="Collapse course map",
                icon="map",
            ),
            _render_command_button(
                class_name="raya-command raya-command-focus",
                aria_label="Focus reading",
                icon="focus",
                label="Focus reading",
                aria_pressed="false",
                extra_attrs=" data-raya-reader-focus-toggle",
            ),
            _render_command_button(
                class_name="raya-command raya-command-context",
                aria_label="Hide learning context",
                icon="context",
                label="Context",
                extra_attrs=(
                    " data-raya-learning-rail-toggle "
                    'aria-controls="raya-learning-rail-body" '
                    'aria-expanded="true"'
                ),
            ),
            "</div>",
            (
                '<div class="raya-command-group raya-command-group-comfort" '
                'data-raya-command-group="comfort" '
                'role="group" '
                'aria-label="Reading comfort">'
            ),
            _render_command_button(
                class_name="raya-command raya-command-size raya-text-size-toggle",
                aria_label="Text size: normal",
                icon="text-size",
                label="Text size",
                aria_pressed="false",
            ),
            _render_command_button(
                class_name="raya-command raya-command-font raya-font-toggle",
                aria_label="Toggle OpenDyslexic font",
                icon="font",
                label="OpenDyslexic",
                aria_pressed="false",
            ),
            _render_skin_toggle_command(skin_context),
            "</div>",
            "</div>",
            "</div>",
            "</header>",
        ]
    )


def _render_skin_toggle_command(skin_context: SkinContext) -> str:
    entries = [("", "authored"), *skin_cycle_entries(skin_context)]
    cycle = [skin_id for skin_id, _label in entries]
    labels = {skin_id: label for skin_id, label in entries}
    extra_attrs = (
        " data-raya-skin-toggle "
        f"data-raya-skin-cycle='{html.escape(json.dumps(cycle), quote=True)}' "
        f"data-raya-skin-labels='{html.escape(json.dumps(labels), quote=True)}' "
        'data-raya-skin-active="authored"'
    )
    return _render_command_button(
        class_name="raya-command raya-command-skin raya-skin-toggle",
        aria_label="Skin: authored",
        icon="skin",
        label="Skin",
        aria_pressed="false",
        extra_attrs=extra_attrs,
    )


def _render_command_search_form(search_href: str) -> str:
    parsed_href = urlsplit(search_href)
    form_action = urlunsplit(
        (
            parsed_href.scheme,
            parsed_href.netloc,
            parsed_href.path,
            "",
            "",
        )
    )
    return (
        '<form class="raya-command-search-form" '
        f'action="{html.escape(form_action, quote=True)}" method="get" role="search">'
        '<label class="raya-visually-hidden" for="raya-command-search-input">'
        "Search course text"
        "</label>"
        '<input id="raya-command-search-input" class="raya-command-search-input" '
        'type="search" name="q" placeholder="Search course" autocomplete="off" '
        'aria-label="Search course text">'
        '<button class="raya-command-search-submit" type="submit" '
        'aria-label="Open search results">'
        '<span aria-hidden="true">Go</span>'
        "</button>"
        "</form>"
    )


def _render_discovery_command_bar(
    *,
    course_title: str,
    workspace_label: str,
    current_workspace: str,
    home_href: str,
    search_href: str | None,
    graph_href: str | None,
    practice_href: str | None,
    tasks_href: str | None,
    schedule_href: str | None,
) -> str:
    commands = [
        _render_command_link(
            class_name="raya-command raya-command-home",
            href=home_href,
            aria_label="Back to course",
            icon="home",
            label="Course",
        )
    ]

    def workspace_command(
        *,
        kind: str,
        href: str,
        aria_label: str,
        icon: str,
        label: str,
    ) -> str:
        attrs = (
            {"aria-current": "page", "data-raya-current-workspace": kind}
            if current_workspace == kind
            else None
        )
        return _render_command_link(
            class_name=f"raya-command raya-command-{kind}",
            href=href,
            aria_label=aria_label,
            icon=icon,
            label=label,
            attrs=attrs,
        )

    if search_href is not None:
        commands.append(
            workspace_command(
                kind="search",
                href=search_href,
                aria_label="Open course search",
                icon="search",
                label="Search",
            )
        )
    if graph_href is not None:
        commands.append(
            workspace_command(
                kind="graph",
                href=graph_href,
                aria_label="Open course graph",
                icon="graph",
                label="Graph",
            )
        )
    if practice_href is not None:
        commands.append(
            workspace_command(
                kind="practice",
                href=practice_href,
                aria_label="Open official practice",
                icon="practice",
                label="Practice",
            )
        )
    if tasks_href is not None:
        commands.append(
            workspace_command(
                kind="tasks",
                href=tasks_href,
                aria_label="Open official tasks",
                icon="tasks",
                label="Tasks",
            )
        )
    if schedule_href is not None:
        commands.append(
            workspace_command(
                kind="schedule",
                href=schedule_href,
                aria_label="Open official schedule",
                icon="schedule",
                label="Schedule",
            )
        )
    commands.extend(
        [
            _render_command_button(
                class_name="raya-command raya-command-size raya-text-size-toggle",
                aria_label="Text size: normal",
                icon="text-size",
                label="Text size",
                aria_pressed="false",
            ),
            _render_command_button(
                class_name="raya-command raya-command-font raya-font-toggle",
                aria_label="Toggle OpenDyslexic font",
                icon="font",
                label="OpenDyslexic",
                aria_pressed="false",
            ),
        ]
    )
    return "\n".join(
        [
            (
                '<header class="raya-top-command-bar raya-discovery-command-bar" '
                'aria-label="Course discovery tools">'
            ),
            '<div class="raya-top-command-bar-inner">',
            '<div class="raya-reading-context">',
            f'<span class="raya-reading-context-course">{html.escape(course_title)}</span>',
            '<span class="raya-reading-context-separator" aria-hidden="true">/</span>',
            f'<span class="raya-reading-context-page">{html.escape(workspace_label)}</span>',
            "</div>",
            '<div class="raya-course-tools">',
            "\n".join(commands),
            "</div>",
            "</div>",
            "</header>",
        ]
    )


def _discovery_workspace_entries(
    *,
    current_workspace: str,
    page_count: int,
    graph_link_count: int,
    official_count: int,
    task_count: int,
    dated_count: int,
) -> list[dict[str, str]]:
    entries = [
        ("search", "Search", "../search/index.html", f"{page_count} pages"),
        ("graph", "Graph", "../graph/index.html", f"{graph_link_count} links"),
        ("practice", "Practice", "../practice/index.html", f"{official_count} official"),
        ("tasks", "Tasks", "../tasks/index.html", f"{task_count} tasks"),
        ("schedule", "Schedule", "../schedule/index.html", f"{dated_count} dated"),
    ]
    return [
        {
            "badge": badge,
            "href": href,
            "kind": kind,
            "label": label,
        }
        for kind, label, href, badge in entries
    ]


def _render_discovery_course_rail(
    *,
    content_model: ContentModel,
    course_title: str,
    current_workspace: str,
    from_path: str,
    graph_index: dict[str, Any] | None = None,
    official_by_page: dict[str, list[dict[str, Any]]] | None = None,
) -> str:
    official_pages = official_by_page or {}
    official_objects = [
        item for page_items in official_pages.values() for item in page_items
    ]
    task_family = {"assignment", "exam", "project", "task"}
    task_objects = [
        item for item in official_objects if str(item.get("type") or "") in task_family
    ]
    dated_count = 0
    for item in task_objects:
        content = item.get("content")
        if isinstance(content, dict) and (content.get("due") or content.get("available")):
            dated_count += 1
    page_focus_handoffs = "\n".join(
        [
            (
            '<a data-raya-discovery-rail-page-handoff="search" '
            f'data-raya-handoff-base="{html.escape(_relative_href(from_path, "../search/index.html"), quote=True)}" '
            'href="#">Search</a>'
            ),
            (
            '<a data-raya-discovery-rail-page-handoff="graph" '
            f'data-raya-handoff-base="{html.escape(_relative_href(from_path, "../graph/index.html"), quote=True)}" '
            'href="#">Graph</a>'
            ),
            (
            '<a data-raya-discovery-rail-page-handoff="practice" '
            f'data-raya-handoff-base="{html.escape(_relative_href(from_path, "../practice/index.html"), quote=True)}" '
            'href="#">Practice</a>'
            ),
            (
            '<a data-raya-discovery-rail-page-handoff="tasks" '
            f'data-raya-handoff-base="{html.escape(_relative_href(from_path, "../tasks/index.html"), quote=True)}" '
            'href="#">Tasks</a>'
            ),
            (
            '<a data-raya-discovery-rail-page-handoff="schedule" '
            f'data-raya-handoff-base="{html.escape(_relative_href(from_path, "../schedule/index.html"), quote=True)}" '
            'href="#">Schedule</a>'
            ),
        ]
    )
    page_links = "\n".join(
        (
            "<li>"
            '<a class="raya-discovery-course-page-link" '
            f'data-raya-discovery-course-page="{html.escape(page.id, quote=True)}" '
            f'href="{html.escape(_relative_href(from_path, page.output_path), quote=True)}">'
            f"<span>{html.escape(page.display_label or '')}</span>"
            f"<strong>{html.escape(page.title)}</strong>"
            "</a>"
            "</li>"
        )
        for page in content_model.pages[:18]
    )
    workspace_links = "\n".join(
        (
            '<a class="raya-discovery-workspace-link" '
            f'data-raya-workspace-link="{html.escape(entry["kind"], quote=True)}" '
            f'href="{html.escape(_relative_href(from_path, entry["href"]), quote=True)}"'
            + (' aria-current="page"' if current_workspace == entry["kind"] else "")
            + ">"
            f"<span>{html.escape(entry['label'])}</span>"
            f"<em>{html.escape(entry['badge'])}</em>"
            "</a>"
        )
        for entry in _discovery_workspace_entries(
            current_workspace=current_workspace,
            page_count=len(content_model.pages),
            graph_link_count=len((graph_index or {}).get("edges", [])),
            official_count=len(official_objects),
            task_count=len(task_objects),
            dated_count=dated_count,
        )
    )
    return "\n".join(
        [
            (
                '<aside class="raya-discovery-course-rail" '
                'data-raya-discovery-course-rail aria-label="Course workspace">'
            ),
            (
                '<button class="raya-discovery-course-tab" type="button" '
                'data-raya-discovery-toggle-rail '
                'aria-controls="raya-discovery-course-rail-body" '
                'aria-expanded="true" '
                'aria-label="Collapse course workspace">Course</button>'
            ),
            (
                '<div id="raya-discovery-course-rail-body" '
                'class="raya-discovery-course-rail-body" '
                'data-raya-discovery-course-rail-body aria-hidden="false">'
            ),
            '<div class="raya-discovery-course-identity">',
            f"<h2>{html.escape(course_title)}</h2>",
            (
                f'<a href="{html.escape(_relative_href(from_path, "index.html"), quote=True)}">'
                "Back to course</a>"
            ),
            "</div>",
            '<nav class="raya-discovery-workspace-links" aria-label="Discovery workspaces">',
            workspace_links,
            "</nav>",
            (
                '<section class="raya-discovery-rail-page-focus" '
                'data-raya-discovery-rail-page-focus hidden aria-live="polite">'
            ),
            "<h3>Focused page</h3>",
            "<p data-raya-discovery-rail-page-focus-title></p>",
            (
                '<p class="raya-discovery-rail-page-handoffs" '
                'data-raya-discovery-rail-page-handoffs>'
            ),
            page_focus_handoffs,
            "</p>",
            "</section>",
            '<nav class="raya-discovery-course-pages" aria-label="Course pages">',
            "<h3>Course pages</h3>",
            f"<ol>{page_links}</ol>",
            "</nav>",
            "</div>",
            "</aside>",
        ]
    )


def _render_discovery_overview(
    *,
    kind: str,
    title: str,
    summary: str,
    meta: list[tuple[str, str]],
    actions: list[tuple[str, str]],
) -> str:
    meta_html = "\n".join(
        [
            "<div>"
            f"<dt>{html.escape(label)}</dt>"
            f"<dd>{html.escape(value)}</dd>"
            "</div>"
            for label, value in meta
        ]
    )
    action_html = "\n".join(
        [
            (
                f'<a href="{html.escape(href, quote=True)}">'
                f"{html.escape(label)}</a>"
            )
            for label, href in actions
        ]
    )
    return "\n".join(
        [
            (
                '<section class="raya-discovery-overview" '
                f'data-raya-discovery-overview="{html.escape(kind, quote=True)}" '
                f'aria-label="{html.escape(title, quote=True)} overview">'
            ),
            '<div class="raya-discovery-overview-main">',
            f"<h2>{html.escape(title)}</h2>",
            f"<p>{html.escape(summary)}</p>",
            "</div>",
            '<dl class="raya-discovery-overview-meta">',
            meta_html,
            "</dl>",
            (
                '<nav class="raya-discovery-overview-actions" '
                'aria-label="Related discovery workspaces">'
            ),
            action_html,
            "</nav>",
            "</section>",
        ]
    )


def _render_discovery_quick_guide(
    *,
    kind: str,
    cards: list[tuple[str, str]],
) -> str:
    card_html = "\n".join(
        [
            (
                '<article class="raya-discovery-guide-card">'
                f"<h3>{html.escape(label)}</h3>"
                f"<p>{html.escape(text)}</p>"
                "</article>"
            )
            for label, text in cards
        ]
    )
    return "\n".join(
        [
            (
                '<details class="raya-discovery-quick-guide" '
                f'data-raya-discovery-guide="{html.escape(kind, quote=True)}" '
                'aria-label="Workspace quick guide">'
            ),
            "<summary>Quick guide</summary>",
            '<div class="raya-discovery-guide-cards">',
            card_html,
            "</div>",
            "</details>",
        ]
    )


def _render_reading_context(
    course_title: str,
    page: ContentPage,
    content_model: ContentModel,
    toc_html: str = "",
) -> str:
    position = _page_position(page, content_model)
    sequence = _reading_context_sequence_links(page, content_model)
    section = _reading_context_section_link(toc_html)
    sequence_html = (
        '<nav class="raya-reading-context-sequence" '
        'aria-label="Compact previous and next pages">' + sequence + "</nav>"
        if sequence
        else ""
    )
    parts = [
        '<div class="raya-reading-context" aria-label="Current reading position">'
        f'<span class="raya-reading-context-course">{html.escape(course_title)}</span>',
        '<span class="raya-reading-context-separator">/</span>',
        f'<span class="raya-reading-context-page">{html.escape(page.nav_title or page.title)}</span>',
        '<span class="raya-reading-context-separator">/</span>',
        f'<span class="raya-reading-context-position">{html.escape(position)}</span>',
    ]
    if section:
        section_href, section_label = section
        parts.extend(
            [
                '<span class="raya-reading-context-separator">/</span>',
                (
                    '<a class="raya-reading-context-link '
                    'raya-reading-context-section" '
                    'data-raya-current-section-link '
                    f'href="{html.escape(section_href, quote=True)}" '
                    f'aria-label="Current section: {html.escape(section_label, quote=True)}">'
                    '<span class="raya-reading-context-section-kicker">Now</span> '
                    '<span class="raya-reading-context-section-label">'
                    f"{html.escape(section_label)}</span>"
                    "</a>"
                ),
            ]
        )
    if sequence_html:
        parts.append('<span class="raya-reading-context-separator">/</span>')
        parts.append(sequence_html)
    parts.append("</div>")
    return "".join(parts)


def _reading_context_section_link(toc_html: str) -> tuple[str, str] | None:
    match = re.search(r'<a href="([^"]+)">([^<]+)</a>', toc_html)
    if match is None:
        return None
    href = html.unescape(match.group(1))
    if href.startswith("#raya-generated-"):
        return None
    label = html.unescape(match.group(2)).strip() or "Current section"
    return href, label


def _reading_context_sequence_links(
    page: ContentPage,
    content_model: ContentModel,
) -> str:
    pages = content_model.pages
    current_index = next(
        (
            index
            for index, target in enumerate(pages)
            if target.output_path == page.output_path
        ),
        None,
    )
    if current_index is None:
        return ""
    links: list[str] = []
    if current_index > 0:
        previous = pages[current_index - 1]
        title = previous.nav_title or previous.title
        href = _relative_href(page.output_path, previous.output_path)
        links.append(
            '<a class="raya-reading-context-link raya-reading-context-prev" '
            f'href="{html.escape(href)}" '
            'aria-keyshortcuts="ArrowLeft" '
            f'aria-label="Previous page: {html.escape(title, quote=True)}">'
            "Previous</a>"
        )
    if current_index + 1 < len(pages):
        next_page = pages[current_index + 1]
        title = next_page.nav_title or next_page.title
        href = _relative_href(page.output_path, next_page.output_path)
        links.append(
            '<a class="raya-reading-context-link raya-reading-context-next" '
            f'href="{html.escape(href)}" '
            'aria-keyshortcuts="ArrowRight" '
            f'aria-label="Next page: {html.escape(title, quote=True)}">'
            "Next</a>"
        )
    return "\n".join(links)


def _page_position(page: ContentPage, content_model: ContentModel) -> str:
    for index, target in enumerate(content_model.pages, start=1):
        if target.id == page.id:
            return f"Page {index} of {len(content_model.pages)}"
    return ""


def _render_course_map_toggle(
    label: str = "Course map",
    expanded: bool = True,
    *,
    class_name: str = "raya-course-map-toggle",
    aria_label: str | None = None,
    icon: str | None = None,
) -> str:
    aria_expanded = "true" if expanded else "false"
    aria_label_attr = (
        f' aria-label="{html.escape(aria_label, quote=True)}"' if aria_label else ""
    )
    label_markup = html.escape(label)
    if icon is not None:
        label_markup = (
            f"{_command_icon(icon)}"
            f'<span class="raya-command-label">{html.escape(label)}</span>'
        )
    return (
        f'<button class="{html.escape(class_name, quote=True)}" type="button" '
        "data-raya-course-map-toggle "
        'aria-controls="raya-course-map" '
        f'aria-expanded="{aria_expanded}"{aria_label_attr}>'
        f"{label_markup}"
        "</button>"
    )


def _safe_map_fragment_id(value: str) -> str:
    fragment = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-")
    return fragment or "course-map-node"


def _render_course_map(
    page: ContentPage,
    content_model: ContentModel,
    *,
    search_href: str,
    graph_href: str,
    practice_href: str,
    tasks_href: str,
    schedule_href: str,
    official_counts: dict[str, dict[str, int]],
    official_objects: list[dict[str, Any]],
    page_graph_context: dict[str, list[dict[str, str]]],
) -> str:
    active_path = {crumb.id for crumb in _breadcrumb_pages(page, content_model)}
    active_path.add(page.id)
    sequence_index = {
        target.id: index for index, target in enumerate(content_model.pages, start=1)
    }

    def render_node(target: ContentPage, depth: int) -> str:
        child_ids = content_model.children_by_parent.get(target.id, [])
        child_pages = [
            content_model.pages_by_id[child_id]
            for child_id in child_ids
            if child_id in content_model.pages_by_id
        ]
        href = _relative_href(page.output_path, target.output_path)
        label = _navigation_label(target)
        active_state = (
            "current"
            if target.id == page.id
            else "ancestor"
            if target.id in active_path
            else "inactive"
        )
        expanded = bool(child_pages) and target.id in active_path
        node_id = (
            f"raya-map-children-{sequence_index[target.id]}-"
            f"{_safe_map_fragment_id(target.id)}"
        )
        current = (
            ' aria-current="page"' if target.output_path == page.output_path else ""
        )
        parent = (
            f'data-raya-map-parent="{html.escape(target.parent_id, quote=True)}" '
            if target.parent_id
            else ""
        )
        toggle = ""
        children = ""
        if child_pages:
            toggle = (
                '<button class="raya-course-map-node-toggle" type="button" '
                "data-raya-map-node-toggle "
                f'aria-controls="{html.escape(node_id, quote=True)}" '
                f'aria-expanded="{"true" if expanded else "false"}" '
                f'aria-label="Toggle {html.escape(label, quote=True)}">'
                "</button>"
            )
            children = "\n".join(render_node(child, depth + 1) for child in child_pages)
            children = (
                f'<ol id="{html.escape(node_id, quote=True)}" '
                "data-raya-map-children "
                f"{'hidden ' if not expanded else ''}"
                f'aria-hidden="{"false" if expanded else "true"}">'
                f"{children}"
                "</ol>"
            )
        else:
            toggle = (
                '<span class="raya-course-map-node-spacer" aria-hidden="true"></span>'
            )
        return "\n".join(
            [
                (
                    '<li class="raya-course-map-node" '
                    f'data-raya-map-node="{html.escape(target.id, quote=True)}" '
                    f"{parent}"
                    f'data-raya-map-depth="{depth}" '
                    f'data-raya-map-active="{active_state}" '
                    f'data-raya-map-expanded="{"true" if expanded else "false"}">'
                ),
                (
                    '<div class="raya-course-map-node-row" '
                    f'data-raya-map-label="{html.escape(label, quote=True)}">'
                ),
                toggle,
                (
                    "<a "
                    f'href="{html.escape(href)}"{current} '
                    f'data-raya-map-index="{sequence_index[target.id]}" '
                    f'data-raya-map-label="{html.escape(label, quote=True)}">'
                    f"{html.escape(label)}"
                    "</a>"
                ),
                "</div>",
                children,
                "</li>",
            ]
        )

    root_ids = (
        [content_model.root_id]
        if content_model.root_id and content_model.root_id in content_model.pages_by_id
        else content_model.children_by_parent.get(None, [])
    )
    nav_items = [
        render_node(content_model.pages_by_id[root_id], 0)
        for root_id in root_ids
        if root_id in content_model.pages_by_id
    ]
    position = html.escape(_page_position(page, content_model))
    current_map_label = html.escape(page.title or page.nav_title or _navigation_label(page))
    direct_official_count = sum(official_counts.get(page.id, {}).values())
    direct_task_count = sum(
        1
        for item in official_objects
        if _official_public_task_summary(item) is not None
    )
    direct_dated_task_count = sum(
        1
        for item in official_objects
        if _official_public_task_summary(item) is not None
        and _official_task_event_date(item)
    )
    outgoing_link_count = len(page_graph_context.get("outgoing", []))
    incoming_link_count = len(page_graph_context.get("incoming", []))
    direct_link_count = outgoing_link_count + incoming_link_count
    graph_detail_badges = [
        (
            f"{outgoing_link_count} "
            f'{_relationship_count_label(outgoing_link_count, "from this page", "from this page")}'
        ),
        (
            f"{incoming_link_count} "
            f'{_relationship_count_label(incoming_link_count, "links here", "link here")}'
        ),
    ]
    course_map_tasks_href = tasks_href
    if direct_task_count:
        course_map_tasks_href = _href_with_query(
            course_map_tasks_href,
            {"page": page.id},
        )
    course_map_schedule_href = schedule_href
    if direct_dated_task_count:
        course_map_schedule_href = _href_with_query(
            course_map_schedule_href,
            {"page": page.id},
        )
    workspace_links = [
        ("search", "Search", search_href, "Course", []),
        (
            "graph",
            "Graph",
            graph_href,
            _count_label(direct_link_count, "link"),
            graph_detail_badges,
        ),
        (
            "practice",
            "Practice",
            practice_href,
            f"{direct_official_count} official"
            if direct_official_count
            else "Course",
            [],
        ),
        (
            "tasks",
            "Tasks",
            course_map_tasks_href,
            _count_label(direct_task_count, "task") if direct_task_count else "Course",
            [],
        ),
        (
            "schedule",
            "Schedule",
            course_map_schedule_href,
            f"{direct_dated_task_count} dated" if direct_dated_task_count else "Course",
            [],
        ),
    ]

    def render_workspace_link(
        kind: str,
        label: str,
        href: str,
        badge: str,
        details: list[str],
    ) -> str:
        detail_html = ""
        if details:
            detail_html = (
                '<span class="raya-course-map-workspace-details">'
                + "".join(
                    (
                        '<span class="raya-course-map-workspace-detail" '
                        "data-raya-course-map-workspace-detail>"
                        f"{html.escape(detail)}"
                        "</span>"
                    )
                    for detail in details
                )
                + "</span>"
            )
        aria_detail = html.escape(", ".join([badge, *details]), quote=True)
        return "\n".join(
            [
                (
                    f'<a class="raya-course-map-workspace-link '
                    f'raya-course-map-workspace-{html.escape(kind, quote=True)}" '
                    "data-raya-course-map-workspace-link "
                    f'href="{html.escape(href)}" '
                    f'aria-label="{html.escape(label, quote=True)} workspace, {aria_detail}">'
                ),
                '<span class="raya-course-map-workspace-label">'
                f"{html.escape(label)}"
                "</span>",
                '<span class="raya-course-map-workspace-badge">'
                f"{html.escape(badge)}"
                "</span>",
                detail_html,
                "</a>",
            ]
        )

    workspace_html = "\n".join(
        [
            '<section class="raya-course-map-workspaces" '
            'aria-label="Course workspaces" data-raya-course-map-workspaces>',
            '<p class="raya-course-map-workspaces-label">Course workspaces</p>',
            '<div class="raya-course-map-workspace-links">',
            "\n".join(
                render_workspace_link(
                    kind,
                    label,
                    href,
                    badge,
                    details,
                )
                for kind, label, href, badge, details in workspace_links
            ),
            "</div>",
            "</section>",
        ]
    )
    return "\n".join(
        [
            '<nav id="raya-course-map" class="raya-course-map" aria-label="Course map" data-raya-course-map="expanded">',
            '<div class="raya-course-map-header">',
            '<div class="raya-course-map-drawer-chrome">',
            '<span class="raya-course-map-drawer-grip" aria-hidden="true"></span>',
            '<p class="raya-course-map-drawer-title">Course map</p>',
            f'<p class="raya-course-map-drawer-position">{position}</p>'
            if position
            else "",
            "</div>",
            '<p class="raya-region-title">Course map</p>',
            f'<p class="raya-page-position">{position}</p>' if position else "",
            (
                '<button class="raya-course-map-close" type="button" '
                'data-raya-course-map-close aria-label="Close course map">'
                "Close</button>"
            ),
            _render_course_map_toggle("Collapse map"),
            "</div>",
            (
                '<p class="raya-course-map-current-chip" '
                "data-raya-course-map-current-chip "
                f'aria-label="Current page: {current_map_label}">'
                f"{current_map_label}"
                "</p>"
            ),
            workspace_html,
            '<div class="raya-course-map-actions" role="group" aria-label="Course map section controls">',
            '<button type="button" data-raya-course-map-action="current">Current</button>',
            '<button type="button" data-raya-course-map-action="expand-all">All</button>',
            (
                '<button type="button" data-raya-course-map-action="scan" '
                'aria-pressed="false" aria-label="Scan course map branches">'
                "Scan</button>"
            ),
            '<button type="button" data-raya-course-map-action="less">Less</button>',
            "</div>",
            '<label class="raya-course-map-filter-label" for="raya-course-map-filter">Filter map</label>',
            (
                '<input id="raya-course-map-filter" '
                'class="raya-course-map-filter" type="search" autocomplete="off" '
                "data-raya-course-map-filter>"
            ),
            '<p class="raya-map-filter-empty" data-raya-map-filter-empty hidden>No map matches.</p>',
            '<div class="raya-course-map-list" id="raya-course-map-list" aria-hidden="false">',
            "<ol>",
            "\n".join(nav_items),
            "</ol>",
            "</div>",
            (
                '<div class="raya-course-map-compact-preview" '
                'data-raya-course-map-compact-preview aria-hidden="true" hidden></div>'
            ),
            "</nav>",
            (
                '<div class="raya-course-map-drawer-backdrop" '
                'data-raya-course-map-drawer-backdrop hidden></div>'
            ),
        ]
    )


def _render_learning_rail(
    page: ContentPage,
    toc_html: str,
    public_sections: list[dict[str, str]],
    content_model: ContentModel,
    support_panels: str,
    page_graph_context: dict[str, list[dict[str, str]]],
    estimated_reading_time: tuple[str, str] | None,
) -> str:
    graph_href = _href_with_query(
        _relative_href(page.output_path, STATIC_GRAPH_PATH.as_posix()),
        {"page": page.id},
    )
    reading_flow = _render_reading_flow_rail(
        page,
        content_model,
        page_graph_context,
        graph_href,
    )
    panels = [
        _render_current_section_rail(toc_html),
        _render_page_contents_rail(toc_html, public_sections),
        reading_flow,
        _render_page_summary_rail(page),
        _render_page_status_rail(page),
        _render_estimated_time_rail(estimated_reading_time),
        _render_tags_rail(page),
        _render_prerequisites_rail(page, content_model),
        "" if reading_flow else _render_linked_pages_rail(page, page_graph_context),
        "" if reading_flow else _render_sequence_rail(page, content_model),
        support_panels,
    ]
    body = "\n".join(panel for panel in panels if panel)
    if not body:
        return ""
    context_chip = _render_learning_rail_context_chip(page)
    return "\n".join(
        [
            (
                '<aside id="raya-learning-rail" class="raya-learning-rail" '
                'aria-label="Learning context" data-raya-learning-rail="expanded">'
            ),
            '<div class="raya-learning-rail-header">',
            '<p class="raya-region-title">Learning context</p>',
            (
                '<button class="raya-learning-rail-collapse" type="button" '
                "data-raya-learning-rail-collapse "
                'aria-controls="raya-learning-rail-body" '
                'aria-expanded="true" '
                'aria-label="Hide learning context">Hide context</button>'
            ),
            "</div>",
            '<div id="raya-learning-rail-body" class="raya-learning-rail-body" aria-hidden="false">',
            body,
            "</div>",
            context_chip,
            (
                '<button class="raya-learning-rail-expand" type="button" '
                "data-raya-learning-rail-expand "
                'aria-controls="raya-learning-rail-body" '
                'aria-expanded="true" '
                'aria-label="Show learning context">Context</button>'
            ),
            "</aside>",
            (
                '<div class="raya-learning-rail-drawer-backdrop" '
                "data-raya-learning-rail-drawer-backdrop hidden></div>"
            ),
        ]
    )


def _render_learning_rail_context_chip(page: ContentPage) -> str:
    title = page.title or page.nav_title or page.id
    status = page.status or "ready"
    return (
        '<p class="raya-learning-rail-context-chip" '
        "data-raya-learning-rail-context-chip "
        f'aria-label="Learning context for {html.escape(title, quote=True)}, '
        f'status {html.escape(status, quote=True)}">'
        f'<span class="raya-learning-rail-context-chip-title">{html.escape(title)}</span>'
        f'<span class="raya-learning-rail-context-chip-status">{html.escape(status)}</span>'
        "</p>"
    )


def _render_rail_panel(
    class_name: str,
    title: str,
    body: str,
    *,
    expanded: bool = False,
) -> str:
    if not body:
        return ""
    panel_id = re.sub(r"[^a-z0-9_-]+", "-", class_name.lower()).strip("-")
    body_id = f"{panel_id}-body"
    panel_state = "expanded" if expanded else "collapsed"
    aria_expanded = "true" if expanded else "false"
    aria_hidden = "false" if expanded else "true"
    inert = "" if expanded else " inert"
    return "\n".join(
        [
            (
                f'<section class="raya-rail-panel {html.escape(class_name)}" '
                f'data-raya-rail-panel-state="{panel_state}">'
            ),
            '<h2 class="raya-rail-title">',
            (
                '<button class="raya-rail-toggle" type="button" '
                "data-raya-rail-toggle "
                f'aria-controls="{html.escape(body_id, quote=True)}" '
                f'aria-expanded="{aria_expanded}">'
                f"{html.escape(title)}"
                "</button>"
            ),
            "</h2>",
            (
                f'<div class="raya-rail-panel-body" id="{html.escape(body_id, quote=True)}" '
                f'aria-hidden="{aria_hidden}"{inert}>'
            ),
            '<div class="raya-rail-panel-body-inner">',
            body,
            "</div>",
            "</div>",
            "</section>",
        ]
    )


def _extract_page_toc(rendered_article_html: str) -> tuple[str, str]:
    match = re.search(
        r'<nav class="raya-page-toc" aria-label="Page contents">.*?</nav>',
        rendered_article_html,
        flags=re.DOTALL,
    )
    if match is None:
        return rendered_article_html, _render_generated_index_toc(
            rendered_article_html
        )
    article_without_toc = (
        rendered_article_html[: match.start()] + rendered_article_html[match.end() :]
    )
    toc_html = _append_generated_index_toc_items(
        match.group(0),
        article_without_toc,
    )
    return article_without_toc, toc_html


def _append_generated_index_toc_items(toc_html: str, article_html: str) -> str:
    generated_items = _generated_index_toc_items(article_html)
    if not generated_items:
        return toc_html
    existing_hrefs = set(re.findall(r'<a href="([^"]+)">', toc_html))
    new_items = [
        item for item in generated_items if f"#{html.escape(item[1], quote=True)}" not in existing_hrefs
    ]
    if not new_items:
        return toc_html
    insertion = "\n".join(_toc_item_html(*item) for item in new_items)
    return toc_html.replace("</ol>", insertion + "\n</ol>", 1)


def _render_generated_index_toc(rendered_article_html: str) -> str:
    headings = _generated_index_toc_items(rendered_article_html)
    if len(headings) < 2:
        return ""
    return "\n".join(
        [
            '<nav class="raya-page-toc" aria-label="Page contents">',
            '<p class="raya-page-toc-title">On This Page</p>',
            "<ol>",
            "\n".join(_toc_item_html(*item) for item in headings),
            "</ol>",
            "</nav>",
        ]
    )


def _generated_index_toc_items(rendered_article_html: str) -> list[tuple[int, str, str]]:
    generated_section = re.search(
        r'<section class="[^"]*\braya-generated-index\b[^"]*".*?</section>',
        rendered_article_html,
        flags=re.DOTALL,
    )
    if generated_section is None:
        return []
    items: list[tuple[int, str, str]] = []
    for match in re.finditer(
        r'<h([2-6]) id="([^"]+)">(.*?)</h\1>',
        generated_section.group(0),
        flags=re.DOTALL,
    ):
        level = int(match.group(1))
        anchor = html.unescape(match.group(2))
        label = html.unescape(re.sub(r"<[^>]+>", "", match.group(3))).strip()
        if anchor and label:
            items.append((level, anchor, label))
    return items


def _toc_item_html(level: int, anchor: str, label: str) -> str:
    return (
        f'<li class="raya-page-toc-level-{level}">'
        f'<a href="#{html.escape(anchor, quote=True)}">'
        f"{html.escape(label)}</a></li>"
    )


class _PublicArticleTextParser(HTMLParser):
    _SKIP_CLASSES = {
        "MathJax",
        "mjx-assistive-mml",
        "mjx-container",
        "raya-page-brief",
        "raya-official-practice",
        "raya-static-environment--answer",
        "raya-static-environment--hint",
        "raya-static-environment--solution",
    }
    _BLOCK_TAGS = {
        "blockquote",
        "dd",
        "dt",
        "figcaption",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "li",
        "p",
        "summary",
        "td",
        "th",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = self._classes(attrs)
        skip = (
            self._skip_depth > 0
            or tag in {"code", "pre", "script", "style", "svg"}
            or bool(classes & self._SKIP_CLASSES)
        )
        if skip:
            self._skip_depth += 1
            return
        if tag in self._BLOCK_TAGS:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if self._skip_depth > 0:
            self._skip_depth -= 1
            return
        if tag in self._BLOCK_TAGS:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self.parts.append(data)

    @staticmethod
    def _classes(attrs: list[tuple[str, str | None]]) -> set[str]:
        for name, value in attrs:
            if name == "class" and value:
                return set(value.split())
        return set()


def _public_article_search_text(article_html: str) -> str:
    parser = _PublicArticleTextParser()
    parser.feed(article_html)
    return _sanitize_public_search_text(_compact_public_text(" ".join(parser.parts)))


class _PublicArticleSectionParser(HTMLParser):
    _HEADING_LEVELS = {
        "h2": 2,
        "h3": 3,
        "h4": 4,
        "h5": 5,
        "h6": 6,
    }

    def __init__(self, *, page_id: str) -> None:
        super().__init__(convert_charrefs=True)
        self._page_id = page_id
        self._skip_depth = 0
        self._heading_capture: dict[str, Any] | None = None
        self._title_capture: list[str] | None = None
        self._title_capture_kind = ""
        self._current: dict[str, Any] | None = None
        self.sections: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = _PublicArticleTextParser._classes(attrs)
        anchor = self._attr(attrs, "id")
        if (
            tag == "section"
            and anchor
            and self._skip_depth == 0
            and bool(classes & {"raya-numbered-object", "raya-proof"})
        ):
            kind = "proof" if "raya-proof" in classes else "numbered-object"
            self._finalize_current()
            self._current = {
                "anchor": anchor,
                "kind": kind,
                "level": 2,
                "reference": "",
                "title": "",
                "parts": [],
            }
            return
        if tag in self._HEADING_LEVELS and self._skip_depth == 0:
            level = self._HEADING_LEVELS[tag]
            if self._current is not None and level <= int(self._current["level"]):
                self._finalize_current()
            if anchor:
                self._heading_capture = {
                    "anchor": anchor,
                    "level": level,
                    "tag": tag,
                    "parts": [],
                }
            return
        skip = (
            self._skip_depth > 0
            or tag in {"code", "pre", "script", "style", "svg"}
            or bool(classes & _PublicArticleTextParser._SKIP_CLASSES)
        )
        if skip:
            self._skip_depth += 1
            return
        title_classes: set[str] = set()
        reference_classes: set[str] = set()
        if self._current is not None:
            current_anchor = str(self._current.get("anchor", ""))
            if current_anchor.startswith("raya-object-"):
                title_classes = classes & {"raya-numbered-object-title"}
                reference_classes = classes & {"raya-numbered-object-reference"}
            elif current_anchor.startswith("raya-proof-"):
                title_classes = classes & {"raya-proof-title"}
                reference_classes = classes & {"raya-proof-reference"}
        if self._current is not None and tag == "span" and (title_classes or reference_classes):
            self._title_capture = []
            self._title_capture_kind = "title" if title_classes else "reference"
        if self._current is not None and tag in _PublicArticleTextParser._BLOCK_TAGS:
            self._current["parts"].append(" ")

    def handle_endtag(self, tag: str) -> None:
        if self._skip_depth > 0:
            self._skip_depth -= 1
            return
        if self._heading_capture is not None and tag == self._heading_capture["tag"]:
            title = _sanitize_public_search_text(
                _compact_public_text(" ".join(self._heading_capture["parts"]))
            )
            if title:
                self._current = {
                    "anchor": str(self._heading_capture["anchor"]),
                    "kind": "heading",
                    "level": int(self._heading_capture["level"]),
                    "reference": "",
                    "title": title,
                    "parts": [title, " "],
                }
            self._heading_capture = None
            return
        if self._title_capture is not None and tag == "span":
            title = _sanitize_public_search_text(
                _compact_public_text(" ".join(self._title_capture))
            )
            if title and self._current is not None:
                existing_title = str(self._current.get("title", ""))
                if self._title_capture_kind == "title":
                    self._current["title"] = title
                else:
                    self._current["reference"] = title
                    if not existing_title:
                        self._current["title"] = title
            self._title_capture = None
            self._title_capture_kind = ""
        if self._current is not None and tag in _PublicArticleTextParser._BLOCK_TAGS:
            self._current["parts"].append(" ")

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        if self._title_capture is not None:
            self._title_capture.append(data)
        if self._heading_capture is not None:
            self._heading_capture["parts"].append(data)
            return
        if self._current is not None:
            self._current["parts"].append(data)

    def close(self) -> None:
        super().close()
        self._finalize_current()

    def _finalize_current(self) -> None:
        if self._current is None:
            return
        anchor = str(self._current["anchor"])
        search_text = _sanitize_public_search_text(
            _compact_public_text(" ".join(str(part) for part in self._current["parts"]))
        )
        title = _sanitize_public_search_text(str(self._current["title"]))
        reference = _sanitize_public_search_text(str(self._current.get("reference", "")))
        if not title:
            title = _public_search_snippet(search_text, limit=80)
        if search_text:
            section = {
                "id": f"{self._page_id}:{anchor}",
                "anchor": anchor,
                "kind": str(self._current.get("kind", "")),
                "title": title,
                "search_text": search_text,
                "search_snippet": _public_search_snippet(search_text, limit=160),
            }
            if reference:
                section["reference"] = reference
            self.sections.append(section)
        self._current = None

    @staticmethod
    def _attr(attrs: list[tuple[str, str | None]], name: str) -> str:
        for attr_name, value in attrs:
            if attr_name == name and value:
                return value
        return ""


def _public_article_search_sections(
    article_html: str, *, page_id: str
) -> list[dict[str, str]]:
    parser = _PublicArticleSectionParser(page_id=page_id)
    parser.feed(article_html)
    parser.close()
    return parser.sections


def _compact_public_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _sanitize_public_search_text(value: str) -> str:
    sanitized = value
    sanitized = re.sub(r"\\(?:begin|end)\{[^}]+\}", " ", sanitized)
    sanitized = re.sub(r"\\[A-Za-z]+(?:\s*\{[^}]*\})*", " ", sanitized)
    sanitized = re.sub(
        r"(?i)\b(?:_?assets|_?official|_?reviewed|_?drafts|_?partials)\b/?",
        " ",
        sanitized,
    )
    sanitized = re.sub(r"(?i)\bartifact(?:/[\w./-]*)?\b", " ", sanitized)
    sanitized = re.sub(r"(?i)\bcourse/", " ", sanitized)
    sanitized = re.sub(r"(?i)\bsource[_ ]path\b", " ", sanitized)
    sanitized = re.sub(r"(?i)\bcache[_ ]key\b", " ", sanitized)
    sanitized = re.sub(r"(?i)\bsource path\b", " ", sanitized)
    sanitized = re.sub(r"(?i)\bcache key\b", " ", sanitized)
    for sensitive_token in (
        "calendar sync",
        "completion",
        "confidence",
        "mastery",
        "overdue",
        "progress",
        "recommendation",
        "recommendations",
        "recommended",
        "reminder",
        "review history",
    ):
        sanitized = re.sub(
            re.escape(sensitive_token),
            "",
            sanitized,
            flags=re.IGNORECASE,
        )
    sanitized = re.sub(
        r"\brecommend\b",
        "",
        sanitized,
        flags=re.IGNORECASE,
    )
    sanitized = re.sub(r"\$+", " ", sanitized)
    return _compact_public_text(sanitized)


def _public_search_snippet(text: str, *, limit: int = 240) -> str:
    compact = _compact_public_text(text)
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "..."


def _render_page_contents_rail(
    toc_html: str, public_sections: list[dict[str, str]]
) -> str:
    object_links = _render_page_contents_object_links(public_sections)
    body = "\n".join(part for part in (toc_html, object_links) if part)
    if not body:
        return ""
    return _render_rail_panel(
        "raya-page-contents", "Page contents", body, expanded=True
    )


def _render_page_contents_object_links(public_sections: list[dict[str, str]]) -> str:
    items: list[str] = []
    for section in public_sections:
        if section.get("kind") not in {"numbered-object", "proof"}:
            continue
        anchor = section.get("anchor", "")
        title = section.get("title", "").strip()
        reference = section.get("reference", "").strip()
        label_parts = [reference]
        if title != reference:
            label_parts.append(title)
        label = " ".join(part for part in label_parts if part)
        if not anchor or not label:
            continue
        escaped_anchor = html.escape(anchor, quote=True)
        items.append(
            '<li class="raya-page-toc-object-item">'
            f'<a href="#{escaped_anchor}" '
            f'data-raya-key-object-link="{escaped_anchor}">'
            f"{html.escape(label)}</a></li>"
        )
    if not items:
        return ""
    return "\n".join(
        [
            '<div class="raya-page-toc-objects" aria-label="Key objects">',
            '<p class="raya-page-toc-objects-title">Key objects</p>',
            '<ol class="raya-page-toc-object-list">',
            "\n".join(items),
            "</ol>",
            "</div>",
        ]
    )


def _render_current_section_rail(toc_html: str) -> str:
    if not toc_html:
        return ""
    match = re.search(r'<a href="([^"]+)">([^<]+)</a>', toc_html)
    if match is None:
        return ""
    href = match.group(1)
    if href.startswith("#raya-generated-"):
        return ""
    label = html.unescape(match.group(2))
    body = "\n".join(
        [
            '<div class="raya-current-section" data-raya-current-section>',
            '<span class="raya-current-section-label">Current section</span>',
            (
                '<a class="raya-current-section-link" '
                "data-raya-current-section-link "
                'aria-live="polite" '
                f'href="{html.escape(href, quote=True)}">'
                f"{html.escape(label)}"
                "</a>"
            ),
            "</div>",
        ]
    )
    return _render_rail_panel(
        "raya-page-current-section",
        "Current section",
        body,
        expanded=True,
    )


def _render_page_summary_rail(page: ContentPage) -> str:
    if not page.summary:
        return ""
    return _render_rail_panel(
        "raya-page-summary",
        "Summary",
        f"<p>{html.escape(page.summary)}</p>",
        expanded=True,
    )


def _render_reading_flow_rail(
    page: ContentPage,
    content_model: ContentModel,
    page_graph_context: dict[str, list[dict[str, str]]],
    graph_href: str,
) -> str:
    targets = _sequence_targets(page, content_model)
    outgoing = page_graph_context.get("outgoing", [])
    incoming = page_graph_context.get("incoming", [])
    if not targets and not outgoing and not incoming:
        return ""

    parts: list[str] = []
    sequence_links: list[str] = []
    previous = targets.get("previous")
    if previous is not None:
        previous_page = previous["page"]
        assert isinstance(previous_page, ContentPage)
        sequence_links.append(
            '<a class="raya-reading-flow-link raya-reading-flow-prev" '
            'rel="prev" data-raya-prev-page aria-keyshortcuts="ArrowLeft" '
            f'href="{html.escape(str(previous["href"]))}">'
            '<span class="raya-reading-flow-link-label">Previous</span>'
            f'<span class="raya-reading-flow-link-title">{html.escape(previous_page.nav_title or previous_page.title)}</span>'
            "</a>"
        )
    next_target = targets.get("next")
    if next_target is not None:
        next_page = next_target["page"]
        assert isinstance(next_page, ContentPage)
        sequence_links.append(
            '<a class="raya-reading-flow-link raya-reading-flow-next" '
            'rel="next" data-raya-next-page aria-keyshortcuts="ArrowRight" '
            f'href="{html.escape(str(next_target["href"]))}">'
            '<span class="raya-reading-flow-link-label">Next</span>'
            f'<span class="raya-reading-flow-link-title">{html.escape(next_page.nav_title or next_page.title)}</span>'
            "</a>"
        )
    if sequence_links:
        parts.append(
            '<div class="raya-reading-flow-grid" aria-label="Previous and next pages">'
            + "\n".join(sequence_links)
            + "</div>"
        )

    if outgoing or incoming:
        parts.extend(
            [
                '<div class="raya-reading-flow-graph">',
                '<p class="raya-reading-flow-counts">',
                (
                    f"<span><strong>{len(outgoing)}</strong> "
                    f"{_relationship_count_label(len(outgoing), 'from this page', 'from this page')}</span>"
                ),
                (
                    f"<span><strong>{len(incoming)}</strong> "
                    f"{_relationship_count_label(len(incoming), 'links here', 'link here')}</span>"
                ),
                "</p>",
                (
                    f'<a class="raya-reading-flow-graph-link" href="{html.escape(graph_href)}">'
                    "Open in course graph</a>"
                ),
                "</div>",
            ]
        )
        connection_chips = _reading_flow_connection_chips(page, outgoing, incoming)
        if connection_chips:
            parts.append(
                '<ul class="raya-reading-flow-connections" aria-label="Connected pages">'
                + connection_chips
                + "</ul>"
            )
    return _render_rail_panel(
        "raya-page-reading-flow",
        "Reading flow",
        "\n".join(parts),
        expanded=True,
    )


def _reading_flow_connection_chips(
    page: ContentPage,
    outgoing: list[dict[str, str]],
    incoming: list[dict[str, str]],
    *,
    limit: int = 4,
) -> str:
    chips: list[str] = []
    for direction, items in (("From this page", outgoing), ("Links here", incoming)):
        for item in items[: max(0, limit - len(chips))]:
            href = _relative_href(page.output_path, item["url"])
            kind = item.get("kind", "content")
            kind_label = _connection_kind_label(kind)
            chips.append(
                '<li>'
                f'<a href="{html.escape(href)}" '
                f'data-raya-reading-flow-kind="{html.escape(kind, quote=True)}">'
                '<span class="raya-reading-flow-connection-meta">'
                f'<span class="raya-reading-flow-connection-direction">{html.escape(direction)}</span>'
                f'<span class="raya-reading-flow-connection-kind">{html.escape(kind_label)}</span>'
                "</span>"
                f'<span class="raya-reading-flow-connection-title">{html.escape(item["title"])}</span>'
                "</a>"
                "</li>"
            )
            if len(chips) >= limit:
                break
    return "\n".join(chips)


def _render_page_status_rail(page: ContentPage) -> str:
    if not page.status:
        return ""
    return _render_rail_panel(
        "raya-page-status",
        "Status",
        f'<p><span class="raya-status-chip">{html.escape(page.status)}</span></p>',
    )


def _render_estimated_time_rail(estimated_reading_time: tuple[str, str] | None) -> str:
    if estimated_reading_time is None:
        return ""
    label, value = estimated_reading_time
    return _render_rail_panel(
        "raya-page-estimated-time",
        label,
        f"<p>{html.escape(value)}</p>",
    )


def _render_tags_rail(page: ContentPage) -> str:
    if not page.tags:
        return ""
    items = "\n".join(f"<li>{html.escape(tag)}</li>" for tag in page.tags)
    return _render_rail_panel("raya-page-tags", "Tags", f"<ul>{items}</ul>")


def _render_prerequisites_rail(
    page: ContentPage,
    content_model: ContentModel,
) -> str:
    items = []
    for prerequisite in page.prerequisites:
        target = content_model.pages_by_id.get(prerequisite)
        if target is None:
            continue
        items.append(
            _rail_page_context_item(
                page,
                prerequisite,
                target.nav_title or target.title,
                target.output_path,
            )
        )
    if not items:
        return ""
    return _render_rail_panel(
        "raya-page-prerequisites",
        "Prerequisites",
        '<ul class="raya-rail-link-list">' + "\n".join(items) + "</ul>",
    )


def _render_linked_pages_rail(
    page: ContentPage,
    page_graph_context: dict[str, list[dict[str, str]]],
) -> str:
    sections = []
    outgoing = page_graph_context.get("outgoing", [])
    incoming = page_graph_context.get("incoming", [])
    summary = (
        '<p class="raya-rail-connection-summary">'
        f"<span><strong>{len(outgoing)}</strong> {_relationship_count_label(len(outgoing), 'from this page', 'from this page')}</span>"
        f"<span><strong>{len(incoming)}</strong> {_relationship_count_label(len(incoming), 'links here', 'link here')}</span>"
        "</p>"
    )
    if outgoing:
        sections.append(
            _rail_connection_heading("From this page", len(outgoing))
            + '<ul class="raya-rail-link-list">'
            + "\n".join(
                _linked_page_item(page, item, "From this page") for item in outgoing
            )
            + "</ul>"
        )
    if incoming:
        sections.append(
            _rail_connection_heading("Links here", len(incoming))
            + '<ul class="raya-rail-link-list">'
            + "\n".join(
                _linked_page_item(page, item, "Links here") for item in incoming
            )
            + "</ul>"
        )
    if not sections:
        return ""
    return _render_rail_panel(
        "raya-page-linked-pages",
        "Connections",
        summary + "\n" + "\n".join(sections),
    )


def _render_article_connections(
    page: ContentPage,
    page_graph_context: dict[str, list[dict[str, str]]],
    graph_href: str,
) -> str:
    outgoing = page_graph_context.get("outgoing", [])
    incoming = page_graph_context.get("incoming", [])
    if not outgoing and not incoming:
        return ""

    sections = []
    if outgoing:
        sections.append(_article_connection_section("From this page", outgoing, page))
    if incoming:
        sections.append(_article_connection_section("Links here", incoming, page))

    return "\n".join(
        [
            (
                '<section class="raya-article-connections" '
                'aria-labelledby="raya-article-connections-title">'
            ),
            '<div class="raya-article-connections-header">',
            "<div>",
            '<p class="raya-article-connections-kicker">Course graph</p>',
            '<h2 id="raya-article-connections-title">Page connections</h2>',
            "</div>",
            (
                '<a class="raya-article-connections-graph" '
                f'href="{html.escape(graph_href)}">Open in course graph</a>'
            ),
            "</div>",
            '<p class="raya-article-connections-summary">',
            (
                '<span><span class="raya-article-connections-count">'
                f"{len(outgoing)}</span> "
                f"{_relationship_count_label(len(outgoing), 'from this page', 'from this page')}</span>"
            ),
            (
                '<span><span class="raya-article-connections-count">'
                f"{len(incoming)}</span> "
                f"{_relationship_count_label(len(incoming), 'links here', 'link here')}</span>"
            ),
            "</p>",
            '<div class="raya-article-connections-grid">',
            "\n".join(sections),
            "</div>",
            "</section>",
        ]
    )


def _article_connection_section(
    title: str,
    items: list[dict[str, str]],
    page: ContentPage,
) -> str:
    rendered_items = "\n".join(
        _article_connection_item(page, item, title) for item in items
    )
    return "\n".join(
        [
            '<section class="raya-article-connections-section">',
            f"<h3>{html.escape(title)}</h3>",
            f'<ul aria-label="{html.escape(title, quote=True)}">',
            rendered_items,
            "</ul>",
            "</section>",
        ]
    )


def _article_connection_item(
    page: ContentPage,
    item: dict[str, str],
    direction: str,
) -> str:
    preview = _connection_preview_item(page, item, "article", direction)
    return f'<li class="raya-article-connection-item">{preview}</li>'


def _relationship_count_label(count: int, plural: str, singular: str) -> str:
    return singular if count == 1 else plural


def _connection_kind_label(kind: str) -> str:
    labels = {
        "content": "Content",
        "navigation": "Navigation",
        "parent": "Parent",
        "prerequisite": "Prerequisite",
    }
    normalized = kind.strip().lower()
    return labels.get(
        normalized,
        normalized.replace("-", " ").replace("_", " ").title() or "Content",
    )


def _connection_direction_sentence(direction: str, kind: str) -> str:
    kind_label = _connection_kind_label(kind).lower()
    if direction == "Links here":
        return f"This target page links here through an explicit {kind_label} link."
    return f"This page links to the target page through an explicit {kind_label} link."


def _rail_connection_heading(title: str, count: int) -> str:
    return (
        '<div class="raya-rail-connection-heading">'
        f"<h3>{html.escape(title)}</h3>"
        f'<span class="raya-rail-count">{count}</span>'
        "</div>"
    )


def _linked_page_item(page: ContentPage, item: dict[str, str], direction: str) -> str:
    return "<li>" + _connection_preview_item(page, item, "rail", direction) + "</li>"


def _connection_preview_item(
    page: ContentPage,
    item: dict[str, str],
    variant: str,
    direction: str,
) -> str:
    title = item["title"]
    href = _relative_href(page.output_path, item["url"])
    graph_href = _href_with_query(
        _relative_href(page.output_path, STATIC_GRAPH_PATH.as_posix()),
        {"page": item["id"]},
    )
    kind_label = _connection_kind_label(item.get("kind", "content"))
    metadata = _connection_preview_metadata(item, direction)
    return "\n".join(
        [
            (
                '<details class="raya-connection-preview '
                f'raya-connection-preview-{html.escape(variant, quote=True)}">'
            ),
            (
                "<summary>"
                '<span class="raya-connection-preview-meta">'
                f'<span class="raya-connection-preview-kind">{html.escape(kind_label)}</span>'
                f'<span class="raya-connection-preview-direction">{html.escape(direction)}</span>'
                "</span>"
                f'<span class="raya-connection-preview-title">{html.escape(title)}</span>'
                "</summary>"
            ),
            '<div class="raya-connection-preview-body">',
            metadata,
            '<p class="raya-connection-preview-actions">',
            (
                f'<a class="raya-connection-preview-open" href="{html.escape(href)}">'
                "Open page</a>"
            ),
            (
                f'<a class="raya-connection-preview-graph" href="{html.escape(graph_href)}" '
                f'aria-label="View {html.escape(title, quote=True)} in course graph">'
                "Graph</a>"
            ),
            "</p>",
            "</div>",
            "</details>",
        ]
    )


def _connection_preview_metadata(item: dict[str, str], direction: str) -> str:
    parts: list[str] = []
    kind = item.get("kind", "content")
    parts.append(
        '<p class="raya-connection-preview-direction-note">'
        f"{html.escape(_connection_direction_sentence(direction, kind))}</p>"
    )
    summary = item.get("summary", "")
    status = item.get("status", "")
    if summary:
        parts.append(
            f'<p class="raya-connection-preview-summary">{html.escape(summary)}</p>'
        )
    if status:
        parts.append(
            '<p><span class="raya-connection-preview-status">'
            f"{html.escape(status)}</span></p>"
        )
    outgoing_count = int(item.get("outgoing_count", "0"))
    incoming_count = int(item.get("incoming_count", "0"))
    parts.append(
        '<p class="raya-connection-preview-counts">'
        f"<span><strong>{outgoing_count}</strong> "
        f"{_relationship_count_label(outgoing_count, 'from this page', 'from this page')}</span>"
        f"<span><strong>{incoming_count}</strong> "
        f"{_relationship_count_label(incoming_count, 'links here', 'link here')}</span>"
        "</p>"
    )
    return "\n".join(parts)


def _rail_page_context_item(
    page: ContentPage,
    target_id: str,
    title: str,
    target_output_path: str,
) -> str:
    href = _relative_href(page.output_path, target_output_path)
    graph_href = _href_with_query(
        _relative_href(page.output_path, STATIC_GRAPH_PATH.as_posix()),
        {"page": target_id},
    )
    return (
        '<li><span class="raya-rail-link-row">'
        f'<a href="{html.escape(href)}">{html.escape(title)}</a>'
        f'<a class="raya-rail-context-link" href="{html.escape(graph_href)}" '
        f'aria-label="View {html.escape(title, quote=True)} in course graph">'
        "Graph</a>"
        "</span></li>"
    )


def _render_sequence_rail(page: ContentPage, content_model: ContentModel) -> str:
    sequence_nav = _render_sequence_nav(page, content_model)
    if not sequence_nav:
        return ""
    return _render_rail_panel("raya-page-sequence", "Sequence", sequence_nav)


_COMMAND_ICON_BODIES = {
    "home": (
        '<path d="M4.5 11.2 12 5l7.5 6.2"/>'
        '<path d="M6.8 10.5v8h10.4v-8"/>'
        '<path d="M10 18.5v-5h4v5"/>'
    ),
    "search": '<circle cx="10.5" cy="10.5" r="5.5"/><path d="m15 15 4.5 4.5"/>',
    "graph": (
        '<circle cx="6.5" cy="7" r="2.3"/>'
        '<circle cx="17.5" cy="8.5" r="2.3"/>'
        '<circle cx="12" cy="17" r="2.3"/>'
        '<path d="m8.6 7.4 6.7.7M7.7 9.1l3.1 5.9M16.4 10.7l-3.2 4.4"/>'
    ),
    "practice": '<path d="M5 12.8 9.4 17 19 7"/>',
    "tasks": (
        '<path d="M8 5h8l1.5 2v12h-11V7L8 5Z"/>'
        '<path d="M9 11h6M9 15h4"/>'
        '<path d="M9.2 7.2h5.6"/>'
    ),
    "schedule": (
        '<path d="M6.5 5.5h11v13h-11z"/>'
        '<path d="M6.5 9h11M9 4v3M15 4v3"/>'
        '<path d="M9 12h2M13 12h2M9 15h2"/>'
    ),
    "map": (
        '<path d="M4.8 6.5 9.8 5l4.4 1.5 5-1.5v12.5l-5 1.5-4.4-1.5-5 1.5z"/>'
        '<path d="M9.8 5v12.5M14.2 6.5V19"/>'
    ),
    "focus": (
        '<path d="M8 5H5v3M16 5h3v3M5 16v3h3M19 16v3h-3"/>'
        '<path d="M9 12h6"/>'
        '<path d="M12 9v6"/>'
    ),
    "context": (
        '<path d="M5 5.5h14v13H5z"/>'
        '<path d="M14.5 5.5v13"/>'
        '<path d="M7.5 9h4M7.5 12h4M7.5 15h4"/>'
    ),
    "text-size": (
        '<text class="raya-command-icon-text" x="11.7" y="14.8" '
        'text-anchor="middle">A+</text>'
    ),
    "font": (
        '<text class="raya-command-icon-text" x="11.8" y="14.8" '
        'text-anchor="middle">Aa</text>'
    ),
    "skin": (
        '<path d="M5.5 8.2c1.8-2.2 4-3.3 6.5-3.3 4.2 0 7.5 3.2 7.5 7.1 0 3.5-2.7 6.5-6.3 6.5h-1.4c-.9 0-1.4-.8-1-1.5.5-.9-.1-1.8-1.2-1.8H8.4c-2.2 0-3.9-1.5-3.9-3.7 0-1.2.3-2.3 1-3.3Z"/>'
        '<circle cx="8.5" cy="10" r=".8"/>'
        '<circle cx="11.6" cy="8.4" r=".8"/>'
        '<circle cx="15" cy="10.3" r=".8"/>'
    ),
}


def _command_icon(name: str) -> str:
    body = _COMMAND_ICON_BODIES[name]
    return (
        '<svg class="raya-command-icon" '
        f'data-raya-command-icon="{html.escape(name, quote=True)}" '
        'aria-hidden="true" focusable="false" viewBox="0 0 24 24" '
        'width="24" height="24">'
        f"{body}"
        "</svg>"
    )


def _render_command_link(
    *,
    class_name: str,
    href: str,
    aria_label: str,
    icon: str,
    label: str,
    attrs: dict[str, str] | None = None,
) -> str:
    attrs_text = "".join(
        (
            f' {html.escape(name, quote=True)}='
            f'"{html.escape(value, quote=True)}"'
        )
        for name, value in (attrs or {}).items()
    )
    return (
        f'<a class="{html.escape(class_name, quote=True)}" '
        f'href="{html.escape(href)}" '
        f'aria-label="{html.escape(aria_label, quote=True)}"{attrs_text}>'
        f"{_command_icon(icon)}"
        f'<span class="raya-command-label">{html.escape(label)}</span>'
        "</a>"
    )


def _render_command_button(
    *,
    class_name: str,
    aria_label: str,
    icon: str,
    label: str,
    aria_pressed: str | None = None,
    extra_attrs: str = "",
) -> str:
    pressed_attr = "" if aria_pressed is None else f' aria-pressed="{aria_pressed}"'
    return (
        f'<button class="{html.escape(class_name, quote=True)}" type="button" '
        f'aria-label="{html.escape(aria_label, quote=True)}"{pressed_attr}{extra_attrs}>'
        f"{_command_icon(icon)}"
        f'<span class="raya-command-label">{html.escape(label)}</span>'
        "</button>"
    )


def _resolve_markdown_href(
    page: ContentPage,
    href: str,
    pages_by_source: dict[Path, ContentPage],
    pages_by_reference: dict[str, ContentPage],
    objects_by_id: dict[str, NumberedObject],
    course_root: Path,
    source_dir: Path,
    report: ValidationReport,
) -> str:
    kind = classify_markdown_target(href)
    if kind == "ignored":
        return href
    fragment = markdown_link_fragment(href)
    if kind == "stable":
        stable_id = stable_markdown_id(href)
        if stable_id.startswith("ref/"):
            object_id = stable_id[len("ref/") :]
            obj = objects_by_id.get(object_id)
            if obj is not None:
                return (
                    _relative_href(page.output_path, obj.page_output_path)
                    + f"#raya-object-{object_id}"
                )
            report.add_error(
                f"Unknown numbered object reference '{href}'",
                path=page.source_path,
                field=f"link:{href}",
                next_action="Use a raya:ref link target that matches a numbered object ID",
            )
            return href
        target_page = pages_by_reference.get(stable_id)
        if target_page is not None:
            return _relative_href(page.output_path, target_page.output_path) + fragment
    if kind == "content":
        target_page = _target_content_page(page, href, pages_by_source, course_root)
        if target_page is not None:
            return _relative_href(page.output_path, target_page.output_path) + fragment
    if kind == "asset":
        target_href = _target_asset_href(page, href, course_root, source_dir)
        if target_href is not None:
            return target_href + fragment
    if kind in {"code", "notebook"}:
        target_href = _target_reference_href(page, href, course_root, source_dir, kind)
        if target_href is not None:
            return target_href + fragment
    return href


def _resolve_wikilink_page_id(
    target: str,
    resolver: WikilinkResolver,
) -> str | None:
    resolution = resolver.resolve(target)
    if resolution.page is None:
        return None
    return resolution.page.id


def _validate_rich_markdown_inputs(
    pages: list[ContentPage],
    report: ValidationReport,
) -> None:
    for page in pages:
        if contains_full_latex_document(page.body):
            report.add_error(
                "Full LaTeX documents are not supported",
                path=page.source_path,
                field="math:latex-document",
                next_action=(
                    "Remove full LaTeX document commands such as \\documentclass, "
                    "\\begin{document}, and \\end{document}. Keep only supported "
                    "inline `$...$` and display `$$` math expressions in Markdown."
                ),
            )
        if has_unsupported_nested_math_delimiters(page.body):
            report.add_error(
                "Unsupported nested math delimiter",
                path=page.source_path,
                field="math:delimiter-nesting",
                next_action=(
                    "Do not nest `$...$` and `$$` delimiters. Use inline math "
                    "with `$...$`, or put display math between standalone $$ "
                    "delimiter lines."
                ),
            )
        if has_malformed_display_math_delimiters(page.body):
            report.add_error(
                "Malformed display math delimiter",
                path=page.source_path,
                field="math:display-delimiter",
                next_action=(
                    "Close each display math block with a matching $$ delimiter "
                    "on its own line, or escape dollar signs intended as text."
                ),
            )
        for label in missing_footnote_definitions(page.body):
            report.add_error(
                "Missing footnote definition",
                path=page.source_path,
                field=f"footnote:{label}",
                next_action=(
                    f"Add a [^{label}]: footnote definition on this page "
                    f"or remove the [^{label}] reference"
                ),
            )


def _render_breadcrumbs(page: ContentPage, content_model: ContentModel) -> str:
    breadcrumbs = _breadcrumb_pages(page, content_model)
    if not breadcrumbs:
        return ""
    home_page = content_model.pages[0]
    crumbs: list[tuple[str, str | None, str]] = [
        (
            home_page.nav_title,
            _relative_href(page.output_path, home_page.output_path),
            "raya-breadcrumb-home",
        )
    ]
    for crumb in breadcrumbs:
        if crumb.id == home_page.id:
            continue
        crumbs.append(
            (
                crumb.nav_title,
                _relative_href(page.output_path, crumb.output_path),
                "raya-breadcrumb-link",
            )
        )
    crumbs.append((page.nav_title, None, "raya-breadcrumb-current"))

    items = []
    for index, (label, href, class_name) in enumerate(crumbs):
        if index > 0:
            items.append(
                '<li class="raya-breadcrumb-separator" aria-hidden="true">›</li>'
            )
        escaped_label = html.escape(label)
        if href is None:
            items.append(
                '<li><span class="raya-breadcrumb-current" aria-current="page">'
                f"{escaped_label}</span></li>"
            )
        else:
            items.append(
                f'<li><a class="{class_name}" href="{html.escape(href)}">'
                f"{escaped_label}</a></li>"
            )
    return (
        '<nav class="raya-breadcrumbs" aria-label="Breadcrumbs">'
        '<ol class="raya-breadcrumbs-list">' + "".join(items) + "</ol></nav>"
    )


def _count_label(count: int, singular: str) -> str:
    suffix = singular if count == 1 else f"{singular}s"
    return f"{count} {suffix}"


def _page_reading_time(
    page: ContentPage,
    public_article_text: str,
    content_model: ContentModel,
) -> tuple[str, str] | None:
    if page.estimated_time:
        return ("Estimated time", page.estimated_time)
    word_count = len(re.findall(r"\b[\w'-]+\b", public_article_text))
    if word_count == 0:
        return None
    minutes = max(1, (word_count + 199) // 200)
    return ("Estimated read time", f"{minutes} min read")


def _render_page_brief(
    page: ContentPage,
    content_model: ContentModel,
    official_practice_count: int,
    page_graph_context: dict[str, list[dict[str, str]]],
    graph_href: str,
    estimated_reading_time: tuple[str, str] | None,
) -> str:
    facts: list[str] = []
    status = page.status.strip() if page.status else ""
    if status:
        facts.append(_page_brief_fact("Status", html.escape(status), "status"))
    position = _page_position(page, content_model)
    if position:
        facts.append(_page_brief_fact("Position", html.escape(position), "position"))
    sequence_links = _page_brief_sequence_links(page, content_model)
    if sequence_links:
        facts.append(_page_brief_fact("Learning path", sequence_links, "path"))
    if estimated_reading_time is not None:
        label, value = estimated_reading_time
        facts.append(
            _page_brief_fact(label, html.escape(value), "time")
        )
    if page.tags:
        tag_items = " ".join(
            f'<span class="raya-page-brief-tag">{html.escape(tag)}</span>'
            for tag in page.tags
        )
        facts.append(_page_brief_fact("Tags", tag_items, "tags"))
    prerequisite_links = _page_brief_prerequisite_links(page, content_model)
    if prerequisite_links:
        facts.append(
            _page_brief_fact("Prerequisites", prerequisite_links, "prerequisites")
        )
    connection_text = _page_brief_connection_text(page_graph_context)
    if connection_text:
        facts.append(
            _page_brief_fact(
                "Connections",
                f'<a href="{html.escape(graph_href)}">{connection_text}</a>',
                "connections",
            )
        )
    if official_practice_count:
        label = (
            "official practice object"
            if official_practice_count == 1
            else "official practice objects"
        )
        facts.append(
            _page_brief_fact(
                "Practice",
                (
                    '<a href="#raya-official-practice">'
                    f"{official_practice_count} {label}</a>"
                ),
                "practice",
            )
        )
    summary = page.summary.strip() if page.summary else ""
    if not summary and not facts:
        return ""
    summary_html = (
        f'<p class="raya-page-brief-summary">{html.escape(summary)}</p>'
        if summary
        else ""
    )
    facts_html = (
        '<ul class="raya-page-brief-facts">' + "\n".join(facts) + "</ul>"
        if facts
        else ""
    )
    return "\n".join(
        [
            '<section class="raya-page-brief" aria-labelledby="raya-page-brief-title">',
            '<div class="raya-page-brief-heading">',
            '<p class="raya-page-brief-kicker">Page brief</p>',
            '<h2 id="raya-page-brief-title">At a glance</h2>',
            "</div>",
            summary_html,
            facts_html,
            "</section>",
        ]
    )


def _page_brief_fact(label: str, value: str, class_suffix: str) -> str:
    return (
        f'<li class="raya-page-brief-fact raya-page-brief-{html.escape(class_suffix, quote=True)}">'
        f'<span class="raya-page-brief-label">{html.escape(label)}</span>'
        f'<span class="raya-page-brief-value">{value}</span>'
        "</li>"
    )


def _page_brief_prerequisite_links(
    page: ContentPage,
    content_model: ContentModel,
) -> str:
    links: list[str] = []
    for prerequisite in page.prerequisites:
        target = content_model.pages_by_id.get(prerequisite)
        if target is None:
            continue
        href = _relative_href(page.output_path, target.output_path)
        title = target.nav_title or target.title
        links.append(f'<a href="{html.escape(href)}">{html.escape(title)}</a>')
    return ", ".join(links)


def _page_brief_sequence_links(page: ContentPage, content_model: ContentModel) -> str:
    return _sequence_links(page, content_model)


def _page_brief_connection_text(
    page_graph_context: dict[str, list[dict[str, str]]],
) -> str:
    outgoing_count = len(page_graph_context.get("outgoing", []))
    incoming_count = len(page_graph_context.get("incoming", []))
    if not outgoing_count and not incoming_count:
        return ""
    return (
        "View graph context: "
        f"{outgoing_count} "
        f"{_relationship_count_label(outgoing_count, 'from this page', 'from this page')}"
        f", {incoming_count} "
        f"{_relationship_count_label(incoming_count, 'links here', 'link here')}"
    )


def _renderable_official_object_count(objects: list[dict[str, Any]]) -> int:
    return sum(
        1
        for item in objects
        if isinstance(item, dict) and _render_official_object(item)
    )


def _sequence_targets(
    page: ContentPage,
    content_model: ContentModel,
) -> dict[str, dict[str, object]]:
    pages = content_model.pages
    current_index = next(
        (
            index
            for index, target in enumerate(pages)
            if target.output_path == page.output_path
        ),
        None,
    )
    if current_index is None:
        return {}
    targets: dict[str, dict[str, object]] = {}
    total_pages = len(pages)
    if current_index > 0:
        previous = pages[current_index - 1]
        targets["previous"] = {
            "page": previous,
            "href": _relative_href(page.output_path, previous.output_path),
            "index": current_index,
            "total": total_pages,
        }
    if current_index + 1 < total_pages:
        next_page = pages[current_index + 1]
        targets["next"] = {
            "page": next_page,
            "href": _relative_href(page.output_path, next_page.output_path),
            "index": current_index + 2,
            "total": total_pages,
        }
    return targets


def _sequence_links(page: ContentPage, content_model: ContentModel) -> str:
    targets = _sequence_targets(page, content_model)
    links: list[str] = []
    previous = targets.get("previous")
    if previous is not None:
        previous_page = previous["page"]
        assert isinstance(previous_page, ContentPage)
        links.append(
            '<a rel="prev" data-raya-prev-page '
            'aria-keyshortcuts="ArrowLeft" '
            f'href="{html.escape(str(previous["href"]))}">'
            f"Previous: {html.escape(previous_page.nav_title or previous_page.title)}</a>"
        )
    next_target = targets.get("next")
    if next_target is not None:
        next_page = next_target["page"]
        assert isinstance(next_page, ContentPage)
        links.append(
            '<a rel="next" data-raya-next-page '
            'aria-keyshortcuts="ArrowRight" '
            f'href="{html.escape(str(next_target["href"]))}">'
            f"Next: {html.escape(next_page.nav_title or next_page.title)}</a>"
        )
    return "\n".join(links)


def _render_article_sequence_nav(page: ContentPage, content_model: ContentModel) -> str:
    sequence = _sequence_links(page, content_model)
    if not sequence:
        return ""
    return (
        '<nav class="raya-article-sequence raya-article-sequence-top" '
        'aria-label="Previous and next pages">' + sequence + "</nav>"
    )


def _render_article_sequence_cards(
    page: ContentPage,
    content_model: ContentModel,
) -> str:
    targets = _sequence_targets(page, content_model)
    if not targets:
        return ""
    cards: list[str] = []
    previous = targets.get("previous")
    if previous is not None:
        previous_page = previous["page"]
        assert isinstance(previous_page, ContentPage)
        cards.append(
            '<a class="raya-sequence-card raya-sequence-card-prev" '
            'rel="prev" data-raya-prev-page '
            'aria-keyshortcuts="ArrowLeft" '
            f'href="{html.escape(str(previous["href"]))}">'
            '<span class="raya-sequence-card-kicker">Previous page</span>'
            '<span class="raya-sequence-card-title">'
            f"{html.escape(previous_page.nav_title or previous_page.title)}</span>"
            '<span class="raya-sequence-card-meta">'
            f"Page {previous['index']} of {previous['total']}</span>"
            "</a>"
        )
    next_target = targets.get("next")
    if next_target is not None:
        next_page = next_target["page"]
        assert isinstance(next_page, ContentPage)
        cards.append(
            '<a class="raya-sequence-card raya-sequence-card-next" '
            'rel="next" data-raya-next-page '
            'aria-keyshortcuts="ArrowRight" '
            f'href="{html.escape(str(next_target["href"]))}">'
            '<span class="raya-sequence-card-kicker">Next page</span>'
            '<span class="raya-sequence-card-title">'
            f"{html.escape(next_page.nav_title or next_page.title)}</span>"
            '<span class="raya-sequence-card-meta">'
            f"Page {next_target['index']} of {next_target['total']}</span>"
            "</a>"
        )
    return (
        '<nav class="raya-article-sequence-cards" '
        'aria-label="End-of-page navigation">' + "\n".join(cards) + "</nav>"
    )


def _render_sequence_nav(page: ContentPage, content_model: ContentModel) -> str:
    sequence = _sequence_links(page, content_model)
    if not sequence:
        return ""
    return '<nav aria-label="Previous and next">' + sequence + "</nav>"


def _render_official_practice_section(
    objects: list[dict[str, Any]],
    *,
    practice_href: str,
) -> str:
    if not objects:
        return ""
    ordered = sorted(
        objects,
        key=lambda item: (
            item.get("source_order")
            if isinstance(item.get("source_order"), int)
            else 0,
            str(item.get("id") or ""),
        ),
    )
    rendered_objects = [
        _render_official_object(item) for item in ordered if isinstance(item, dict)
    ]
    rendered_objects = [item for item in rendered_objects if item]
    if not rendered_objects:
        return ""
    return "\n".join(
        [
            (
                '<section class="raya-official-practice" '
                'id="raya-official-practice" aria-label="Official practice">'
            ),
            "<h2>Official practice</h2>",
            (
                "<p>Official course prompts and checks for this page. Reveal support "
                "when you want it; nothing is submitted or saved.</p>"
            ),
            (
                '<p class="raya-official-practice-actions">'
                f'<a class="raya-official-practice-open" href="{html.escape(practice_href)}">'
                "Open all page practice</a>"
                "</p>"
            ),
            *rendered_objects,
            "</section>",
        ]
    )


def _render_official_object(item: dict[str, Any]) -> str:
    object_id = str(item.get("id") or "official-object")
    object_type = str(item.get("type") or "practice")
    object_type_class = _safe_map_fragment_id(object_type)
    body = _render_official_content(item)
    if not body:
        return ""
    return "\n".join(
        [
            (
                f'<article class="raya-official-object raya-official-{html.escape(object_type_class, quote=True)}" '
                f'id="raya-official-{html.escape(_safe_map_fragment_id(object_id), quote=True)}">'
            ),
            '<header class="raya-official-object-header">',
            (
                f'<span class="raya-official-kind">'
                f"{html.escape(_official_type_label(object_type))}</span>"
            ),
            '<span class="raya-official-authority">official</span>',
            "</header>",
            body,
            "</article>",
        ]
    )


def _render_official_content(item: dict[str, Any]) -> str:
    content = item.get("content")
    if not isinstance(content, dict):
        return ""
    object_type = str(item.get("type") or "")
    if object_type == "card":
        front = _official_text(content.get("front"))
        back = _official_text(content.get("back"))
        parts = []
        if front:
            parts.append(f'<p class="raya-official-prompt">{front}</p>')
        if back:
            parts.append(
                _official_reveal("Reveal answer", back, "raya-official-answer")
            )
        return "\n".join(parts)
    if object_type == "prompt":
        prompt = _official_text(content.get("prompt"))
        return f'<p class="raya-official-prompt">{prompt}</p>' if prompt else ""
    if object_type == "quiz":
        return _render_official_quiz(content)
    return _render_generic_official_content(content)


def _render_official_quiz(content: dict[str, Any]) -> str:
    questions = content.get("questions")
    if not isinstance(questions, list):
        return ""
    rendered_questions = []
    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            continue
        prompt = _official_text(question.get("prompt"))
        options = question.get("options")
        if not prompt and not isinstance(options, list):
            continue
        parts = [
            (
                f'<section class="raya-official-question" aria-label="Question {index}" '
                'data-raya-official-quiz-question data-raya-official-quiz-state="ready">'
            )
        ]
        if prompt:
            parts.append(f'<p class="raya-official-prompt">{prompt}</p>')
        if isinstance(options, list):
            option_items = []
            correct_labels = []
            for option in options:
                if not isinstance(option, dict):
                    continue
                label = _official_text(option.get("label"))
                if not label:
                    continue
                correct = option.get("correct") is True
                option_items.append(
                    "<li>"
                    '<button type="button" class="raya-official-option" '
                    "data-raya-official-quiz-option "
                    f'data-raya-official-quiz-correct="{str(correct).lower()}">'
                    f"{label}"
                    "</button>"
                    "</li>"
                )
                if correct:
                    correct_labels.append(label)
            if option_items:
                parts.append(
                    '<ol class="raya-official-options">'
                    + "".join(option_items)
                    + "</ol>"
                )
                parts.append(
                    '<p class="raya-official-quiz-feedback" '
                    'data-raya-official-quiz-feedback aria-live="polite">'
                    "Choose an option.</p>"
                )
                parts.append(
                    '<button type="button" class="raya-official-quiz-reset" '
                    "data-raya-official-quiz-reset hidden>Try again</button>"
                )
            if correct_labels:
                parts.append(
                    _official_reveal(
                        "Reveal correct option",
                        _official_list(correct_labels, label="Correct option"),
                        "raya-official-answer",
                    )
                )
        parts.append("</section>")
        rendered_questions.append("\n".join(parts))
    return "\n".join(rendered_questions)


def _render_generic_official_content(content: dict[str, Any]) -> str:
    visible_fields = [
        ("title", "Title"),
        ("summary", "Summary"),
        ("prompt", "Prompt"),
        ("instructions", "Instructions"),
        ("body", "Details"),
        ("question", "Question"),
    ]
    support_fields = [("answer", "Reveal answer"), ("solution", "Reveal solution")]
    parts: list[str] = []
    for field, label in visible_fields:
        value = _official_text(content.get(field))
        if value:
            parts.append(f"<p><strong>{html.escape(label)}:</strong> {value}</p>")
    for field, summary in support_fields:
        value = _official_text(content.get(field))
        if value:
            parts.append(_official_reveal(summary, value, "raya-official-answer"))
    return "\n".join(parts)


def _official_type_label(object_type: str) -> str:
    labels = {
        "assignment": "Assignment",
        "card": "Card",
        "exam": "Exam",
        "example": "Example",
        "project": "Project",
        "prompt": "Prompt",
        "quiz": "Quiz",
        "task": "Task",
    }
    return labels.get(object_type, "Practice")


def _official_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "; ".join(
            text for text in (_official_text(item) for item in value) if text
        )
    if isinstance(value, dict):
        return "; ".join(
            f"{html.escape(str(key))}: {text}"
            for key, text in (
                (str(key), _official_text(item)) for key, item in value.items()
            )
            if text
        )
    return html.escape(str(value))


def _official_list(values: list[str], *, label: str) -> str:
    items = "".join(
        f"<li><strong>{html.escape(label)}:</strong> {value}</li>" for value in values
    )
    return f'<ul class="raya-official-answer-list">{items}</ul>'


def _official_reveal(summary: str, body: str, class_name: str) -> str:
    return "\n".join(
        [
            f'<details class="raya-official-reveal {html.escape(class_name, quote=True)}">',
            f"<summary>{html.escape(summary)}</summary>",
            f'<div class="raya-official-reveal-body">{body}</div>',
            "</details>",
        ]
    )


def _render_generated_index(
    page: ContentPage,
    content_model: ContentModel,
    official_counts: dict[str, dict[str, int]],
) -> str:
    child_ids = content_model.children_by_parent.get(page.id, [])
    counts = _aggregate_study_counts(page.id, content_model, official_counts)
    if not child_ids and not counts:
        return ""

    section_class = (
        "raya-generated-index raya-section-landing"
        if child_ids
        else "raya-generated-index"
    )
    parts = [f'<section class="{section_class}" aria-label="Generated index">']
    if child_ids:
        heading = "Course Index" if page.parent_id is None else "Topics"
        heading_id = (
            "raya-generated-course-index"
            if page.parent_id is None
            else "raya-generated-topics"
        )
        parts.append(f'<h2 id="{heading_id}">{html.escape(heading)}</h2>')
        parts.append('<ol class="raya-section-card-list">')
        for child_id in child_ids:
            child = content_model.pages_by_id[child_id]
            href = _relative_href(page.output_path, child.output_path)
            child_counts = _aggregate_study_counts(
                child.id,
                content_model,
                official_counts,
            )
            meta_items = []
            if child.estimated_time:
                meta_items.append(f"Estimated time: {child.estimated_time}")
            if child_counts:
                meta_items.append(_study_counts_text(child_counts))
            parts.append('<li class="raya-section-card">')
            parts.append(
                f'<a class="raya-section-card-link" href="{html.escape(href)}">'
                f'<span class="raya-section-card-title">'
                f"{html.escape(_navigation_label(child))}"
                "</span>"
            )
            if child.summary:
                parts.append(
                    f'<span class="raya-section-card-summary">'
                    f"{html.escape(child.summary)}"
                    "</span>"
                )
            if meta_items:
                parts.append(
                    f'<span class="raya-section-card-meta">'
                    f"{html.escape(' | '.join(meta_items))}"
                    "</span>"
                )
            parts.append("</a>")
            parts.append("</li>")
        parts.append("</ol>")
    if counts:
        parts.append('<h2 id="raya-generated-study">Study</h2>')
        parts.append(f"<p>{html.escape(_study_counts_text(counts))}</p>")
    parts.append("</section>")
    return "\n".join(parts)


def _pages_index(course_id: str, pages: list[ContentPage]) -> dict[str, Any]:
    return {
        "course_id": course_id,
        "pages": [
            {
                "path": page.rel_path,
                "url": page.output_path,
                "title": page.title,
                "nav_title": page.nav_title,
                "summary": page.summary,
                "quantum_id": page.id,
                "aliases": list(page.aliases),
                "status": page.status,
                "estimated_time": page.estimated_time,
                "tags": list(page.tags),
                "prerequisites": list(page.prerequisites),
                "hierarchy_key": page.hierarchy_key,
                "hierarchy_label": page.hierarchy_label,
                "label": page.display_label,
            }
            for page in pages
        ],
    }


def _quanta_index(course_id: str, pages: list[ContentPage]) -> dict[str, Any]:
    quanta = []
    for page in pages:
        item = {
            "id": page.id,
            "type": page.hierarchy_key,
            "path": page.rel_path,
            "title": page.title,
            "summary": page.summary,
            "aliases": list(page.aliases),
            "status": page.status,
            "label": page.display_label,
        }
        if page.parent_id is not None:
            item["parent"] = page.parent_id
        quanta.append(item)
    return {"course_id": course_id, "quanta": quanta}


def _links_index(
    course_id: str,
    content_model: ContentModel,
    pages_by_reference: dict[str, ContentPage],
    pages_by_source: dict[Path, ContentPage],
    course_root: Path,
    wikilink_resolver: WikilinkResolver,
) -> dict[str, Any]:
    links: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    def add_link(source: str, target: str, kind: str) -> None:
        key = (source, target, kind)
        if key in seen:
            return
        seen.add(key)
        links.append({"from": source, "to": target, "kind": kind})

    for page in content_model.pages:
        if page.parent_id and page.parent_id in content_model.pages_by_id:
            add_link(page.parent_id, page.id, "navigation")
            add_link(page.id, page.parent_id, "parent")
        for prerequisite in page.prerequisites:
            target_page = pages_by_reference.get(prerequisite)
            if target_page is not None:
                add_link(page.id, target_page.id, "prerequisite")
        for link in extract_markdown_links(page.body):
            kind = classify_markdown_target(link.target)
            if kind == "stable":
                target_page = pages_by_reference.get(stable_markdown_id(link.target))
                if target_page is not None:
                    add_link(page.id, target_page.id, "content")
                continue
            if kind != "content":
                continue
            target_page = _target_content_page(
                page,
                link.target,
                pages_by_source,
                course_root,
            )
            if target_page is not None:
                add_link(page.id, target_page.id, "content")
        for wikilink in extract_wikilinks(page.body):
            target_page = wikilink_resolver.resolve(wikilink.target).page
            if target_page is not None:
                add_link(page.id, target_page.id, "content")
    return {"course_id": course_id, "links": links}


def _graph_index(
    course_id: str,
    content_model: ContentModel,
    links_index: dict[str, Any],
) -> dict[str, Any]:
    group_by_page = _graph_group_by_page(content_model)
    nodes = [
        {
            "id": page.id,
            "title": page.title,
            "nav_title": page.nav_title,
            "url": page.output_path,
            "group": group_by_page.get(page.id, ""),
            "order": index,
            "status": page.status,
            "tags": list(page.tags),
        }
        for index, page in enumerate(content_model.pages, start=1)
    ]
    edges = [
        {
            "from": link["from"],
            "to": link["to"],
            "kind": link["kind"],
            "source": "links",
        }
        for link in links_index["links"]
    ]
    groups = [
        {
            "id": page.id,
            "title": page.nav_title or page.title,
            "order": index,
        }
        for index, page in enumerate(
            (
                content_model.pages_by_id[page_id]
                for page_id in content_model.children_by_parent.get(
                    content_model.root_id or "",
                    [],
                )
            ),
            start=1,
        )
    ]
    pages_by_id = content_model.pages_by_id
    backlinks: dict[str, list[dict[str, str]]] = {
        page.id: [] for page in content_model.pages
    }
    for edge in edges:
        if edge["kind"] not in {"content", "prerequisite"}:
            continue
        source = pages_by_id.get(edge["from"])
        target = pages_by_id.get(edge["to"])
        if source is None or target is None:
            continue
        backlinks[target.id].append(
            {
                "from": source.id,
                "title": source.title,
                "url": source.output_path,
                "kind": edge["kind"],
            }
        )
    return {
        "version": 1,
        "course_id": course_id,
        "nodes": nodes,
        "edges": edges,
        "groups": groups,
        "backlinks": backlinks,
    }


def _graph_context_by_page(
    content_model: ContentModel,
    graph_index: dict[str, Any],
) -> dict[str, dict[str, list[dict[str, str]]]]:
    pages_by_id = content_model.pages_by_id
    context: dict[str, dict[str, list[dict[str, str]]]] = {
        page.id: {"outgoing": [], "incoming": []} for page in content_model.pages
    }
    outgoing_counts = {page.id: 0 for page in content_model.pages}
    incoming_counts = {page.id: 0 for page in content_model.pages}
    seen: set[tuple[str, str, str]] = set()
    content_edges: list[tuple[ContentPage, ContentPage, str]] = []
    for edge in graph_index["edges"]:
        if edge["kind"] != "content":
            continue
        source = pages_by_id.get(edge["from"])
        target = pages_by_id.get(edge["to"])
        if source is None or target is None or source.id == target.id:
            continue
        key = (source.id, target.id, edge["kind"])
        if key in seen:
            continue
        seen.add(key)
        content_edges.append((source, target, edge["kind"]))
        outgoing_counts[source.id] += 1
        incoming_counts[target.id] += 1
    for source, target, kind in content_edges:
        target_context = _public_graph_page_context(
            target,
            outgoing_count=outgoing_counts[target.id],
            incoming_count=incoming_counts[target.id],
        )
        target_context["kind"] = kind
        context[source.id]["outgoing"].append(target_context)
        source_context = _public_graph_page_context(
            source,
            outgoing_count=outgoing_counts[source.id],
            incoming_count=incoming_counts[source.id],
        )
        source_context["kind"] = kind
        context[target.id]["incoming"].append(source_context)
    return context


def _public_graph_page_context(
    page: ContentPage,
    *,
    outgoing_count: int,
    incoming_count: int,
) -> dict[str, str]:
    data = {
        "id": page.id,
        "title": page.nav_title or page.title,
        "url": page.output_path,
        "outgoing_count": str(outgoing_count),
        "incoming_count": str(incoming_count),
    }
    if page.summary:
        data["summary"] = page.summary
    if page.status:
        data["status"] = page.status
    return data


def _graph_group_by_page(content_model: ContentModel) -> dict[str, str]:
    groups: dict[str, str] = {}
    root_id = content_model.root_id
    top_level = set(content_model.children_by_parent.get(root_id or "", []))
    for page in content_model.pages:
        if page.id in top_level:
            groups[page.id] = page.id
            continue
        ancestor = page.parent_id
        selected = ""
        while ancestor:
            if ancestor in top_level:
                selected = ancestor
                break
            ancestor_page = content_model.pages_by_id.get(ancestor)
            ancestor = ancestor_page.parent_id if ancestor_page is not None else None
        groups[page.id] = selected
    return groups


def _navigation_index(course_id: str, content_model: ContentModel) -> dict[str, Any]:
    flat = _flatten_navigation(content_model)
    previous_next: dict[str, tuple[str | None, str | None]] = {}
    for index, page_id in enumerate(flat):
        previous_next[page_id] = (
            flat[index - 1] if index > 0 else None,
            flat[index + 1] if index < len(flat) - 1 else None,
        )
    items = []
    for page in content_model.pages:
        previous, next_page = previous_next.get(page.id, (None, None))
        items.append(
            {
                "id": page.id,
                "path": page.rel_path,
                "url": page.output_path,
                "title": page.title,
                "nav_title": page.nav_title,
                "label": page.display_label,
                "hierarchy_key": page.hierarchy_key,
                "hierarchy_label": page.hierarchy_label,
                "parent": page.parent_id,
                "children": content_model.children_by_parent.get(page.id, []),
                "breadcrumbs": [
                    crumb.id for crumb in _breadcrumb_pages(page, content_model)
                ],
                "previous": previous,
                "next": next_page,
            }
        )
    return {
        "course_id": course_id,
        "root": content_model.root_id or "",
        "items": items,
    }


def _indices_index(
    course_id: str,
    content_model: ContentModel,
    official_counts: dict[str, dict[str, int]],
) -> dict[str, Any]:
    local = []
    for page in content_model.pages:
        child_ids = content_model.children_by_parent.get(page.id, [])
        local.append(
            {
                "id": page.id,
                "entries": [
                    _index_entry(
                        content_model.pages_by_id[child_id],
                        official_counts,
                        content_model,
                    )
                    for child_id in child_ids
                ],
                "study_counts": _aggregate_study_counts(
                    page.id,
                    content_model,
                    official_counts,
                ),
            }
        )
    master = [
        _index_entry(
            content_model.pages_by_id[child_id], official_counts, content_model
        )
        for child_id in content_model.children_by_parent.get(content_model.root_id, [])
    ]
    return {
        "course_id": course_id,
        "local": local,
        "master": master,
    }


def _index_entry(
    page: ContentPage,
    official_counts: dict[str, dict[str, int]],
    content_model: ContentModel,
) -> dict[str, Any]:
    return {
        "id": page.id,
        "url": page.output_path,
        "label": page.display_label,
        "title": page.title,
        "summary": page.summary,
        "estimated_time": page.estimated_time,
        "study_counts": _aggregate_study_counts(
            page.id, content_model, official_counts
        ),
        "hierarchy_key": page.hierarchy_key,
        "hierarchy_label": page.hierarchy_label,
    }


def _navigation_label(page: ContentPage) -> str:
    parts: list[str] = []
    if page.hierarchy_key == "appendix":
        parts.append(page.hierarchy_label)
    if page.display_label:
        parts.append(page.display_label)
    parts.append(page.nav_title)
    return " ".join(part for part in parts if part).strip()


def _target_content_page(
    page: ContentPage,
    target: str,
    pages_by_source: dict[Path, ContentPage],
    course_root: Path,
) -> ContentPage | None:
    target_path = resolve_local_markdown_target(
        source_path=page.source_path,
        course_root=course_root,
        target_path=markdown_link_path(target),
    )
    return pages_by_source.get(target_path)


def _target_asset_href(
    page: ContentPage,
    target: str,
    course_root: Path,
    source_dir: Path,
) -> str | None:
    asset_ref = resolve_course_asset_reference(
        source_path=page.source_path,
        course_root=course_root,
        source_dir=source_dir,
        target_path=markdown_link_path(target),
    )
    if asset_ref.kind != "colocated" or asset_ref.output_path is None:
        return None
    static_asset_path = (STATIC_ASSETS_PATH / asset_ref.output_path).as_posix()
    return _relative_href(page.output_path, static_asset_path)


def _target_reference_href(
    page: ContentPage,
    target: str,
    course_root: Path,
    source_dir: Path,
    kind: str,
) -> str | None:
    reference = resolve_course_reference(
        source_path=page.source_path,
        course_root=course_root,
        source_dir=source_dir,
        target_path=markdown_link_path(target),
        kind=kind,
    )
    if reference.status != "referenced" or reference.output_path is None:
        return None
    static_file_path = (STATIC_FILES_PATH / reference.output_path).as_posix()
    return _relative_href(page.output_path, static_file_path)


def _collect_source_references(
    course_id: str,
    content_model: ContentModel,
    course_root: Path,
    source_dir: Path,
    runtime_model: RuntimeModel,
    report: ValidationReport,
) -> list[SourceReference]:
    references: list[SourceReference] = []
    seen: set[tuple[str, Path]] = set()
    for page in content_model.pages:
        for link in extract_markdown_links(page.body):
            kind = classify_markdown_target(link.target)
            if kind not in {"code", "notebook"}:
                continue
            resolved = resolve_course_reference(
                source_path=page.source_path,
                course_root=course_root,
                source_dir=source_dir,
                target_path=markdown_link_path(link.target),
                kind=kind,
            )
            if (
                resolved.status != "referenced"
                or resolved.output_path is None
                or not resolved.target_path.is_file()
            ):
                continue
            if kind == "notebook" and notebook_validation_error(resolved.target_path):
                continue
            key = (page.id, resolved.target_path.resolve())
            if key in seen:
                continue
            seen.add(key)
            source_rel_path = resolved.target_path.relative_to(source_dir).as_posix()
            artifact_path = (Path("files") / resolved.output_path).as_posix()
            browser_path = (STATIC_FILES_PATH / resolved.output_path).as_posix()
            execution = reference_execution_metadata(
                reference_source_path=resolved.target_path,
                model=runtime_model,
            )
            references.append(
                SourceReference(
                    id=source_reference_id(course_id, page.id, resolved.output_path),
                    page_id=page.id,
                    page_source_path=page.rel_path,
                    label=link.label,
                    target=link.target,
                    kind=kind,
                    format=reference_format(kind),
                    source_path=resolved.target_path,
                    source_rel_path=source_rel_path,
                    output_path=resolved.output_path,
                    artifact_path=artifact_path,
                    browser_path=browser_path,
                    sha256=_file_sha256(resolved.target_path),
                    execution_policy=execution["policy"],
                    runtime_profile=execution.get("profile"),
                )
            )
            report.read_file(resolved.target_path)
    return references


def _references_by_page(
    references: list[SourceReference],
) -> dict[str, list[SourceReference]]:
    grouped: dict[str, list[SourceReference]] = defaultdict(list)
    for reference in references:
        grouped[reference.page_id].append(reference)
    return dict(grouped)


def _copy_reference_files(
    references: list[SourceReference],
    artifact_files_dir: Path,
    site_files_dir: Path,
    report: ValidationReport,
) -> int:
    copied = 0
    seen: set[str] = set()
    for reference in references:
        if reference.output_path in seen:
            continue
        seen.add(reference.output_path)
        for root in (artifact_files_dir, site_files_dir):
            target_path = root / reference.output_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(reference.source_path, target_path)
            report.wrote_output(target_path)
        copied += 1
    return copied


def _copy_reviewed_output_files(
    reviewed_outputs: list[ReviewedOutput],
    artifact_dir: Path,
    site_dir: Path,
    report: ValidationReport,
) -> int:
    copied = 0
    seen: set[tuple[Path, Path]] = set()
    for reviewed in reviewed_outputs:
        for reviewed_file in reviewed.files:
            for target_path in (
                artifact_dir / reviewed_file.artifact_path(reviewed),
                site_dir / reviewed_file.browser_path(reviewed),
            ):
                key = (reviewed_file.path.resolve(), target_path.resolve())
                if key in seen:
                    continue
                seen.add(key)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(reviewed_file.path, target_path)
                report.wrote_output(target_path)
            copied += 1
    return copied


def _references_index(
    course_id: str,
    references: list[SourceReference],
    reviewed_by_reference: dict[str, ReviewedOutput],
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for reference in references:
        item = reference.to_index_item()
        reviewed = reviewed_by_reference.get(reference.id)
        if reviewed is not None:
            execution = item.setdefault("execution", {})
            if isinstance(execution, dict):
                execution["reviewed_output"] = {
                    "status": "current",
                    "id": reviewed.id,
                    "authority": reviewed.authority,
                    "artifact_paths": [
                        reviewed_file.artifact_path(reviewed)
                        for reviewed_file in reviewed.files
                    ],
                    "browser_paths": [
                        reviewed_file.browser_path(reviewed)
                        for reviewed_file in reviewed.files
                    ],
                }
        items.append(item)
    return {
        "course_id": course_id,
        "references": items,
    }


def _render_reference_panel(
    page: ContentPage,
    references: list[SourceReference],
    reviewed_by_reference: dict[str, ReviewedOutput],
) -> str:
    if not references:
        return ""
    parts = [
        (
            '<section class="raya-reference-panel" '
            f'aria-label="Referenced work" data-raya-surface="{SURFACE_SUPPORT_PANEL}">'
        )
    ]
    parts.append("<h2>Referenced Work</h2>")
    parts.append(
        "<p>These files are copied for reading and download. They were not executed during build.</p>"
    )
    parts.append("<ul>")
    for reference in references:
        href = _relative_href(page.output_path, reference.browser_path)
        label = "Notebook" if reference.kind == "notebook" else "Script"
        reviewed = reviewed_by_reference.get(reference.id)
        status = "reviewed output current" if reviewed is not None else "not executed"
        parts.append(
            f'<li class="raya-reference-item raya-reference-{html.escape(reference.kind)}">'
        )
        parts.append(
            f"<p><strong>{label}</strong>: "
            f'<a href="{html.escape(href)}">{html.escape(Path(reference.source_rel_path).name)}</a> '
            f'<span class="raya-reference-status">{html.escape(status)}</span></p>'
        )
        preview = _reference_preview(reference)
        if preview:
            parts.append(preview)
        parts.append("</li>")
    parts.append("</ul>")
    parts.append("</section>")
    return "\n".join(parts)


def _render_reviewed_output_panel(
    page: ContentPage,
    reviewed_outputs: list[ReviewedOutput],
) -> str:
    if not reviewed_outputs:
        return ""
    parts = [
        (
            '<section class="raya-reviewed-output-panel" '
            f'aria-label="Reviewed execution output" data-raya-surface="{SURFACE_SUPPORT_PANEL}">'
        )
    ]
    parts.append("<h2>Reviewed Output</h2>")
    parts.append(
        "<p>Reviewed course support. Build and static serving did not execute code.</p>"
    )
    parts.append("<ul>")
    for reviewed in reviewed_outputs:
        parts.append('<li class="raya-reviewed-output-item">')
        parts.append(
            f"<p><strong>{html.escape(reviewed.id)}</strong>: "
            f"reviewed {html.escape(reviewed.kind)} output "
            f'<span class="raya-reviewed-output-status">{html.escape(reviewed.status)}</span></p>'
        )
        parts.append("<ul>")
        for reviewed_file in reviewed.files:
            href = _relative_href(
                page.output_path, reviewed_file.browser_path(reviewed)
            )
            parts.append(
                f'<li><a href="{html.escape(href)}">{html.escape(reviewed_file.rel_path)}</a> '
                f"<span>{html.escape(reviewed_file.kind)}</span></li>"
            )
        parts.append("</ul>")
        excerpt = _reviewed_output_excerpt(reviewed)
        if excerpt:
            parts.append(excerpt)
        parts.append("</li>")
    parts.append("</ul>")
    parts.append("</section>")
    return "\n".join(parts)


def _write_inspection_surface(
    *,
    site_dir: Path,
    site_assets_dir: Path,
    content_model: ContentModel,
    course_title: str,
    language: str,
    graph_index: dict[str, Any],
    references: list[SourceReference],
    reviewed_outputs: list[ReviewedOutput],
    report: ValidationReport,
) -> None:
    output_path = site_dir / STATIC_INSPECTION_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        _render_inspection_surface(
            site_assets_dir=site_assets_dir,
            content_model=content_model,
            course_title=course_title,
            language=language,
            graph_index=graph_index,
            references=references,
            reviewed_outputs=reviewed_outputs,
        ),
        encoding="utf-8",
    )
    report.wrote_output(output_path)


def _render_inspection_surface(
    *,
    site_assets_dir: Path,
    content_model: ContentModel,
    course_title: str,
    language: str,
    graph_index: dict[str, Any],
    references: list[SourceReference],
    reviewed_outputs: list[ReviewedOutput],
) -> str:
    stylesheet_href = _relative_href(
        STATIC_INSPECTION_PATH.as_posix(),
        RENDER_STYLESHEET_PATH,
    )
    skin_stylesheet_href = _relative_href(
        STATIC_INSPECTION_PATH.as_posix(),
        SKIN_STYLESHEET_PATH,
    )
    page_items = []
    for page in content_model.pages:
        href = _relative_href(STATIC_INSPECTION_PATH.as_posix(), page.output_path)
        page_items.append(
            "<li>"
            f'<a href="{html.escape(href)}">{html.escape(page.title)}</a> '
            f"<span>{html.escape(page.id)}</span>"
            "</li>"
        )

    graph_node_items = []
    for node in graph_index["nodes"]:
        href = _relative_href(STATIC_INSPECTION_PATH.as_posix(), node["url"])
        graph_node_items.append(
            f'<li><a href="{html.escape(href)}">{html.escape(node["title"])}</a></li>'
        )
    edge_kind_counts: dict[str, int] = {}
    for edge in graph_index["edges"]:
        kind = str(edge["kind"])
        edge_kind_counts[kind] = edge_kind_counts.get(kind, 0) + 1
    edge_kind_items = [
        f"<li>{html.escape(kind)}: {count}</li>"
        for kind, count in sorted(edge_kind_counts.items())
    ]
    group_items = [
        f"<li>{html.escape(group['title'])}</li>" for group in graph_index["groups"]
    ]

    reference_items = []
    for reference in references:
        href = _relative_href(STATIC_INSPECTION_PATH.as_posix(), reference.browser_path)
        reference_items.append(
            "<li>"
            f"<strong>{html.escape(reference.kind)}</strong> "
            f'<a href="{html.escape(href)}">{html.escape(reference.source_rel_path)}</a>'
            "<dl>"
            f"<dt>Reference ID</dt><dd>{html.escape(reference.id)}</dd>"
            f"<dt>Policy</dt><dd>{html.escape(reference.execution_policy)}</dd>"
            f"<dt>Status</dt><dd>{html.escape(reference.execution_status)}</dd>"
            f"<dt>Profile</dt><dd>{html.escape(reference.runtime_profile or 'none')}</dd>"
            f"<dt>SHA-256</dt><dd>{html.escape(reference.sha256)}</dd>"
            f"<dt>Artifact path</dt><dd>{html.escape(reference.artifact_path)}</dd>"
            f"<dt>Browser path</dt><dd>{html.escape(reference.browser_path)}</dd>"
            "</dl>"
            "</li>"
        )

    reviewed_items = []
    for reviewed in reviewed_outputs:
        file_items = []
        for reviewed_file in reviewed.files:
            href = _relative_href(
                STATIC_INSPECTION_PATH.as_posix(),
                reviewed_file.browser_path(reviewed),
            )
            file_items.append(
                "<li>"
                f'<a href="{html.escape(href)}">{html.escape(reviewed_file.rel_path)}</a> '
                f"<span>{html.escape(reviewed_file.kind)}</span>"
                "</li>"
            )
        reviewed_items.append(
            "<li>"
            f"<strong>{html.escape(reviewed.id)}</strong>"
            "<dl>"
            f"<dt>Reference ID</dt><dd>{html.escape(reviewed.reference_id)}</dd>"
            f"<dt>Source path</dt><dd>{html.escape(reviewed.source_root_rel_path)}</dd>"
            f"<dt>Policy</dt><dd>{html.escape(reviewed.policy)}</dd>"
            f"<dt>Status</dt><dd>{html.escape(reviewed.status)}</dd>"
            f"<dt>Authority</dt><dd>{html.escape(reviewed.authority)}</dd>"
            f"<dt>Profile</dt><dd>{html.escape(reviewed.profile or 'none')}</dd>"
            f"<dt>Review key</dt><dd>{html.escape(reviewed.review_key)}</dd>"
            "</dl>"
            "<ul>" + "\n".join(file_items) + "</ul>"
            "</li>"
        )

    asset_items = []
    if site_assets_dir.exists():
        site_root = site_assets_dir.parents[1]
        for asset_path in sorted(
            path for path in site_assets_dir.rglob("*") if path.is_file()
        ):
            browser_path = asset_path.relative_to(site_root).as_posix()
            href = _relative_href(STATIC_INSPECTION_PATH.as_posix(), browser_path)
            asset_items.append(
                f'<li><a href="{html.escape(href)}">{html.escape(browser_path)}</a></li>'
            )

    return "\n".join(
        [
            "<!doctype html>",
            f'<html lang="{html.escape(language)}">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>Artifact Inspection - {html.escape(course_title)}</title>",
            f'<link rel="stylesheet" href="{html.escape(stylesheet_href)}">',
            f'<link rel="stylesheet" href="{html.escape(skin_stylesheet_href)}">',
            "</head>",
            f'<body data-raya-surface="{SURFACE_INSPECTION}" data-raya-skin="raya-default">',
            '<main class="raya-inspection-main">',
            "<h1>Artifact Inspection</h1>",
            (
                "<p>Surface tier: inspection. This static view is generated from "
                "manifest-declared artifact data for professors, contributors, and agents. "
                "Normal course pages remain the student-default surface.</p>"
            ),
            "<h2>Course Graph</h2>",
            (
                f"<p>{len(graph_index['nodes'])} page node(s), "
                f"{len(graph_index['edges'])} graph edge(s).</p>"
            ),
            "<p>Artifact data path: <code>data/graph.json</code></p>",
            "<h3>Edge kinds</h3>",
            "<ul>",
            "\n".join(edge_kind_items)
            if edge_kind_items
            else "<li>No graph edges.</li>",
            "</ul>",
            "<h3>Groups</h3>",
            "<ul>",
            "\n".join(group_items) if group_items else "<li>No graph groups.</li>",
            "</ul>",
            "<h3>Graph Pages</h3>",
            "<ul>",
            "\n".join(graph_node_items)
            if graph_node_items
            else "<li>No graph nodes.</li>",
            "</ul>",
            "<h2>Pages</h2>",
            "<ul>",
            "\n".join(page_items),
            "</ul>",
            "<h2>References</h2>",
            "<ul>",
            "\n".join(reference_items)
            if reference_items
            else "<li>No references.</li>",
            "</ul>",
            "<h2>Reviewed Outputs</h2>",
            "<ul>",
            "\n".join(reviewed_items)
            if reviewed_items
            else "<li>No reviewed outputs.</li>",
            "</ul>",
            "<h2>Browser Assets</h2>",
            "<ul>",
            "\n".join(asset_items) if asset_items else "<li>No browser assets.</li>",
            "</ul>",
            "</main>",
            "</body>",
            "</html>",
            "",
        ]
    )


def _public_discovery_page_payload(
    page: ContentPage,
    *,
    content_model: ContentModel,
    graph_index: dict[str, Any],
    official_counts: dict[str, dict[str, int]],
    from_path: str,
    search_from_path: str,
    graph_from_path: str,
    practice_from_path: str,
    tasks_from_path: str | None = None,
    schedule_from_path: str | None = None,
    official_by_page: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    previous_page, next_page = _previous_next_pages(page, content_model)
    counts = _aggregate_study_counts(page.id, content_model, official_counts)
    direct_counts = official_counts.get(page.id, {})
    page_objects = (official_by_page or {}).get(page.id, [])
    public_task_objects = [
        item for item in page_objects if _official_public_task_summary(item) is not None
    ]
    dated_task_objects = [
        item for item in public_task_objects if _official_task_event_date(item)
    ]
    return {
        "id": page.id,
        "stable_id": page.id,
        "title": page.title,
        "nav_title": page.nav_title,
        "summary": page.summary,
        "status": page.status,
        "tags": list(page.tags),
        "hierarchy_label": page.hierarchy_label,
        "url": _relative_href(from_path, page.output_path),
        "previous_url": (
            _relative_href(from_path, previous_page.output_path)
            if previous_page is not None
            else ""
        ),
        "next_url": (
            _relative_href(from_path, next_page.output_path)
            if next_page is not None
            else ""
        ),
        "graph_url": _href_with_query(
            _relative_href(graph_from_path, STATIC_GRAPH_PATH.as_posix()),
            {"page": page.id},
        ),
        "search_url": _href_with_query(
            _relative_href(search_from_path, STATIC_SEARCH_PATH.as_posix()),
            {"page": page.id},
        ),
        "practice_url": (
            _href_with_query(
                _relative_href(practice_from_path, STATIC_PRACTICE_PATH.as_posix()),
                {"page": page.id},
            )
            if direct_counts
            else ""
        ),
        "tasks_url": (
            _href_with_query(
                _relative_href(tasks_from_path, STATIC_TASKS_PATH.as_posix()),
                {"page": page.id},
            )
            if tasks_from_path is not None and public_task_objects
            else ""
        ),
        "schedule_url": (
            _href_with_query(
                _relative_href(schedule_from_path, STATIC_SCHEDULE_PATH.as_posix()),
                {"page": page.id},
            )
            if schedule_from_path is not None and dated_task_objects
            else ""
        ),
        "study_counts": counts,
        "link_counts": _graph_link_counts(page.id, graph_index),
    }


def _previous_next_pages(
    page: ContentPage,
    content_model: ContentModel,
) -> tuple[ContentPage | None, ContentPage | None]:
    flat = _flatten_navigation(content_model)
    try:
        index = flat.index(page.id)
    except ValueError:
        return None, None
    previous_id = flat[index - 1] if index > 0 else None
    next_id = flat[index + 1] if index < len(flat) - 1 else None
    return (
        content_model.pages_by_id.get(previous_id) if previous_id else None,
        content_model.pages_by_id.get(next_id) if next_id else None,
    )


def _graph_link_counts(page_id: str, graph_index: dict[str, Any]) -> dict[str, int]:
    connected: set[str] = set()
    outgoing = 0
    incoming = 0
    for edge in graph_index["edges"]:
        source = str(edge["from"])
        target = str(edge["to"])
        if source == page_id:
            outgoing += 1
            connected.add(target)
        if target == page_id:
            incoming += 1
            connected.add(source)
    connected.discard(page_id)
    return {
        "connected": len(connected),
        "incoming": incoming,
        "outgoing": outgoing,
    }


def _write_graph_surface(
    *,
    site_dir: Path,
    content_model: ContentModel,
    course_title: str,
    language: str,
    graph_index: dict[str, Any],
    official_counts: dict[str, dict[str, int]],
    official_by_page: dict[str, list[dict[str, Any]]],
    search_records: dict[str, dict[str, Any]],
    skin_context: SkinContext,
    report: ValidationReport,
) -> None:
    graph_path = site_dir / STATIC_GRAPH_PATH
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    report.wrote_output(graph_path.parent)
    graph_path.write_text(
        _render_graph_surface(
            content_model=content_model,
            course_title=course_title,
            language=language,
            graph_index=graph_index,
            official_counts=official_counts,
            official_by_page=official_by_page,
            search_records=search_records,
            skin_context=skin_context,
        ),
        encoding="utf-8",
    )
    report.wrote_output(graph_path)


def _render_graph_surface(
    *,
    content_model: ContentModel,
    course_title: str,
    language: str,
    graph_index: dict[str, Any],
    official_counts: dict[str, dict[str, int]],
    official_by_page: dict[str, list[dict[str, Any]]],
    search_records: dict[str, dict[str, Any]],
    skin_context: SkinContext,
) -> str:
    stylesheet_href = _relative_href(
        STATIC_GRAPH_PATH.as_posix(), RENDER_STYLESHEET_PATH
    )
    skin_stylesheet_href = _relative_href(
        STATIC_GRAPH_PATH.as_posix(),
        SKIN_STYLESHEET_PATH,
    )
    accessibility_css_href = _relative_href(
        STATIC_GRAPH_PATH.as_posix(),
        f"{ACCESSIBILITY_RESOURCE_PATH}/{OPEN_DYSLEXIC_CSS_NAME}",
    )
    accessibility_js_href = _relative_href(
        STATIC_GRAPH_PATH.as_posix(),
        f"{ACCESSIBILITY_RESOURCE_PATH}/{OPEN_DYSLEXIC_VOLATILE_JS_NAME}",
    )
    discovery_js_href = _relative_href(
        STATIC_GRAPH_PATH.as_posix(),
        Path(DISCOVERY_RESOURCE_PATH) / DISCOVERY_SCRIPT_NAME,
    )
    graph_js_href = _relative_href(
        STATIC_GRAPH_PATH.as_posix(),
        Path(GRAPH_RESOURCE_PATH) / GRAPH_SCRIPT_NAME,
    )
    root_skin = skin_id_for_source_path(
        content_model.pages[0].source_path, skin_context
    )
    browser_graph = _browser_graph_payload(
        content_model,
        graph_index,
        official_counts,
        official_by_page,
        search_records,
    )
    graph_payload = _json_script_text(browser_graph)
    group_buttons = _graph_group_filter_buttons(graph_index["groups"])
    edge_counts: dict[str, int] = defaultdict(int)
    for edge in browser_graph["edges"]:
        edge_counts[str(edge["from"])] += 1
        edge_counts[str(edge["to"])] += 1
    node_items = []
    for node in browser_graph["nodes"]:
        backlink_count = len(browser_graph["backlinks"].get(node["id"], []))
        edge_count = edge_counts[node["id"]]
        node_items.append(
            f'<li data-raya-graph-node="{html.escape(node["id"], quote=True)}">'
            '<div class="raya-graph-list-title-row">'
            f'<a href="{html.escape(node["url"])}">{html.escape(node["title"])}</a>'
            f'<span class="raya-graph-list-status">{html.escape(node["status"])}</span>'
            '<span class="raya-graph-list-search-role" '
            'data-raya-graph-list-search-role hidden></span>'
            "</div>"
            '<span class="raya-graph-list-metrics">'
            f'<span class="raya-graph-list-stable-id">Stable ID '
            f'{html.escape(node["stable_id"])}</span>'
            f'<span class="raya-graph-list-relationship-counts">'
            f"Explicit links: {edge_count}; Backlinks: {backlink_count}</span>"
            "</span>"
            f'<span class="raya-graph-list-summary">{html.escape(node["summary"])}</span>'
            "</li>"
        )
    return "\n".join(
        [
            "<!doctype html>",
            f'<html lang="{html.escape(language)}">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>Course Graph - {html.escape(course_title)}</title>",
            f'<link rel="stylesheet" href="{html.escape(stylesheet_href)}">',
            f'<link rel="stylesheet" href="{html.escape(skin_stylesheet_href)}">',
            f'<link rel="stylesheet" href="{html.escape(accessibility_css_href)}">',
            "</head>",
            (
                f'<body data-raya-surface="graph" '
                f'data-raya-skin="{html.escape(root_skin, quote=True)}">'
            ),
            '<a class="raya-skip-link" href="#raya-graph-main">Skip to graph</a>',
            _render_discovery_command_bar(
                course_title=course_title,
                workspace_label="Graph workspace",
                current_workspace="graph",
                home_href="../../index.html",
                search_href="../search/index.html",
                graph_href="index.html",
                practice_href="../practice/index.html",
                tasks_href="../tasks/index.html",
                schedule_href="../schedule/index.html",
            ),
            (
                '<main id="raya-graph-main" class="raya-graph-page" '
                'data-raya-graph-page data-raya-discovery-page '
                'data-raya-discovery-rail-state="expanded">'
            ),
            '<header class="raya-graph-header raya-discovery-header">',
            "<h1>Course Graph</h1>",
            (
                "<p>Explore pages, unit groups, prerequisites, and content references "
                "generated from this course.</p>"
            ),
            "</header>",
            (
                '<section class="raya-graph-reading-keys" '
                'data-raya-graph-reading-keys aria-label="Graph reading keys">'
                '<article data-raya-graph-reading-key="pages">'
                "<h2>Pages</h2>"
                "<p>Circles are pages. Color follows course groups.</p>"
                "</article>"
                '<article data-raya-graph-reading-key="arrows">'
                "<h2>Arrows</h2>"
                "<p>Arrows point source to target.</p>"
                "</article>"
                '<article data-raya-graph-reading-key="selection">'
                "<h2>Selection</h2>"
                "<p>Click inspects. Double-click or Enter opens.</p>"
                "</article>"
                '<article data-raya-graph-reading-key="filters">'
                "<h2>Filters</h2>"
                "<p>Relationship filters hide visible graph marks only. "
                "Source data stays unchanged.</p>"
                "</article>"
                "</section>"
            ),
            '<section class="raya-graph-controls raya-graph-toolbar" aria-label="Graph controls">',
            (
                '<div class="raya-graph-toolbar-group raya-graph-toolbar-primary" '
                'role="group" aria-label="Find pages">'
            ),
            '<span class="raya-graph-toolbar-label">Find pages</span>',
            '<label for="graph-search">Search</label>',
            '<input id="graph-search" type="search" autocomplete="off">',
            '<label for="graph-layout">Layout</label>',
            (
                '<select id="graph-layout">'
                '<option value="connections" selected>Connections</option>'
                '<option value="topology">Topology</option>'
                '<option value="cluster">Cluster</option>'
                '<option value="map">Map</option>'
                '<option value="radial">Radial</option>'
                '<option value="list">List</option>'
                "</select>"
            ),
            "</div>",
            (
                '<div class="raya-graph-toolbar-group raya-graph-edge-kind-filters" '
                'role="group" aria-label="Relationship filters">'
            ),
            '<span class="raya-graph-toolbar-label">Relationship filters</span>',
            (
                '<button type="button" class="raya-graph-edge-kind-filter" '
                'data-raya-graph-edge-kind-filter="navigation" '
                'aria-pressed="true">Navigation</button>'
            ),
            (
                '<button type="button" class="raya-graph-edge-kind-filter" '
                'data-raya-graph-edge-kind-filter="content" '
                'aria-pressed="true">Content</button>'
            ),
            (
                '<button type="button" class="raya-graph-edge-kind-filter" '
                'data-raya-graph-edge-kind-filter="prerequisite" '
                'aria-pressed="true">Prerequisite</button>'
            ),
            (
                '<button type="button" class="raya-graph-edge-kind-filter" '
                'data-raya-graph-edge-kind-filter="parent" '
                'aria-pressed="true">Parent</button>'
            ),
            "</div>",
            (
                '<div class="raya-graph-toolbar-group raya-graph-toolbar-viewport" '
                'role="group" aria-label="Canvas view">'
            ),
            '<span class="raya-graph-toolbar-label">Canvas view</span>',
            '<button id="graph-fit" type="button">Fit</button>',
            '<button id="graph-fit-selection" type="button" disabled>'
            "Fit selection</button>",
            '<button id="graph-zoom-in" type="button" aria-label="Zoom in graph">+</button>',
            '<button id="graph-zoom-out" type="button" aria-label="Zoom out graph">-</button>',
            '<button id="graph-reset-view" type="button" aria-label="Reset graph view">Reset</button>',
            "</div>",
            (
                '<span class="raya-graph-pan-controls raya-graph-toolbar-group '
                'raya-graph-toolbar-pan" role="group" aria-label="Move canvas">'
            ),
            '<span class="raya-graph-toolbar-label">Move canvas</span>',
            '<button type="button" data-raya-graph-pan="left" aria-label="Pan graph left">&#8592;</button>',
            '<button type="button" data-raya-graph-pan="right" aria-label="Pan graph right">&#8594;</button>',
            '<button type="button" data-raya-graph-pan="up" aria-label="Pan graph up">&#8593;</button>',
            '<button type="button" data-raya-graph-pan="down" aria-label="Pan graph down">&#8595;</button>',
            "</span>",
            (
                '<div class="raya-graph-toolbar-group raya-graph-toolbar-state" '
                'role="group" aria-label="Workspace">'
            ),
            '<span class="raya-graph-toolbar-label">Workspace</span>',
            (
                '<span class="raya-graph-active-state" '
                'data-raya-graph-active-state aria-live="polite">'
                "Ready: full graph</span>"
            ),
            '<button id="graph-reset" type="button">Reset graph</button>',
            '<button id="graph-expand" type="button" '
            'aria-pressed="false" aria-label="Expand graph focus mode">Focus</button>',
            "</div>",
            (
                '<p class="raya-graph-shortcut-hints" '
                'aria-label="Graph keyboard shortcuts">'
                '<span class="raya-graph-shortcut-hint" '
                'data-raya-graph-shortcut="search"><kbd>/</kbd><span>Search</span></span>'
                '<span class="raya-graph-shortcut-hint" '
                'data-raya-graph-shortcut="fit"><kbd>F</kbd><span>Fit</span></span>'
                '<span class="raya-graph-shortcut-hint" '
                'data-raya-graph-shortcut="reset"><kbd>R</kbd><span>Reset</span></span>'
                "</p>"
            ),
            "</section>",
            (
                '<p class="raya-graph-instructions">'
                "Hover or focus a page to inspect nearby structure. "
                "Click a graph page once to inspect it. "
                "Double-click a graph page to open it. "
                "When a graph page has keyboard focus, press Enter to open it."
                "</p>"
            ),
            '<section class="raya-discovery-workspace-shell" aria-label="Course discovery workspace">',
            _render_discovery_course_rail(
                content_model=content_model,
                course_title=course_title,
                current_workspace="graph",
                from_path=STATIC_GRAPH_PATH.as_posix(),
                graph_index=graph_index,
                official_by_page=official_by_page,
            ),
            (
                '<section class="raya-graph-workspace" '
                'aria-label="Graph inspection workspace">'
            ),
            (
                '<aside id="raya-graph-list-panel" class="raya-graph-list-panel" '
                'data-raya-graph-list-panel aria-label="Graph pages">'
            ),
            '<div class="raya-graph-panel-header">',
            "<h2>Pages</h2>",
            (
                '<p class="raya-graph-panel-rail-summary" '
                'data-raya-graph-panel-rail-summary="list" '
                'aria-hidden="true"></p>'
            ),
            (
                '<button type="button" data-raya-graph-toggle-panel="list" '
                'aria-controls="raya-graph-list-panel-body" aria-expanded="true" '
                'aria-label="Collapse graph pages panel">Hide</button>'
            ),
            "</div>",
            (
                '<div id="raya-graph-list-panel-body" class="raya-graph-panel-body" '
                'data-raya-graph-panel-body="list" aria-hidden="false">'
            ),
            '<section class="raya-graph-groups" aria-label="Graph groups">',
            "\n".join(group_buttons),
            "</section>",
            '<ol id="raya-graph-list" class="raya-graph-list">',
            "\n".join(node_items),
            "</ol>",
            "</div>",
            "</aside>",
            '<section class="raya-graph-map-panel" aria-label="Course graph map">',
            (
                '<p class="raya-graph-canvas-hint">'
                "Press / to search, F to fit, R to reset."
                "</p>"
            ),
            '<p id="graph-status" class="raya-graph-status" aria-live="polite"></p>',
            (
                '<p class="raya-graph-arrangement-status" '
                'data-raya-graph-arrangement-status aria-live="polite" hidden>'
                "Manual arrangement active. Reset graph restores the generated layout."
                "</p>"
            ),
            (
                '<section class="raya-graph-orientation" '
                'data-raya-graph-orientation aria-label="Graph orientation">'
                '<div class="raya-graph-orientation-main">'
                '<p class="raya-graph-orientation-counts" '
                'data-raya-graph-orientation-counts>'
                '0 visible page(s), 0 visible relationship(s)</p>'
                '<p class="raya-graph-orientation-selection">'
                '<span>Selected</span> '
                '<strong data-raya-graph-orientation-selected>None</strong>'
                "</p>"
                "</div>"
                '<dl class="raya-graph-orientation-meta">'
                '<div><dt>Layout</dt><dd data-raya-graph-orientation-layout>'
                "Connections</dd></div>"
                '<div><dt>Page focus</dt><dd data-raya-graph-orientation-page-focus>'
                "None</dd></div>"
                '<div><dt>Search</dt><dd data-raya-graph-orientation-query>'
                "None</dd></div>"
                '<div><dt>Filters</dt><dd data-raya-graph-orientation-filters>'
                "All groups and relationships visible</dd></div>"
                "<div><dt>Neighborhood</dt>"
                '<dd data-raya-graph-orientation-neighborhood>Off</dd></div>'
                "</dl>"
                '<p class="raya-graph-orientation-actions">'
                '<a data-raya-graph-orientation-open href="../../index.html" hidden>'
                "Open page</a>"
                '<button type="button" data-raya-graph-orientation-details hidden>'
                "Details</button>"
                '<button type="button" data-raya-graph-orientation-neighborhood-toggle '
                "hidden>Focus neighborhood</button>"
                '<button type="button" data-raya-graph-orientation-fit-selection '
                "hidden disabled>Fit selection</button>"
                '<button type="button" data-raya-graph-orientation-clear hidden>'
                "Clear selection</button>"
                "</p>"
                "</section>"
            ),
            (
                '<section class="raya-graph-canvas-legend" '
                'aria-label="Graph group legend">'
                "<h2>Groups</h2>"
                '<div class="raya-graph-canvas-legend-items">'
                + "\n".join(_graph_group_filter_buttons(graph_index["groups"]))
                + "</div>"
                "</section>"
            ),
            (
                '<svg id="raya-graph-canvas" class="raya-graph-canvas" '
                'role="img" aria-label="Course graph" tabindex="0"></svg>'
            ),
            (
                '<aside class="raya-graph-minimap-panel" aria-label="Graph overview">'
                "<h2>Overview</h2>"
                '<svg id="raya-graph-minimap" class="raya-graph-minimap" '
                'role="button" '
                'aria-label="Graph overview and current viewport; activate to center the graph view" '
                'aria-disabled="false" tabindex="0" focusable="true">'
                '<rect class="raya-graph-minimap-viewport" '
                'data-raya-graph-minimap-viewport hidden></rect>'
                "</svg>"
                '<p class="raya-graph-minimap-caption">'
                "The rectangle shows the visible canvas area."
                "</p>"
                "</aside>"
            ),
            (
                '<details class="raya-graph-guide" data-raya-graph-guide>'
                "<summary>Graph quick guide</summary>"
                '<div class="raya-graph-guide-cards">'
                '<article class="raya-graph-guide-card">'
                "<h3>Find</h3>"
                "<p>Search titles, stable IDs, tags, groups, and status. "
                "Arrow keys move results; Enter opens the active result.</p>"
                "</article>"
                '<article class="raya-graph-guide-card">'
                "<h3>Choose a view</h3>"
                "<p>Connections reads link flow. Topology follows relationships; "
                "Cluster groups pages. Other views are visual only.</p>"
                "</article>"
                '<article class="raya-graph-guide-card">'
                "<h3>Inspect</h3>"
                "<p>Hover or focus previews. Click once to select; double-click "
                "or press Enter to open.</p>"
                "</article>"
                '<article class="raya-graph-guide-card">'
                "<h3>Move</h3>"
                "<p>Pan, zoom, and fit change only this SVG viewport. Fit "
                "selection frames context. "
                '<span class="raya-graph-guide-desktop">'
                "On desktop, drag pages to tidy the map; "
                "</span>"
                '<span class="raya-graph-guide-mobile">'
                "Use Fit, zoom, and pan controls; "
                "</span>"
                "Reset graph restores the generated layout.</p>"
                "</article>"
                '<article class="raya-graph-guide-card">'
                "<h3>Filter</h3>"
                "<p>Filters hide visible graph marks only. They keep source "
                "data unchanged and can be cleared.</p>"
                "</article>"
                "</div>"
                "</details>"
            ),
            (
                '<section class="raya-graph-preview-bubble" '
                "data-raya-graph-preview-bubble hidden aria-hidden=\"true\">"
                '<p class="raya-graph-preview-kicker" '
                "data-raya-graph-preview-meta></p>"
                "<h2 data-raya-graph-preview-title>Graph page</h2>"
                "<p data-raya-graph-preview-summary></p>"
                '<p class="raya-graph-preview-counts" '
                "data-raya-graph-preview-counts></p>"
                "</section>"
            ),
            (
                '<section class="raya-graph-relationship-preview" '
                "data-raya-graph-relationship-preview hidden "
                'aria-hidden="true" aria-label="Graph relationship preview">'
                '<p class="raya-graph-relationship-preview-kicker" '
                "data-raya-graph-relationship-preview-kind></p>"
                "<h2>Relationship</h2>"
                '<p><strong data-raya-graph-relationship-preview-source></strong> '
                '<span data-raya-graph-relationship-preview-direction>'
                "source to target</span> "
                '<strong data-raya-graph-relationship-preview-target></strong></p>'
                '<p class="raya-graph-relationship-preview-actions">'
                '<button type="button" '
                "data-raya-graph-relationship-preview-source-action>"
                "Select source</button>"
                '<button type="button" '
                "data-raya-graph-relationship-preview-target-action>"
                "Select target</button>"
                '<button type="button" '
                "data-raya-graph-relationship-preview-kind-action>"
                "Focus this kind</button>"
                "</p>"
                "</section>"
            ),
            (
                '<section class="raya-graph-inspection-preview" '
                "data-raya-graph-inspection-preview hidden "
                'aria-label="Graph page preview" aria-live="polite">'
                '<div class="raya-graph-inspection-preview-header">'
                "<h2 data-raya-graph-inspection-preview-title>Page preview</h2>"
                "<p data-raya-graph-inspection-preview-meta></p>"
                "</div>"
                "<p data-raya-graph-inspection-preview-summary></p>"
                '<p class="raya-graph-inspection-preview-counts" '
                "data-raya-graph-inspection-preview-counts></p>"
                '<p class="raya-graph-inspection-preview-actions">'
                '<button type="button" data-raya-graph-inspection-preview-select>'
                "Inspect page</button>"
                '<a data-raya-graph-inspection-preview-open href="../../index.html">'
                "Open page</a>"
                "</p>"
                "</section>"
            ),
            "</section>",
            (
                '<aside id="raya-graph-inspector-panel" '
                'class="raya-graph-inspector-panel" '
                'data-raya-graph-inspector-panel aria-label="Graph inspector">'
            ),
            '<div class="raya-graph-panel-header">',
            "<h2>Inspector</h2>",
            (
                '<p class="raya-graph-panel-rail-summary" '
                'data-raya-graph-panel-rail-summary="inspector" '
                'aria-hidden="true"></p>'
            ),
            (
                '<button type="button" data-raya-graph-toggle-panel="inspector" '
                'aria-controls="raya-graph-inspector-panel-body" aria-expanded="true" '
                'aria-label="Collapse graph inspector panel">Hide</button>'
            ),
            "</div>",
            (
                '<div id="raya-graph-inspector-panel-body" '
                'class="raya-graph-panel-body" '
                'data-raya-graph-panel-body="inspector" aria-hidden="false">'
            ),
            (
                '<p class="raya-graph-hover-status" '
                'data-raya-graph-hover-status aria-live="polite"></p>'
            ),
            (
                '<details class="raya-graph-state raya-graph-debug" '
                'data-raya-graph-state-readout data-raya-graph-debug>'
                "<summary>Graph state</summary>"
                "<dl>"
                "<div><dt>Selected</dt><dd data-raya-graph-state-selected>none</dd></div>"
                "<div><dt>Page focus</dt><dd data-raya-graph-state-page-focus>none</dd></div>"
                "<div><dt>Search</dt><dd data-raya-graph-state-query>none</dd></div>"
                "<div><dt>Layout</dt><dd data-raya-graph-state-layout>connections</dd></div>"
                "<div><dt>Visible</dt><dd data-raya-graph-state-visible>"
                "0 visible node(s), 0 visible edge(s)</dd></div>"
                "<div><dt>Hidden groups</dt><dd data-raya-graph-state-hidden-groups>"
                "none</dd></div>"
                "<div><dt>Hidden edges</dt><dd data-raya-graph-state-hidden-edges>"
                "none</dd></div>"
                "<div><dt>Neighborhood</dt><dd data-raya-graph-state-neighborhood>"
                "off</dd></div>"
                "<div><dt>Share URL</dt><dd class=\"raya-graph-share-url\">"
                "<code data-raya-graph-state-url></code>"
                "<button type=\"button\" data-raya-graph-copy-url>Copy URL</button>"
                "<span data-raya-graph-copy-status aria-live=\"polite\"></span>"
                "</dd></div>"
                "</dl>"
                "</details>"
            ),
            '<section class="raya-graph-detail" aria-label="Selected page" data-raya-graph-detail>',
            "<p data-raya-graph-detail-empty>Select a page in the graph or list.</p>",
            (
                '<div data-raya-graph-detail-panel hidden tabindex="-1" '
                'role="region" aria-labelledby="raya-graph-detail-title">'
            ),
            '<div class="raya-graph-detail-header">',
            '<h2 id="raya-graph-detail-title" data-raya-graph-detail-title>'
            "Selected page</h2>",
            '<button type="button" data-raya-graph-detail-clear>Clear</button>',
            "</div>",
            '<p class="raya-graph-detail-summary" data-raya-graph-detail-summary></p>',
            '<p class="raya-graph-detail-meta" data-raya-graph-detail-meta></p>',
            (
                '<p class="raya-graph-detail-study-counts" '
                "data-raya-graph-detail-study-counts></p>"
            ),
            (
                '<section class="raya-graph-detail-sections" '
                "data-raya-graph-detail-sections hidden>"
                "<h3>Page sections</h3>"
                "<ol data-raya-graph-detail-section-list></ol>"
                "</section>"
            ),
            (
                '<section class="raya-graph-detail-study-objects" '
                "data-raya-graph-detail-study-objects hidden>"
                "<h3>Study objects</h3>"
                "<ul data-raya-graph-detail-study-object-list></ul>"
                "</section>"
            ),
            (
                '<section class="raya-graph-detail-key-objects" '
                "data-raya-graph-detail-key-objects hidden>"
                "<h3>Key objects</h3>"
                "<ol data-raya-graph-detail-key-object-list></ol>"
                "</section>"
            ),
            (
                '<p class="raya-graph-detail-neighborhood" '
                "data-raya-graph-detail-neighborhood></p>"
            ),
            (
                '<section class="raya-graph-detail-relationship-overview" '
                "data-raya-graph-detail-relationship-overview hidden>"
                "<h3>Relationship overview</h3>"
                '<p data-raya-graph-detail-relationship-overview-counts></p>'
                '<div class="raya-graph-relationship-overview-grid" '
                "data-raya-graph-relationship-overview-list></div>"
                "</section>"
            ),
            (
                '<section class="raya-graph-detail-relationship-chips" '
                "data-raya-graph-detail-relationship-chips hidden>"
                "<h3>Relationship types</h3>"
                '<div class="raya-graph-relationship-focus-bar" '
                "data-raya-graph-relationship-focus-bar>"
                '<p data-raya-graph-relationship-focus-summary>'
                "All selected-page relationships are visible.</p>"
                '<button type="button" class="raya-graph-relationship-focus-reset" '
                "data-raya-graph-relationship-focus-reset hidden>"
                "Show all relationships</button>"
                "</div>"
                '<div class="raya-graph-detail-relationship-chip-list" '
                "data-raya-graph-detail-relationship-chip-list></div>"
                "</section>"
            ),
            (
                '<section class="raya-graph-relationship-walkthrough" '
                "data-raya-graph-relationship-walkthrough hidden>"
                "<h3>Relationship walkthrough</h3>"
                '<p class="raya-graph-relationship-focus-status" '
                'data-raya-graph-relationship-focus-status aria-live="polite"></p>'
                '<div class="raya-graph-relationship-walkthrough-list" '
                "data-raya-graph-relationship-walkthrough-list></div>"
                "</section>"
            ),
            (
                '<section class="raya-graph-detail-reading-path" '
                "data-raya-graph-detail-reading-path>"
                "<h3>Reading path</h3>"
                '<p class="raya-graph-detail-reading-path-summary" '
                "data-raya-graph-detail-reading-path-summary></p>"
            ),
            '<p class="raya-graph-detail-actions raya-graph-detail-primary-actions">',
            (
                '<a class="raya-graph-detail-open-primary" '
                'data-raya-graph-detail-link href="../../index.html">'
                "Open selected page</a>"
            ),
            "</p>",
            '<p class="raya-graph-detail-actions raya-graph-detail-secondary-actions">',
            '<a data-raya-graph-detail-search-link href="../search/index.html">Find in search</a>',
            '<a data-raya-graph-detail-practice-link href="../practice/index.html">Open practice</a>',
            '<a data-raya-graph-detail-tasks-link hidden>Open tasks</a>',
            '<a data-raya-graph-detail-schedule-link hidden>Open schedule</a>',
            '<button type="button" data-raya-graph-focus-neighborhood hidden>Focus neighborhood</button>',
            "</p>",
            '<nav class="raya-graph-detail-sequence" data-raya-graph-detail-sequence '
            'aria-label="Selected page course order">',
            '<a class="raya-graph-detail-sequence-card" '
            'data-raya-graph-detail-previous href="../../index.html" hidden>Previous</a>',
            '<a class="raya-graph-detail-sequence-card" '
            'data-raya-graph-detail-current href="../../index.html">Selected page</a>',
            '<a class="raya-graph-detail-sequence-card" '
            'data-raya-graph-detail-next href="../../index.html" hidden>Next</a>',
            "</nav>",
            "</section>",
            '<div class="raya-graph-detail-links">',
            "<section>",
            "<h3>Links from this page</h3>",
            "<ul data-raya-graph-detail-outgoing></ul>",
            "</section>",
            "<section>",
            "<h3>Links to this page</h3>",
            "<ul data-raya-graph-detail-incoming></ul>",
            "</section>",
            "</div>",
            "</div>",
            "</section>",
            "</section>",
            '<section class="raya-graph-legend" aria-label="Graph legend">',
            (
                '<span class="raya-graph-legend-item" data-raya-graph-legend="node">'
                '<span class="raya-graph-legend-swatch raya-graph-legend-node"></span>'
                "Page node"
                "</span>"
            ),
            (
                '<span class="raya-graph-legend-item" data-raya-graph-legend="match">'
                '<span class="raya-graph-legend-swatch raya-graph-legend-match"></span>'
                "Search match"
                "</span>"
            ),
            (
                '<span class="raya-graph-legend-item" data-raya-graph-legend="selected">'
                '<span class="raya-graph-legend-swatch raya-graph-legend-selected"></span>'
                "Selected page"
                "</span>"
            ),
            (
                '<span class="raya-graph-legend-item" data-raya-graph-legend="neighbor">'
                '<span class="raya-graph-legend-swatch raya-graph-legend-neighbor"></span>'
                "Connected page"
                "</span>"
            ),
            (
                '<span class="raya-graph-legend-item" data-raya-graph-legend="edge-color">'
                '<span class="raya-graph-legend-line raya-graph-legend-edge-color"></span>'
                "Source group edge"
                "</span>"
            ),
            (
                '<span class="raya-graph-legend-item" data-raya-graph-legend="edge-navigation">'
                '<span class="raya-graph-legend-line raya-graph-legend-edge-navigation"></span>'
                "Navigation link"
                "</span>"
            ),
            (
                '<span class="raya-graph-legend-item" data-raya-graph-legend="edge-content">'
                '<span class="raya-graph-legend-line raya-graph-legend-edge-content"></span>'
                "Content reference"
                "</span>"
            ),
            (
                '<span class="raya-graph-legend-item" data-raya-graph-legend="edge-prerequisite">'
                '<span class="raya-graph-legend-line raya-graph-legend-edge-prerequisite"></span>'
                "Prerequisite metadata"
                "</span>"
            ),
            (
                '<span class="raya-graph-legend-item" data-raya-graph-legend="edge-parent">'
                '<span class="raya-graph-legend-line raya-graph-legend-edge-parent"></span>'
                "Parent link"
                "</span>"
            ),
            "</section>",
            '<details class="raya-graph-help" data-raya-graph-help>',
            "<summary>Graph controls</summary>",
            (
                "<p>Search filters pages by generated titles, labels, stable IDs, "
                "groups, tags, and status metadata.</p>"
            ),
            (
                "<p>Search spotlight keeps matching pages visually primary, "
                "keeps directly connected pages visible as context, and dims "
                "unrelated visible graph structure. The search spotlight is a "
                "structural readability cue only, not learner state or personal "
                "guidance.</p>"
            ),
            (
                "<p>When graph search is focused, Arrow keys move through "
                "visible page results and Enter opens the active result.</p>"
            ),
            (
                "<p><strong>Keyboard shortcuts:</strong> / focuses graph search, "
                "F fits the current graph view, and R resets graph filters and "
                "selection. Shortcuts are ignored while typing in form fields.</p>"
            ),
            (
                "<p>Click a graph page once to inspect it. Double-click a graph "
                "page to open it. When a graph page has keyboard focus, press "
                "Enter to open it.</p>"
            ),
            (
                "<p>Connections is the default layout. It arranges pages from "
                "explicit links and course order; positions are structural reading "
                "cues, not learner state or personal guidance.</p>"
            ),
            (
                "<p>Topology groups visible pages by explicit graph relationships. "
                "It is a structural readability cue only, not learner state "
                "or personal guidance.</p>"
            ),
            (
                "<p>Cluster groups visible pages by generated course group so "
                "nearby pages can be scanned together.</p>"
            ),
            (
                "<p>Hover and keyboard focus spotlight the inspected page and "
                "its directly connected pages. Other graph marks dim "
                "temporarily; this is only a readability cue.</p>"
            ),
            (
                "<p>Edge color follows the source page group so explicit links "
                "are easier to trace across the course; source-group edge "
                "colors are structural readability cues only.</p>"
            ),
            (
                "<p>Relationship line patterns distinguish navigation links, "
                "content references, prerequisite metadata, and parent links. "
                "They describe generated graph structure only, not learner "
                "state or personal guidance.</p>"
            ),
            (
                "<p>Graph arrows show link direction from the source page to "
                "the target page. Direction is generated graph structure.</p>"
            ),
            (
                "<p>Relationship filters hide or show relationship kinds in the SVG "
                "graph. They do not remove pages from the list or selected-page "
                "inspector.</p>"
            ),
            (
                "<p>Map groups pages by course structure, radial places visible "
                "pages around one circle, and list hides the SVG so links stay "
                "simple to scan.</p>"
            ),
            (
                "<p>Fit redraws the current layout. Reset graph clears search, group "
                "filters, selected page, and expanded graph workspace.</p>"
            ),
            (
                "<p>Fit selection frames the selected page and visible directly "
                "connected graph context. Fit selection changes only the SVG "
                "viewport; it does not change filters, selection, graph data, "
                "or learner state.</p>"
            ),
            (
                "<p>Zoom and Reset view change only the visual SVG graph view; "
                "the list and selected-page details remain complete.</p>"
            ),
            (
                "<p>Drag the graph canvas, use pan buttons, or focus the graph "
                "and use Arrow keys to move the viewport. Pan changes only the "
                "viewport.</p>"
            ),
            (
                "<p>Drag individual graph pages to untangle the visible SVG "
                "while reading. Manual positions are temporary browser-side "
                "readability cues; Reset graph or changing layout restores the "
                "generated structure.</p>"
            ),
            "</details>",
            "</div>",
            "</aside>",
            "</section>",
            '<script type="application/json" id="raya-graph-data">',
            graph_payload,
            "</script>",
            "</main>",
            f'<script src="{html.escape(accessibility_js_href)}" defer></script>',
            f'<script src="{html.escape(discovery_js_href)}" defer></script>',
            f'<script src="{html.escape(graph_js_href)}" defer></script>',
            "</body>",
            "</html>",
            "",
        ]
    )


def _graph_group_filter_buttons(groups: list[dict[str, Any]]) -> list[str]:
    buttons: list[str] = []
    for index, group in enumerate(groups):
        group_color = GRAPH_GROUP_COLORS[index % len(GRAPH_GROUP_COLORS)]
        buttons.append(
            (
                '<button class="raya-graph-chip" type="button" '
                f'style="--raya-graph-group-color: {html.escape(group_color, quote=True)}" '
                f'data-raya-graph-group-filter="{html.escape(str(group["id"]), quote=True)}" '
                'aria-pressed="true">'
                '<span class="raya-graph-group-swatch" aria-hidden="true"></span>'
                f"{html.escape(str(group['title']))}"
                "</button>"
            )
        )
    return buttons


def _browser_graph_payload(
    content_model: ContentModel,
    graph_index: dict[str, Any],
    official_counts: dict[str, dict[str, int]],
    official_by_page: dict[str, list[dict[str, Any]]] | None = None,
    search_records: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    official_by_page = official_by_page or {}
    search_records = search_records or {}
    nodes: list[dict[str, Any]] = []
    for node in graph_index["nodes"]:
        page = content_model.pages_by_id.get(str(node["id"]))
        if page is None:
            continue
        page_objects = official_by_page.get(page.id, [])
        public_task_objects = [
            item for item in page_objects if _official_public_task_summary(item) is not None
        ]
        dated_task_objects = [
            item for item in public_task_objects if _official_task_event_date(item)
        ]
        discovery_payload = _public_discovery_page_payload(
            page,
            content_model=content_model,
            graph_index=graph_index,
            official_counts=official_counts,
            from_path=STATIC_GRAPH_PATH.as_posix(),
            search_from_path=STATIC_GRAPH_PATH.as_posix(),
            graph_from_path=STATIC_GRAPH_PATH.as_posix(),
            practice_from_path=STATIC_GRAPH_PATH.as_posix(),
        )
        nodes.append(
            {
                **node,
                **discovery_payload,
                "key_objects": _browser_graph_key_objects(
                    search_records.get(page.id, {}),
                    page_url=str(discovery_payload.get("url", "")),
                ),
                "sections": _browser_graph_sections(
                    search_records.get(page.id, {}),
                    page_url=str(discovery_payload.get("url", "")),
                ),
                "study_objects": _browser_graph_study_objects(page, page_objects),
                "tasks_url": (
                    _href_with_query(
                        _relative_href(
                            STATIC_GRAPH_PATH.as_posix(), STATIC_TASKS_PATH.as_posix()
                        ),
                        {"page": page.id},
                    )
                    if public_task_objects
                    else ""
                ),
                "schedule_url": (
                    _href_with_query(
                        _relative_href(
                            STATIC_GRAPH_PATH.as_posix(), STATIC_SCHEDULE_PATH.as_posix()
                        ),
                        {"page": page.id},
                    )
                    if dated_task_objects
                    else ""
                ),
            }
        )
    return {
        **graph_index,
        "nodes": nodes,
        "backlinks": {
            page_id: [
                {
                    **backlink,
                    "url": _relative_href(
                        STATIC_GRAPH_PATH.as_posix(), backlink["url"]
                    ),
                }
                for backlink in backlinks
            ]
            for page_id, backlinks in graph_index["backlinks"].items()
        },
    }


def _browser_graph_key_objects(
    public_record: dict[str, Any],
    *,
    page_url: str,
) -> list[dict[str, str]]:
    key_objects: list[dict[str, str]] = []
    for section in public_record.get("sections", []):
        kind = _sanitize_public_search_text(str(section.get("kind", "")))
        if kind not in {"numbered-object", "proof"}:
            continue
        anchor = _sanitize_public_search_text(str(section.get("anchor", "")))
        title = _sanitize_public_search_text(str(section.get("title", "")))
        reference = _sanitize_public_search_text(str(section.get("reference", "")))
        section_id = _sanitize_public_search_text(str(section.get("id", "")))
        if not (anchor and title and section_id):
            continue
        label = title
        if reference and title != reference:
            label = f"{reference} {title}"
        key_objects.append(
            {
                "id": section_id,
                "anchor": anchor,
                "kind": kind,
                "reference": reference,
                "title": label,
                "url": f"{page_url}#{quote(anchor)}",
            }
        )
    return key_objects


def _browser_graph_sections(
    public_record: dict[str, Any],
    *,
    page_url: str,
    limit: int = 16,
) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    for section in public_record.get("sections", []):
        anchor = str(section.get("anchor", "")).strip()
        title = _sanitize_public_search_text(str(section.get("title", "")))
        section_id = str(section.get("id", "")).strip()
        kind = _sanitize_public_search_text(str(section.get("kind", "")))
        if not (anchor and title and section_id):
            continue
        if not (
            _is_public_graph_section_fragment(anchor)
            and _is_public_graph_section_fragment(section_id, allow_colon=True)
        ):
            continue
        if kind not in {"heading", "numbered-object", "proof"}:
            kind = ""
        sections.append(
            {
                "id": section_id,
                "anchor": anchor,
                "kind": kind,
                "title": title,
                "url": f"{page_url}#{quote(anchor)}",
            }
        )
        if len(sections) >= limit:
            break
    return sections


def _is_public_graph_section_fragment(value: str, *, allow_colon: bool = False) -> bool:
    allowed = r"A-Za-z0-9_.:-" if allow_colon else r"A-Za-z0-9_.-"
    if not re.fullmatch(rf"[{allowed}]+", value):
        return False
    lowered = value.lower()
    if ".." in value or lowered.startswith("_"):
        return False
    private_tokens = (
        "_assets",
        "_official",
        "_reviewed",
        "_drafts",
        "_partials",
        "artifact",
        "cache_key",
        "source_path",
    )
    return not any(token in lowered for token in private_tokens)


def _write_search_surface(
    *,
    site_dir: Path,
    content_model: ContentModel,
    course_title: str,
    language: str,
    graph_index: dict[str, Any],
    official_counts: dict[str, dict[str, int]],
    official_by_page: dict[str, list[dict[str, Any]]],
    search_records: dict[str, dict[str, Any]],
    skin_context: SkinContext,
    report: ValidationReport,
) -> None:
    search_path = site_dir / STATIC_SEARCH_PATH
    search_path.parent.mkdir(parents=True, exist_ok=True)
    report.wrote_output(search_path.parent)
    search_path.write_text(
        _render_search_surface(
            content_model=content_model,
            course_title=course_title,
            language=language,
            graph_index=graph_index,
            official_counts=official_counts,
            official_by_page=official_by_page,
            search_records=search_records,
            skin_context=skin_context,
        ),
        encoding="utf-8",
    )
    report.wrote_output(search_path)


def _render_search_surface(
    *,
    content_model: ContentModel,
    course_title: str,
    language: str,
    graph_index: dict[str, Any],
    official_counts: dict[str, dict[str, int]],
    official_by_page: dict[str, list[dict[str, Any]]],
    search_records: dict[str, dict[str, Any]],
    skin_context: SkinContext,
) -> str:
    stylesheet_href = _relative_href(
        STATIC_SEARCH_PATH.as_posix(), RENDER_STYLESHEET_PATH
    )
    skin_stylesheet_href = _relative_href(
        STATIC_SEARCH_PATH.as_posix(),
        SKIN_STYLESHEET_PATH,
    )
    accessibility_css_href = _relative_href(
        STATIC_SEARCH_PATH.as_posix(),
        f"{ACCESSIBILITY_RESOURCE_PATH}/{OPEN_DYSLEXIC_CSS_NAME}",
    )
    accessibility_js_href = _relative_href(
        STATIC_SEARCH_PATH.as_posix(),
        f"{ACCESSIBILITY_RESOURCE_PATH}/{OPEN_DYSLEXIC_VOLATILE_JS_NAME}",
    )
    discovery_js_href = _relative_href(
        STATIC_SEARCH_PATH.as_posix(),
        Path(DISCOVERY_RESOURCE_PATH) / DISCOVERY_SCRIPT_NAME,
    )
    search_js_href = _relative_href(
        STATIC_SEARCH_PATH.as_posix(),
        Path(SEARCH_RESOURCE_PATH) / SEARCH_SCRIPT_NAME,
    )
    root_skin = skin_id_for_source_path(
        content_model.pages[0].source_path, skin_context
    )
    browser_search = _browser_search_payload(
        content_model,
        graph_index,
        official_counts,
        official_by_page,
        search_records,
    )
    search_section_count = sum(
        len(page.get("sections", [])) for page in browser_search["pages"]
    )
    search_payload = _json_script_text(browser_search)
    result_items = []
    for page in browser_search["pages"]:
        tags = ", ".join(page["tags"])
        meta_parts = [
            f"Stable ID {page['stable_id']}",
            page["status"],
            page["hierarchy_label"],
            tags,
        ]
        meta = " | ".join(part for part in meta_parts if part)
        link_counts = page["link_counts"]
        counts_text = (
            f"Explicit links: {link_counts['outgoing']} outgoing, "
            f"{link_counts['incoming']} incoming, "
            f"{link_counts['connected']} connected"
        )
        study_counts_text = _study_counts_text(page["study_counts"])
        study_counts_html = (
            '<p class="raya-search-result-counts">'
            f"Official objects: {html.escape(study_counts_text)}"
            "</p>"
            if study_counts_text
            else ""
        )
        practice_action = (
            f'<a class="raya-search-result-practice" href="{html.escape(page["practice_url"])}">'
            "Open practice</a>"
            if page["practice_url"]
            else ""
        )
        tasks_action = (
            f'<a class="raya-search-result-tasks" href="{html.escape(page["tasks_url"])}">'
            "Open tasks</a>"
            if page["tasks_url"]
            else ""
        )
        schedule_action = (
            f'<a class="raya-search-result-schedule" href="{html.escape(page["schedule_url"])}">'
            "Open schedule</a>"
            if page["schedule_url"]
            else ""
        )
        section_items = []
        for section in page["sections"]:
            section_items.append(
                '<li class="raya-search-result-section" '
                f'data-raya-search-section="{html.escape(section["id"], quote=True)}">'
                f'<a href="{html.escape(section["url"])}">'
                f'{html.escape(section["title"])}</a>'
                f'<span>{html.escape(section["search_snippet"])}</span>'
                "</li>"
            )
        sections_html = (
            '<section class="raya-search-result-sections" '
            'aria-label="Section matches">'
            "<h3>Section matches</h3>"
            '<ol class="raya-search-result-section-list">'
            f'{"".join(section_items)}'
            "</ol>"
            "</section>"
            if section_items
            else ""
        )
        result_items.append(
            f'<li data-raya-search-result="{html.escape(page["id"], quote=True)}" '
            'data-raya-search-active="false">'
            f'<a class="raya-search-result-page" href="{html.escape(page["url"])}">'
            f"{html.escape(page['title'])}</a>"
            f"<p>{html.escape(page['summary'])}</p>"
            f'<p class="raya-search-result-meta">{html.escape(meta)}</p>'
            f'<p class="raya-search-result-counts">{html.escape(counts_text)}</p>'
            f"{study_counts_html}"
            f"{sections_html}"
            '<p class="raya-search-result-actions">'
            f'<a class="raya-search-result-open" href="{html.escape(page["url"])}">'
            "Open page</a>"
            f'<a class="raya-search-result-graph" href="{html.escape(page["graph_url"])}" '
            f'aria-label="View {html.escape(page["title"], quote=True)} in course graph">'
            "View in graph</a>"
            f"{practice_action}"
            f"{tasks_action}"
            f"{schedule_action}"
            "</p>"
            "</li>"
        )
    return "\n".join(
        [
            "<!doctype html>",
            f'<html lang="{html.escape(language)}">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>Course Search - {html.escape(course_title)}</title>",
            f'<link rel="stylesheet" href="{html.escape(stylesheet_href)}">',
            f'<link rel="stylesheet" href="{html.escape(skin_stylesheet_href)}">',
            f'<link rel="stylesheet" href="{html.escape(accessibility_css_href)}">',
            "</head>",
            (
                f'<body data-raya-surface="search" '
                f'data-raya-skin="{html.escape(root_skin, quote=True)}">'
            ),
            '<a class="raya-skip-link" href="#raya-search-main">Skip to search</a>',
            _render_discovery_command_bar(
                course_title=course_title,
                workspace_label="Search workspace",
                current_workspace="search",
                home_href="../../index.html",
                search_href="index.html",
                graph_href="../graph/index.html",
                practice_href="../practice/index.html",
                tasks_href="../tasks/index.html",
                schedule_href="../schedule/index.html",
            ),
            (
                '<main id="raya-search-main" class="raya-search-page" '
                'data-raya-search-page data-raya-discovery-page '
                'data-raya-discovery-rail-state="expanded" '
                'data-raya-discovery-controls-state="expanded" '
                'data-raya-discovery-context-state="expanded" tabindex="-1">'
            ),
            '<header class="raya-search-header raya-discovery-header">',
            "<h1>Course Search</h1>",
            "<p>Search public page metadata and public article text.</p>",
            "</header>",
            '<section class="raya-discovery-workspace-shell" aria-label="Course discovery workspace">',
            _render_discovery_course_rail(
                content_model=content_model,
                course_title=course_title,
                current_workspace="search",
                from_path=STATIC_SEARCH_PATH.as_posix(),
                graph_index=graph_index,
                official_by_page=official_by_page,
            ),
            '<section class="raya-search-workspace" aria-label="Search workspace">',
            '<aside class="raya-search-control-panel" aria-label="Search controls panel">',
            '<div class="raya-discovery-panel-header">',
            "<h2>Find pages</h2>",
            (
                '<p class="raya-discovery-panel-rail-summary" '
                'data-raya-discovery-panel-rail-summary="controls" '
                'aria-hidden="true"></p>'
            ),
            (
                '<button type="button" data-raya-discovery-toggle-panel="controls" '
                'aria-controls="raya-search-control-panel-body" aria-expanded="true" '
                'aria-label="Collapse controls panel">'
                "Collapse controls</button>"
            ),
            "</div>",
            (
                '<div id="raya-search-control-panel-body" class="raya-discovery-panel-body" '
                'data-raya-discovery-panel-body="controls" aria-hidden="false">'
            ),
            '<section class="raya-search-controls" aria-label="Course search controls">',
            '<fieldset class="raya-discovery-control-group">',
            "<legend>Query</legend>",
            '<label for="raya-search-input">Search</label>',
            '<input id="raya-search-input" type="search" autocomplete="off">',
            "</fieldset>",
            '<fieldset class="raya-discovery-control-group">',
            "<legend>Reset</legend>",
            '<button id="raya-search-clear" type="button">Clear</button>',
            "</fieldset>",
            "</section>",
            '<div class="raya-discovery-control-state" aria-label="Search workspace state">',
            '<p id="raya-search-status" class="raya-search-status" aria-live="polite"></p>',
            (
                '<p class="raya-discovery-summary" '
                f"data-raya-search-summary-count>{len(browser_search['pages'])} visible result(s).</p>"
            ),
            (
                '<p class="raya-discovery-page-focus" '
                'data-raya-search-page-focus hidden aria-live="polite"></p>'
            ),
            "</div>",
            (
                '<p class="raya-discovery-results-jump">'
                '<a href="#raya-search-results-panel">Results</a></p>'
            ),
            "</div>",
            "</aside>",
            (
                '<section id="raya-search-results-panel" '
                'class="raya-search-results-panel" '
                'aria-label="Search results" tabindex="-1">'
            ),
            '<p id="raya-search-empty" class="raya-search-empty" hidden>No matching pages.</p>',
            '<ol id="raya-search-results" class="raya-search-results">',
            "\n".join(result_items),
            "</ol>",
            "</section>",
            (
                '<aside class="raya-search-context-panel" data-raya-search-context '
                'aria-label="Search context panel">'
            ),
            '<div class="raya-discovery-panel-header">',
            "<h2>Context</h2>",
            (
                '<p class="raya-discovery-panel-rail-summary" '
                'data-raya-discovery-panel-rail-summary="context" '
                'aria-hidden="true"></p>'
            ),
            (
                '<button type="button" data-raya-discovery-toggle-panel="context" '
                'aria-controls="raya-search-context-panel-body" aria-expanded="true" '
                'aria-label="Collapse context panel">'
                "Collapse context</button>"
            ),
            "</div>",
            (
                '<div id="raya-search-context-panel-body" class="raya-discovery-panel-body" '
                'data-raya-discovery-panel-body="context" aria-hidden="false" '
                'aria-live="polite">'
            ),
            "<p data-raya-search-context-title>Select or filter a page.</p>",
            (
                '<p class="raya-discovery-context-meta" '
                "data-raya-search-context-meta>Public page metadata only.</p>"
            ),
            (
                '<p class="raya-discovery-context-actions" '
                "data-raya-search-context-actions hidden></p>"
            ),
            "</div>",
            "</aside>",
            "</section>",
            "</section>",
            _render_discovery_overview(
                kind="search",
                title="Search workspace",
                summary=(
                    "Use local search to scan public pages, section anchors, "
                    "and generated handoffs without leaving the static site."
                ),
                meta=[
                    ("Public pages", f"{len(browser_search['pages'])}"),
                    ("Section anchors", f"{search_section_count}"),
                    ("Source scope", "Public page metadata and article text"),
                    ("Reset path", "Clear or Escape"),
                ],
                actions=[
                    ("View graph", "../graph/index.html"),
                    ("Open practice", "../practice/index.html"),
                    ("Open tasks", "../tasks/index.html"),
                    ("Open schedule", "../schedule/index.html"),
                ],
            ),
            _render_discovery_quick_guide(
                kind="search",
                cards=[
                    ("Find", "Type public page, section, tag, or stable-ID text."),
                    (
                        "Inspect",
                        "Pointer, focus, or keyboard movement updates the context panel.",
                    ),
                    (
                        "Open",
                        "Use result links to open the page, graph, or matching workspaces.",
                    ),
                    ("Reset", "Clear or Escape returns to all visible public pages."),
                ],
            ),
            '<script type="application/json" id="raya-search-data">',
            search_payload,
            "</script>",
            "</main>",
            f'<script src="{html.escape(accessibility_js_href)}" defer></script>',
            f'<script src="{html.escape(discovery_js_href)}" defer></script>',
            f'<script src="{html.escape(search_js_href)}" defer></script>',
            "</body>",
            "</html>",
            "",
        ]
    )


def _browser_search_payload(
    content_model: ContentModel,
    graph_index: dict[str, Any],
    official_counts: dict[str, dict[str, int]],
    official_by_page: dict[str, list[dict[str, Any]]],
    search_records: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    pages = []
    for page in content_model.pages:
        payload = _public_discovery_page_payload(
            page,
            content_model=content_model,
            graph_index=graph_index,
            official_counts=official_counts,
            from_path=STATIC_SEARCH_PATH.as_posix(),
            search_from_path=STATIC_SEARCH_PATH.as_posix(),
            graph_from_path=STATIC_SEARCH_PATH.as_posix(),
            practice_from_path=STATIC_SEARCH_PATH.as_posix(),
            tasks_from_path=STATIC_SEARCH_PATH.as_posix(),
            schedule_from_path=STATIC_SEARCH_PATH.as_posix(),
            official_by_page=official_by_page,
        )
        for text_key in ("title", "nav_title", "summary", "status", "hierarchy_label"):
            payload[text_key] = _sanitize_public_search_text(str(payload.get(text_key, "")))
        payload["tags"] = [
            _sanitize_public_search_text(str(tag))
            for tag in payload.get("tags", [])
        ]
        public_record = search_records.get(page.id, {})
        public_sections = []
        page_url = str(payload.get("url", ""))
        for section in public_record.get("sections", []):
            anchor = _sanitize_public_search_text(str(section.get("anchor", "")))
            title = _sanitize_public_search_text(str(section.get("title", "")))
            search_text = _sanitize_public_search_text(
                str(section.get("search_text", ""))
            )
            search_snippet = _sanitize_public_search_text(
                str(section.get("search_snippet", ""))
            )
            section_id = _sanitize_public_search_text(str(section.get("id", "")))
            if not (anchor and title and search_text and section_id):
                continue
            public_sections.append(
                {
                    "id": section_id,
                    "anchor": anchor,
                    "title": title,
                    "url": f"{page_url}#{quote(anchor)}",
                    "search_text": search_text,
                    "search_snippet": search_snippet or _public_search_snippet(search_text),
                }
            )
        payload["search_text"] = _compact_public_text(
            " ".join(
                [
                    str(payload.get("id", "")),
                    str(payload.get("stable_id", "")),
                    str(payload.get("title", "")),
                    str(payload.get("nav_title", "")),
                    str(payload.get("summary", "")),
                    str(payload.get("status", "")),
                    str(payload.get("hierarchy_label", "")),
                    " ".join(str(tag) for tag in payload.get("tags", [])),
                    str(public_record.get("search_text", "")),
                    " ".join(section["search_text"] for section in public_sections),
                ]
            )
        )
        payload["search_snippet"] = str(public_record.get("search_snippet", ""))
        payload["sections"] = public_sections
        pages.append(payload)
    return {
        "version": 1,
        "pages": pages,
    }


def _search_index(
    content_model: ContentModel,
    search_records: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "version": 1,
        "pages": [
            {
                "id": page.id,
                "search_text": str(
                    search_records.get(page.id, {}).get("search_text", "")
                ),
                "search_snippet": str(
                    search_records.get(page.id, {}).get("search_snippet", "")
                ),
                "sections": [
                    {
                        "id": str(section.get("id", "")),
                        "anchor": str(section.get("anchor", "")),
                        "title": str(section.get("title", "")),
                        "search_text": str(section.get("search_text", "")),
                        "search_snippet": str(section.get("search_snippet", "")),
                    }
                    for section in search_records.get(page.id, {}).get("sections", [])
                ],
            }
            for page in content_model.pages
        ],
    }


def _write_practice_surface(
    *,
    site_dir: Path,
    content_model: ContentModel,
    official_by_page: dict[str, list[dict[str, Any]]],
    course_title: str,
    language: str,
    skin_context: SkinContext,
    report: ValidationReport,
) -> None:
    practice_path = site_dir / STATIC_PRACTICE_PATH
    practice_path.parent.mkdir(parents=True, exist_ok=True)
    report.wrote_output(practice_path.parent)
    practice_path.write_text(
        _render_practice_surface(
            content_model=content_model,
            official_by_page=official_by_page,
            course_title=course_title,
            language=language,
            skin_context=skin_context,
        ),
        encoding="utf-8",
    )
    report.wrote_output(practice_path)


def _render_practice_surface(
    *,
    content_model: ContentModel,
    official_by_page: dict[str, list[dict[str, Any]]],
    course_title: str,
    language: str,
    skin_context: SkinContext,
) -> str:
    stylesheet_href = _relative_href(
        STATIC_PRACTICE_PATH.as_posix(), RENDER_STYLESHEET_PATH
    )
    skin_stylesheet_href = _relative_href(
        STATIC_PRACTICE_PATH.as_posix(),
        SKIN_STYLESHEET_PATH,
    )
    accessibility_css_href = _relative_href(
        STATIC_PRACTICE_PATH.as_posix(),
        f"{ACCESSIBILITY_RESOURCE_PATH}/{OPEN_DYSLEXIC_CSS_NAME}",
    )
    accessibility_js_href = _relative_href(
        STATIC_PRACTICE_PATH.as_posix(),
        f"{ACCESSIBILITY_RESOURCE_PATH}/{OPEN_DYSLEXIC_VOLATILE_JS_NAME}",
    )
    discovery_js_href = _relative_href(
        STATIC_PRACTICE_PATH.as_posix(),
        Path(DISCOVERY_RESOURCE_PATH) / DISCOVERY_SCRIPT_NAME,
    )
    practice_js_href = _relative_href(
        STATIC_PRACTICE_PATH.as_posix(),
        Path(PRACTICE_RESOURCE_PATH) / PRACTICE_SCRIPT_NAME,
    )
    root_skin = skin_id_for_source_path(
        content_model.pages[0].source_path, skin_context
    )
    browser_practice = _browser_practice_payload(content_model, official_by_page)
    practice_payload = _json_script_text(browser_practice)
    type_buttons = [
        (
            '<button class="raya-practice-chip" type="button" '
            'data-raya-practice-filter="all" aria-pressed="true">'
            f"All ({len(browser_practice['objects'])})"
            "</button>"
        )
    ]
    for type_info in browser_practice["types"]:
        type_buttons.append(
            (
                '<button class="raya-practice-chip" type="button" '
                f'data-raya-practice-filter="{html.escape(type_info["type"], quote=True)}" '
                'aria-pressed="false">'
                f"{html.escape(type_info['label'])} ({type_info['count']})"
                "</button>"
            )
        )

    objects_by_page: dict[str, list[dict[str, str]]] = defaultdict(list)
    for item in browser_practice["objects"]:
        objects_by_page[str(item["page_id"])].append(item)

    group_sections: list[str] = []
    for page in content_model.pages:
        page_objects = objects_by_page.get(page.id, [])
        if not page_objects:
            continue
        cards = []
        for item in page_objects:
            cards.append(
                "\n".join(
                    [
                        (
                            '<article class="raya-practice-object" '
                            f'data-raya-practice-object="{html.escape(item["id"], quote=True)}" '
                            f'data-raya-practice-type="{html.escape(item["type"], quote=True)}" '
                            f'data-raya-practice-page="{html.escape(item["page_id"], quote=True)}" '
                            'data-raya-practice-active="false">'
                        ),
                        '<header class="raya-practice-object-header">',
                        (
                            '<span class="raya-practice-kind">'
                            f"{html.escape(item['type_label'])}</span>"
                        ),
                        (
                            '<span class="raya-practice-authority">'
                            f"{html.escape(item['authority'])}</span>"
                        ),
                        "</header>",
                        f"<h3>{html.escape(item['preview'])}</h3>",
                        (
                            '<p class="raya-practice-meta">'
                            f"From {html.escape(item['page_title'])} | "
                            f"ID {html.escape(item['id'])}"
                            "</p>"
                        ),
                        '<p class="raya-practice-actions">',
                        (
                            '<a class="raya-practice-open" '
                            f'href="{html.escape(item["page_url"])}">Open page</a>'
                        ),
                        (
                            '<a class="raya-practice-graph" '
                            f'href="{html.escape(item["graph_url"])}" '
                            f'aria-label="View {html.escape(item["page_title"], quote=True)} in course graph">'
                            "View in graph</a>"
                        ),
                        "</p>",
                        "</article>",
                    ]
                )
            )
        group_sections.append(
            "\n".join(
                [
                    (
                        '<section class="raya-practice-group" '
                        f'data-raya-practice-group="{html.escape(page.id, quote=True)}">'
                    ),
                    f"<h2>{html.escape(page.title)}</h2>",
                    '<div class="raya-practice-grid">',
                    "\n".join(cards),
                    "</div>",
                    "</section>",
                ]
            )
        )

    return "\n".join(
        [
            "<!doctype html>",
            f'<html lang="{html.escape(language)}">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>Official Practice - {html.escape(course_title)}</title>",
            f'<link rel="stylesheet" href="{html.escape(stylesheet_href)}">',
            f'<link rel="stylesheet" href="{html.escape(skin_stylesheet_href)}">',
            f'<link rel="stylesheet" href="{html.escape(accessibility_css_href)}">',
            "</head>",
            (
                f'<body data-raya-surface="practice" '
                f'data-raya-skin="{html.escape(root_skin, quote=True)}">'
            ),
            '<a class="raya-skip-link" href="#raya-practice-main">Skip to practice</a>',
            _render_discovery_command_bar(
                course_title=course_title,
                workspace_label="Official practice workspace",
                current_workspace="practice",
                home_href="../../index.html",
                search_href="../search/index.html",
                graph_href="../graph/index.html",
                practice_href="index.html",
                tasks_href="../tasks/index.html",
                schedule_href="../schedule/index.html",
            ),
            (
                '<main id="raya-practice-main" class="raya-practice-page" '
                'data-raya-practice-page data-raya-discovery-page '
                'data-raya-discovery-rail-state="expanded" '
                'data-raya-discovery-controls-state="expanded" '
                'data-raya-discovery-context-state="expanded" tabindex="-1">'
            ),
            '<header class="raya-practice-header raya-discovery-header">',
            "<h1>Official Practice</h1>",
            (
                "<p>Find accepted course practice objects by page and type. "
                "Open the owning page when you are ready to work with the full context.</p>"
            ),
            "</header>",
            '<section class="raya-discovery-workspace-shell" aria-label="Course discovery workspace">',
            _render_discovery_course_rail(
                content_model=content_model,
                course_title=course_title,
                current_workspace="practice",
                from_path=STATIC_PRACTICE_PATH.as_posix(),
                official_by_page=official_by_page,
            ),
            '<section class="raya-practice-workspace" aria-label="Official practice workspace">',
            '<aside class="raya-practice-control-panel" aria-label="Practice controls panel">',
            '<div class="raya-discovery-panel-header">',
            "<h2>Find practice</h2>",
            (
                '<p class="raya-discovery-panel-rail-summary" '
                'data-raya-discovery-panel-rail-summary="controls" '
                'aria-hidden="true"></p>'
            ),
            (
                '<button type="button" data-raya-discovery-toggle-panel="controls" '
                'aria-controls="raya-practice-control-panel-body" aria-expanded="true" '
                'aria-label="Collapse controls panel">'
                "Collapse controls</button>"
            ),
            "</div>",
            (
                '<div id="raya-practice-control-panel-body" class="raya-discovery-panel-body" '
                'data-raya-discovery-panel-body="controls" aria-hidden="false">'
            ),
            '<section class="raya-practice-controls" aria-label="Official practice controls">',
            '<fieldset class="raya-discovery-control-group">',
            "<legend>Query</legend>",
            '<label for="raya-practice-search">Search</label>',
            '<input id="raya-practice-search" type="search" autocomplete="off">',
            "</fieldset>",
            '<fieldset class="raya-discovery-control-group">',
            "<legend>Object type</legend>",
            '<div class="raya-practice-filters" aria-label="Practice type filters">',
            "\n".join(type_buttons),
            "</div>",
            "</fieldset>",
            '<fieldset class="raya-discovery-control-group">',
            "<legend>Reset</legend>",
            '<button id="raya-practice-clear" type="button">Clear</button>',
            "</fieldset>",
            "</section>",
            '<div class="raya-discovery-control-state" aria-label="Practice workspace state">',
            '<p id="raya-practice-status" class="raya-practice-status" aria-live="polite"></p>',
            (
                '<p class="raya-discovery-summary" '
                f"data-raya-practice-summary-count>{len(browser_practice['objects'])} visible practice object(s).</p>"
            ),
            (
                '<p class="raya-discovery-page-focus" '
                'data-raya-practice-page-focus hidden aria-live="polite"></p>'
            ),
            "</div>",
            (
                '<p class="raya-discovery-results-jump">'
                '<a href="#raya-practice-results-panel">Results</a></p>'
            ),
            "</div>",
            "</aside>",
            (
                '<section id="raya-practice-results-panel" '
                'class="raya-practice-results-panel" '
                'aria-label="Official practice results" tabindex="-1">'
            ),
            (
                '<p id="raya-practice-empty" class="raya-practice-empty" hidden>'
                "No matching official practice objects.</p>"
            ),
            '<section class="raya-practice-results" aria-label="Official practice results">',
            "\n".join(group_sections),
            "</section>",
            "</section>",
            (
                '<aside class="raya-practice-context-panel" data-raya-practice-context '
                'aria-label="Practice context panel">'
            ),
            '<div class="raya-discovery-panel-header">',
            "<h2>Context</h2>",
            (
                '<p class="raya-discovery-panel-rail-summary" '
                'data-raya-discovery-panel-rail-summary="context" '
                'aria-hidden="true"></p>'
            ),
            (
                '<button type="button" data-raya-discovery-toggle-panel="context" '
                'aria-controls="raya-practice-context-panel-body" aria-expanded="true" '
                'aria-label="Collapse context panel">'
                "Collapse context</button>"
            ),
            "</div>",
            (
                '<div id="raya-practice-context-panel-body" class="raya-discovery-panel-body" '
                'data-raya-discovery-panel-body="context" aria-hidden="false" '
                'aria-live="polite">'
            ),
            "<p data-raya-practice-context-title>Select or filter an official object.</p>",
            (
                '<p class="raya-discovery-context-meta" '
                "data-raya-practice-context-meta>Accepted public object metadata only.</p>"
            ),
            (
                '<p class="raya-discovery-context-actions" '
                "data-raya-practice-context-actions hidden></p>"
            ),
            "</div>",
            "</aside>",
            "</section>",
            "</section>",
            _render_discovery_overview(
                kind="practice",
                title="Official practice workspace",
                summary=(
                    "Use local filters to inspect accepted official objects "
                    "and return to their owning course pages."
                ),
                meta=[
                    ("Official objects", f"{len(browser_practice['objects'])}"),
                    ("Object types", f"{len(browser_practice['types'])}"),
                    ("Source scope", "Accepted official objects"),
                    ("Reset path", "Clear or Escape"),
                ],
                actions=[
                    ("Open search", "../search/index.html"),
                    ("View graph", "../graph/index.html"),
                    ("Open tasks", "../tasks/index.html"),
                    ("Open schedule", "../schedule/index.html"),
                ],
            ),
            _render_discovery_quick_guide(
                kind="practice",
                cards=[
                    ("Find", "Search accepted official objects and filter by type."),
                    ("Inspect", "Select visible objects to read public metadata."),
                    ("Open", "Return to the owning page or graph focus."),
                    ("Reset", "Clear or Escape shows accepted objects again."),
                ],
            ),
            '<script type="application/json" id="raya-practice-data">',
            practice_payload,
            "</script>",
            "</main>",
            f'<script src="{html.escape(accessibility_js_href)}" defer></script>',
            f'<script src="{html.escape(discovery_js_href)}" defer></script>',
            f'<script src="{html.escape(practice_js_href)}" defer></script>',
            "</body>",
            "</html>",
            "",
        ]
    )


def _browser_practice_payload(
    content_model: ContentModel,
    official_by_page: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    objects: list[dict[str, str]] = []
    type_counts: dict[str, int] = defaultdict(int)
    for page in content_model.pages:
        page_objects = sorted(
            official_by_page.get(page.id, []),
            key=lambda item: (
                item.get("source_order")
                if isinstance(item.get("source_order"), int)
                else 0,
                str(item.get("id") or ""),
            ),
        )
        for item in page_objects:
            if not isinstance(item, dict):
                continue
            object_id = str(item.get("id") or "").strip()
            object_type = str(item.get("type") or "practice").strip() or "practice"
            authority = str(item.get("authority") or "official").strip() or "official"
            preview = _official_preview_text(item)
            if not object_id or not preview:
                continue
            anchor = f"raya-official-{_safe_map_fragment_id(object_id)}"
            page_url = (
                _relative_href(STATIC_PRACTICE_PATH.as_posix(), page.output_path)
                + f"#{anchor}"
            )
            graph_url = _href_with_query(
                _relative_href(
                    STATIC_PRACTICE_PATH.as_posix(),
                    STATIC_GRAPH_PATH.as_posix(),
                ),
                {"page": page.id},
            )
            type_counts[object_type] += 1
            objects.append(
                {
                    "anchor": anchor,
                    "authority": authority,
                    "graph_url": graph_url,
                    "id": object_id,
                    "page_id": page.id,
                    "page_title": page.title,
                    "page_url": page_url,
                    "preview": preview,
                    "type": object_type,
                    "type_label": _official_type_label(object_type),
                }
            )
    types = [
        {
            "count": count,
            "label": _official_type_label(object_type),
            "type": object_type,
        }
        for object_type, count in sorted(
            type_counts.items(),
            key=lambda pair: (_official_type_label(pair[0]), pair[0]),
        )
    ]
    return {
        "objects": objects,
        "types": types,
        "version": 1,
    }


_OFFICIAL_TASK_TYPES = frozenset({"assignment", "exam", "project", "task"})


def _write_tasks_surface(
    *,
    site_dir: Path,
    content_model: ContentModel,
    official_by_page: dict[str, list[dict[str, Any]]],
    course_title: str,
    language: str,
    skin_context: SkinContext,
    report: ValidationReport,
) -> None:
    tasks_path = site_dir / STATIC_TASKS_PATH
    tasks_path.parent.mkdir(parents=True, exist_ok=True)
    report.wrote_output(tasks_path.parent)
    tasks_path.write_text(
        _render_tasks_surface(
            content_model=content_model,
            official_by_page=official_by_page,
            course_title=course_title,
            language=language,
            skin_context=skin_context,
        ),
        encoding="utf-8",
    )
    report.wrote_output(tasks_path)


def _render_tasks_surface(
    *,
    content_model: ContentModel,
    official_by_page: dict[str, list[dict[str, Any]]],
    course_title: str,
    language: str,
    skin_context: SkinContext,
) -> str:
    stylesheet_href = _relative_href(STATIC_TASKS_PATH.as_posix(), RENDER_STYLESHEET_PATH)
    skin_stylesheet_href = _relative_href(
        STATIC_TASKS_PATH.as_posix(),
        SKIN_STYLESHEET_PATH,
    )
    accessibility_css_href = _relative_href(
        STATIC_TASKS_PATH.as_posix(),
        f"{ACCESSIBILITY_RESOURCE_PATH}/{OPEN_DYSLEXIC_CSS_NAME}",
    )
    accessibility_js_href = _relative_href(
        STATIC_TASKS_PATH.as_posix(),
        f"{ACCESSIBILITY_RESOURCE_PATH}/{OPEN_DYSLEXIC_VOLATILE_JS_NAME}",
    )
    discovery_js_href = _relative_href(
        STATIC_TASKS_PATH.as_posix(),
        Path(DISCOVERY_RESOURCE_PATH) / DISCOVERY_SCRIPT_NAME,
    )
    tasks_js_href = _relative_href(
        STATIC_TASKS_PATH.as_posix(),
        Path(TASKS_RESOURCE_PATH) / TASKS_SCRIPT_NAME,
    )
    root_skin = skin_id_for_source_path(
        content_model.pages[0].source_path, skin_context
    )
    browser_tasks = _browser_tasks_payload(content_model, official_by_page)
    tasks_payload = _json_script_text(browser_tasks)
    type_buttons = [
        (
            '<button class="raya-task-chip" type="button" '
            'data-raya-task-filter="all" aria-pressed="true">'
            f"All ({len(browser_tasks['objects'])})"
            "</button>"
        )
    ]
    for type_info in browser_tasks["types"]:
        type_buttons.append(
            (
                '<button class="raya-task-chip" type="button" '
                f'data-raya-task-filter="{html.escape(type_info["type"], quote=True)}" '
                'aria-pressed="false">'
                f"{html.escape(type_info['label'])} ({type_info['count']})"
                "</button>"
            )
        )

    cards = []
    for order, item in enumerate(browser_tasks["objects"]):
        meta_bits = [
            f"From {item['page_title']}",
            f"ID {item['id']}",
            f"Due {item['due']}" if item["due"] else "",
            f"Available {item['available']}" if item["available"] else "",
            item["points"],
            f"Weight {item['weight']}" if item["weight"] else "",
            f"Status {item['status']}" if item["status"] else "",
        ]
        tags_html = "".join(
            f'<span class="raya-task-tag">{html.escape(tag)}</span>'
            for tag in item["tags"]
        )
        cards.append(
            "\n".join(
                [
                    (
                        '<article class="raya-task-object" '
                        f'data-raya-task-object="{html.escape(item["id"], quote=True)}" '
                        f'data-raya-task-type="{html.escape(item["type"], quote=True)}" '
                        f'data-raya-task-page="{html.escape(item["page_id"], quote=True)}" '
                        f'data-raya-task-order="{order}" '
                        'data-raya-task-active="false">'
                    ),
                    '<header class="raya-task-object-header">',
                    (
                        '<span class="raya-task-kind">'
                        f"{html.escape(item['type_label'])}</span>"
                    ),
                    (
                        '<span class="raya-task-authority">'
                        f"{html.escape(item['authority'])}</span>"
                    ),
                    "</header>",
                    f"<h3>{html.escape(item['title'] or item['preview'])}</h3>",
                    (
                        '<p class="raya-task-preview">'
                        f"{html.escape(item['preview'])}</p>"
                        if item["preview"] and item["preview"] != item["title"]
                        else ""
                    ),
                    (
                        '<p class="raya-task-meta">'
                        f"{html.escape(' | '.join(bit for bit in meta_bits if bit))}"
                        "</p>"
                    ),
                    (
                        f'<p class="raya-task-tags">{tags_html}</p>'
                        if tags_html
                        else ""
                    ),
                    '<p class="raya-task-actions">',
                    (
                        '<a class="raya-task-open" '
                        f'href="{html.escape(item["page_url"])}">Open page</a>'
                    ),
                    (
                        '<a class="raya-task-graph" '
                        f'href="{html.escape(item["graph_url"])}" '
                        f'aria-label="View {html.escape(item["page_title"], quote=True)} in course graph">'
                        "View in graph</a>"
                    ),
                    "</p>",
                    "</article>",
                ]
            )
        )

    return "\n".join(
        [
            "<!doctype html>",
            f'<html lang="{html.escape(language)}">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>Official Tasks - {html.escape(course_title)}</title>",
            f'<link rel="stylesheet" href="{html.escape(stylesheet_href)}">',
            f'<link rel="stylesheet" href="{html.escape(skin_stylesheet_href)}">',
            f'<link rel="stylesheet" href="{html.escape(accessibility_css_href)}">',
            "</head>",
            (
                f'<body data-raya-surface="tasks" '
                f'data-raya-skin="{html.escape(root_skin, quote=True)}">'
            ),
            '<a class="raya-skip-link" href="#raya-tasks-main">Skip to tasks</a>',
            _render_discovery_command_bar(
                course_title=course_title,
                workspace_label="Official tasks workspace",
                current_workspace="tasks",
                home_href="../../index.html",
                search_href="../search/index.html",
                graph_href="../graph/index.html",
                practice_href="../practice/index.html",
                tasks_href="index.html",
                schedule_href="../schedule/index.html",
            ),
            (
                '<main id="raya-tasks-main" class="raya-tasks-page" '
                'data-raya-tasks-page data-raya-discovery-page '
                'data-raya-discovery-rail-state="expanded" '
                'data-raya-discovery-controls-state="expanded" '
                'data-raya-discovery-context-state="expanded" tabindex="-1">'
            ),
            '<header class="raya-tasks-header raya-discovery-header">',
            "<h1>Official Tasks</h1>",
            (
                "<p>Scan accepted assignments, projects, exams, and tasks. "
                "Open the owning page when you need the full course context.</p>"
            ),
            "</header>",
            '<section class="raya-discovery-workspace-shell" aria-label="Course discovery workspace">',
            _render_discovery_course_rail(
                content_model=content_model,
                course_title=course_title,
                current_workspace="tasks",
                from_path=STATIC_TASKS_PATH.as_posix(),
                official_by_page=official_by_page,
            ),
            '<section class="raya-tasks-workspace" aria-label="Official tasks workspace">',
            '<aside class="raya-tasks-control-panel" aria-label="Tasks controls panel">',
            '<div class="raya-discovery-panel-header">',
            "<h2>Find tasks</h2>",
            (
                '<p class="raya-discovery-panel-rail-summary" '
                'data-raya-discovery-panel-rail-summary="controls" '
                'aria-hidden="true"></p>'
            ),
            (
                '<button type="button" data-raya-discovery-toggle-panel="controls" '
                'aria-controls="raya-tasks-control-panel-body" aria-expanded="true" '
                'aria-label="Collapse controls panel">'
                "Collapse controls</button>"
            ),
            "</div>",
            (
                '<div id="raya-tasks-control-panel-body" class="raya-discovery-panel-body" '
                'data-raya-discovery-panel-body="controls" aria-hidden="false">'
            ),
            '<section class="raya-tasks-controls" aria-label="Official task controls">',
            '<fieldset class="raya-discovery-control-group">',
            "<legend>Query</legend>",
            '<label for="raya-tasks-search">Search</label>',
            '<input id="raya-tasks-search" type="search" autocomplete="off">',
            "</fieldset>",
            '<fieldset class="raya-discovery-control-group">',
            "<legend>Sort</legend>",
            '<label for="raya-tasks-sort">Sort</label>',
            '<select id="raya-tasks-sort">',
            '<option value="course">Course order</option>',
            '<option value="due">Due date</option>',
            '<option value="type">Type</option>',
            "</select>",
            "</fieldset>",
            '<fieldset class="raya-discovery-control-group">',
            "<legend>Object type</legend>",
            '<div class="raya-task-filters" aria-label="Task type filters">',
            "\n".join(type_buttons),
            "</div>",
            "</fieldset>",
            '<fieldset class="raya-discovery-control-group">',
            "<legend>Reset</legend>",
            '<button id="raya-tasks-clear" type="button">Clear</button>',
            "</fieldset>",
            "</section>",
            '<div class="raya-discovery-control-state" aria-label="Tasks workspace state">',
            '<p id="raya-tasks-status" class="raya-tasks-status" aria-live="polite"></p>',
            (
                '<p class="raya-discovery-summary" '
                f"data-raya-tasks-summary-count>{len(browser_tasks['objects'])} visible task(s).</p>"
            ),
            (
                '<p class="raya-discovery-page-focus" '
                'data-raya-tasks-page-focus hidden aria-live="polite"></p>'
            ),
            "</div>",
            (
                '<p class="raya-discovery-results-jump">'
                '<a href="#raya-tasks-results-panel">Results</a></p>'
            ),
            "</div>",
            "</aside>",
            (
                '<section id="raya-tasks-results-panel" '
                'class="raya-tasks-results-panel" '
                'aria-label="Official task results" tabindex="-1">'
            ),
            (
                '<p id="raya-tasks-empty" class="raya-tasks-empty" hidden>'
                "No matching official tasks.</p>"
            ),
            (
                '<section class="raya-tasks-results" data-raya-tasks-results '
                'aria-label="Official task results">'
            ),
            "\n".join(cards),
            "</section>",
            "</section>",
            (
                '<aside class="raya-tasks-context-panel" data-raya-tasks-context '
                'aria-label="Tasks context panel">'
            ),
            '<div class="raya-discovery-panel-header">',
            "<h2>Context</h2>",
            (
                '<p class="raya-discovery-panel-rail-summary" '
                'data-raya-discovery-panel-rail-summary="context" '
                'aria-hidden="true"></p>'
            ),
            (
                '<button type="button" data-raya-discovery-toggle-panel="context" '
                'aria-controls="raya-tasks-context-panel-body" aria-expanded="true" '
                'aria-label="Collapse context panel">'
                "Collapse context</button>"
            ),
            "</div>",
            (
                '<div id="raya-tasks-context-panel-body" class="raya-discovery-panel-body" '
                'data-raya-discovery-panel-body="context" aria-hidden="false" '
                'aria-live="polite">'
            ),
            "<p data-raya-tasks-context-title>Select or filter an official task.</p>",
            (
                '<p class="raya-discovery-context-meta" '
                "data-raya-tasks-context-meta>Accepted public task metadata only.</p>"
            ),
            (
                '<p class="raya-discovery-context-actions" '
                "data-raya-tasks-context-actions hidden></p>"
            ),
            "</div>",
            "</aside>",
            "</section>",
            "</section>",
            _render_discovery_overview(
                kind="tasks",
                title="Official tasks workspace",
                summary=(
                    "Use local filters and sorting to inspect accepted "
                    "task-family objects from course source."
                ),
                meta=[
                    ("Task-family objects", f"{len(browser_tasks['objects'])}"),
                    ("Object types", f"{len(browser_tasks['types'])}"),
                    (
                        "Source scope",
                        "Accepted assignments, exams, projects, and tasks",
                    ),
                    ("Reset path", "Clear or Escape"),
                ],
                actions=[
                    ("Open search", "../search/index.html"),
                    ("View graph", "../graph/index.html"),
                    ("Open practice", "../practice/index.html"),
                    ("Open schedule", "../schedule/index.html"),
                ],
            ),
            _render_discovery_quick_guide(
                kind="tasks",
                cards=[
                    ("Find", "Filter accepted task-family objects by text and type."),
                    ("Sort", "Switch course order, authored due date, or type."),
                    ("Inspect", "Select visible tasks to read public planning fields."),
                    ("Open", "Return to the owning page or graph focus."),
                ],
            ),
            '<script type="application/json" id="raya-tasks-data">',
            tasks_payload,
            "</script>",
            "</main>",
            f'<script src="{html.escape(accessibility_js_href)}" defer></script>',
            f'<script src="{html.escape(discovery_js_href)}" defer></script>',
            f'<script src="{html.escape(tasks_js_href)}" defer></script>',
            "</body>",
            "</html>",
            "",
        ]
    )


def _write_schedule_surface(
    *,
    site_dir: Path,
    content_model: ContentModel,
    official_by_page: dict[str, list[dict[str, Any]]],
    course_title: str,
    language: str,
    skin_context: SkinContext,
    report: ValidationReport,
) -> None:
    schedule_path = site_dir / STATIC_SCHEDULE_PATH
    schedule_path.parent.mkdir(parents=True, exist_ok=True)
    report.wrote_output(schedule_path.parent)
    schedule_path.write_text(
        _render_schedule_surface(
            content_model=content_model,
            official_by_page=official_by_page,
            course_title=course_title,
            language=language,
            skin_context=skin_context,
        ),
        encoding="utf-8",
    )
    report.wrote_output(schedule_path)


def _render_schedule_surface(
    *,
    content_model: ContentModel,
    official_by_page: dict[str, list[dict[str, Any]]],
    course_title: str,
    language: str,
    skin_context: SkinContext,
) -> str:
    stylesheet_href = _relative_href(
        STATIC_SCHEDULE_PATH.as_posix(), RENDER_STYLESHEET_PATH
    )
    skin_stylesheet_href = _relative_href(
        STATIC_SCHEDULE_PATH.as_posix(),
        SKIN_STYLESHEET_PATH,
    )
    accessibility_css_href = _relative_href(
        STATIC_SCHEDULE_PATH.as_posix(),
        f"{ACCESSIBILITY_RESOURCE_PATH}/{OPEN_DYSLEXIC_CSS_NAME}",
    )
    accessibility_js_href = _relative_href(
        STATIC_SCHEDULE_PATH.as_posix(),
        f"{ACCESSIBILITY_RESOURCE_PATH}/{OPEN_DYSLEXIC_VOLATILE_JS_NAME}",
    )
    discovery_js_href = _relative_href(
        STATIC_SCHEDULE_PATH.as_posix(),
        Path(DISCOVERY_RESOURCE_PATH) / DISCOVERY_SCRIPT_NAME,
    )
    schedule_js_href = _relative_href(
        STATIC_SCHEDULE_PATH.as_posix(),
        Path(SCHEDULE_RESOURCE_PATH) / SCHEDULE_SCRIPT_NAME,
    )
    root_skin = skin_id_for_source_path(
        content_model.pages[0].source_path, skin_context
    )
    schedule_payload = _browser_schedule_payload(content_model, official_by_page)
    schedule_payload_text = _json_script_text(schedule_payload)
    dated_event_type_count = sum(
        1 for count in schedule_payload["event_counts"].values() if count
    )
    type_buttons = [
        (
            '<button class="raya-schedule-chip" type="button" '
            'data-raya-schedule-type-filter="all" aria-pressed="true">'
            f"All ({len(schedule_payload['items'])})"
            "</button>"
        )
    ]
    for type_info in schedule_payload["types"]:
        type_buttons.append(
            (
                '<button class="raya-schedule-chip" type="button" '
                f'data-raya-schedule-type-filter="{html.escape(type_info["type"], quote=True)}" '
                'aria-pressed="false">'
                f"{html.escape(type_info['label'])} ({type_info['count']})"
                "</button>"
            )
        )
    kind_buttons = [
        (
            '<button class="raya-schedule-chip" type="button" '
            'data-raya-schedule-kind-filter="all" aria-pressed="true">'
            f"All dated ({len(schedule_payload['items'])})"
            "</button>"
        ),
        (
            '<button class="raya-schedule-chip" type="button" '
            'data-raya-schedule-kind-filter="due" aria-pressed="false">'
            f"Due ({schedule_payload['event_counts'].get('due', 0)})"
            "</button>"
        ),
        (
            '<button class="raya-schedule-chip" type="button" '
            'data-raya-schedule-kind-filter="available" aria-pressed="false">'
            f"Available ({schedule_payload['event_counts'].get('available', 0)})"
            "</button>"
        ),
    ]

    cards = []
    for order, item in enumerate(schedule_payload["items"]):
        tags_html = "".join(
            f'<span class="raya-schedule-tag">{html.escape(tag)}</span>'
            for tag in item["tags"]
        )
        meta_bits = [
            item["event_label"],
            item["type_label"],
            f"From {item['page_title']}",
            item["points"],
            f"Weight {item['weight']}" if item["weight"] else "",
            f"Status {item['status']}" if item["status"] else "",
        ]
        cards.append(
            "\n".join(
                [
                    (
                        '<article class="raya-schedule-item" '
                        f'data-raya-schedule-item="{html.escape(item["id"], quote=True)}" '
                        f'data-raya-schedule-type="{html.escape(item["type"], quote=True)}" '
                        f'data-raya-schedule-kind="{html.escape(item["event_kind"], quote=True)}" '
                        f'data-raya-schedule-page="{html.escape(item["page_id"], quote=True)}" '
                        f'data-raya-schedule-order="{order}" '
                        'data-raya-schedule-active="false">'
                    ),
                    '<header class="raya-schedule-item-header">',
                    (
                        '<span class="raya-schedule-date">'
                        f"{html.escape(item['event_date'])}</span>"
                    ),
                    (
                        '<span class="raya-schedule-kind">'
                        f"{html.escape(item['event_kind_label'])}</span>"
                    ),
                    "</header>",
                    f"<h3>{html.escape(item['title'] or item['preview'])}</h3>",
                    (
                        '<p class="raya-schedule-preview">'
                        f"{html.escape(item['preview'])}</p>"
                        if item["preview"] and item["preview"] != item["title"]
                        else ""
                    ),
                    (
                        '<p class="raya-schedule-meta">'
                        f"{html.escape(' | '.join(bit for bit in meta_bits if bit))}"
                        "</p>"
                    ),
                    (
                        f'<p class="raya-schedule-tags">{tags_html}</p>'
                        if tags_html
                        else ""
                    ),
                    '<p class="raya-schedule-actions">',
                    (
                        '<a class="raya-schedule-open" '
                        f'href="{html.escape(item["page_url"])}">Open page</a>'
                    ),
                    (
                        '<a class="raya-schedule-graph" '
                        f'href="{html.escape(item["graph_url"])}" '
                        f'aria-label="View {html.escape(item["page_title"], quote=True)} in course graph">'
                        "View in graph</a>"
                    ),
                    "</p>",
                    "</article>",
                ]
            )
        )

    return "\n".join(
        [
            "<!doctype html>",
            f'<html lang="{html.escape(language)}">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>Official Schedule - {html.escape(course_title)}</title>",
            f'<link rel="stylesheet" href="{html.escape(stylesheet_href)}">',
            f'<link rel="stylesheet" href="{html.escape(skin_stylesheet_href)}">',
            f'<link rel="stylesheet" href="{html.escape(accessibility_css_href)}">',
            "</head>",
            (
                f'<body data-raya-surface="schedule" '
                f'data-raya-skin="{html.escape(root_skin, quote=True)}">'
            ),
            '<a class="raya-skip-link" href="#raya-schedule-main">Skip to schedule</a>',
            _render_discovery_command_bar(
                course_title=course_title,
                workspace_label="Official schedule workspace",
                current_workspace="schedule",
                home_href="../../index.html",
                search_href="../search/index.html",
                graph_href="../graph/index.html",
                practice_href="../practice/index.html",
                tasks_href="../tasks/index.html",
                schedule_href="index.html",
            ),
            (
                '<main id="raya-schedule-main" class="raya-schedule-page" '
                'data-raya-schedule-page data-raya-discovery-page '
                'data-raya-discovery-rail-state="expanded" '
                'data-raya-discovery-controls-state="expanded" '
                'data-raya-discovery-context-state="expanded" tabindex="-1">'
            ),
            '<header class="raya-schedule-header raya-discovery-header">',
            "<h1>Official Schedule</h1>",
            (
                "<p>Scan dated official assignments, projects, exams, and tasks. "
                "Dates are authored course metadata from accepted official objects.</p>"
            ),
            "</header>",
            '<section class="raya-discovery-workspace-shell" aria-label="Course discovery workspace">',
            _render_discovery_course_rail(
                content_model=content_model,
                course_title=course_title,
                current_workspace="schedule",
                from_path=STATIC_SCHEDULE_PATH.as_posix(),
                official_by_page=official_by_page,
            ),
            '<section class="raya-schedule-workspace" aria-label="Official schedule workspace">',
            '<aside class="raya-schedule-control-panel" aria-label="Schedule controls panel">',
            '<div class="raya-discovery-panel-header">',
            "<h2>Find schedule items</h2>",
            (
                '<p class="raya-discovery-panel-rail-summary" '
                'data-raya-discovery-panel-rail-summary="controls" '
                'aria-hidden="true"></p>'
            ),
            (
                '<button type="button" data-raya-discovery-toggle-panel="controls" '
                'aria-controls="raya-schedule-control-panel-body" aria-expanded="true" '
                'aria-label="Collapse controls panel">'
                "Collapse controls</button>"
            ),
            "</div>",
            (
                '<div id="raya-schedule-control-panel-body" class="raya-discovery-panel-body" '
                'data-raya-discovery-panel-body="controls" aria-hidden="false">'
            ),
            '<section class="raya-schedule-controls" aria-label="Official schedule controls">',
            '<fieldset class="raya-discovery-control-group">',
            "<legend>Query</legend>",
            '<label for="raya-schedule-search">Search</label>',
            '<input id="raya-schedule-search" type="search" autocomplete="off">',
            "</fieldset>",
            '<fieldset class="raya-discovery-control-group">',
            "<legend>Date kind</legend>",
            '<div class="raya-schedule-filters" aria-label="Schedule event filters">',
            "\n".join(kind_buttons),
            "</div>",
            "</fieldset>",
            '<fieldset class="raya-discovery-control-group">',
            "<legend>Object type</legend>",
            '<div class="raya-schedule-filters" aria-label="Schedule type filters">',
            "\n".join(type_buttons),
            "</div>",
            "</fieldset>",
            '<fieldset class="raya-discovery-control-group">',
            "<legend>Reset</legend>",
            '<button id="raya-schedule-clear" type="button">Clear</button>',
            "</fieldset>",
            "</section>",
            '<div class="raya-discovery-control-state" aria-label="Schedule workspace state">',
            '<p id="raya-schedule-status" class="raya-schedule-status" aria-live="polite"></p>',
            (
                '<p class="raya-discovery-summary" '
                f"data-raya-schedule-summary-count>{len(schedule_payload['items'])} visible schedule item(s).</p>"
            ),
            (
                '<p class="raya-discovery-page-focus" '
                'data-raya-schedule-page-focus hidden aria-live="polite"></p>'
            ),
            "</div>",
            (
                '<p class="raya-discovery-results-jump">'
                '<a href="#raya-schedule-results-panel">Results</a></p>'
            ),
            "</div>",
            "</aside>",
            (
                '<section id="raya-schedule-results-panel" '
                'class="raya-schedule-results-panel" '
                'aria-label="Official schedule results" tabindex="-1">'
            ),
            (
                '<p id="raya-schedule-empty" class="raya-schedule-empty" hidden>'
                "No matching dated official work.</p>"
            ),
            (
                '<section class="raya-schedule-results" data-raya-schedule-results '
                'aria-label="Official schedule results">'
            ),
            "\n".join(cards),
            "</section>",
            "</section>",
            (
                '<aside class="raya-schedule-context-panel" data-raya-schedule-context '
                'aria-label="Schedule context panel">'
            ),
            '<div class="raya-discovery-panel-header">',
            "<h2>Context</h2>",
            (
                '<p class="raya-discovery-panel-rail-summary" '
                'data-raya-discovery-panel-rail-summary="context" '
                'aria-hidden="true"></p>'
            ),
            (
                '<button type="button" data-raya-discovery-toggle-panel="context" '
                'aria-controls="raya-schedule-context-panel-body" aria-expanded="true" '
                'aria-label="Collapse context panel">'
                "Collapse context</button>"
            ),
            "</div>",
            (
                '<div id="raya-schedule-context-panel-body" class="raya-discovery-panel-body" '
                'data-raya-discovery-panel-body="context" aria-hidden="false" '
                'aria-live="polite">'
            ),
            "<p data-raya-schedule-context-title>Select or filter a dated official item.</p>",
            (
                '<p class="raya-discovery-context-meta" '
                "data-raya-schedule-context-meta>Accepted public dated task metadata only.</p>"
            ),
            (
                '<p class="raya-discovery-context-actions" '
                "data-raya-schedule-context-actions hidden></p>"
            ),
            "</div>",
            "</aside>",
            "</section>",
            "</section>",
            _render_discovery_overview(
                kind="schedule",
                title="Official schedule workspace",
                summary=(
                    "Use local filters to scan authored due and available "
                    "dates across accepted task-family objects."
                ),
                meta=[
                    ("Dated objects", f"{len(schedule_payload['items'])}"),
                    ("Dated event types", f"{dated_event_type_count}"),
                    ("Source scope", "Authored due and available dates"),
                    ("Reset path", "Clear or Escape"),
                ],
                actions=[
                    ("Open search", "../search/index.html"),
                    ("View graph", "../graph/index.html"),
                    ("Open practice", "../practice/index.html"),
                    ("Open tasks", "../tasks/index.html"),
                ],
            ),
            _render_discovery_quick_guide(
                kind="schedule",
                cards=[
                    ("Find", "Filter dated official work by text, date kind, and type."),
                    (
                        "Scan dates",
                        "Read authored due and available dates as course metadata.",
                    ),
                    (
                        "Inspect",
                        "Select visible dated items to read public planning fields.",
                    ),
                    ("Open", "Return to the owning page or graph focus."),
                ],
            ),
            '<script type="application/json" id="raya-schedule-data">',
            schedule_payload_text,
            "</script>",
            "</main>",
            f'<script src="{html.escape(accessibility_js_href)}" defer></script>',
            f'<script src="{html.escape(discovery_js_href)}" defer></script>',
            f'<script src="{html.escape(schedule_js_href)}" defer></script>',
            "</body>",
            "</html>",
            "",
        ]
    )


def _browser_tasks_payload(
    content_model: ContentModel,
    official_by_page: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    objects: list[dict[str, Any]] = []
    type_counts: dict[str, int] = defaultdict(int)
    for page in content_model.pages:
        page_objects = sorted(
            official_by_page.get(page.id, []),
            key=lambda item: (
                item.get("source_order")
                if isinstance(item.get("source_order"), int)
                else 0,
                str(item.get("id") or ""),
            ),
        )
        for item in page_objects:
            task_summary = _official_public_task_summary(item)
            if task_summary is None:
                continue
            object_type = task_summary["type"]
            object_id = task_summary["id"]
            content_map = task_summary["content"]
            title = task_summary["title"]
            preview = task_summary["preview"]
            anchor = f"raya-official-{_safe_map_fragment_id(object_id)}"
            page_url = (
                _relative_href(STATIC_TASKS_PATH.as_posix(), page.output_path)
                + f"#{anchor}"
            )
            graph_url = _href_with_query(
                _relative_href(STATIC_TASKS_PATH.as_posix(), STATIC_GRAPH_PATH.as_posix()),
                {"page": page.id},
            )
            type_counts[object_type] += 1
            objects.append(
                {
                    "anchor": anchor,
                    "authority": task_summary["authority"],
                    "available": _official_public_text(content_map, ("available",)),
                    "due": _official_public_text(content_map, ("due",)),
                    "graph_url": graph_url,
                    "id": object_id,
                    "page_id": page.id,
                    "page_title": page.title,
                    "page_url": page_url,
                    "points": _official_public_text(content_map, ("points",)),
                    "preview": preview,
                    "status": _official_public_text(content_map, ("status",)),
                    "tags": _official_public_tags(content_map),
                    "title": title,
                    "type": object_type,
                    "type_label": _official_type_label(object_type),
                    "weight": _official_public_text(content_map, ("weight",)),
                }
            )
    types = [
        {
            "count": count,
            "label": _official_type_label(object_type),
            "type": object_type,
        }
        for object_type, count in sorted(
            type_counts.items(),
            key=lambda pair: (_official_type_label(pair[0]), pair[0]),
        )
    ]
    return {
        "objects": objects,
        "types": types,
        "version": 1,
    }


def _official_public_task_summary(item: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    object_type = str(item.get("type") or "").strip()
    if object_type not in _OFFICIAL_TASK_TYPES:
        return None
    object_id = str(item.get("id") or "").strip()
    if not object_id:
        return None
    content = item.get("content")
    content_map = content if isinstance(content, dict) else {}
    title = _official_public_text(content_map, ("title",))
    preview = _official_public_text(
        content_map,
        ("summary", "prompt", "instructions", "body", "question"),
    )
    if not title and preview:
        title = preview
    if not preview:
        preview = title
    if not title and not preview:
        return None
    authority = str(item.get("authority") or "official").strip() or "official"
    return {
        "authority": authority,
        "content": content_map,
        "id": object_id,
        "preview": preview,
        "title": title,
        "type": object_type,
    }


def _browser_graph_study_objects(
    page: ContentPage,
    page_objects: list[dict[str, Any]],
) -> list[dict[str, str]]:
    objects: list[dict[str, str]] = []
    sorted_objects = sorted(
        page_objects,
        key=lambda item: (
            item.get("source_order")
            if isinstance(item.get("source_order"), int)
            else 0,
            str(item.get("id") or ""),
        ),
    )
    for item in sorted_objects:
        if not isinstance(item, dict):
            continue
        object_id = str(item.get("id") or "").strip()
        object_type = str(item.get("type") or "practice").strip() or "practice"
        if not object_id:
            continue
        task_summary = _official_public_task_summary(item)
        if task_summary is not None:
            title = task_summary["title"]
            preview = task_summary["preview"]
            content_map = task_summary["content"]
        else:
            title = _official_type_label(object_type)
            preview = _official_graph_preview_text(item)
            content_map = {}
        if task_summary is None and not preview:
            continue
        if not title and preview:
            title = preview
        if not preview:
            preview = title
        anchor = f"raya-official-{_safe_map_fragment_id(object_id)}"
        payload = {
            "id": object_id,
            "preview": preview,
            "title": title,
            "type": object_type,
            "type_label": _official_type_label(object_type),
            "url": (
                _relative_href(STATIC_GRAPH_PATH.as_posix(), page.output_path)
                + f"#{anchor}"
            ),
        }
        if task_summary is not None:
            available = _official_public_text(content_map, ("available",))
            due = _official_public_text(content_map, ("due",))
            if available:
                payload["available"] = available
            if due:
                payload["due"] = due
        objects.append(payload)
    return objects


def _official_graph_preview_text(item: dict[str, Any]) -> str:
    content = item.get("content")
    if not isinstance(content, dict):
        return ""
    object_type = str(item.get("type") or "")
    if object_type == "card":
        return _official_public_text(content, ("front",))
    if object_type == "prompt":
        return _official_public_text(content, ("prompt",))
    if object_type == "quiz":
        questions = content.get("questions")
        if isinstance(questions, list):
            for question in questions:
                if isinstance(question, dict):
                    prompt = _official_public_text(question, ("prompt",))
                    if prompt:
                        return prompt
        return ""
    return _official_public_text(
        content,
        ("title", "summary", "prompt", "instructions", "body", "question"),
    )


def _browser_schedule_payload(
    content_model: ContentModel,
    official_by_page: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    tasks_payload = _browser_tasks_payload(content_model, official_by_page)
    type_counts: dict[str, int] = defaultdict(int)
    event_counts: dict[str, int] = defaultdict(int)
    items: list[dict[str, Any]] = []
    for task in tasks_payload["objects"]:
        event_kind, event_date = _task_payload_event(task)
        if not event_date:
            continue
        type_counts[task["type"]] += 1
        event_counts[event_kind] += 1
        event_kind_label = "Due" if event_kind == "due" else "Available"
        item = dict(task)
        item["event_date"] = event_date
        item["event_kind"] = event_kind
        item["event_kind_label"] = event_kind_label
        item["event_label"] = f"{event_kind_label} {event_date}"
        items.append(item)
    items.sort(
        key=lambda item: (
            item["event_date"],
            _page_sequence_index(content_model, str(item["page_id"])),
            str(item["id"]),
        )
    )
    types = [
        {
            "count": count,
            "label": _official_type_label(object_type),
            "type": object_type,
        }
        for object_type, count in sorted(
            type_counts.items(),
            key=lambda pair: (_official_type_label(pair[0]), pair[0]),
        )
    ]
    return {
        "event_counts": dict(event_counts),
        "items": items,
        "types": types,
        "version": 1,
    }


def _task_payload_event(task: dict[str, Any]) -> tuple[str, str]:
    due = str(task.get("due") or "").strip()
    if due:
        return "due", due
    available = str(task.get("available") or "").strip()
    if available:
        return "available", available
    return "", ""


def _official_task_event_date(item: dict[str, Any]) -> str:
    content = item.get("content")
    content_map = content if isinstance(content, dict) else {}
    due = _official_public_text(content_map, ("due",))
    if due:
        return due
    return _official_public_text(content_map, ("available",))


def _page_sequence_index(content_model: ContentModel, page_id: str) -> int:
    for index, page in enumerate(content_model.pages):
        if page.id == page_id:
            return index
    return 0


def _official_public_text(
    content: dict[str, Any],
    fields: tuple[str, ...],
) -> str:
    for field in fields:
        text = _official_public_scalar_text(content.get(field))
        if text:
            return text
    return ""


def _official_public_tags(content: dict[str, Any]) -> list[str]:
    value = content.get("tags")
    if isinstance(value, (list, tuple)):
        return [
            text
            for text in (_official_public_scalar_text(tag) for tag in value)
            if text
        ]
    text = _official_public_scalar_text(value)
    return [text] if text else []


def _official_public_scalar_text(value: Any) -> str:
    if value is None or isinstance(value, (dict, list, tuple, set)):
        return ""
    return " ".join(str(value).split())


def _official_preview_text(item: dict[str, Any]) -> str:
    content = item.get("content")
    if not isinstance(content, dict):
        return ""
    object_type = str(item.get("type") or "")
    if object_type == "card":
        return _official_plain_text(content.get("front"))
    if object_type == "prompt":
        return _official_plain_text(content.get("prompt"))
    if object_type == "quiz":
        questions = content.get("questions")
        if isinstance(questions, list):
            for question in questions:
                if isinstance(question, dict):
                    prompt = _official_plain_text(question.get("prompt"))
                    if prompt:
                        return prompt
        return ""
    for field in ("title", "summary", "prompt", "instructions", "body", "question"):
        preview = _official_plain_text(content.get(field))
        if preview:
            return preview
    return ""


def _official_plain_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "; ".join(
            text for text in (_official_plain_text(item) for item in value) if text
        )
    if isinstance(value, dict):
        return "; ".join(
            text
            for text in (_official_plain_text(item) for item in value.values())
            if text
        )
    return " ".join(str(value).split())


def _json_script_text(data: dict[str, Any]) -> str:
    return (
        json.dumps(data, ensure_ascii=False, sort_keys=True)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _reviewed_output_excerpt(reviewed: ReviewedOutput) -> str:
    for reviewed_file in reviewed.files:
        if reviewed_file.kind not in {"stdout", "text", "output"}:
            continue
        text = reviewed_file.path.read_text(encoding="utf-8", errors="replace")
        excerpt = "\n".join(text.splitlines()[:16])
        if len(excerpt) > 2000:
            excerpt = excerpt[:2000]
        if excerpt:
            return (
                '<pre class="raya-reviewed-output-excerpt"><code>'
                f"{html.escape(excerpt)}"
                "</code></pre>"
            )
    return ""


def _reference_preview(reference: SourceReference) -> str:
    if reference.kind == "code":
        text = reference.source_path.read_text(encoding="utf-8", errors="replace")
        excerpt = "\n".join(text.splitlines()[:12])
        return (
            '<pre class="raya-reference-preview"><code>'
            f"{html.escape(excerpt)}"
            "</code></pre>"
            if excerpt
            else ""
        )
    if reference.kind == "notebook":
        try:
            data = json.loads(reference.source_path.read_text(encoding="utf-8"))
        except Exception:
            return ""
        cells = data.get("cells")
        if not isinstance(cells, list):
            return ""
        lines: list[str] = []
        for index, cell in enumerate(cells[:5], start=1):
            if not isinstance(cell, dict):
                continue
            cell_type = str(cell.get("cell_type") or "cell")
            source = cell.get("source")
            if isinstance(source, list):
                source_text = "".join(str(part) for part in source)
            elif isinstance(source, str):
                source_text = source
            else:
                source_text = ""
            first_line = next(
                (line.strip() for line in source_text.splitlines() if line.strip()),
                "",
            )
            lines.append(f"{index}. {cell_type}: {first_line}")
        if not lines:
            return ""
        return (
            '<pre class="raya-reference-preview"><code>'
            f"{html.escape(chr(10).join(lines))}"
            "</code></pre>"
        )
    return ""


def _official_index(
    course_id: str,
    official_objects: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "course_id": course_id,
        "objects": official_objects,
    }


def _official_counts(
    official_objects: list[dict[str, Any]],
    *,
    content_model: ContentModel,
    course_id: str,
) -> dict[str, dict[str, int]]:
    page_ids_by_scope = _official_page_ids_by_scope(content_model, course_id)
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for item in official_objects:
        scope = item.get("scope")
        quantum = scope.get("quantum") if isinstance(scope, dict) else None
        object_type = item.get("type")
        if isinstance(quantum, str) and isinstance(object_type, str):
            page_id = page_ids_by_scope.get(quantum)
            if page_id is not None:
                counts[page_id][object_type] += 1
    return {quantum: dict(values) for quantum, values in counts.items()}


def _official_objects_by_page(
    official_objects: list[dict[str, Any]],
    *,
    content_model: ContentModel,
    course_id: str,
) -> dict[str, list[dict[str, Any]]]:
    page_ids_by_scope = _official_page_ids_by_scope(content_model, course_id)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in official_objects:
        scope = item.get("scope")
        quantum = scope.get("quantum") if isinstance(scope, dict) else None
        if isinstance(quantum, str):
            page_id = page_ids_by_scope.get(quantum)
            if page_id is not None:
                grouped[page_id].append(item)
    return {page_id: list(values) for page_id, values in grouped.items()}


def _official_page_ids_by_scope(
    content_model: ContentModel,
    course_id: str,
) -> dict[str, str]:
    page_ids: dict[str, str] = {}
    for page in content_model.pages:
        page_ids[page.id] = page.id
        page_ids[page.rel_path] = page.id
        page_ids[f"{course_id}:{page.rel_path}"] = page.id
        for alias in page.aliases:
            page_ids[alias] = page.id
    return page_ids


def _aggregate_study_counts(
    page_id: str,
    content_model: ContentModel,
    official_counts: dict[str, dict[str, int]],
) -> dict[str, int]:
    aggregate: dict[str, int] = defaultdict(int)
    for object_type, count in official_counts.get(page_id, {}).items():
        aggregate[object_type] += count
    for child_id in content_model.children_by_parent.get(page_id, []):
        for object_type, count in _aggregate_study_counts(
            child_id,
            content_model,
            official_counts,
        ).items():
            aggregate[object_type] += count
    return dict(sorted(aggregate.items()))


def _study_counts_text(counts: dict[str, int]) -> str:
    labels = []
    for object_type, count in sorted(counts.items()):
        label = object_type.capitalize()
        if count != 1:
            label += "s"
        labels.append(f"{label}: {count}")
    return ", ".join(labels)


def _flatten_navigation(content_model: ContentModel) -> list[str]:
    ordered: list[str] = []

    def visit(page_id: str | None) -> None:
        if page_id is not None:
            ordered.append(page_id)
        for child_id in content_model.children_by_parent.get(page_id, []):
            visit(child_id)

    visit(content_model.root_id)
    return ordered


def _breadcrumb_pages(
    page: ContentPage,
    content_model: ContentModel,
) -> list[ContentPage]:
    breadcrumbs: list[ContentPage] = []
    current = page
    while current.parent_id is not None:
        parent = content_model.pages_by_id.get(current.parent_id)
        if parent is None:
            break
        breadcrumbs.append(parent)
        current = parent
    breadcrumbs.reverse()
    return breadcrumbs


def _write_json(path: Path, data: dict[str, Any], report: ValidationReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report.wrote_output(path)


def _write_rich_render_resources(
    site_dir: Path,
    report: ValidationReport,
    *,
    skin_context: SkinContext,
) -> None:
    stylesheet = site_dir / RENDER_STYLESHEET_PATH
    stylesheet.parent.mkdir(parents=True, exist_ok=True)
    stylesheet.write_text(rich_render_css(), encoding="utf-8")
    report.wrote_output(stylesheet)
    skin_stylesheet = site_dir / SKIN_STYLESHEET_PATH
    skin_stylesheet.parent.mkdir(parents=True, exist_ok=True)
    skin_stylesheet.write_text(render_skin_css(skin_context), encoding="utf-8")
    report.wrote_output(skin_stylesheet)
    skin_prepaint_js_path = skin_stylesheet.parent / SKIN_PREPAINT_JS_NAME
    skin_toggle_js_path = skin_stylesheet.parent / SKIN_TOGGLE_JS_NAME
    skin_prepaint_js_path.write_text(skin_prepaint_script(), encoding="utf-8")
    skin_toggle_js_path.write_text(skin_toggle_script(), encoding="utf-8")
    report.wrote_output(skin_prepaint_js_path)
    report.wrote_output(skin_toggle_js_path)
    accessibility = open_dyslexic_resources()
    accessibility_dir = site_dir / ACCESSIBILITY_RESOURCE_PATH
    accessibility_dir.mkdir(parents=True, exist_ok=True)
    css_path = accessibility_dir / OPEN_DYSLEXIC_CSS_NAME
    prepaint_js_path = accessibility_dir / COMFORT_PREPAINT_JS_NAME
    js_path = accessibility_dir / OPEN_DYSLEXIC_JS_NAME
    volatile_js_path = accessibility_dir / OPEN_DYSLEXIC_VOLATILE_JS_NAME
    font_dir = accessibility_dir / "fonts"
    font_dir.mkdir(parents=True, exist_ok=True)
    font_path = font_dir / accessibility.font_name
    if not accessibility.source_font.is_file():
        report.add_error(
            "Missing local OpenDyslexic font asset",
            path=Path(str(accessibility.source_font)),
            next_action=(
                "Add the local OpenDyslexic font under "
                "packages/static/src/raya_static/assets/accessibility/open-dyslexic/"
            ),
        )
        return
    css_path.write_text(accessibility.css, encoding="utf-8")
    prepaint_js_path.write_text(accessibility.prepaint_javascript, encoding="utf-8")
    js_path.write_text(accessibility.javascript, encoding="utf-8")
    volatile_js_path.write_text(accessibility.volatile_javascript, encoding="utf-8")
    with resources.as_file(accessibility.source_font) as source_font:
        shutil.copy2(source_font, font_path)
    report.wrote_output(css_path)
    report.wrote_output(prepaint_js_path)
    report.wrote_output(js_path)
    report.wrote_output(volatile_js_path)
    report.wrote_output(font_path)


def _write_shell_resources(site_dir: Path, report: ValidationReport) -> None:
    resources = shell_resources()
    shell_dir = site_dir / SHELL_RESOURCE_PATH
    shell_dir.mkdir(parents=True, exist_ok=True)
    report.wrote_output(shell_dir)
    script_path = shell_dir / SHELL_SCRIPT_NAME
    script_path.write_text(resources.javascript, encoding="utf-8")
    report.wrote_output(script_path)


def _write_graph_resources(site_dir: Path, report: ValidationReport) -> None:
    resources = graph_resources()
    graph_dir = site_dir / GRAPH_RESOURCE_PATH
    graph_dir.mkdir(parents=True, exist_ok=True)
    report.wrote_output(graph_dir)
    script_path = graph_dir / GRAPH_SCRIPT_NAME
    script_path.write_text(resources.javascript, encoding="utf-8")
    report.wrote_output(script_path)


def _write_discovery_resources(site_dir: Path, report: ValidationReport) -> None:
    resources = discovery_resources()
    discovery_dir = site_dir / DISCOVERY_RESOURCE_PATH
    discovery_dir.mkdir(parents=True, exist_ok=True)
    report.wrote_output(discovery_dir)
    script_path = discovery_dir / DISCOVERY_SCRIPT_NAME
    script_path.write_text(resources.javascript, encoding="utf-8")
    report.wrote_output(script_path)


def _write_search_resources(site_dir: Path, report: ValidationReport) -> None:
    resources = search_resources()
    search_dir = site_dir / SEARCH_RESOURCE_PATH
    search_dir.mkdir(parents=True, exist_ok=True)
    report.wrote_output(search_dir)
    script_path = search_dir / SEARCH_SCRIPT_NAME
    script_path.write_text(resources.javascript, encoding="utf-8")
    report.wrote_output(script_path)


def _write_practice_resources(site_dir: Path, report: ValidationReport) -> None:
    resources = practice_resources()
    practice_dir = site_dir / PRACTICE_RESOURCE_PATH
    practice_dir.mkdir(parents=True, exist_ok=True)
    report.wrote_output(practice_dir)
    script_path = practice_dir / PRACTICE_SCRIPT_NAME
    script_path.write_text(resources.javascript, encoding="utf-8")
    report.wrote_output(script_path)


def _write_tasks_resources(site_dir: Path, report: ValidationReport) -> None:
    resources = tasks_resources()
    tasks_dir = site_dir / TASKS_RESOURCE_PATH
    tasks_dir.mkdir(parents=True, exist_ok=True)
    report.wrote_output(tasks_dir)
    script_path = tasks_dir / TASKS_SCRIPT_NAME
    script_path.write_text(resources.javascript, encoding="utf-8")
    report.wrote_output(script_path)


def _write_schedule_resources(site_dir: Path, report: ValidationReport) -> None:
    resources = schedule_resources()
    schedule_dir = site_dir / SCHEDULE_RESOURCE_PATH
    schedule_dir.mkdir(parents=True, exist_ok=True)
    report.wrote_output(schedule_dir)
    script_path = schedule_dir / SCHEDULE_SCRIPT_NAME
    script_path.write_text(resources.javascript, encoding="utf-8")
    report.wrote_output(script_path)


def _prepare_math_render_resources(
    css_chunks: list[str],
    report: ValidationReport,
) -> _MathRenderResources:
    css = "\n".join(chunk for chunk in css_chunks if chunk.strip())
    if not css:
        return _MathRenderResources(css="", font_files=())

    required_fonts = _math_font_names_from_css(css, report=report)
    if not report.ok:
        return _MathRenderResources(css=css, font_files=())
    missing_fonts = [
        name for name in required_fonts if not (MATH_FONT_SOURCE_DIR / name).is_file()
    ]
    if missing_fonts:
        report.add_error(
            "Missing local MathJax font assets",
            path=MATH_FONT_SOURCE_DIR,
            field="math.fonts",
            next_action=(
                "Reinstall renderer dependencies with "
                "`npm ci --ignore-scripts --no-audit --no-fund`. Missing CSS-referenced "
                f"font file(s): {', '.join(missing_fonts)}."
            ),
        )
        return _MathRenderResources(css=css, font_files=())

    font_files = sorted(MATH_FONT_SOURCE_DIR.glob("*.woff2"))
    if required_fonts and not font_files:
        report.add_error(
            "Missing local MathJax font assets",
            path=MATH_FONT_SOURCE_DIR,
            field="math.fonts",
            next_action=(
                "Reinstall renderer dependencies with "
                "`npm ci --ignore-scripts --no-audit --no-fund`. No .woff2 "
                "MathJax font files were found."
            ),
        )
        return _MathRenderResources(css=css, font_files=())

    return _MathRenderResources(css=css, font_files=tuple(font_files))


def _write_math_render_resources(
    site_dir: Path,
    resources: _MathRenderResources,
    report: ValidationReport,
) -> int:
    stylesheet = site_dir / MATH_STYLESHEET_PATH
    stylesheet.parent.mkdir(parents=True, exist_ok=True)
    stylesheet.write_text(resources.css, encoding="utf-8")
    report.wrote_output(stylesheet)

    if not resources.css or not resources.font_files:
        return 0

    target_fonts = stylesheet.parent / "fonts"
    target_fonts.mkdir(parents=True, exist_ok=True)
    report.wrote_output(target_fonts)
    copied = 0
    for font_file in resources.font_files:
        report.read_file(font_file)
        target = target_fonts / font_file.name
        shutil.copy2(font_file, target)
        report.wrote_output(target)
        copied += 1
    return copied


def _math_font_names_from_css(
    css: str,
    *,
    report: ValidationReport,
) -> list[str]:
    names: set[str] = set()
    for match in MATH_CSS_URL_RE.finditer(css):
        raw_url = _unquote_css_url(match.group("value"))
        font_name = _local_math_font_name(raw_url)
        if font_name is not None:
            names.add(font_name)
            continue
        if _looks_like_math_font_url(raw_url):
            report.add_error(
                "Unsupported MathJax font URL",
                path=MATH_FONT_SOURCE_DIR,
                field="math.fonts",
                next_action=(
                    "MathJax font URLs must be local relative paths under "
                    f"`fonts/`. Unsupported URL: {raw_url}."
                ),
            )
    return sorted(names)


def _unquote_css_url(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {"'", '"'}:
        return stripped[1:-1].strip()
    return stripped


def _local_math_font_name(raw_url: str) -> str | None:
    path = raw_url.split("?", 1)[0].split("#", 1)[0].strip()
    if path.startswith("./"):
        path = path[2:]
    if not path.startswith("fonts/"):
        return None
    name = path.removeprefix("fonts/")
    if "/" in name or not MATH_FONT_NAME_RE.fullmatch(name):
        return None
    return name


def _looks_like_math_font_url(raw_url: str) -> bool:
    path = raw_url.split("?", 1)[0].split("#", 1)[0].strip()
    lower = path.lower()
    return (
        lower.startswith(("http://", "https://", "//"))
        or path.startswith("/")
        or ".woff2" in lower
    )


def _validate_generated_artifact(artifact_dir: Path, report: ValidationReport) -> None:
    for generated_report in (
        validate_artifact_manifest(artifact_dir / "manifest.json"),
        validate_pages_index(artifact_dir / "data" / "pages.json"),
        validate_quanta_index(artifact_dir / "data" / "quanta.json"),
        validate_links_index(artifact_dir / "data" / "links.json"),
        validate_graph_index(artifact_dir / "data" / "graph.json"),
        validate_navigation_index(artifact_dir / "data" / "navigation.json"),
        validate_indices_index(artifact_dir / "data" / "indices.json"),
        validate_official_index(artifact_dir / "data" / "official.json"),
        validate_tasks_index(artifact_dir / "data" / "tasks.json"),
        validate_search_index(artifact_dir / "data" / "search-index.json"),
        validate_references_index(artifact_dir / "data" / "references.json"),
        validate_reviewed_outputs_index(
            artifact_dir / "data" / "reviewed-outputs.json"
        ),
        validate_numbered_objects_index(
            artifact_dir / "data" / "numbered-objects.json"
        ),
        validate_runtime_index(artifact_dir / "data" / "runtime.json"),
        validate_execution_index(artifact_dir / "data" / "execution.json"),
        validate_cache_index(artifact_dir / "data" / "cache.json"),
    ):
        _merge_report(report, generated_report)


def _merge_report(target: ValidationReport, source: ValidationReport) -> None:
    for path in source.files_read:
        target.read_file(path)
    for path in source.outputs_written:
        target.wrote_output(path)
    target.diagnostics.extend(source.diagnostics)


def _source_hash(
    root: Path,
    source_dir: Path,
) -> str:
    digest = hashlib.sha256()
    source_files = [root / "raya.yaml"]
    for support_file in (root / "pyproject.toml", root / "uv.lock"):
        if support_file.exists():
            source_files.append(support_file)
    runtime_dir = root / "runtime"
    if runtime_dir.exists():
        source_files.extend(path for path in runtime_dir.rglob("*") if path.is_file())
    if source_dir.exists():
        source_files.extend(path for path in source_dir.rglob("*") if path.is_file())
    for path in sorted(source_files):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _relative_href(from_output: str, to_output: str) -> str:
    from_dir = Path(from_output).parent
    rel = os.path.relpath(to_output, start=from_dir if str(from_dir) != "." else ".")
    return Path(rel).as_posix()


def _href_with_query(href: str, params: dict[str, str]) -> str:
    encoded = [
        f"{quote(key, safe='')}={quote(value, safe='')}"
        for key, value in params.items()
        if value
    ]
    if not encoded:
        return href
    return f"{href}?{'&'.join(encoded)}"
