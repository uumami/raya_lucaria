from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from raya_schema import ValidationReport


SKIN_STYLESHEET_PATH = "_raya/render/skin.css"
DEFAULT_SKIN_ID = "raya-default"
REQUIRED_COLOR_TOKENS = (
    "page",
    "surface",
    "text",
    "muted",
    "accent",
    "accent_soft",
    "border",
    "success",
    "warning",
    "danger",
)
REQUIRED_FONT_TOKENS = ("body", "heading", "mono")
REQUIRED_GRAPH_TOKENS = (
    "group_1",
    "group_2",
    "group_3",
    "group_4",
    "group_5",
    "group_6",
    "group_7",
    "group_8",
)
ALLOWED_PROFILE_FIELDS = frozenset({"id", "name", "tokens"})
ALLOWED_TOKEN_GROUPS = frozenset({"color", "font", "graph", "density"})
ALLOWED_DENSITIES = frozenset({"comfortable", "compact", "spacious"})
ALLOWED_FONT_STACKS = frozenset(
    {
        "system-ui",
        "serif",
        "sans-serif",
        "ui-monospace",
        "monospace",
    }
)
DENSITY_SPACING = {
    "compact": {
        "page": "0.75rem",
        "panel": "0.75rem",
        "block": "0.85rem",
        "inline": "0.5rem",
    },
    "comfortable": {
        "page": "1rem",
        "panel": "1rem",
        "block": "1rem",
        "inline": "0.75rem",
    },
    "spacious": {
        "page": "1.5rem",
        "panel": "1.25rem",
        "block": "1.5rem",
        "inline": "1rem",
    },
}
DEFAULT_GRAPH_COLORS = (
    "var(--raya-color-accent)",
    "var(--raya-color-success)",
    "color-mix(in srgb, var(--raya-color-accent) 68%, var(--raya-color-success))",
    "color-mix(in srgb, var(--raya-color-success) 70%, var(--raya-color-text))",
    "color-mix(in srgb, var(--raya-color-accent) 58%, var(--raya-color-text))",
    (
        "color-mix(in srgb, var(--raya-color-success) 52%, "
        "var(--raya-color-accent-soft))"
    ),
    "color-mix(in srgb, var(--raya-color-accent) 44%, var(--raya-color-surface))",
    "color-mix(in srgb, var(--raya-color-success) 44%, var(--raya-color-surface))",
)
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
SKIN_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


@dataclass(frozen=True)
class SkinProfile:
    id: str
    name: str
    colors: dict[str, str]
    fonts: dict[str, str]
    density: str
    graph_colors: dict[str, str] | None = None
    source_path: Path | None = None


@dataclass(frozen=True)
class SectionSkinSelector:
    section_dir: Path
    skin_id: str
    source_path: Path


@dataclass(frozen=True)
class SkinContext:
    default_skin_id: str
    profiles: dict[str, SkinProfile]
    section_selectors: tuple[SectionSkinSelector, ...]


BUILT_IN_SKINS = {
    DEFAULT_SKIN_ID: SkinProfile(
        id=DEFAULT_SKIN_ID,
        name="Raya Default",
        colors={
            "page": "#f7f8fa",
            "surface": "#ffffff",
            "text": "#24292f",
            "muted": "#57606a",
            "accent": "#0969da",
            "accent_soft": "#ddf4ff",
            "border": "#d8dee4",
            "success": "#1a7f37",
            "warning": "#9a6700",
            "danger": "#cf222e",
        },
        fonts={
            "body": "system-ui",
            "heading": "system-ui",
            "mono": "ui-monospace",
        },
        graph_colors=None,
        density="comfortable",
    )
}


def load_skin_context(
    course_root: Path,
    course_config: dict[str, Any],
    *,
    source_root: Path,
    report: ValidationReport,
) -> SkinContext:
    profiles = dict(BUILT_IN_SKINS)
    _load_course_skin_profiles(course_root, profiles, report)

    default_skin_id = _course_default_skin_id(
        course_config,
        path=course_root / "raya.yaml",
        report=report,
    )
    if default_skin_id != DEFAULT_SKIN_ID and not _valid_skin_id(default_skin_id):
        _report_invalid_skin_id(
            report,
            default_skin_id,
            path=course_root / "raya.yaml",
            field="render.skin",
        )
        default_skin_id = DEFAULT_SKIN_ID
    elif default_skin_id not in profiles:
        _report_unknown_skin(
            report,
            default_skin_id,
            path=course_root / "raya.yaml",
            field="render.skin",
            profiles=profiles,
        )
        default_skin_id = DEFAULT_SKIN_ID

    selectors = _load_section_skin_selectors(
        source_root,
        profiles=profiles,
        report=report,
    )
    return SkinContext(
        default_skin_id=default_skin_id,
        profiles=profiles,
        section_selectors=tuple(selectors),
    )


def _course_default_skin_id(
    course_config: dict[str, Any],
    *,
    path: Path,
    report: ValidationReport,
) -> str:
    render = course_config.get("render")
    if not isinstance(render, dict):
        return DEFAULT_SKIN_ID
    if "skin" not in render:
        return DEFAULT_SKIN_ID
    skin_id = render.get("skin")
    if not isinstance(skin_id, str) or not skin_id.strip():
        report.add_error(
            "render.skin must be a non-empty string",
            path=path,
            field="render.skin",
            next_action="Set render.skin to a skin profile ID such as warm-academic.",
        )
        return DEFAULT_SKIN_ID
    return skin_id


def _load_course_skin_profiles(
    course_root: Path,
    profiles: dict[str, SkinProfile],
    report: ValidationReport,
) -> None:
    skins_dir = course_root / "skins"
    if not skins_dir.is_dir():
        return

    for path in sorted(skins_dir.glob("*.yaml")):
        report.read_file(path)
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, OSError) as exc:
            report.add_error(
                "Unable to read skin profile YAML",
                path=path,
                next_action=f"Check that the file exists and is valid UTF-8: {exc}",
            )
            continue
        except yaml.YAMLError as exc:
            report.add_error(
                "Invalid skin profile YAML",
                path=path,
                next_action=f"Fix YAML syntax: {exc}",
            )
            continue
        profile = _parse_skin_profile(raw, path=path, report=report)
        if profile is None:
            continue
        if profile.id in profiles:
            report.add_error(
                f"Duplicate skin profile ID '{profile.id}'",
                path=path,
                field="id",
                next_action="Use a unique skin profile ID and filename",
            )
            continue
        profiles[profile.id] = profile


def _parse_skin_profile(
    raw: Any,
    *,
    path: Path,
    report: ValidationReport,
) -> SkinProfile | None:
    if not isinstance(raw, dict):
        report.add_error(
            "Skin profile must be a mapping",
            path=path,
            next_action="Define id, name, and tokens in the skin YAML file",
        )
        return None
    _validate_allowed_keys(
        raw,
        allowed=ALLOWED_PROFILE_FIELDS,
        path=path,
        field_prefix="",
        label="Skin profile",
        report=report,
    )

    skin_id = raw.get("id")
    if not isinstance(skin_id, str) or not skin_id.strip():
        report.add_error(
            "Skin profile is missing a string ID",
            path=path,
            field="id",
            next_action="Set id to the skin filename stem",
        )
        return None
    if not _valid_skin_id(skin_id):
        _report_invalid_skin_id(report, skin_id, path=path, field="id")
        return None
    if skin_id != path.stem:
        report.add_error(
            f"Skin profile ID '{skin_id}' must match filename '{path.stem}'",
            path=path,
            field="id",
            next_action="Rename the file or update the id field so they match",
        )
        return None

    name = raw.get("name")
    if not isinstance(name, str) or not name.strip():
        report.add_error(
            "Skin profile is missing a string name",
            path=path,
            field="name",
            next_action="Set name to a human-readable skin name",
        )
        return None

    tokens = raw.get("tokens")
    if not isinstance(tokens, dict):
        report.add_error(
            "Skin profile tokens must be a mapping",
            path=path,
            field="tokens",
            next_action="Define tokens.color, tokens.font, and tokens.density",
        )
        return None
    _validate_allowed_keys(
        tokens,
        allowed=ALLOWED_TOKEN_GROUPS,
        path=path,
        field_prefix="tokens",
        label="Skin profile tokens",
        report=report,
    )

    colors = _required_string_map(
        tokens.get("color"),
        required=REQUIRED_COLOR_TOKENS,
        path=path,
        field="tokens.color",
        report=report,
    )
    fonts = _required_string_map(
        tokens.get("font"),
        required=REQUIRED_FONT_TOKENS,
        path=path,
        field="tokens.font",
        report=report,
    )
    graph_colors = None
    if "graph" in tokens:
        graph_colors = _required_string_map(
            tokens.get("graph"),
            required=REQUIRED_GRAPH_TOKENS,
            path=path,
            field="tokens.graph",
            report=report,
        )
    _validate_colors(colors, path=path, report=report)
    if graph_colors is not None:
        _validate_colors(
            graph_colors,
            path=path,
            report=report,
            field_prefix="tokens.graph",
        )
    _validate_contrast(colors, path=path, report=report)
    _validate_fonts(fonts, path=path, report=report)

    density = tokens.get("density")
    if not isinstance(density, str) or density not in ALLOWED_DENSITIES:
        report.add_error(
            "Skin profile density is invalid",
            path=path,
            field="tokens.density",
            next_action=(
                "Use one of: " + ", ".join(sorted(ALLOWED_DENSITIES))
            ),
        )

    if any(
        diagnostic.severity == "error" and diagnostic.path == path
        for diagnostic in report.diagnostics
    ):
        return None

    return SkinProfile(
        id=skin_id,
        name=name,
        colors=colors,
        fonts=fonts,
        graph_colors=graph_colors,
        density=density,
        source_path=path,
    )


def _required_string_map(
    raw: Any,
    *,
    required: tuple[str, ...],
    path: Path,
    field: str,
    report: ValidationReport,
) -> dict[str, str]:
    if not isinstance(raw, dict):
        report.add_error(
            "Skin token group must be a mapping",
            path=path,
            field=field,
            next_action=f"Define required keys: {', '.join(required)}",
        )
        return {}
    allowed = frozenset(required)
    _validate_allowed_keys(
        raw,
        allowed=allowed,
        path=path,
        field_prefix=field,
        label="Skin token group",
        report=report,
    )

    values: dict[str, str] = {}
    for key in required:
        value = raw.get(key)
        token_field = f"{field}.{key}"
        if not isinstance(value, str) or not value:
            report.add_error(
                f"Skin token '{key}' must be a non-empty string",
                path=path,
                field=token_field,
                next_action=f"Set {token_field} to a supported value",
            )
            continue
        values[key] = value
    return values


def _validate_allowed_keys(
    raw: dict[Any, Any],
    *,
    allowed: frozenset[str],
    path: Path,
    field_prefix: str,
    label: str,
    report: ValidationReport,
) -> None:
    for key in sorted(raw, key=str):
        if key in allowed:
            continue
        field = f"{field_prefix}.{key}" if field_prefix else str(key)
        if label == "Skin token group":
            message = f"{label} contains unsupported key '{key}'"
        elif label == "Skin profile tokens":
            message = f"{label} contain unsupported field '{key}'"
        else:
            message = f"{label} contains unsupported field '{key}'"
        report.add_error(
            message,
            path=path,
            field=field,
            next_action=(
                "Remove this field. V1 skins only support semantic tokens, "
                "not arbitrary CSS or extra style fields."
            ),
        )


def _validate_colors(
    colors: dict[str, str],
    *,
    path: Path,
    report: ValidationReport,
    field_prefix: str = "tokens.color",
) -> None:
    for key, value in colors.items():
        if not HEX_COLOR_RE.match(value):
            report.add_error(
                f"Skin color token '{key}' must be a 6-digit hex color",
                path=path,
                field=f"{field_prefix}.{key}",
                next_action='Use a value like "#0969da"',
            )


def _relative_luminance(hex_color: str) -> float:
    value = hex_color.lstrip("#")
    channels = [int(value[index : index + 2], 16) / 255 for index in (0, 2, 4)]
    linear = [
        channel / 12.92
        if channel <= 0.03928
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(first: str, second: str) -> float:
    first_lum = _relative_luminance(first)
    second_lum = _relative_luminance(second)
    lighter = max(first_lum, second_lum)
    darker = min(first_lum, second_lum)
    return (lighter + 0.05) / (darker + 0.05)


def _validate_contrast(
    colors: dict[str, str],
    *,
    path: Path,
    report: ValidationReport,
) -> None:
    pairs = (
        ("text", "page"),
        ("accent", "page"),
        ("text", "accent_soft"),
    )
    for foreground, background in pairs:
        if foreground not in colors or background not in colors:
            continue
        if not HEX_COLOR_RE.match(colors[foreground]) or not HEX_COLOR_RE.match(
            colors[background]
        ):
            continue
        ratio = _contrast_ratio(colors[foreground], colors[background])
        if ratio < 4.5:
            report.add_error(
                (
                    f"Skin contrast for {foreground} on {background} is too low "
                    f"({ratio:.2f}:1)"
                ),
                path=path,
                field=f"tokens.color.{foreground}",
                next_action=(
                    f"Choose colors for tokens.color.{foreground} and "
                    f"tokens.color.{background} with at least 4.5:1 contrast."
                ),
            )


def _validate_fonts(
    fonts: dict[str, str],
    *,
    path: Path,
    report: ValidationReport,
) -> None:
    for key, value in fonts.items():
        if value not in ALLOWED_FONT_STACKS:
            report.add_error(
                f"Skin font token '{key}' is not supported",
                path=path,
                field=f"tokens.font.{key}",
                next_action=(
                    "Use one of: " + ", ".join(sorted(ALLOWED_FONT_STACKS))
                ),
            )


def _load_section_skin_selectors(
    source_root: Path,
    *,
    profiles: dict[str, SkinProfile],
    report: ValidationReport,
) -> list[SectionSkinSelector]:
    selectors: list[SectionSkinSelector] = []
    for path in sorted(source_root.glob("**/_raya/skin.yaml")):
        report.read_file(path)
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, OSError) as exc:
            report.add_error(
                "Unable to read section skin selector YAML",
                path=path,
                next_action=f"Check that the file exists and is valid UTF-8: {exc}",
            )
            continue
        except yaml.YAMLError as exc:
            report.add_error(
                "Invalid section skin selector YAML",
                path=path,
                next_action=f"Fix YAML syntax: {exc}",
            )
            continue

        section_dir = path.parent.parent
        if not (section_dir / "0_index.md").is_file():
            report.add_error(
                "_raya/skin.yaml must live beside a section 0_index.md",
                path=path,
                next_action="Move _raya/skin.yaml under a section directory",
            )
            continue

        skin_id = _selector_skin_id(raw)
        if skin_id is None:
            report.add_error(
                "Section skin selector is missing render.skin",
                path=path,
                field="render.skin",
                next_action="Set render.skin to a known skin profile ID",
            )
            continue
        if not _valid_skin_id(skin_id):
            _report_invalid_skin_id(report, skin_id, path=path, field="render.skin")
            continue
        if skin_id not in profiles:
            _report_unknown_skin(
                report,
                skin_id,
                path=path,
                field="render.skin",
                profiles=profiles,
            )
            continue
        selectors.append(
            SectionSkinSelector(
                section_dir=section_dir,
                skin_id=skin_id,
                source_path=path,
            )
        )
    return selectors


def _selector_skin_id(raw: Any) -> str | None:
    if not isinstance(raw, dict):
        return None
    render = raw.get("render")
    if not isinstance(render, dict):
        return None
    skin_id = render.get("skin")
    if not isinstance(skin_id, str) or not skin_id.strip():
        return None
    return skin_id


def _valid_skin_id(skin_id: str) -> bool:
    return bool(SKIN_ID_RE.match(skin_id))


def _report_invalid_skin_id(
    report: ValidationReport,
    skin_id: str,
    *,
    path: Path,
    field: str,
) -> None:
    report.add_error(
        f"Invalid skin ID '{skin_id}'",
        path=path,
        field=field,
        next_action="Use lowercase letters, numbers, and hyphens; start with a letter or number",
    )


def _report_unknown_skin(
    report: ValidationReport,
    skin_id: str,
    *,
    path: Path,
    field: str,
    profiles: dict[str, SkinProfile],
) -> None:
    report.add_error(
        f"Unknown render skin '{skin_id}'",
        path=path,
        field=field,
        next_action="Use one of: " + ", ".join(sorted(profiles)),
    )


def skin_id_for_source_path(source_path: Path, context: SkinContext) -> str:
    resolved_source = source_path.resolve()
    best_selector: SectionSkinSelector | None = None
    for selector in context.section_selectors:
        section_dir = selector.section_dir.resolve()
        try:
            resolved_source.relative_to(section_dir)
        except ValueError:
            continue
        if best_selector is None:
            best_selector = selector
            continue
        if len(section_dir.parts) > len(best_selector.section_dir.resolve().parts):
            best_selector = selector
    if best_selector is not None:
        return best_selector.skin_id
    return context.default_skin_id


def render_skin_css(context: SkinContext) -> str:
    blocks: list[str] = []
    for skin_id in sorted(context.profiles):
        profile = context.profiles[skin_id]
        selector = _css_escape_identifier(skin_id)
        lines = [
            f'[data-raya-skin="{selector}"] {{',
        ]
        for key in REQUIRED_COLOR_TOKENS:
            lines.append(f"  --raya-color-{key.replace('_', '-')}: {profile.colors[key]};")
        for key in REQUIRED_FONT_TOKENS:
            lines.append(f"  --raya-font-{key}: {profile.fonts[key]};")
        if profile.graph_colors is not None:
            for index, key in enumerate(REQUIRED_GRAPH_TOKENS, start=1):
                lines.append(
                    f"  --raya-graph-group-{index}: {profile.graph_colors[key]};"
                )
        else:
            for index, value in enumerate(DEFAULT_GRAPH_COLORS, start=1):
                lines.append(f"  --raya-graph-group-{index}: {value};")
        lines.append(f"  --raya-density: {profile.density};")
        for key, value in DENSITY_SPACING[profile.density].items():
            lines.append(f"  --raya-space-{key}: {value};")
        lines.append("}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n"


def _css_escape_identifier(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
