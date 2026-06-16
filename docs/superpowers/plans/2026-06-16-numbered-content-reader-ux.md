# Numbered Content Reader UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a scannable default reader style for numbered learning objects, add `remark`, and prove the result with a realistic render fixture.

**Architecture:** Keep source truth in fenced directives and `raya.yaml`, machine truth in manifest-declared `data/numbered-objects.json`, and normal pages as static reader-facing views. The schema package owns built-in families and accepted styles; the static package owns rendered HTML/CSS; CLI render-debug keeps screenshots/report evidence without becoming authority.

**Tech Stack:** Python 3.10, `pytest`, Playwright/Chromium, Raya schema/static/CLI packages, Markdown fixture content, local MathJax artifact resources.

---

## File Structure

- `packages/schema/src/raya_schema/numbered_objects.py`
  - Owns built-in numbered-object sequences, built-in families, accepted style names, config normalization, and numbered index validation.
- `tests/contracts/test_numbered_objects.py`
  - Owns schema/default/config tests for numbered families, styles, shorthand references, source collection, and numbered index validation.
- `packages/static/src/raya_static/rendering.py`
  - Owns renderer CSS and numbered-object HTML shape.
- `tests/contracts/test_static_builder.py`
  - Owns build-level fixture assertions for rendered HTML, `data/numbered-objects.json`, and rich render fixture output.
- `examples/courses/render-fixture/raya.yaml`
  - Owns render-fixture course-level numbered-object overrides.
- `examples/courses/render-fixture/course/4_reader_ux/0_index.md`
  - New realistic fixture page for reader-facing numbered-content flow.
- `examples/courses/render-fixture/course/0_index.md`
  - Add a link to the realistic reader UX fixture.
- `packages/cli/src/raya_cli/render_debug.py`
  - Owns render-debug page discovery for screenshot capture.
- `packages/cli/src/raya_cli/render_debug_report.py`
  - Owns render-debug expected page list and inspection report checks.
- `tests/e2e/test_preview_static_read_path.py`
  - Owns browser/static-read-path checks for fixture pages, render-debug summary, and screenshots.
- `tests/e2e/test_render_debug_parity_gate.py`
  - Owns parity-gate checks for render-debug report shape.
- `docs/foundation/17_rendering_execution_plan.md`
  - Update accepted rendering status for `remark` and `scannable`.
- `docs/guides/en/professors/index.md`
- `docs/guides/en/students/index.md`
- `docs/guides/en/contributors/index.md`
- `docs/guides/en/agents/index.md`
- `docs/guides/es/profesores/index.md`
- `docs/guides/es/estudiantes/index.md`
- `docs/guides/es/colaboradores/index.md`
- `docs/guides/es/agentes/index.md`
  - Update role guidance in separate languages.

## Task 1: Schema Defaults For Remark And Scannable Style

**Files:**
- Modify: `tests/contracts/test_numbered_objects.py`
- Modify: `packages/schema/src/raya_schema/numbered_objects.py`

- [ ] **Step 1: Write failing built-in default assertions**

In `tests/contracts/test_numbered_objects.py`, update `test_built_in_numbered_object_defaults_group_math_and_coursework()` to assert the new built-in family and style defaults:

```python
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["remark"]["sequence"] == "theorem"
    assert BUILT_IN_NUMBERED_OBJECT_FAMILIES["remark"]["label"] == "Remark"
    assert BUILT_IN_NUMBERED_OBJECT_SEQUENCES["theorem"]["style"] == "scannable"
    assert BUILT_IN_NUMBERED_OBJECT_SEQUENCES["example"]["style"] == "scannable"
    assert BUILT_IN_NUMBERED_OBJECT_SEQUENCES["exercise"]["style"] == "scannable"
    assert BUILT_IN_NUMBERED_OBJECT_SEQUENCES["assignment"]["style"] == "scannable"
    assert BUILT_IN_NUMBERED_OBJECT_SEQUENCES["figure"]["style"] == "caption"
    assert BUILT_IN_NUMBERED_OBJECT_SEQUENCES["table"]["style"] == "caption"
    assert BUILT_IN_NUMBERED_OBJECT_SEQUENCES["equation"]["style"] == "equation"
```

Replace any older expectation that `theorem` or `example` uses `margin`, or that `assignment` uses `banded`, with the assertions above.

- [ ] **Step 2: Write failing config acceptance assertion for `scannable`**

In `test_normalize_numbered_object_config_accepts_course_overrides()`, change the assignment override to use `scannable`:

```python
                        "assignment": {"label": "Activity", "style": "scannable"},
```

Then add this assertion with the existing override assertions:

```python
    assert config.sequences["assignment"].style == "scannable"
```

- [ ] **Step 3: Update unknown-style diagnostic expectation**

Find `test_numbered_object_config_rejects_unknown_style_with_precise_field()` and update its expected next action to include `scannable`:

```python
    assert diagnostic.next_action == "Use scannable, margin, banded, caption, or equation"
```

- [ ] **Step 4: Run the focused schema tests and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_numbered_objects.py::test_built_in_numbered_object_defaults_group_math_and_coursework \
  tests/contracts/test_numbered_objects.py::test_normalize_numbered_object_config_accepts_course_overrides \
  tests/contracts/test_numbered_objects.py::test_numbered_object_config_rejects_unknown_style_with_precise_field \
  -q
```

Expected: FAIL because `remark` is missing, `scannable` is not accepted, and the default styles still use the old values.

- [ ] **Step 5: Implement schema defaults**

In `packages/schema/src/raya_schema/numbered_objects.py`, update `BUILT_IN_NUMBERED_OBJECT_SEQUENCES` to:

```python
BUILT_IN_NUMBERED_OBJECT_SEQUENCES: dict[str, dict[str, str]] = {
    "theorem": {"label": "Theorem", "style": "scannable"},
    "example": {"label": "Example", "style": "scannable"},
    "exercise": {"label": "Exercise", "style": "scannable"},
    "assignment": {"label": "Assignment", "style": "scannable"},
    "figure": {"label": "Figure", "style": "caption"},
    "table": {"label": "Table", "style": "caption"},
    "equation": {"label": "Equation", "style": "equation"},
}
```

Add `remark` to `BUILT_IN_NUMBERED_OBJECT_FAMILIES` after `definition`:

```python
    "remark": {"sequence": "theorem", "label": "Remark"},
```

Update the style set:

```python
NUMBERED_OBJECT_STYLES = {"scannable", "margin", "banded", "caption", "equation"}
```

If the unknown-style diagnostic builds the next-action text from a hard-coded string elsewhere in the file, update it to exactly:

```python
"Use scannable, margin, banded, caption, or equation"
```

- [ ] **Step 6: Run the focused schema tests and verify GREEN**

Run the same focused command:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_numbered_objects.py::test_built_in_numbered_object_defaults_group_math_and_coursework \
  tests/contracts/test_numbered_objects.py::test_normalize_numbered_object_config_accepts_course_overrides \
  tests/contracts/test_numbered_objects.py::test_numbered_object_config_rejects_unknown_style_with_precise_field \
  -q
```

Expected: PASS.

- [ ] **Step 7: Run the full numbered-object contract suite**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_numbered_objects.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit schema defaults**

Commit only the schema/default test changes:

```bash
git add packages/schema/src/raya_schema/numbered_objects.py tests/contracts/test_numbered_objects.py
git commit -m "Add scannable numbered object defaults"
```

## Task 2: Scannable Numbered Object Rendering

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `packages/static/src/raya_static/rendering.py`

- [ ] **Step 1: Update existing HTML class assertion to expect scannable**

In `tests/contracts/test_static_builder.py`, in `test_numbered_objects_render_html_and_cross_references()`, replace the class assertion for the theorem object with:

```python
    assert (
        'class="raya-numbered-object raya-numbered-object--scannable '
        'raya-numbered-object--theorem"'
        in math_html
    )
    assert 'class="raya-numbered-object-layout"' in math_html
    assert 'class="raya-numbered-object-badge" aria-hidden="true"' in math_html
    assert 'class="raya-numbered-object-badge-label">Theorem</span>' in math_html
    assert 'class="raya-numbered-object-badge-number">1.1</span>' in math_html
```

- [ ] **Step 2: Add a build test for style preservation of caption/equation**

Add this test near `test_numbered_objects_render_html_and_cross_references()`:

```python
def test_numbered_objects_default_scannable_keeps_caption_and_equation_styles(
    tmp_path: Path,
) -> None:
    course = _copy_minimal(tmp_path)
    page = course / "course" / "0_index.md"
    page.write_text(
        "---\n"
        "id: style-demo\n"
        "title: Style Demo\n"
        "summary: Numbered object style fixture.\n"
        "status: ready\n"
        "---\n"
        "# Style Demo\n\n"
        "::: remark {#reader-remark title=\"Reader note\"}\n"
        "A remark should use the scannable reader style.\n"
        ":::\n\n"
        "::: figure {#reader-figure title=\"Reader figure\"}\n"
        "![Figure asset](_assets/style-demo.txt)\n"
        ":::\n\n"
        "::: equation {#reader-equation}\n"
        "$$\n"
        "x + y = y + x\n"
        "$$\n"
        ":::\n",
        encoding="utf-8",
    )
    assets = course / "course" / "_assets"
    assets.mkdir(exist_ok=True)
    (assets / "style-demo.txt").write_text("style fixture\n", encoding="utf-8")

    report = build_course(course)

    assert report.ok, [diagnostic.format() for diagnostic in report.diagnostics]
    html = (course / "artifact" / "site" / "index.html").read_text(encoding="utf-8")
    numbered_index = json.loads(
        (course / "artifact" / "data" / "numbered-objects.json").read_text(
            encoding="utf-8"
        )
    )
    by_id = {item["id"]: item for item in numbered_index["objects"]}
    assert by_id["reader-remark"]["style"] == "scannable"
    assert by_id["reader-figure"]["style"] == "caption"
    assert by_id["reader-equation"]["style"] == "equation"
    assert "Remark 1" in _visible_text(html)
    assert 'raya-numbered-object--remark' in html
    assert 'raya-numbered-object--scannable' in html
    assert 'raya-numbered-object--caption' in html
    assert 'raya-numbered-object--equation' in html
```

- [ ] **Step 3: Run the rendering tests and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py::test_numbered_objects_render_html_and_cross_references \
  tests/contracts/test_static_builder.py::test_numbered_objects_default_scannable_keeps_caption_and_equation_styles \
  -q
```

Expected: FAIL because the renderer does not emit the scannable wrapper/badge classes yet, and the old default style may still appear if Task 1 was not applied.

- [ ] **Step 4: Implement scannable HTML structure**

In `packages/static/src/raya_static/rendering.py`, update `_render_numbered_object_html()` so `scannable` objects render with a layout and badge. Keep the existing simple structure for non-scannable styles.

Use this implementation shape:

```python
def _render_numbered_object_html(
    rendered_body: str,
    *,
    item: NumberedObjectRenderItem,
) -> str:
    obj = item.object
    escaped_id = html.escape(obj.id, quote=True)
    escaped_family = html.escape(obj.family, quote=True)
    escaped_style = html.escape(obj.style, quote=True)
    escaped_reference = html.escape(obj.reference_text)
    escaped_label = html.escape(obj.label)
    escaped_number = html.escape(obj.number)
    title = obj.title or ""
    body = rendered_body.strip() or "<p></p>"
    title_html = (
        f'<span class="raya-numbered-object-title">{html.escape(title)}</span>'
        if title
        else ""
    )
    heading = (
        f'<span class="raya-numbered-object-reference">{escaped_reference}</span>'
        + (f" {title_html}" if title_html else "")
    )
    opening = (
        f'<section id="raya-object-{escaped_id}" '
        f'class="raya-numbered-object raya-numbered-object--{escaped_style} '
        f'raya-numbered-object--{escaped_family}" '
        f'data-object-id="{escaped_id}">'
    )
    if obj.style == "scannable":
        return "\n".join(
            [
                opening,
                '<div class="raya-numbered-object-layout">',
                '<div class="raya-numbered-object-badge" aria-hidden="true">',
                f'<span class="raya-numbered-object-badge-label">{escaped_label}</span>',
                f'<span class="raya-numbered-object-badge-number">{escaped_number}</span>',
                "</div>",
                '<div class="raya-numbered-object-content">',
                '<p class="raya-numbered-object-heading">',
                heading,
                "</p>",
                '<div class="raya-numbered-object-body">',
                body,
                "</div>",
                "</div>",
                "</div>",
                "</section>",
            ]
        )
    return "\n".join(
        [
            opening,
            '<p class="raya-numbered-object-heading">',
            heading,
            "</p>",
            '<div class="raya-numbered-object-body">',
            body,
            "</div>",
            "</section>",
        ]
    )
```

Keep `escaped_reference` visible in the heading so screen readers and copied text still include the full reference text.

- [ ] **Step 5: Add scannable CSS**

In `packages/static/src/raya_static/rendering.py`, in `rich_render_css()`, add CSS after the existing `.raya-numbered-object--banded` rules and before caption/equation rules:

```css
.raya-numbered-object--scannable {
  border-color: #d7dee2;
  overflow: hidden;
}
.raya-numbered-object-layout {
  display: grid;
  grid-template-columns: minmax(4.75rem, 5.75rem) minmax(0, 1fr);
}
.raya-numbered-object-badge {
  align-items: center;
  background: #e9f4f2;
  border-right: 1px solid #d7dee2;
  color: #214e4a;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  justify-content: center;
  padding: 0.8rem 0.55rem;
  text-align: center;
}
.raya-numbered-object-badge-label {
  font-size: 0.76rem;
  font-weight: 700;
  line-height: 1.15;
}
.raya-numbered-object-badge-number {
  font-size: 1rem;
  font-weight: 750;
  line-height: 1.15;
}
.raya-numbered-object-content {
  min-width: 0;
}
.raya-numbered-object--scannable .raya-numbered-object-heading {
  background: #ffffff;
}
@media (max-width: 640px) {
  .raya-numbered-object-layout {
    grid-template-columns: 1fr;
  }
  .raya-numbered-object-badge {
    align-items: baseline;
    border-bottom: 1px solid #d7dee2;
    border-right: 0;
    flex-direction: row;
    justify-content: flex-start;
    padding: 0.55rem 0.85rem;
  }
}
```

If this duplicates an existing media block near the bottom of the stylesheet, place the mobile rules there instead. Do not introduce viewport-scaled font sizes.

- [ ] **Step 6: Run the rendering tests and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py::test_numbered_objects_render_html_and_cross_references \
  tests/contracts/test_static_builder.py::test_numbered_objects_default_scannable_keeps_caption_and_equation_styles \
  -q
```

Expected: PASS.

- [ ] **Step 7: Run focused static builder numbered tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py::test_build_collects_numbered_objects_with_page_hierarchy \
  tests/contracts/test_static_builder.py::test_numbered_objects_render_html_and_cross_references \
  tests/contracts/test_static_builder.py::test_numbered_objects_default_scannable_keeps_caption_and_equation_styles \
  tests/contracts/test_static_builder.py::test_build_renders_proof_of_numbered_object \
  -q
```

Expected: PASS.

- [ ] **Step 8: Commit scannable rendering**

Commit only rendering and static-builder test changes:

```bash
git add packages/static/src/raya_static/rendering.py tests/contracts/test_static_builder.py
git commit -m "Render scannable numbered objects"
```

## Task 3: Realistic Reader UX Fixture And Browser Debug Coverage

**Files:**
- Modify: `examples/courses/render-fixture/raya.yaml`
- Modify: `examples/courses/render-fixture/course/0_index.md`
- Create: `examples/courses/render-fixture/course/4_reader_ux/0_index.md`
- Modify: `tests/contracts/test_static_builder.py`
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify: `packages/cli/src/raya_cli/render_debug.py`
- Modify: `packages/cli/src/raya_cli/render_debug_report.py`
- Modify: `tests/e2e/test_render_debug_parity_gate.py`

- [ ] **Step 1: Add failing fixture build assertions**

In `tests/contracts/test_static_builder.py`, extend `test_render_fixture_builds_rich_static_pages()` with a new reader UX page path after `numbered_objects_html_path`:

```python
    reader_ux_html_path = artifact / "site" / "reader-ux" / "index.html"
    assert reader_ux_html_path.exists()
    reader_ux_html = reader_ux_html_path.read_text(encoding="utf-8")
    reader_ux_visible = _visible_text(reader_ux_html)
```

Add assertions after the existing numbered object visible assertions:

```python
    assert "Reader UX Fixture" in reader_ux_visible
    assert "Remark 4.4" in reader_ux_visible
    assert "Example 4.1" in reader_ux_visible
    assert "Problem 4.1" in reader_ux_visible
    assert "Activity 4.1" in reader_ux_visible
    assert "Proof of Proposition 4.2" in reader_ux_visible
    assert "Solution sketch of Activity 4.1" in reader_ux_visible
    assert "raya-numbered-object--scannable" in reader_ux_html
    assert "raya-numbered-object-badge" in reader_ux_html
    assert "raya-numbered-object--caption" in reader_ux_html
    assert "raya-numbered-object--equation" in reader_ux_html
    assert "reader-facing fixture material" in reader_ux_visible.lower()
```

Extend the `numbered_index` checks in this test by building `by_id` if it is not already present:

```python
    by_id = {item["id"]: item for item in numbered_index["objects"]}
    assert by_id["orthogonal-remark"]["family"] == "remark"
    assert by_id["orthogonal-remark"]["style"] == "scannable"
    assert by_id["orthogonal-activity"]["style"] == "scannable"
    assert by_id["orthogonal-figure"]["style"] == "caption"
    assert by_id["orthogonal-equation"]["style"] == "equation"
```

- [ ] **Step 2: Run the fixture build test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages \
  -q
```

Expected: FAIL because `course/4_reader_ux/0_index.md` does not exist and the page is not rendered.

- [ ] **Step 3: Add realistic fixture source**

Create `examples/courses/render-fixture/course/4_reader_ux/0_index.md`:

```markdown
---
id: reader-ux
title: Reader UX Fixture
---

# Reader UX Fixture

This reader-facing fixture material demonstrates how a compact course note can
combine theorem-like content, equations, figures, tables, practice objects,
proofs, and static references without browser-side numbering.

We will use @orthogonal-definition, @orthogonal-proposition,
@orthogonal-remark, @orthogonal-example, @orthogonal-equation,
@orthogonal-figure, @orthogonal-table, @orthogonal-problem, and
@orthogonal-activity in one reading flow.

::: definition {#orthogonal-definition title="Orthogonal vectors"}
Vectors $u,v \in \mathbb{R}^n$ are orthogonal when their inner product satisfies
$\langle u,v\rangle = 0$.
:::

::: proposition {#orthogonal-proposition title="Projection residual"}
Let $u$ be nonzero and define
$$
p = \frac{\langle v,u\rangle}{\langle u,u\rangle}u.
$$
Then $v-p$ is orthogonal to $u$.
:::

::: proof {#proof-orthogonal-proposition of="orthogonal-proposition" title="Projection residual"}
Using @orthogonal-definition, compute
$$
\langle v-p,u\rangle
= \langle v,u\rangle
- \frac{\langle v,u\rangle}{\langle u,u\rangle}\langle u,u\rangle
= 0.
$$
:::

::: remark {#orthogonal-remark title="Why the residual matters"}
The residual $v-p$ records the part of $v$ that is invisible along the direction
of $u$. This is the geometric idea behind least-squares projection.
:::

::: example {#orthogonal-example title="A two-dimensional projection"}
For $u=\begin{bmatrix}1\\0\end{bmatrix}$ and
$v=\begin{bmatrix}2\\3\end{bmatrix}$, the projection is
$p=\begin{bmatrix}2\\0\end{bmatrix}$ and the residual is
$v-p=\begin{bmatrix}0\\3\end{bmatrix}$.
:::

::: equation {#orthogonal-equation}
$$
v = p + (v-p)
$$
:::

::: figure {#orthogonal-figure title="Projection as a decomposition"}
![Static path diagram](../_assets/diagrams/static-path.svg)
:::

::: table {#orthogonal-table title="Projection pieces"}
| Object | Formula | Role |
| --- | --- | --- |
| Projection | $p$ | visible along $u$ |
| Residual | $v-p$ | orthogonal to $u$ |
:::

::: problem {#orthogonal-problem title="Check the residual"}
Use [the projection residual](raya:ref/orthogonal-proposition) and
@orthogonal-equation to verify that the residual in @orthogonal-example is
orthogonal to $u$.
:::

::: activity {#orthogonal-activity title="Two-line explanation"}
Write two lines explaining why @orthogonal-figure and @orthogonal-table show the
same decomposition.
:::

::: proof {of="orthogonal-activity" title="Solution sketch"}
The activity follows by matching the visual decomposition in @orthogonal-figure
with the algebraic split in @orthogonal-equation, then naming the residual term
using @orthogonal-remark.
:::
```

- [ ] **Step 4: Link the fixture from the render fixture index**

In `examples/courses/render-fixture/course/0_index.md`, add a normal Markdown link near the other fixture links:

```markdown
Read the [reader UX fixture](4_reader_ux/0_index.md) for a realistic course-note flow using scannable numbered content.
```

- [ ] **Step 5: Update render fixture course config**

In `examples/courses/render-fixture/raya.yaml`, ensure the custom assignment sequence uses `scannable`:

```yaml
    sequences:
      assignment:
        label: Activity
        style: scannable
```

Keep the existing `homework`, `activity`, and `assignment` family overrides mapped to that sequence.

- [ ] **Step 6: Run the fixture build test and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages \
  -q
```

Expected: PASS.

- [ ] **Step 7: Update browser e2e assertions for scannable and reader UX**

In `tests/e2e/test_preview_static_read_path.py`, update `test_render_fixture_numbered_objects_are_static_and_local()`:

Replace:

```python
    assert any("raya-numbered-object--banded" in value for value in probe["classes"])
```

with:

```python
    assert any("raya-numbered-object--scannable" in value for value in probe["classes"])
```

Add a new browser test below it:

```python
def test_render_fixture_reader_ux_page_uses_scannable_static_numbering(
    tmp_path: Path,
) -> None:
    from playwright.sync_api import sync_playwright
    from raya_cli.preview import create_preview

    course = tmp_path / "render-fixture"
    shutil.copytree(RENDER_FIXTURE, course, ignore=shutil.ignore_patterns("artifact"))
    browser_executable = _browser_executable()

    handle = create_preview(course, host="127.0.0.1", port=0, dry_run=False)
    external_requests: list[str] = []
    try:
        assert handle.report.ok, [diagnostic.format() for diagnostic in handle.report.diagnostics]
        base_url = handle.base_url
        assert base_url is not None
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(browser_executable),
                headless=True,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.on(
                    "request",
                    lambda request: record_external_request(
                        request.url,
                        base_url,
                        external_requests,
                    ),
                )
                try:
                    page.goto(f"{base_url}/reader-ux/index.html", wait_until="networkidle")
                    _assert_no_horizontal_overflow(page)
                    _assert_visible_mathjax_output(page, minimum=3)
                    probe = page.evaluate(
                        """() => {
                          const objects = Array.from(document.querySelectorAll('.raya-numbered-object'));
                          return {
                            text: document.body.innerText,
                            objectIds: objects.map((node) => node.dataset.objectId),
                            classes: objects.map((node) => node.className),
                            badgeTexts: Array.from(document.querySelectorAll('.raya-numbered-object-badge'))
                              .map((node) => node.innerText),
                            refs: Array.from(document.querySelectorAll('a[href*="raya-object-"]'))
                              .map((node) => ({text: node.innerText, href: node.getAttribute('href')})),
                            proofHeadings: Array.from(document.querySelectorAll('.raya-proof-heading'))
                              .map((node) => node.innerText),
                            mathJaxScripts: Array.from(document.scripts)
                              .map((script) => script.src || script.textContent || '')
                              .filter((value) => value.includes('MathJax')),
                            visibleRawTex: document.body.innerText.includes('\\\\begin{bmatrix}'),
                          };
                        }"""
                    )
                finally:
                    page.close()
            finally:
                browser.close()
    finally:
        handle.close()

    assert set(probe["objectIds"]) >= {
        "orthogonal-definition",
        "orthogonal-proposition",
        "orthogonal-remark",
        "orthogonal-example",
        "orthogonal-equation",
        "orthogonal-figure",
        "orthogonal-table",
        "orthogonal-problem",
        "orthogonal-activity",
    }
    assert "Remark 4.4" in probe["text"]
    assert "Example 4.1" in probe["text"]
    assert "Activity 4.1" in probe["text"]
    assert any("raya-numbered-object--scannable" in value for value in probe["classes"])
    assert any("raya-numbered-object--caption" in value for value in probe["classes"])
    assert any("raya-numbered-object--equation" in value for value in probe["classes"])
    assert any("Remark" in value and "4.4" in value for value in probe["badgeTexts"])
    assert any(
        ref["text"] == "Proposition 4.2"
        and ref["href"].endswith("#raya-object-orthogonal-proposition")
        for ref in probe["refs"]
    )
    assert "Proof of Proposition 4.2" in " ".join(probe["proofHeadings"])
    assert "Solution sketch of Activity 4.1" in " ".join(probe["proofHeadings"])
    assert probe["mathJaxScripts"] == []
    assert probe["visibleRawTex"] is False
    assert external_requests == []
```

- [ ] **Step 8: Run the browser tests and verify RED or GREEN**

Run:

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_numbered_objects_are_static_and_local \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_ux_page_uses_scannable_static_numbering \
  -q
```

Expected: PASS after Tasks 1-3 changes. If it fails for expected numbering text, inspect generated `data/numbered-objects.json` and update only incorrect test expectations, not the contract.

- [ ] **Step 9: Add reader UX page to render-debug capture allowlists**

In `packages/cli/src/raya_cli/render_debug.py`, update `_available_page_names()`:

```python
    if (site_root / "reader-ux" / "index.html").is_file():
        page_names.append("reader-ux")
```

Place it after the numbered-objects page block.

In `packages/cli/src/raya_cli/render_debug_report.py`, update `_expected_page_names()`:

```python
    if (site_dir / "reader-ux" / "index.html").is_file():
        page_names.append("reader-ux")
```

Place it after the numbered-objects page block.

- [ ] **Step 10: Update render-debug screenshot expectations**

In `tests/e2e/test_preview_static_read_path.py`, in `test_capture_render_debug_writes_screenshots_and_summary()`, add these expected screenshots:

```python
        "desktop-reader-ux.png",
        "mobile-reader-ux.png",
```

Add report check IDs:

```python
        "capture:reader-ux:desktop",
        "capture:reader-ux:mobile",
```

Add a reader UX evidence check after the existing `numbered_capture` assertions:

```python
    reader_capture = next(
        capture
        for capture in summary["captures"]
        if capture["page"] == "reader-ux"
        and capture["viewport"]["name"] == "desktop"
    )
    reader_evidence = reader_capture["numbered_content"]
    assert {item["id"] for item in reader_evidence["objects"]} >= {
        "orthogonal-remark",
        "orthogonal-activity",
    }
    assert {item["target_text"] for item in reader_evidence["proofs"]} >= {
        "Proposition 4.2",
        "Activity 4.1",
    }
```

- [ ] **Step 11: Update render-debug parity gate expectations**

In `tests/e2e/test_render_debug_parity_gate.py`, find the passing render-fixture parity test and extend it to assert reader UX checks are present:

```python
    assert "capture:reader-ux:desktop" in check_ids
    assert "capture:reader-ux:mobile" in check_ids
    assert "numbered-content:reader-ux:desktop" in check_ids
    assert "numbered-content:reader-ux:mobile" in check_ids
```

If the test currently computes `check_ids` inline, create it with:

```python
    check_ids = {check["id"] for check in report["checks"]}
```

- [ ] **Step 12: Run focused render-debug tests**

Run:

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/e2e/test_preview_static_read_path.py::test_capture_render_debug_writes_screenshots_and_summary \
  tests/e2e/test_render_debug_parity_gate.py::test_render_debug_parity_gate_passes_on_render_fixture_copy \
  -q
```

Expected: PASS.

- [ ] **Step 13: Run render-debug script**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS. Confirm the output includes `render-debug-report: passed`.

- [ ] **Step 14: Commit fixture and render-debug coverage**

Commit only fixture, render-debug, and e2e changes:

```bash
git add \
  examples/courses/render-fixture/raya.yaml \
  examples/courses/render-fixture/course/0_index.md \
  examples/courses/render-fixture/course/4_reader_ux/0_index.md \
  tests/contracts/test_static_builder.py \
  tests/e2e/test_preview_static_read_path.py \
  tests/e2e/test_render_debug_parity_gate.py \
  packages/cli/src/raya_cli/render_debug.py \
  packages/cli/src/raya_cli/render_debug_report.py
git commit -m "Add reader UX render fixture"
```

## Task 4: Foundation And Role Documentation

**Files:**
- Modify: `docs/foundation/17_rendering_execution_plan.md`
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/agentes/index.md`
- Modify: `tests/contracts/test_renderer_dependencies.py`

- [ ] **Step 1: Add failing docs contract assertions**

In `tests/contracts/test_renderer_dependencies.py`, find `test_role_docs_cover_numbered_objects_and_references()` and add these needles to the relevant role docs.

For English professor docs:

```python
                "`scannable`",
                "remark",
                "course-level",
```

For English student docs:

```python
                "scannable",
                "Remark",
```

For English contributor docs:

```python
                "`scannable`",
                "`remark`",
                "course-level",
```

For English agent docs:

```python
                "`scannable`",
                "`remark`",
                "reader UX fixture",
```

For Spanish professor docs:

```python
                "`scannable`",
                "`remark`",
                "nivel de curso",
```

For Spanish student docs:

```python
                "scannable",
                "Remark",
```

For Spanish contributor docs:

```python
                "`scannable`",
                "`remark`",
                "nivel de curso",
```

For Spanish agent docs:

```python
                "`scannable`",
                "`remark`",
                "fixture de reader UX",
```

Add a foundation assertion to an existing rendering-plan docs test if one exists. If no focused test exists, add this small test to `tests/contracts/test_renderer_dependencies.py`:

```python
def test_foundation_rendering_plan_covers_scannable_reader_ux() -> None:
    text = (ROOT / "docs/foundation/17_rendering_execution_plan.md").read_text(
        encoding="utf-8"
    )

    assert "`remark`" in text
    assert "`scannable`" in text
    assert "course-level" in text
    assert "page/section" in text
```

- [ ] **Step 2: Run docs contract tests and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_renderer_dependencies.py::test_role_docs_cover_numbered_objects_and_references \
  tests/contracts/test_renderer_dependencies.py::test_foundation_rendering_plan_covers_scannable_reader_ux \
  -q
```

Expected: FAIL because docs do not yet include the new reader UX guidance.

- [ ] **Step 3: Update foundation rendering plan**

In `docs/foundation/17_rendering_execution_plan.md`, update the numbered objects accepted baseline paragraph to mention:

```markdown
`remark` is a built-in theorem-family object. The default reader presentation
uses the `scannable` style for theorem, example, exercise, and assignment
sequences; figure and table keep caption presentation, and equation keeps
equation presentation. Course-level `render.numbered_objects` sequence and
family overrides remain the current customization surface. Page/section style
overrides are future work.
```

Keep this near the existing numbered-object rendering bullets.

- [ ] **Step 4: Update English role docs**

Make concise additions:

`docs/guides/en/professors/index.md` should say:

```markdown
The default reader style for theorem-like and coursework objects is `scannable`.
Use `remark` for short theorem-family observations. Course-level
`render.numbered_objects` overrides can change sequence styles and labels; page
or section overrides are not current behavior.
```

`docs/guides/en/students/index.md` should say:

```markdown
Numbered learning objects use a scannable reader style by default. The visible
badge is for navigation; links such as `Theorem 3.1` or `Remark 4.4` are still
static references generated during build.
```

`docs/guides/en/contributors/index.md` should say:

```markdown
Preserve `scannable` as the default style for theorem, example, exercise, and
assignment sequences, and preserve `remark` as a theorem-family built-in. Keep
customization at the course-level `render.numbered_objects` surface until a
future page/section override contract exists.
```

`docs/guides/en/agents/index.md` should say:

```markdown
For reader UX checks, use the reader UX fixture source page and inspect
`scannable` objects, `remark`, static references, proof targets, and
`data/numbered-objects.json`. Do not infer numbered-object truth from scraped
HTML.
```

- [ ] **Step 5: Update Spanish role docs**

Make concise additions:

`docs/guides/es/profesores/index.md` should say:

```markdown
El estilo lector predeterminado para objetos tipo teorema y trabajo de curso es
`scannable`. Usa `remark` para observaciones breves de la familia theorem. Los
overrides de `render.numbered_objects` a nivel de curso pueden cambiar estilos y
etiquetas de secuencia; los overrides por pagina o seccion no son comportamiento
actual.
```

`docs/guides/es/estudiantes/index.md` should say:

```markdown
Los objetos numerados de aprendizaje usan un estilo scannable por defecto. La
insignia visible ayuda a navegar; links como `Theorem 3.1` o `Remark 4.4` siguen
siendo referencias estaticas generadas durante build.
```

`docs/guides/es/colaboradores/index.md` should say:

```markdown
Preserva `scannable` como estilo predeterminado para secuencias theorem,
example, exercise y assignment, y preserva `remark` como built-in de la familia
theorem. Mantiene la personalizacion en la superficie `render.numbered_objects`
a nivel de curso hasta que exista un contrato futuro de overrides por pagina o
seccion.
```

`docs/guides/es/agentes/index.md` should say:

```markdown
Para checks de reader UX, usa la pagina source del fixture de reader UX e
inspecciona objetos `scannable`, `remark`, referencias estaticas, objetivos de
prueba y `data/numbered-objects.json`. No infieras la verdad de objetos
numerados desde HTML scrapeado.
```

Keep technical identifiers in English. Avoid adding new English prose where a Spanish phrase is natural.

- [ ] **Step 6: Run docs contract tests and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_renderer_dependencies.py::test_role_docs_cover_numbered_objects_and_references \
  tests/contracts/test_renderer_dependencies.py::test_foundation_rendering_plan_covers_scannable_reader_ux \
  -q
```

Expected: PASS.

- [ ] **Step 7: Check Spanish wording for avoidable English from this task**

Run:

```bash
rg -n "source page|reader style|course-level|page/section|scraped HTML|proof targets|static references" docs/guides/es
```

Expected: no hits from the newly added Spanish prose. Existing technical identifiers such as `reader UX`, `source`, `scannable`, `render.numbered_objects`, and `data/numbered-objects.json` are acceptable where intentional.

- [ ] **Step 8: Commit docs**

Commit only docs and docs contract tests:

```bash
git add \
  docs/foundation/17_rendering_execution_plan.md \
  docs/guides/en/professors/index.md \
  docs/guides/en/students/index.md \
  docs/guides/en/contributors/index.md \
  docs/guides/en/agents/index.md \
  docs/guides/es/profesores/index.md \
  docs/guides/es/estudiantes/index.md \
  docs/guides/es/colaboradores/index.md \
  docs/guides/es/agentes/index.md \
  tests/contracts/test_renderer_dependencies.py
git commit -m "Document numbered content reader UX"
```

## Task 5: Final Verification And Review

**Files:**
- No planned source edits unless verification or review finds a defect.

- [ ] **Step 1: Run focused contract and e2e tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/contracts/test_numbered_objects.py \
  tests/contracts/test_static_builder.py \
  tests/contracts/test_renderer_dependencies.py \
  tests/e2e/test_render_debug_report.py \
  -q
```

Expected: PASS.

- [ ] **Step 2: Run focused browser tests**

Run:

```bash
RAYA_TEST_BROWSER=/usr/bin/google-chrome UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_numbered_objects_are_static_and_local \
  tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_ux_page_uses_scannable_static_numbering \
  tests/e2e/test_preview_static_read_path.py::test_capture_render_debug_writes_screenshots_and_summary \
  tests/e2e/test_render_debug_parity_gate.py::test_render_debug_parity_gate_passes_on_render_fixture_copy \
  -q
```

Expected: PASS.

- [ ] **Step 3: Run render-debug parity script**

Run:

```bash
./scripts/check-render-debug.sh
```

Expected: PASS with `check-render-debug: passed`.

- [ ] **Step 4: Run host canonical gate**

Run:

```bash
./scripts/check.sh
```

Expected: PASS with `check: passed`.

- [ ] **Step 5: Run Docker canonical gate**

Run:

```bash
./scripts/check-docker.sh
```

Expected: PASS with `check-docker: passed`.

- [ ] **Step 6: Request final code review**

Use `superpowers:requesting-code-review`.

Review range should start at the implementation base commit. At the start of
Task 1, record the plan commit SHA:

```bash
IMPLEMENTATION_BASE_SHA=$(git rev-parse HEAD)
```

When requesting final review, use:

```bash
BASE_SHA=$IMPLEMENTATION_BASE_SHA
HEAD_SHA=$(git rev-parse HEAD)
```

Ask the reviewer to check:

- `remark` defaults and `scannable` style behavior,
- course-level override preservation,
- no page/section override implementation,
- rendered HTML remains reader-facing and static,
- `data/numbered-objects.json` remains machine authority,
- no browser-side MathJax or external renderer requests,
- realistic fixture is labeled fixture material and not pedagogy canon,
- English and Spanish role docs stay separated.

- [ ] **Step 7: Fix review findings with TDD**

If the final reviewer reports Critical or Important issues:

1. Use `superpowers:systematic-debugging` for unexpected failures.
2. Write or update a focused failing test.
3. Run it and verify RED.
4. Implement the minimal fix.
5. Run it and verify GREEN.
6. Rerun the relevant focused suite.
7. Commit the fix.
8. Send the reviewer a re-review request.

Do not proceed with unfixed Critical or Important findings.

- [ ] **Step 8: Confirm clean status**

Run:

```bash
git status --short --branch
```

Expected: clean working tree on `new_rayalucaria`, ahead of `origin/new_rayalucaria`.

- [ ] **Step 9: Finish branch**

Use `superpowers:finishing-a-development-branch` after all verification and review pass. Present the standard options to the user; do not push unless the user asks.
