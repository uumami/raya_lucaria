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
from raya_static.rendering import rich_render_css


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


def test_render_fixture_uses_eva_unit_02_default_and_emits_new_skin_selectors() -> None:
    import yaml

    fixture = Path("examples/courses/render-fixture")
    config = yaml.safe_load((fixture / "raya.yaml").read_text(encoding="utf-8"))
    report = ValidationReport(context="skin-test")

    context = load_skin_context(
        fixture,
        config,
        source_root=fixture / "course",
        report=report,
    )
    css = render_skin_css(context)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    assert context.default_skin_id == "eva-unit-02"
    for skin_id in (
        "eva-unit-02",
        "eva-unit-01",
        "eva-unit-03",
        "ghost-in-the-shell",
    ):
        assert f'[data-raya-skin="{skin_id}"]' in css
    assert "--raya-color-page: #f6f7f9;" in css
    assert "--raya-color-surface: #ffffff;" in css
    assert "--raya-color-accent: #d92323;" in css
    assert "--raya-color-accent-soft: #fff0ec;" in css
    assert "--raya-color-border: #d8dee4;" in css


def test_invalid_default_skin_type_reports_error(
    tmp_path: Path,
) -> None:
    course = tmp_path
    source_root = course / "course"
    source_root.mkdir()
    report = ValidationReport(context="skin-test")

    context = load_skin_context(
        course,
        {"render": {"skin": 123}},
        source_root=source_root,
        report=report,
    )

    assert context.default_skin_id == DEFAULT_SKIN_ID
    assert any(
        diagnostic.message == "render.skin must be a non-empty string"
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


def test_duplicate_skin_profile_id_reports_error_and_keeps_original(
    tmp_path: Path,
) -> None:
    course = tmp_path
    source_root = course / "course"
    source_root.mkdir()
    skins_dir = course / "skins"
    skins_dir.mkdir()
    skin_path = skins_dir / f"{DEFAULT_SKIN_ID}.yaml"
    skin_path.write_text(
        _skin_yaml(DEFAULT_SKIN_ID),
        encoding="utf-8",
    )
    report = ValidationReport(context="skin-test")

    context = load_skin_context(
        course,
        {"render": {"skin": DEFAULT_SKIN_ID}},
        source_root=source_root,
        report=report,
    )

    assert context.profiles[DEFAULT_SKIN_ID].name == "Raya Default"
    assert context.profiles[DEFAULT_SKIN_ID].source_path is None
    assert any(
        diagnostic.message == f"Duplicate skin profile ID '{DEFAULT_SKIN_ID}'"
        and diagnostic.field == "id"
        and diagnostic.path == skin_path
        and "unique skin profile ID" in diagnostic.next_action
        for diagnostic in report.diagnostics
    )


def test_skin_profile_filename_id_mismatch_reports_error_and_is_not_loaded(
    tmp_path: Path,
) -> None:
    course = tmp_path
    source_root = course / "course"
    source_root.mkdir()
    skins_dir = course / "skins"
    skins_dir.mkdir()
    skin_path = skins_dir / "filename-skin.yaml"
    skin_path.write_text(
        _skin_yaml("profile-skin"),
        encoding="utf-8",
    )
    report = ValidationReport(context="skin-test")

    context = load_skin_context(
        course,
        {"render": {"skin": "profile-skin"}},
        source_root=source_root,
        report=report,
    )

    assert "profile-skin" not in context.profiles
    assert context.default_skin_id == DEFAULT_SKIN_ID
    assert any(
        diagnostic.message
        == "Skin profile ID 'profile-skin' must match filename 'filename-skin'"
        and diagnostic.field == "id"
        and diagnostic.path == skin_path
        and "match" in diagnostic.next_action
        for diagnostic in report.diagnostics
    )


def test_skin_profile_rejects_unsupported_css_fields(tmp_path: Path) -> None:
    course = tmp_path
    source_root = course / "course"
    source_root.mkdir()
    skins_dir = course / "skins"
    skins_dir.mkdir()
    skin_path = skins_dir / "unsupported.yaml"
    skin_path.write_text(
        _skin_yaml("unsupported").replace(
            "tokens:\n",
            'css: "body { color: red; }"\n'
            "tokens:\n"
            '  css: "body { color: red; }"\n',
        ),
        encoding="utf-8",
    )
    report = ValidationReport(context="skin-test")

    context = load_skin_context(
        course,
        {"render": {"skin": "unsupported"}},
        source_root=source_root,
        report=report,
    )

    assert "unsupported" not in context.profiles
    assert any(
        diagnostic.message == "Skin profile contains unsupported field 'css'"
        and diagnostic.field == "css"
        for diagnostic in report.diagnostics
    )
    assert any(
        diagnostic.message == "Skin profile tokens contain unsupported field 'css'"
        and diagnostic.field == "tokens.css"
        for diagnostic in report.diagnostics
    )


def test_skin_profile_rejects_extra_token_keys(tmp_path: Path) -> None:
    course = tmp_path
    source_root = course / "course"
    source_root.mkdir()
    skins_dir = course / "skins"
    skins_dir.mkdir()
    skin_path = skins_dir / "extra-token.yaml"
    skin_path.write_text(
        _skin_yaml("extra-token").replace(
            '    danger: "#cf222e"\n',
            '    danger: "#cf222e"\n'
            '    custom: "#000000"\n',
        ),
        encoding="utf-8",
    )
    report = ValidationReport(context="skin-test")

    context = load_skin_context(
        course,
        {"render": {"skin": "extra-token"}},
        source_root=source_root,
        report=report,
    )

    assert "extra-token" not in context.profiles
    assert any(
        diagnostic.message == "Skin token group contains unsupported key 'custom'"
        and diagnostic.field == "tokens.color.custom"
        for diagnostic in report.diagnostics
    )


def test_invalid_skin_profile_density_reports_error_and_is_not_loaded(
    tmp_path: Path,
) -> None:
    course = tmp_path
    source_root = course / "course"
    source_root.mkdir()
    skins_dir = course / "skins"
    skins_dir.mkdir()
    skin_path = skins_dir / "dense-skin.yaml"
    skin_path.write_text(
        _skin_yaml("dense-skin").replace(
            "  density: comfortable\n",
            "  density: dense\n",
        ),
        encoding="utf-8",
    )
    report = ValidationReport(context="skin-test")

    context = load_skin_context(
        course,
        {"render": {"skin": "dense-skin"}},
        source_root=source_root,
        report=report,
    )

    assert "dense-skin" not in context.profiles
    assert context.default_skin_id == DEFAULT_SKIN_ID
    assert any(
        diagnostic.message == "Skin profile density is invalid"
        and diagnostic.field == "tokens.density"
        and diagnostic.path == skin_path
        and "comfortable" in diagnostic.next_action
        and "compact" in diagnostic.next_action
        and "spacious" in diagnostic.next_action
        for diagnostic in report.diagnostics
    )


def test_unsupported_skin_profile_font_stack_reports_error_and_is_not_loaded(
    tmp_path: Path,
) -> None:
    course = tmp_path
    source_root = course / "course"
    source_root.mkdir()
    skins_dir = course / "skins"
    skins_dir.mkdir()
    skin_path = skins_dir / "font-skin.yaml"
    skin_path.write_text(
        _skin_yaml("font-skin").replace(
            '    body: "system-ui"\n',
            '    body: "Georgia, serif"\n',
        ),
        encoding="utf-8",
    )
    report = ValidationReport(context="skin-test")

    context = load_skin_context(
        course,
        {"render": {"skin": "font-skin"}},
        source_root=source_root,
        report=report,
    )

    assert "font-skin" not in context.profiles
    assert context.default_skin_id == DEFAULT_SKIN_ID
    assert any(
        diagnostic.message == "Skin font token 'body' is not supported"
        and diagnostic.field == "tokens.font.body"
        and diagnostic.path == skin_path
        and "system-ui" in diagnostic.next_action
        and "ui-monospace" in diagnostic.next_action
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


def test_low_contrast_skin_profile_reports_error_and_is_not_loaded(
    tmp_path: Path,
) -> None:
    course = tmp_path
    source_root = course / "course"
    source_root.mkdir()
    skins_dir = course / "skins"
    skins_dir.mkdir()
    skin_path = skins_dir / "low-contrast.yaml"
    skin_path.write_text(
        _skin_yaml("low-contrast").replace(
            'text: "#1f2328"',
            'text: "#ffffff"',
        ),
        encoding="utf-8",
    )
    report = ValidationReport(context="skin-test")

    context = load_skin_context(
        course,
        {"render": {"skin": "low-contrast"}},
        source_root=source_root,
        report=report,
    )

    assert "low-contrast" not in context.profiles
    assert context.default_skin_id == DEFAULT_SKIN_ID
    assert any(
        diagnostic.message.startswith("Skin contrast for text on page is too low")
        and diagnostic.field == "tokens.color.text"
        and diagnostic.path == skin_path
        and "tokens.color.text" in diagnostic.next_action
        and "tokens.color.page" in diagnostic.next_action
        for diagnostic in report.diagnostics
    )


def test_malformed_color_reports_token_error_without_contrast_crash(
    tmp_path: Path,
) -> None:
    course = tmp_path
    source_root = course / "course"
    source_root.mkdir()
    skins_dir = course / "skins"
    skins_dir.mkdir()
    skin_path = skins_dir / "bad-color.yaml"
    skin_path.write_text(
        _skin_yaml("bad-color").replace(
            'page: "#ffffff"',
            'page: "white"',
        ),
        encoding="utf-8",
    )
    report = ValidationReport(context="skin-test")

    context = load_skin_context(
        course,
        {"render": {"skin": "bad-color"}},
        source_root=source_root,
        report=report,
    )

    assert "bad-color" not in context.profiles
    assert context.default_skin_id == DEFAULT_SKIN_ID
    assert any(
        diagnostic.message == "Skin color token 'page' must be a 6-digit hex color"
        and diagnostic.field == "tokens.color.page"
        and diagnostic.path == skin_path
        for diagnostic in report.diagnostics
    )
    assert not any(
        "contrast" in diagnostic.message.lower()
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


def test_section_selector_missing_render_skin_reports_error_and_is_not_loaded(
    tmp_path: Path,
) -> None:
    course = tmp_path
    source_root = course / "course"
    section = source_root / "1_section"
    selector_dir = section / "_raya"
    selector_dir.mkdir(parents=True)
    (section / "0_index.md").write_text("# Section\n", encoding="utf-8")
    selector_path = selector_dir / "skin.yaml"
    selector_path.write_text("render: {}\n", encoding="utf-8")
    report = ValidationReport(context="skin-test")

    context = load_skin_context(
        course,
        {},
        source_root=source_root,
        report=report,
    )

    assert context.section_selectors == ()
    assert any(
        diagnostic.message == "Section skin selector is missing render.skin"
        and diagnostic.field == "render.skin"
        and diagnostic.path == selector_path
        and "render.skin" in diagnostic.next_action
        for diagnostic in report.diagnostics
    )


def test_section_selector_unknown_render_skin_reports_error_and_is_not_loaded(
    tmp_path: Path,
) -> None:
    course = tmp_path
    source_root = course / "course"
    section = source_root / "1_section"
    selector_dir = section / "_raya"
    selector_dir.mkdir(parents=True)
    (section / "0_index.md").write_text("# Section\n", encoding="utf-8")
    selector_path = selector_dir / "skin.yaml"
    selector_path.write_text(
        "render:\n"
        "  skin: missing-skin\n",
        encoding="utf-8",
    )
    report = ValidationReport(context="skin-test")

    context = load_skin_context(
        course,
        {},
        source_root=source_root,
        report=report,
    )

    assert context.section_selectors == ()
    assert any(
        diagnostic.message == "Unknown render skin 'missing-skin'"
        and diagnostic.field == "render.skin"
        and diagnostic.path == selector_path
        and "Use one of:" in diagnostic.next_action
        and DEFAULT_SKIN_ID in diagnostic.next_action
        for diagnostic in report.diagnostics
    )


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
    assert "data-raya-skin-override" not in css
    assert "--raya-color-page: #ffffff;" in css
    assert "--raya-color-accent: #111111;" in css
    assert "--raya-font-body: system-ui;" in css
    assert "--raya-font-heading: system-ui;" in css
    assert "--raya-font-mono: ui-monospace;" in css
    assert "--raya-density: comfortable;" in css
    assert "--raya-space-page: 1rem;" in css


def test_render_skin_css_maps_density_to_spacing_variables() -> None:
    context = SkinContext(
        default_skin_id=DEFAULT_SKIN_ID,
        profiles={
            "compact-skin": SkinProfile(
                id="compact-skin",
                name="Compact Skin",
                colors=_profile("compact-skin", accent="#111111").colors,
                fonts=_profile("compact-skin", accent="#111111").fonts,
                density="compact",
            ),
            "spacious-skin": SkinProfile(
                id="spacious-skin",
                name="Spacious Skin",
                colors=_profile("spacious-skin", accent="#111111").colors,
                fonts=_profile("spacious-skin", accent="#111111").fonts,
                density="spacious",
            ),
        },
        section_selectors=(),
    )

    css = render_skin_css(context)

    assert '[data-raya-skin="compact-skin"]' in css
    assert "--raya-space-page: 0.75rem;" in css
    assert "--raya-space-block: 0.85rem;" in css
    assert "--raya-space-page: 1.5rem;" in css
    assert "--raya-space-block: 1.5rem;" in css


def test_rich_render_css_consumes_font_and_density_tokens() -> None:
    css = rich_render_css()

    assert "font-family: var(--raya-font-heading)" in css
    assert "font-family: var(--raya-font-mono)" in css
    assert "padding: var(--raya-space-page)" in css
    assert "gap: var(--raya-space-block)" in css


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
