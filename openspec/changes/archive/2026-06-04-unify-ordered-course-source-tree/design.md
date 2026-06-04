## Context

Raya Lucaria now has an ordered rendered-content contract, stable page IDs, generated local/master indexes, live rendered docs, and official learning-object export. Before this change, examples split authored course material into separate top-level trees:

```text
course/
  content/      rendered pages
  official/     official cards, prompts, quizzes
  assets/       local files
```

That shape is technically valid but pedagogically awkward. It hides the relationship between a learning quantum and the official cards, prompts, quizzes, examples, tasks, or assets that support it. It also makes the course source look less ordered than the course itself.

This change treats the course source as one ordered authored tree. Rendered pages, official learning objects, local assets, drafts, and support material are separated by local directory conventions rather than by unrelated top-level roots.

## Goals / Non-Goals

**Goals:**

- Make `source: course` and `course/` the canonical source-course shape for new courses.
- Keep one authored source-root field and reject stale source `content:` configuration.
- Colocate official learning objects under the learning quantum they support through `_official/`.
- Allow `_official/` objects to infer scope from the nearest rendered quantum while preserving explicit stable IDs.
- Keep official object files ordered for predictable authoring and generated study order.
- Support colocated `_assets/` at the source root, section, or learning-quantum level.
- Keep underscore support directories private and out of rendered navigation.
- Migrate examples, docs, course init, tests, and role documentation so the canonical shape is visible everywhere.

**Non-Goals:**

- No personal review queues, spaced repetition scheduling, confidence ratings, or mastery state.
- No dynamic backend, account system, graph UI, or frontend renderer expansion.
- No automatic source rewriting command for old source-tree shapes.
- No change to stable identity rules: page IDs and official object IDs remain explicit metadata, not path-derived order prefixes.

## Decisions

### Use `source: course` as the canonical source root

New scaffolds and examples should use:

```yaml
source: course
artifact: artifact
```

`content:` is not a supported course configuration field. Validation should fail with actionable guidance to use `source: course`.

Alternative considered: keep `content:` and allow support directories inside it. Rejected as the canonical shape because `content/` now includes more than rendered prose: official objects, assets, drafts, examples, assignments, and future study seeds.

### Keep one ordered authored source tree

Canonical shape:

```text
course/
  0_index.md
  _assets/
  _official/
    exams/
      1_midterm.yaml
  1_foundations/
    0_index.md
    1_limits/
      0_index.md
      _assets/
      _official/
        cards/
          1_limit_meaning.yaml
        prompts/
          1_explain_limit.yaml
    2_derivatives/
      0_index.md
      _official/
        cards/
          1_rate_of_change.yaml
  2_practice/
    0_index.md
  A_reference/
    0_index.md
```

Rendered entries use ordered names. Support directories use leading underscores and never render. This keeps public navigation clean while making source ownership local and inspectable.

### Prefer directory pages for quanta with support material

A file page such as `1_limits.md` can remain valid, but a page that owns `_official/` or `_assets/` needs a directory form:

```text
1_limits/
  0_index.md
  _official/
```

This is the right trade-off because support material belongs to a quantum directory. Future tooling can help convert `1_limits.md` into `1_limits/0_index.md`, but this change only validates and builds the resulting shape.

### Infer colocated official-object scope conservatively

Objects under a quantum's `_official/` directory may omit `scope.quantum`; Glintstone infers it from the nearest rendered directory landing page:

```text
course/1_foundations/1_limits/_official/cards/1_meaning.yaml
                                      |
                                      v
                         scope.quantum = limits-intuition
```

If a colocated object declares `scope.quantum`, it must match the nearest quantum. Source-root `course/_official/` objects must declare explicit `scope.quantum` because no nearest child quantum is implied.

Alternative considered: allow colocated objects to target any quantum. Rejected because it makes source locality misleading and recreates the detached-bank problem under a different path.

### Order official object files within each family

Inside `_official/<family>/`, object files should use ordered prefixes:

```text
cards/
  1_limit_meaning.yaml
  2_limit_notation.yaml
quizzes/
  1_concept_check.yaml
```

The prefix controls authoring/display order only. The object `id` remains the durable identity used by artifacts and future Rennala state.

Root authored `official/` is not supported. New examples use ordered files under `course/_official/` or a quantum-local `_official/`.

### Treat `_assets/` as local source support

Assets that belong to a quantum should live beside it:

```text
1_derivatives/
  0_index.md
  _assets/
    tangent-diagram.txt
```

Root authored `assets/` is not supported. Source-root shared assets live under `course/_assets/`; section and topic assets live under their nearest `_assets/`. The builder copies referenced source assets to artifact assets and browser-facing static assets through collision-safe generated paths. Asset files do not need ordered prefixes because their filenames often come from external tools and are not learning sequence entries.

### Keep generated artifacts separate

`artifact/` remains generated and ignored. Neither `data/official.json` nor copied assets become canonical source. Dynamic services and future study state read generated data through `manifest.json`.

## Risks / Trade-offs

- [Migration churn] Moving from file pages to directory pages for colocated support material can rename paths. Stable page IDs, `raya:<id>` links, aliases, and official object scopes mitigate reference breakage.
- [Stale config fields] Authors may try old `content:` or root `assets:` fields. Validation should reject those fields with concrete guidance.
- [Too many underscore conventions] `_official/`, `_assets/`, `_drafts/`, and `_partials/` add vocabulary. The consistency rule is simple: underscore directories are source support and do not render.
- [Scope inference mistakes] Inference is convenient but can hide intent. Course-level/global objects require explicit scope, and colocated explicit scopes must match the nearest quantum.
- [Official object order vs identity] Ordered filenames might be mistaken for IDs. Docs and validation should keep object `id` mandatory and stable.
- [Fixture churn] Existing examples and tests should migrate in one focused change so canonical patterns are not split.

## Implementation Plan

1. Extend schema/config resolution to require `source` and reject stale source-root fields such as `content:` and root authored `assets:`.
2. Extend content resolution to treat `_official/` and `_assets/` as private support directories under the configured source root.
3. Extend official object discovery to scan source-root and quantum-colocated `_official/`.
4. Infer colocated scopes from nearest rendered directory quantum and preserve explicit scopes in generated data.
5. Extend asset validation and copying to support source-root and quantum-colocated `_assets/`.
6. Update course init and fixtures to use `source: course`, `course/`, colocated `_official/`, and colocated `_assets/`.
7. Update docs and role guides in English and Spanish.
8. Keep invalid-field tests for `content:` and root authored `assets:` so the unsupported paths fail explicitly.

## Open Questions

- Should source-root `course/_official/` remain explicit-scope only, or should a future design add course-level/global object scopes beyond `scope.quantum`?
- Should `_assets/` paths expose a friendlier browser URL later, or should generated collision-safe paths remain the public static path?
