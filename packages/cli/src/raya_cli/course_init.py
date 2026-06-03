from __future__ import annotations

import json
import re
from pathlib import Path

from raya_schema import ValidationReport


COURSE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def init_course(
    target_path: str | Path,
    *,
    course_id: str | None = None,
    title: str | None = None,
    description: str | None = None,
    language: str = "en",
) -> ValidationReport:
    target = Path(target_path).resolve()
    report = ValidationReport(context="course")

    if target.exists() and not target.is_dir():
        report.add_error(
            "Course target is not a directory",
            path=target,
            next_action="Pass a missing or empty directory path",
        )
        return report
    if target.exists() and any(target.iterdir()):
        report.add_error(
            "Course target directory is not empty",
            path=target,
            next_action="Choose an empty directory or a new path",
        )
        return report

    resolved_course_id = course_id or _default_course_id(target)
    resolved_title = title or _default_title(target)
    resolved_description = (
        description or "Replace this scaffold description with the course description."
    )
    if not COURSE_ID_RE.fullmatch(resolved_course_id):
        report.add_error(
            "Course ID is invalid",
            path=target,
            field="course_id",
            next_action="Use lowercase letters, numbers, dots, underscores, or hyphens",
        )
        return report

    target.mkdir(parents=True, exist_ok=True)
    report.wrote_output(target)

    directories = [
        target / "content",
        target / "assets",
        target / "official" / "cards",
        target / "official" / "quizzes",
        target / "official" / "prompts",
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        report.wrote_output(directory)

    config_path = target / "raya.yaml"
    config_path.write_text(
        "\n".join(
            [
                f"course_id: {resolved_course_id}",
                f"title: {_yaml_string(resolved_title)}",
                f"description: {_yaml_string(resolved_description)}",
                f"language: {_yaml_string(language)}",
                "content: content",
                "artifact: artifact",
                "",
            ]
        ),
        encoding="utf-8",
    )
    report.wrote_output(config_path)

    index_path = target / "content" / "00_index.md"
    index_path.write_text(
        "\n".join(
            [
                "---",
                f"title: {resolved_title}",
                "quantum:",
                "  id: course-root",
                "  type: page",
                "---",
                "",
                f"# {resolved_title}",
                "",
                "This page is replaceable scaffold created by `raya course init`.",
                "Replace it with course material before treating it as official canon.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    report.wrote_output(index_path)

    report.add_info(
        "Course scaffold created",
        path=target,
        next_action="Run raya validate, raya build, and raya artifacts inspect",
    )
    return report


def _default_course_id(target: Path) -> str:
    value = target.name.lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = value.strip(".-_")
    if not value or not value[0].isalnum():
        return "new-course"
    return value


def _default_title(target: Path) -> str:
    words = re.split(r"[-_ .]+", target.name.strip())
    title = " ".join(word.capitalize() for word in words if word)
    return title or "New Course"


def _yaml_string(value: str) -> str:
    return json.dumps(value)
