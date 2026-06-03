## Why

Raya Lucaria has strong foundation truth, but it still lacks executable contracts and a repeatable development loop. This change turns the reset foundation into the first implementation-ready baseline without committing to a rich renderer, backend, or web UI stack too early.

## What Changes

- Establish Docker Compose as the reference development workflow, with local non-Docker execution kept available.
- Establish `uv` as the Python environment and package-management tool for the first packages.
- Establish a Python CLI baseline for the first operational commands: `raya --help`, `raya doctor`, and `raya validate <course>`.
- Add an external-course smoke test that validates a temporary course copy outside the repository through both local `uv` and Docker Compose.
- Define Phase 1 source contracts for `raya.yaml`, `content/`, learning quanta, and minimal fixture courses.
- Define official learning-object seed contracts for cards, quizzes, prompts, examples, assignments, exams, projects, and tasks.
- Define the first artifact contract surfaces: `manifest.json`, generated data indexes, and official learning-object indexes.
- Preserve the static-only Glintstone path while leaving renderer, TypeScript, backend, and web UI decisions for later proposals.
- Explicitly reject legacy renderer assumptions as current requirements: old Eleventy/Tailwind/Pagefind choices, old `glintstone.yaml`, old `clase/`, and old generated JSON shapes are historical unless reaccepted by current specs.

Minimum requirement: make contracts validate in a reproducible Docker/uv/Python CLI loop.

Growth path: once source, artifact, CLI, and study-seed contracts are stable, future proposals can add a fresh static builder, Primeval Current graph behavior, Rennala personal study state, Sellen agent workflows, Glintstone Key identity, and richer browser UI.

## Capabilities

### New Capabilities

- `dev-workflow-baseline`: Docker Compose reference development workflow, `uv` Python setup, local non-Docker escape hatch, external-course smoke test, and baseline validation commands.
- `cli-contract-baseline`: Python `raya` CLI baseline for help, doctor, context detection, validation diagnostics, and stable exit behavior.
- `course-source-contract`: `raya.yaml`, `content/`, learning quanta, source-course structure, minimal fixture course, and source validation.
- `official-learning-objects`: official cards, quizzes, prompts, examples, assignments, exams, projects, tasks, retrieval hooks, authority labels, and validation/indexing requirements.
- `artifact-contract-baseline`: portable artifact shape, manifest requirements, generated data indexes, official learning-object indexes, and artifact boundary rules.

### Modified Capabilities

- None. Existing OpenSpec specs have not been regenerated from the foundation yet.

## Impact

- Adds initial OpenSpec specs for the reset baseline.
- Guides future package scaffolding under plain package names such as `packages/cli`, `packages/schema`, and `packages/static`.
- Introduces Docker/uv/Python as the first implementation posture while keeping the renderer and frontend stack undecided.
- Affects future README/AGENTS/CLI documentation, fixture layout, validation tests, and contract tests.
- Does not add backend services, identity providers, live classroom features, personal study state, a rich renderer, or TypeScript/web UI implementation.
