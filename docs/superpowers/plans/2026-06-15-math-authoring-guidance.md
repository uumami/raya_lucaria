# Math Authoring Guidance Implementation Plan

> **Supersession note:** The theorem/proof/numbered-object status in this June 15 math-authoring plan captured the pre-numbered-object baseline. Current behavior is superseded by `docs/superpowers/specs/2026-06-15-numbered-objects-cross-references-design.md`, `docs/superpowers/specs/2026-06-16-proof-blocks-design.md`, and `docs/superpowers/plans/2026-06-16-proof-blocks.md`.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dedicated math authoring fixture page, role-specific guidance, and tests that lock current build-time MathJax authoring patterns. The theorem/proof handoff language in this historical plan has since been superseded by the numbered-object and proof-block design docs listed above.

**Architecture:** Keep renderer behavior unchanged. Add source fixture content under `examples/courses/render-fixture/course/`, update role docs in separate English and Spanish pages, and lock both surfaces through existing static-builder/e2e/contract tests. The fixture demonstrates only valid current MathJax/Markdown patterns; invalid examples stay in tests and diagnostic guidance.

**Tech Stack:** Python 3.10, `uv`, `pytest`, Glintstone static builder, Playwright/Chromium render-debug gate, Markdown role docs.

---

## File Structure

- Create `examples/courses/render-fixture/course/2_math_authoring/0_index.md`: fixture-only page for accepted math authoring patterns and theorem-like current Markdown patterns.
- Modify `examples/courses/render-fixture/course/0_index.md`: add a local link to the new fixture page so generated navigation and static-read-path tests can reach it.
- Modify `tests/contracts/test_static_builder.py`: assert the new fixture page builds, renders MathJax CHTML, and does not leak raw TeX markers in visible text.
- Modify `tests/e2e/test_preview_static_read_path.py`: include the new fixture page in browser/render-debug checks where static-read-path coverage is already exercised.
- Modify `tests/contracts/test_renderer_dependencies.py`: add a role-doc guidance contract for current math examples and the theorem-support next loop.
- Modify role docs:
  - `docs/guides/en/professors/index.md`
  - `docs/guides/en/students/index.md`
  - `docs/guides/en/contributors/index.md`
  - `docs/guides/en/agents/index.md`
  - `docs/guides/es/profesores/index.md`
  - `docs/guides/es/estudiantes/index.md`
  - `docs/guides/es/colaboradores/index.md`
  - `docs/guides/es/agentes/index.md`

---

### Task 1: Add Failing Fixture Rendering Contract

**Files:**
- Modify: `tests/contracts/test_static_builder.py`
- Create later: `examples/courses/render-fixture/course/2_math_authoring/0_index.md`
- Modify later: `examples/courses/render-fixture/course/0_index.md`

- [ ] **Step 1: Add the failing fixture assertions**

In `tests/contracts/test_static_builder.py`, inside `test_rich_static_fixture_renders_markdown_math_code_and_assets`, after `nested_html` is read, add:

```python
    math_authoring_html = (
        course / "artifact" / "site" / "math-authoring" / "index.html"
    ).read_text(encoding="utf-8")
    math_authoring_visible = _visible_text(math_authoring_html)
```

Then after the existing root-page visible text assertions, add:

```python
    assert 'href="math-authoring/index.html"' in html
```

Then after the existing nested-page assertions, add:

```python
    assert '<link rel="stylesheet" href="../_raya/render/rich.css">' in math_authoring_html
    assert (
        '<link rel="stylesheet" href="../_raya/render/math/mathjax.css">'
        in math_authoring_html
    )
    assert "Math Authoring Fixture" in math_authoring_visible
    assert "Inline And Display Math" in math_authoring_visible
    assert "Vectors And Matrices" in math_authoring_visible
    assert "Page Local Macros" in math_authoring_visible
    assert "Sets Logic And Functions" in math_authoring_visible
    assert "Aligned Derivations And Optimization" in math_authoring_visible
    assert "Theorem Like Writing With Current Markdown" in math_authoring_visible
    assert "Macro Redefinition" in math_authoring_visible
    assert "mjx-container" in math_authoring_html
    assert "This theorem-like block is authored Markdown" in math_authoring_visible
    assert "This historical fixture text captured the pre-numbered-object baseline" in math_authoring_visible
    for raw_marker in (
        "\\newcommand",
        "\\renewcommand",
        "\\begin{bmatrix}",
        "\\rayaVec",
        "\\fixtureNorm",
        "\\forall",
        "\\label",
        "\\ref",
    ):
        assert raw_marker not in math_authoring_visible
    assert "$" not in math_authoring_visible
```

- [ ] **Step 2: Run the contract test and verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_rich_static_fixture_renders_markdown_math_code_and_assets
```

Expected: FAIL because `artifact/site/math-authoring/index.html` does not exist.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/contracts/test_static_builder.py
git commit -m "Test math authoring fixture rendering"
```

---

### Task 2: Add The Math Authoring Fixture Page

**Files:**
- Create: `examples/courses/render-fixture/course/2_math_authoring/0_index.md`
- Modify: `examples/courses/render-fixture/course/0_index.md`
- Test: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Create the fixture page**

Create `examples/courses/render-fixture/course/2_math_authoring/0_index.md` with exactly this content:

````markdown
---
id: math-authoring
title: Math Authoring Fixture
summary: Fixture page for current build-time MathJax authoring patterns.
status: ready
---

# Math Authoring Fixture

This is fixture material for renderer and documentation tests. It is not canonical pedagogy or architecture truth. Fixture authority remains in docs/foundation/.

This page demonstrates current valid math authoring patterns. Invalid examples belong in tests and diagnostics, not in copyable course notes.

## Inline And Display Math

Inline math such as $e^{i\pi} + 1 = 0$ should be typeset during build.

Display math uses delimiter lines on their own:

$$
\int_0^1 x^2\,dx = \frac{1}{3}
$$

Escaped currency stays text, such as \$10.

## Vectors And Matrices

Page-local vector notation can be defined before use:
$\newcommand{\rayaVec}[1]{\mathbf{#1}}$.

Vectors and matrices should render without raw TeX leakage:

$$
\begin{bmatrix}
1 & 2 \\
3 & 4
\end{bmatrix}
\rayaVec{x}
=
\rayaVec{y}
$$

## Page Local Macros

Define page-local macros before the expressions that use them:
$\newcommand{\fixtureNorm}[1]{\left\lVert #1 \right\rVert}\newcommand{\fixtureInner}[2]{\left\langle #1, #2 \right\rangle}$.

Norms and inner products should render as MathJax output:

$$
\fixtureNorm{\rayaVec{x}}^2 = \fixtureInner{\rayaVec{x}}{\rayaVec{x}}
$$

## Sets Logic And Functions

Set, logic, and function notation should render in ordinary course notes:

$$
f: A \to B,
\qquad
\forall x \in A,\ \exists y \in B \text{ such that } y = f(x)
$$

Sequences and limits should render before publication:

$$
(a_n)_{n\ge 1},
\qquad
\lim_{n\to\infty} a_n = L
$$

## Aligned Derivations And Optimization

Aligned derivations stay in one display block:

$$
\begin{aligned}
g(\theta)
  &= \sum_{i=1}^{n} \log p(x_i\mid\theta) \\
\hat{\theta}
  &= \operatorname*{arg\,max}_{\theta \in \Theta} g(\theta)
\end{aligned}
$$

Cases remain part of the accepted MathJax subset:

$$
h(x) =
\begin{cases}
x^2, & x \ge 0 \\
-x, & x < 0
\end{cases}
$$

## Theorem Like Writing With Current Markdown

This historical fixture section captured the pre-numbered-object baseline. Current theorem, proof, numbered-object, and reference behavior is superseded by the June 15 numbered-object design and the June 16 proof-block design/plan.

> [!NOTE]
> **Theorem.** This theorem-like block is authored Markdown. It is not an automatic theorem environment.
>
> If $a,b \in \mathbb{R}$, then
>
> $$
> (a+b)^2 = a^2 + 2ab + b^2.
> $$

**Proof.** Expand the product and collect terms:

$$
(a+b)(a+b) = a^2 + ab + ba + b^2.
$$

This baseline wording was superseded once numbered objects and proof blocks landed.

## Macro Redefinition

Page-local redefinition is accepted when it remains local to the page:
$\newcommand{\fixtureUnit}{\mathrm{unit}}\renewcommand{\fixtureUnit}{\mathrm{u}}$.

The redefined macro should render before publication:

$$
\rayaVec{v}_{\fixtureUnit}
=
\begin{bmatrix}
5 \\
8
\end{bmatrix}
$$
````

- [ ] **Step 2: Link the fixture from the root page**

In `examples/courses/render-fixture/course/0_index.md`, after:

```markdown
Read the [static path page](raya:static-path) and inspect the [static path note](_assets/diagrams/static-path.txt).
```

add:

```markdown
Read the [math authoring fixture](2_math_authoring/0_index.md) for current build-time MathJax authoring patterns.
```

- [ ] **Step 3: Run the focused contract test**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py::test_rich_static_fixture_renders_markdown_math_code_and_assets
```

Expected: PASS.

- [ ] **Step 4: Commit the fixture**

```bash
git add examples/courses/render-fixture/course/0_index.md examples/courses/render-fixture/course/2_math_authoring/0_index.md
git commit -m "Add math authoring render fixture"
```

---

### Task 3: Add Browser And Render-Debug Coverage For The New Fixture Page

**Files:**
- Modify: `tests/e2e/test_preview_static_read_path.py`
- Modify if needed: `packages/cli/src/raya_cli/render_debug.py`
- Modify if needed: `packages/cli/src/raya_cli/render_debug_report.py`

- [ ] **Step 1: Add failing browser assertions for the new page**

In `tests/e2e/test_preview_static_read_path.py`, inside `_run_render_fixture_math_check`, after the block that checks `static-path/index.html`, add:

```python
                        page.goto(
                            f"{base_url}/math-authoring/index.html",
                            wait_until="networkidle",
                        )
                        _assert_no_horizontal_overflow(page)
                        _assert_visible_mathjax_output(page, minimum=7)
                        math_authoring_text = page.locator("body").inner_text()
                        assert raw_tex_markers_from_text(math_authoring_text) == []
                        assert "This historical fixture text captured the pre-numbered-object baseline" in math_authoring_text
```

- [ ] **Step 2: Extend expected render-debug screenshots**

In `test_capture_render_debug_writes_screenshots_and_summary`, extend `expected_screenshots` to include:

```python
        "desktop-math-authoring.png",
        "mobile-math-authoring.png",
```

Then extend the expected check IDs set to include:

```python
        "capture:math-authoring:desktop",
        "capture:math-authoring:mobile",
```

- [ ] **Step 3: Run the focused e2e tests and verify the render-debug assertions fail**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_math_renders_in_browser_without_external_requests tests/e2e/test_preview_static_read_path.py::test_capture_render_debug_writes_screenshots_and_summary
```

Expected: browser page check may pass, but `test_capture_render_debug_writes_screenshots_and_summary` FAILS until render-debug captures `math-authoring`.

- [ ] **Step 4: Add `math-authoring` to render-debug page names**

In `packages/cli/src/raya_cli/render_debug.py`, update the page-name collection so it includes the new page. If the file has a constant such as `RENDER_DEBUG_PAGE_NAMES`, change it from:

```python
RENDER_DEBUG_PAGE_NAMES = ("index", "static-path")
```

to:

```python
RENDER_DEBUG_PAGE_NAMES = ("index", "static-path", "math-authoring")
```

If the file uses equivalent page metadata instead of that exact constant, add an entry with:

```python
("math-authoring", "math-authoring/index.html")
```

matching the existing local pattern.

- [ ] **Step 5: Update report expected captures**

In `packages/cli/src/raya_cli/render_debug_report.py`, update the expected capture map from:

```python
("static-path", "mobile"): "mobile-static-path.png",
```

to include:

```python
("math-authoring", "desktop"): "desktop-math-authoring.png",
("math-authoring", "mobile"): "mobile-math-authoring.png",
```

Place the new entries beside the existing `index` and `static-path` entries.

- [ ] **Step 6: Run focused e2e tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_render_fixture_math_renders_in_browser_without_external_requests tests/e2e/test_preview_static_read_path.py::test_capture_render_debug_writes_screenshots_and_summary
```

Expected: PASS.

- [ ] **Step 7: Run the direct render-debug gate**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local scripts/check-render-debug.sh
```

Expected: PASS with `render-debug-report:` and `check-render-debug: passed`.

- [ ] **Step 8: Commit browser/debug coverage**

```bash
git add tests/e2e/test_preview_static_read_path.py packages/cli/src/raya_cli/render_debug.py packages/cli/src/raya_cli/render_debug_report.py
git commit -m "Cover math authoring fixture in render debug"
```

---

### Task 4: Lock Role Documentation Guidance With A Contract Test

**Files:**
- Modify: `tests/contracts/test_renderer_dependencies.py`
- Modify later: all role docs listed in the file structure.

- [ ] **Step 1: Add the failing role-doc contract test**

In `tests/contracts/test_renderer_dependencies.py`, after `test_render_debug_report_module_and_guidance_are_declared`, add:

```python
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
```

- [ ] **Step 2: Run the contract test and verify it fails**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_renderer_dependencies.py::test_math_authoring_guidance_and_theorem_handoff_are_documented
```

Expected: FAIL because role docs do not yet mention the new fixture path and theorem handoff consistently.

- [ ] **Step 3: Commit the failing contract**

```bash
git add tests/contracts/test_renderer_dependencies.py
git commit -m "Test math authoring role guidance"
```

---

### Task 5: Update English Role Docs

**Files:**
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/en/students/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Test: `tests/contracts/test_renderer_dependencies.py`

- [ ] **Step 1: Update professor guidance**

In `docs/guides/en/professors/index.md`, after the paragraph that starts `For common course notation`, add:

```markdown
Use `examples/courses/render-fixture/course/2_math_authoring/0_index.md` as the current fixture reference for copyable build-time MathJax patterns. It covers inline and display math, `\begin{bmatrix}` matrices, vector macros, `\newcommand`, `\renewcommand`, set and logic notation, norms, inner products, aligned derivations, and optimization notation. Define macros before use, keep them page-local, and use `$$` delimiter lines for larger expressions.

For current theorem/proof/numbered-object behavior, follow the superseding numbered-object and proof-block design docs listed at the top of this historical plan.
```

- [ ] **Step 2: Update student guidance**

In `docs/guides/en/students/index.md`, after the paragraph that starts `If math appears as raw TeX commands`, add:

```markdown
Rendered matrices, vectors, set notation, theorem-like notes, and proofs should appear as normal course text plus typeset math. If you see raw `\begin{bmatrix}`, an unknown macro, visible dollar-delimited math, or a page asking your browser to load browser-side MathJax, report it to the course team with the page URL or title.
```

- [ ] **Step 3: Update contributor guidance**

In `docs/guides/en/contributors/index.md`, after the paragraph that starts `Rich static rendering is Glintstone-owned`, add:

```markdown
Use `examples/courses/render-fixture/course/2_math_authoring/0_index.md` when changing math rendering or authoring guidance. It is the fixture target for current valid examples: `\begin{bmatrix}`, vector macros, `\newcommand`, `\renewcommand`, set and logic notation, norms, inner products, aligned derivations, optimization notation, and theorem-like Markdown. Keep invalid math examples in tests so professor and student docs remain copyable.

For current theorem/proof/numbered-object behavior, follow the superseding numbered-object and proof-block design docs listed at the top of this historical plan.
```

- [ ] **Step 4: Update agent guidance**

In `docs/guides/en/agents/index.md`, after the paragraph that starts `For rich static rendering`, add:

```markdown
For math authoring checks, use `examples/courses/render-fixture/course/2_math_authoring/0_index.md` as the focused source fixture. Verify source pages rather than generated `artifact/` files, and use render-debug evidence to confirm there is no raw visible TeX, no browser-side MathJax conversion, and no external renderer request. For current theorem/proof/numbered-object behavior, follow the superseding numbered-object and proof-block design docs listed at the top of this historical plan.
```

- [ ] **Step 5: Run the role-doc contract**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_renderer_dependencies.py::test_math_authoring_guidance_and_theorem_handoff_are_documented
```

Expected: still FAIL because Spanish docs are not updated yet.

- [ ] **Step 6: Commit English docs**

```bash
git add docs/guides/en/professors/index.md docs/guides/en/students/index.md docs/guides/en/contributors/index.md docs/guides/en/agents/index.md
git commit -m "Document math authoring guidance in English"
```

---

### Task 6: Update Spanish Role Docs

**Files:**
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/es/estudiantes/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/es/agentes/index.md`
- Test: `tests/contracts/test_renderer_dependencies.py`

- [ ] **Step 1: Update professor guidance in Spanish**

In `docs/guides/es/profesores/index.md`, after the paragraph that starts `Para notacion comun de curso`, add:

```markdown
Usa `examples/courses/render-fixture/course/2_math_authoring/0_index.md` como referencia fixture actual para patrones copiables de MathJax en build. Cubre math inline y display, matrices `\begin{bmatrix}`, macros de vectores, `\newcommand`, `\renewcommand`, notacion de conjuntos y logica, normas, productos internos, derivaciones alineadas y notacion de optimizacion. Define macros antes de usarlas, mantenlas locales a la pagina y usa delimitadores `$$` en lineas propias para expresiones grandes.

Nota de supersesion: esta guia de Junio 15 describia el baseline anterior. El soporte actual para objetos numerados y proof blocks esta en `docs/superpowers/specs/2026-06-15-numbered-objects-cross-references-design.md`, `docs/superpowers/specs/2026-06-16-proof-blocks-design.md` y `docs/superpowers/plans/2026-06-16-proof-blocks.md`.
```

- [ ] **Step 2: Update student guidance in Spanish**

In `docs/guides/es/estudiantes/index.md`, after the paragraph that starts `Si la math aparece como comandos TeX crudos`, add:

```markdown
Matrices renderizadas, vectores, notacion de conjuntos, notas tipo theorem y proofs deben aparecer como texto normal del curso mas math compuesta. Si ves `\begin{bmatrix}` crudo, una macro desconocida, math visible con delimitadores de dolar, o una pagina que pide cargar browser-side MathJax, reportalo al equipo del curso con la URL o titulo de la pagina.
```

- [ ] **Step 3: Update contributor guidance in Spanish**

In `docs/guides/es/colaboradores/index.md`, after the paragraph that starts `El rich static rendering pertenece a Glintstone`, add:

```markdown
Usa `examples/courses/render-fixture/course/2_math_authoring/0_index.md` cuando cambies rendering de math o guia de autoria. Es el fixture target para ejemplos validos actuales: `\begin{bmatrix}`, macros de vectores, `\newcommand`, `\renewcommand`, notacion de conjuntos y logica, normas, productos internos, derivaciones alineadas, notacion de optimizacion y Markdown tipo theorem. Mantiene ejemplos invalidos de math en tests para que docs de profesores y estudiantes sigan siendo copiables.

Para comportamiento actual de theorems/proofs/numbered objects, sigue los docs superseding de numbered objects y proof blocks listados al inicio de este plan historico.
```

- [ ] **Step 4: Update agent guidance in Spanish**

In `docs/guides/es/agentes/index.md`, after the paragraph that starts `Para rich static rendering`, add:

```markdown
Para checks de autoria de math, usa `examples/courses/render-fixture/course/2_math_authoring/0_index.md` como fixture source enfocado. Verifica paginas source en vez de archivos generados bajo `artifact/`, y usa evidencia de render-debug para confirmar que no hay TeX crudo visible, conversion browser-side MathJax ni requests externos del renderer. Para comportamiento actual de theorems/proofs/numbered objects, sigue los docs superseding de numbered objects y proof blocks listados al inicio de este plan historico.
```

- [ ] **Step 5: Run the role-doc contract**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_renderer_dependencies.py::test_math_authoring_guidance_and_theorem_handoff_are_documented
```

Expected: PASS.

- [ ] **Step 6: Commit Spanish docs**

```bash
git add docs/guides/es/profesores/index.md docs/guides/es/estudiantes/index.md docs/guides/es/colaboradores/index.md docs/guides/es/agentes/index.md
git commit -m "Document math authoring guidance in Spanish"
```

---

### Task 7: Focused Verification

**Files:**
- No source edits unless verification finds a failure.

- [ ] **Step 1: Run focused contract and e2e tests**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py tests/contracts/test_renderer_dependencies.py tests/e2e/test_preview_static_read_path.py
```

Expected: PASS.

- [ ] **Step 2: Run direct render-debug gate**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local scripts/check-render-debug.sh
```

Expected: PASS with `render-debug-report:` and `check-render-debug: passed`.

- [ ] **Step 3: Commit verification fixes if needed**

If any focused verification fix is required, commit it:

```bash
git add examples/courses/render-fixture/course/0_index.md \
  examples/courses/render-fixture/course/2_math_authoring/0_index.md \
  packages/cli/src/raya_cli/render_debug.py \
  packages/cli/src/raya_cli/render_debug_report.py \
  tests/contracts/test_static_builder.py \
  tests/contracts/test_renderer_dependencies.py \
  tests/e2e/test_preview_static_read_path.py \
  docs/guides/en/professors/index.md \
  docs/guides/en/students/index.md \
  docs/guides/en/contributors/index.md \
  docs/guides/en/agents/index.md \
  docs/guides/es/profesores/index.md \
  docs/guides/es/estudiantes/index.md \
  docs/guides/es/colaboradores/index.md \
  docs/guides/es/agentes/index.md
git commit -m "Fix math authoring guidance verification"
```

If no files changed, do not create an empty commit.

---

### Task 8: Full Verification And Execution Status

**Files:**
- Modify: `docs/superpowers/plans/2026-06-15-math-authoring-guidance.md`

- [ ] **Step 1: Run host archive gate**

Run:

```bash
./scripts/check.sh
```

Expected: PASS with `check: passed`.

- [ ] **Step 2: Run Docker archive gate**

Run:

```bash
./scripts/check-docker.sh
```

Expected: PASS with `check-docker: passed`.

- [ ] **Step 3: Request code review**

Use `superpowers:requesting-code-review` over commits after `b83d9b0`.

Reviewer prompt:

```text
Review the math authoring guidance implementation. Focus on whether fixture examples stay within the accepted MathJax subset, no raw TeX leakage, role-doc accuracy in English and Spanish, theorem/proof functionality being clearly next rather than current, no browser-side MathJax/CDN regression, and whether tests lock the right surfaces without overfitting generated output.
```

- [ ] **Step 4: Address accepted review findings with TDD**

For each Critical or Important accepted review finding:

```text
1. Write or update a focused failing test.
2. Run it and confirm it fails for the expected reason.
3. Implement the minimal fix.
4. Re-run the focused test and relevant gate.
5. Commit the fix.
```

- [ ] **Step 5: Append execution status**

Run this command to collect the implementation commits:

```bash
git log --oneline --reverse b83d9b0..HEAD
```

Append an `## Execution Status` section to `docs/superpowers/plans/2026-06-15-math-authoring-guidance.md` that lists:

- each commit shown by the command,
- the focused pytest command and result,
- the direct `scripts/check-render-debug.sh` result,
- the host `./scripts/check.sh` result,
- the Docker `./scripts/check-docker.sh` result,
- the final code-review result.

Do not use invented hashes or invented counts. Copy the real commit subjects from `git log`, and copy the final verification counts from the command output.

- [ ] **Step 6: Commit execution status**

```bash
git add docs/superpowers/plans/2026-06-15-math-authoring-guidance.md
git commit -m "Track math authoring guidance execution"
```

## Self-Review

- Spec coverage: tasks cover a dedicated fixture page, current valid math examples, role docs in English and Spanish, student reporting guidance, contributor/agent diagnostics, render-debug/static parity, and the theorem/proof next-loop boundary.
- Template scan: no unresolved implementation template values remain in the plan.
- Type consistency: the plan consistently uses `math-authoring`, `2_math_authoring/0_index.md`, `report.json`, `index.html`, and `scripts/check-render-debug.sh`.

## Execution Status

Implementation commits from `git log --oneline --reverse b83d9b0..HEAD` before this status commit:

```text
f0e570a Plan math authoring guidance
4f3bc42 Test math authoring fixture rendering
ed8bfd1 Add math authoring render fixture
17e1c5f Tighten math authoring raw TeX guard
330f25a Cover math authoring fixture in render debug
4cfe93b Test math authoring role guidance
d8f2851 Document math authoring guidance in English
79f41e8 Document math authoring guidance in Spanish
17462e1 Fix render debug CLI capture contract
```

Focused pytest:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py tests/contracts/test_renderer_dependencies.py tests/e2e/test_preview_static_read_path.py
```

Result: `57 passed in 102.44s (0:01:42)`.

Direct render-debug gate:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local scripts/check-render-debug.sh
```

Result: `render-debug-report: passed (34 check(s), report=/tmp/raya-render-debug.ui092f/index.html)` and `check-render-debug: passed`.

Host archive gate:

```bash
./scripts/check.sh
```

Result: `231 passed in 226.44s (0:03:46)` and `check: passed`.

Docker archive gate:

```bash
./scripts/check-docker.sh
```

Result: `231 passed in 375.13s (0:06:15)` and `check-docker: passed`.

Final code review:

```text
Reviewed b83d9b0..17462e1.
Critical: None found.
Important: None found.
Minor: None found.
Assessment: ready to merge/push.
```
