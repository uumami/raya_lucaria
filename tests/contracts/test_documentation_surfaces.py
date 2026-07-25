from __future__ import annotations

import json
import shutil
from pathlib import Path

from raya_static import build_course


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "openspec" / "config.yaml"
SPECS = ROOT / "openspec" / "specs"
DOCS_ROOT = ROOT / "docs"
GUIDES = ROOT / "docs" / "guides"
DOCS_FIXTURE = ROOT / "examples" / "docs" / "documentation-fixture"

ROLE_PAGES = {
    "en": ("contributors", "professors", "students", "agents"),
    "es": ("colaboradores", "profesores", "estudiantes", "agentes"),
}


def test_current_specs_have_meaningful_purpose_text() -> None:
    for spec in sorted(SPECS.glob("*/spec.md")):
        text = spec.read_text(encoding="utf-8")

        assert "## Purpose" in text, f"{spec} is missing a Purpose section"
        assert "Purpose\nTBD" not in text, f"{spec} has a placeholder Purpose"
        assert "TBD - created by archiving" not in text, (
            f"{spec} has a generated placeholder Purpose"
        )

        purpose = text.split("## Purpose", 1)[1].split("## Requirements", 1)[0].strip()
        assert len(purpose) >= 40, f"{spec} Purpose is too thin"


def test_openspec_config_requires_role_documentation_impact() -> None:
    text = CONFIG.read_text(encoding="utf-8")

    assert "contributors/collaborators, professors, students, and agents" in text
    assert "documentation impact" in text
    assert "documentation tasks" in text
    assert "separate English and Spanish role-documentation directories" in text
    assert "Purpose: TBD" in text


def test_role_documentation_uses_separate_english_and_spanish_pages() -> None:
    for language, pages in ROLE_PAGES.items():
        index = GUIDES / language / "index.md"
        assert index.exists(), f"missing {index}"
        for page in pages:
            path = GUIDES / language / page / "index.md"
            assert path.exists(), f"missing {path}"
            text = path.read_text(encoding="utf-8")
            assert "docs/foundation/" in text
            assert "OpenSpec" in text
            assert "## English" not in text
            assert "## Espanol" not in text

    assert not (GUIDES / "en" / "colaboradores" / "index.md").exists()
    assert not (GUIDES / "es" / "contributors" / "index.md").exists()


def test_guidance_surfaces_allow_user_selected_superpowers_renderer_loops() -> None:
    required = {
        "docs/foundation/13_truth_surfaces.md": [
            "Superpowers design and plan documents",
            "user explicitly selects that workflow",
            "OpenSpec remains an accepted workflow",
        ],
        "docs/foundation/16_documentation_surfaces.md": [
            "Superpowers design and plan documents",
            "OpenSpec remains an accepted workflow",
        ],
        "docs/foundation/17_rendering_execution_plan.md": [
            "Superpowers",
            "science-backed course shell",
            "OpenSpec remains available",
        ],
        "README.md": [
            "Superpowers",
            "OpenSpec remains available",
            "docs/foundation/",
        ],
        "AGENTS.md": [
            "Superpowers",
            "OpenSpec remains available",
            "docs/foundation/",
        ],
        "openspec/config.yaml": [
            "Superpowers",
            "OpenSpec remains available",
            "docs/foundation/",
        ],
        "docs/guides/en/contributors/index.md": [
            "Superpowers",
            "OpenSpec remains available",
        ],
        "docs/guides/en/agents/index.md": [
            "Superpowers",
            "OpenSpec remains available",
        ],
        "docs/guides/es/colaboradores/index.md": [
            "Superpowers",
            "OpenSpec sigue disponible",
            "documentos de diseno y plan de Superpowers versionados",
            "superficies afectadas de foundation, rol, test y contrato",
        ],
        "docs/guides/es/agentes/index.md": [
            "Superpowers",
            "OpenSpec sigue disponible",
            "documentos de diseno y plan de Superpowers versionados",
            "superficies afectadas de foundation, rol, test y contrato",
        ],
    }
    for relative_path, needles in required.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{relative_path} must mention {needle}"


def test_implemented_superpowers_ux_plans_are_marked_as_completed_records() -> None:
    implemented_plan_paths = (
        "docs/superpowers/plans/2026-06-26-course-map-keyboard-navigation.md",
        "docs/superpowers/plans/2026-06-26-discovery-context-actions.md",
        "docs/superpowers/plans/2026-06-26-discovery-fuzzy-matching-parity.md",
        "docs/superpowers/plans/2026-06-25-graph-skin-palette.md",
        "docs/superpowers/plans/2026-06-25-graph-workspace-comfort.md",
        "docs/superpowers/plans/2026-06-26-discovery-guided-controls.md",
        "docs/superpowers/plans/2026-06-26-discovery-workspace-panel-collapse.md",
        "docs/superpowers/plans/2026-06-26-discovery-workspace-reset-parity.md",
        "docs/superpowers/plans/2026-06-26-discovery-workspace-grouped-controls.md",
        "docs/superpowers/plans/2026-06-26-discovery-workspace-switcher.md",
        "docs/superpowers/plans/2026-06-26-discovery-workspace-comfort-parity.md",
        "docs/superpowers/plans/2026-06-26-graph-reading-keys.md",
        "docs/superpowers/plans/2026-06-26-legacy-ux-convergence-audit.md",
        "docs/superpowers/plans/2026-06-26-review-gallery-dashboard.md",
    )
    for relative_path in implemented_plan_paths:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "Status: implemented" in text, (
            f"{relative_path} should identify its checklist as historical "
            "after the UX convergence work lands"
        )


def test_role_documentation_covers_renderer_skins_and_accessibility() -> None:
    needles = {
        "docs/guides/en/professors/index.md": ["render.skin", "skins/", "eva-unit-02"],
        "docs/guides/en/contributors/index.md": [
            "semantic tokens",
            "arbitrary CSS",
            "no CDN",
        ],
        "docs/guides/en/students/index.md": ["OpenDyslexic", "reading preference"],
        "docs/guides/en/agents/index.md": [
            "OpenDyslexic",
            "external font",
            "static parity",
        ],
        "docs/guides/es/profesores/index.md": ["render.skin", "skins/", "eva-unit-02"],
        "docs/guides/es/colaboradores/index.md": [
            "tokens semanticos",
            "CSS arbitrario",
            "CDN",
        ],
        "docs/guides/es/estudiantes/index.md": [
            "OpenDyslexic",
            "preferencia de lectura",
        ],
        "docs/guides/es/agentes/index.md": [
            "OpenDyslexic",
            "fuente externa",
            "paridad estatica",
        ],
    }
    for relative_path, expected in needles.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for needle in expected:
            assert needle in text


def test_student_docs_cover_constrained_graph_node_repositioning() -> None:
    required = {
        "docs/foundation/20_learning_renderer_contract.md": [
            "temporarily reposition visible SVG graph nodes",
            "must not persist to browser storage",
            "must not mutate URL state",
            "must not imply recommendation, ranking, progress, mastery, or authority",
        ],
        "docs/guides/en/students/index.md": [
            "reposition visible graph nodes",
            "Reset graph restores the generated layout",
            "not a layout editor",
            "course-data change",
            "saved preference",
            "recommendation, progress, mastery, or authority signal",
        ],
        "docs/guides/es/estudiantes/index.md": [
            "reposicionar nodos visibles del grafo",
            "Reset graph restaura el layout generado",
            "no es un editor de layout",
            "cambio de datos del curso",
            "preferencia guardada",
            "recomendacion, progreso, dominio ni senal de autoridad",
        ],
    }
    for relative_path, needles in required.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{relative_path} must mention {needle}"


def test_rendered_documentation_fixture_is_labeled_and_separate() -> None:
    assert DOCS_FIXTURE.exists()
    assert DOCS_FIXTURE.relative_to(ROOT).parts[:2] == ("examples", "docs")
    assert DOCS_FIXTURE.relative_to(ROOT).parts[:3] != ("examples", "courses", "minimal")

    markdown = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((DOCS_FIXTURE / "course").rglob("*.md"))
    )
    assert "documentation fixture material" in markdown
    assert "not class material" in markdown
    assert "docs/foundation/" in markdown
    assert "docs/guides/en/" in markdown
    assert "docs/guides/es/" in markdown


def test_rendered_documentation_fixture_keeps_role_languages_separate() -> None:
    english = DOCS_FIXTURE / "course" / "1_en" / "1_contributors" / "0_index.md"
    spanish = DOCS_FIXTURE / "course" / "2_es" / "1_colaboradores" / "0_index.md"

    assert english.exists()
    assert spanish.exists()
    assert "Contributors" in english.read_text(encoding="utf-8")
    assert "Colaboradores" in spanish.read_text(encoding="utf-8")
    assert "Colaboradores" not in english.read_text(encoding="utf-8")
    assert "Contributors" not in spanish.read_text(encoding="utf-8")


def test_current_documentation_tree_is_a_renderable_docs_course(
    tmp_path: Path,
) -> None:
    source = tmp_path / "docs"
    shutil.copytree(DOCS_ROOT, source, ignore=shutil.ignore_patterns("artifact"))

    report = build_course(source)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    artifact = source / "artifact"
    pages = json.loads((artifact / "data" / "pages.json").read_text(encoding="utf-8"))
    page_ids = {item["quantum_id"] for item in pages["pages"]}
    assert "docs-foundation" in page_ids
    assert "docs-system-overview" in page_ids
    assert "docs-guides-en-contributors" in page_ids
    assert "docs-guides-es-colaboradores" in page_ids

    navigation = json.loads(
        (artifact / "data" / "navigation.json").read_text(encoding="utf-8")
    )
    assert navigation["root"] == "docs-root"
    urls = {item["url"] for item in navigation["items"]}
    assert "foundation/system-overview/index.html" in urls
    assert "guides/en/contributors/index.html" in urls
    assert "guides/es/colaboradores/index.html" in urls

    indices = json.loads((artifact / "data" / "indices.json").read_text(encoding="utf-8"))
    assert [item["id"] for item in indices["master"]] == [
        "docs-foundation",
        "docs-guides",
    ]


def test_current_documentation_render_content_points_to_real_docs() -> None:
    render_content = DOCS_ROOT / "render-content"
    assert (DOCS_ROOT / "raya.yaml").exists()
    assert (render_content / "0_index.md").is_symlink()
    assert (render_content / "1_foundation" / "0_index.md").resolve() == (
        DOCS_ROOT / "foundation" / "00_index.md"
    ).resolve()
    assert (
        render_content / "2_guides" / "1_en" / "1_contributors" / "0_index.md"
    ).resolve() == (DOCS_ROOT / "guides" / "en" / "contributors" / "index.md").resolve()


def test_learning_science_foundation_pages_are_rendered() -> None:
    learning = DOCS_ROOT / "foundation" / "19_learning_science_principles.md"
    contract = DOCS_ROOT / "foundation" / "20_learning_renderer_contract.md"
    assert learning.exists()
    assert contract.exists()

    learning_text = learning.read_text(encoding="utf-8")
    contract_text = contract.read_text(encoding="utf-8")
    for needle in (
        "## Cognitive Load",
        "## Coherence, Signaling, And Segmenting",
        "## Retrieval Practice",
        "## Spaced Practice And Interleaving",
        "## Worked Examples And Fading",
        "## Self-Explanation",
        "## Metacognition And Calibration",
        "## Motivation, Autonomy, Relevance, And Belonging",
        "## Universal Design And Accessibility",
        "## Static HTML Boundary",
        "reduce extraneous load",
        "authored checkpoint prompts",
        "Current static pages can ask calibration questions",
        "meaningful choice",
        "semantic HTML",
    ):
        assert needle in learning_text
    for inventory in (
        "The core phrases for this contract are",
        "The full learning-science surface also includes",
    ):
        assert inventory not in learning_text
    for needle in (
        "`current`",
        "`planned`",
        "`future`",
        "course shell",
        "right learning rail",
        "no personal progress",
        "no browser-side MathJax",
        "no external CSS, font, script, renderer, or CDN requests",
        "no hidden schema change",
        "raw `summary` or `status`",
        "Related practice index",
        "Personal progress, analytics, adaptive review, spaced queues",
    ):
        assert needle in contract_text

    index = (DOCS_ROOT / "foundation" / "00_index.md").read_text(encoding="utf-8")
    assert "19_learning_science_principles.md" in index
    assert "20_learning_renderer_contract.md" in index

    render_content = DOCS_ROOT / "render-content" / "1_foundation"
    assert (render_content / "19_learning_science_principles.md").resolve() == learning.resolve()
    assert (render_content / "20_learning_renderer_contract.md").resolve() == contract.resolve()


def test_discovery_context_actions_are_documented() -> None:
    contract = DOCS_ROOT / "foundation" / "20_learning_renderer_contract.md"
    student_guide = DOCS_ROOT / "guides" / "en" / "students" / "index.md"
    spanish_student_guide = DOCS_ROOT / "guides" / "es" / "estudiantes" / "index.md"

    assert "context panels may expose static action links" in contract.read_text(
        encoding="utf-8"
    )
    assert "Context panels may also show direct static links" in student_guide.read_text(
        encoding="utf-8"
    )
    assert "Los paneles de contexto tambien pueden mostrar links estaticos directos" in (
        spanish_student_guide.read_text(encoding="utf-8")
    )


def test_discovery_workspace_fuzzy_filters_are_documented() -> None:
    contract = DOCS_ROOT / "foundation" / "20_learning_renderer_contract.md"
    student_guide = DOCS_ROOT / "guides" / "en" / "students" / "index.md"
    spanish_student_guide = DOCS_ROOT / "guides" / "es" / "estudiantes" / "index.md"

    contract_text = contract.read_text(encoding="utf-8")
    assert "approximate text matching over public fields" in contract_text
    assert "help find likely public results despite small spelling mistakes" in contract_text
    assert "not ranking, personalization, or recommendation" in contract_text

    student_text = student_guide.read_text(encoding="utf-8")
    assert "Text filters may tolerate small spelling mistakes" in student_text
    assert "not ranking, personalization, or recommendation" in student_text

    spanish_text = spanish_student_guide.read_text(encoding="utf-8")
    assert "Los filtros de texto pueden tolerar errores pequenos" in spanish_text
    assert "no ranking, personalizacion" in spanish_text


def test_reader_rail_visual_parity_truth_surfaces_agree() -> None:
    paths = {
        "foundation": ROOT / "docs/foundation/20_learning_renderer_contract.md",
        "student_en": ROOT / "docs/guides/en/students/index.md",
        "student_es": ROOT / "docs/guides/es/estudiantes/index.md",
        "agent_en": ROOT / "docs/guides/en/agents/index.md",
        "agent_es": ROOT / "docs/guides/es/agentes/index.md",
    }
    text = {name: path.read_text(encoding="utf-8") for name, path in paths.items()}

    for name in paths:
        assert "Expand course map" in text[name], name
    for name in ("foundation", "student_en", "agent_en"):
        assert "Hide map" in text[name], name
        assert "Search, Graph, Practice, Tasks, Schedule, Context, Text size, and OpenDyslexic" in text[name], name
    for name in ("student_es", "agent_es"):
        assert "Hide map" in text[name], name
        assert "Search, Graph, Practice, Tasks, Schedule, Context, Text size y OpenDyslexic" in text[name], name

    assert "header Map action" in text["agent_en"]
    assert "accion Map del header" in text["agent_es"]
    assert "all nine actions as body tiles" not in text["foundation"]

    # Rail home control is part of the amended header enumeration.
    assert "course-home action" in text["foundation"]
    assert "ten reader actions" in text["foundation"]
