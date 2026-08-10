from __future__ import annotations

import re
from datetime import date, time
from pathlib import Path
from typing import Any

from jsonschema import ValidationError

from raya_schema.content import ContentModel, parse_ordered_name
from raya_schema.diagnostics import ValidationReport
from raya_schema.schema_loader import validator_for
from raya_schema.yaml_io import load_yaml_file


CALENDAR_KINDS = frozenset({"session", "holiday", "milestone", "cancellation"})
TASK_FAMILY_TYPES = frozenset({"assignment", "exam", "project", "task"})
_CIVIL_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_LOCAL_TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")
_EVENT_FIELDS = (
    "id",
    "kind",
    "date",
    "start_time",
    "end_time",
    "title",
    "summary",
    "page",
)


def discover_calendar_documents(
    *,
    course_root: Path,
    source_dir: Path,
    content_model: ContentModel,
    timezone: str,
    report: ValidationReport,
) -> list[dict[str, Any]]:
    calendar_dir = source_dir / "_official" / "calendar"
    return _read_calendar_documents(
        calendar_dir=calendar_dir,
        course_root=course_root,
        content_model=content_model,
        timezone=timezone,
        report=report,
    )


def validate_official_calendar_dates(
    objects: list[dict[str, Any]],
    report: ValidationReport,
) -> None:
    for item in objects:
        if item.get("type") not in TASK_FAMILY_TYPES:
            continue
        for field in ("due", "available"):
            _validate_civil_date(item, field, report)


def _read_calendar_documents(
    *,
    calendar_dir: Path,
    course_root: Path,
    content_model: ContentModel,
    timezone: str,
    report: ValidationReport,
) -> list[dict[str, Any]]:
    if not calendar_dir.is_dir():
        return []

    validator = validator_for("calendar-document.schema.json")
    seen_document_orders: dict[int, Path] = {}
    seen_document_ids: dict[str, Path] = {}
    seen_event_ids: dict[str, Path] = {}
    seen_occurrence_ids: dict[str, Path] = {}
    documents: list[dict[str, Any]] = []
    valid_page_ids = set(content_model.pages_by_id) | set(content_model.pages_by_alias)

    for document_path in sorted(path for path in calendar_dir.rglob("*") if path.is_file()):
        if document_path.parent != calendar_dir or document_path.suffix != ".yaml":
            report.add_error(
                "Calendar documents must be direct .yaml files",
                path=document_path,
                next_action=(
                    "Move the document to course/_official/calendar/ "
                    "and use a .yaml filename"
                ),
            )
            continue
        report.read_file(document_path)
        ordered = parse_ordered_name(document_path.stem)
        source_order = ordered.order if ordered is not None else None
        if ordered is None or ordered.sequence != "main" or ordered.order <= 0:
            report.add_error(
                "Unordered calendar document file",
                path=document_path,
                next_action="Use an ordered filename such as 1_2026-o26.yaml",
            )
        else:
            previous_path = seen_document_orders.get(ordered.order)
            if previous_path is not None:
                report.add_error(
                    "Duplicate calendar document order",
                    path=document_path,
                    next_action=(
                        "Use a unique numeric filename order; "
                        f"first seen in {previous_path}"
                    ),
                )
            else:
                seen_document_orders[ordered.order] = document_path

        try:
            data = load_yaml_file(document_path)
        except Exception as exc:
            report.add_error(
                f"Could not read calendar document: {exc}",
                path=document_path,
                next_action="Fix calendar document syntax",
            )
            continue
        if not isinstance(data, dict):
            report.add_error(
                "Calendar document must be a mapping",
                path=document_path,
                next_action="Use key/value calendar document fields",
            )
            continue

        for error in sorted(validator.iter_errors(data), key=_schema_error_key):
            report.add_error(
                _schema_error_message(error),
                path=document_path,
                field=".".join(str(part) for part in error.absolute_path) or None,
                next_action="Update the calendar document",
            )

        document_id = data.get("id")
        if isinstance(document_id, str):
            if _validate_nonblank_string(
                document_id,
                message="Calendar document ID must not be blank",
                path=document_path,
                field="id",
                report=report,
            ):
                _report_duplicate(
                    value=document_id,
                    seen=seen_document_ids,
                    message="Duplicate calendar document ID",
                    path=document_path,
                    field="id",
                    report=report,
                )

        scope = data.get("scope")
        quantum = scope.get("quantum") if isinstance(scope, dict) else None
        if isinstance(quantum, str) and quantum not in valid_page_ids:
            report.add_error(
                "Calendar document references an unknown quantum scope",
                path=document_path,
                field="scope.quantum",
                next_action="Set scope.quantum to a rendered page stable ID",
            )

        events = data.get("events")
        normalized_events: list[dict[str, Any]] = []
        if isinstance(events, list):
            for index, event in enumerate(events):
                if not isinstance(event, dict):
                    continue
                _validate_event_semantics(
                    event=event,
                    index=index,
                    path=document_path,
                    valid_page_ids=valid_page_ids,
                    report=report,
                )
                event_id = event.get("id")
                if isinstance(event_id, str):
                    event_id_is_valid = _validate_nonblank_string(
                        event_id,
                        message="Calendar event ID must not be blank",
                        path=document_path,
                        field=f"events.{index}.id",
                        report=report,
                    )
                    if event_id_is_valid:
                        _report_duplicate(
                            value=event_id,
                            seen=seen_event_ids,
                            message="Duplicate calendar event ID",
                            path=document_path,
                            field=f"events.{index}.id",
                            report=report,
                        )
                        if isinstance(document_id, str) and document_id.strip():
                            _report_duplicate(
                                value=f"calendar:{document_id}:{event_id}",
                                seen=seen_occurrence_ids,
                                message="Duplicate calendar occurrence ID",
                                path=document_path,
                                field=f"events.{index}.id",
                                report=report,
                            )
                normalized_events.append(
                    {field: event[field] for field in _EVENT_FIELDS if field in event}
                )

        documents.append(
            {
                "id": document_id,
                "authority": data.get("authority"),
                "scope": data.get("scope"),
                "source_path": document_path.relative_to(course_root).as_posix(),
                "source_order": source_order,
                "events": normalized_events,
            }
        )

    return documents


def _validate_event_semantics(
    *,
    event: dict[str, Any],
    index: int,
    path: Path,
    valid_page_ids: set[str],
    report: ValidationReport,
) -> None:
    title = event.get("title")
    if isinstance(title, str):
        _validate_nonblank_string(
            title,
            message="Calendar event title must not be blank",
            path=path,
            field=f"events.{index}.title",
            report=report,
        )
    kind = event.get("kind")
    if isinstance(kind, str) and kind not in CALENDAR_KINDS:
        report.add_error(
            "Unsupported calendar event kind",
            path=path,
            field=f"events.{index}.kind",
            next_action="Use session, holiday, milestone, or cancellation",
        )
    _validate_calendar_civil_date(event, "date", index=index, path=path, report=report)
    start_time = _validate_local_time(event, "start_time", index=index, path=path, report=report)
    end_time = _validate_local_time(event, "end_time", index=index, path=path, report=report)
    if event.get("end_time") is not None and event.get("start_time") is None:
        report.add_error(
            "Calendar event end_time requires start_time",
            path=path,
            field=f"events.{index}.end_time",
            next_action="Set start_time before setting end_time",
        )
    if start_time is not None and end_time is not None and end_time <= start_time:
        report.add_error(
            "Calendar event end_time must be later than start_time",
            path=path,
            field=f"events.{index}.end_time",
            next_action="Set end_time later than start_time on the same date",
        )
    page = event.get("page")
    if isinstance(page, str) and page not in valid_page_ids:
        report.add_error(
            "Calendar event references an unknown page",
            path=path,
            field=f"events.{index}.page",
            next_action="Set page to a rendered page stable ID",
        )


def _validate_civil_date(item: dict[str, Any], field: str, report: ValidationReport) -> None:
    content = item.get("content")
    value = content.get(field) if isinstance(content, dict) else None
    if value is None:
        return
    if not _is_civil_date(value):
        source_path = item.get("source_path")
        report.add_error(
            "Official task-family dates must be ISO civil dates (YYYY-MM-DD)",
            path=Path(source_path) if isinstance(source_path, str) else None,
            field=f"content.{field}",
            next_action=f"Set content.{field} to an ISO civil date such as 2026-08-10",
        )


def _validate_calendar_civil_date(
    event: dict[str, Any],
    field: str,
    *,
    index: int,
    path: Path,
    report: ValidationReport,
) -> None:
    if field in event and not _is_civil_date(event[field]):
        report.add_error(
            "Calendar event date must be an ISO civil date (YYYY-MM-DD)",
            path=path,
            field=f"events.{index}.{field}",
            next_action="Use a date such as 2026-08-10",
        )


def _validate_local_time(
    event: dict[str, Any],
    field: str,
    *,
    index: int,
    path: Path,
    report: ValidationReport,
) -> time | None:
    value = event.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not _LOCAL_TIME_PATTERN.fullmatch(value):
        report.add_error(
            "Calendar event time must be local 24-hour HH:MM",
            path=path,
            field=f"events.{index}.{field}",
            next_action="Use a time such as 16:00",
        )
        return None
    try:
        return time.fromisoformat(value)
    except ValueError:
        report.add_error(
            "Calendar event time must be local 24-hour HH:MM",
            path=path,
            field=f"events.{index}.{field}",
            next_action="Use a time such as 16:00",
        )
        return None


def _is_civil_date(value: Any) -> bool:
    if not isinstance(value, str) or not _CIVIL_DATE_PATTERN.fullmatch(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _report_duplicate(
    *,
    value: str,
    seen: dict[str, Path],
    message: str,
    path: Path,
    field: str,
    report: ValidationReport,
) -> None:
    if value in seen:
        report.add_error(
            message,
            path=path,
            field=field,
            next_action=f"Use a unique value; first seen in {seen[value]}",
        )
        return
    seen[value] = path


def _validate_nonblank_string(
    value: str,
    *,
    message: str,
    path: Path,
    field: str,
    report: ValidationReport,
) -> bool:
    if value.strip():
        return True
    report.add_error(
        message,
        path=path,
        field=field,
        next_action="Use a non-whitespace value",
    )
    return False


def _schema_error_key(error: ValidationError) -> tuple[str, str]:
    return (".".join(str(part) for part in error.absolute_path), error.message)


def _schema_error_message(error: ValidationError) -> str:
    if error.absolute_path:
        return error.message
    return f"Calendar document does not match schema: {error.message}"
