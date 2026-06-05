from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from raya_schema import inspect_artifact


ROOT = Path(__file__).resolve().parents[2]
EXECUTION_FIXTURE = ROOT / "examples" / "courses" / "execution-fixture"


def run_cli(
    *args: str,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "raya_cli", *args],
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_cli_run_help() -> None:
    result = run_cli("run", "--help")

    assert result.returncode == 0
    assert "--dry-run" in result.stdout
    assert "--refresh" in result.stdout
    assert "--docker" in result.stdout


def test_run_dry_run_reports_plan_without_writing_artifact(tmp_path: Path) -> None:
    course = _copy_execution_fixture(tmp_path)

    result = run_cli("run", str(course), "manual-script", "--dry-run")

    assert result.returncode == 0
    assert "Local execution dry run" in result.stdout
    assert "policy=manual" in result.stdout
    assert "command=uv run" in result.stdout
    assert not (course / "artifact" / "manifest.json").exists()


def test_run_manual_script_writes_generated_results(tmp_path: Path) -> None:
    course = _copy_execution_fixture(tmp_path)
    env, fake_uv_log = _env_with_fake_uv(tmp_path)

    result = run_cli("run", str(course), "manual-script", env=env)

    assert result.returncode == 0, result.stdout
    assert "Local execution target passed" in result.stdout
    assert "manual execution sentinel" in (
        course
        / "artifact"
        / "execution"
        / "outputs"
        / "execution-root-ccb37407e288"
        / "stdout.txt"
    ).read_text(encoding="utf-8")
    assert "run --project" in fake_uv_log.read_text(encoding="utf-8")

    manifest = json.loads((course / "artifact" / "manifest.json").read_text())
    assert manifest["data"]["execution_results"] == "data/execution-results.json"
    results = json.loads(
        (course / "artifact" / "data" / "execution-results.json").read_text()
    )
    assert results["results"][0]["status"] == "succeeded"
    assert results["results"][0]["policy"] == "manual"

    inspect_report = inspect_artifact(course / "artifact")
    assert inspect_report.ok, [diagnostic.format() for diagnostic in inspect_report.diagnostics]
    assert course / "artifact" / "data" / "execution-results.json" in inspect_report.files_read


def test_run_cache_reuses_and_refreshes(tmp_path: Path) -> None:
    course = _copy_execution_fixture(tmp_path)
    env, _fake_uv_log = _env_with_fake_uv(tmp_path)

    first = run_cli("run", str(course), "cache-script", env=env)
    second = run_cli("run", str(course), "cache-script", env=env)
    refreshed = run_cli("run", str(course), "cache-script", "--refresh", env=env)

    assert first.returncode == 0, first.stdout
    assert second.returncode == 0, second.stdout
    assert refreshed.returncode == 0, refreshed.stdout
    assert "Local execution cache hit reused" in second.stdout
    assert (course / "execution-side-effect.txt").read_text(encoding="utf-8") == "2"
    results = json.loads(
        (course / "artifact" / "data" / "execution-results.json").read_text()
    )
    assert results["results"][0]["status"] == "succeeded"


def test_run_policy_refusals_do_not_execute(tmp_path: Path) -> None:
    course = _copy_execution_fixture(tmp_path)
    env, _fake_uv_log = _env_with_fake_uv(tmp_path)

    never = run_cli("run", str(course), "never-script", env=env)
    frozen = run_cli("run", str(course), "frozen-script", env=env)

    assert never.returncode == 1
    assert frozen.returncode == 1
    assert "Execution policy refuses local execution" in never.stdout
    assert "Frozen execution policy" in frozen.stdout
    assert not (course / "SHOULD_NOT_EXIST_NEVER_SENTINEL").exists()
    assert not (course / "SHOULD_NOT_EXIST_FROZEN_SENTINEL").exists()


def test_run_failure_exits_nonzero_and_writes_logs(tmp_path: Path) -> None:
    course = _copy_execution_fixture(tmp_path)
    env, _fake_uv_log = _env_with_fake_uv(tmp_path)

    result = run_cli("run", str(course), "failing-script", env=env)

    assert result.returncode == 1
    assert "Local execution target failed" in result.stdout
    results = json.loads(
        (course / "artifact" / "data" / "execution-results.json").read_text()
    )
    record = results["results"][0]
    stderr_log = course / "artifact" / record["stderr_path"]
    assert "failing execution sentinel" in stderr_log.read_text(encoding="utf-8")
    assert record["status"] == "failed"
    assert record["exit_code"] == 7


def test_run_missing_uv_fails_clearly(tmp_path: Path) -> None:
    course = _copy_execution_fixture(tmp_path)
    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()
    env = {**os.environ, "PATH": str(empty_bin)}

    result = run_cli("run", str(course), "manual-script", env=env)

    assert result.returncode == 1
    assert "uv is unavailable" in result.stdout


def test_run_unknown_target_fails(tmp_path: Path) -> None:
    course = _copy_execution_fixture(tmp_path)

    result = run_cli("run", str(course), "missing-target", "--dry-run")

    assert result.returncode == 1
    assert "Local execution target was not found" in result.stdout


def test_run_notebook_writes_generated_output_without_mutating_source(
    tmp_path: Path,
) -> None:
    course = _copy_execution_fixture(tmp_path)
    env, _fake_uv_log = _env_with_fake_uv(tmp_path)
    source = course / "course" / "notebooks" / "demo.ipynb"
    before = source.read_text(encoding="utf-8")

    result = run_cli("run", str(course), "demo-notebook", env=env)

    assert result.returncode == 0, result.stdout
    assert source.read_text(encoding="utf-8") == before
    results = json.loads(
        (course / "artifact" / "data" / "execution-results.json").read_text()
    )
    output = course / "artifact" / results["results"][0]["output_path"]
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["metadata"]["fake_executed"] is True


def test_run_docker_dry_run_reports_compose_service(tmp_path: Path) -> None:
    course = _copy_execution_fixture(tmp_path)

    result = run_cli("run", str(course), "manual-script", "--docker", "--dry-run")

    assert result.returncode == 0
    assert "docker compose run --rm dev" in result.stdout


def test_run_docker_without_metadata_fails(tmp_path: Path) -> None:
    course = _copy_execution_fixture(tmp_path)
    profiles = course / "runtime" / "profiles.yaml"
    profiles.write_text(
        profiles.read_text(encoding="utf-8").replace(
            "    docker:\n      compose_service: dev\n",
            "",
        ),
        encoding="utf-8",
    )

    result = run_cli("run", str(course), "manual-script", "--docker", "--dry-run")

    assert result.returncode == 1
    assert "Docker execution requires profile Docker metadata" in result.stdout


def test_validate_build_inspect_do_not_execute_execution_fixture(
    tmp_path: Path,
) -> None:
    course = _copy_execution_fixture(tmp_path)
    env, fake_uv_log = _env_with_fake_uv(tmp_path)

    validate = run_cli("validate", str(course), env=env)
    build = run_cli("build", str(course), env=env)
    inspect = run_cli("artifacts", "inspect", str(course / "artifact"), env=env)

    assert validate.returncode == 0
    assert build.returncode == 0
    assert inspect.returncode == 0
    assert not fake_uv_log.exists()
    assert not (course / "execution-side-effect.txt").exists()
    assert not (course / "SHOULD_NOT_EXIST_NEVER_SENTINEL").exists()


def test_artifact_inspection_checks_execution_result_files(tmp_path: Path) -> None:
    course = _copy_execution_fixture(tmp_path)
    env, _fake_uv_log = _env_with_fake_uv(tmp_path)
    result = run_cli("run", str(course), "manual-script", env=env)
    assert result.returncode == 0, result.stdout
    stdout_path = (
        course
        / "artifact"
        / "logs"
        / "execution-root-ccb37407e288.stdout.log"
    )
    stdout_path.unlink()

    inspect_report = inspect_artifact(course / "artifact")

    assert not inspect_report.ok
    assert any(
        item.message == "Referenced artifact file is missing"
        for item in inspect_report.diagnostics
    )


def _copy_execution_fixture(tmp_path: Path) -> Path:
    course = tmp_path / "execution-fixture"
    shutil.copytree(EXECUTION_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    return course


def _env_with_fake_uv(tmp_path: Path) -> tuple[dict[str, str], Path]:
    bin_dir = tmp_path / "fake-bin"
    bin_dir.mkdir(exist_ok=True)
    fake_uv = bin_dir / "uv"
    fake_uv_log = tmp_path / "fake-uv.log"
    fake_uv.write_text(
        "\n".join(
            [
                f"#!{sys.executable}",
                "from __future__ import annotations",
                "import json",
                "import os",
                "import subprocess",
                "import sys",
                "from pathlib import Path",
                "",
                "log_path = os.environ.get('RAYA_FAKE_UV_LOG')",
                "if log_path:",
                "    path = Path(log_path)",
                "    previous = path.read_text(encoding='utf-8') if path.exists() else ''",
                "    path.write_text(previous + ' '.join(sys.argv[1:]) + '\\n', encoding='utf-8')",
                "args = sys.argv[1:]",
                "if not args or args[0] != 'run':",
                "    print('fake uv supports only run', file=sys.stderr)",
                "    sys.exit(2)",
                "payload = args[1:]",
                "while payload:",
                "    if payload[0] == '--project':",
                "        payload = payload[2:]",
                "    elif payload[0] == '--locked':",
                "        payload = payload[1:]",
                "    else:",
                "        break",
                "if payload[:3] == ['python', '-m', 'jupyter']:",
                "    if os.environ.get('RAYA_FAKE_UV_MISSING_JUPYTER'):",
                "        print('No module named jupyter', file=sys.stderr)",
                "        sys.exit(1)",
                "    source = Path(payload[payload.index('--execute') + 1])",
                "    output_name = payload[payload.index('--output') + 1]",
                "    output_dir = Path(payload[payload.index('--output-dir') + 1])",
                "    output_dir.mkdir(parents=True, exist_ok=True)",
                "    data = json.loads(source.read_text(encoding='utf-8'))",
                "    data.setdefault('metadata', {})['fake_executed'] = True",
                "    (output_dir / output_name).write_text(json.dumps(data, indent=2) + '\\n', encoding='utf-8')",
                "    print('notebook execution sentinel')",
                "    sys.exit(0)",
                "if payload and payload[0] == 'python':",
                "    completed = subprocess.run([sys.executable, *payload[1:]], text=True)",
                "    sys.exit(completed.returncode)",
                "print('unsupported fake uv command: ' + ' '.join(payload), file=sys.stderr)",
                "sys.exit(2)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    fake_uv.chmod(0o755)
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ.get('PATH', '')}"}
    env["RAYA_FAKE_UV_LOG"] = str(fake_uv_log)
    return env, fake_uv_log
