# Math Authoring Guidance Design

> **Supersession note:** The theorem/proof/numbered-object status in this June 15 math-authoring design captured the pre-numbered-object baseline. Current behavior is superseded by `docs/superpowers/specs/2026-06-15-numbered-objects-cross-references-design.md`, `docs/superpowers/specs/2026-06-16-proof-blocks-design.md`, and `docs/superpowers/plans/2026-06-16-proof-blocks.md`.

## Goal

Strengthen the current build-time MathJax authoring surface by adding a dedicated math authoring fixture page, role-specific English and Spanish guidance, and tests that keep those surfaces aligned.

This loop documents and tests the math behavior that was already accepted in the Glintstone baseline on June 15. It did not add new renderer semantics; its theorem/proof handoff language has since been superseded by the numbered-object and proof-block design docs listed above.

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
  - historical theorem-like Markdown patterns from the pre-numbered-object baseline.
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
- No theorem engine in this June 15 math-authoring loop; later status is superseded by the numbered-object and proof-block docs listed above.
- No automatic theorem numbering in this June 15 math-authoring loop.
- No theorem/proof environments in this June 15 math-authoring loop.
- No equation or theorem label registry in this June 15 math-authoring loop.
- No `\label` or `\ref` support in this June 15 math-authoring loop.
- No theorem index or cross-reference rendering in this June 15 math-authoring loop.
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
- `Theorem Like Writing With Current Markdown` as historical pre-numbered-object fixture context
- `Macro Redefinition`

The page should contain only valid examples. Invalid examples belong in tests and contributor/agent diagnostics, not in professor/student copyable guidance.

The theorem-like section captured the pre-numbered-object fixture context using Markdown patterns such as headings, callouts, prose labels, and displayed equations. Current theorem, proof, numbered-object, and reference behavior is superseded by the June 15 numbered-object design and the June 16 proof-block design/plan.

## Role Documentation Design

### Professors / Profesores

Add concise authoring guidance for valid math patterns. Emphasize:

- define macros before use,
- keep macros page-local,
- use display delimiter lines for larger expressions,
- point current theorem/proof/numbered-object guidance to the superseding docs listed at the top of this historical design,
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
- point theorem/proof/numbered-object status to the superseding docs listed at the top of this historical design.

Spanish pages should keep the existing ASCII/no-accent style. Technical identifiers stay in English.

## Superseded Theorem Handoff

This handoff was completed and superseded by the numbered-object and proof-block docs listed at the top of this historical design.

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

This historical loop should not be used as current theorem/proof/numbered-object guidance.

## Testing Design

Add or extend tests so they fail if the fixture/docs drift from the accepted contract:

- Static builder or e2e test confirms the new fixture page renders and includes MathJax CHTML.
- Visible text assertions confirm current fixture examples do not leak raw TeX markers such as `\newcommand`, `\renewcommand`, `\begin{bmatrix}`, selected authoring macro names, or dollar-delimited math.
- Contract test confirms role docs mention accepted math patterns and point theorem/proof/numbered-object status at the superseding docs.
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

- **Risk: historical docs imply stale theorem/proof status.** Mitigation: explicitly point theorem/proof/numbered-object status to the superseding design and plan docs.
- **Risk: fixture becomes accidental pedagogy.** Mitigation: keep fixture authority labels and avoid course-teaching language.
- **Risk: Spanish pages drift in style.** Mitigation: keep ASCII style and English technical identifiers.
- **Risk: examples exceed the supported MathJax subset.** Mitigation: use only accepted `base`, `ams`, and `newcommand` patterns and lock them with focused tests.
