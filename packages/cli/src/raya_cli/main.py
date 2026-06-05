from __future__ import annotations

import argparse
from pathlib import Path

from raya_schema import ValidationReport, inspect_artifact, validate_course
from raya_static import build_course
from raya_cli.course_init import init_course
from raya_cli.execution import run_course_target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="raya",
        description="Raya Lucaria operational CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("doctor", help="Report detected context and setup status")

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a source course",
    )
    validate_parser.add_argument("course", help="Path to a source course")

    build_parser = subparsers.add_parser(
        "build",
        help="Build a static course artifact",
    )
    build_parser.add_argument("course", help="Path to a source course")

    run_parser = subparsers.add_parser(
        "run",
        help="Run one explicit local code or notebook target",
    )
    run_parser.add_argument("course", help="Path to a source course")
    run_parser.add_argument("target", help="Reference ID, runtime target ID, or source path")
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved execution plan without running the target",
    )
    run_parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh cache policy targets instead of reusing a valid cache result",
    )
    run_parser.add_argument(
        "--docker",
        action="store_true",
        help="Run through Docker Compose plus uv using the selected runtime profile",
    )

    course_parser = subparsers.add_parser(
        "course",
        help="Create and manage source courses",
    )
    course_subparsers = course_parser.add_subparsers(dest="course_command")
    course_subparsers.required = True
    init_parser = course_subparsers.add_parser(
        "init",
        help="Create a minimal source course",
    )
    init_parser.add_argument("path", help="Target course directory")
    init_parser.add_argument("--course-id", help="Stable course ID")
    init_parser.add_argument("--title", help="Human-readable course title")
    init_parser.add_argument("--description", help="Human-readable course description")
    init_parser.add_argument("--language", default="en", help="Course language code")

    artifacts_parser = subparsers.add_parser(
        "artifacts",
        help="Inspect and work with generated artifacts",
    )
    artifact_subparsers = artifacts_parser.add_subparsers(dest="artifact_command")
    artifact_subparsers.required = True
    inspect_parser = artifact_subparsers.add_parser(
        "inspect",
        help="Inspect a generated course artifact",
    )
    inspect_parser.add_argument("artifact", help="Path to an artifact directory")

    args = parser.parse_args(argv)
    if args.command == "doctor":
        return _doctor(Path.cwd())
    if args.command == "validate":
        report = validate_course(args.course)
        _print_report(report)
        return 0 if report.ok else 1
    if args.command == "build":
        report = build_course(args.course)
        _print_report(report)
        return 0 if report.ok else 1
    if args.command == "run":
        report = run_course_target(
            args.course,
            args.target,
            dry_run=args.dry_run,
            refresh=args.refresh,
            docker=args.docker,
        )
        _print_report(report)
        return 0 if report.ok else 1
    if args.command == "course" and args.course_command == "init":
        report = init_course(
            args.path,
            course_id=args.course_id,
            title=args.title,
            description=args.description,
            language=args.language,
        )
        _print_report(report)
        return 0 if report.ok else 1
    if args.command == "artifacts" and args.artifact_command == "inspect":
        report = inspect_artifact(args.artifact)
        _print_report(report)
        return 0 if report.ok else 1

    parser.print_help()
    return 0


def _doctor(cwd: Path) -> int:
    context, inspected = _detect_context(cwd)
    print("Raya doctor")
    print(f"context: {context}")
    print("files inspected:")
    for path in inspected:
        print(f"- {path}")

    if context == "unknown":
        print("next: run from a framework repo, course repo, or create one with raya course init <path>")
    elif context == "framework":
        print("next: run raya validate examples/courses/minimal, raya build examples/courses/minimal, then raya artifacts inspect examples/courses/minimal/artifact")
    elif context == "course":
        print("next: run raya validate ., raya build ., then raya artifacts inspect artifact")
    elif context == "installation":
        print("next: installation validation is not implemented in this baseline")
    return 0


def _detect_context(cwd: Path) -> tuple[str, list[Path]]:
    checks = [
        (cwd / "docs" / "foundation", "framework"),
        (cwd / "openspec" / "config.yaml", "framework"),
        (cwd / "raya.yaml", "course"),
        (cwd / "installation.yaml", "installation"),
    ]
    inspected = [path for path, _context in checks]

    has_foundation = (cwd / "docs" / "foundation").exists()
    has_openspec = (cwd / "openspec" / "config.yaml").exists()
    if has_foundation and has_openspec:
        return "framework", inspected
    if (cwd / "raya.yaml").exists():
        return "course", inspected
    if (cwd / "installation.yaml").exists():
        return "installation", inspected
    return "unknown", inspected


def _print_report(report: ValidationReport) -> None:
    print(f"context: {report.context or 'unknown'}")
    if report.files_read:
        print("files read:")
        for path in report.files_read:
            print(f"- {path}")
    if report.outputs_written:
        print("outputs written:")
        for path in report.outputs_written:
            print(f"- {path}")
    if report.diagnostics:
        print("diagnostics:")
        for diagnostic in report.diagnostics:
            print(f"- {diagnostic.format()}")
