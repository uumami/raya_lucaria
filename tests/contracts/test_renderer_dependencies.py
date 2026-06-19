from __future__ import annotations

import json
import os
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_static_wheel_includes_open_dyslexic_font_resource(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            "uv",
            "build",
            "--package",
            "raya-static",
            "--wheel",
            "--out-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    wheels = sorted(tmp_path.glob("raya_static-*.whl"))
    assert len(wheels) == 1
    with zipfile.ZipFile(wheels[0]) as wheel:
        names = set(wheel.namelist())
    assert (
        "raya_static/assets/accessibility/open-dyslexic/OpenDyslexic-Regular.woff"
        in names
    )


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


def test_render_debug_parity_script_uses_report_module() -> None:
    script = (ROOT / "scripts" / "check-render-debug.sh").read_text(encoding="utf-8")

    assert "uv run python -m raya_cli.render_debug_report" in script
    assert "uv run python - " not in script
    assert "<<'PY'" not in script
    assert "<<PY" not in script


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


def test_render_debug_parity_gate_is_documented_in_command_guidance() -> None:
    for path in (
        ROOT / "README.md",
        ROOT / "AGENTS.md",
        ROOT / "openspec" / "config.yaml",
    ):
        assert "check-render-debug.sh" in path.read_text(encoding="utf-8")


def test_render_debug_report_module_and_guidance_are_declared() -> None:
    module = ROOT / "packages" / "cli" / "src" / "raya_cli" / "render_debug_report.py"
    script = (ROOT / "scripts" / "check-render-debug.sh").read_text(encoding="utf-8")

    assert module.exists()
    module_text = module.read_text(encoding="utf-8")
    assert "inspect_render_debug" in module_text
    assert "report.json" in module_text
    assert "index.html" in module_text
    assert "copied_site_dir" in module_text
    assert "python -m raya_cli.render_debug_report" in script

    for path in (
        ROOT / "README.md",
        ROOT / "AGENTS.md",
        ROOT / "openspec" / "config.yaml",
        ROOT / "docs" / "guides" / "en" / "contributors" / "index.md",
        ROOT / "docs" / "guides" / "en" / "agents" / "index.md",
        ROOT / "docs" / "guides" / "es" / "colaboradores" / "index.md",
        ROOT / "docs" / "guides" / "es" / "agentes" / "index.md",
    ):
        text = path.read_text(encoding="utf-8")
        assert "report.json" in text
        assert "index.html" in text


def test_role_docs_cover_skin_profiles_and_style_guide() -> None:
    foundation = (ROOT / "docs/foundation/17_rendering_execution_plan.md").read_text(
        encoding="utf-8"
    )
    for needle in (
        "`render.skin`",
        "`skins/`",
        "`_raya/skin.yaml`",
        "semantic tokens",
        "no external fonts",
    ):
        assert needle in foundation

    required = {
        "docs/guides/en/professors/index.md": [
            "`render.skin`",
            "`skins/`",
            "`_raya/skin.yaml`",
            "section",
            "contrast",
            "no external fonts",
        ],
        "docs/guides/en/contributors/index.md": [
            "semantic tokens",
            "`skin.css`",
            "no arbitrary CSS",
            "render-debug",
        ],
        "docs/guides/en/students/index.md": [
            "visual presentation",
            "does not change",
            "links",
        ],
        "docs/guides/en/agents/index.md": [
            "`data-raya-skin`",
            "`skin.css`",
            "`_raya/skin.yaml`",
            "render-debug",
        ],
        "docs/guides/es/profesores/index.md": [
            "`render.skin`",
            "`skins/`",
            "`_raya/skin.yaml`",
            "seccion",
            "contraste",
            "fuentes externas",
        ],
        "docs/guides/es/colaboradores/index.md": [
            "tokens semanticos",
            "`skin.css`",
            "CSS arbitrario",
            "render-debug",
        ],
        "docs/guides/es/estudiantes/index.md": [
            "presentacion visual",
            "no cambia",
            "enlaces",
        ],
        "docs/guides/es/agentes/index.md": [
            "`data-raya-skin`",
            "`skin.css`",
            "`_raya/skin.yaml`",
            "render-debug",
        ],
    }
    for relative_path, needles in required.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{relative_path} must mention {needle}"

    professor_profile_needles = (
        "tokens:",
        "color:",
        "font:",
        "density:",
        "accent_soft",
    )
    for relative_path in (
        "docs/guides/en/professors/index.md",
        "docs/guides/es/profesores/index.md",
    ):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for needle in professor_profile_needles:
            assert needle in text, f"{relative_path} must include profile {needle}"
        assert "skin: practice-lab" not in text or "id: practice-lab" in text, (
            f"{relative_path} must define practice-lab before selecting it"
        )


def test_role_docs_cover_learning_science_course_shell() -> None:
    required = {
        "docs/guides/en/professors/index.md": [
            "learning-science",
            "course shell",
            "retrieval practice",
            "prerequisites",
        ],
        "docs/guides/en/contributors/index.md": [
            "learning renderer contract",
            "current",
            "planned",
            "future",
            "no browser-side MathJax",
        ],
        "docs/guides/en/students/index.md": [
            "course map",
            "learning rail",
            "OpenDyslexic",
            "personal progress",
        ],
        "docs/guides/en/agents/index.md": [
            "course shell",
            "right learning rail",
            "no inferred goals",
            "render-debug",
        ],
        "docs/guides/es/profesores/index.md": [
            "ciencia del aprendizaje",
            "estructura del curso",
            "practica de recuperacion",
            "prerrequisitos",
        ],
        "docs/guides/es/colaboradores/index.md": [
            "contrato del renderizador de aprendizaje",
            "current",
            "planned",
            "future",
            "MathJax",
        ],
        "docs/guides/es/estudiantes/index.md": [
            "mapa del curso",
            "riel de aprendizaje",
            "OpenDyslexic",
            "progreso personal",
        ],
        "docs/guides/es/agentes/index.md": [
            "estructura del curso",
            "riel derecho",
            "metas inferidas",
            "render-debug",
        ],
    }
    for relative_path, needles in required.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{relative_path} must mention {needle}"


def test_docs_cover_collapsible_learning_shell() -> None:
    required = {
        "docs/foundation/20_learning_renderer_contract.md": [
            "expanded course map",
            "compact map rail",
            "non-persistent",
            "not hover-triggered",
            "Page N of M",
            "no personal progress",
        ],
        "docs/guides/en/professors/index.md": [
            "expanded course map",
            "compact map rail",
            "non-persistent",
            "Page N of M",
            "not personal progress",
        ],
        "docs/guides/en/contributors/index.md": [
            "expanded course map",
            "compact map rail",
            "non-persistent",
            "explicit-click",
            "aria-expanded",
            "local renderer resources",
        ],
        "docs/guides/en/students/index.md": [
            "expanded course map",
            "compact map rail",
            "non-persistent",
            "Previous",
            "Next",
            "OpenDyslexic",
        ],
        "docs/guides/en/agents/index.md": [
            "expanded course map",
            "non-persistent",
            "no external requests",
            "render-debug",
        ],
        "docs/guides/es/profesores/index.md": [
            "mapa del curso expandido",
            "riel compacto",
            "no persistente",
            "Page N of M",
            "no es progreso personal",
        ],
        "docs/guides/es/colaboradores/index.md": [
            "mapa del curso expandido",
            "riel compacto",
            "no persistente",
            "click explicito",
            "aria-expanded",
            "recursos locales del renderer",
        ],
        "docs/guides/es/estudiantes/index.md": [
            "mapa del curso expandido",
            "riel compacto",
            "no persistente",
            "Anterior",
            "Siguiente",
            "OpenDyslexic",
        ],
        "docs/guides/es/agentes/index.md": [
            "mapa del curso expandido",
            "no persistente",
            "sin solicitudes externas",
            "render-debug",
        ],
    }
    for relative_path, needles in required.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{relative_path} must mention {needle}"


def test_math_authoring_guidance_and_theorem_handoff_are_documented() -> None:
    professor_paths = (
        ROOT / "docs" / "guides" / "en" / "professors" / "index.md",
        ROOT / "docs" / "guides" / "es" / "profesores" / "index.md",
    )
    student_paths = (
        ROOT / "docs" / "guides" / "en" / "students" / "index.md",
        ROOT / "docs" / "guides" / "es" / "estudiantes" / "index.md",
    )
    contributor_paths = (
        ROOT / "docs" / "guides" / "en" / "contributors" / "index.md",
        ROOT / "docs" / "guides" / "es" / "colaboradores" / "index.md",
    )
    agent_paths = (
        ROOT / "docs" / "guides" / "en" / "agents" / "index.md",
        ROOT / "docs" / "guides" / "es" / "agentes" / "index.md",
    )

    for path in professor_paths:
        text = path.read_text(encoding="utf-8")
        assert "2_math_authoring/0_index.md" in text
        assert "\\begin{bmatrix}" in text
        assert "\\newcommand" in text
        assert "\\renewcommand" in text
        assert "theorem" in text.lower()

    for path in student_paths:
        text = path.read_text(encoding="utf-8")
        assert "\\begin{bmatrix}" in text
        assert "unknown macro" in text or "macro desconocida" in text
        assert "browser-side MathJax" in text

    for path in contributor_paths:
        text = path.read_text(encoding="utf-8")
        assert "2_math_authoring/0_index.md" in text
        assert "scripts/check-render-debug.sh" in text
        assert "report.json" in text
        assert "theorem" in text.lower()

    for path in agent_paths:
        text = path.read_text(encoding="utf-8")
        assert "2_math_authoring/0_index.md" in text
        assert "artifact/" in text
        assert "raw" in text.lower() and "TeX" in text
        assert "theorem" in text.lower()


def test_role_docs_cover_numbered_objects_and_references() -> None:
    foundation = (ROOT / "docs/foundation/17_rendering_execution_plan.md").read_text(
        encoding="utf-8"
    )
    for needle in [
        "`remark`",
        "`scannable`",
        "`solution`",
        "`hint`",
        "`answer`",
        "course-level",
        "page/section",
        "do not appear in `data/numbered-objects.json`",
    ]:
        assert needle in foundation, f"foundation rendering plan must mention {needle}"

    required = {
        "docs/guides/en/professors/index.md": [
            "::: theorem",
            "::: problem",
            "`remark`",
            "`scannable`",
            "`solution`",
            "`hint`",
            "`answer`",
            "`caption`",
            "`equation`",
            "course-level",
            "page/section",
            "not numbered objects",
            "any numbered object",
            '::: hint {#hint-',
            '::: solution {#solution-',
            '::: answer {#answer-',
            "`@id` shorthand",
            "`raya:ref/id`",
            "Do not write LaTeX `\\label` or `\\ref`",
        ],
        "docs/guides/en/students/index.md": [
            "`Theorem 2.3.1`",
            "`Figure 2.3.1`",
            "`scannable`",
            "`caption`",
            "`equation`",
            "labels, anchors, and references",
            "static links",
        ],
        "docs/guides/en/contributors/index.md": [
            "render.numbered_objects",
            "`remark`",
            "`scannable`",
            "`caption`",
            "`equation`",
            "reader-ux",
            "static environments",
            "`@id` shorthand references",
            "`raya:ref/id` explicit references",
            "data/numbered-objects.json",
            "anchors, hrefs, and reference text",
            "no browser-side MathJax",
        ],
        "docs/guides/en/agents/index.md": [
            "`@id` shorthand references",
            "`raya:ref/id` explicit references",
            "data/numbered-objects.json",
            "reader-ux",
            "`scannable`",
            "`caption`",
            "`equation`",
            "rendered page anchor",
            "when `of` is present",
            "instead of looking for LaTeX `\\label` or `\\ref` support",
        ],
        "docs/guides/es/profesores/index.md": [
            "::: theorem",
            "::: problem",
            "`remark`",
            "`scannable`",
            "`solution`",
            "`hint`",
            "`answer`",
            "`caption`",
            "`equation`",
            "nivel de curso",
            "pagina/seccion",
            "no son objetos numerados",
            "cualquier objeto numerado",
            '::: hint {#hint-',
            '::: solution {#solution-',
            '::: answer {#answer-',
            "forma abreviada `@id`",
            "enlaces `raya:ref/id`",
            "referencias cruzadas de Raya",
        ],
        "docs/guides/es/estudiantes/index.md": [
            "`Teorema 2.3.1`",
            "`Figura 2.3.1`",
            "`scannable`",
            "`caption`",
            "`equation`",
            "anchors y referencias",
            "enlaces estaticos",
        ],
        "docs/guides/es/colaboradores/index.md": [
            "render.numbered_objects",
            "`remark`",
            "`scannable`",
            "`caption`",
            "`equation`",
            "reader-ux",
            "entornos estaticos",
            "referencias abreviadas `@id`",
            "referencias explicitas `raya:ref/id`",
            "data/numbered-objects.json",
            "anchors, hrefs y texto de referencia",
            "MathJax en el navegador",
        ],
        "docs/guides/es/agentes/index.md": [
            "referencias abreviadas `@id`",
            "referencias explicitas `raya:ref/id`",
            "data/numbered-objects.json",
            "reader-ux",
            "entornos estaticos",
            "`scannable`",
            "`caption`",
            "`equation`",
            "ancla renderizada",
            "si `of` esta presente",
            "en vez de buscar soporte LaTeX `\\label` o `\\ref`",
        ],
    }
    for relative_path, needles in required.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{relative_path} must mention {needle}"


def test_role_docs_cover_proof_blocks() -> None:
    authoring_docs = [
        Path("docs/guides/en/professors/index.md"),
        Path("docs/guides/en/contributors/index.md"),
        Path("docs/guides/en/agents/index.md"),
        Path("docs/guides/es/profesores/index.md"),
        Path("docs/guides/es/colaboradores/index.md"),
        Path("docs/guides/es/agentes/index.md"),
    ]

    for path in authoring_docs:
        text = path.read_text(encoding="utf-8")
        assert "::: proof" in text, path
        assert 'of="' in text, path

    en_students = Path("docs/guides/en/students/index.md").read_text(encoding="utf-8")
    assert "proof headings" in en_students
    assert "browser-side MathJax" in en_students
    assert "::: proof" not in en_students

    es_students = Path("docs/guides/es/estudiantes/index.md").read_text(
        encoding="utf-8"
    )
    assert "encabezados" in es_students
    assert "browser-side MathJax" in es_students
    assert "::: proof" not in es_students


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
