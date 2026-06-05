## Why

Phase 2 made code and notebook references visible, validated, and downloadable without execution. The next missing contract is how courses declare reproducible runtimes, execution policies, and cache metadata before Raya Lucaria runs anything; otherwise later execution work would mix environment choices, cache invalidation, and rendering behavior in one risky step.

## What Changes

- Define a Phase 3 runtime profile baseline centered on `uv` and Docker plus `uv`, with other environment managers left as future adapters.
- Define source placement for runtime support files beside `course/`, not inside the ordered learning tree.
- Define explicit execution policies: `never`, `manual`, `cache`, `always`, and `frozen`.
- Define cache-key metadata inputs without adding an execution engine.
- Define generated artifact metadata for runtime profiles, execution plans, logs, and cache records.
- Add validation diagnostics for missing runtime files, stale or missing lockfile signals, and unsafe execution defaults.
- Preserve the current static build behavior: referenced scripts and notebooks remain downloadable and marked as not executed.

## Capabilities

### New Capabilities

- `runtime-profile-cache-baseline`: Declares runtime profiles, execution policies, cache-key metadata, and non-executing artifact metadata for future local execution.

### Modified Capabilities

- `course-source-contract`: Runtime files and profile configuration live beside the ordered `course/` tree and do not define learning order.
- `code-notebook-references`: Code and notebook references gain policy metadata hooks while keeping Phase 2 `not-executed` behavior.
- `artifact-contract-baseline`: Artifacts expose manifest-declared runtime, execution-plan, and cache metadata as generated machine surfaces.
- `artifact-inspection-command`: Artifact inspection validates runtime and execution metadata without executing anything.
- `minimal-static-builder`: Glintstone may emit non-executing runtime/execution metadata while preserving static pages.
- `dev-workflow-baseline`: Docker plus `uv` becomes the reference verification path for runtime-profile metadata.

## Impact

- Affected packages: `packages/schema`, `packages/static`, `packages/cli`.
- Affected fixtures: add a minimal runtime-profile fixture and invalid runtime-profile fixtures.
- Affected artifacts: optional `data/runtime.json`, `data/execution.json`, `data/cache.json`, and manifest declarations.
- Affected docs: `docs/foundation/17_rendering_execution_plan.md`, README/AGENTS operational notes if commands or workflow expectations change, and separated English/Spanish role guides.
- No runtime execution, notebook kernels, Pyodide/JupyterLite, remote runners, trusted outputs, or `raya run` command execution are introduced by this change.
