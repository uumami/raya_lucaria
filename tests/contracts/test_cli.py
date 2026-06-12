from __future__ import annotations

import os
import subprocess
import sys
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MINIMAL = ROOT / "examples" / "courses" / "minimal"


def run_cli(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
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
    return subprocess.run(
        [sys.executable, "-m", "raya_cli", *args],
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_cli_help() -> None:
    result = run_cli("--help")
    assert result.returncode == 0
    assert "doctor" in result.stdout
    assert "validate" in result.stdout
    assert "build" in result.stdout
    assert "run" in result.stdout
    assert "outputs" in result.stdout
    assert "course" in result.stdout
    assert "artifacts" in result.stdout


def test_cli_course_help() -> None:
    result = run_cli("course", "--help")

    assert result.returncode == 0
    assert "init" in result.stdout


def test_cli_artifacts_help() -> None:
    result = run_cli("artifacts", "--help")

    assert result.returncode == 0
    assert "inspect" in result.stdout


def test_cli_outputs_help() -> None:
    result = run_cli("outputs", "--help")

    assert result.returncode == 0
    assert "list" in result.stdout
    assert "freeze" in result.stdout


def test_cli_doctor_framework_context() -> None:
    result = run_cli("doctor")
    assert result.returncode == 0
    assert "context: framework" in result.stdout
    assert "files inspected:" in result.stdout


def test_cli_doctor_unknown_context(tmp_path: Path) -> None:
    result = run_cli("doctor", cwd=tmp_path)
    assert result.returncode == 0
    assert "context: unknown" in result.stdout
    assert "next:" in result.stdout


def test_cli_validate_success() -> None:
    result = run_cli("validate", str(MINIMAL))
    assert result.returncode == 0
    assert "Course validation passed" in result.stdout
    assert "files read:" in result.stdout


def test_cli_validate_failure(tmp_path: Path) -> None:
    result = run_cli("validate", str(tmp_path))
    assert result.returncode == 1
    assert "Missing raya.yaml" in result.stdout


def test_cli_build_success(tmp_path: Path) -> None:
    course = tmp_path / "course"
    shutil.copytree(MINIMAL, course, ignore=shutil.ignore_patterns("artifact"))

    result = run_cli("build", str(course))

    assert result.returncode == 0
    assert "Course artifact build passed" in result.stdout
    assert "outputs written:" in result.stdout
    assert (course / "artifact" / "manifest.json").exists()


def test_cli_build_failure(tmp_path: Path) -> None:
    result = run_cli("build", str(tmp_path))

    assert result.returncode == 1
    assert "Missing raya.yaml" in result.stdout


def test_cli_artifacts_inspect_success(tmp_path: Path) -> None:
    course = tmp_path / "course"
    shutil.copytree(MINIMAL, course, ignore=shutil.ignore_patterns("artifact"))
    build_result = run_cli("build", str(course))
    assert build_result.returncode == 0

    result = run_cli("artifacts", "inspect", str(course / "artifact"))

    assert result.returncode == 0
    assert "Artifact inspection passed" in result.stdout
    assert "files read:" in result.stdout
    assert "outputs written:" not in result.stdout


def test_cli_artifacts_inspect_failure(tmp_path: Path) -> None:
    result = run_cli("artifacts", "inspect", str(tmp_path))

    assert result.returncode == 1
    assert "Artifact manifest is missing" in result.stdout


def test_cli_course_init_success(tmp_path: Path) -> None:
    course = tmp_path / "new-course"

    result = run_cli(
        "course",
        "init",
        str(course),
        "--course-id",
        "new-course",
        "--title",
        "New Course",
    )

    assert result.returncode == 0
    assert "Course scaffold created" in result.stdout
    assert "outputs written:" in result.stdout
    assert (course / "raya.yaml").exists()


def test_cli_course_init_validate_build_inspect_loop(tmp_path: Path) -> None:
    course = tmp_path / "loop-course"
    init_result = run_cli("course", "init", str(course), "--course-id", "loop-course")
    assert init_result.returncode == 0

    validate_result = run_cli("validate", str(course))
    assert validate_result.returncode == 0

    build_result = run_cli("build", str(course))
    assert build_result.returncode == 0

    inspect_result = run_cli("artifacts", "inspect", str(course / "artifact"))
    assert inspect_result.returncode == 0
    assert "Artifact inspection passed" in inspect_result.stdout


def test_cli_course_init_refuses_non_empty_target(tmp_path: Path) -> None:
    target = tmp_path / "existing"
    target.mkdir()
    (target / "notes.txt").write_text("do not overwrite", encoding="utf-8")

    result = run_cli("course", "init", str(target))

    assert result.returncode == 1
    assert "not empty" in result.stdout
