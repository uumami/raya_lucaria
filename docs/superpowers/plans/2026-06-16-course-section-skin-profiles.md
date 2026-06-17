# Course And Section Skin Profiles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add validated course-level and section-level skin profiles that decouple visual tokens from static rendering structure.

**Architecture:** Add a focused `raya_static.skins` module for loading, validating, resolving, and emitting skin CSS variables. Keep `rendering.py` responsible for semantic HTML/classes and structural CSS, but replace hardcoded visual values with CSS variables. `builder.py` wires course and section skin resolution into generated pages, writes `_raya/render/skin.css`, and keeps static deployment/browser preview parity.

**Tech Stack:** Python 3.10, YAML course metadata, `pytest`, Playwright/Chromium e2e checks, Glintstone static builder, existing `ValidationReport` diagnostics, no browser-side theme resolver.

---

## File Structure

- Create: `packages/static/src/raya_static/skins.py`
  - Owns built-in skin definitions, token dataclasses, YAML loading, validation, section selector loading, page skin resolution, and `skin.css` generation.
- Modify: `packages/static/src/raya_static/rendering.py`
  - Keep HTML rendering here. Tokenize `rich_render_css()` by replacing visual hardcoded colors/fonts with CSS variables.
- Modify: `packages/static/src/raya_static/builder.py`
  - Load skin context after course validation, write `skin.css`, link it on normal pages and inspection pages, and add `data-raya-skin` to rendered page bodies.
- Modify: `packages/cli/src/raya_cli/render_debug.py`
  - Capture active page skin IDs from rendered pages.
- Modify: `packages/cli/src/raya_cli/render_debug_report.py`
  - Validate skin evidence and local `skin.css` presence in render-debug reports.
- Modify: `tests/contracts/test_static_builder.py`
  - Add temporary-course tests for course default skin, section inheritance, diagnostics, and generated CSS.
- Modify: `tests/e2e/test_preview_static_read_path.py`
  - Add browser/static-read-path assertions for active skin IDs and local skin CSS.
- Modify: `tests/e2e/test_render_debug_report.py`
  - Add render-debug report assertions for skin evidence.
- Modify: `tests/contracts/test_renderer_dependencies.py`
  - Add documentation contract needles for EN/ES skin guidance.
- Modify: `examples/courses/render-fixture/raya.yaml`
  - Select a course-level skin for the render fixture.
- Create: `examples/courses/render-fixture/skins/warm-academic.yaml`
- Create: `examples/courses/render-fixture/skins/practice-lab.yaml`
- Create: `examples/courses/render-fixture/course/4_reader_ux/_raya/skin.yaml`
  - Demonstrates section-level skin emphasis on a realistic unit.
- Modify: `docs/foundation/17_rendering_execution_plan.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`

## Task 1: Skin Model And Validation Contract

**Files:**
- Create: `packages/static/src/raya_static/skins.py`
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add failing tests for course skin validation**

Append these tests near other temporary-course build diagnostics in `tests/contracts/test_static_builder.py`:

```python
def test_build_applies_course_skin_to_pages_and_writes_skin_css(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    config = course / "raya.yaml"
    config.write_text(
        config.read_text(encoding="utf-8")
        + "\nrender:\n  skin: warm-academic\n",
        encoding="utf-8",
    )
    skins_dir = course / "skins"
    skins_dir.mkdir()
    (skins_dir / "warm-academic.yaml").write_text(
        "id: warm-academic\n"
        "name: Warm Academic\n"
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
        "  density: comfortable\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    index_html = (course / "artifact" / "site" / "index.html").read_text(
        encoding="utf-8"
    )
    skin_css = (course / "artifact" / "site" / "_raya" / "render" / "skin.css")
    assert 'data-raya-skin="warm-academic"' in index_html
    assert '<link rel="stylesheet" href="_raya/render/skin.css">' in index_html
    assert skin_css.exists()
    assert '[data-raya-skin="warm-academic"]' in skin_css.read_text(
        encoding="utf-8"
    )
```

Add the first invalid diagnostic test:

```python
def test_build_fails_for_unknown_course_skin(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    config = course / "raya.yaml"
    config.write_text(
        config.read_text(encoding="utf-8")
        + "\nrender:\n  skin: missing-skin\n",
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    messages = [diagnostic.format() for diagnostic in report.diagnostics]
    assert any("Unknown render skin 'missing-skin'" in message for message in messages)
    assert any("render.skin" in message for message in messages)
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py::test_build_applies_course_skin_to_pages_and_writes_skin_css \
  tests/contracts/test_static_builder.py::test_build_fails_for_unknown_course_skin \
  -q
```

Expected: FAIL because `render.skin` is ignored, no `skin.css` is written, and no skin diagnostics exist.

- [ ] **Step 3: Create `skins.py` with token dataclasses and built-in fallback**

Create `packages/static/src/raya_static/skins.py` with:

```python
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
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


@dataclass(frozen=True)
class SkinProfile:
    id: str
    name: str
    colors: dict[str, str]
    fonts: dict[str, str]
    density: str
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


BUILT_IN_SKINS: dict[str, SkinProfile] = {
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
        density="comfortable",
    )
}
```

- [ ] **Step 4: Add skin loading and validation functions**

Continue `skins.py` with:

```python
def load_skin_context(
    course_root: Path,
    course_config: dict[str, Any],
    *,
    source_root: Path,
    report: ValidationReport,
) -> SkinContext:
    profiles = dict(BUILT_IN_SKINS)
    _load_course_skin_profiles(course_root, profiles, report)
    default_skin_id = _course_default_skin_id(course_config)
    if default_skin_id not in profiles:
        _report_unknown_skin(
            report,
            default_skin_id,
            path=course_root / "raya.yaml",
            field="render.skin",
            profiles=profiles,
        )
        default_skin_id = DEFAULT_SKIN_ID
    section_selectors = _load_section_skin_selectors(
        source_root,
        profiles=profiles,
        report=report,
    )
    return SkinContext(
        default_skin_id=default_skin_id,
        profiles=profiles,
        section_selectors=tuple(section_selectors),
    )


def _course_default_skin_id(course_config: dict[str, Any]) -> str:
    render = course_config.get("render")
    if not isinstance(render, dict):
        return DEFAULT_SKIN_ID
    skin = render.get("skin", DEFAULT_SKIN_ID)
    return skin if isinstance(skin, str) and skin else DEFAULT_SKIN_ID


def _load_course_skin_profiles(
    course_root: Path,
    profiles: dict[str, SkinProfile],
    report: ValidationReport,
) -> None:
    skins_dir = course_root / "skins"
    if not skins_dir.exists():
        return
    for path in sorted(skins_dir.glob("*.yaml")):
        report.read_file(path)
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        profile = _parse_skin_profile(raw, path=path, report=report)
        if profile is None:
            continue
        if profile.id in profiles:
            report.error(
                f"Duplicate render skin ID '{profile.id}'",
                path=path,
                field="id",
                next_action="Use a unique skin id or remove the duplicate skin file.",
            )
            continue
        profiles[profile.id] = profile
```

Add `_parse_skin_profile()` and helpers:

```python
def _parse_skin_profile(
    raw: Any,
    *,
    path: Path,
    report: ValidationReport,
) -> SkinProfile | None:
    if not isinstance(raw, dict):
        report.error(
            "Skin profile must be a YAML mapping",
            path=path,
            field="skin",
            next_action="Use id, name, and tokens fields.",
        )
        return None
    skin_id = raw.get("id")
    if not isinstance(skin_id, str) or not skin_id:
        report.error(
            "Skin profile is missing id",
            path=path,
            field="id",
            next_action="Set id to match the skin filename stem.",
        )
        return None
    if skin_id != path.stem:
        report.error(
            f"Skin profile id '{skin_id}' must match filename '{path.stem}'",
            path=path,
            field="id",
            next_action=f"Rename the file or set id: {path.stem}.",
        )
        return None
    name = raw.get("name", skin_id)
    if not isinstance(name, str) or not name:
        name = skin_id
    tokens = raw.get("tokens")
    if not isinstance(tokens, dict):
        report.error(
            "Skin profile is missing tokens",
            path=path,
            field="tokens",
            next_action="Define color, font, and density tokens.",
        )
        return None
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
    density = tokens.get("density")
    if not isinstance(density, str) or density not in ALLOWED_DENSITIES:
        report.error(
            f"Skin profile uses invalid density '{density}'",
            path=path,
            field="tokens.density",
            next_action="Use comfortable, compact, or spacious.",
        )
        density = "comfortable"
    _validate_colors(colors, path=path, report=report)
    _validate_fonts(fonts, path=path, report=report)
    if not report.ok:
        return None
    return SkinProfile(
        id=skin_id,
        name=name,
        colors=colors,
        fonts=fonts,
        density=density,
        source_path=path,
    )
```

Add map/color/font helpers:

```python
def _required_string_map(
    raw: Any,
    *,
    required: tuple[str, ...],
    path: Path,
    field: str,
    report: ValidationReport,
) -> dict[str, str]:
    if not isinstance(raw, dict):
        report.error(
            f"Skin profile is missing {field}",
            path=path,
            field=field,
            next_action=f"Define required keys: {', '.join(required)}.",
        )
        return {}
    result: dict[str, str] = {}
    for key in required:
        value = raw.get(key)
        if not isinstance(value, str) or not value:
            report.error(
                f"Skin profile is missing {field}.{key}",
                path=path,
                field=f"{field}.{key}",
                next_action=f"Set {field}.{key} to a non-empty string.",
            )
            continue
        result[key] = value
    return result


def _validate_colors(colors: dict[str, str], *, path: Path, report: ValidationReport) -> None:
    for key, value in colors.items():
        if HEX_COLOR_RE.match(value) is None:
            report.error(
                f"Skin color token '{key}' uses invalid hex color '{value}'",
                path=path,
                field=f"tokens.color.{key}",
                next_action='Use a six-digit hex color such as "#0969da".',
            )


def _validate_fonts(fonts: dict[str, str], *, path: Path, report: ValidationReport) -> None:
    for key, value in fonts.items():
        if value not in ALLOWED_FONT_STACKS:
            report.error(
                f"Skin font token '{key}' uses unsupported font stack '{value}'",
                path=path,
                field=f"tokens.font.{key}",
                next_action=(
                    "Use system-ui, serif, sans-serif, ui-monospace, or monospace."
                ),
            )
```

- [ ] **Step 5: Add section selector loading and unknown-skin diagnostics**

Continue `skins.py`:

```python
def _load_section_skin_selectors(
    source_root: Path,
    *,
    profiles: dict[str, SkinProfile],
    report: ValidationReport,
) -> list[SectionSkinSelector]:
    selectors: list[SectionSkinSelector] = []
    for path in sorted(source_root.glob("**/_raya/skin.yaml")):
        report.read_file(path)
        section_dir = path.parent.parent
        if not (section_dir / "0_index.md").is_file():
            report.error(
                "_raya/skin.yaml must live beside a section 0_index.md",
                path=path,
                field="render.skin",
                next_action="Move this selector beside a directory page with 0_index.md.",
            )
            continue
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        skin_id = _selector_skin_id(raw)
        if skin_id is None:
            report.error(
                "Section skin selector must define render.skin",
                path=path,
                field="render.skin",
                next_action='Use render: {skin: "skin-id"} or a render.skin mapping.',
            )
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
            SectionSkinSelector(section_dir=section_dir, skin_id=skin_id, source_path=path)
        )
    return selectors


def _selector_skin_id(raw: Any) -> str | None:
    if not isinstance(raw, dict):
        return None
    render = raw.get("render")
    if not isinstance(render, dict):
        return None
    skin = render.get("skin")
    if not isinstance(skin, str) or not skin:
        return None
    return skin


def _report_unknown_skin(
    report: ValidationReport,
    skin_id: str,
    *,
    path: Path,
    field: str,
    profiles: dict[str, SkinProfile],
) -> None:
    available = ", ".join(sorted(profiles))
    report.error(
        f"Unknown render skin '{skin_id}'",
        path=path,
        field=field,
        next_action=f"Use one of: {available}.",
    )
```

- [ ] **Step 6: Add skin resolution and CSS generation**

Continue `skins.py`:

```python
def skin_id_for_source_path(source_path: Path, context: SkinContext) -> str:
    best: SectionSkinSelector | None = None
    for selector in context.section_selectors:
        try:
            source_path.relative_to(selector.section_dir)
        except ValueError:
            continue
        if best is None or len(selector.section_dir.parts) > len(best.section_dir.parts):
            best = selector
    return best.skin_id if best is not None else context.default_skin_id


def render_skin_css(context: SkinContext) -> str:
    blocks = []
    for skin_id in sorted(context.profiles):
        profile = context.profiles[skin_id]
        declarations = [
            f"  --raya-color-{key.replace('_', '-')}: {value};"
            for key, value in profile.colors.items()
        ]
        declarations.extend(
            [
                f"  --raya-font-{key}: {value};"
                for key, value in profile.fonts.items()
            ]
        )
        declarations.append(f"  --raya-density: {profile.density};")
        blocks.append(
            f'[data-raya-skin="{_css_escape_identifier(skin_id)}"] {{\n'
            + "\n".join(declarations)
            + "\n}"
        )
    return "\n\n".join(blocks) + "\n"


def _css_escape_identifier(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
```

- [ ] **Step 7: Run focused tests and verify current failures move forward**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py::test_build_applies_course_skin_to_pages_and_writes_skin_css \
  tests/contracts/test_static_builder.py::test_build_fails_for_unknown_course_skin \
  -q
```

Expected: still FAIL because `builder.py` has not wired the skin context into page rendering or resource writing.

- [ ] **Step 8: Commit parser/validation module**

Commit only after reviewing the diff:

```bash
git add packages/static/src/raya_static/skins.py tests/contracts/test_static_builder.py
git commit -m "Add static skin profile validation"
```

## Task 2: Builder Integration And Structural CSS Tokenization

**Files:**
- Modify: `packages/static/src/raya_static/builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Import skin helpers in `builder.py`**

Modify the imports in `packages/static/src/raya_static/builder.py`:

```python
from raya_static.skins import (
    SKIN_STYLESHEET_PATH,
    SkinContext,
    load_skin_context,
    render_skin_css,
    skin_id_for_source_path,
)
```

- [ ] **Step 2: Load skin context during build**

In `build_course`, after `_validate_rich_markdown_inputs(pages, report)` passes
and before `site_dir = artifact_dir / "site"`, add:

```python
    skin_context = load_skin_context(
        root,
        config,
        source_root=source_dir,
        report=report,
    )
    if not report.ok:
        return report
```

- [ ] **Step 3: Pass skin context into page rendering**

Update `_render_page(...)` signature to include:

```python
    skin_context: SkinContext,
```

Inside `_render_page`, compute:

```python
    skin_id = skin_id_for_source_path(page.source_path, skin_context)
    skin_stylesheet_href = _relative_href(page.output_path, SKIN_STYLESHEET_PATH)
```

Add a skin CSS link after `rich.css`:

```python
            f'<link rel="stylesheet" href="{html.escape(stylesheet_href)}">',
            f'<link rel="stylesheet" href="{html.escape(skin_stylesheet_href)}">',
            f'<link rel="stylesheet" href="{html.escape(math_stylesheet_href)}">',
```

Change the body tag to:

```python
            (
                f'<body data-raya-surface="{SURFACE_STUDENT_DEFAULT}" '
                f'data-raya-skin="{html.escape(skin_id, quote=True)}">'
            ),
```

Update the existing `_render_page(...)` call inside the `for page in pages:` loop
to pass `skin_context=skin_context`.

- [ ] **Step 4: Link skin CSS on inspection pages**

Find the inspection HTML renderer in `builder.py`. Add:

```python
    skin_stylesheet_href = _relative_href(
        STATIC_INSPECTION_PATH,
        SKIN_STYLESHEET_PATH,
    )
```

Add the stylesheet link after `rich.css` and set:

```python
<body data-raya-surface="inspection" data-raya-skin="raya-default">
```

Inspection pages can use the built-in default in v1 because they are audit UI, not course reading content.

- [ ] **Step 5: Write `skin.css` beside `rich.css`**

Change `_write_rich_render_resources` signature:

```python
def _write_rich_render_resources(
    site_dir: Path,
    report: ValidationReport,
    *,
    skin_context: SkinContext,
) -> None:
```

Keep the existing `rich.css` write and add:

```python
    skin_stylesheet = site_dir / SKIN_STYLESHEET_PATH
    skin_stylesheet.parent.mkdir(parents=True, exist_ok=True)
    skin_stylesheet.write_text(render_skin_css(skin_context), encoding="utf-8")
    report.wrote_output(skin_stylesheet)
```

Update the call site:

```python
    _write_rich_render_resources(site_dir, report, skin_context=skin_context)
```

- [ ] **Step 6: Tokenize `rich_render_css()` visual values**

In `packages/static/src/raya_static/rendering.py`, update `rich_render_css()` so baseline visual rules use variables. Start with this mapping:

```css
body {
  background: var(--raya-color-page);
  color: var(--raya-color-text);
  font-family: var(--raya-font-body), -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
a {
  color: var(--raya-color-accent);
}
.raya-site-header,
.raya-article,
.raya-support-stack,
.raya-inspection-main {
  background: var(--raya-color-surface);
  border-color: var(--raya-color-border);
}
.raya-numbered-object-reference,
.raya-numbered-object-badge-label,
.raya-course-nav a[aria-current="page"] {
  color: var(--raya-color-success);
}
.raya-page-footer,
nav[aria-label="Breadcrumbs"],
.raya-proof-title,
.raya-static-environment-title,
.raya-reference-status,
.raya-reviewed-output-status {
  color: var(--raya-color-muted);
}
```

Do not attempt to eliminate every single hardcoded color in one step. Replace the major course-visible values and preserve layout behavior.

- [ ] **Step 7: Run focused tests and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py::test_build_applies_course_skin_to_pages_and_writes_skin_css \
  tests/contracts/test_static_builder.py::test_build_fails_for_unknown_course_skin \
  -q
```

Expected: PASS.

- [ ] **Step 8: Run broader static builder contracts**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -q
```

Expected: PASS.

- [ ] **Step 9: Commit builder and CSS integration**

```bash
git add packages/static/src/raya_static/builder.py packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py
git commit -m "Apply course skin profiles during build"
```

## Task 3: Section Inheritance And Invalid Fixture Coverage

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Create: `examples/courses/invalid/unknown-section-skin/raya.yaml`
- Create: `examples/courses/invalid/unknown-section-skin/course/0_index.md`
- Create: `examples/courses/invalid/unknown-section-skin/course/1_unit/0_index.md`
- Create: `examples/courses/invalid/unknown-section-skin/course/1_unit/_raya/skin.yaml`

- [ ] **Step 1: Add failing section inheritance test**

Add to `tests/contracts/test_static_builder.py`:

```python
def test_build_applies_nearest_section_skin_to_descendant_pages(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    config = course / "raya.yaml"
    config.write_text(
        config.read_text(encoding="utf-8")
        + "\nrender:\n  skin: warm-academic\n",
        encoding="utf-8",
    )
    _write_test_skin(course / "skins" / "warm-academic.yaml", "warm-academic")
    _write_test_skin(course / "skins" / "practice-lab.yaml", "practice-lab")
    selector = course / "course" / "1_unit" / "_raya" / "skin.yaml"
    selector.parent.mkdir(parents=True)
    selector.write_text("render:\n  skin: practice-lab\n", encoding="utf-8")

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    root_html = (course / "artifact" / "site" / "index.html").read_text(
        encoding="utf-8"
    )
    unit_html = (course / "artifact" / "site" / "unit" / "index.html").read_text(
        encoding="utf-8"
    )
    topic_html = (course / "artifact" / "site" / "unit" / "topic" / "index.html").read_text(
        encoding="utf-8"
    )
    assert 'data-raya-skin="warm-academic"' in root_html
    assert 'data-raya-skin="practice-lab"' in unit_html
    assert 'data-raya-skin="practice-lab"' in topic_html
```

Add helper near other test helpers:

```python
def _write_test_skin(path: Path, skin_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"id: {skin_id}\n"
        f"name: {skin_id}\n"
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
        "  density: comfortable\n",
        encoding="utf-8",
    )
```

- [ ] **Step 2: Add failing invalid-token tests**

Add focused tests:

```python
def test_build_fails_for_invalid_skin_color(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    (course / "raya.yaml").write_text(
        (course / "raya.yaml").read_text(encoding="utf-8")
        + "\nrender:\n  skin: broken\n",
        encoding="utf-8",
    )
    _write_test_skin(course / "skins" / "broken.yaml", "broken")
    skin_path = course / "skins" / "broken.yaml"
    skin_path.write_text(
        skin_path.read_text(encoding="utf-8").replace(
            'page: "#ffffff"',
            'page: "white"',
        ),
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    assert any(
        "tokens.color.page" in diagnostic.format()
        for diagnostic in report.diagnostics
    )
```

```python
def test_build_fails_for_section_skin_selector_without_section_index(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    _write_test_skin(course / "skins" / "practice-lab.yaml", "practice-lab")
    selector = course / "course" / "orphan" / "_raya" / "skin.yaml"
    selector.parent.mkdir(parents=True)
    selector.write_text("render:\n  skin: practice-lab\n", encoding="utf-8")

    report = build_course(course)

    assert not report.ok
    assert any(
        "_raya/skin.yaml must live beside a section 0_index.md" in diagnostic.format()
        for diagnostic in report.diagnostics
    )
```

- [ ] **Step 3: Run tests and verify validation behavior**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py::test_build_applies_nearest_section_skin_to_descendant_pages \
  tests/contracts/test_static_builder.py::test_build_fails_for_invalid_skin_color \
  tests/contracts/test_static_builder.py::test_build_fails_for_section_skin_selector_without_section_index \
  -q
```

Expected: PASS. If a test fails, fix only `skins.py` or the test helper added in
this task; do not change builder wiring in this task.

- [ ] **Step 4: Add contrast validation**

In `skins.py`, add helpers:

```python
def _relative_luminance(hex_color: str) -> float:
    value = hex_color.lstrip("#")
    channels = [int(value[index : index + 2], 16) / 255 for index in (0, 2, 4)]
    linear = [
        channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(first: str, second: str) -> float:
    first_lum = _relative_luminance(first)
    second_lum = _relative_luminance(second)
    lighter = max(first_lum, second_lum)
    darker = min(first_lum, second_lum)
    return (lighter + 0.05) / (darker + 0.05)


def _validate_contrast(colors: dict[str, str], *, path: Path, report: ValidationReport) -> None:
    pairs = (
        ("text", "page"),
        ("accent", "page"),
        ("text", "accent_soft"),
    )
    for foreground, background in pairs:
        if foreground not in colors or background not in colors:
            continue
        ratio = _contrast_ratio(colors[foreground], colors[background])
        if ratio < 4.5:
            report.error(
                (
                    f"Skin contrast for {foreground} on {background} is too low "
                    f"({ratio:.2f}:1)"
                ),
                path=path,
                field=f"tokens.color.{foreground}",
                next_action="Choose colors with at least 4.5:1 contrast.",
            )
```

Call it after `_validate_colors(...)`.

- [ ] **Step 5: Add contrast test**

Add:

```python
def test_build_fails_for_low_contrast_skin(tmp_path: Path) -> None:
    course = _copy_minimal(tmp_path)
    (course / "raya.yaml").write_text(
        (course / "raya.yaml").read_text(encoding="utf-8")
        + "\nrender:\n  skin: low-contrast\n",
        encoding="utf-8",
    )
    _write_test_skin(course / "skins" / "low-contrast.yaml", "low-contrast")
    skin_path = course / "skins" / "low-contrast.yaml"
    skin_path.write_text(
        skin_path.read_text(encoding="utf-8").replace(
            'text: "#1f2328"',
            'text: "#ffffff"',
        ),
        encoding="utf-8",
    )

    report = build_course(course)

    assert not report.ok
    assert any("contrast" in diagnostic.format().lower() for diagnostic in report.diagnostics)
```

- [ ] **Step 6: Run static builder contracts**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit validation and inheritance**

```bash
git add packages/static/src/raya_static/skins.py tests/contracts/test_static_builder.py
git commit -m "Validate section skin inheritance"
```

## Task 4: Render Fixture, Browser Evidence, And Render-Debug

**Files:**
- Modify: `examples/courses/render-fixture/raya.yaml`
- Create: `examples/courses/render-fixture/skins/warm-academic.yaml`
- Create: `examples/courses/render-fixture/skins/practice-lab.yaml`
- Create: `examples/courses/render-fixture/course/4_reader_ux/_raya/skin.yaml`
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `packages/cli/src/raya_cli/render_debug.py`
- Modify: `packages/cli/src/raya_cli/render_debug_report.py`
- Modify: `tests/e2e/test_render_debug_report.py`

- [ ] **Step 1: Add render fixture skins**

Update `examples/courses/render-fixture/raya.yaml` under `render:`:

```yaml
  skin: warm-academic
```

Create `examples/courses/render-fixture/skins/warm-academic.yaml`:

```yaml
id: warm-academic
name: Warm Academic
tokens:
  color:
    page: "#ffffff"
    surface: "#f6f8fa"
    text: "#1f2328"
    muted: "#57606a"
    accent: "#0969da"
    accent_soft: "#ddf4ff"
    border: "#d0d7de"
    success: "#1a7f37"
    warning: "#9a6700"
    danger: "#cf222e"
  font:
    body: "system-ui"
    heading: "system-ui"
    mono: "ui-monospace"
  density: comfortable
```

Create `examples/courses/render-fixture/skins/practice-lab.yaml`:

```yaml
id: practice-lab
name: Practice Lab
tokens:
  color:
    page: "#ffffff"
    surface: "#fff8c5"
    text: "#1f2328"
    muted: "#57606a"
    accent: "#8250df"
    accent_soft: "#fbefff"
    border: "#d0d7de"
    success: "#1a7f37"
    warning: "#9a6700"
    danger: "#cf222e"
  font:
    body: "system-ui"
    heading: "system-ui"
    mono: "ui-monospace"
  density: comfortable
```

Create `examples/courses/render-fixture/course/4_reader_ux/_raya/skin.yaml`:

```yaml
render:
  skin: practice-lab
```

- [ ] **Step 2: Add browser/static-read-path test**

In `tests/e2e/test_preview_static_read_path.py`, add this render-fixture test:

```python
def test_render_fixture_applies_course_and_section_skins(tmp_path: Path) -> None:
    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    site = course / "artifact" / "site"
    index_html = (site / "index.html").read_text(encoding="utf-8")
    reader_html = (site / "reader-ux" / "index.html").read_text(encoding="utf-8")
    skin_css = (site / "_raya" / "render" / "skin.css").read_text(encoding="utf-8")

    assert 'data-raya-skin="warm-academic"' in index_html
    assert 'data-raya-skin="practice-lab"' in reader_html
    assert '[data-raya-skin="warm-academic"]' in skin_css
    assert '[data-raya-skin="practice-lab"]' in skin_css
    assert "_raya/render/skin.css" in index_html
    assert "../_raya/render/skin.css" in reader_html
```

- [ ] **Step 3: Run browser/static-read-path test and verify RED/GREEN**

Run:

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_applies_course_and_section_skins \
  -q
```

Expected: PASS after previous tasks; if helper naming fails, fix the test helper usage only.

- [ ] **Step 4: Capture active skin in render-debug**

In `packages/cli/src/raya_cli/render_debug.py`, extend the browser page probe object to include:

```javascript
skin: document.body ? document.body.getAttribute("data-raya-skin") : null,
```

Place it beside existing page-level evidence such as surface or page metadata.

- [ ] **Step 5: Validate skin evidence in report**

In `packages/cli/src/raya_cli/render_debug_report.py`, add a check that:

- `site/_raya/render/skin.css` exists and is non-empty;
- each captured page has a non-empty `skin`;
- copied-site parity also contains the same skin evidence.

Use existing check result patterns. The message should name `skin.css` and the page URL/path.

- [ ] **Step 6: Add render-debug report tests**

In `tests/e2e/test_render_debug_report.py`, add minimal report fixture data with `skin: "practice-lab"` and assert the report includes a passing skin check. Also add a missing-skin case and assert failure.

Use existing report fixture builder patterns in that file.

- [ ] **Step 7: Run focused e2e/debug tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_applies_course_and_section_skins \
  tests/e2e/test_render_debug_report.py \
  -q
```

Expected: PASS.

- [ ] **Step 8: Run render-debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS and report includes skin checks.

- [ ] **Step 9: Commit fixture and render-debug evidence**

```bash
git add \
  examples/courses/render-fixture/raya.yaml \
  examples/courses/render-fixture/skins \
  examples/courses/render-fixture/course/4_reader_ux/_raya/skin.yaml \
  tests/e2e/test_preview_static_read_path.py \
  packages/cli/src/raya_cli/render_debug.py \
  packages/cli/src/raya_cli/render_debug_report.py \
  tests/e2e/test_render_debug_report.py
git commit -m "Add skin profile render debug evidence"
```

## Task 5: Foundation And Role Documentation

**Files:**
- Modify: `docs/foundation/17_rendering_execution_plan.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`
- Modify: `tests/contracts/test_renderer_dependencies.py`

- [ ] **Step 1: Add failing docs contract needles**

In `tests/contracts/test_renderer_dependencies.py`, add a test:

```python
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
```

- [ ] **Step 2: Run docs test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_renderer_dependencies.py::test_role_docs_cover_skin_profiles_and_style_guide \
  -q
```

Expected: FAIL because docs do not mention the skin contract yet.

- [ ] **Step 3: Update foundation rendering plan**

Add a concise accepted-baseline bullet to `docs/foundation/17_rendering_execution_plan.md` near the rendered-resource bullets:

```markdown
- Skin profiles are current build-time rendering behavior. A course may select
  a default skin with `render.skin` in `raya.yaml`; course-local profiles live
  under root `skins/`; section selectors live at `course/**/_raya/skin.yaml`
  beside a section `0_index.md` and inherit to descendants. Skins define
  validated semantic tokens for color, font, and density. They generate local
  `_raya/render/skin.css` variables and `data-raya-skin` page attributes, but
  they do not change content order, object IDs, references, artifact data,
  execution behavior, or source authority. V1 forbids arbitrary CSS, external
  fonts, CDN requests, and browser-side skin resolution.
```

- [ ] **Step 4: Update professor docs in EN/ES**

Add copyable examples to `docs/guides/en/professors/index.md` and `docs/guides/es/profesores/index.md`:

```markdown
Use course skins for visual identity and section skins to emphasize units,
labs, appendices, practice sections, or review sections.

```yaml
render:
  skin: warm-academic
```

```text
skins/
  warm-academic.yaml
  practice-lab.yaml
course/
  2_practice/
    0_index.md
    _raya/
      skin.yaml
```

```yaml
render:
  skin: practice-lab
```

Skin files define semantic color, font, and density tokens. Keep contrast high,
avoid external fonts, and do not use skins to change course content, links, or
numbered object identity.
```

Translate the explanatory text in Spanish while keeping paths and identifiers in English.

- [ ] **Step 5: Update contributor, agent, and student docs in EN/ES**

Add one paragraph per role:

- contributors/collaborators: preserve token validation, `skin.css`, `data-raya-skin`, no arbitrary CSS, no external fonts/CDNs, render-debug coverage.
- agents: debug order is `raya.yaml` or `_raya/skin.yaml`, skin file, diagnostics, `_raya/render/skin.css`, rendered `data-raya-skin`, render-debug report.
- students: skins only change visual presentation and unit emphasis; they do not change source authority, labels, links, official/generated status, or assignments.

- [ ] **Step 6: Run docs contracts and docs build**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_renderer_dependencies.py -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build docs
```

Expected: both PASS.

- [ ] **Step 7: Commit docs**

```bash
git add \
  docs/foundation/17_rendering_execution_plan.md \
  docs/guides/en/professors/index.md \
  docs/guides/en/contributors/index.md \
  docs/guides/en/students/index.md \
  docs/guides/en/agents/index.md \
  docs/guides/es/profesores/index.md \
  docs/guides/es/colaboradores/index.md \
  docs/guides/es/estudiantes/index.md \
  docs/guides/es/agentes/index.md \
  tests/contracts/test_renderer_dependencies.py
git commit -m "Document course section skin profiles"
```

## Task 6: Final Verification And Review

**Files:**
- No planned source edits unless verification or review finds issues.

- [ ] **Step 1: Run focused contract and e2e suite**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py \
  tests/contracts/test_renderer_dependencies.py \
  tests/e2e/test_render_debug_report.py \
  -q
```

Expected: PASS.

- [ ] **Step 2: Run browser-focused skin/static checks**

Run:

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_applies_course_and_section_skins \
  -q
```

Expected: PASS.

- [ ] **Step 3: Run render-debug parity gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS and report mentions skin checks.

- [ ] **Step 4: Run full host gate**

Run:

```bash
./scripts/check.sh
```

Expected: PASS.

- [ ] **Step 5: Run Docker gate**

Run:

```bash
./scripts/check-docker.sh
```

Expected: PASS.

- [ ] **Step 6: Request final code review**

Use `superpowers:requesting-code-review` with:

- base SHA: the plan commit before implementation starts;
- head SHA: current `HEAD`;
- requirements: this plan and `docs/superpowers/specs/2026-06-16-course-section-skin-profiles-design.md`;
- verification evidence from Steps 1-5.

Fix any Critical or Important findings, then rerun focused verification and commit fixes.

- [ ] **Step 7: Finish branch**

Use `superpowers:finishing-a-development-branch` after review and verification pass. Present merge/push options or push if the user explicitly asks for the matching GitHub branch.
