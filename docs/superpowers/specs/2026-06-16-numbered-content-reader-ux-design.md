# Numbered Content Reader UX Design

## Status

Approved design for the next Superpowers implementation loop.

## Goal

Improve the reader-facing presentation of numbered course content while keeping
the numbered-object contract static, local, and artifact-driven.

The default rendered experience should feel useful for a serious math or
university course page: theorem-like objects, examples, exercises, homework,
activities, assignments, and similar learning objects should be easy to scan,
link, and cite without turning the normal student page into an inspection
surface.

## Current Context

The current baseline already supports:

- build-time numbered objects from fenced `:::` directives,
- course-level `render.numbered_objects` configuration in `raya.yaml`,
- shorthand references such as `@main-theorem`,
- explicit references such as `raya:ref/main-theorem`,
- proof blocks using `::: proof {of="object-id"}`,
- manifest-declared `data/numbered-objects.json`,
- render-debug evidence for numbered objects, references, proofs, and proof
  targets,
- no browser-side numbering or reference resolver,
- no browser-side MathJax conversion,
- no external renderer or CDN requests.

The next gap is not the machine contract. The next gap is the default reader
experience and a realistic fixture that shows how a real course note would use
the contract.

## Scope

This loop will implement course-level reader UX improvements only.

In scope:

- add `remark` as a built-in numbered object family,
- add a new numbered-object style for scannable learning objects,
- make that scannable style the default for learning-object sequences,
- keep figure/table caption behavior,
- keep equation behavior,
- preserve existing course-level sequence and family overrides,
- add a realistic mini-course fixture page that combines course-note objects,
  references, proofs, figures, tables, equations, activities, and assignments,
- update foundation status and role docs in English and Spanish,
- add tests and browser/render-debug verification for the new default.

Out of scope:

- page-level or section-level style overrides,
- dynamic reference panels on normal student pages,
- browser-side numbering, reference resolution, or MathJax conversion,
- a new canonical data file beyond `data/numbered-objects.json`,
- external renderer or CDN resources,
- changing the source directory contract,
- changing proof blocks into numbered objects.

Page and section overrides are an intended future direction, but this loop will
only document them as future work if mentioned at all.

## Design Direction

The approved default visual direction is the "Scannable Course" model:

- learning objects render as stable blocks with a left-side number badge,
- the main content area carries the full label, number, optional title, and
  body,
- references remain normal static links,
- proof headings continue to name their target object,
- normal student pages stay readable and focused.

The "Inspection Rich" model is not the default. Its richer IDs and cross-check
details belong in `_raya/inspect/`, render-debug reports, and machine-readable
artifact data, not in normal course reading pages.

## Numbered Families And Styles

Add `remark` as a built-in family:

```yaml
remark:
  sequence: theorem
  label: Remark
```

Add a new accepted numbered-object style:

```text
scannable
```

Built-in sequence defaults should become:

| Sequence | Default style |
| --- | --- |
| `theorem` | `scannable` |
| `example` | `scannable` |
| `exercise` | `scannable` |
| `assignment` | `scannable` |
| `figure` | `caption` |
| `table` | `caption` |
| `equation` | `equation` |

The existing config surface remains the customization mechanism:

```yaml
render:
  numbered_objects:
    numbering: page-hierarchy
    sequences:
      assignment:
        label: Activity
        style: scannable
    families:
      homework:
        sequence: assignment
        label: Activity
```

Course authors may continue to override sequence labels, sequence styles,
family labels, and family-to-sequence mappings at the course level.

## Rendering Behavior

For `scannable` objects, rendered HTML should:

- include a stable style class such as `raya-numbered-object--scannable`,
- include a left visual badge containing a compact label/number,
- keep the full reference text visible in the object heading,
- keep optional titles visible and semantically adjacent to the reference text,
- keep the body in a separate content region,
- work with math, tables, lists, links, and local images inside the body,
- remain static HTML generated at build time.

The badge is visual help, not the source of truth. The object ID, family,
sequence, number, label, source path, output path, anchor, href, and reference
text remain in `data/numbered-objects.json`.

References continue to render from source references to static links at build
time. No browser-side resolver is introduced.

Proofs continue to render as proof environments. They may target any numbered
object family, including `remark`, but proofs remain absent from
`data/numbered-objects.json`.

## Fixture Work

Add a realistic fixture page under `examples/courses/render-fixture/course/`.
The page should read like a compact course note rather than an object matrix.

It should include at least:

- a theorem,
- a lemma or proposition,
- a definition,
- a remark,
- an example,
- an equation,
- a figure,
- a table,
- an exercise or problem,
- a homework/activity/assignment object,
- a proof targeting a theorem-like object,
- a proof or solution sketch targeting a practice object,
- shorthand `@id` references,
- explicit `raya:ref/id` references,
- build-time MathJax content,
- local figure/table assets where appropriate.

The existing numbered-object matrix can remain as a compact coverage fixture.
The realistic fixture should complement it by exercising reading flow and visual
hierarchy.

## Documentation Work

Update the smallest relevant foundation text, likely
`docs/foundation/17_rendering_execution_plan.md`, to record:

- `remark` as current numbered-object behavior,
- the scannable default reader style,
- course-level style overrides as the current customization surface,
- page/section overrides as future work if mentioned.

Update role docs in both languages:

- English:
  - `docs/guides/en/professors/index.md`
  - `docs/guides/en/students/index.md`
  - `docs/guides/en/contributors/index.md`
  - `docs/guides/en/agents/index.md`
- Spanish:
  - `docs/guides/es/profesores/index.md`
  - `docs/guides/es/estudiantes/index.md`
  - `docs/guides/es/colaboradores/index.md`
  - `docs/guides/es/agentes/index.md`

Docs should keep technical identifiers such as `render.numbered_objects`,
`scannable`, `raya:ref/id`, `data/numbered-objects.json`, and file paths in
English.

## Testing Requirements

Focused tests should cover:

- built-in `remark` defaults,
- `scannable` accepted as a numbered-object style,
- unknown styles still rejected with precise diagnostics,
- default built-in sequences use the expected styles,
- course-level style overrides continue to work,
- `data/numbered-objects.json` records `style: "scannable"` for default
  learning objects,
- rendered HTML includes the scannable classes and visible reference text,
- figure/table caption style remains intact,
- equation style remains intact,
- browser checks confirm static/local rendering and working references,
- render-debug evidence includes the realistic fixture page or a representative
  numbered-content page with scannable objects,
- role docs mention the current default and authoring workflow.

Verification should include:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest tests/contracts/test_numbered_objects.py tests/contracts/test_static_builder.py tests/e2e/test_preview_static_read_path.py tests/e2e/test_render_debug_report.py -q
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

The final implementation may narrow or expand the focused pytest command based
on exact test placement, but it must still run the canonical host and Docker
gates before completion.

## Non-Goals And Guardrails

- Do not add page or section override syntax in this loop.
- Do not make rendered HTML the authority for numbered objects.
- Do not add JavaScript to compute numbers or references.
- Do not add browser-side MathJax.
- Do not add external CSS, font, renderer, or CDN requests.
- Do not edit generated artifacts as source.
- Do not make the realistic fixture accidental pedagogy canon; label it as
  fixture material.

## Open Follow-Up

After this loop, a later design can add page/section override inheritance. That
future design should decide whether overrides belong in page frontmatter,
directory metadata, or another course-level mapping. It should not be smuggled
into this reader UX loop.
