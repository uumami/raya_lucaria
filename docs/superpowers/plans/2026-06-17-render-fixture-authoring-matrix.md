# Render Fixture Authoring Matrix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a compact combined authoring matrix page to the existing render fixture and test that it renders math, numbered content, static environments, references, local assets, and section skin activation.

**Architecture:** Keep the current fixture architecture: source truth lives under `examples/courses/render-fixture/course/`, generated artifacts remain rebuildable, and renderer behavior is unchanged. The new `5_authoring_matrix` section demonstrates existing features together; tests prove the generated page uses existing static output contracts. Role docs get short pointers only where they improve discovery.

**Tech Stack:** Python 3.10, pytest, Glintstone static builder, Markdown fenced directives, build-time MathJax, Raya role docs.

---

## File Structure

- Modify: `tests/contracts/test_static_builder.py`
  - Extend `test_render_fixture_builds_rich_static_pages` with focused assertions for the new generated `authoring-matrix/index.html` page.
- Create: `examples/courses/render-fixture/course/5_authoring_matrix/0_index.md`
  - Source fixture page for the combined authoring matrix.
- Create: `examples/courses/render-fixture/course/5_authoring_matrix/_raya/skin.yaml`
  - Section selector using existing `practice-lab` skin.
- Modify: `examples/courses/render-fixture/course/0_index.md`
  - Add one navigation sentence linking to `5_authoring_matrix/0_index.md`.
- Modify: `docs/guides/en/professors/index.md`
  - Add a short pointer to the combined authoring matrix.
- Modify: `docs/guides/es/profesores/index.md`
  - Spanish counterpart, keeping ASCII/no-accent style.
- Modify: `docs/guides/en/contributors/index.md`
  - Add a short pointer for cross-feature fixture changes.
- Modify: `docs/guides/es/colaboradores/index.md`
  - Spanish counterpart.
- Modify: `docs/guides/en/agents/index.md`
  - Add a short pointer for cross-feature debugging.
- Modify: `docs/guides/es/agentes/index.md`
  - Spanish counterpart.
- Do not modify: `packages/static/src/raya_static/*`
  - Production renderer changes are out of scope for this loop.
- Do not edit: generated `examples/courses/render-fixture/artifact/**`
  - Generated artifacts are rebuildable and must not be source truth.

## Task 1: Add Failing Render-Fixture Assertions

**Files:**
- Modify: `tests/contracts/test_static_builder.py`

- [ ] **Step 1: Add reads for the future authoring matrix page**

Inside `test_render_fixture_builds_rich_static_pages`, after `reader_ux_html` and
`reader_ux_visible` are defined, add:

```python
    authoring_matrix_html_path = (
        course / "artifact" / "site" / "authoring-matrix" / "index.html"
    )
    assert authoring_matrix_html_path.exists()
    authoring_matrix_html = authoring_matrix_html_path.read_text(encoding="utf-8")
    authoring_matrix_visible = _visible_text(authoring_matrix_html)
```

- [ ] **Step 2: Add numbered index expectations for the future page**

Extend `expected_numbered_ids` in the same test with:

```python
        "authoring-theorem",
        "authoring-equation",
        "authoring-figure",
        "authoring-table",
        "authoring-activity",
```

After the existing `by_id["orthogonal-equation"]["style"] == "equation"` assertion,
add:

```python
    assert by_id["authoring-theorem"]["href"] == (
        "authoring-matrix/#raya-object-authoring-theorem"
    )
    assert by_id["authoring-theorem"]["style"] == "scannable"
    assert by_id["authoring-equation"]["style"] == "equation"
    assert by_id["authoring-figure"]["style"] == "caption"
    assert by_id["authoring-activity"]["label"] == "Activity"
```

- [ ] **Step 3: Add focused generated-page assertions**

Near the existing reader UX assertions, add:

```python
    for expected_text in (
        "Authoring Matrix Fixture",
        "Theorem 5.1",
        "Equation 5.1",
        "Figure 5.1",
        "Table 5.1",
        "Activity 5.1",
        "Proof of Theorem 5.1",
        "Hint for Activity 5.1",
        "Solution of Activity 5.1",
        "Answer to Activity 5.1",
        "combined authoring matrix",
    ):
        assert expected_text in authoring_matrix_visible
    assert 'data-raya-skin="practice-lab"' in authoring_matrix_html
    assert 'class="raya-numbered-object raya-numbered-object--scannable ' in (
        authoring_matrix_html
    )
    assert 'class="raya-numbered-object raya-numbered-object--caption ' in (
        authoring_matrix_html
    )
    assert 'class="raya-numbered-object raya-numbered-object--equation ' in (
        authoring_matrix_html
    )
    assert "raya-static-environment--hint" in authoring_matrix_html
    assert "raya-static-environment--solution" in authoring_matrix_html
    assert "raya-static-environment--answer" in authoring_matrix_html
    assert "raya-numbered-object-reference" in authoring_matrix_html
    assert 'href="../_raya/assets/_source/_local/diagrams/static-path.svg"' in (
        authoring_matrix_html
    )
    assert "mjx-container" in authoring_matrix_html
    assert "@authoring-theorem" not in authoring_matrix_visible
    assert "\\begin{bmatrix}" not in authoring_matrix_visible
```

- [ ] **Step 4: Run the focused test and verify RED**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages -q
```

Expected: FAIL because `artifact/site/authoring-matrix/index.html` does not exist yet.

- [ ] **Step 5: Commit the failing test**

Do not commit RED unless the project convention allows it. For this repo, keep
the failing test uncommitted and continue to Task 2. Record the RED output in
the worker final message.

## Task 2: Add The Authoring Matrix Fixture Page

**Files:**
- Create: `examples/courses/render-fixture/course/5_authoring_matrix/0_index.md`
- Create: `examples/courses/render-fixture/course/5_authoring_matrix/_raya/skin.yaml`
- Modify: `examples/courses/render-fixture/course/0_index.md`

- [ ] **Step 1: Create the section skin selector**

Create `examples/courses/render-fixture/course/5_authoring_matrix/_raya/skin.yaml`:

```yaml
render:
  skin: practice-lab
```

- [ ] **Step 2: Create the fixture source page**

Create `examples/courses/render-fixture/course/5_authoring_matrix/0_index.md`:

````markdown
---
id: authoring-matrix
title: Authoring Matrix Fixture
summary: Combined fixture page for copyable authoring patterns across math, numbered content, skins, and static environments.
status: ready
---

# Authoring Matrix Fixture

This page is fixture material for renderer and documentation tests. It is a
combined authoring matrix, not canonical pedagogy or architecture truth.

Use the specialized pages for focused coverage: [math authoring](../2_math_authoring/0_index.md),
[numbered objects](../3_numbered_objects/0_index.md), and
[reader UX](../4_reader_ux/0_index.md). Use this page when a change crosses
math, numbered objects, skins, static environments, references, and local assets.

We define page-local notation before use:
$\newcommand{\mat}[1]{\mathbf{#1}}\newcommand{\vect}[1]{\mathbf{#1}}\newcommand{\norm}[1]{\left\lVert #1 \right\rVert}$.

::: theorem {#authoring-theorem title="Matrix norm fixture"}
Let
$$
\mat{I}=\begin{bmatrix}1&0\\0&1\end{bmatrix}
$$
and let $\vect{x}\in\mathbb{R}^2$. Then $\mat{I}\vect{x}=\vect{x}$ and
$\norm{\mat{I}\vect{x}}=\norm{\vect{x}}$.
:::

::: proof {#proof-authoring-theorem of="authoring-theorem" title="Identity proof"}
The matrix multiplication is componentwise:

$$
\begin{bmatrix}
1&0\\
0&1
\end{bmatrix}
\begin{bmatrix}
x_1\\
x_2
\end{bmatrix}
=
\begin{bmatrix}
x_1\\
x_2
\end{bmatrix}.
$$

The norm equality follows from the same vector equality.
:::

::: equation {#authoring-equation}
$$
\mat{I}\vect{x}=\vect{x}
$$
:::

::: figure {#authoring-figure title="Fixture asset path"}
![Static path diagram](../_assets/diagrams/static-path.svg)
:::

::: table {#authoring-table title="Authoring surfaces"}
| Surface | Source pattern |
| --- | --- |
| Math | Page-local macros before use |
| Numbered content | Fenced directives with stable IDs |
| References | `@id` shorthand or `raya:ref/id` links |
| Skin | Section selector under `_raya/skin.yaml` |
:::

::: activity {#authoring-activity title="Authoring check"}
Use @authoring-theorem, @authoring-equation, @authoring-figure, and
[the source reference](raya:ref/authoring-table) to explain why this page is a
combined fixture rather than a separate example course.
:::

::: hint {#hint-authoring-activity of="authoring-activity"}
Start by checking which parts are source files and which parts are generated
artifact output.
:::

::: solution {#solution-authoring-activity of="authoring-activity" title="Fixture path"}
The source page, local asset reference, section skin selector, and fenced
directives are authored source. Static labels, anchors, links, MathJax HTML,
`data-raya-skin`, and copied assets are generated artifact output.
:::

::: answer {#answer-authoring-activity of="authoring-activity"}
This page combines existing authoring patterns so tests can inspect their
rendered output together.
:::
````

- [ ] **Step 3: Link the page from the render fixture root**

In `examples/courses/render-fixture/course/0_index.md`, after the reader UX
sentence, add:

```markdown
Read the [authoring matrix fixture](5_authoring_matrix/0_index.md) for a compact combined source page that uses math, numbered content, static environments, local assets, references, and a section skin together.
```

- [ ] **Step 4: Run the focused test and verify GREEN**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages -q
```

Expected: PASS.

- [ ] **Step 5: Run fixture validation/build smoke checks**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate examples/courses/render-fixture
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya artifacts inspect examples/courses/render-fixture/artifact
```

Expected: all commands exit 0. Build writes ignored generated output under
`examples/courses/render-fixture/artifact/`.

- [ ] **Step 6: Commit fixture and test changes**

Run:

```bash
git add tests/contracts/test_static_builder.py \
  examples/courses/render-fixture/course/0_index.md \
  examples/courses/render-fixture/course/5_authoring_matrix/0_index.md \
  examples/courses/render-fixture/course/5_authoring_matrix/_raya/skin.yaml
git commit -m "Add render fixture authoring matrix"
```

## Task 3: Add Role-Doc Discovery Pointers

**Files:**
- Modify: `docs/guides/en/professors/index.md`
- Modify: `docs/guides/es/profesores/index.md`
- Modify: `docs/guides/en/contributors/index.md`
- Modify: `docs/guides/es/colaboradores/index.md`
- Modify: `docs/guides/en/agents/index.md`
- Modify: `docs/guides/es/agentes/index.md`

- [ ] **Step 1: Add professor/profesor pointer**

In `docs/guides/en/professors/index.md`, after the paragraph that starts
`Use examples/courses/render-fixture/course/2_math_authoring/0_index.md`, add:

```markdown
Use `examples/courses/render-fixture/course/5_authoring_matrix/0_index.md` when you want one compact source page that combines math macros, numbered content, references, static environments, local assets, and a section skin.
```

In `docs/guides/es/profesores/index.md`, add the Spanish counterpart after the
matching math-authoring paragraph:

```markdown
Usa `examples/courses/render-fixture/course/5_authoring_matrix/0_index.md` cuando quieras una pagina fuente compacta que combine macros de math, contenido numerado, referencias, entornos estaticos, assets locales y una skin de seccion.
```

- [ ] **Step 2: Add contributor/colaborador pointer**

In `docs/guides/en/contributors/index.md`, after the paragraph that starts
`Use examples/courses/render-fixture/course/2_math_authoring/0_index.md`, add:

```markdown
Use `examples/courses/render-fixture/course/5_authoring_matrix/0_index.md` as the compact fixture when a change crosses math, numbered objects, skins, static environments, local assets, and static read-path behavior.
```

In `docs/guides/es/colaboradores/index.md`, add the Spanish counterpart after the
matching math-authoring paragraph:

```markdown
Usa `examples/courses/render-fixture/course/5_authoring_matrix/0_index.md` como fixture compacto cuando un cambio cruce math, objetos numerados, skins, entornos estaticos, assets locales y comportamiento de static read path.
```

- [ ] **Step 3: Add agent/agente pointer**

In `docs/guides/en/agents/index.md`, after the paragraph that starts
`For math authoring checks`, add:

```markdown
When a rendering issue crosses math, numbered objects, skins, references, static environments, and local assets, inspect `examples/courses/render-fixture/course/5_authoring_matrix/0_index.md` first, then move to the specialized fixture page for the failing surface.
```

In `docs/guides/es/agentes/index.md`, add the Spanish counterpart after the
matching math-authoring paragraph:

```markdown
Cuando un problema de rendering cruce math, objetos numerados, skins, referencias, entornos estaticos y assets locales, inspecciona primero `examples/courses/render-fixture/course/5_authoring_matrix/0_index.md`, despues pasa a la pagina fixture especializada de la superficie que falla.
```

- [ ] **Step 4: Run doc checks**

Run:

```bash
git diff --check -- \
  docs/guides/en/professors/index.md \
  docs/guides/es/profesores/index.md \
  docs/guides/en/contributors/index.md \
  docs/guides/es/colaboradores/index.md \
  docs/guides/en/agents/index.md \
  docs/guides/es/agentes/index.md
scripts/check-hygiene.sh
```

Expected: both commands exit 0.

- [ ] **Step 5: Commit role-doc changes**

Run:

```bash
git add docs/guides/en/professors/index.md \
  docs/guides/es/profesores/index.md \
  docs/guides/en/contributors/index.md \
  docs/guides/es/colaboradores/index.md \
  docs/guides/en/agents/index.md \
  docs/guides/es/agentes/index.md
git commit -m "Document render fixture authoring matrix"
```

## Task 4: Focused Verification And Review

**Files:**
- Read: all files changed in Tasks 1-3

- [ ] **Step 1: Run focused verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py::test_render_fixture_builds_rich_static_pages -q
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py -q
scripts/check-hygiene.sh
git diff --check origin/new_rayalucaria..HEAD
```

Expected: all commands exit 0.

- [ ] **Step 2: Run render fixture build verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate examples/courses/render-fixture
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/render-fixture
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya artifacts inspect examples/courses/render-fixture/artifact
```

Expected: all commands exit 0.

- [ ] **Step 3: Run docs verification**

Run:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate docs
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build docs
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya artifacts inspect docs/artifact
```

Expected: all commands exit 0.

- [ ] **Step 4: Request final code review**

Use `superpowers:requesting-code-review` over the range starting at the parent
of the plan commit and ending at HEAD. The reviewer must check:

- the implementation matches this plan and the design spec;
- no production renderer code changed;
- tests are focused and stable;
- docs pointers are short and EN/ES separated;
- generated artifacts are not committed.

- [ ] **Step 5: Push after clean review**

If review returns no Critical or Important issues, push:

```bash
git push origin new_rayalucaria
```
