from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run_npm_renderer(
    *args: str,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    return subprocess.run(
        ["npm", "run", "raya-render-math", "--", *args],
        cwd=ROOT,
        env=env,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def run_node_renderer(
    *args: str,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    return subprocess.run(
        ["node", "packages/static/scripts/render_math.mjs", *args],
        cwd=ROOT,
        env=env,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_package_json_declares_renderer_only_mathjax_tooling() -> None:
    path = ROOT / "package.json"
    assert path.exists(), "root package.json must declare renderer tooling"
    package_json = json.loads(path.read_text(encoding="utf-8"))

    assert package_json["name"] == "raya-lucaria-renderer-tools"
    assert package_json["private"] is True
    assert package_json["type"] == "module"
    assert (
        package_json["scripts"]["raya-render-math"]
        == "node packages/static/scripts/render_math.mjs"
    )
    assert package_json["dependencies"]["@mathjax/src"] == "4.0.0"
    assert package_json["overrides"]["@xmldom/xmldom"] == "0.9.10"


def test_package_lock_pins_mathjax_src_v4() -> None:
    path = ROOT / "package-lock.json"
    assert path.exists(), "root package-lock.json must pin renderer dependencies"
    package_lock = json.loads(path.read_text(encoding="utf-8"))

    assert package_lock["name"] == "raya-lucaria-renderer-tools"
    assert package_lock["packages"][""]["dependencies"]["@mathjax/src"] == "4.0.0"
    assert package_lock["packages"]["node_modules/@mathjax/src"]["version"] == "4.0.0"
    assert package_lock["packages"]["node_modules/@xmldom/xmldom"]["version"] == "0.9.10"


def test_check_python_installs_renderer_dependencies_before_python_sync() -> None:
    script = (ROOT / "scripts" / "check-python.sh").read_text(encoding="utf-8")

    npm_ci = "run npm ci --ignore-scripts --no-audit --no-fund"
    self_test = "run npm run raya-render-math -- --self-test"
    uv_sync = "run uv sync --python 3.10 --all-packages --dev"

    assert "Node/MathJax renderer dependency installation" in script
    assert npm_ci in script
    assert self_test in script
    assert script.index(npm_ci) < script.index(self_test) < script.index(uv_sync)


def test_render_debug_parity_script_is_declared() -> None:
    script = ROOT / "scripts" / "check-render-debug.sh"

    assert script.exists(), "renderer parity gate script must exist"
    content = script.read_text(encoding="utf-8")
    assert "Usage: scripts/check-render-debug.sh" in content
    assert "raya preview" in content
    assert "--render-debug" in content
    assert "summary.json" in content


def test_check_python_runs_render_debug_parity_gate_after_fixture_builds() -> None:
    script = (ROOT / "scripts" / "check-python.sh").read_text(encoding="utf-8")

    render_fixture_build = 'run uv run raya build "$course"'
    render_debug_gate = "run scripts/check-render-debug.sh"
    docs_validate = "run uv run raya validate docs"

    assert "render-debug parity gate" in script
    assert render_debug_gate in script
    assert script.index(render_fixture_build) < script.index(render_debug_gate)
    assert script.index(render_debug_gate) < script.index(docs_validate)


def test_docker_check_inherits_render_debug_parity_gate() -> None:
    docker_script = (ROOT / "scripts" / "check-docker.sh").read_text(encoding="utf-8")
    python_script = (ROOT / "scripts" / "check-python.sh").read_text(encoding="utf-8")

    assert "./scripts/check-python.sh" in docker_script
    assert "scripts/check-render-debug.sh" in python_script


def test_renderer_script_path_and_npm_cache_are_owned_by_repo_contract() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    script = ROOT / "packages" / "static" / "scripts" / "render_math.mjs"

    assert "node_modules/" in gitignore
    assert ".npm/" in gitignore
    assert script.exists()


def test_renderer_self_test_succeeds() -> None:
    result = run_npm_renderer("--self-test")

    assert result.returncode == 0, result.stderr + result.stdout

    direct = run_node_renderer("--self-test")
    assert direct.returncode == 0, direct.stderr + direct.stdout
    assert direct.stdout == ""


def test_renderer_converts_json_stdin_to_json_stdout() -> None:
    result = run_node_renderer(
        input_text=json.dumps(
            {
                "items": [
                    {"id": "inline", "tex": "x^2", "display": False},
                    {"id": "display", "tex": "\\int_0^1 x^2 dx", "display": True},
                    {
                        "id": "macro",
                        "tex": "\\newcommand{\\vect}[1]{\\mathbf{#1}}\\vect{x}",
                        "display": False,
                    },
                ],
            },
        ),
    )

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["errors"] == []
    assert payload["css"]
    assert [item["id"] for item in payload["rendered"]] == ["inline", "display", "macro"]
    assert all("MathJax" in item["html"] for item in payload["rendered"])
    assert 'display="true"' in payload["rendered"][1]["html"]


def test_renderer_fails_unknown_control_sequence() -> None:
    result = run_node_renderer(
        input_text=json.dumps(
            {
                "items": [
                    {"id": "bad", "tex": "\\unknownmacro", "display": False},
                ],
            },
        ),
    )

    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["rendered"] == []
    assert payload["css"]
    assert payload["errors"][0]["id"] == "bad"
    assert "Undefined control sequence" in payload["errors"][0]["message"]
    assert "\\unknownmacro" in payload["errors"][0]["message"]
