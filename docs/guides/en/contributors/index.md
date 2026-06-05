---
id: docs-guides-en-contributors
title: Contributors And Collaborators
nav_title: Contributors
summary: Workflow guidance for changing code, specs, docs, tests, and contracts safely.
status: ready
---
# Contributors And Collaborators

Start with `docs/foundation/15_system_overview.md`, then `docs/foundation/13_truth_surfaces.md`, then the accepted OpenSpec specs for the capability you are changing.

Use the Docker Compose and `uv` commands from `README.md` and `AGENTS.md` when changing code, contracts, docs, or tests. Keep package paths, commands, schema fields, and stable IDs in English.

When changing course validation or rendering, preserve the convention-first source model: `source: course` points at the ordered `course/` tree, ordered filenames define authoring order, frontmatter `id` defines stable identity, colocated `_official/` and `_assets/` stay private, and `navigation.json` plus `indices.json` are generated artifact data. Tests should cover source diagnostics, official object export, asset copying, artifact schemas, and static-read-path rendering.

Rich static rendering is Glintstone-owned. Keep parser, highlighter, and math libraries behind the `packages/static` boundary; source contracts should describe supported authoring behavior, not library internals. Renderer changes need representative fixtures, invalid diagnostics when applicable, contract tests, e2e/static-read-path tests, and role documentation updates.

Code and notebook references are static source support in the current baseline. Validate `.py` links under `code/` and `.ipynb` links under `notebooks/`, copy referenced files to manifest-declared `artifact/files/` and `artifact/site/_raya/files/`, keep `references.json` machine-readable, and preserve the `not-executed` status until an execution proposal accepts runtimes and caches.

Runtime profiles are metadata only. Keep `runtime/profiles.yaml`, `pyproject.toml`, and `uv.lock` outside the ordered `course/` tree; validate policies, profile paths, cache inputs, and generated `runtime.json`, `execution.json`, and `cache.json` without calling `uv`, Docker, kernels, or source files.

Local execution is explicit. `raya run <course> <target>` may run one validated script or notebook through the selected `uv` profile, with `--docker` only when requested and configured. Execution changes need CLI tests for dry-run, policies, cache reuse, refresh, logs, output files, notebook output preservation, Docker command shape, artifact inspection, and no-execution regressions for validate/build/inspect/static serving.

Current documentation is also a renderable docs course. Edit the readable pages under `docs/foundation/` and `docs/guides/`, keep `docs/render-content/` aligned for rendered order, and treat `docs/artifact/` as ignored generated output. Use `raya validate docs`, `raya build docs`, and static-read-path tests when changing documentation rendering behavior.

For substantial changes, state the documentation impact for contributors/collaborators, professors, students, and agents. If role documentation changes, keep the English and Spanish pages separate.
