from __future__ import annotations

import hashlib
import html
import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from raya_schema import (
    ValidationReport,
    validate_artifact_manifest,
    validate_course,
    validate_links_index,
    validate_official_index,
    validate_pages_index,
    validate_quanta_index,
)
from raya_schema.links import (
    classify_markdown_target,
    extract_markdown_links,
    markdown_link_fragment,
    markdown_link_path,
    resolve_local_markdown_target,
)
from raya_schema.yaml_io import load_yaml_file, parse_frontmatter


ARTIFACT_VERSION = "0.1"
SOURCE_SCHEMA_VERSION = "0.1"
SUPPORTED_OFFICIAL_SUFFIXES = {".yaml", ".yml", ".json"}
STATIC_RESOURCE_DIR = "_raya"
STATIC_ASSETS_PATH = Path(STATIC_RESOURCE_DIR) / "assets"


@dataclass(frozen=True)
class SourcePage:
    source_path: Path
    rel_path: str
    output_path: str
    title: str
    quantum_id: str
    quantum_type: str
    parent: str | None
    body: str


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
    content_dir = (root / str(config["content"])).resolve()
    artifact_dir = (root / str(config["artifact"])).resolve()
    assets_dir = (root / str(config.get("assets", "assets"))).resolve()
    official_dir = root / "official"

    if _is_unsafe_artifact_dir(root, content_dir, assets_dir, official_dir, artifact_dir):
        report.add_error(
            "Artifact directory overlaps source course truth",
            path=artifact_dir,
            field="artifact",
            next_action="Use a generated output directory such as artifact or _site",
        )
        return report

    pages = _discover_pages(content_dir, course_id, report)
    official_objects = _discover_official_objects(official_dir, report)
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

    pages_by_source = {page.source_path.resolve(): page for page in pages}
    pages_by_quantum = {page.quantum_id: page for page in pages}

    for page in pages:
        output_file = site_dir / page.output_path
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(
            _render_page(
                page=page,
                pages=pages,
                pages_by_source=pages_by_source,
                course_root=root,
                assets_dir=assets_dir,
                course_title=str(config["title"]),
                language=str(config["language"]),
            ),
            encoding="utf-8",
        )
        report.wrote_output(output_file)

    copied_assets = _copy_assets(assets_dir, artifact_assets_dir, report)
    copied_site_assets = _copy_assets(assets_dir, site_assets_dir, report)

    pages_index = _pages_index(course_id, pages)
    quanta_index = _quanta_index(course_id, pages)
    links_index = _links_index(course_id, pages, pages_by_quantum, pages_by_source, root)
    official_index = _official_index(course_id, official_objects)

    _write_json(data_dir / "pages.json", pages_index, report)
    _write_json(data_dir / "quanta.json", quanta_index, report)
    _write_json(data_dir / "links.json", links_index, report)
    _write_json(data_dir / "official.json", official_index, report)

    manifest = {
        "artifact_version": ARTIFACT_VERSION,
        "course_id": course_id,
        "course_version_id": _source_hash(root, content_dir, official_dir, assets_dir),
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "static_site_root": "site",
        "data": {
            "pages": "data/pages.json",
            "quanta": "data/quanta.json",
            "links": "data/links.json",
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
        if copied_assets:
            report.add_info(
                f"Copied {copied_assets} asset file(s)",
                path=artifact_assets_dir,
            )
        if copied_site_assets:
            report.add_info(
                f"Copied {copied_site_assets} browser asset file(s)",
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


def _discover_pages(
    content_dir: Path,
    course_id: str,
    report: ValidationReport,
) -> list[SourcePage]:
    pages: list[SourcePage] = []
    for source_path in sorted(content_dir.rglob("*.md")):
        report.read_file(source_path)
        rel_path = source_path.relative_to(content_dir).as_posix()
        try:
            frontmatter = parse_frontmatter(source_path)
        except Exception as exc:
            report.add_error(
                f"Unreadable Markdown frontmatter: {exc}",
                path=source_path,
                next_action="Fix frontmatter syntax",
            )
            continue

        body = _markdown_body(source_path)
        quantum = frontmatter.get("quantum")
        quantum_data = quantum if isinstance(quantum, dict) else {}
        quantum_id = str(quantum_data.get("id") or f"{course_id}:{rel_path}")
        title = str(frontmatter.get("title") or _first_heading(body) or source_path.stem)
        pages.append(
            SourcePage(
                source_path=source_path,
                rel_path=rel_path,
                output_path=_output_path_for(rel_path),
                title=title,
                quantum_id=quantum_id,
                quantum_type=str(quantum_data.get("type") or "page"),
                parent=(
                    str(quantum_data["parent"])
                    if quantum_data.get("parent") is not None
                    else None
                ),
                body=body,
            )
        )
    return pages


def _discover_official_objects(
    official_dir: Path,
    report: ValidationReport,
) -> list[dict[str, Any]]:
    if not official_dir.exists():
        return []

    objects: list[dict[str, Any]] = []
    for object_path in sorted(
        path
        for path in official_dir.rglob("*")
        if path.suffix.lower() in SUPPORTED_OFFICIAL_SUFFIXES
    ):
        report.read_file(object_path)
        try:
            data = load_yaml_file(object_path)
        except Exception as exc:
            report.add_error(
                f"Could not read official learning object: {exc}",
                path=object_path,
                next_action="Fix official learning object syntax",
            )
            continue
        if not isinstance(data, dict):
            report.add_error(
                "Official learning object must be a mapping",
                path=object_path,
                next_action="Use key/value object fields",
            )
            continue
        exported = {
            "id": data.get("id"),
            "type": data.get("type"),
            "authority": data.get("authority"),
            "scope": data.get("scope", {}),
            "content": data.get("content", {}),
            "source_path": object_path.relative_to(official_dir.parent).as_posix(),
        }
        if "retrieval" in data:
            exported["retrieval"] = data["retrieval"]
        objects.append(exported)
    return objects


def _is_unsafe_artifact_dir(
    root: Path,
    content_dir: Path,
    assets_dir: Path,
    official_dir: Path,
    artifact_dir: Path,
) -> bool:
    source_roots = {root, content_dir}
    if assets_dir.exists():
        source_roots.add(assets_dir)
    if official_dir.exists():
        source_roots.add(official_dir.resolve())
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


def _copy_assets(source_assets: Path, target_assets: Path, report: ValidationReport) -> int:
    if not source_assets.exists():
        return 0

    copied = 0
    for source_path in sorted(path for path in source_assets.rglob("*") if path.is_file()):
        report.read_file(source_path)
        rel_path = source_path.relative_to(source_assets)
        target_path = target_assets / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        report.wrote_output(target_path)
        copied += 1
    return copied


def _render_page(
    *,
    page: SourcePage,
    pages: list[SourcePage],
    pages_by_source: dict[Path, SourcePage],
    course_root: Path,
    assets_dir: Path,
    course_title: str,
    language: str,
) -> str:
    nav_items = []
    for target in pages:
        href = _relative_href(page.output_path, target.output_path)
        label = html.escape(target.title)
        current = ' aria-current="page"' if target.output_path == page.output_path else ""
        nav_items.append(f'<a href="{html.escape(href)}"{current}>{label}</a>')

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
            "</header>",
            "<main>",
            _render_markdown(page.body, page, pages_by_source, course_root, assets_dir),
            "</main>",
            "</body>",
            "</html>",
            "",
        ]
    )


def _render_markdown(
    body: str,
    page: SourcePage,
    pages_by_source: dict[Path, SourcePage],
    course_root: Path,
    assets_dir: Path,
) -> str:
    output: list[str] = []
    paragraph: list[str] = []
    in_list = False

    def flush_paragraph() -> None:
        if paragraph:
            output.append(
                f"<p>{_render_inline(' '.join(paragraph), page, pages_by_source, course_root, assets_dir)}</p>"
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

        heading_level = _heading_level(stripped)
        if heading_level:
            flush_paragraph()
            close_list()
            heading_text = stripped[heading_level + 1 :].strip()
            output.append(
                f"<h{heading_level}>{_render_inline(heading_text, page, pages_by_source, course_root, assets_dir)}</h{heading_level}>"
            )
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            if not in_list:
                output.append("<ul>")
                in_list = True
            output.append(
                f"<li>{_render_inline(stripped[2:].strip(), page, pages_by_source, course_root, assets_dir)}</li>"
            )
            continue

        paragraph.append(stripped)

    flush_paragraph()
    close_list()
    return "\n".join(output)


def _render_inline(
    text: str,
    page: SourcePage,
    pages_by_source: dict[Path, SourcePage],
    course_root: Path,
    assets_dir: Path,
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
            course_root,
            assets_dir,
        )
        rendered.append(f'<a href="{html.escape(href)}">{label}</a>')
        cursor = link.end
    rendered.append(html.escape(text[cursor:]))
    return "".join(rendered)


def _resolve_markdown_href(
    page: SourcePage,
    href: str,
    pages_by_source: dict[Path, SourcePage],
    course_root: Path,
    assets_dir: Path,
) -> str:
    kind = classify_markdown_target(href)
    if kind == "ignored":
        return href
    fragment = markdown_link_fragment(href)
    if kind == "content":
        target_page = _target_content_page(page, href, pages_by_source, course_root)
        if target_page is not None:
            return _relative_href(page.output_path, target_page.output_path) + fragment
    if kind == "asset":
        target_href = _target_asset_href(page, href, course_root, assets_dir)
        if target_href is not None:
            return target_href + fragment
    return href


def _pages_index(course_id: str, pages: list[SourcePage]) -> dict[str, Any]:
    return {
        "course_id": course_id,
        "pages": [
            {
                "path": page.rel_path,
                "url": page.output_path,
                "title": page.title,
                "quantum_id": page.quantum_id,
            }
            for page in pages
        ],
    }


def _quanta_index(course_id: str, pages: list[SourcePage]) -> dict[str, Any]:
    quanta = []
    for page in pages:
        item = {
            "id": page.quantum_id,
            "type": page.quantum_type,
            "path": page.rel_path,
        }
        if page.parent is not None:
            item["parent"] = page.parent
        quanta.append(item)
    return {"course_id": course_id, "quanta": quanta}


def _links_index(
    course_id: str,
    pages: list[SourcePage],
    pages_by_quantum: dict[str, SourcePage],
    pages_by_source: dict[Path, SourcePage],
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

    for page in pages:
        if page.parent and page.parent in pages_by_quantum:
            add_link(page.parent, page.quantum_id, "navigation")
            add_link(page.quantum_id, page.parent, "parent")
        for link in extract_markdown_links(page.body):
            if classify_markdown_target(link.target) != "content":
                continue
            target_page = _target_content_page(
                page,
                link.target,
                pages_by_source,
                course_root,
            )
            if target_page is not None:
                add_link(page.quantum_id, target_page.quantum_id, "content")
    return {"course_id": course_id, "links": links}


def _target_content_page(
    page: SourcePage,
    target: str,
    pages_by_source: dict[Path, SourcePage],
    course_root: Path,
) -> SourcePage | None:
    target_path = resolve_local_markdown_target(
        source_path=page.source_path,
        course_root=course_root,
        target_path=markdown_link_path(target),
    )
    return pages_by_source.get(target_path)


def _target_asset_href(
    page: SourcePage,
    target: str,
    course_root: Path,
    assets_dir: Path,
) -> str | None:
    target_path = resolve_local_markdown_target(
        source_path=page.source_path,
        course_root=course_root,
        target_path=markdown_link_path(target),
    )
    try:
        rel_asset_path = target_path.relative_to(assets_dir)
    except ValueError:
        return None
    static_asset_path = (STATIC_ASSETS_PATH / rel_asset_path).as_posix()
    return _relative_href(page.output_path, static_asset_path)


def _official_index(
    course_id: str,
    official_objects: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "course_id": course_id,
        "objects": official_objects,
    }


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
    content_dir: Path,
    official_dir: Path,
    assets_dir: Path,
) -> str:
    digest = hashlib.sha256()
    source_files = [root / "raya.yaml"]
    for directory in (content_dir, official_dir, assets_dir):
        if directory.exists():
            source_files.extend(path for path in directory.rglob("*") if path.is_file())
    for path in sorted(source_files):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _markdown_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return text
    marker = "\n---"
    end = text.find(marker, 4)
    if end == -1:
        return text
    body = text[end + len(marker) :]
    return body[1:] if body.startswith("\n") else body


def _first_heading(body: str) -> str | None:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None


def _heading_level(stripped: str) -> int | None:
    if not stripped.startswith("#"):
        return None
    hashes = len(stripped) - len(stripped.lstrip("#"))
    if 1 <= hashes <= 6 and len(stripped) > hashes and stripped[hashes] == " ":
        return hashes
    return None


def _output_path_for(rel_path: str) -> str:
    path = Path(rel_path)
    if path.name in {"00_index.md", "index.md"}:
        if path.parent == Path("."):
            return "index.html"
        return (path.parent / "index.html").as_posix()
    return path.with_suffix(".html").as_posix()


def _relative_href(from_output: str, to_output: str) -> str:
    from_dir = Path(from_output).parent
    rel = os.path.relpath(to_output, start=from_dir if str(from_dir) != "." else ".")
    return Path(rel).as_posix()
