---
id: study-object-family-scan-polish
title: Study Object Family Scan Polish
status: active
---

# Study Object Family Scan Polish

## Context

The legacy `main` branch made homework, exercises, prompts, examples, exams,
projects, quizzes, and embeds easy to scan by giving each component family a
clear label and color. The reset renderer already has the stronger content
model: numbered objects, static proof/support environments, accepted official
practice objects, generated Practice/Tasks/Schedule workspaces, and local graph
handoffs. The next UX fusion slice should keep those current contracts and make
the reader page more scannable without importing legacy generic wrappers,
browser quiz scoring, saved learning state, or external rendering dependencies.

## Options Considered

### A. Port legacy component wrappers

This would copy the old `component--homework`, `component--quiz`, and related
classes directly. It is rejected because the reset branch has explicit object
families and official-object contracts; generic wrappers would blur authority
and invite legacy quiz behavior back into the renderer.

### B. Add a new authoring block syntax for components

This could eventually be useful, but it changes authoring contracts and would
need foundation work. It is too large for this frontend UX loop.

### C. Polish existing object families with current classes

This is the selected approach. It uses classes that the renderer already emits:
`raya-numbered-object--definition`, `--problem`, `--activity`, `--example`,
`--equation`, `raya-official-card`, `raya-official-quiz`, and related official
task-family classes. CSS variables provide family accents and surfaces from the
current skin tokens. No Markdown syntax, schema, artifact data, JavaScript, or
browser storage behavior changes.

## Design

Reader pages will expose clearer study-object hierarchy through existing
markup:

- numbered object families receive semantic accent variables for theorem-like,
  practice-like, explanatory, and artifact-like content;
- scannable numbered objects use the family accent for the left badge, header
  tint, border, and focus outline while preserving the configured numbering
  style;
- official practice objects receive type-specific accents for cards, prompts,
  quizzes, assignments, exams, projects, examples, and tasks;
- official reveal panels use the current object accent softly so support
  content visually belongs to the object it explains;
- responsive behavior remains stable: desktop keeps the two-column scannable
  badge layout, mobile stacks the badge above content.

The visual language should be stronger than the current same-accent treatment,
but still quiet enough for study. Color is a scanning aid, not progress,
priority, ranking, mastery, grading, or recommendation metadata.

## Boundaries

This loop does not add:

- browser-side quiz attempts, scoring, submissions, progress, or persistence;
- browser-side MathJax, Mermaid, graph libraries, external CSS, or CDN calls;
- new course schema fields or Markdown block syntax;
- browser-side skin switching;
- saved shell/navigation state.

## Testing

Add a browser e2e regression against `examples/courses/render-fixture` proving:

- official card and quiz objects render with different computed accent colors;
- numbered definition and problem objects render with different computed accent
  colors;
- the scannable numbered badge and official type chip still have visible
  contrast and nonzero dimensions;
- no horizontal overflow appears on the reader page at a representative desktop
  viewport.

Existing render-debug checks remain the broad parity gate for static rendering,
MathJax, local-only assets, screenshots, overflow, and copied site parity.

## Self-Review

- No placeholders remain.
- Scope is limited to CSS and browser-visible rendering evidence.
- The approach uses current emitted classes and does not require authoring,
  schema, artifact, or JavaScript changes.
- The rejected behaviors match the legacy convergence audit and current
  renderer principles.
