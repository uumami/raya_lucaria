from __future__ import annotations

import os
import select
import shutil
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MINIMAL = ROOT / "examples" / "courses" / "minimal"
EXECUTION_FIXTURE = ROOT / "examples" / "courses" / "execution-fixture"


def run_cli(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "raya_cli", *args],
        cwd=cwd,
        env=cli_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def cli_env() -> dict[str, str]:
    env = {**os.environ}
    pythonpath = ":".join(
        str(path)
        for path in (
            ROOT / "packages" / "schema" / "src",
            ROOT / "packages" / "static" / "src",
            ROOT / "packages" / "cli" / "src",
        )
    )
    env["PYTHONPATH"] = (
        f"{pythonpath}:{env['PYTHONPATH']}" if env.get("PYTHONPATH") else pythonpath
    )
    return env


def test_cli_preview_help_lists_static_options() -> None:
    result = run_cli("preview", "--help")

    assert result.returncode == 0
    assert "preview" in result.stdout
    assert "--host" in result.stdout
    assert "--port" in result.stdout
    assert "--dry-run" in result.stdout


def test_cli_preview_dry_run_reports_static_plan(tmp_path: Path) -> None:
    course = tmp_path / "minimal"
    shutil.copytree(MINIMAL, course, ignore=shutil.ignore_patterns("artifact"))

    result = run_cli(
        "preview",
        str(course),
        "--host",
        "127.0.0.1",
        "--port",
        "8123",
        "--dry-run",
    )

    assert result.returncode == 0
    assert "context: preview" in result.stdout
    assert "Preview dry run" in result.stdout
    assert f"file={course.resolve()}" in result.stdout
    assert f"artifact={course.resolve() / 'artifact'}" in result.stdout
    assert f"site={course.resolve() / 'artifact' / 'site'}" in result.stdout
    assert "entrypoint=http://127.0.0.1:8123/index.html" in result.stdout
    assert "inspection=http://127.0.0.1:8123/_raya/inspect/index.html" in result.stdout


def test_cli_preview_non_dry_run_flushes_startup_urls(tmp_path: Path) -> None:
    course = tmp_path / "minimal"
    shutil.copytree(MINIMAL, course, ignore=shutil.ignore_patterns("artifact"))

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "raya_cli",
            "preview",
            str(course),
            "--host",
            "127.0.0.1",
            "--port",
            "0",
        ],
        cwd=ROOT,
        env=cli_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        output = _read_until(process, "_raya/inspect/index.html", timeout=10)
        assert "Static preview ready" in output
        assert "entrypoint=http://127.0.0.1:" in output
        assert "_raya/inspect/index.html" in output
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_cli_preview_failure_reports_invalid_course(tmp_path: Path) -> None:
    result = run_cli("preview", str(tmp_path), "--dry-run")

    assert result.returncode == 1
    assert "context: preview" in result.stdout
    assert "Missing raya.yaml" in result.stdout
    assert f"file={tmp_path.resolve() / 'raya.yaml'}" in result.stdout


def test_preview_planning_does_not_mutate_process_cwd() -> None:
    from raya_cli.preview import create_preview

    cwd = Path.cwd()
    handle = create_preview(MINIMAL, host="127.0.0.1", port=8124, dry_run=True)

    assert Path.cwd() == cwd
    assert handle.report.ok
    assert handle.server is None


def test_preview_preparation_does_not_execute_course_targets(tmp_path: Path) -> None:
    from raya_cli.preview import create_preview

    course = tmp_path / "execution-fixture"
    shutil.copytree(EXECUTION_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        assert handle.server is not None
    finally:
        handle.close()

    assert not (course / "execution-side-effect.txt").exists()
    assert not (course / "SHOULD_NOT_EXIST_NEVER_SENTINEL").exists()
    assert not (course / "artifact" / "data" / "execution-results.json").exists()
    diagnostics = "\n".join(diagnostic.format() for diagnostic in handle.report.diagnostics)
    assert "Static preview ready" in diagnostics
    assert "raya run" not in diagnostics
    assert "outputs freeze" not in diagnostics


def test_preview_does_not_invoke_execution_commands_or_tooling(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from raya_cli import execution, outputs
    from raya_cli.preview import create_preview

    course = tmp_path / "execution-fixture"
    shutil.copytree(EXECUTION_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    invocation_log = tmp_path / "tool-invocations.log"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    for name in (
        "uv",
        "docker",
        "jupyter",
        "jupyter-notebook",
        "ipython",
        "pip",
        "pip3",
        "python",
        "python3",
    ):
        tool = fake_bin / name
        tool.write_text(
            "#!/usr/bin/env bash\n"
            f"printf '%s\\n' {name!r} >> {str(invocation_log)!r}\n"
            "exit 97\n",
            encoding="utf-8",
        )
        tool.chmod(0o755)

    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("preview must not call execution or output freezing")

    monkeypatch.setattr(execution, "run_course_target", fail_if_called)
    monkeypatch.setattr(outputs, "freeze_course_output", fail_if_called)
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}")

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        assert handle.server is not None
    finally:
        handle.close()

    assert not invocation_log.exists()


def _read_until(
    process: subprocess.Popen[str],
    expected: str,
    *,
    timeout: float,
) -> str:
    assert process.stdout is not None
    output = ""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stderr = process.stderr.read() if process.stderr is not None else ""
            raise AssertionError(
                f"process exited before {expected!r}; stdout={output!r}; stderr={stderr!r}"
            )
        readable, _, _ = select.select([process.stdout], [], [], 0.1)
        if not readable:
            continue
        line = process.stdout.readline()
        if not line:
            continue
        output += line
        if expected in output:
            return output
    raise AssertionError(f"timed out waiting for {expected!r}; stdout={output!r}")
