from __future__ import annotations

from pathlib import Path

from raya_schema import ValidationReport
from raya_static.skins import (
    DEFAULT_SKIN_ID,
    SkinContext,
    SkinProfile,
    SectionSkinSelector,
    load_skin_context,
    render_skin_css,
    skin_id_for_source_path,
)


def test_unknown_default_skin_reports_error_and_falls_back(
    tmp_path: Path,
) -> None:
    course = tmp_path
    source_root = course / "course"
    source_root.mkdir()
    report = ValidationReport(context="skin-test")

    context = load_skin_context(
        course,
        {"render": {"skin": "missing-skin"}},
        source_root=source_root,
        report=report,
    )

    assert context.default_skin_id == DEFAULT_SKIN_ID
    assert any(
        diagnostic.message == "Unknown render skin 'missing-skin'"
        and diagnostic.field == "render.skin"
        for diagnostic in report.diagnostics
    )


def test_invalid_skin_profile_id_reports_error_and_is_not_loaded(
    tmp_path: Path,
) -> None:
    course = tmp_path
    source_root = course / "course"
    source_root.mkdir()
    skins_dir = course / "skins"
    skins_dir.mkdir()
    (skins_dir / "Bad_Skin.yaml").write_text(
        _skin_yaml("Bad_Skin"),
        encoding="utf-8",
    )
    report = ValidationReport(context="skin-test")

    context = load_skin_context(
        course,
        {},
        source_root=source_root,
        report=report,
    )

    assert "Bad_Skin" not in context.profiles
    assert any(
        diagnostic.field == "id" and "Invalid skin ID" in diagnostic.message
        for diagnostic in report.diagnostics
    )


def test_invalid_utf8_skin_yaml_reports_error_without_raising(
    tmp_path: Path,
) -> None:
    course = tmp_path
    source_root = course / "course"
    source_root.mkdir()
    skins_dir = course / "skins"
    skins_dir.mkdir()
    (skins_dir / "broken.yaml").write_bytes(b"\xff\xfe\x00")
    report = ValidationReport(context="skin-test")

    context = load_skin_context(
        course,
        {},
        source_root=source_root,
        report=report,
    )

    assert context.default_skin_id == DEFAULT_SKIN_ID
    assert any(
        diagnostic.message == "Unable to read skin profile YAML"
        and diagnostic.path == skins_dir / "broken.yaml"
        for diagnostic in report.diagnostics
    )


def test_nearest_section_selector_resolution(tmp_path: Path) -> None:
    source_root = tmp_path / "course"
    parent = source_root / "1_parent"
    child = parent / "2_child"
    page = child / "0_index.md"
    page.parent.mkdir(parents=True)
    page.write_text("# Child\n", encoding="utf-8")
    context = SkinContext(
        default_skin_id=DEFAULT_SKIN_ID,
        profiles={},
        section_selectors=(
            SectionSkinSelector(
                section_dir=parent,
                skin_id="parent-skin",
                source_path=parent / "_raya" / "skin.yaml",
            ),
            SectionSkinSelector(
                section_dir=child,
                skin_id="child-skin",
                source_path=child / "_raya" / "skin.yaml",
            ),
        ),
    )

    assert skin_id_for_source_path(page, context) == "child-skin"


def test_render_skin_css_is_deterministic_and_writes_token_variables() -> None:
    context = SkinContext(
        default_skin_id=DEFAULT_SKIN_ID,
        profiles={
            "z-skin": _profile("z-skin", accent="#222222"),
            "a-skin": _profile("a-skin", accent="#111111"),
        },
        section_selectors=(),
    )

    css = render_skin_css(context)

    assert css.index('[data-raya-skin="a-skin"]') < css.index(
        '[data-raya-skin="z-skin"]'
    )
    assert "--raya-color-page: #ffffff;" in css
    assert "--raya-color-accent: #111111;" in css
    assert "--raya-font-body: system-ui;" in css
    assert "--raya-density: comfortable;" in css


def _skin_yaml(skin_id: str) -> str:
    return (
        f"id: {skin_id}\n"
        "name: Test Skin\n"
        "tokens:\n"
        "  color:\n"
        '    page: "#ffffff"\n'
        '    surface: "#f6f8fa"\n'
        '    text: "#1f2328"\n'
        '    muted: "#57606a"\n'
        '    accent: "#0969da"\n'
        '    accent_soft: "#ddf4ff"\n'
        '    border: "#d0d7de"\n'
        '    success: "#1a7f37"\n'
        '    warning: "#9a6700"\n'
        '    danger: "#cf222e"\n'
        "  font:\n"
        '    body: "system-ui"\n'
        '    heading: "system-ui"\n'
        '    mono: "ui-monospace"\n'
        "  density: comfortable\n"
    )


def _profile(skin_id: str, *, accent: str) -> SkinProfile:
    return SkinProfile(
        id=skin_id,
        name=skin_id,
        colors={
            "page": "#ffffff",
            "surface": "#f6f8fa",
            "text": "#1f2328",
            "muted": "#57606a",
            "accent": accent,
            "accent_soft": "#ddf4ff",
            "border": "#d0d7de",
            "success": "#1a7f37",
            "warning": "#9a6700",
            "danger": "#cf222e",
        },
        fonts={
            "body": "system-ui",
            "heading": "system-ui",
            "mono": "ui-monospace",
        },
        density="comfortable",
    )
