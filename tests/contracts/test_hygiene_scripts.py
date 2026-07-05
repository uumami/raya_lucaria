from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run_command(
    *args: str,
    cwd: Path = ROOT,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
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
    if extra_env is not None:
        env.update(extra_env)
    return subprocess.run(
        list(args),
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def run_script(
    path: str,
    *args: str,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    script = ROOT / path
    assert script.exists(), f"missing script: {path}"
    return run_command(str(script), *args, extra_env=extra_env)


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


def test_check_hygiene_rejects_stale_graph_search_guidance(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "repo"
    fixture.mkdir()
    write_minimal_hygiene_root(fixture)
    (fixture / "README.md").write_text(
        "# Fixture\n\n"
        "Renderer, TypeScript/web UI, backend, identity, dynamic study state, "
        "graph UI, backlinks, wikilinks, heading-anchor validation, and external "
        "link policy remain out of scope until later proposals.\n",
        encoding="utf-8",
    )
    init_git_repo(fixture)
    commit_all(fixture, "Track stale graph search guidance")

    result = run_script("scripts/check-hygiene.sh", "--root", str(fixture))

    assert result.returncode != 0
    assert "stale graph/search current-status guidance" in result.stdout
    assert "README.md" in result.stdout


def test_check_hygiene_allows_historical_graph_search_guidance(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "repo"
    fixture.mkdir()
    write_minimal_hygiene_root(fixture)
    historical_doc = fixture / "docs" / "superpowers" / "specs" / "historical.md"
    historical_doc.parent.mkdir(parents=True)
    historical_doc.write_text(
        "# Historical fixture\n\n"
        "Graph UI, backlinks, wikilinks, heading-anchor validation, and external "
        "link policy remain out of scope until later proposals.\n",
        encoding="utf-8",
    )
    archived_doc = (
        fixture / "openspec" / "changes" / "archive" / "old-change" / "notes.md"
    )
    archived_doc.parent.mkdir(parents=True)
    archived_doc.write_text(
        "# Archived fixture\n\n"
        "Full-text search indexes and prose-derived search used to be deferred.\n",
        encoding="utf-8",
    )
    init_git_repo(fixture)
    commit_all(fixture, "Track historical stale guidance")

    result = run_script("scripts/check-hygiene.sh", "--root", str(fixture))

    assert result.returncode == 0, result.stdout


def test_check_hygiene_rejects_incomplete_markers_in_domain_language(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "repo"
    fixture.mkdir()
    write_minimal_hygiene_root(fixture)
    (fixture / "docs" / "foundation" / "14_domain_language.md").write_text(
        "# Domain Language Fixture\n\nTODO: finish this current foundation note.\n",
        encoding="utf-8",
    )
    init_git_repo(fixture)
    commit_all(fixture, "Track incomplete foundation marker")

    result = run_script("scripts/check-hygiene.sh", "--root", str(fixture))

    assert result.returncode != 0
    assert "current spec/doc incomplete markers" in result.stdout
    assert "docs/foundation/14_domain_language.md" in result.stdout


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


def test_check_hygiene_rejects_untracked_render_debug_output(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "repo"
    fixture.mkdir()
    write_minimal_hygiene_root(fixture)
    debug_dir = fixture / "tmp" / "raya-render-debug.sample"
    debug_dir.mkdir(parents=True)
    (debug_dir / "report.json").write_text("{}\n", encoding="utf-8")
    (debug_dir / "desktop-index.png").write_bytes(b"png")

    init_git_repo(fixture)

    result = run_script("scripts/check-hygiene.sh", "--root", str(fixture))

    assert result.returncode != 0
    assert "generated output appears as untracked source" in result.stdout
    assert "tmp/raya-render-debug.sample/report.json" in result.stdout


def test_check_hygiene_rejects_ignored_render_debug_sample_output(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "repo"
    fixture.mkdir()
    write_minimal_hygiene_root(fixture)
    (fixture / ".gitignore").write_text(
        "raya-render-debug*/\n"
        "**/raya-render-debug*/\n"
        "render-debug/\n"
        "**/render-debug/\n",
        encoding="utf-8",
    )
    debug_dir = fixture / "tmp" / "raya-render-debug.sample"
    debug_dir.mkdir(parents=True)
    (debug_dir / "report.json").write_text("{}\n", encoding="utf-8")

    init_git_repo(fixture)

    result = run_script("scripts/check-hygiene.sh", "--root", str(fixture))

    assert result.returncode != 0
    assert "ignored render-debug outputs" in result.stdout
    assert "tmp/raya-render-debug.sample" in result.stdout


def test_check_hygiene_rejects_ignored_render_debug_output(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "repo"
    fixture.mkdir()
    write_minimal_hygiene_root(fixture)
    (fixture / ".gitignore").write_text(
        "raya-render-debug*/\n"
        "**/raya-render-debug*/\n"
        "render-debug/\n"
        "**/render-debug/\n",
        encoding="utf-8",
    )
    debug_dir = fixture / "render-debug"
    debug_dir.mkdir()
    (debug_dir / "index.html").write_text("<html></html>\n", encoding="utf-8")

    init_git_repo(fixture)

    result = run_script("scripts/check-hygiene.sh", "--root", str(fixture))

    assert result.returncode != 0
    assert "ignored render-debug outputs" in result.stdout
    assert "render-debug" in result.stdout


def test_check_hygiene_allows_authored_png_assets(tmp_path: Path) -> None:
    fixture = tmp_path / "repo"
    fixture.mkdir()
    write_minimal_hygiene_root(fixture)
    asset = (
        fixture
        / "examples"
        / "courses"
        / "demo"
        / "course"
        / "_assets"
        / "diagram.png"
    )
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"png")

    init_git_repo(fixture)

    result = run_script("scripts/check-hygiene.sh", "--root", str(fixture))

    assert result.returncode == 0, result.stdout


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


def write_fake_docker(path: Path) -> Path:
    bin_dir = path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "{\n"
        "  printf 'RAYA_DOCKER_USER=%s\\n' \"${RAYA_DOCKER_USER-}\"\n"
        "  printf 'ARGS=%s\\n' \"$*\"\n"
        "} >> \"$RAYA_FAKE_DOCKER_CAPTURE\"\n",
        encoding="utf-8",
    )
    docker.chmod(0o755)
    return bin_dir


def test_check_docker_defaults_to_caller_user_for_compose_run(tmp_path: Path) -> None:
    capture = tmp_path / "docker.env"
    fake_bin = write_fake_docker(tmp_path)

    result = run_script(
        "scripts/check-docker.sh",
        extra_env={
            "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
            "RAYA_FAKE_DOCKER_CAPTURE": str(capture),
        },
    )

    expected_user = f"{os.getuid()}:{os.getgid()}"
    assert result.returncode == 0, result.stdout
    assert f"RAYA_DOCKER_USER={expected_user}" in result.stdout
    assert capture.read_text(encoding="utf-8") == (
        f"RAYA_DOCKER_USER={expected_user}\n"
        "ARGS=compose run --rm dev node --version\n"
        f"RAYA_DOCKER_USER={expected_user}\n"
        "ARGS=compose run --rm dev npm --version\n"
        f"RAYA_DOCKER_USER={expected_user}\n"
        "ARGS=compose run --rm dev npx --version\n"
        f"RAYA_DOCKER_USER={expected_user}\n"
        "ARGS=compose run --rm --env RAYA_INSTALL_PLAYWRIGHT_CHROMIUM=1 dev ./scripts/check-python.sh\n"
    )


def test_check_docker_preserves_user_override_for_compose_run(tmp_path: Path) -> None:
    capture = tmp_path / "docker.env"
    fake_bin = write_fake_docker(tmp_path)

    result = run_script(
        "scripts/check-docker.sh",
        extra_env={
            "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
            "RAYA_FAKE_DOCKER_CAPTURE": str(capture),
            "RAYA_DOCKER_USER": "123:456",
        },
    )

    assert result.returncode == 0, result.stdout
    assert "RAYA_DOCKER_USER=123:456" in result.stdout
    assert capture.read_text(encoding="utf-8") == (
        "RAYA_DOCKER_USER=123:456\n"
        "ARGS=compose run --rm dev node --version\n"
        "RAYA_DOCKER_USER=123:456\n"
        "ARGS=compose run --rm dev npm --version\n"
        "RAYA_DOCKER_USER=123:456\n"
        "ARGS=compose run --rm dev npx --version\n"
        "RAYA_DOCKER_USER=123:456\n"
        "ARGS=compose run --rm --env RAYA_INSTALL_PLAYWRIGHT_CHROMIUM=1 dev ./scripts/check-python.sh\n"
    )
