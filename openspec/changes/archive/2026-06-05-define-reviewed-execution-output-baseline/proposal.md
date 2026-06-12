## Why

Raya Lucaria can run explicit local targets and write generated execution results, but professors still have no accepted way to promote a successful result into reviewed course material or to make `frozen` policy useful. Without that contract, static pages cannot safely show computed outputs, and heavy computations remain hard to publish without rerunning.

## What Changes

- Add reviewed execution outputs as a source-controlled, professor-reviewed surface for selected code and notebook targets.
- Add a colocated `_reviewed/` private support directory for reviewed execution output manifests and files.
- Add `raya outputs list <course>` to inspect generated and reviewed output status without executing code.
- Add `raya outputs freeze <course> <target>` to copy the latest successful generated execution result into reviewed source support for explicit human review and commit.
- Change `policy: frozen` from "always refuse" to "validate reviewed output exists and is current; never execute".
- Add artifact data for reviewed outputs and copy reviewed output files into artifact-level and browser-facing static storage.
- Render a compact reviewed-output panel on pages that reference targets with current reviewed output.
- Keep validation, build, artifact inspection, output listing, reviewed-output freezing, and static serving non-executing.
- Defer multi-target CI execution, remote runners, browser execution, signed attestations, rich notebook result rendering, and professor approval workflows beyond explicit source review.

## Capabilities

### New Capabilities

- `reviewed-execution-output-baseline`: Defines source-controlled reviewed outputs, freeze/list command behavior, frozen policy validation, artifact data, and static visualization.

### Modified Capabilities

- `course-source-contract`: Adds `_reviewed/` as private source support colocated with the learning quantum it serves.
- `cli-contract-baseline`: Adds `raya outputs list` and `raya outputs freeze` command surfaces.
- `runtime-profile-cache-baseline`: Changes `frozen` policy from deferred refusal to reviewed-output validation without execution.
- `local-execution-baseline`: Integrates reviewed outputs with generated execution results and frozen target behavior.
- `artifact-contract-baseline`: Adds manifest-declared reviewed output data and copied reviewed output file surfaces.
- `artifact-inspection-command`: Validates reviewed output metadata and copied files without execution.
- `code-notebook-references`: Lets referenced scripts and notebooks expose reviewed output status in generated reference surfaces.
- `rich-static-rendering`: Adds static reviewed-output panels without making rendered HTML authoritative.
- `dev-workflow-baseline`: Requires fixtures, contract tests, e2e/static-read-path tests, docs, and no-execution regressions for reviewed/frozen outputs.

## Impact

- Affected packages: `packages/cli`, `packages/schema`, and `packages/static`.
- Affected source conventions: add colocated `_reviewed/` as private source support; no root `content:`, root authored `official/`, or root authored `assets/` is introduced.
- Affected artifacts: add `data/reviewed-outputs.json`, artifact-level reviewed files, and browser-facing reviewed files under the static read path.
- Affected fixtures: extend or add an execution/review fixture with generated result freezing, stale-output diagnostics, frozen-policy validation, and static reviewed-output rendering.
- Affected docs: update the rendering/execution plan, README/AGENTS, CLI docs, OpenSpec config, and separate English/Spanish role guides for contributors, professors, students, and agents.
- Safety boundary: reviewed output commands read generated results and write reviewed source support but never execute targets; only `raya run` may execute explicit local targets.
