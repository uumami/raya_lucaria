from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run_command(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    return subprocess.run(
        list(args),
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def run_script(path: str, *args: str) -> subprocess.CompletedProcess[str]:
    script = ROOT / path
    assert script.exists(), f"missing script: {path}"
    return run_command(str(script), *args)


def init_git_repo(path: Path) -> None:
    result = run_command("git", "init", cwd=path)
    assert result.returncode == 0, result.stdout

    for key, value in (
        ("user.name", "Raya Test"),
        ("user.email", "raya-test@example.invalid"),
    ):
        result = run_command("git", "config", key, value, cwd=path)
        assert result.returncode == 0, result.stdout


def commit_all(path: Path, message: str) -> None:
    result = run_command("git", "add", ".", cwd=path)
    assert result.returncode == 0, result.stdout

    result = run_command("git", "commit", "-m", message, cwd=path)
    assert result.returncode == 0, result.stdout


def test_check_hygiene_help_includes_usage_and_root_option() -> None:
    result = run_script("scripts/check-hygiene.sh", "--help")

    assert result.returncode == 0, result.stdout
    assert "Usage: scripts/check-hygiene.sh" in result.stdout
    assert "--root" in result.stdout


def test_check_hygiene_rejects_stale_required_code_notebook_guidance(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "repo"
    fixture.mkdir()
    (fixture / "README.md").write_text(
        "# Fixture\n\n"
        "Local `.py` files must resolve under accepted `code/` support roots.\n"
        "Local `.ipynb` files must resolve under accepted `notebooks/` support roots.\n",
        encoding="utf-8",
    )
    init_git_repo(fixture)
    commit_all(fixture, "Track stale guidance")

    result = run_script("scripts/check-hygiene.sh", "--root", str(fixture))

    assert result.returncode != 0
    assert "stale code/notebook folder requirement" in result.stdout
    assert "README.md" in result.stdout


def test_check_hygiene_rejects_tracked_generated_course_artifact(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "repo"
    generated = fixture / "examples" / "courses" / "minimal" / "artifact" / "site"
    generated.mkdir(parents=True)
    (generated / "index.html").write_text("<html></html>\n", encoding="utf-8")

    init_git_repo(fixture)
    commit_all(fixture, "Track generated output")

    result = run_script("scripts/check-hygiene.sh", "--root", str(fixture))

    assert result.returncode != 0
    assert "generated output tracked by git" in result.stdout
    assert "examples/courses/minimal/artifact/site/index.html" in result.stdout


def test_check_help_mentions_python_check_script() -> None:
    result = run_script("scripts/check.sh", "--help")

    assert result.returncode == 0, result.stdout
    assert "Usage: scripts/check.sh" in result.stdout
    assert "scripts/check-python.sh" in result.stdout


def test_check_docker_help_mentions_docker_compose() -> None:
    result = run_script("scripts/check-docker.sh", "--help")

    assert result.returncode == 0, result.stdout
    assert "Usage: scripts/check-docker.sh" in result.stdout
    assert "docker compose" in result.stdout
