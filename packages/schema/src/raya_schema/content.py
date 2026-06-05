from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from raya_schema.diagnostics import ValidationReport
from raya_schema.yaml_io import parse_frontmatter


PRIVATE_DIR_NAMES = {
    "drafts",
    "_drafts",
    "_partials",
    "_official",
    "_assets",
    "code",
    "notebooks",
    "runtime",
}
SUPPORT_OWNER_DIR_NAMES = {"_official", "_assets", "code", "notebooks"}
SUPPORTED_STATUSES = {"draft", "ready", "archived", "deprecated"}
DEFAULT_HIERARCHY = (
    {"key": "unit", "label": "Unit"},
    {"key": "topic", "label": "Topic"},
    {"key": "lesson", "label": "Lesson"},
)


@dataclass(frozen=True)
class OrderedName:
    sequence: str
    order: int
    label: str
    raw_prefix: str
    slug: str
    prefix_width: int


@dataclass(frozen=True)
class HierarchyConfig:
    levels: tuple[dict[str, str], ...] = DEFAULT_HIERARCHY
    appendix_label: str = "Appendix"


@dataclass(frozen=True)
class ContentPage:
    source_path: Path
    rel_path: str
    output_path: str
    slug_parts: tuple[str, ...]
    id: str
    aliases: tuple[str, ...]
    title: str
    nav_title: str
    summary: str
    status: str
    estimated_time: str | None
    tags: tuple[str, ...]
    prerequisites: tuple[str, ...]
    body: str
    is_index: bool
    sequence: str
    order: int
    order_label: str
    display_label: str
    hierarchy_key: str
    hierarchy_label: str
    parent_id: str | None


@dataclass
class ContentModel:
    pages: list[ContentPage]
    hierarchy: HierarchyConfig
    root_id: str | None
    children_by_parent: dict[str | None, list[str]] = field(default_factory=dict)
    pages_by_id: dict[str, ContentPage] = field(default_factory=dict)
    pages_by_alias: dict[str, ContentPage] = field(default_factory=dict)
    pages_by_source: dict[Path, ContentPage] = field(default_factory=dict)


def resolve_course_content(
    *,
    course_root: Path,
    content_dir: Path,
    course_id: str,
    config: dict[str, Any],
    report: ValidationReport,
) -> ContentModel:
    hierarchy = hierarchy_from_config(config, report=report, path=course_root / "raya.yaml")
    markdown_files = sorted(content_dir.rglob("*.md"))
    parsed_pages: list[ContentPage] = []
    index_by_dir: dict[Path, ContentPage] = {}
    candidate_children: dict[Path, list[tuple[Path, OrderedName]]] = {}
    directory_candidates: dict[Path, OrderedName] = {}
    page_candidates: dict[Path, OrderedName] = {}
    support_owner_dirs = _support_owner_dirs(content_dir)

    for source_path in markdown_files:
        report.read_file(source_path)
        rel_path_obj = source_path.relative_to(content_dir)
        rel_path = rel_path_obj.as_posix()
        if _is_private_path(rel_path_obj.parts):
            continue

        invalid_parent = _validate_ordered_parent_dirs(
            rel_path_obj=rel_path_obj,
            content_dir=content_dir,
            source_path=source_path,
            report=report,
            directory_candidates=directory_candidates,
            candidate_children=candidate_children,
        )
        ordered_file = parse_ordered_name(source_path.stem)
        if ordered_file is None:
            report.add_error(
                "Unordered published content file",
                path=source_path,
                next_action="Add an order prefix such as 1_ or move the file under drafts/",
            )
            continue
        if ordered_file.sequence != "main" and ordered_file.slug == "index":
            report.add_error(
                "Appendix index file must use a numeric zero index name",
                path=source_path,
                next_action="Use 0_index.md inside appendix directories",
            )
            continue
        if ordered_file.order == 0 and ordered_file.slug != "index":
            report.add_error(
                "Zero-order content files must be index pages",
                path=source_path,
                next_action="Rename the file to 0_index.md or use a positive order prefix",
            )
            continue
        if invalid_parent:
            continue

        try:
            frontmatter = parse_frontmatter(source_path)
        except Exception as exc:
            report.add_error(
                f"Unreadable Markdown frontmatter: {exc}",
                path=source_path,
                next_action="Fix frontmatter syntax",
            )
            continue

        body = markdown_body(source_path)
        metadata = _metadata_from_frontmatter(
            path=source_path,
            frontmatter=frontmatter,
            body=body,
            fallback_title=_title_from_slug(ordered_file.slug),
            report=report,
        )
        if metadata is None:
            continue

        slug_parts = _slug_parts(rel_path_obj, ordered_file)
        page = ContentPage(
            source_path=source_path,
            rel_path=rel_path,
            output_path=output_path_for_slug_parts(slug_parts),
            slug_parts=slug_parts,
            id=metadata["id"],
            aliases=tuple(metadata["aliases"]),
            title=metadata["title"],
            nav_title=metadata["nav_title"],
            summary=metadata["summary"],
            status=metadata["status"],
            estimated_time=metadata["estimated_time"],
            tags=tuple(metadata["tags"]),
            prerequisites=tuple(metadata["prerequisites"]),
            body=body,
            is_index=ordered_file.order == 0 and ordered_file.slug == "index",
            sequence=ordered_file.sequence,
            order=ordered_file.order,
            order_label=_display_label(rel_path_obj, ordered_file),
            display_label=_display_label(rel_path_obj, ordered_file),
            hierarchy_key=_hierarchy_key(rel_path_obj, slug_parts, hierarchy, ordered_file),
            hierarchy_label=_hierarchy_label(
                rel_path_obj,
                slug_parts,
                hierarchy,
                ordered_file,
            ),
            parent_id=None,
        )
        parsed_pages.append(page)

        if page.is_index:
            index_by_dir[source_path.parent] = page
        else:
            page_candidates[source_path] = ordered_file
            candidate_children.setdefault(source_path.parent, []).append(
                (source_path, ordered_file)
            )

    _validate_sibling_sets(candidate_children, report)
    _validate_section_landing_pages(directory_candidates, index_by_dir, report)
    _validate_support_owner_indexes(
        support_owner_dirs,
        content_dir,
        index_by_dir,
        report,
    )
    _validate_slug_collisions(candidate_children, report)

    pages_with_parents = _attach_parents(parsed_pages, content_dir, index_by_dir, report)
    model = _build_content_model(pages_with_parents, hierarchy, report)
    _validate_prerequisites(model, report)
    return model


def parse_ordered_name(name: str) -> OrderedName | None:
    match = re.fullmatch(r"([0-9]+)_(.+)", name)
    if match:
        raw_prefix, slug = match.groups()
        return OrderedName(
            sequence="main",
            order=int(raw_prefix),
            label=str(int(raw_prefix)),
            raw_prefix=raw_prefix,
            slug=_clean_slug(slug),
            prefix_width=len(raw_prefix),
        )

    match = re.fullmatch(r"([A-Z]+)_(.+)", name)
    if match:
        raw_prefix, slug = match.groups()
        return OrderedName(
            sequence="appendix",
            order=_appendix_order(raw_prefix),
            label=raw_prefix,
            raw_prefix=raw_prefix,
            slug=_clean_slug(slug),
            prefix_width=len(raw_prefix),
        )
    return None


def hierarchy_from_config(
    config: dict[str, Any],
    *,
    report: ValidationReport | None = None,
    path: Path | None = None,
) -> HierarchyConfig:
    raw_hierarchy = config.get("hierarchy")
    appendix_label = str(config.get("appendix_label") or "Appendix")
    if raw_hierarchy is None:
        return HierarchyConfig(appendix_label=appendix_label)
    if not isinstance(raw_hierarchy, dict):
        if report is not None:
            report.add_error(
                "Hierarchy configuration must be a mapping",
                path=path,
                field="hierarchy",
                next_action="Use hierarchy.levels with key/label entries",
            )
        return HierarchyConfig(appendix_label=appendix_label)
    raw_levels = raw_hierarchy.get("levels")
    if raw_levels is None:
        return HierarchyConfig(appendix_label=appendix_label)
    if not isinstance(raw_levels, list):
        if report is not None:
            report.add_error(
                "Hierarchy levels must be a list",
                path=path,
                field="hierarchy.levels",
                next_action="Use a list of key/label mappings",
            )
        return HierarchyConfig(appendix_label=appendix_label)

    levels: list[dict[str, str]] = []
    for index, raw_level in enumerate(raw_levels):
        if not isinstance(raw_level, dict):
            if report is not None:
                report.add_error(
                    "Hierarchy level must be a mapping",
                    path=path,
                    field=f"hierarchy.levels.{index}",
                    next_action="Use key and label fields",
                )
            continue
        key = raw_level.get("key")
        label = raw_level.get("label")
        if not isinstance(key, str) or not key or not isinstance(label, str) or not label:
            if report is not None:
                report.add_error(
                    "Hierarchy level requires key and label",
                    path=path,
                    field=f"hierarchy.levels.{index}",
                    next_action="Provide non-empty key and label strings",
                )
            continue
        levels.append({"key": key, "label": label})
    return HierarchyConfig(
        levels=tuple(levels) if levels else DEFAULT_HIERARCHY,
        appendix_label=appendix_label,
    )


def markdown_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return text
    marker = "\n---"
    end = text.find(marker, 4)
    if end == -1:
        return text
    body = text[end + len(marker) :]
    return body[1:] if body.startswith("\n") else body


def output_path_for_slug_parts(slug_parts: tuple[str, ...]) -> str:
    if not slug_parts:
        return "index.html"
    return (Path(*slug_parts) / "index.html").as_posix()


def _is_private_path(parts: tuple[str, ...]) -> bool:
    return any(part.startswith("_") or part in PRIVATE_DIR_NAMES for part in parts)


def _support_owner_dirs(content_dir: Path) -> set[Path]:
    owners: set[Path] = set()
    for support_dir in sorted(content_dir.rglob("*")):
        if not support_dir.is_dir() or support_dir.name not in SUPPORT_OWNER_DIR_NAMES:
            continue
        try:
            rel_parent = support_dir.parent.relative_to(content_dir)
        except ValueError:
            continue
        if _is_private_path(rel_parent.parts):
            continue
        owners.add(support_dir.parent)
    return owners


def _validate_ordered_parent_dirs(
    *,
    rel_path_obj: Path,
    content_dir: Path,
    source_path: Path,
    report: ValidationReport,
    directory_candidates: dict[Path, OrderedName],
    candidate_children: dict[Path, list[tuple[Path, OrderedName]]],
) -> bool:
    invalid_parent = False
    current = content_dir
    for raw_part in rel_path_obj.parts[:-1]:
        ordered = parse_ordered_name(raw_part)
        if ordered is None:
            report.add_error(
                "Unordered content directory",
                path=source_path,
                field=raw_part,
                next_action="Add an order prefix such as 1_ or move the directory under drafts/",
            )
            invalid_parent = True
            break
        directory = current / raw_part
        if directory not in directory_candidates:
            directory_candidates[directory] = ordered
            candidate_children.setdefault(current, []).append((directory, ordered))
        current = directory
    return invalid_parent


def _metadata_from_frontmatter(
    *,
    path: Path,
    frontmatter: dict[str, Any],
    body: str,
    fallback_title: str,
    report: ValidationReport,
) -> dict[str, Any] | None:
    metadata_id = frontmatter.get("id")
    if not isinstance(metadata_id, str) or not metadata_id.strip():
        report.add_error(
            "Rendered published page requires stable frontmatter id",
            path=path,
            field="id",
            next_action="Add a stable id that will survive renumbering and moves",
        )
        return None

    title = _string_field(frontmatter, "title", path, report)
    nav_title = _string_field(frontmatter, "nav_title", path, report, required=False)
    summary = _string_field(frontmatter, "summary", path, report, required=False)
    status = _string_field(frontmatter, "status", path, report, required=False) or "ready"
    estimated_time = _string_field(
        frontmatter,
        "estimated_time",
        path,
        report,
        required=False,
    )
    tags = _string_list_field(frontmatter, "tags", path, report)
    prerequisites = _string_list_field(frontmatter, "prerequisites", path, report)
    aliases = _string_list_field(frontmatter, "aliases", path, report)

    if status not in SUPPORTED_STATUSES:
        report.add_error(
            "Unsupported page status",
            path=path,
            field="status",
            next_action="Use draft, ready, archived, or deprecated",
        )
        return None

    resolved_title = title or first_heading(body) or fallback_title
    resolved_summary = summary or first_paragraph(body) or resolved_title
    return {
        "id": metadata_id.strip(),
        "title": resolved_title,
        "nav_title": nav_title or resolved_title,
        "summary": resolved_summary,
        "status": status,
        "estimated_time": estimated_time,
        "tags": tags,
        "prerequisites": prerequisites,
        "aliases": aliases,
    }


def _string_field(
    frontmatter: dict[str, Any],
    field: str,
    path: Path,
    report: ValidationReport,
    *,
    required: bool = False,
) -> str | None:
    value = frontmatter.get(field)
    if value is None:
        if required:
            report.add_error(
                "Missing required metadata field",
                path=path,
                field=field,
                next_action=f"Add {field} to the page frontmatter",
            )
        return None
    if not isinstance(value, str):
        report.add_error(
            "Metadata field must be a string",
            path=path,
            field=field,
            next_action=f"Use a string value for {field}",
        )
        return None
    return value.strip()


def _string_list_field(
    frontmatter: dict[str, Any],
    field: str,
    path: Path,
    report: ValidationReport,
) -> tuple[str, ...]:
    value = frontmatter.get(field)
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        report.add_error(
            "Metadata field must be a list of strings",
            path=path,
            field=field,
            next_action=f"Use a YAML list of string values for {field}",
        )
        return ()
    return tuple(item.strip() for item in value if item.strip())


def _slug_parts(rel_path_obj: Path, ordered_file: OrderedName) -> tuple[str, ...]:
    parts: list[str] = []
    for raw_part in rel_path_obj.parts[:-1]:
        ordered = parse_ordered_name(raw_part)
        if ordered is not None:
            parts.append(ordered.slug)
    if ordered_file.order != 0 or ordered_file.slug != "index":
        parts.append(ordered_file.slug)
    return tuple(parts)


def _validate_sibling_sets(
    candidate_children: dict[Path, list[tuple[Path, OrderedName]]],
    report: ValidationReport,
) -> None:
    for _parent, children in candidate_children.items():
        seen_main: dict[int, Path] = {}
        seen_appendix: dict[str, Path] = {}
        padded_widths: set[int] = set()
        main_children: list[tuple[Path, OrderedName]] = []
        for path, ordered in children:
            if ordered.sequence == "main":
                main_children.append((path, ordered))
                if ordered.order in seen_main:
                    report.add_error(
                        "Duplicate normalized order",
                        path=path,
                        field=ordered.raw_prefix,
                        next_action=f"Use a unique order; first seen in {seen_main[ordered.order]}",
                    )
                else:
                    seen_main[ordered.order] = path
                if ordered.raw_prefix.startswith("0") and ordered.order != 0:
                    padded_widths.add(ordered.prefix_width)
            else:
                if ordered.label in seen_appendix:
                    report.add_error(
                        "Duplicate appendix order",
                        path=path,
                        field=ordered.label,
                        next_action=f"Use a unique appendix label; first seen in {seen_appendix[ordered.label]}",
                    )
                else:
                    seen_appendix[ordered.label] = path

        if not padded_widths:
            continue
        if len(padded_widths) > 1:
            for path, ordered in main_children:
                if ordered.order != 0:
                    report.add_error(
                        "Mixed ordered prefix widths",
                        path=path,
                        field=ordered.raw_prefix,
                        next_action="Use one numeric prefix style among siblings",
                    )
            continue
        padded_width = next(iter(padded_widths))
        for path, ordered in main_children:
            if ordered.order != 0 and ordered.prefix_width != padded_width:
                report.add_error(
                    "Mixed ordered prefix widths",
                    path=path,
                    field=ordered.raw_prefix,
                    next_action="Use one numeric prefix style among siblings",
                )


def _validate_section_landing_pages(
    directory_candidates: dict[Path, OrderedName],
    index_by_dir: dict[Path, ContentPage],
    report: ValidationReport,
) -> None:
    for directory in sorted(directory_candidates):
        if directory not in index_by_dir:
            report.add_error(
                "Rendered section directory is missing an index page",
                path=directory,
                next_action="Add 0_index.md to the rendered directory",
            )


def _validate_support_owner_indexes(
    support_owner_dirs: set[Path],
    content_dir: Path,
    index_by_dir: dict[Path, ContentPage],
    report: ValidationReport,
) -> None:
    for owner_dir in sorted(support_owner_dirs):
        if owner_dir == content_dir:
            continue
        if owner_dir not in index_by_dir:
            report.add_error(
                "Learning quantum support directory requires a directory index page",
                path=owner_dir,
                next_action=(
                    "Represent the quantum as a directory with 0_index.md "
                    "before adding _official/, _assets/, code/, or notebooks/"
                ),
            )


def _validate_slug_collisions(
    candidate_children: dict[Path, list[tuple[Path, OrderedName]]],
    report: ValidationReport,
) -> None:
    for _parent, children in candidate_children.items():
        seen_slugs: dict[str, Path] = {}
        for path, ordered in children:
            if ordered.order == 0 and ordered.slug == "index":
                continue
            if ordered.slug in seen_slugs:
                report.add_error(
                    "Duplicate clean slug",
                    path=path,
                    field=ordered.slug,
                    next_action=f"Use a unique slug after the order prefix; first seen in {seen_slugs[ordered.slug]}",
                )
            else:
                seen_slugs[ordered.slug] = path


def _attach_parents(
    pages: list[ContentPage],
    content_dir: Path,
    index_by_dir: dict[Path, ContentPage],
    report: ValidationReport,
) -> list[ContentPage]:
    attached: list[ContentPage] = []
    root_index = index_by_dir.get(content_dir)
    for page in pages:
        if page.source_path.parent == content_dir and page.is_index:
            parent_id = None
        elif page.is_index:
            parent_index = index_by_dir.get(page.source_path.parent.parent)
            parent_id = parent_index.id if parent_index is not None else None
        else:
            parent_index = index_by_dir.get(page.source_path.parent)
            if parent_index is None and root_index is not None:
                report.add_error(
                    "Rendered page is missing parent index",
                    path=page.source_path,
                    next_action="Add 0_index.md to the parent directory",
                )
            parent_id = parent_index.id if parent_index is not None else None
        attached.append(
            ContentPage(
                source_path=page.source_path,
                rel_path=page.rel_path,
                output_path=page.output_path,
                slug_parts=page.slug_parts,
                id=page.id,
                aliases=page.aliases,
                title=page.title,
                nav_title=page.nav_title,
                summary=page.summary,
                status=page.status,
                estimated_time=page.estimated_time,
                tags=page.tags,
                prerequisites=page.prerequisites,
                body=page.body,
                is_index=page.is_index,
                sequence=page.sequence,
                order=page.order,
                order_label=page.order_label,
                display_label=page.display_label,
                hierarchy_key=page.hierarchy_key,
                hierarchy_label=page.hierarchy_label,
                parent_id=parent_id,
            )
        )
    return attached


def _build_content_model(
    pages: list[ContentPage],
    hierarchy: HierarchyConfig,
    report: ValidationReport,
) -> ContentModel:
    pages_by_id: dict[str, ContentPage] = {}
    pages_by_alias: dict[str, ContentPage] = {}
    pages_by_source: dict[Path, ContentPage] = {}
    children_by_parent: dict[str | None, list[str]] = {}
    root_id: str | None = None

    for page in _sorted_pages(pages):
        if page.id in pages_by_id:
            report.add_error(
                "Duplicate quantum ID",
                path=page.source_path,
                field="id",
                next_action=f"Use a unique ID; first seen in {pages_by_id[page.id].source_path}",
            )
        else:
            pages_by_id[page.id] = page
        if page.source_path.name.startswith("0_") or page.source_path.name.startswith("00_"):
            if page.parent_id is None:
                root_id = page.id
        pages_by_source[page.source_path.resolve()] = page
        children_by_parent.setdefault(page.parent_id, []).append(page.id)

    for page in _sorted_pages(pages):
        for alias in page.aliases:
            if alias in pages_by_id:
                report.add_error(
                    "Alias collides with page ID",
                    path=page.source_path,
                    field="aliases",
                    next_action=f"Use an alias that does not collide with existing page ID {alias}",
                )
            elif alias in pages_by_alias:
                report.add_error(
                    "Duplicate page alias",
                    path=page.source_path,
                    field="aliases",
                    next_action=f"Use a unique alias; first seen in {pages_by_alias[alias].source_path}",
                )
            else:
                pages_by_alias[alias] = page

    return ContentModel(
        pages=_sorted_pages(pages),
        hierarchy=hierarchy,
        root_id=root_id,
        children_by_parent=children_by_parent,
        pages_by_id=pages_by_id,
        pages_by_alias=pages_by_alias,
        pages_by_source=pages_by_source,
    )


def _validate_prerequisites(model: ContentModel, report: ValidationReport) -> None:
    known = set(model.pages_by_id) | set(model.pages_by_alias)
    for page in model.pages:
        for prerequisite in page.prerequisites:
            if prerequisite not in known:
                report.add_error(
                    "Page prerequisite references an unknown stable ID",
                    path=page.source_path,
                    field="prerequisites",
                    next_action="Use the id or alias of a rendered page",
                )


def _sorted_pages(pages: list[ContentPage]) -> list[ContentPage]:
    return sorted(
        pages,
        key=lambda page: (
            tuple(_sort_key_for_part(part) for part in page.source_path.parts),
            page.source_path.as_posix(),
        ),
    )


def _sort_key_for_part(part: str) -> tuple[int, int, str]:
    ordered = parse_ordered_name(Path(part).stem)
    if ordered is None:
        return (1, 0, part)
    if ordered.sequence == "main":
        return (0, ordered.order, ordered.slug)
    return (2, ordered.order, ordered.slug)


def _display_label(rel_path_obj: Path, ordered_file: OrderedName) -> str:
    labels: list[str] = []
    for raw_part in rel_path_obj.parts[:-1]:
        ordered = parse_ordered_name(raw_part)
        if ordered is not None:
            labels.append(ordered.label)
    if ordered_file.order != 0 or ordered_file.slug != "index":
        labels.append(ordered_file.label)
    return ".".join(labels)


def _hierarchy_key(
    rel_path_obj: Path,
    slug_parts: tuple[str, ...],
    hierarchy: HierarchyConfig,
    ordered_file: OrderedName,
) -> str:
    if _is_appendix_entry_page(rel_path_obj, ordered_file):
        return "appendix"
    depth = max(len(slug_parts), 1)
    index = min(depth - 1, len(hierarchy.levels) - 1)
    return hierarchy.levels[index]["key"]


def _hierarchy_label(
    rel_path_obj: Path,
    slug_parts: tuple[str, ...],
    hierarchy: HierarchyConfig,
    ordered_file: OrderedName,
) -> str:
    if _is_appendix_entry_page(rel_path_obj, ordered_file):
        return hierarchy.appendix_label
    depth = max(len(slug_parts), 1)
    index = min(depth - 1, len(hierarchy.levels) - 1)
    return hierarchy.levels[index]["label"]


def _is_appendix_entry_page(rel_path_obj: Path, ordered_file: OrderedName) -> bool:
    if ordered_file.sequence == "appendix":
        return True
    if ordered_file.order != 0 or ordered_file.slug != "index":
        return False
    if not rel_path_obj.parts[:-1]:
        return False
    parent_order = parse_ordered_name(rel_path_obj.parts[-2])
    return parent_order is not None and parent_order.sequence == "appendix"


def _appendix_order(label: str) -> int:
    order = 0
    for char in label:
        order = order * 26 + (ord(char) - ord("A") + 1)
    return order


def _clean_slug(value: str) -> str:
    slug = value.strip().lower()
    slug = slug.replace("_", "-")
    slug = re.sub(r"[^a-z0-9._-]+", "-", slug)
    slug = slug.strip(".-_")
    return slug or "page"


def _title_from_slug(slug: str) -> str:
    return " ".join(part.capitalize() for part in re.split(r"[-_]+", slug) if part) or "Page"


def first_heading(body: str) -> str | None:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None


def first_paragraph(body: str) -> str | None:
    paragraph: list[str] = []
    for raw_line in body.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            if paragraph:
                break
            continue
        if stripped.startswith("#") or stripped.startswith("<!--"):
            continue
        paragraph.append(stripped)
    return " ".join(paragraph) if paragraph else None
