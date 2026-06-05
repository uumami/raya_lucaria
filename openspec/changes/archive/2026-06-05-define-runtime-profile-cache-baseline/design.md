## Context

Raya Lucaria now has a static Glintstone read path and a Phase 2 code/notebook reference contract. Referenced `.py` and `.ipynb` files validate, copy into artifacts, render as static links/previews, and record `not-executed` status. The next phase should make future execution predictable without actually running anything.

The foundation already names the main constraints: `uv` is the default Python runtime contract, Docker plus `uv` is the reproducible classroom path, static rendering must not rerun heavy or unsafe work, and execution outputs are generated artifact data unless a future accepted contract says otherwise.

## Goals / Non-Goals

**Goals:**

- Define where runtime profile source lives and how it relates to `course/`.
- Define the baseline profile file shape using `runtime/profiles.yaml`.
- Define `uv` as the default profile manager and Docker plus `uv` as the reference reproducibility profile.
- Define execution policy metadata for `never`, `manual`, `cache`, `always`, and `frozen`.
- Define cache-key inputs and generated metadata surfaces for future execution managers.
- Add validation and fixture coverage for runtime metadata without executing code.
- Keep current static builds useful and deterministic.

**Non-Goals:**

- Add `raya run`, script execution, notebook execution, kernels, or output trust.
- Install dependencies, create environments, call Docker, or execute `uv`.
- Add Pyodide, JupyterLite, marimo, remote runners, GPUs, or backend services.
- Treat generated execution outputs as source truth.
- Solve shared cross-quantum code reuse.

## Decisions

1. Runtime profile source lives beside `course/`.

Runtime files support execution; they do not define learning order. A course may contain root-level `pyproject.toml`, `uv.lock`, and `runtime/profiles.yaml` beside `course/`. Files under `runtime/` are private support material and never render as pages.

Alternative considered: profile metadata inside `raya.yaml`. That keeps configuration centralized, but it would make execution metadata grow inside the course entrypoint and blur static course metadata with runtime concerns.

2. `runtime/profiles.yaml` defines named profiles.

The first supported profile manager is `uv`. A minimal profile can name `manager: uv`, a Python constraint, a project file, a lockfile, and optional Docker Compose service metadata. Profile names are stable metadata keys, not UI labels.

Alternative considered: infer everything from `pyproject.toml` and `uv.lock`. Inference is convenient for trivial courses, but named profiles are needed for future CPU/GPU, local/Docker, and manual/cache/frozen differences.

3. Execution policy metadata is explicit and defaults to `never`.

Every executable target must resolve to one of `never`, `manual`, `cache`, `always`, or `frozen`. Phase 3 records plans and cache metadata only; `never` and `manual` are the safe defaults. `always` must be explicit because it can make builds slow or unsafe later.

Alternative considered: use booleans like `execute: true`. Booleans are too coarse for cached outputs, frozen reviewed outputs, and manual classroom workflows.

4. Cache keys are computed from declared inputs, not output files.

Cache metadata should include code or notebook source hash, referenced input file hashes when declared, runtime profile hash, lockfile hash when present, execution policy, and relevant Raya/Glintstone schema or renderer version. The cache key is a plan identity, not proof that execution already happened.

Alternative considered: use file mtimes. Mtimes are not portable across Git, archives, Docker mounts, and static hosting.

5. Artifacts expose generated metadata, not execution side effects.

The baseline can generate `data/runtime.json`, `data/execution.json`, and `data/cache.json` when runtime profiles or executable references exist. These files describe profiles, plans, and cache keys; they do not contain trusted outputs or logs. Future output/log roots can be added by a later execution proposal.

Alternative considered: create empty `execution/` and `cache/` directories now. That makes the artifact look execution-ready before the execution contract exists, so Phase 3 should stay metadata-only.

6. Validation is source-oriented and non-executing.

Validation may parse profile files, check path containment, check that declared project and lockfile paths exist when required, and warn or fail for unsafe defaults. It must not create virtual environments, call Docker, run `uv`, execute notebooks, or refresh caches.

## Risks / Trade-offs

- Profile schema becomes too detailed too early -> keep the first schema minimal and allow future adapters through explicit profile manager fields.
- Authors expect `cache` or `always` to run during build -> generated HTML, artifact metadata, and docs must keep saying Phase 3 does not execute.
- Docker metadata differs by institution -> record Docker Compose service metadata only as a reference path, not as a required hosting dependency.
- Cache keys miss hidden inputs -> require declared inputs now and allow future execution proposals to add dependency discovery.
- `runtime/profiles.yaml` adds another source file -> keep it optional and infer a default `uv` profile only when root `pyproject.toml`/`uv.lock` are present.

## Migration Plan

1. Add schema helpers for runtime profile parsing and policy validation.
2. Add artifact schemas for runtime, execution-plan, and cache metadata.
3. Extend validation and builder behavior with metadata-only output.
4. Add valid and invalid fixtures.
5. Update foundation docs, role guides, README/AGENTS only where workflow guidance changes.
6. Keep existing courses valid when they do not declare runtime profiles.

Rollback is straightforward: remove runtime metadata generation and validators. Existing Phase 1/2 static builds and reference artifacts remain valid because no execution behavior changes.

## Open Questions

- Should future shared code live in a course-level support namespace or remain explicit per quantum?
- Should `frozen` outputs eventually live in source after review, or only in generated artifacts with source-side approval metadata?
- Should notebook kernels be declared per profile, per notebook, or inferred from profile environment after execution support exists?
