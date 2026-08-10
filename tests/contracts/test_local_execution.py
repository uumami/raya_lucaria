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


def test_cli_outputs_list_reports_reviewed_state(tmp_path: Path) -> None:
    course = _copy_execution_fixture(tmp_path)
    env, fake_uv_log = _env_with_fake_uv(tmp_path)

    result = run_cli("outputs", "list", str(course), env=env)

    assert result.returncode == 0, result.stdout
    assert "Output listing passed" in result.stdout
    assert "field=frozen-script" in result.stdout
    assert "reviewed=current" in result.stdout
    assert "frozen=valid" in result.stdout
    assert not fake_uv_log.exists()


def test_cli_outputs_freeze_copies_generated_result(tmp_path: Path) -> None:
    course = _copy_execution_fixture(tmp_path)
    env, fake_uv_log = _env_with_fake_uv(tmp_path)

    run = run_cli("run", str(course), "cache-script", env=env)
    before_freeze_log = fake_uv_log.read_text(encoding="utf-8")
    freeze = run_cli("outputs", "freeze", str(course), "cache-script", env=env)

    assert run.returncode == 0, run.stdout
    assert freeze.returncode == 0, freeze.stdout
    assert "Reviewed output frozen" in freeze.stdout
    assert fake_uv_log.read_text(encoding="utf-8") == before_freeze_log
    manifest = course / "course" / "_reviewed" / "execution" / "cache-script" / "reviewed.yaml"
    reviewed_stdout = manifest.parent / "stdout.txt"
    assert manifest.exists()
    assert reviewed_stdout.exists()
    assert "cache execution count" in reviewed_stdout.read_text(encoding="utf-8")

    build = run_cli("build", str(course), env=env)
    assert build.returncode == 0, build.stdout
    html = (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8")
    assert "Reviewed Output" in html
    assert "cache-script" in html
    assert (course / "artifact" / "site" / "_raya" / "reviewed" / "cache-script" / "stdout.txt").exists()


def test_run_outputs_and_freeze_support_non_special_script_path(tmp_path: Path) -> None:
    course = _write_natural_execution_course(tmp_path)
    env, fake_uv_log = _env_with_fake_uv(tmp_path)

    run = run_cli("run", str(course), "course/scripts/manual_task.py", env=env)
    listing = run_cli("outputs", "list", str(course), env=env)
    freeze = run_cli("outputs", "freeze", str(course), "course/scripts/manual_task.py", env=env)

    assert run.returncode == 0, run.stdout
    assert listing.returncode == 0, listing.stdout
    assert freeze.returncode == 0, freeze.stdout
    assert "Local execution target passed" in run.stdout
    assert "field=natural-script" in listing.stdout
    assert "generated=succeeded" in listing.stdout
    assert "Reviewed output frozen" in freeze.stdout
    assert "course/scripts/manual_task.py" in fake_uv_log.read_text(encoding="utf-8")

    manifest = course / "course" / "_reviewed" / "execution" / "natural-script" / "reviewed.yaml"
    reviewed_stdout = manifest.parent / "stdout.txt"
    assert manifest.exists()
    assert reviewed_stdout.read_text(encoding="utf-8") == "natural execution sentinel\n"

    build = run_cli("build", str(course), env=env)
    assert build.returncode == 0, build.stdout
    html = (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8")
    assert 'href="_raya/files/_source/scripts/manual_task.py"' in html
    assert "Reviewed Output" in html


def test_cli_outputs_freeze_refuses_failed_result(tmp_path: Path) -> None:
    course = _copy_execution_fixture(tmp_path)
    env, _fake_uv_log = _env_with_fake_uv(tmp_path)

    run = run_cli("run", str(course), "failing-script", env=env)
    freeze = run_cli("outputs", "freeze", str(course), "failing-script", env=env)

    assert run.returncode == 1
    assert freeze.returncode == 1
    assert "Generated execution result is not successful" in freeze.stdout
    assert not (
        course / "course" / "_reviewed" / "execution" / "failing-script"
    ).exists()


def test_cli_outputs_freeze_refuses_stale_generated_result(tmp_path: Path) -> None:
    course = _copy_execution_fixture(tmp_path)
    env, _fake_uv_log = _env_with_fake_uv(tmp_path)

    run = run_cli("run", str(course), "cache-script", env=env)
    assert run.returncode == 0, run.stdout
    task = course / "course" / "code" / "cache_task.py"
    task.write_text(task.read_text(encoding="utf-8") + "\nprint('changed')\n", encoding="utf-8")
    freeze = run_cli("outputs", "freeze", str(course), "cache-script", env=env)

    assert freeze.returncode == 1
    assert "Generated execution result is stale" in freeze.stdout
    assert not (course / "course" / "_reviewed" / "execution" / "cache-script").exists()


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

    assert never.returncode == 1
    assert "Execution policy refuses local execution" in never.stdout
    assert not (course / "SHOULD_NOT_EXIST_NEVER_SENTINEL").exists()


def test_run_frozen_target_validates_reviewed_output_without_executing(
    tmp_path: Path,
) -> None:
    course = _copy_execution_fixture(tmp_path)
    env, fake_uv_log = _env_with_fake_uv(tmp_path)

    frozen = run_cli("run", str(course), "frozen-script", env=env)

    assert frozen.returncode == 0, frozen.stdout
    assert "Frozen execution target reviewed output is current" in frozen.stdout
    assert not fake_uv_log.exists()
    assert not (course / "SHOULD_NOT_EXIST_FROZEN_SENTINEL").exists()


def test_run_frozen_missing_reviewed_output_fails_without_executing(
    tmp_path: Path,
) -> None:
    course = _copy_execution_fixture(tmp_path)
    shutil.rmtree(course / "course" / "_reviewed")
    env, fake_uv_log = _env_with_fake_uv(tmp_path)

    frozen = run_cli("run", str(course), "frozen-script", env=env)

    assert frozen.returncode == 1
    assert "Frozen execution target is missing current reviewed output" in frozen.stdout
    assert not fake_uv_log.exists()
    assert not (course / "SHOULD_NOT_EXIST_FROZEN_SENTINEL").exists()


def test_validate_stale_reviewed_output_fails(tmp_path: Path) -> None:
    course = _copy_execution_fixture(tmp_path)
    task = course / "course" / "code" / "frozen_task.py"
    task.write_text(task.read_text(encoding="utf-8") + "\nprint('changed')\n", encoding="utf-8")

    result = run_cli("validate", str(course))

    assert result.returncode == 1
    assert "Stale reviewed output metadata" in result.stdout
    assert "source_sha256" in result.stdout


def test_validate_missing_reviewed_file_fails(tmp_path: Path) -> None:
    course = _copy_execution_fixture(tmp_path)
    (course / "course" / "_reviewed" / "execution" / "frozen-script" / "stdout.txt").unlink()

    result = run_cli("validate", str(course))

    assert result.returncode == 1
    assert "Reviewed output file is missing" in result.stdout


def test_validate_escaping_reviewed_file_fails(tmp_path: Path) -> None:
    course = _copy_execution_fixture(tmp_path)
    manifest = course / "course" / "_reviewed" / "execution" / "frozen-script" / "reviewed.yaml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace("path: stdout.txt", "path: ../stdout.txt"),
        encoding="utf-8",
    )

    result = run_cli("validate", str(course))

    assert result.returncode == 1
    assert "Reviewed output file path must stay under its manifest directory" in result.stdout


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
        ).replace("policy: frozen", "policy: never"),
        encoding="utf-8",
    )
    shutil.rmtree(course / "course" / "_reviewed")

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


def _write_natural_execution_course(tmp_path: Path) -> Path:
    course = tmp_path / "natural-execution"
    source = course / "course"
    scripts = source / "scripts"
    runtime = course / "runtime"
    scripts.mkdir(parents=True)
    runtime.mkdir(parents=True)
    (course / "raya.yaml").write_text(
        "\n".join(
            [
                "course_id: natural-execution",
                "title: Natural Execution",
                "description: Fixture for non-special execution paths.",
                "language: en",
                "source: course",
                "artifact: artifact",
                "calendar:",
                "  timezone: America/Mexico_City",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (course / "pyproject.toml").write_text(
        "[project]\nname = \"natural-execution\"\nversion = \"0.1.0\"\n",
        encoding="utf-8",
    )
    (course / "uv.lock").write_text("", encoding="utf-8")
    (runtime / "profiles.yaml").write_text(
        "\n".join(
            [
                "profiles:",
                "  default:",
                "    manager: uv",
                "    python: \"3.10\"",
                "    project: pyproject.toml",
                "    lockfile: uv.lock",
                "execution:",
                "  defaults:",
                "    policy: never",
                "    profile: default",
                "  references:",
                "    - id: natural-script",
                "      source: course/scripts/manual_task.py",
                "      policy: manual",
                "      profile: default",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (source / "0_index.md").write_text(
        "---\n"
        "id: natural-root\n"
        "title: Natural Root\n"
        "summary: Non-special execution fixture.\n"
        "status: ready\n"
        "---\n"
        "# Natural Root\n\n"
        "Run the [manual task](scripts/manual_task.py).\n",
        encoding="utf-8",
    )
    (scripts / "manual_task.py").write_text(
        "print('natural execution sentinel')\n",
        encoding="utf-8",
    )
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
