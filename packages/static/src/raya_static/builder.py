from __future__ import annotations

import hashlib
import html
import json
import os
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from raya_schema import (
    ValidationReport,
    validate_artifact_manifest,
    validate_indices_index,
    validate_course,
    validate_links_index,
    validate_navigation_index,
    validate_official_index,
    validate_pages_index,
    validate_quanta_index,
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
from raya_schema.official import discover_official_objects
from raya_schema.yaml_io import load_yaml_file


ARTIFACT_VERSION = "0.1"
SOURCE_SCHEMA_VERSION = "0.1"
STATIC_RESOURCE_DIR = "_raya"
STATIC_ASSETS_PATH = Path(STATIC_RESOURCE_DIR) / "assets"


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
    source_root = resolve_course_source_root(root=root, config=config, report=report)
    if source_root is None:
        return report
    source_dir = source_root
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

    _replace_generated_output(artifact_dir, report)

    site_dir = artifact_dir / "site"
    data_dir = artifact_dir / "data"
    artifact_assets_dir = artifact_dir / "assets"
    site_assets_dir = site_dir / STATIC_ASSETS_PATH
    for directory in (site_dir, data_dir, artifact_assets_dir, site_assets_dir):
        directory.mkdir(parents=True, exist_ok=True)
        report.wrote_output(directory)

    pages_by_source = content_model.pages_by_source
    pages_by_reference = {
        **content_model.pages_by_id,
        **content_model.pages_by_alias,
    }
    official_counts = _official_counts(official_objects)

    for page in pages:
        output_file = site_dir / page.output_path
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(
            _render_page(
                page=page,
                content_model=content_model,
                pages_by_source=pages_by_source,
                pages_by_reference=pages_by_reference,
                course_root=root,
                source_dir=source_dir,
                course_title=str(config["title"]),
                language=str(config["language"]),
                official_counts=official_counts,
            ),
            encoding="utf-8",
        )
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

    pages_index = _pages_index(course_id, pages)
    quanta_index = _quanta_index(course_id, pages)
    links_index = _links_index(
        course_id,
        content_model,
        pages_by_reference,
        pages_by_source,
        root,
    )
    navigation_index = _navigation_index(course_id, content_model)
    indices_index = _indices_index(course_id, content_model, official_counts)
    official_index = _official_index(course_id, official_objects)

    _write_json(data_dir / "pages.json", pages_index, report)
    _write_json(data_dir / "quanta.json", quanta_index, report)
    _write_json(data_dir / "links.json", links_index, report)
    _write_json(data_dir / "navigation.json", navigation_index, report)
    _write_json(data_dir / "indices.json", indices_index, report)
    _write_json(data_dir / "official.json", official_index, report)

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
            "navigation": "data/navigation.json",
            "indices": "data/indices.json",
            "official": "data/official.json",
        },
        "assets": "assets",
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
    for relative in ("site", "data", "assets"):
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


def _render_page(
    *,
    page: ContentPage,
    content_model: ContentModel,
    pages_by_source: dict[Path, ContentPage],
    pages_by_reference: dict[str, ContentPage],
    course_root: Path,
    source_dir: Path,
    course_title: str,
    language: str,
    official_counts: dict[str, dict[str, int]],
) -> str:
    nav_items = []
    for target in content_model.pages:
        href = _relative_href(page.output_path, target.output_path)
        label = html.escape(_navigation_label(target))
        current = ' aria-current="page"' if target.output_path == page.output_path else ""
        nav_items.append(f'<a href="{html.escape(href)}"{current}>{label}</a>')
    breadcrumbs = _render_breadcrumbs(page, content_model)
    sequence_nav = _render_sequence_nav(page, content_model)
    generated_index = _render_generated_index(
        page,
        content_model,
        official_counts,
    )

    return "\n".join(
        [
            "<!doctype html>",
            f'<html lang="{html.escape(language)}">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{html.escape(page.title)} - {html.escape(course_title)}</title>",
            "</head>",
            "<body>",
            "<header>",
            f"<p>{html.escape(course_title)}</p>",
            '<nav aria-label="Course pages">',
            "\n".join(nav_items),
            "</nav>",
            breadcrumbs,
            "</header>",
            "<main>",
            _render_markdown(
                page.body,
                page,
                pages_by_source,
                pages_by_reference,
                course_root,
                source_dir,
                generated_index,
            ),
            "</main>",
            sequence_nav,
            "</body>",
            "</html>",
            "",
        ]
    )


def _render_markdown(
    body: str,
    page: ContentPage,
    pages_by_source: dict[Path, ContentPage],
    pages_by_reference: dict[str, ContentPage],
    course_root: Path,
    source_dir: Path,
    generated_index: str = "",
) -> str:
    output: list[str] = []
    paragraph: list[str] = []
    in_list = False
    marker_used = False

    def flush_paragraph() -> None:
        if paragraph:
            output.append(
                f"<p>{_render_inline(' '.join(paragraph), page, pages_by_source, pages_by_reference, course_root, source_dir)}</p>"
            )
            paragraph.clear()

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            output.append("</ul>")
            in_list = False

    for raw_line in body.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            close_list()
            continue
        if stripped == "<!-- raya:index -->":
            flush_paragraph()
            close_list()
            if generated_index:
                output.append(generated_index)
            marker_used = True
            continue

        heading_level = _heading_level(stripped)
        if heading_level:
            flush_paragraph()
            close_list()
            heading_text = stripped[heading_level + 1 :].strip()
            output.append(
                f"<h{heading_level}>{_render_inline(heading_text, page, pages_by_source, pages_by_reference, course_root, source_dir)}</h{heading_level}>"
            )
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            if not in_list:
                output.append("<ul>")
                in_list = True
            output.append(
                f"<li>{_render_inline(stripped[2:].strip(), page, pages_by_source, pages_by_reference, course_root, source_dir)}</li>"
            )
            continue

        paragraph.append(stripped)

    flush_paragraph()
    close_list()
    if generated_index and not marker_used:
        output.append(generated_index)
    return "\n".join(output)


def _render_inline(
    text: str,
    page: ContentPage,
    pages_by_source: dict[Path, ContentPage],
    pages_by_reference: dict[str, ContentPage],
    course_root: Path,
    source_dir: Path,
) -> str:
    rendered: list[str] = []
    cursor = 0
    for link in extract_markdown_links(text):
        rendered.append(html.escape(text[cursor : link.start]))
        label = html.escape(link.label)
        href = _resolve_markdown_href(
            page,
            link.target,
            pages_by_source,
            pages_by_reference,
            course_root,
            source_dir,
        )
        rendered.append(f'<a href="{html.escape(href)}">{label}</a>')
        cursor = link.end
    rendered.append(html.escape(text[cursor:]))
    return "".join(rendered)


def _resolve_markdown_href(
    page: ContentPage,
    href: str,
    pages_by_source: dict[Path, ContentPage],
    pages_by_reference: dict[str, ContentPage],
    course_root: Path,
    source_dir: Path,
) -> str:
    kind = classify_markdown_target(href)
    if kind == "ignored":
        return href
    fragment = markdown_link_fragment(href)
    if kind == "stable":
        target_page = pages_by_reference.get(stable_markdown_id(href))
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
    return href


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


def _render_sequence_nav(page: ContentPage, content_model: ContentModel) -> str:
    flat_pages = _flatten_navigation(content_model)
    try:
        index = flat_pages.index(page.id)
    except ValueError:
        return ""
    links: list[str] = []
    if index > 0:
        previous = content_model.pages_by_id[flat_pages[index - 1]]
        links.append(
            f'<a rel="prev" href="{html.escape(_relative_href(page.output_path, previous.output_path))}">Previous: {html.escape(previous.nav_title)}</a>'
        )
    if index < len(flat_pages) - 1:
        next_page = content_model.pages_by_id[flat_pages[index + 1]]
        links.append(
            f'<a rel="next" href="{html.escape(_relative_href(page.output_path, next_page.output_path))}">Next: {html.escape(next_page.nav_title)}</a>'
        )
    if not links:
        return ""
    return '<nav aria-label="Previous and next">' + " ".join(links) + "</nav>"


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


def _validate_generated_artifact(artifact_dir: Path, report: ValidationReport) -> None:
    for generated_report in (
        validate_artifact_manifest(artifact_dir / "manifest.json"),
        validate_pages_index(artifact_dir / "data" / "pages.json"),
        validate_quanta_index(artifact_dir / "data" / "quanta.json"),
        validate_links_index(artifact_dir / "data" / "links.json"),
        validate_navigation_index(artifact_dir / "data" / "navigation.json"),
        validate_indices_index(artifact_dir / "data" / "indices.json"),
        validate_official_index(artifact_dir / "data" / "official.json"),
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
    if source_dir.exists():
        source_files.extend(path for path in source_dir.rglob("*") if path.is_file())
    for path in sorted(source_files):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _heading_level(stripped: str) -> int | None:
    if not stripped.startswith("#"):
        return None
    hashes = len(stripped) - len(stripped.lstrip("#"))
    if 1 <= hashes <= 6 and len(stripped) > hashes and stripped[hashes] == " ":
        return hashes
    return None


def _relative_href(from_output: str, to_output: str) -> str:
    from_dir = Path(from_output).parent
    rel = os.path.relpath(to_output, start=from_dir if str(from_dir) != "." else ".")
    return Path(rel).as_posix()
