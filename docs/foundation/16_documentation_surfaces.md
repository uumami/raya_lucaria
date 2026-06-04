---
id: docs-documentation-surfaces
title: Documentation Surfaces
summary: Role documentation, language separation, rendered-doc boundaries, and documentation fixtures.
status: ready
---
# Documentation Surfaces

Documentation explains accepted Raya Lucaria behavior for people and agents. It is not course canon, generated output, or a substitute for foundation decisions and accepted OpenSpec specs.

## Role Audiences

Role documentation covers four audiences:

| Audience | Needs |
| --- | --- |
| Contributors/collaborators | how to change code, specs, docs, tests, and workflows safely |
| Professors | how to own course source, official material, review, and publishing |
| Students | how to read, study, keep work portable, and understand authority labels |
| Agents | explicit files, commands, contracts, diagnostics, and authority boundaries |

Not every change needs documentation for every role. A proposal should name the affected role-doc audiences, or say that no role-facing documentation update is needed.

## Language Pages

Role documentation must use separate English and Spanish role directories with index pages. Do not mix English and Spanish sections in the same role page.

Each role directory can grow into multiple topic pages. Code identifiers, package names, commands, schema fields, file paths, domain names, and stable IDs stay in English. Spanish pages may explain those identifiers in Spanish, but the identifier itself remains unchanged.

## Surface Boundary

```text
foundation docs       accepted specs        role documentation
seed truth            testable contracts    operational guidance
       |                    |                       |
       +---------+----------+-----------------------+
                 |
                 v
          examples and rendered docs
          fixtures or generated output,
          never higher authority
```

Documentation must:

- reference the relevant foundation or spec authority,
- stay readable as plain Markdown,
- avoid requiring a backend, hosted service, rendered site, or frontend build,
- keep rendered documentation fixtures separate from class/course examples,
- avoid defining pedagogy or architecture by accident.

## Rendered Documentation

Glintstone may render documentation or documentation fixtures to prove static rendering behavior. Rendered documentation remains explanatory material. It must stay separate from class/course examples and must use the same static read path rules as course artifacts.

Rendered documentation does not replace `manifest.json`, `data/*.json`, source course files, accepted specs, or foundation docs as authority surfaces.

The live repository documentation is also a renderable docs course. `docs/raya.yaml` uses `source: render-content` to point Glintstone at `docs/render-content/`, an ordered render tree that references the real `docs/foundation/` and `docs/guides/` pages. The render tree exists to satisfy source-order validation and static-read-path tests; the readable documentation paths remain `docs/foundation/` and `docs/guides/`.

```text
readable docs                 render source                 generated output
-------------                 -------------                 ----------------
docs/foundation/   <------    docs/render-content/   --->   docs/artifact/
docs/guides/                  ordered symlink tree          site/ + data/*.json
docs/raya.yaml                source-order contract         ignored, rebuildable
```

Maintenance rule:

- edit the real Markdown under `docs/foundation/` and `docs/guides/`,
- keep compact frontmatter metadata on rendered documentation pages,
- update `docs/render-content/` when adding or reordering rendered docs pages,
- validate with `raya validate docs`,
- build or test with `raya build docs` or static-read-path tests,
- never edit `docs/artifact/` as source truth.
