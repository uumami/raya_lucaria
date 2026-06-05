## Context

Raya Lucaria has a stable static path, validated code/notebook references, and runtime/cache metadata. The current system can tell users what could run, under which profile, and with which cache key, but it intentionally does not execute anything. Phase 4 adds the first execution surface while preserving the Phase 1-3 no-execution guarantees for `raya validate`, `raya build`, static serving, and artifact inspection.

The execution boundary belongs outside Glintstone static rendering. A local execution helper can live under a plain package boundary such as `execution` or inside the CLI package until the implementation is large enough to split. The CLI remains the user-facing entry point.

## Goals / Non-Goals

**Goals:**

- Add `raya run <course> <target>` for explicit single-target execution.
- Resolve targets from accepted code/notebook references, source paths, or generated execution metadata.
- Execute Python scripts through `uv run` using the selected runtime profile.
- Execute notebooks through established Jupyter execution tooling under the selected runtime profile.
- Support an explicit Docker plus `uv` wrapper path when profile metadata declares a Compose service.
- Reuse cache entries for `cache` policy targets and refresh them with `--refresh`.
- Write generated outputs, logs, and result metadata under the artifact root.
- Keep static build and static read paths useful without execution.

**Non-Goals:**

- Execute all course targets by default.
- Execute during `raya validate`, `raya build`, `raya artifacts inspect`, or static serving.
- Add browser execution, remote runners, GPU runners, multi-user services, or realtime state.
- Publish trusted frozen outputs into course source.
- Add a web UI for execution results.
- Make Docker mandatory for local execution.

## Decisions

1. `raya run <course> <target>` requires an explicit target.

Targets may resolve by reference ID, execution target ID, or course-root-relative source path. Running an entire course is useful later, but it is too easy to trigger expensive or unsafe work early.

Alternative considered: `raya run <course>` executes every runnable target. That is convenient for CI, but it violates the foundation bias against accidental expensive execution.

2. `raya run` writes generated execution state under the artifact root.

Execution result metadata belongs under `artifact/data/`, while logs, outputs, and cached result records live under generated artifact directories such as `artifact/execution/`, `artifact/logs/`, and `artifact/cache/`. These are rebuildable/generated surfaces, not course truth.

Alternative considered: write into source beside the executed file. That would make review difficult and blur authored material with generated results.

3. `uv` is the default local script runner.

For scripts, the implementation should execute from the course root with a command equivalent to `uv run python <source>`, using the selected runtime profile paths. It must capture stdout, stderr, exit code, start/end time, and generated result metadata.

Alternative considered: execute through the current Python interpreter. That is simpler for tests, but it would make classroom behavior diverge from the accepted `uv` profile contract.

4. Notebook execution uses established Jupyter tooling.

Notebook execution should use accepted notebook libraries rather than hand-rolling `.ipynb` execution. The output notebook is generated output, not trusted course source. If notebook tooling is unavailable, diagnostics should be actionable.

Alternative considered: treat notebooks as scripts by extracting code cells. That loses notebook semantics, metadata, and output handling.

5. Docker execution is explicit.

Docker plus `uv` is the reference classroom reproducibility path, but `raya run` should only use Docker when requested, such as `--docker`, and when the selected profile declares a Compose service. The command should report the Docker command shape before execution in `--dry-run`.

Alternative considered: automatically use Docker when profile metadata exists. That surprises local authors and makes ordinary local workflows slower.

6. Cache policy affects execution behavior.

`never` refuses execution unless a future explicit override is accepted. `manual` runs only when explicitly targeted. `cache` reuses a valid cached result unless `--refresh` is passed. `always` runs whenever explicitly targeted. `frozen` fails until a later trusted-output contract accepts frozen output validation.

Alternative considered: treat all targeted execution the same. That would make the policy metadata decorative and unsafe.

## Risks / Trade-offs

- Running arbitrary course code is inherently risky -> require explicit target, keep diagnostics concrete, and do not execute in build/inspect/static paths.
- `uv` may be missing locally -> fail with a clear diagnostic and keep Docker as an optional path.
- Notebook execution dependencies may be heavy -> isolate them behind execution-only dependencies and tests.
- Docker behavior varies by host -> keep Docker optional and command-shaped, with representative Compose tests where available.
- Cache invalidation can miss undeclared inputs -> require declared inputs for baseline cache keys and document that hidden dependencies are not tracked yet.
- Generated outputs can be mistaken for official source -> keep outputs under artifact directories and mark authority as generated.

## Migration Plan

1. Add execution helpers and generated result schemas.
2. Add `raya run` CLI parsing, dry-run diagnostics, and exit behavior.
3. Implement explicit target resolution from runtime/reference metadata.
4. Implement script execution through `uv run`.
5. Implement notebook execution through accepted Jupyter tooling.
6. Implement cache reuse, refresh, output/log writing, and artifact inspection validation.
7. Add fixtures, contract tests, CLI tests, Docker representative checks, and docs.

Rollback is straightforward: remove `raya run` and execution result validators. Existing static build artifacts and metadata-only contracts remain valid.

## Open Questions

- Should future multi-target execution use an explicit target group in `runtime/profiles.yaml` or a CLI selector?
- Should frozen outputs eventually be committed source, reviewed generated artifact data, or both?
- Should CI execution live under `raya run` flags or a separate `raya verify` command later?
