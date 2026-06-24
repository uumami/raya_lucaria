# Fluid Reader Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish the static reader shell into a calmer, wider, more fluid desktop learning workspace without changing renderer authority or adding learner state.

**Architecture:** Keep the current generated HTML regions and local shell script. Drive most of the change through `rendering.py` CSS, with tests proving desktop proportions, compact rail affordances, disclosure animation hooks, and accessibility state.

**Tech Stack:** Python 3.10, pytest, Playwright, generated static HTML/CSS/JavaScript.

---

### Task 1: Contract Tests For Shell Polish CSS

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [x] **Step 1: Add failing CSS assertions**

In `test_build_writes_reader_shell_css_and_command_bar_resources`, require these polish selectors/tokens in generated `rich.css`:

```python
for token in (
    ".raya-course-map a::before",
    ".raya-learning-rail-expand::after",
    "grid-template-columns: minmax(13.75rem, 13.75rem) minmax(42rem, 1fr) minmax(15rem, 15rem);",
    "grid-template-columns: 3.5rem minmax(48rem, 1fr) minmax(15rem, 15rem);",
    "backdrop-filter: blur(18px);",
    "transition: grid-template-rows 220ms ease, opacity 180ms ease, margin-top 220ms ease;",
):
    assert token in css
```

- [x] **Step 2: Run contract test and confirm failure**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_rich_css_defines_learning_shell_regions -q
```

Expected: fails because the new shell polish CSS tokens do not exist yet.

### Task 2: Browser Tests For Desktop Shell Comfort

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`

- [x] **Step 1: Add failing desktop geometry assertions**

Extend `test_render_fixture_learning_shell_layout_and_accessibility` or the focused course-map collapse test to assert at `1440x950`:

```python
metrics = page.evaluate(
    """() => {
      const shell = document.querySelector('.raya-learning-shell');
      const map = document.querySelector('#raya-course-map');
      const article = document.querySelector('#raya-article');
      const rail = document.querySelector('#raya-learning-rail');
      const commandBar = document.querySelector('.raya-top-command-bar');
      const commands = Array.from(document.querySelectorAll('.raya-command'));
      return {
        shellWidth: shell.getBoundingClientRect().width,
        mapWidth: map.getBoundingClientRect().width,
        articleWidth: article.getBoundingClientRect().width,
        railWidth: rail.getBoundingClientRect().width,
        commandBarHeight: commandBar.getBoundingClientRect().height,
        commandHeights: commands.map((button) => button.getBoundingClientRect().height),
        commandWidths: commands.map((button) => button.getBoundingClientRect().width),
      };
    }"""
)
assert 188 <= metrics["mapWidth"] <= 250
assert metrics["articleWidth"] >= 760
assert 220 <= metrics["railWidth"] <= 285
assert metrics["commandBarHeight"] <= 72
assert all(36 <= height <= 48 for height in metrics["commandHeights"])
assert all(width >= 40 for width in metrics["commandWidths"])
```

- [x] **Step 2: Add failing collapsed rail assertions**

After collapsing the map and learning rail at desktop, assert compact affordances:

```python
page.click(".raya-course-map-toggle")
page.click("[data-raya-learning-rail-collapse]")
collapsed = page.evaluate(
    """() => ({
      mapWidth: document.querySelector('#raya-course-map').getBoundingClientRect().width,
      railWidth: document.querySelector('#raya-learning-rail').getBoundingClientRect().width,
      mapButtonAfter: getComputedStyle(
        document.querySelector('#raya-course-map .raya-course-map-toggle'),
        '::after'
      ).content,
      railButtonAfter: getComputedStyle(
        document.querySelector('.raya-learning-rail-expand'),
        '::after'
      ).content,
      railBodyHidden: document.querySelector('#raya-learning-rail-body').getAttribute('aria-hidden'),
      railBodyInert: document.querySelector('#raya-learning-rail-body').inert,
    })"""
)
assert 52 <= collapsed["mapWidth"] <= 72
assert 44 <= collapsed["railWidth"] <= 64
assert collapsed["mapButtonAfter"] == '"Map"'
assert collapsed["railButtonAfter"] == '"Info"'
assert collapsed["railBodyHidden"] == "true"
assert collapsed["railBodyInert"] is True
```

- [x] **Step 3: Add failing expanded map numbering assertions**

At desktop before collapsing the map, assert the generated structural number is visible through CSS:

```python
numbering = page.evaluate(
    """() => {
      const current = document.querySelector('#raya-course-map a[aria-current="page"]');
      return {
        index: current?.getAttribute('data-raya-map-index'),
        before: current ? getComputedStyle(current, '::before').content : '',
        display: current ? getComputedStyle(current, '::before').display : '',
      };
    }"""
)
assert numbering["index"]
assert numbering["before"] == f'"{numbering["index"]}"'
assert numbering["display"] in {"inline-flex", "flex"}
```

- [x] **Step 4: Run focused e2e test and confirm failure**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/e2e/test_preview_static_read_path.py::test_render_fixture_learning_shell_layout_and_accessibility -q
```

Expected: fails until CSS is updated.

### Task 3: Implement Shell CSS Polish

**Files:**
- Modify: `packages/static/src/raya_static/rendering.py`

- [x] **Step 1: Add reusable panel/chrome CSS**

Add `.raya-shell-panel` semantics through grouped selectors or direct class selectors without requiring new HTML. Use current existing selectors as the source of truth:

```css
.raya-course-map,
.raya-learning-rail {
  background: color-mix(in srgb, var(--raya-color-surface) 86%, var(--raya-color-page));
  border-color: color-mix(in srgb, var(--raya-color-border) 62%, var(--raya-color-page));
  box-shadow: 0 0.75rem 1.75rem rgba(31, 35, 40, 0.06);
}
```

- [x] **Step 2: Tighten desktop columns**

At desktop, use:

```css
grid-template-columns: minmax(13.75rem, 13.75rem) minmax(42rem, 1fr) minmax(15rem, 15rem);
grid-template-columns: 3.5rem minmax(48rem, 1fr) minmax(15rem, 15rem);
```

Preserve mobile single-column behavior.

- [x] **Step 3: Polish command bar controls**

Make command buttons consistent, compact, and icon-forward:

```css
.raya-command {
  min-height: 2.5rem;
  min-width: 2.5rem;
}
.raya-command::before {
  flex: 0 0 auto;
}
```

Keep labels readable on desktop and visually hidden only at constrained widths.

- [x] **Step 4: Add expanded map numbering**

Use existing generated `data-raya-map-index` values:

```css
.raya-course-map a::before {
  content: attr(data-raya-map-index);
}
```

Keep collapsed map numbers using the existing `::after` compact rail treatment.

- [x] **Step 5: Polish collapsed rails**

Use compact labels:

```css
.raya-learning-rail-expand::after { content: "Info"; }
```

Ensure collapsed map remains clickable and compact with no wrapped visible text.

- [x] **Step 6: Smooth rail disclosure**

Set rail disclosure transition to:

```css
transition: grid-template-rows 220ms ease, opacity 180ms ease, margin-top 220ms ease;
```

Respect `prefers-reduced-motion`.

- [x] **Step 7: Run focused tests**

Run the focused contract and e2e tests until green.

### Task 4: Documentation And Verification

**Files:**
- Modify: `docs/foundation/20_learning_renderer_contract.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [x] **Step 1: Update docs only if behavior text needs clarification**

If implementation changes visible behavior, document the shell as a fluid static workspace with compact explicit rails. If only visual CSS changes, avoid unnecessary docs churn.

- [x] **Step 2: Run verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_rich_css_defines_learning_shell_regions tests/e2e/test_preview_static_read_path.py::test_render_fixture_learning_shell_layout_and_accessibility -q
./scripts/check-render-debug.sh
```

Expected: all pass before broader gates.
