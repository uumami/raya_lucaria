## Why

Raya Lucaria can now validate, render, copy, and describe code/notebook references, but students and professors still lack an accepted local way to execute the referenced work. Phase 4 should add a deliberate `raya run` path that uses the Phase 3 runtime/profile/cache metadata without making normal static builds execute code.

## What Changes

- Add a local execution capability for explicit code and notebook targets.
- Add `raya run <course> <target>` as the user-facing command shape.
- Execute Python scripts through `uv run` using declared runtime profiles.
- Execute notebooks through established Jupyter execution tooling under the selected runtime profile.
- Add Docker plus `uv` execution as an explicit wrapper option for classroom reproducibility.
- Add cache reuse and `--refresh` behavior for `cache` policy targets.
- Add generated execution output, log, and cache directories under the artifact root.
- Preserve static builds: `raya build` still does not execute scripts, notebooks, kernels, `uv`, Docker, package installers, or cache refreshes.
- Defer browser execution, remote runners, GPU runners, trusted frozen-output publication, and multi-user execution services.

## Capabilities

### New Capabilities

- `local-execution-baseline`: Defines explicit local execution for referenced scripts and notebooks using runtime profiles, cache reuse, logs, and generated outputs.

### Modified Capabilities

- `cli-contract-baseline`: Adds the `raya run` command surface, exit behavior, diagnostics, and dry-run behavior.
- `runtime-profile-cache-baseline`: Uses accepted runtime profiles, execution policies, and cache keys for actual local execution.
- `code-notebook-references`: Allows referenced scripts and notebooks to become executable targets only when selected explicitly.
- `artifact-contract-baseline`: Adds generated execution output, log, and cache directories and manifest-declared execution result metadata.
- `artifact-inspection-command`: Validates generated execution result metadata and referenced output/log/cache files without re-executing.
- `dev-workflow-baseline`: Adds host and Docker verification for local execution behavior and no-execution static builds.

## Impact

- Affected packages: `packages/cli`, `packages/schema`, and a new or existing execution helper boundary.
- Potential dependency impact: Jupyter notebook execution tooling may be added behind the execution boundary; it must not affect static rendering contracts.
- Affected fixtures: add executable script and notebook fixtures with sentinel outputs, cache behavior, refresh behavior, and Docker metadata.
- Affected artifacts: add generated execution outputs/logs/cache files and metadata surfaces under the artifact root.
- Affected docs: update the rendering/execution plan, README/AGENTS command guidance, and separated English/Spanish role guides.
- Safety boundary: execution requires an explicit `raya run` command and target; `raya validate`, `raya build`, and `raya artifacts inspect` remain non-executing.
