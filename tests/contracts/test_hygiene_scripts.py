from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run_command(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    for key in tuple(env):
        if (
            key == "GIT_CONFIG_COUNT"
            or key == "GIT_CONFIG_PARAMETERS"
            or key.startswith("GIT_CONFIG_KEY_")
            or key.startswith("GIT_CONFIG_VALUE_")
        ):
            env.pop(key)
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
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

    disabled_hooks = path / ".git" / "hooks-disabled"
    disabled_hooks.mkdir()

    for key, value in (
        ("user.name", "Raya Test"),
        ("user.email", "raya-test@example.invalid"),
        ("commit.gpgsign", "false"),
        ("tag.gpgsign", "false"),
        ("core.hooksPath", str(disabled_hooks)),
        ("core.excludesFile", os.devnull),
    ):
        result = run_command("git", "config", key, value, cwd=path)
        assert result.returncode == 0, result.stdout


def commit_all(path: Path, message: str) -> None:
    result = run_command("git", "add", ".", cwd=path)
    assert result.returncode == 0, result.stdout

    result = run_command(
        "git",
        "commit",
        "--no-gpg-sign",
        "--no-verify",
        "-m",
        message,
        cwd=path,
    )
    assert result.returncode == 0, result.stdout


def write_minimal_hygiene_root(path: Path) -> None:
    files = {
        "README.md": "# Fixture\n\nCurrent repository guidance fixture.\n",
        "AGENTS.md": "# Fixture Agents\n\nFixture material for agent guidance.\n",
        "docs/foundation/00_index.md": "# Foundation Fixture\n",
        "docs/guides/en/contributors/index.md": "# Contributor Fixture\n",
        "docs/guides/es/contributors/index.md": "# Colaborador Fixture\n",
        "examples/gallery/index.html": "<p>fixture material</p>\n",
        "openspec/config.yaml": "project: fixture\n",
        "openspec/specs/dev-workflow-baseline/spec.md": "# Dev Workflow Fixture\n",
        "packages/schema/README.md": "# Schema Fixture\n",
    }

    for relative_path, contents in files.items():
        target = path / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(contents, encoding="utf-8")


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
    write_minimal_hygiene_root(fixture)
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
    fixture.mkdir()
    write_minimal_hygiene_root(fixture)
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
