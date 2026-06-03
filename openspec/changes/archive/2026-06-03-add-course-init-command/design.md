## Context

The current CLI supports validation, building, and artifact inspection. Course source creation still depends on copying the fixture or hand-writing files. `docs/foundation/07_cli_contract.md` identifies `raya course init` as a next command, and `docs/foundation/05_course_contract.md` defines the minimal source-course shape.

## Goals / Non-Goals

**Goals:**

- Add `raya course init <path>`.
- Create a valid minimal source-course tree.
- Use safe defaults while allowing explicit metadata flags.
- Refuse to overwrite non-empty directories.
- Keep generated content minimal and replaceable.
- Ensure initialized courses pass validate, build, and artifact inspect flows.

**Non-Goals:**

- No rich template marketplace.
- No course import/migration.
- No official learning-object starter pack beyond empty directories.
- No professor dashboard, web UI, backend, identity, or deployment setup.
- No attempt to define required pedagogy through generated starter text.

## Decisions

### Decision: init behavior stays in the CLI package

Implement the first course init helper in `packages/cli` because this is command scaffolding rather than a reusable domain package yet.

Rationale: the first version only writes a few contract files. A separate template package would be premature.

Alternative considered: create a full `templates/course` package. That is useful later when templates become configurable or distributed, but it is not needed for the first command.

### Decision: no overwrite by default

The init command fails when the target directory exists and contains files.

Rationale: course source is canonical human-owned material. The command should never overwrite user work by accident.

### Decision: initialized course has no official objects yet

Create empty `official/cards`, `official/quizzes`, and `official/prompts` directories but do not write starter learning objects.

Rationale: this preserves the source shape without accidentally defining pedagogy or course content.

## Risks / Trade-offs

- Generated starter text may be mistaken for required pedagogy -> label it as replaceable scaffold and keep it minimal.
- Lack of rich templates may feel sparse -> future template proposals can add options once source contracts are stable.
- Defaults may not fit every course -> support explicit metadata flags from the start.

## Migration Plan

1. Add course init helper in `packages/cli`.
2. Add nested `raya course init <path>` parsing.
3. Add tests for generated source validation/build/inspection.
4. Update docs and smoke coverage.

Rollback is simple during reset: remove the helper, CLI command, tests, docs, and change specs before archive.
