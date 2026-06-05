## 1. Execution Boundary And Schemas

- [x] 1.1 Add an execution helper boundary for local run behavior.
- [x] 1.2 Add execution target resolution from reference ID, execution target ID, and course-root-relative source path.
- [x] 1.3 Add generated execution result data structures.
- [x] 1.4 Add execution result schema or validator.
- [x] 1.5 Extend manifest/artifact inspection for generated execution result data.
- [x] 1.6 Ensure execution outputs, logs, and cache results are generated artifact data, not source truth.

## 2. CLI Command Surface

- [x] 2.1 Add `raya run <course> <target>` to the CLI.
- [x] 2.2 Add `--dry-run` to report the resolved execution plan without running.
- [x] 2.3 Add `--refresh` for cache policy targets.
- [x] 2.4 Add `--docker` for explicit Docker plus `uv` execution.
- [x] 2.5 Preserve nonzero exit behavior and actionable diagnostics for run failures.
- [x] 2.6 Update CLI help and CLI README command guidance.

## 3. Policy And Target Behavior

- [x] 3.1 Refuse `never` policy targets without executing.
- [x] 3.2 Execute `manual` policy targets only when explicitly selected.
- [x] 3.3 Reuse valid cache results for `cache` policy targets.
- [x] 3.4 Rerun cache policy targets when `--refresh` is passed.
- [x] 3.5 Execute `always` policy targets only when explicitly selected.
- [x] 3.6 Refuse `frozen` policy targets until a frozen-output trust contract exists.
- [x] 3.7 Fail when a selected target is not a validated reference or accepted source path.

## 4. Script Execution

- [x] 4.1 Construct local `uv` command shapes from runtime profile metadata.
- [x] 4.2 Execute `.py` targets through `uv run` from the course root.
- [x] 4.3 Capture stdout, stderr, exit code, and start/end timestamps.
- [x] 4.4 Write script execution logs and result metadata under the artifact root.
- [x] 4.5 Fail clearly when `uv` is unavailable.
- [x] 4.6 Add script execution fixtures with sentinel outputs.

## 5. Notebook Execution

- [x] 5.1 Add notebook execution dependency or adapter behind the execution boundary.
- [x] 5.2 Execute `.ipynb` targets through established Jupyter tooling under the selected runtime profile.
- [x] 5.3 Write generated output notebooks under the artifact root.
- [x] 5.4 Preserve authored source notebooks unchanged.
- [x] 5.5 Fail clearly when notebook tooling is unavailable.
- [x] 5.6 Add notebook execution fixtures with source-mutation assertions.

## 6. Docker Execution

- [x] 6.1 Resolve Docker Compose service metadata from runtime profiles.
- [x] 6.2 Report Docker command shape in dry-run mode.
- [x] 6.3 Execute selected targets through Docker Compose plus `uv` when `--docker` is requested.
- [x] 6.4 Fail clearly when `--docker` is requested without profile Docker metadata.
- [x] 6.5 Add representative Docker workflow tests or document environment gaps.

## 7. Cache And Output Artifacts

- [x] 7.1 Define generated execution output, log, and cache result directory layout.
- [x] 7.2 Write cache result records with cache key, policy, target, profile, status, and output/log paths.
- [x] 7.3 Validate cache hit reuse does not rerun target code.
- [x] 7.4 Validate refresh reruns target code and updates cache result metadata.
- [x] 7.5 Validate artifact inspection checks declared output/log/cache paths without re-executing.

## 8. No-Execution Regression Coverage

- [x] 8.1 Prove `raya validate` does not execute executable fixtures.
- [x] 8.2 Prove `raya build` does not execute executable fixtures.
- [x] 8.3 Prove `raya artifacts inspect` does not execute executable fixtures.
- [x] 8.4 Prove static serving does not execute executable fixtures.
- [x] 8.5 Keep Phase 1-3 static read path behavior unchanged.

## 9. Documentation And Guidance

- [x] 9.1 Update `docs/foundation/17_rendering_execution_plan.md` with the accepted Phase 4 baseline.
- [x] 9.2 Update English role guides for contributors/collaborators, professors, students, and agents.
- [x] 9.3 Update Spanish role guides for colaboradores, profesores, estudiantes, and agentes.
- [x] 9.4 Update README, AGENTS, and OpenSpec config with `raya run` safety and workflow guidance.
- [x] 9.5 Verify live docs with `raya validate docs` and `raya build docs`.

## 10. Verification

- [x] 10.1 Run focused host tests for CLI, execution helpers, artifact inspection, and no-execution regressions.
- [x] 10.2 Run full host test suite.
- [x] 10.3 Run representative Docker Compose workflow or document any Docker gap.
- [x] 10.4 Run `openspec validate define-local-execution-baseline --strict`.
- [x] 10.5 Run `openspec validate --specs --strict` before archive.
- [x] 10.6 Run `git diff --check` and remove generated artifacts before completion.
