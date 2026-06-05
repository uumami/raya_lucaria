## Why

Raya Lucaria can now render rich static notes, but serious data and computing courses also need pages to point at scripts and notebooks without running them during ordinary builds. Phase 2 defines that static reference layer so future runtime profiles, caches, local execution, and browser execution have a clean source and artifact contract to build on.

## What Changes

- Define `code/` and `notebooks/` as user-facing source support directories owned by the nearest learning quantum.
- Keep code and notebooks out of rendered navigation, `_assets/`, and `_official/`.
- Validate Markdown references to supported `.py` and `.ipynb` files before build.
- Copy referenced code and notebook files into artifact-level inspection storage and browser-facing static storage.
- Generate manifest-declared `data/references.json` for code and notebook references.
- Render deployment-neutral links and small static reference panels or previews for referenced scripts and notebooks.
- Add representative fixtures, invalid fixtures, contract tests, e2e/static-read-path tests, live documentation coverage, and English/Spanish role guidance.
- Defer all execution behavior: no `raya run`, no kernels, no runtime profiles, no cache refresh, no trusted notebook output, no Pyodide/JupyterLite, and no remote runners.

## Capabilities

### New Capabilities

- `code-notebook-references`: Defines source conventions, validation, artifact data, copying, static rendering, and no-execution behavior for referenced code and notebook files.

### Modified Capabilities

- `course-source-contract`: Treat `code/` and `notebooks/` as authored source support directories that do not render as navigation entries.
- `source-link-asset-validation`: Validate local Markdown references to supported code and notebook files separately from local content links and `_assets/`.
- `minimal-static-builder`: Copy referenced code/notebook files, rewrite links to static paths, and render generated reference surfaces without executing code.
- `artifact-contract-baseline`: Declare `references.json` and artifact file storage when code/notebook references are present.
- `artifact-inspection-command`: Validate manifest-declared reference data and copied reference files during artifact inspection.
- `static-render-resource-resolution`: Reserve browser-facing generated reference files under `site/_raya/files/` with deployment-neutral URLs.
- `dev-workflow-baseline`: Require fixtures, invalid diagnostics, contract tests, e2e/static-read-path tests, docs, and role guidance for code/notebook reference changes.

## Impact

- Affected packages: `packages/schema` link/reference validation and source support classification, `packages/static` artifact builder and renderer integration, and artifact inspection helpers if reference data is added.
- Affected artifacts: `artifact/files/`, `artifact/site/_raya/files/`, `artifact/data/references.json`, `manifest.json`, generated HTML links/panels, and existing link/index data if code/notebook references are exported.
- Affected fixtures: a representative code/notebook reference course fixture, invalid fixtures for missing/unsupported/path-escaping/private references, and rendered documentation examples.
- Affected documentation: `docs/foundation/17_rendering_execution_plan.md` is the planning anchor; English and Spanish role guides need compact author/student/agent guidance if behavior lands.
- No runtime dependency is introduced. `uv`, Docker execution, notebook kernels, execution caches, Pyodide/JupyterLite, marimo, remote runners, and `raya run` remain future phases.
