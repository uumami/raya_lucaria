## Why

Before this change, source-course examples split rendered pages under `content/` and official learning objects under a separate `official/` tree, which made the course feel less ordered than the learning structure itself. Raya Lucaria needs the authored course source to be organized around learning quanta so pages, official study seeds, local assets, drafts, and support files stay near the concept they serve while remaining clearly separated from rendered navigation and generated output.

## What Changes

- Define a canonical authored source root named `course/`, referenced from `raya.yaml` with a new `source: course` field.
- Reject source `content:` so new contracts have one authored source-root field.
- Treat the authored source root as an ordered learning tree: public rendered entries use ordered names, and non-rendered support material uses underscore directories.
- Add colocated `_official/` directories under any rendered learning quantum for course-owned cards, quizzes, prompts, examples, assignments, exams, projects, and tasks.
- Add scope inference for quantum-colocated official objects from the nearest rendered page or section landing page, while requiring explicit `scope.quantum` for source-root course-level/global official objects.
- Add colocated `_assets/` directories for assets that belong to the source root, a section, or a specific learning quantum.
- Keep `_drafts/`, `drafts/`, `_partials/`, `_official/`, and `_assets/` private/unrendered, even when they contain structured source material.
- Update Glintstone validation, artifact generation, static read-path rendering, course init scaffolds, fixtures, live docs rendering, and documentation to preserve the unified ordered source model.
- No personal study state, spaced-repetition scheduling, dynamic backend, graph UI, or rich renderer component system is introduced by this change.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `course-source-contract`: Replace the canonical `content/` source root with `source: course`, reject stale root source fields, and define non-rendered underscore support directories inside the ordered source tree.
- `content-order-index-baseline`: Clarify that ordered source entries live under the configured authored source root and that underscore support directories do not enter rendered navigation or generated indexes.
- `official-learning-objects`: Support colocated `_official/` discovery, nearest-quantum scope inference, explicit scope requirements for course-level/global official objects, and duplicate validation across all official object locations.
- `course-init-command`: Scaffold new courses with `source: course`, `course/0_index.md`, and ordered/private support directory conventions instead of separate `content/` and `official/` roots.
- `minimal-static-builder`: Build artifacts from the configured source root, discover colocated official objects and assets, preserve source paths in generated data, and keep generated static output deployment-neutral.
- `source-link-asset-validation`: Validate local asset links against own and ancestor `_assets/` directories without treating support directories as rendered content.
- `dev-workflow-baseline`: Require fixture, docs, and e2e tests when changes touch the unified course source tree or support-directory conventions.

## Impact

- Affected source contract: `raya.yaml` schema, course validation, source root resolution, private/support path classification, learning-object validation, and local asset validation.
- Affected builders/artifacts: Glintstone static builder, `data/official.json`, study counts in `indices.json`, asset copying, source-path exports, and artifact inspection.
- Affected scaffolds/fixtures: `raya course init`, minimal course, ordered-content fixture, invalid fixtures, documentation fixture, and live docs `docs/raya.yaml` / `docs/render-content/`.
- Affected docs: `docs/foundation/05_course_contract.md`, `docs/foundation/15_system_overview.md`, role guides in English and Spanish, and `openspec/config.yaml`.
- Removed source shapes: source `content:`, root authored `official/`, and root authored `assets/` are not accepted by the new contract; generated artifact `assets/` remains an output surface.
