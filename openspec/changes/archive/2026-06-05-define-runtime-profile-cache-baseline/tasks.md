## 1. Runtime Source Model

- [x] 1.1 Add schema-layer data structures for runtime profiles, execution policies, execution targets, and cache key records.
- [x] 1.2 Parse optional `runtime/profiles.yaml` beside the configured `course/` tree.
- [x] 1.3 Treat `runtime/` as private source support that does not render as pages, indexes, assets, or official objects.
- [x] 1.4 Preserve root `pyproject.toml`, `uv.lock`, Docker files, and runtime metadata as support files outside source ordering.
- [x] 1.5 Define the default inferred `uv` profile behavior when root runtime files exist and no profile file is declared.

## 2. Validation And Diagnostics

- [x] 2.1 Validate supported `uv` runtime profile fields.
- [x] 2.2 Reject unsupported runtime managers with actionable diagnostics.
- [x] 2.3 Validate declared project and lockfile paths stay under the course root and exist according to accepted strictness.
- [x] 2.4 Validate execution policy values: `never`, `manual`, `cache`, `always`, and `frozen`.
- [x] 2.5 Require target-specific declarations for `always`.
- [x] 2.6 Validate declared cache input paths and path-escape failures.
- [x] 2.7 Ensure validation never calls `uv`, Docker, kernels, package installers, or executable source files.

## 3. Artifact Contracts

- [x] 3.1 Add runtime metadata schema or validator.
- [x] 3.2 Add execution-plan metadata schema or validator.
- [x] 3.3 Add cache metadata schema or validator.
- [x] 3.4 Extend manifest schema for optional runtime, execution-plan, and cache data declarations.
- [x] 3.5 Update artifact inspection to validate runtime, execution-plan, and cache metadata without execution.
- [x] 3.6 Add artifact inspection diagnostics for invalid profile references, policy values, cache hashes, and escaping declared paths.

## 4. Builder Metadata

- [x] 4.1 Generate runtime metadata when a course declares or infers runtime profiles.
- [x] 4.2 Generate execution-plan metadata for code/notebook references with default policy `never` and status `not-executed`.
- [x] 4.3 Generate cache-key metadata for references that declare `cache`, `always`, or `frozen`.
- [x] 4.4 Add policy/profile/cache metadata hooks to `references.json` without breaking existing Phase 2 reference behavior.
- [x] 4.5 Keep static pages, reference links, reference panels, assets, navigation, generated indexes, and static read paths unchanged.
- [x] 4.6 Ensure builder validation never executes scripts, notebooks, `uv`, Docker, kernels, or cache refreshes.

## 5. Fixtures And Examples

- [x] 5.1 Add a valid runtime-profile fixture with `runtime/profiles.yaml`, `pyproject.toml`, `uv.lock`, code references, and Docker Compose service metadata.
- [x] 5.2 Label the valid runtime fixture as fixture material, not pedagogy or architecture canon.
- [x] 5.3 Add invalid fixture coverage for unsupported runtime manager.
- [x] 5.4 Add invalid fixture coverage for missing project file or lockfile diagnostics.
- [x] 5.5 Add invalid fixture coverage for escaping runtime paths or cache input paths.
- [x] 5.6 Add invalid fixture coverage for unsafe `always` policy defaults.

## 6. Contract And E2E Tests

- [x] 6.1 Add contract tests for runtime profile parsing and validation.
- [x] 6.2 Add contract tests for execution policy validation and diagnostics.
- [x] 6.3 Add contract tests for generated runtime, execution-plan, and cache data schemas.
- [x] 6.4 Add contract tests for artifact inspection of runtime and cache metadata.
- [x] 6.5 Add builder tests proving runtime metadata does not change static page rendering or reference downloads.
- [x] 6.6 Add e2e/static-read-path coverage that serves the runtime fixture artifact and confirms pages remain static.
- [x] 6.7 Add tests proving no execution sentinel files or side effects are produced during validation, build, inspection, or e2e serving.

## 7. Documentation And Guidance

- [x] 7.1 Update `docs/foundation/17_rendering_execution_plan.md` with accepted Phase 3 runtime/cache baseline decisions.
- [x] 7.2 Update English role guides for contributors/collaborators, professors, students, and agents.
- [x] 7.3 Update Spanish role guides for colaboradores, profesores, estudiantes, and agentes with separated pages and English technical identifiers.
- [x] 7.4 Update README and AGENTS only where runtime metadata commands, fixtures, or workflow expectations change.
- [x] 7.5 Update OpenSpec config if future proposal rules need tighter runtime/cache guidance.
- [x] 7.6 Verify live documentation remains renderable with `raya validate docs` and `raya build docs`.

## 8. Verification

- [x] 8.1 Run focused host tests for schema, validation, builder, artifact inspection, documentation surfaces, and e2e coverage.
- [x] 8.2 Run the full host test suite.
- [x] 8.3 Run a Docker Compose reference workflow for runtime metadata tests or document any Docker workflow gap.
- [x] 8.4 Run `openspec validate define-runtime-profile-cache-baseline --strict`.
- [x] 8.5 Run `openspec validate --specs --strict` before archive.
- [x] 8.6 Run `git diff --check` and remove generated artifacts before completion.
