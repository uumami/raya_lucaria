---
id: docs-guides-en-contributors
title: Contributors And Collaborators
nav_title: Contributors
summary: Workflow guidance for changing code, specs, docs, tests, and contracts safely.
status: ready
---
# Contributors And Collaborators

Start with `docs/foundation/15_system_overview.md`, then `docs/foundation/13_truth_surfaces.md`, then the accepted OpenSpec specs for the capability you are changing.

Use the Docker Compose and `uv` commands from `README.md` and `AGENTS.md` when changing code, contracts, docs, or tests. Run `./scripts/check.sh` before archive or commit, run `./scripts/check-docker.sh` when Docker behavior changes, and keep `./scripts/smoke-test.sh` for external-course smoke checks when command or course portability changes. Keep deferred capabilities in `docs/foundation/18_known_missing_work.md` until an accepted OpenSpec change makes them current. Keep package paths, commands, schema fields, and stable IDs in English.

When changing course validation or rendering, preserve the convention-first source model: `source: course` points at the ordered `course/` tree, ordered filenames define authoring order, frontmatter `id` defines stable identity, colocated `_official/` and `_assets/` stay private, and `navigation.json` plus `indices.json` are generated artifact data. Tests should cover source diagnostics, official object export, asset copying, artifact schemas, and static-read-path rendering.

Rich static rendering is Glintstone-owned. Keep parser, highlighter, and MathJax libraries behind the `packages/static` boundary; source contracts should describe supported authoring behavior, not library internals. Accepted math uses inline dollar math, display dollar-delimiter blocks, page-local macros, local `site/_raya/render/math/` support resources, strict diagnostics, and no browser-only renderer dependency. Renderer changes need representative fixtures, invalid diagnostics when applicable, contract tests, e2e/static-read-path tests, Chromium visible-math/no-external-request checks, desktop/mobile overflow checks, and role documentation updates.

Before changing renderer behavior, run the focused parity gate with `scripts/check-render-debug.sh`. It builds and previews `examples/courses/render-fixture`, captures desktop/mobile render-debug artifacts, and fails on visible raw TeX, external renderer requests, missing screenshots, overflow, or browser-side MathJax runtime dependencies. The gate writes `report.json` and `index.html` beside the screenshots. When it fails, inspect `index.html` first, then use `report.json` for exact page, viewport, file path, and copied-site diagnostics. For an individual course regression, use `raya preview <course> --render-debug /tmp/raya-render-debug`. Treat those files as local evidence only; do not commit them and do not treat them as artifact authority.

Code and notebook references are static source support in the current baseline. Validate linked `.py` and `.ipynb` files by extension and own-or-ancestor quantum ownership, not by required folder names. Copy only validated linked files to manifest-declared `artifact/files/` and `artifact/site/_raya/files/`, keep `references.json` machine-readable, and preserve the `not-executed` status until an execution proposal accepts runtimes and caches.

Runtime profiles are metadata only. Keep `runtime/profiles.yaml`, `pyproject.toml`, and `uv.lock` outside the ordered `course/` tree; validate policies, profile paths, cache inputs, and generated `runtime.json`, `execution.json`, and `cache.json` without calling `uv`, Docker, kernels, or source files.

Local execution is explicit. `raya run <course> <target>` may run one validated script or notebook through the selected `uv` profile, with `--docker` only when requested and configured. Execution changes need CLI tests for dry-run, policies, cache reuse, refresh, logs, output files, notebook output preservation, Docker command shape, artifact inspection, and no-execution regressions for validate/build/inspect/static serving.

Reviewed execution output is the source-controlled frozen path. Keep reviewed files under colocated `_reviewed/execution/<target>/`, validate `reviewed.yaml` against current source/runtime/input/review/file hashes, and expose current reviewed output through `data/reviewed-outputs.json`, `artifact/reviewed/`, `site/_raya/reviewed/`, reference metadata, and static panels. Changes need tests for `raya outputs list`, `raya outputs freeze`, stale metadata, missing files, `policy: frozen`, artifact inspection, static read paths, and no-execution regressions.

Rendered pages use surface discipline. Keep normal pages focused on authored content, navigation, generated indexes, compact resource/status panels, and deployment-neutral links. Put verbose hashes, cache keys, source paths, artifact paths, and reviewed-output freshness internals in `manifest.json`, `data/*.json`, or static `_raya/inspect/` pages.

Use `raya preview <course>` for local review of generated static pages. Preview validates, builds, serves `artifact/site/`, and reports the student entrypoint plus `_raya/inspect/` URL when present. Preview changes need CLI tests, no-execution regressions, static-read-path coverage, and visual/layout assertions for representative desktop and mobile-sized viewports.

Current documentation is also a renderable docs course. Edit the readable pages under `docs/foundation/` and `docs/guides/`, keep `docs/render-content/` aligned for rendered order, and treat `docs/artifact/` as ignored generated output. Use `raya validate docs`, `raya build docs`, and static-read-path tests when changing documentation rendering behavior.

For substantial changes, state the documentation impact for contributors/collaborators, professors, students, and agents. If role documentation changes, keep the English and Spanish pages separate.
