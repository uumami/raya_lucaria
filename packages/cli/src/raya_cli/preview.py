from __future__ import annotations

import functools
import threading
import time
from dataclasses import dataclass
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from raya_schema import ValidationReport, validate_course
from raya_schema.yaml_io import load_yaml_file
from raya_static import build_course


DEFAULT_PREVIEW_HOST = "127.0.0.1"
DEFAULT_PREVIEW_PORT = 8000
INSPECTION_PATH = Path("_raya") / "inspect" / "index.html"


class _QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


@dataclass(frozen=True)
class PreviewPlan:
    course_root: Path
    artifact_dir: Path
    site_dir: Path
    entrypoint: Path
    inspection_path: Path
    host: str
    port: int

    def entrypoint_url(self, port: int | None = None) -> str:
        resolved_port = self.port if port is None else port
        return f"http://{self.host}:{resolved_port}/index.html"

    def inspection_url(self, port: int | None = None) -> str:
        resolved_port = self.port if port is None else port
        return f"http://{self.host}:{resolved_port}/{INSPECTION_PATH.as_posix()}"


@dataclass
class PreviewHandle:
    report: ValidationReport
    plan: PreviewPlan | None = None
    server: ThreadingHTTPServer | None = None
    thread: threading.Thread | None = None

    @property
    def base_url(self) -> str | None:
        if self.plan is None or self.server is None:
            return None
        return f"http://{self.plan.host}:{self.server.server_port}"

    def serve_forever(self) -> None:
        while self.server is not None:
            time.sleep(1)

    def close(self) -> None:
        server = self.server
        if server is None:
            return
        self.server = None
        if self.thread is not None and self.thread.is_alive():
            server.shutdown()
            server.server_close()
            self.thread.join(timeout=5)
        else:
            server.server_close()
        self.thread = None

    def __enter__(self) -> PreviewHandle:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()


def create_preview(
    course_path: str | Path,
    *,
    host: str = DEFAULT_PREVIEW_HOST,
    port: int = DEFAULT_PREVIEW_PORT,
    dry_run: bool = False,
) -> PreviewHandle:
    report = ValidationReport(context="preview")
    root = Path(course_path).resolve()

    if port < 0 or port > 65535:
        report.add_error(
            "Preview port is invalid",
            path=root,
            field="port",
            next_action="Use a TCP port between 0 and 65535",
        )
        return PreviewHandle(report=report)

    validation_report = validate_course(root)
    validation_report.context = "preview"
    _merge_report(report, validation_report)
    if not validation_report.ok:
        return PreviewHandle(report=report)

    plan = _preview_plan(root, host=host, port=port, report=report)
    if plan is None:
        return PreviewHandle(report=report)

    if dry_run:
        report.add_info(
            "Preview dry run",
            path=root,
            next_action=(
                f"artifact={plan.artifact_dir}; site={plan.site_dir}; "
                f"entrypoint={plan.entrypoint_url()}; inspection={plan.inspection_url()}; "
                "would_validate=true; would_build=true; would_serve=true"
            ),
        )
        return PreviewHandle(report=report, plan=plan)

    build_report = build_course(root)
    build_report.context = "preview"
    _merge_report(report, build_report)
    if not build_report.ok:
        return PreviewHandle(report=report, plan=plan)

    _validate_site(plan, report)
    if not report.ok:
        return PreviewHandle(report=report, plan=plan)

    server = _create_server(plan, report)
    if server is None:
        return PreviewHandle(report=report, plan=plan)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    bound_port = int(server.server_port)
    report.add_info(
        "Static preview ready",
        path=plan.site_dir,
        next_action=(
            f"entrypoint={plan.entrypoint_url(bound_port)}; "
            f"artifact={plan.artifact_dir}"
        ),
    )
    if plan.inspection_path.is_file():
        report.add_info(
            "Preview inspection surface available",
            path=plan.inspection_path,
            next_action=f"inspection={plan.inspection_url(bound_port)}",
        )
    return PreviewHandle(report=report, plan=plan, server=server, thread=thread)


def _preview_plan(
    root: Path,
    *,
    host: str,
    port: int,
    report: ValidationReport,
) -> PreviewPlan | None:
    config_path = root / "raya.yaml"
    report.read_file(config_path)
    try:
        config = load_yaml_file(config_path)
    except Exception as exc:
        report.add_error(
            f"Could not read YAML: {exc}",
            path=config_path,
            next_action="Fix YAML syntax",
        )
        return None
    if not isinstance(config, dict):
        report.add_error(
            "YAML document must be a mapping",
            path=config_path,
            next_action="Use key/value configuration fields",
        )
        return None

    artifact_value = config.get("artifact", "artifact")
    if not isinstance(artifact_value, str) or not artifact_value.strip():
        report.add_error(
            "Course artifact field must be a non-empty string",
            path=config_path,
            field="artifact",
            next_action="Use an artifact directory such as artifact",
        )
        return None

    artifact_dir = (root / artifact_value).resolve()
    site_dir = artifact_dir / "site"
    entrypoint = site_dir / "index.html"
    inspection_path = site_dir / INSPECTION_PATH
    return PreviewPlan(
        course_root=root,
        artifact_dir=artifact_dir,
        site_dir=site_dir,
        entrypoint=entrypoint,
        inspection_path=inspection_path,
        host=host,
        port=port,
    )


def _validate_site(plan: PreviewPlan, report: ValidationReport) -> None:
    if not plan.site_dir.is_dir():
        report.add_error(
            "Preview site directory is missing",
            path=plan.site_dir,
            next_action="Run raya build and confirm the artifact static_site_root exists",
        )
        return
    if not plan.entrypoint.is_file():
        report.add_error(
            "Preview entrypoint is missing",
            path=plan.entrypoint,
            next_action="Build a course with an index page before previewing it",
        )


def _create_server(
    plan: PreviewPlan,
    report: ValidationReport,
) -> ThreadingHTTPServer | None:
    handler = functools.partial(_QuietStaticHandler, directory=str(plan.site_dir))
    try:
        return ThreadingHTTPServer((plan.host, plan.port), handler)
    except OSError as exc:
        report.add_error(
            "Preview host or port is unavailable",
            path=plan.site_dir,
            field=f"{plan.host}:{plan.port}",
            next_action=f"Choose another --host/--port or stop the conflicting process ({exc})",
        )
        return None


def _merge_report(target: ValidationReport, source: ValidationReport) -> None:
    for path in source.files_read:
        target.read_file(path)
    for path in source.outputs_written:
        target.wrote_output(path)
    target.diagnostics.extend(source.diagnostics)

