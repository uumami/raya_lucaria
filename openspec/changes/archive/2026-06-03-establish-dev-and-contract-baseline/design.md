## Context

The reset foundation defines Raya Lucaria as a static-first educational framework and commons. Current truth lives in `docs/foundation/`; there are no regenerated specs or implementation packages yet.

This change creates the first executable baseline:

- a repeatable development workflow,
- a Python `raya` CLI entrypoint,
- source-course validation,
- official learning-object seed validation,
- artifact contract definitions,
- a minimal fixture course.

The design must keep Glintstone (`packages/static`) useful without a backend while leaving rich renderer, TypeScript, identity, web UI, and dynamic study state decisions for later proposals.

## Goals / Non-Goals

**Goals:**

- Make Docker Compose the documented reference development workflow.
- Use `uv` for Python dependency and environment management in Docker and locally.
- Establish a Python CLI baseline under a plain package path.
- Express `raya.yaml`, source-course, official learning-object, and artifact contracts in portable schema files.
- Validate a minimal fixture course through `raya validate examples/courses/minimal`.
- Keep the official learning-object baseline compatible with future Rennala personal study features.

**Non-Goals:**

- No rich renderer implementation.
- No TypeScript or browser UI stack decision.
- No backend, database, auth provider, realtime service, or identity implementation.
- No personal review queues, spaced repetition state, mastery maps, or analytics implementation.
- No migration of legacy Eleventy/Tailwind/Pagefind/glintstone.yaml/clase implementation details into current contracts.

## Decisions

### Decision: Docker Compose is the reference workflow

Use a root `docker-compose.yaml` as the documented default path for development commands. The primary service should be able to run CLI and test commands against the mounted repository.

Rationale: Docker gives contributors and coding agents a stable entrypoint before the local package layout is mature.

Alternative considered: local-only `uv` setup. This is still supported as an escape hatch, but it is not the reference workflow because host Python differences would make the reset baseline less reproducible.

### Decision: `uv` owns Python environments

Use `uv` in both Docker and local workflows. Do not rely on unmanaged `pip install` commands for the baseline.

Rationale: `uv` gives fast, explicit, lockable Python dependency management and aligns with a future workspace containing `packages/cli`, `packages/schema`, and test packages.

Alternative considered: Poetry or raw `pip`. Poetry is heavier for this baseline, and raw `pip` hides too much environment state.

### Decision: External-course smoke tests use temporary directories

Add a root smoke-test script that copies the minimal fixture course into a temporary directory outside the repository, validates that external course through local `uv`, validates the same course through Docker Compose with an explicit temporary mount, and deletes the temporary directory afterward.

Rationale: this proves the CLI can validate a course that is not part of the framework checkout without introducing a second repository or leaving generated outputs in the working tree.

Alternative considered: create a permanent separate test repository. That may become useful once Raya is consumed as an installed dependency by independent course projects, but it is premature for the baseline.

### Decision: Python CLI first

Implement the first `raya` CLI as Python, with the command surface beginning at `raya --help`, `raya doctor`, and `raya validate <course>`.

Rationale: the first real work is schema parsing, filesystem validation, diagnostics, and fixtures. Python is a practical fit and keeps the renderer/frontend stack undecided.

Alternative considered: TypeScript CLI. TypeScript may become useful for `web`, `ui`, graph visualization, or browser-heavy work, but it is premature for the contract-validation baseline.

### Decision: Plain package paths, canonical domain language

Use plain package names for code paths:

```text
packages/cli       raya command surface
packages/schema    contract schemas and validation helpers
packages/static    future Glintstone builder
```

Use canonical domain names in docs, diagnostics, and proposals:

```text
Glintstone          static course path
Primeval Current    graph and links
Rennala             study and mastery
Sellen              agents
```

Rationale: plain paths are easy for contributors and agents to inspect, while domain names preserve Raya Lucaria's conceptual architecture.

### Decision: Portable schemas plus Python validators

Represent core contracts as portable schema files where possible, then use Python validators for cross-file checks that schema alone cannot express.

Initial schema targets:

- `raya.yaml`,
- artifact `manifest.json`,
- page/quanta indexes,
- official learning-object indexes.

Rationale: schemas make contracts inspectable and reusable by future CLIs, agents, web tools, and tests. Python validators handle path existence, duplicate IDs, broken links, and authority checks.

Alternative considered: Python-only dataclasses or Pydantic models as the sole contract. Those are useful internally but less portable as source-of-truth contracts.

### Decision: Official learning objects start as structured source

The first implementation should prefer structured official objects under `official/` for cards, quizzes, prompts, examples, assignments, exams, projects, and tasks.

Rationale: structured files are easier to validate, index, and export than parsing learning objects hidden in prose. Future proposals can add inline Markdown component syntax after the baseline object contract is stable.

### Decision: Artifact contracts precede rendering

Define the artifact shape and manifest contract before implementing a rich builder. The first builder work can later produce minimal HTML, but this change only needs contracts and validation.

Rationale: dynamic domains must read artifact data through manifests, and renderer choices must not define architecture.

## Risks / Trade-offs

- Docker-first workflow may feel heavier for simple CLI work -> keep `uv` local commands documented and tested.
- JSON-schema-style contracts may not cover all validation rules -> pair schemas with Python contract validators and focused tests.
- Structured official objects may feel less ergonomic than inline authoring -> accept this for the baseline, then revisit inline syntax once validation/indexing are stable.
- Deferring renderer decisions may feel slow -> this protects the artifact boundary and avoids importing legacy renderer assumptions.
- Python-first CLI may later coexist with TypeScript UI packages -> keep package boundaries explicit and avoid putting renderer or web logic into the CLI.

## Migration Plan

1. Add root Docker/uv project scaffolding.
2. Add `packages/schema` contract files and Python validation helpers.
3. Add `packages/cli` with `raya --help`, `raya doctor`, and `raya validate`.
4. Add `examples/courses/minimal`.
5. Add contract tests for valid and invalid fixtures.
6. Add the external-course smoke-test script.
7. Update root docs with the Docker, local `uv`, and smoke-test commands.

Rollback is simple during the reset: remove the new package scaffolding, fixture, and generated specs before archival. No production data or deployed services are affected.

## Open Questions

- Should artifact JSON schemas be stored inside `packages/schema` only, or also copied into published artifacts for downstream validation?
- Should the first official learning-object source format be one YAML file per object, grouped YAML files, or a mix?
- Should `raya validate` produce machine-readable output in the first implementation, or only human-readable diagnostics with stable exit codes?
- Which Python version should the baseline require once implementation starts?
