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
from importlib import resources
from pathlib import Path
from typing import Any

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
from raya_schema.yaml_io import load_yaml_file
from raya_static.accessibility import (
    ACCESSIBILITY_RESOURCE_PATH,
    OPEN_DYSLEXIC_CSS_NAME,
    OPEN_DYSLEXIC_JS_NAME,
    open_dyslexic_resources,
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
    SKIN_STYLESHEET_PATH,
    SkinContext,
    load_skin_context,
    render_skin_css,
    skin_id_for_source_path,
)
from raya_static.search import SEARCH_RESOURCE_PATH, SEARCH_SCRIPT_NAME, search_resources
from raya_static.shell import SHELL_RESOURCE_PATH, SHELL_SCRIPT_NAME, shell_resources


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
MATH_STYLESHEET_PATH = Path(STATIC_RESOURCE_DIR) / "render" / "math" / "mathjax.css"
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
    official_counts = _official_counts(official_objects)
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
    )
    graph_index = _graph_index(course_id, content_model, links_index)
    graph_context_by_page = _graph_context_by_page(content_model, graph_index)
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

    for page in pages:
        numbered_context = NumberedObjectRenderContext(
            items=numbered_object_collection.items_by_page_id.get(page.id, []),
            objects_by_id=numbered_object_collection.objects_by_id,
        )
        static_environment_context = StaticEnvironmentRenderContext(
            items=static_environment_collection.items_by_page_id.get(page.id, []),
            objects_by_id=numbered_object_collection.objects_by_id,
        )
        rendered_page = _render_page(
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
            page_references=references_by_page.get(page.id, []),
            reviewed_by_reference=reviewed_by_reference,
            report=report,
            math_renderer=math_renderer,
            skin_context=skin_context,
            page_graph_context=graph_context_by_page.get(page.id, {}),
        )
        if not report.ok:
            return report
        rendered_pages.append((page, rendered_page))

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
    _write_search_resources(site_dir, report)
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
        skin_context=skin_context,
        report=report,
    )
    _write_search_surface(
        site_dir=site_dir,
        content_model=content_model,
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
        target_path = target_assets / colocated_asset_output_path(source_dir, source_path)
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

        course_relative_source_path = page.source_path.relative_to(course_root).as_posix()
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
    page_references: list[SourceReference],
    reviewed_by_reference: dict[str, ReviewedOutput],
    report: ValidationReport,
    math_renderer: MathRenderer,
    skin_context: SkinContext,
    page_graph_context: dict[str, list[dict[str, str]]],
) -> str:
    breadcrumbs = _render_breadcrumbs(page, content_model)
    generated_index = _render_generated_index(
        page,
        content_model,
        official_counts,
    )
    stylesheet_href = _relative_href(page.output_path, RENDER_STYLESHEET_PATH)
    skin_id = skin_id_for_source_path(page.source_path, skin_context)
    skin_stylesheet_href = _relative_href(page.output_path, SKIN_STYLESHEET_PATH)
    accessibility_css_href = _relative_href(
        page.output_path,
        f"{ACCESSIBILITY_RESOURCE_PATH}/{OPEN_DYSLEXIC_CSS_NAME}",
    )
    accessibility_js_href = _relative_href(
        page.output_path,
        f"{ACCESSIBILITY_RESOURCE_PATH}/{OPEN_DYSLEXIC_JS_NAME}",
    )
    shell_js_href = _relative_href(
        page.output_path,
        Path(SHELL_RESOURCE_PATH) / SHELL_SCRIPT_NAME,
    )
    search_href = _relative_href(page.output_path, STATIC_SEARCH_PATH.as_posix())
    graph_href = _relative_href(page.output_path, STATIC_GRAPH_PATH.as_posix())
    math_stylesheet_href = _relative_href(
        page.output_path,
        MATH_STYLESHEET_PATH.as_posix(),
    )
    reference_panel = _render_reference_panel(page, page_references, reviewed_by_reference)
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
    )
    article_html, toc_html = _extract_page_toc(article_html)
    learning_rail = _render_learning_rail(
        page,
        toc_html,
        content_model,
        support_panels,
        page_graph_context,
    )

    return "\n".join(
        [
            "<!doctype html>",
            f'<html lang="{html.escape(language)}" data-raya-course-map="expanded">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{html.escape(page.title)} - {html.escape(course_title)}</title>",
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
            _render_top_command_bar(course_title, search_href, graph_href),
            '<main id="raya-content" class="raya-learning-shell" data-raya-course-map="expanded">',
            _render_course_map(page, content_model),
            '<article id="raya-article" class="raya-main-article" tabindex="-1">',
            _render_article_sequence_nav(page, content_model),
            breadcrumbs,
            article_html,
            "</article>",
            learning_rail,
            "</main>",
            f'<script src="{html.escape(accessibility_js_href)}" defer></script>',
            f'<script src="{html.escape(shell_js_href)}" defer></script>',
            "</body>",
            "</html>",
            "",
        ]
    )


def _render_top_command_bar(
    course_title: str,
    search_href: str,
    graph_href: str,
) -> str:
    return "\n".join(
        [
            '<header class="raya-top-command-bar" aria-label="Course tools">',
            '<div class="raya-top-command-bar-inner">',
            f'<p class="raya-course-title">{html.escape(course_title)}</p>',
            '<div class="raya-course-tools">',
            (
                f'<a class="raya-command raya-command-search" '
                f'href="{html.escape(search_href)}" '
                'aria-label="Open course search">'
                '<span class="raya-command-label">Search</span>'
                "</a>"
            ),
            (
                f'<a class="raya-command raya-command-graph" '
                f'href="{html.escape(graph_href)}" '
                'aria-label="Open course graph">'
                '<span class="raya-command-label">Graph</span>'
                "</a>"
            ),
            _render_course_map_toggle(
                "Course map",
                class_name="raya-command raya-command-map raya-course-map-toggle",
                aria_label="Collapse course map",
            ),
            (
                '<button class="raya-command raya-command-font raya-font-toggle" type="button" '
                'aria-label="Toggle OpenDyslexic font" '
                'aria-pressed="false">'
                '<span class="raya-command-label">OpenDyslexic</span>'
                "</button>"
            ),
            "</div>",
            "</div>",
            "</header>",
        ]
    )


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
) -> str:
    aria_expanded = "true" if expanded else "false"
    aria_label_attr = (
        f' aria-label="{html.escape(aria_label, quote=True)}"' if aria_label else ""
    )
    return (
        f'<button class="{html.escape(class_name, quote=True)}" type="button" '
        "data-raya-course-map-toggle "
        'aria-controls="raya-course-map" '
        f'aria-expanded="{aria_expanded}"{aria_label_attr}>'
        f"{html.escape(label)}"
        "</button>"
    )


def _render_course_map(page: ContentPage, content_model: ContentModel) -> str:
    nav_items = []
    for target in content_model.pages:
        href = _relative_href(page.output_path, target.output_path)
        label = _navigation_label(target)
        current = ' aria-current="page"' if target.output_path == page.output_path else ""
        nav_items.append(
            '<a '
            f'href="{html.escape(href)}"{current} '
            f'data-raya-map-index="{len(nav_items) + 1}" '
            f'data-raya-map-label="{html.escape(label, quote=True)}">'
            f"{html.escape(label)}"
            "</a>"
        )
    position = html.escape(_page_position(page, content_model))
    return "\n".join(
        [
            '<nav id="raya-course-map" class="raya-course-map" aria-label="Course map" data-raya-course-map="expanded">',
            '<div class="raya-course-map-header">',
            '<p class="raya-region-title">Course map</p>',
            f'<p class="raya-page-position">{position}</p>' if position else "",
            _render_course_map_toggle("Collapse map"),
            "</div>",
            '<div class="raya-course-map-list" id="raya-course-map-list" aria-hidden="false">',
            "\n".join(nav_items),
            "</div>",
            "</nav>",
        ]
    )


def _render_learning_rail(
    page: ContentPage,
    toc_html: str,
    content_model: ContentModel,
    support_panels: str,
    page_graph_context: dict[str, list[dict[str, str]]],
) -> str:
    panels = [
        _render_page_summary_rail(page),
        _render_page_status_rail(page),
        _render_estimated_time_rail(page),
        _render_tags_rail(page),
        _render_prerequisites_rail(page, content_model),
        _render_linked_pages_rail(page, page_graph_context),
        _render_page_contents_rail(toc_html),
        _render_sequence_rail(page, content_model),
        support_panels,
    ]
    body = "\n".join(panel for panel in panels if panel)
    if not body:
        return ""
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
            (
                '<button class="raya-learning-rail-expand" type="button" '
                "data-raya-learning-rail-expand "
                'aria-controls="raya-learning-rail-body" '
                'aria-expanded="true" '
                'aria-label="Show learning context">Context</button>'
            ),
            "</aside>",
        ]
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
        return rendered_article_html, ""
    article_without_toc = (
        rendered_article_html[: match.start()] + rendered_article_html[match.end() :]
    )
    return article_without_toc, match.group(0)


def _render_page_contents_rail(toc_html: str) -> str:
    if not toc_html:
        return ""
    return _render_rail_panel("raya-page-contents", "Page contents", toc_html, expanded=True)


def _render_page_summary_rail(page: ContentPage) -> str:
    if not page.summary:
        return ""
    return _render_rail_panel(
        "raya-page-summary",
        "Summary",
        f"<p>{html.escape(page.summary)}</p>",
        expanded=True,
    )


def _render_page_status_rail(page: ContentPage) -> str:
    if not page.status:
        return ""
    return _render_rail_panel(
        "raya-page-status",
        "Status",
        f'<p><span class="raya-status-chip">{html.escape(page.status)}</span></p>',
    )


def _render_estimated_time_rail(page: ContentPage) -> str:
    if not page.estimated_time:
        return ""
    return _render_rail_panel(
        "raya-page-estimated-time",
        "Estimated time",
        f"<p>{html.escape(page.estimated_time)}</p>",
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
        href = _relative_href(page.output_path, target.output_path)
        label = target.nav_title or target.title
        items.append(f'<li><a href="{html.escape(href)}">{html.escape(label)}</a></li>')
    if not items:
        return ""
    return _render_rail_panel(
        "raya-page-prerequisites",
        "Prerequisites",
        "<ul>" + "\n".join(items) + "</ul>",
    )


def _render_linked_pages_rail(
    page: ContentPage,
    page_graph_context: dict[str, list[dict[str, str]]],
) -> str:
    sections = []
    outgoing = page_graph_context.get("outgoing", [])
    incoming = page_graph_context.get("incoming", [])
    if outgoing:
        sections.append(
            "<h3>From this page</h3>"
            "<ul>"
            + "\n".join(_linked_page_item(page, item) for item in outgoing)
            + "</ul>"
        )
    if incoming:
        sections.append(
            "<h3>Links here</h3>"
            "<ul>"
            + "\n".join(_linked_page_item(page, item) for item in incoming)
            + "</ul>"
        )
    if not sections:
        return ""
    return _render_rail_panel(
        "raya-page-linked-pages",
        "Linked pages",
        "\n".join(sections),
    )


def _linked_page_item(page: ContentPage, item: dict[str, str]) -> str:
    href = _relative_href(page.output_path, item["url"])
    return (
        f'<li><a href="{html.escape(href)}">'
        f'{html.escape(item["title"])}</a></li>'
    )


def _render_sequence_rail(page: ContentPage, content_model: ContentModel) -> str:
    sequence_nav = _render_sequence_nav(page, content_model)
    if not sequence_nav:
        return ""
    return _render_rail_panel("raya-page-sequence", "Sequence", sequence_nav)


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
    items = []
    for crumb in breadcrumbs:
        href = _relative_href(page.output_path, crumb.output_path)
        label = html.escape(crumb.nav_title)
        items.append(f'<a href="{html.escape(href)}">{label}</a>')
    return '<nav aria-label="Breadcrumbs">' + " / ".join(items) + "</nav>"


def _sequence_links(page: ContentPage, content_model: ContentModel) -> str:
    pages = content_model.pages
    current_index = next(
        (index for index, target in enumerate(pages) if target.output_path == page.output_path),
        None,
    )
    if current_index is None:
        return ""
    links: list[str] = []
    if current_index > 0:
        previous = pages[current_index - 1]
        href = _relative_href(page.output_path, previous.output_path)
        links.append(
            f'<a rel="prev" href="{html.escape(href)}">Previous: {html.escape(previous.nav_title or previous.title)}</a>'
        )
    if current_index + 1 < len(pages):
        next_page = pages[current_index + 1]
        href = _relative_href(page.output_path, next_page.output_path)
        links.append(
            f'<a rel="next" href="{html.escape(href)}">Next: {html.escape(next_page.nav_title or next_page.title)}</a>'
        )
    return "\n".join(links)


def _render_article_sequence_nav(page: ContentPage, content_model: ContentModel) -> str:
    sequence = _sequence_links(page, content_model)
    if not sequence:
        return ""
    return (
        '<nav class="raya-article-sequence raya-article-sequence-top" '
        'aria-label="Previous and next pages">'
        + sequence
        + "</nav>"
    )


def _render_sequence_nav(page: ContentPage, content_model: ContentModel) -> str:
    sequence = _sequence_links(page, content_model)
    if not sequence:
        return ""
    return '<nav aria-label="Previous and next">' + sequence + "</nav>"


def _render_generated_index(
    page: ContentPage,
    content_model: ContentModel,
    official_counts: dict[str, dict[str, int]],
) -> str:
    child_ids = content_model.children_by_parent.get(page.id, [])
    counts = _aggregate_study_counts(page.id, content_model, official_counts)
    if not child_ids and not counts:
        return ""

    parts = ['<section class="raya-generated-index" aria-label="Generated index">']
    if child_ids:
        heading = "Course Index" if page.parent_id is None else "Topics"
        parts.append(f"<h2>{html.escape(heading)}</h2>")
        parts.append("<ol>")
        for child_id in child_ids:
            child = content_model.pages_by_id[child_id]
            href = _relative_href(page.output_path, child.output_path)
            parts.append("<li>")
            parts.append(
                f'<a href="{html.escape(href)}">{html.escape(_navigation_label(child))}</a>'
            )
            parts.append(f"<p>{html.escape(child.summary)}</p>")
            if child.estimated_time:
                parts.append(
                    f"<p>Estimated time: {html.escape(child.estimated_time)}</p>"
                )
            child_counts = _aggregate_study_counts(
                child.id,
                content_model,
                official_counts,
            )
            if child_counts:
                parts.append(f"<p>{html.escape(_study_counts_text(child_counts))}</p>")
            parts.append("</li>")
        parts.append("</ol>")
    if counts:
        parts.append("<h2>Study</h2>")
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
    seen: set[tuple[str, str, str]] = set()
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
        context[source.id]["outgoing"].append(
            {
                "id": target.id,
                "title": target.nav_title or target.title,
                "url": target.output_path,
                "kind": edge["kind"],
            }
        )
        context[target.id]["incoming"].append(
            {
                "id": source.id,
                "title": source.nav_title or source.title,
                "url": source.output_path,
                "kind": edge["kind"],
            }
        )
    return context


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
                "breadcrumbs": [crumb.id for crumb in _breadcrumb_pages(page, content_model)],
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
        _index_entry(content_model.pages_by_id[child_id], official_counts, content_model)
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
        "study_counts": _aggregate_study_counts(page.id, content_model, official_counts),
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
    parts.append("<p>These files are copied for reading and download. They were not executed during build.</p>")
    parts.append("<ul>")
    for reference in references:
        href = _relative_href(page.output_path, reference.browser_path)
        label = "Notebook" if reference.kind == "notebook" else "Script"
        reviewed = reviewed_by_reference.get(reference.id)
        status = "reviewed output current" if reviewed is not None else "not executed"
        parts.append(f'<li class="raya-reference-item raya-reference-{html.escape(reference.kind)}">')
        parts.append(
            f'<p><strong>{label}</strong>: '
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
    parts.append("<p>Reviewed course support. Build and static serving did not execute code.</p>")
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
            href = _relative_href(page.output_path, reviewed_file.browser_path(reviewed))
            parts.append(
                f'<li><a href="{html.escape(href)}">{html.escape(reviewed_file.rel_path)}</a> '
                f'<span>{html.escape(reviewed_file.kind)}</span></li>'
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
            "<ul>"
            + "\n".join(file_items)
            + "</ul>"
            "</li>"
        )

    asset_items = []
    if site_assets_dir.exists():
        site_root = site_assets_dir.parents[1]
        for asset_path in sorted(path for path in site_assets_dir.rglob("*") if path.is_file()):
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
            "\n".join(edge_kind_items) if edge_kind_items else "<li>No graph edges.</li>",
            "</ul>",
            "<h3>Groups</h3>",
            "<ul>",
            "\n".join(group_items) if group_items else "<li>No graph groups.</li>",
            "</ul>",
            "<h3>Graph Pages</h3>",
            "<ul>",
            "\n".join(graph_node_items) if graph_node_items else "<li>No graph nodes.</li>",
            "</ul>",
            "<h2>Pages</h2>",
            "<ul>",
            "\n".join(page_items),
            "</ul>",
            "<h2>References</h2>",
            "<ul>",
            "\n".join(reference_items) if reference_items else "<li>No references.</li>",
            "</ul>",
            "<h2>Reviewed Outputs</h2>",
            "<ul>",
            "\n".join(reviewed_items) if reviewed_items else "<li>No reviewed outputs.</li>",
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


def _write_graph_surface(
    *,
    site_dir: Path,
    content_model: ContentModel,
    course_title: str,
    language: str,
    graph_index: dict[str, Any],
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
    skin_context: SkinContext,
) -> str:
    stylesheet_href = _relative_href(STATIC_GRAPH_PATH.as_posix(), RENDER_STYLESHEET_PATH)
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
        f"{ACCESSIBILITY_RESOURCE_PATH}/{OPEN_DYSLEXIC_JS_NAME}",
    )
    graph_js_href = _relative_href(
        STATIC_GRAPH_PATH.as_posix(),
        Path(GRAPH_RESOURCE_PATH) / GRAPH_SCRIPT_NAME,
    )
    root_skin = skin_id_for_source_path(content_model.pages[0].source_path, skin_context)
    browser_graph = _browser_graph_payload(graph_index)
    graph_payload = _json_script_text(browser_graph)
    group_buttons = [
        (
            '<button class="raya-graph-chip" type="button" '
            f'data-raya-graph-group-filter="{html.escape(group["id"], quote=True)}" '
            'aria-pressed="true">'
            f'{html.escape(group["title"])}'
            "</button>"
        )
        for group in graph_index["groups"]
    ]
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
            f'<a href="{html.escape(node["url"])}">{html.escape(node["title"])}</a>'
            '<span class="raya-graph-list-metrics">'
            f'Status: {html.escape(node["status"])}; '
            f'Edges: {edge_count}; Backlinks: {backlink_count}'
            "</span>"
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
            '<main id="raya-graph-main" class="raya-graph-page" data-raya-graph-page>',
            '<header class="raya-graph-header">',
            f'<p class="raya-course-title">{html.escape(course_title)}</p>',
            '<a class="raya-graph-back-link" href="../../index.html">Back to course</a>',
            "<h1>Course Graph</h1>",
            (
                "<p>Explore pages, unit groups, prerequisites, and content references "
                "generated from this course.</p>"
            ),
            "</header>",
            '<section class="raya-graph-controls" aria-label="Graph controls">',
            '<label for="graph-search">Search</label>',
            '<input id="graph-search" type="search" autocomplete="off">',
            '<label for="graph-layout">Layout</label>',
            (
                '<select id="graph-layout">'
                '<option value="map">Map</option>'
                '<option value="radial">Radial</option>'
                '<option value="list">List</option>'
                "</select>"
            ),
            '<button id="graph-fit" type="button">Fit</button>',
            '<button id="graph-reset" type="button">Reset</button>',
            "</section>",
            '<section class="raya-graph-groups" aria-label="Graph groups">',
            "\n".join(group_buttons),
            "</section>",
            '<p id="graph-status" class="raya-graph-status" aria-live="polite"></p>',
            (
                '<svg id="raya-graph-canvas" class="raya-graph-canvas" '
                'role="img" aria-label="Course graph"></svg>'
            ),
            '<ol id="raya-graph-list" class="raya-graph-list">',
            "\n".join(node_items),
            "</ol>",
            '<script type="application/json" id="raya-graph-data">',
            graph_payload,
            "</script>",
            "</main>",
            f'<script src="{html.escape(accessibility_js_href)}" defer></script>',
            f'<script src="{html.escape(graph_js_href)}" defer></script>',
            "</body>",
            "</html>",
            "",
        ]
    )


def _browser_graph_payload(graph_index: dict[str, Any]) -> dict[str, Any]:
    return {
        **graph_index,
        "nodes": [
            {
                **node,
                "url": _relative_href(STATIC_GRAPH_PATH.as_posix(), node["url"]),
            }
            for node in graph_index["nodes"]
        ],
        "backlinks": {
            page_id: [
                {
                    **backlink,
                    "url": _relative_href(STATIC_GRAPH_PATH.as_posix(), backlink["url"]),
                }
                for backlink in backlinks
            ]
            for page_id, backlinks in graph_index["backlinks"].items()
        },
    }


def _write_search_surface(
    *,
    site_dir: Path,
    content_model: ContentModel,
    course_title: str,
    language: str,
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
    skin_context: SkinContext,
) -> str:
    stylesheet_href = _relative_href(STATIC_SEARCH_PATH.as_posix(), RENDER_STYLESHEET_PATH)
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
        f"{ACCESSIBILITY_RESOURCE_PATH}/{OPEN_DYSLEXIC_JS_NAME}",
    )
    search_js_href = _relative_href(
        STATIC_SEARCH_PATH.as_posix(),
        Path(SEARCH_RESOURCE_PATH) / SEARCH_SCRIPT_NAME,
    )
    root_skin = skin_id_for_source_path(content_model.pages[0].source_path, skin_context)
    browser_search = _browser_search_payload(content_model)
    search_payload = _json_script_text(browser_search)
    result_items = []
    for page in browser_search["pages"]:
        tags = ", ".join(page["tags"])
        meta_parts = [page["status"], page["hierarchy_label"], tags]
        meta = " | ".join(part for part in meta_parts if part)
        result_items.append(
            f'<li data-raya-search-result="{html.escape(page["id"], quote=True)}">'
            f'<a href="{html.escape(page["url"])}">{html.escape(page["title"])}</a>'
            f'<p>{html.escape(page["summary"])}</p>'
            f'<p class="raya-search-result-meta">{html.escape(meta)}</p>'
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
            (
                '<main id="raya-search-main" class="raya-search-page" '
                'data-raya-search-page tabindex="-1">'
            ),
            '<header class="raya-search-header">',
            f'<p class="raya-course-title">{html.escape(course_title)}</p>',
            '<a class="raya-graph-back-link" href="../../index.html">Back to course</a>',
            "<h1>Course Search</h1>",
            "<p>Search page titles, summaries, stable IDs, tags, and status metadata.</p>",
            "</header>",
            '<section class="raya-search-controls" aria-label="Course search controls">',
            '<label for="raya-search-input">Search</label>',
            '<input id="raya-search-input" type="search" autocomplete="off">',
            '<p id="raya-search-status" class="raya-search-status" aria-live="polite"></p>',
            "</section>",
            '<p id="raya-search-empty" class="raya-search-empty" hidden>No matching pages.</p>',
            '<ol id="raya-search-results" class="raya-search-results">',
            "\n".join(result_items),
            "</ol>",
            '<script type="application/json" id="raya-search-data">',
            search_payload,
            "</script>",
            "</main>",
            f'<script src="{html.escape(accessibility_js_href)}" defer></script>',
            f'<script src="{html.escape(search_js_href)}" defer></script>',
            "</body>",
            "</html>",
            "",
        ]
    )


def _browser_search_payload(content_model: ContentModel) -> dict[str, Any]:
    return {
        "version": 1,
        "pages": [
            {
                "id": page.id,
                "title": page.title,
                "nav_title": page.nav_title,
                "summary": page.summary,
                "status": page.status,
                "tags": list(page.tags),
                "hierarchy_label": page.hierarchy_label,
                "url": _relative_href(STATIC_SEARCH_PATH.as_posix(), page.output_path),
            }
            for page in content_model.pages
        ],
    }


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


def _official_counts(official_objects: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for item in official_objects:
        scope = item.get("scope")
        quantum = scope.get("quantum") if isinstance(scope, dict) else None
        object_type = item.get("type")
        if isinstance(quantum, str) and isinstance(object_type, str):
            counts[quantum][object_type] += 1
    return {quantum: dict(values) for quantum, values in counts.items()}


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
    accessibility = open_dyslexic_resources()
    accessibility_dir = site_dir / ACCESSIBILITY_RESOURCE_PATH
    accessibility_dir.mkdir(parents=True, exist_ok=True)
    css_path = accessibility_dir / OPEN_DYSLEXIC_CSS_NAME
    js_path = accessibility_dir / OPEN_DYSLEXIC_JS_NAME
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
    js_path.write_text(accessibility.javascript, encoding="utf-8")
    with resources.as_file(accessibility.source_font) as source_font:
        shutil.copy2(source_font, font_path)
    report.wrote_output(css_path)
    report.wrote_output(js_path)
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


def _write_search_resources(site_dir: Path, report: ValidationReport) -> None:
    resources = search_resources()
    search_dir = site_dir / SEARCH_RESOURCE_PATH
    search_dir.mkdir(parents=True, exist_ok=True)
    report.wrote_output(search_dir)
    script_path = search_dir / SEARCH_SCRIPT_NAME
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
        name
        for name in required_fonts
        if not (MATH_FONT_SOURCE_DIR / name).is_file()
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
        validate_references_index(artifact_dir / "data" / "references.json"),
        validate_reviewed_outputs_index(artifact_dir / "data" / "reviewed-outputs.json"),
        validate_numbered_objects_index(artifact_dir / "data" / "numbered-objects.json"),
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
