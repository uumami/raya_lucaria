## Why

Raya Lucaria can validate, build, and inspect courses, but a new course still has to be assembled by hand. The foundation names `raya course init` as a next CLI command, and adding it now gives professors, students, and coding agents a safe way to create a valid source-course skeleton without copying legacy examples.

## What Changes

- Add `raya course init <path>` as a nested CLI command.
- Generate the smallest useful source-course tree:
  - `raya.yaml`
  - `content/00_index.md`
  - `assets/`
  - `official/cards/`
  - `official/quizzes/`
  - `official/prompts/`
- Support explicit metadata flags for course ID, title, description, and language.
- Derive conservative defaults from the target path when optional metadata is omitted.
- Refuse to overwrite non-empty target directories.
- Ensure initialized courses validate, build, and produce inspectable artifacts.
- Keep the generated source minimal and label starter text as replaceable scaffold, not required pedagogy.

Minimum requirement: `raya course init <path>` creates a valid course source that can run through `raya validate`, `raya build`, and `raya artifacts inspect`.

Growth path: future proposals can add richer templates, official object starter packs, course importers, professor workflows, installation init, and template customization after the core source contract is stable.

## Capabilities

### New Capabilities

- `course-init-command`: source-course scaffolding workflow for creating a valid minimal course tree from the CLI.

### Modified Capabilities

- `cli-contract-baseline`: add `raya course init <path>` as a nested CLI command with stable diagnostics and safe overwrite behavior.
- `course-source-contract`: require CLI-initialized courses to satisfy the baseline source course contract.

## Impact

- Updates `packages/cli` with a course init helper and nested command.
- Adds tests for course init success, validation/build/inspect compatibility, and overwrite refusal.
- Updates README, AGENTS, CLAUDE, and smoke workflow command coverage.
- Does not add a backend, web UI, renderer stack, identity, registration, or dynamic study state.
