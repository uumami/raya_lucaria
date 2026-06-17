# Renderer UX Skins And Accessibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the render fixture's desktop reading UI, make `eva-unit-02` the default skin, add three more expressive readable skins, and add a local OpenDyslexic toggle.

**Architecture:** Keep skins as existing semantic YAML token profiles and keep renderer structure in `rich.css`. Add local accessibility support as generated static resources under `_raya/render/accessibility/`, link them from rendered student pages, and keep all resources deployment-neutral with no CDN/runtime renderer dependency.

**Tech Stack:** Python 3.10, pytest, Glintstone static builder, YAML skin profiles, generated static CSS/JS/font resources, local `uv` verification.

---

## File Map

- Modify `examples/courses/render-fixture/raya.yaml`: change the course default `render.skin` to `eva-unit-02`.
- Create `examples/courses/render-fixture/skins/eva-unit-02.yaml`: default readable Unit 02-inspired profile.
- Create `examples/courses/render-fixture/skins/eva-unit-01.yaml`: readable Unit 01-inspired profile.
- Create `examples/courses/render-fixture/skins/eva-unit-03.yaml`: readable Unit 03-inspired profile.
- Create `examples/courses/render-fixture/skins/ghost-in-the-shell.yaml`: readable cyber/cyan profile.
- Modify `packages/static/src/raya_static/rendering.py`: widen desktop layout and improve tokenized borders/surfaces.
- Modify `packages/static/src/raya_static/builder.py`: link accessibility resources, render the header toggle, and write local accessibility resources.
- Create `packages/static/src/raya_static/accessibility.py`: constants and static CSS/JS helpers for OpenDyslexic resources.
- Add local font assets under `packages/static/src/raya_static/assets/accessibility/open-dyslexic/`.
- Modify `tests/contracts/test_static_skins.py`: assert new skin CSS selectors and default fixture skin behavior.
- Modify `tests/contracts/test_static_builder.py`: assert generated accessibility files are present in render fixture artifacts.
- Modify `tests/e2e/test_preview_static_read_path.py`: assert local static links, toggle markup, wider desktop CSS, and section override preservation.
- Modify English and Spanish role docs under `docs/guides/en/*/index.md` and `docs/guides/es/*/index.md`: document skin selection and reader font toggle behavior.

## Task 1: Add Failing Skin And Layout Tests

**Files:**
- Modify: `tests/contracts/test_static_skins.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write failing contract test for new fixture skins**

Append this test to `tests/contracts/test_static_skins.py`:

```python
def test_render_fixture_uses_eva_unit_02_default_and_emits_new_skin_selectors() -> None:
    import yaml

    from raya_static.skins import load_skin_context, render_skin_css

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
    assert "--raya-color-accent: #b5121b;" in css
```

- [ ] **Step 2: Run skin test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_skins.py::test_render_fixture_uses_eva_unit_02_default_and_emits_new_skin_selectors -q
```

Expected: FAIL because `render.skin` is still `warm-academic` and the new skin YAML files do not exist.

- [ ] **Step 3: Write failing e2e test for desktop layout and accessibility links**

Extend `test_render_fixture_applies_course_and_section_skins` in `tests/e2e/test_preview_static_read_path.py` so it fetches `rich.css`, the default page accessibility resources, and asserts:

```python
        authoring_url = f"{base_url}/authoring-matrix/index.html"
        authoring_html = _fetch_text(authoring_url)
        rich_css = _fetch_text(f"{base_url}/_raya/render/rich.css")
        accessibility_css = _fetch_text(
            f"{base_url}/_raya/render/accessibility/open-dyslexic.css"
        )
        accessibility_js = _fetch_text(
            f"{base_url}/_raya/render/accessibility/open-dyslexic-toggle.js"
        )
```

Add these assertions after the `finally` block:

```python
    assert 'data-raya-skin="eva-unit-02"' in index_html
    assert 'data-raya-skin="practice-lab"' in reader_html
    assert 'data-raya-skin="practice-lab"' in authoring_html
    assert '[data-raya-skin="eva-unit-02"]' in index_skin_css
    assert '[data-raya-skin="eva-unit-01"]' in index_skin_css
    assert '[data-raya-skin="eva-unit-03"]' in index_skin_css
    assert '[data-raya-skin="ghost-in-the-shell"]' in index_skin_css
    assert '<button class="raya-font-toggle"' in index_html
    assert 'aria-pressed="false"' in index_html
    assert 'href="_raya/render/accessibility/open-dyslexic.css"' in index_html
    assert 'src="_raya/render/accessibility/open-dyslexic-toggle.js"' in index_html
    assert '@font-face' in accessibility_css
    assert 'OpenDyslexic' in accessibility_css
    assert 'localStorage' in accessibility_js
    assert 'data-raya-open-dyslexic' in accessibility_js
    assert "max-width: 96rem" in rich_css
    assert "grid-template-columns: minmax(0, 4fr) minmax(18rem, 1fr)" in rich_css
    assert "@media (max-width: 720px)" in rich_css
```

Replace the old default-skin assertion in the same test:

```python
    assert 'data-raya-skin="warm-academic"' in index_html
```

with:

```python
    assert 'data-raya-skin="eva-unit-02"' in index_html
```

- [ ] **Step 4: Run e2e test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_applies_course_and_section_skins -q
```

Expected: FAIL because accessibility files, toggle markup, new skin selectors, and wider CSS are not implemented.

## Task 2: Add Skin Profiles And Default Selector

**Files:**
- Modify: `examples/courses/render-fixture/raya.yaml`
- Create: `examples/courses/render-fixture/skins/eva-unit-02.yaml`
- Create: `examples/courses/render-fixture/skins/eva-unit-01.yaml`
- Create: `examples/courses/render-fixture/skins/eva-unit-03.yaml`
- Create: `examples/courses/render-fixture/skins/ghost-in-the-shell.yaml`

- [ ] **Step 1: Change render fixture default skin**

In `examples/courses/render-fixture/raya.yaml`, change:

```yaml
render:
  skin: warm-academic
```

to:

```yaml
render:
  skin: eva-unit-02
```

- [ ] **Step 2: Add `eva-unit-02` skin**

Create `examples/courses/render-fixture/skins/eva-unit-02.yaml`:

```yaml
id: eva-unit-02
name: Eva Unit 02
tokens:
  color:
    page: "#fff8f3"
    surface: "#ffffff"
    text: "#211b18"
    muted: "#5f5049"
    accent: "#b5121b"
    accent_soft: "#ffe1d2"
    border: "#d8b8aa"
    success: "#236c3a"
    warning: "#8f5d00"
    danger: "#b5121b"
  font:
    body: "system-ui"
    heading: "system-ui"
    mono: "ui-monospace"
  density: comfortable
```

- [ ] **Step 3: Add `eva-unit-01` skin**

Create `examples/courses/render-fixture/skins/eva-unit-01.yaml`:

```yaml
id: eva-unit-01
name: Eva Unit 01
tokens:
  color:
    page: "#fbf8ff"
    surface: "#ffffff"
    text: "#201a28"
    muted: "#5b5364"
    accent: "#5b2a86"
    accent_soft: "#e8f8d8"
    border: "#d4c2e4"
    success: "#357a22"
    warning: "#8a6500"
    danger: "#b3261e"
  font:
    body: "system-ui"
    heading: "system-ui"
    mono: "ui-monospace"
  density: comfortable
```

- [ ] **Step 4: Add `eva-unit-03` skin**

Create `examples/courses/render-fixture/skins/eva-unit-03.yaml`:

```yaml
id: eva-unit-03
name: Eva Unit 03
tokens:
  color:
    page: "#f7f7f6"
    surface: "#ffffff"
    text: "#1c1c1c"
    muted: "#555555"
    accent: "#8f1117"
    accent_soft: "#eeeeec"
    border: "#c8c8c5"
    success: "#246b3f"
    warning: "#876000"
    danger: "#8f1117"
  font:
    body: "system-ui"
    heading: "system-ui"
    mono: "ui-monospace"
  density: comfortable
```

- [ ] **Step 5: Add `ghost-in-the-shell` skin**

Create `examples/courses/render-fixture/skins/ghost-in-the-shell.yaml`:

```yaml
id: ghost-in-the-shell
name: Ghost In The Shell
tokens:
  color:
    page: "#f4fbfb"
    surface: "#ffffff"
    text: "#162425"
    muted: "#526466"
    accent: "#006d77"
    accent_soft: "#d8f3f0"
    border: "#b8d7d9"
    success: "#247348"
    warning: "#8a6200"
    danger: "#b3261e"
  font:
    body: "system-ui"
    heading: "system-ui"
    mono: "ui-monospace"
  density: comfortable
```

- [ ] **Step 6: Run skin test and verify partial GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_skins.py::test_render_fixture_uses_eva_unit_02_default_and_emits_new_skin_selectors -q
```

Expected: PASS. The e2e test from Task 1 should still fail until layout/accessibility is implemented.

- [ ] **Step 7: Commit skin profiles**

Run:

```bash
git add examples/courses/render-fixture/raya.yaml examples/courses/render-fixture/skins/eva-unit-02.yaml examples/courses/render-fixture/skins/eva-unit-01.yaml examples/courses/render-fixture/skins/eva-unit-03.yaml examples/courses/render-fixture/skins/ghost-in-the-shell.yaml tests/contracts/test_static_skins.py
git commit -m "Add readable fixture skins"
```

## Task 3: Widen Desktop Layout And Improve Borders

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Update desktop layout CSS**

In `rich_render_css()` inside `packages/static/src/raya_static/rendering.py`, change the shared layout block from:

```css
.raya-site-header-inner,
.raya-main,
.raya-page-footer,
.raya-inspection-main {
  margin: 0 auto;
  max-width: 76rem;
  padding: var(--raya-space-page);
}
```

to:

```css
.raya-site-header-inner,
.raya-main,
.raya-page-footer,
.raya-inspection-main {
  margin: 0 auto;
  max-width: 96rem;
  padding: var(--raya-space-page);
}
```

Change `.raya-main` from:

```css
.raya-main {
  align-items: start;
  display: grid;
  gap: var(--raya-space-block);
  grid-template-columns: minmax(0, 1fr) minmax(16rem, 22rem);
}
```

to:

```css
.raya-main {
  align-items: start;
  display: grid;
  gap: calc(var(--raya-space-block) * 1.25);
  grid-template-columns: minmax(0, 4fr) minmax(18rem, 1fr);
}
```

- [ ] **Step 2: Tokenize and strengthen panel borders**

In the `.raya-article, .raya-support-stack, .raya-inspection-main` block, keep the existing variables and add radius/shadow:

```css
.raya-article,
.raya-support-stack,
.raya-inspection-main {
  background: var(--raya-color-surface);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  box-shadow: 0 1px 0 color-mix(in srgb, var(--raya-color-border) 55%, transparent);
  min-width: 0;
}
```

If `color-mix` causes browser compatibility concerns in local Chromium, replace the shadow with:

```css
  box-shadow: 0 1px 0 rgba(0, 0, 0, 0.04);
```

- [ ] **Step 3: Keep mobile collapse stable**

In the `@media (max-width: 720px)` block, keep:

```css
  .raya-main {
    display: block;
  }
```

and add a small reset so the wider desktop panel shape does not crowd phones:

```css
  .raya-article,
  .raya-support-stack,
  .raya-inspection-main {
    border-radius: 0.25rem;
  }
```

- [ ] **Step 4: Run e2e test and verify it still fails only on accessibility**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_applies_course_and_section_skins -q
```

Expected: FAIL only for missing accessibility CSS/JS/toggle assertions.

- [ ] **Step 5: Commit layout changes**

Run:

```bash
git add packages/static/src/raya_static/rendering.py tests/e2e/test_preview_static_read_path.py
git commit -m "Widen rendered desktop layout"
```

## Task 4: Add Local OpenDyslexic Accessibility Resources

**Files:**
- Create: `packages/static/src/raya_static/accessibility.py`
- Modify: `packages/static/src/raya_static/builder.py`
- Add: `packages/static/src/raya_static/assets/accessibility/open-dyslexic/OpenDyslexic-Regular.woff`
- Test: `tests/contracts/test_static_builder.py`
- Test: `tests/e2e/test_preview_static_read_path.py`

- [ ] **Step 1: Write failing artifact test**

Add assertions to `test_render_fixture_builds_rich_static_pages` in `tests/contracts/test_static_builder.py`:

```python
    accessibility_css = site_dir / "_raya" / "render" / "accessibility" / "open-dyslexic.css"
    accessibility_js = (
        site_dir
        / "_raya"
        / "render"
        / "accessibility"
        / "open-dyslexic-toggle.js"
    )
    accessibility_font = (
        site_dir
        / "_raya"
        / "render"
        / "accessibility"
        / "fonts"
        / "OpenDyslexic-Regular.woff"
    )
    assert accessibility_css.is_file()
    assert accessibility_js.is_file()
    assert accessibility_font.is_file()
    assert "OpenDyslexic" in accessibility_css.read_text(encoding="utf-8")
    assert "localStorage" in accessibility_js.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run artifact test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages -q
```

Expected: FAIL because accessibility resources are not written yet.

- [ ] **Step 3: Add local font asset**

If the Debian package is available, prepare the font asset with:

```bash
tmpdir="$(mktemp -d)"
cd "$tmpdir"
apt-get download fonts-opendyslexic
dpkg-deb -x fonts-opendyslexic_*.deb extracted
find extracted -type f \( -iname '*Regular*.otf' -o -iname '*Regular*.ttf' \) -print
```

Convert the regular font to WOFF if a converter is available:

```bash
fonttools ttLib.woff compress extracted/path/to/OpenDyslexic-Regular.otf
```

Copy the resulting file to:

```text
packages/static/src/raya_static/assets/accessibility/open-dyslexic/OpenDyslexic-Regular.woff
```

If no WOFF converter is available, use the package's regular `.otf` file and update the CSS/test file name consistently to `OpenDyslexic-Regular.otf`.

- [ ] **Step 4: Create accessibility helper module**

Create `packages/static/src/raya_static/accessibility.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from importlib.abc import Traversable


ACCESSIBILITY_RESOURCE_PATH = "_raya/render/accessibility"
OPEN_DYSLEXIC_CSS_NAME = "open-dyslexic.css"
OPEN_DYSLEXIC_JS_NAME = "open-dyslexic-toggle.js"
OPEN_DYSLEXIC_FONT_NAME = "OpenDyslexic-Regular.woff"
OPEN_DYSLEXIC_RESOURCE_PACKAGE = "raya_static"
OPEN_DYSLEXIC_RESOURCE_PATH = (
    "assets/accessibility/open-dyslexic/" + OPEN_DYSLEXIC_FONT_NAME
)


@dataclass(frozen=True)
class AccessibilityResources:
    css: str
    javascript: str
    source_font: Traversable
    font_name: str


def open_dyslexic_resources() -> AccessibilityResources:
    css = f'''@font-face {{
  font-family: "OpenDyslexic";
  src: url("fonts/{OPEN_DYSLEXIC_FONT_NAME}") format("woff");
  font-style: normal;
  font-weight: 400;
  font-display: swap;
}}

[data-raya-open-dyslexic="true"] {{
  --raya-font-body: "OpenDyslexic";
  --raya-font-heading: "OpenDyslexic";
}}

.raya-font-toggle {{
  align-items: center;
  background: var(--raya-color-accent-soft);
  border: 1px solid var(--raya-color-border);
  border-radius: 0.375rem;
  color: var(--raya-color-text);
  cursor: pointer;
  display: inline-flex;
  font: inherit;
  font-size: 0.875rem;
  font-weight: 700;
  gap: 0.4rem;
  padding: 0.45rem 0.65rem;
}}

.raya-font-toggle[aria-pressed="true"] {{
  background: var(--raya-color-accent);
  border-color: var(--raya-color-accent);
  color: var(--raya-color-surface);
}}
'''
    javascript = '''(() => {
  const storageKey = "raya:open-dyslexic";
  const activeValue = "true";

  function storedPreference() {
    try {
      return localStorage.getItem(storageKey) === activeValue;
    } catch {
      return false;
    }
  }

  function storePreference(enabled) {
    try {
      localStorage.setItem(storageKey, enabled ? activeValue : "false");
    } catch {
      return;
    }
  }

  function apply(enabled) {
    document.documentElement.setAttribute(
      "data-raya-open-dyslexic",
      enabled ? "true" : "false"
    );
    document.querySelectorAll(".raya-font-toggle").forEach((button) => {
      button.setAttribute("aria-pressed", enabled ? "true" : "false");
    });
  }

  apply(storedPreference());

  document.addEventListener("click", (event) => {
    const button = event.target.closest(".raya-font-toggle");
    if (!button) {
      return;
    }
    const enabled = button.getAttribute("aria-pressed") !== "true";
    storePreference(enabled);
    apply(enabled);
  });
})();
'''
    return AccessibilityResources(
        css=css,
        javascript=javascript,
        source_font=resources.files(OPEN_DYSLEXIC_RESOURCE_PACKAGE).joinpath(
            OPEN_DYSLEXIC_RESOURCE_PATH
        ),
        font_name=OPEN_DYSLEXIC_FONT_NAME,
    )
```

- [ ] **Step 5: Link accessibility resources in rendered pages**

In `packages/static/src/raya_static/builder.py`, import:

```python
from raya_static.accessibility import (
    ACCESSIBILITY_RESOURCE_PATH,
    OPEN_DYSLEXIC_CSS_NAME,
    OPEN_DYSLEXIC_JS_NAME,
    open_dyslexic_resources,
)
```

In `_render_page_html`, compute:

```python
    accessibility_css_href = _relative_href(
        page.output_path,
        f"{ACCESSIBILITY_RESOURCE_PATH}/{OPEN_DYSLEXIC_CSS_NAME}",
    )
    accessibility_js_href = _relative_href(
        page.output_path,
        f"{ACCESSIBILITY_RESOURCE_PATH}/{OPEN_DYSLEXIC_JS_NAME}",
    )
```

Add the CSS link after `skin.css`:

```python
            f'<link rel="stylesheet" href="{html.escape(accessibility_css_href)}">',
```

Add this button after the course title:

```python
            (
                '<button class="raya-font-toggle" type="button" '
                'aria-pressed="false">OpenDyslexic</button>'
            ),
```

Add the script before `</body>`:

```python
            f'<script src="{html.escape(accessibility_js_href)}" defer></script>',
```

- [ ] **Step 6: Write accessibility resources during build**

In `_write_rich_render_resources`, after writing `skin.css`, add:

```python
    accessibility = open_dyslexic_resources()
    accessibility_dir = site_dir / ACCESSIBILITY_RESOURCE_PATH
    accessibility_dir.mkdir(parents=True, exist_ok=True)
    css_path = accessibility_dir / OPEN_DYSLEXIC_CSS_NAME
    js_path = accessibility_dir / OPEN_DYSLEXIC_JS_NAME
    font_dir = accessibility_dir / "fonts"
    font_dir.mkdir(parents=True, exist_ok=True)
    font_path = font_dir / accessibility.font_name
    if not accessibility.source_font.is_file():
        report.add_error(
            "Missing local OpenDyslexic font asset",
            path=accessibility.source_font,
            next_action="Add the local OpenDyslexic font under packages/static/src/raya_static/assets/accessibility/open-dyslexic/",
        )
        return
    css_path.write_text(accessibility.css, encoding="utf-8")
    js_path.write_text(accessibility.javascript, encoding="utf-8")
    with resources.as_file(accessibility.source_font) as source_font:
        shutil.copy2(source_font, font_path)
    report.wrote_output(css_path)
    report.wrote_output(js_path)
    report.wrote_output(font_path)
```

`builder.py` already imports `shutil`.

- [ ] **Step 7: Run artifact and e2e tests and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages tests/e2e/test_preview_static_read_path.py::test_render_fixture_applies_course_and_section_skins -q
```

Expected: PASS.

- [ ] **Step 8: Commit accessibility resources**

Run:

```bash
git add packages/static/src/raya_static/accessibility.py packages/static/src/raya_static/builder.py packages/static/src/raya_static/assets/accessibility/open-dyslexic tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py
git commit -m "Add local OpenDyslexic toggle"
```

## Task 5: Update Role Documentation

**Files:**
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/agentes/index.md`
- Test: `tests/contracts/test_documentation_surfaces.py`

- [ ] **Step 1: Add failing documentation assertions**

In `tests/contracts/test_documentation_surfaces.py`, add or extend a test so it reads the role docs and asserts these needles:

```python
needles = {
    "docs/guides/en/professors/index.md": ["render.skin", "skins/", "eva-unit-02"],
    "docs/guides/en/contributors/index.md": ["semantic tokens", "arbitrary CSS", "no CDN"],
    "docs/guides/en/students/index.md": ["OpenDyslexic", "reading preference"],
    "docs/guides/en/agents/index.md": ["OpenDyslexic", "external font", "static parity"],
    "docs/guides/es/profesores/index.md": ["render.skin", "skins/", "eva-unit-02"],
    "docs/guides/es/colaboradores/index.md": ["tokens semanticos", "CSS arbitrario", "CDN"],
    "docs/guides/es/estudiantes/index.md": ["OpenDyslexic", "preferencia de lectura"],
    "docs/guides/es/agentes/index.md": ["OpenDyslexic", "fuente externa", "paridad estatica"],
}
for path, expected in needles.items():
    text = Path(path).read_text(encoding="utf-8")
    for needle in expected:
        assert needle in text
```

- [ ] **Step 2: Run documentation test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_documentation_surfaces.py -q
```

Expected: FAIL until the role docs mention the new behavior.

- [ ] **Step 3: Update English role docs**

Add concise paragraphs:

- professors: `render.skin` selects course presentation; `eva-unit-02` is the render fixture default example; skins live in `skins/`.
- contributors: skin files use semantic tokens only, not arbitrary CSS; no CDN or external font requests.
- students: the top OpenDyslexic button is a local reading preference.
- agents: verify local `_raya/render/accessibility/` assets, no external font requests, and preview/static parity.

- [ ] **Step 4: Update Spanish role docs**

Add equivalent Spanish paragraphs, keeping technical identifiers in English:

- profesores: `render.skin`, `eva-unit-02`, `skins/`.
- colaboradores: `tokens semanticos`, no `CSS arbitrario`, no `CDN`.
- estudiantes: `OpenDyslexic` as `preferencia de lectura`.
- agentes: check `fuente externa` absence and `paridad estatica`.

- [ ] **Step 5: Run documentation test and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_documentation_surfaces.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit docs**

Run:

```bash
git add docs/guides/en docs/guides/es tests/contracts/test_documentation_surfaces.py
git commit -m "Document renderer skins accessibility"
```

## Task 6: Final Verification And Review

**Files:**
- Verify all changed files.

- [ ] **Step 1: Run focused test gate**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_skins.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py tests/contracts/test_documentation_surfaces.py -q
```

Expected: PASS.

- [ ] **Step 2: Validate and build render fixture**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate examples/courses/render-fixture
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya artifacts inspect examples/courses/render-fixture/artifact
```

Expected: all commands exit 0.

- [ ] **Step 3: Run render-debug gate**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: exit 0 and report no external renderer/font requests.

- [ ] **Step 4: Run hygiene check**

Run:

```bash
./scripts/check-hygiene.sh
```

Expected: exit 0.

- [ ] **Step 5: Request code review**

Use `superpowers:requesting-code-review` and ask the reviewer to focus on:

- whether OpenDyslexic assets are local and static;
- whether new skins remain semantic token profiles;
- whether desktop layout improves without mobile regression;
- whether docs cover English and Spanish role surfaces;
- whether no browser-side MathJax/renderer dependency was introduced.

- [ ] **Step 6: Address review using receiving-code-review**

If review feedback arrives, use `superpowers:receiving-code-review`, verify the finding, and only patch validated issues.

- [ ] **Step 7: Commit review fixes if needed**

If changes are needed:

```bash
git add <changed-files>
git commit -m "Fix renderer UX review findings"
```

- [ ] **Step 8: Final branch state**

Run:

```bash
git status --short --branch
git log --oneline -6
```

Expected: branch is on `new_rayalucaria`; working tree is clean except any intentionally uncommitted local preview/debug outputs ignored by git.
