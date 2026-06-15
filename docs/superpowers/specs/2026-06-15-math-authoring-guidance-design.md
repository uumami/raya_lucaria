# Math Authoring Guidance Design

## Goal

Strengthen the current build-time MathJax authoring surface by adding a dedicated math authoring fixture page, role-specific English and Spanish guidance, and tests that keep those surfaces aligned.

This loop documents and tests the math behavior that is already accepted in the Glintstone baseline. It does not add new renderer semantics. Real theorem/proof functionality is the definite next loop unless discovery finds a blocker.

## Context

The renderer already supports build-time MathJax through local artifact resources. Current fixtures and tests cover inline math, display math, `bmatrix`, vectors, `\newcommand`, `\renewcommand`, aligned equations, cases, probability/statistics notation, optimization notation, no raw visible TeX leakage, no browser-side MathJax conversion, no external renderer requests, and copied static-site parity.

The gap is guidance. Professors, students, contributors, and agents need clearer examples of accepted math authoring patterns, how to report visible raw TeX, and how to diagnose rendering failures without treating generated artifacts as source truth.

## Scope

### In Scope

- Add a dedicated render-fixture math authoring page under `examples/courses/render-fixture/course/`.
- Keep the page labeled as fixture material, not canonical pedagogy.
- Cover accepted valid examples:
  - inline math,
  - display math with `$$` delimiter lines,
  - vectors and matrices,
  - page-local `\newcommand`,
  - page-local `\renewcommand`,
  - aligned equations,
  - optimization notation,
  - set notation,
  - quantifiers and logic notation,
  - functions/maps,
  - norms and inner products,
  - sequences and limits,
  - theorem-like writing patterns using current Markdown.
- Update role docs in English and Spanish:
  - professors/profesores: current valid authoring patterns,
  - students/estudiantes: how rendered math should appear and what to report,
  - contributors/colaboradores: fixture and diagnostic workflow,
  - agents/agentes: source-first debugging and verification workflow.
- Add tests that lock fixture rendering, no raw visible TeX leakage, local MathJax resources, role-doc guidance, and the theorem handoff boundary.

### Out of Scope

- No new public CLI command.
- No new renderer package behavior.
- No browser-side MathJax dependency.
- No external renderer or CDN requests.
- No theorem engine in this loop.
- No automatic theorem numbering.
- No theorem/proof environments.
- No equation or theorem label registry.
- No `\label` or `\ref` support.
- No theorem index or cross-reference rendering.
- No OpenSpec change in this loop unless the user explicitly switches workflows.

## Fixture Design

Add this dedicated fixture page:

```text
examples/courses/render-fixture/course/2_math_authoring/0_index.md
```

The page should begin with a short fixture authority statement:

```text
This is fixture material for renderer and documentation tests. It is not canonical pedagogy or architecture truth.
```

Recommended page sections:

- `Inline And Display Math`
- `Vectors And Matrices`
- `Page Local Macros`
- `Sets Logic And Functions`
- `Aligned Derivations And Optimization`
- `Theorem Like Writing With Current Markdown`
- `Macro Redefinition`

The page should contain only valid examples. Invalid examples belong in tests and contributor/agent diagnostics, not in professor/student copyable guidance.

The theorem-like section should use current Markdown patterns such as headings, callouts, prose labels, and displayed equations. It may show authored labels like `Theorem`, `Definition`, `Lemma`, `Example`, and `Proof` as plain prose or headings. It must state or imply that automatic numbering and cross-references are not current behavior.

## Role Documentation Design

### Professors / Profesores

Add concise authoring guidance for valid math patterns. Emphasize:

- define macros before use,
- keep macros page-local,
- use display delimiter lines for larger expressions,
- use current Markdown for theorem-like writing until theorem support lands,
- report or fix raw TeX leakage before publishing.

### Students / Estudiantes

Add reader-facing guidance. Emphasize:

- math should already be typeset in static pages,
- raw `\begin{bmatrix}`, unknown macros, or dollar-delimited expressions on a published page are rendering problems to report,
- students do not need a CDN, account, backend, or browser-side MathJax conversion.

### Contributors / Colaboradores

Add implementation-facing guidance. Emphasize:

- use the math authoring fixture when changing renderer behavior,
- run `scripts/check-render-debug.sh`,
- inspect `index.html` first and `report.json` for exact diagnostics,
- keep invalid examples in tests,
- preserve no browser-side MathJax and no external renderer requests.

### Agents / Agentes

Add agent workflow guidance. Emphasize:

- debug source pages, not generated `artifact/` output,
- use render-debug reports as evidence,
- verify no raw visible TeX and no external renderer requests,
- preserve English technical identifiers in Spanish docs,
- treat theorem/proof functionality as the next design loop, not current behavior.

Spanish pages should keep the existing ASCII/no-accent style. Technical identifiers stay in English.

## Theorem Handoff

The next Superpowers loop should design real theorem/proof functionality unless discovery finds a blocker.

Candidate next-loop scope:

- authored theorem, definition, lemma, proposition, corollary, example, and proof blocks,
- automatic numbering policy,
- optional titles,
- stable theorem IDs,
- equation and theorem labels,
- cross-references,
- rendered theorem styling,
- theorem index or inspection data if accepted,
- diagnostics for duplicate labels, missing references, and unsupported LaTeX theorem environments.

This loop should explicitly document that those capabilities are next, not current behavior.

## Testing Design

Add or extend tests so they fail if the fixture/docs drift from the accepted contract:

- Static builder or e2e test confirms the new fixture page renders and includes MathJax CHTML.
- Visible text assertions confirm current fixture examples do not leak raw TeX markers such as `\newcommand`, `\renewcommand`, `\begin{bmatrix}`, selected authoring macro names, or dollar-delimited math.
- Contract test confirms role docs mention current accepted math patterns and the theorem-support next loop.
- Existing render-debug tests continue to confirm local preview/static parity, no browser-side MathJax conversion, no external renderer requests, local MathJax CSS/fonts, copied static-site parity, screenshots, `report.json`, and `index.html`.

## Verification Plan

Focused verification should include:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/contracts/test_static_builder.py tests/contracts/test_renderer_dependencies.py tests/e2e/test_preview_static_read_path.py
UV_PROJECT_ENVIRONMENT=.venv-local scripts/check-render-debug.sh
```

Full verification should include:

```bash
./scripts/check.sh
./scripts/check-docker.sh
```

## Risks And Mitigations

- **Risk: docs imply theorem functionality exists now.** Mitigation: explicitly state theorem/proof engine work is next, while current pages use Markdown patterns only.
- **Risk: fixture becomes accidental pedagogy.** Mitigation: keep fixture authority labels and avoid course-teaching language.
- **Risk: Spanish pages drift in style.** Mitigation: keep ASCII style and English technical identifiers.
- **Risk: examples exceed the supported MathJax subset.** Mitigation: use only accepted `base`, `ams`, and `newcommand` patterns and lock them with focused tests.
