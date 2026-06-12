## 1. Reviewed Output Model And Schemas

- [x] 1.1 Add reviewed output data structures and source manifest parsing.
- [x] 1.2 Add reviewed output artifact schema.
- [x] 1.3 Add reviewed output source manifest schema or validator.
- [x] 1.4 Add freshness metadata for source hash, input hashes, runtime profile hash, lockfile hash, cache key, and reviewed file hashes.
- [x] 1.5 Add path safety validation for `_reviewed/` manifests and files.
- [x] 1.6 Export reviewed output validators from `packages/schema`.

## 2. Source Discovery And Validation

- [x] 2.1 Add `_reviewed/` to private source support handling without rendering it as pages.
- [x] 2.2 Discover reviewed output manifests under own-or-ancestor `_reviewed/` ownership boundaries.
- [x] 2.3 Validate current reviewed output succeeds for matching source/runtime/cache/file hashes.
- [x] 2.4 Validate stale reviewed output fails with actionable diagnostics.
- [x] 2.5 Validate missing reviewed files fail with actionable diagnostics.
- [x] 2.6 Validate `policy: frozen` requires current reviewed output without execution.

## 3. CLI Output Commands

- [x] 3.1 Add `raya outputs` command group.
- [x] 3.2 Add `raya outputs list <course>` with target/generated/reviewed/frozen status.
- [x] 3.3 Add `raya outputs freeze <course> <target>` using the latest successful generated execution result.
- [x] 3.4 Make freeze copy reviewed files into colocated `_reviewed/` source support.
- [x] 3.5 Make freeze write reviewed source metadata and report outputs written.
- [x] 3.6 Make list and freeze refuse malformed, missing, failed, or stale generated/reviewed output without executing.

## 4. Frozen Policy Behavior

- [x] 4.1 Change `raya run` frozen targets to validate reviewed output instead of refusing unconditionally.
- [x] 4.2 Ensure frozen target validation does not call `uv`, Docker, kernels, notebooks, scripts, or cache refreshes.
- [x] 4.3 Ensure missing reviewed output for frozen targets exits nonzero.
- [x] 4.4 Ensure stale reviewed output for frozen targets exits nonzero.
- [x] 4.5 Preserve `never`, `manual`, `cache`, and `always` behavior from Phase 4.

## 5. Artifact And Static Rendering

- [x] 5.1 Generate manifest-declared `data/reviewed-outputs.json`.
- [x] 5.2 Copy reviewed files to artifact-level reviewed storage.
- [x] 5.3 Copy reviewed files to browser-facing static reviewed storage under `site/_raya/`.
- [x] 5.4 Extend artifact inspection to validate reviewed output data and copied files without execution.
- [x] 5.5 Associate reviewed output status with code/notebook reference data.
- [x] 5.6 Render compact reviewed-output panels with deployment-neutral links or excerpts.
- [x] 5.7 Fail build before rendering stale reviewed output as current.

## 6. Fixtures And Tests

- [x] 6.1 Add or extend a reviewed output fixture with script output, notebook output, and `policy: frozen`.
- [x] 6.2 Add invalid reviewed output fixtures or equivalent tests for stale hashes, missing files, escaping paths, and missing reviewed output.
- [x] 6.3 Add CLI tests for `raya outputs list`.
- [x] 6.4 Add CLI tests for `raya outputs freeze`.
- [x] 6.5 Add tests proving freeze refuses failed and stale generated results.
- [x] 6.6 Add tests proving frozen targets validate reviewed output without executing.
- [x] 6.7 Add artifact schema and artifact inspection tests for reviewed output data/files.
- [x] 6.8 Add static-read-path e2e tests for reviewed panels and linked reviewed files.
- [x] 6.9 Add no-execution regression tests for validate, build, inspect, outputs list, outputs freeze, and static serving.

## 7. Documentation And Guidance

- [x] 7.1 Update `docs/foundation/17_rendering_execution_plan.md` with the accepted reviewed/frozen baseline.
- [x] 7.2 Update English role guides for contributors/collaborators, professors, students, and agents.
- [x] 7.3 Update Spanish role guides for colaboradores, profesores, estudiantes, and agentes.
- [x] 7.4 Update README, AGENTS, CLI README, schema/static package docs, and OpenSpec config.
- [x] 7.5 Verify live docs with `raya validate docs` and `raya build docs`.

## 8. Verification And Archive Readiness

- [x] 8.1 Run focused host tests for reviewed output schema, validation, CLI, artifact inspection, rendering, frozen policy, and no-execution regressions.
- [x] 8.2 Run full host test suite.
- [x] 8.3 Run representative Docker Compose workflow or document any Docker gap.
- [x] 8.4 Run `openspec validate define-reviewed-execution-output-baseline --strict`.
- [x] 8.5 Run `openspec validate --specs --strict` before archive.
- [x] 8.6 Run `git diff --check`.
- [x] 8.7 Remove generated artifacts and local exploratory output before completion.
