from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "openspec" / "config.yaml"
SPECS = ROOT / "openspec" / "specs"
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


def test_rendered_documentation_fixture_is_labeled_and_separate() -> None:
    assert DOCS_FIXTURE.exists()
    assert DOCS_FIXTURE.relative_to(ROOT).parts[:2] == ("examples", "docs")
    assert DOCS_FIXTURE.relative_to(ROOT).parts[:3] != ("examples", "courses", "minimal")

    markdown = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((DOCS_FIXTURE / "content").rglob("*.md"))
    )
    assert "documentation fixture material" in markdown
    assert "not class material" in markdown
    assert "docs/foundation/" in markdown
    assert "docs/guides/en/" in markdown
    assert "docs/guides/es/" in markdown


def test_rendered_documentation_fixture_keeps_role_languages_separate() -> None:
    english = DOCS_FIXTURE / "content" / "en" / "contributors" / "00_index.md"
    spanish = DOCS_FIXTURE / "content" / "es" / "colaboradores" / "00_index.md"

    assert english.exists()
    assert spanish.exists()
    assert "Contributors" in english.read_text(encoding="utf-8")
    assert "Colaboradores" in spanish.read_text(encoding="utf-8")
    assert "Colaboradores" not in english.read_text(encoding="utf-8")
    assert "Contributors" not in spanish.read_text(encoding="utf-8")
