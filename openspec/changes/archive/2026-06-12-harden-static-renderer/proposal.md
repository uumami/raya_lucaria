## Why

Glintstone currently preserves TeX inside static math elements, but serious
math-heavy courses need actual typeset math. Rendering must be identical for
local preview, offline artifacts, and web deployment, so math must be rendered
during `raya build` into the same `artifact/site/` files that preview and static
hosting serve.

## What Changes

- Add build-time MathJax rendering through an isolated renderer adapter.
- Keep one canonical static artifact path for local preview and web deployment.
- Strengthen math, image, link, code, and layout fixtures.
- Add Chromium checks proving math is visibly typeset and no external renderer
  assets are requested.
- Add strict diagnostics for math that would visibly break published pages.
- Update foundation docs, role guides, `AGENTS.md`, and `openspec/config.yaml`.

## Non-Goals

- No official study-object UI.
- No personal study state.
- No browser-only MathJax as the canonical baseline.
- No course-code execution through validation, build, preview, or inspection.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `rich-static-rendering`: Require Glintstone to pre-render supported
  TeX/LaTeX math with build-time MathJax and fail clearly when math would render
  as broken published content.
- `minimal-static-builder`: Require generated artifacts to carry local MathJax
  support resources and deployment-neutral links through the same
  `artifact/site/` read path used by preview and static hosting.
- `dev-workflow-baseline`: Require contract, fixture, static-read-path,
  Chromium, Docker, local `uv`, and documentation verification for hardened
  renderer behavior.

## Impact

- Affected foundation: `docs/foundation/17_rendering_execution_plan.md`,
  `docs/foundation/06_artifact_contract.md`, and
  `docs/foundation/15_system_overview.md` where they describe rich rendering,
  artifact resources, and the static preview path.
- Affected packages: `packages/static` for the MathJax adapter, static builder,
  page renderer, local support CSS/assets, and renderer diagnostics.
- Affected dependencies: Node and MathJax become renderer dependencies for
  Glintstone, not course runtime dependencies.
- Affected fixtures and tests: representative math/image/link/code/layout
  fixtures, invalid math fixtures, contract tests, static-read-path tests, and
  Chromium checks for visible typesetting and no external renderer asset
  requests.
- Affected documentation: separate English and Spanish role guides for
  contributors/collaborators, professors, students, and agents, plus
  `AGENTS.md`, `README.md` if workflow commands change, and
  `openspec/config.yaml` proposal guidance.
- Static/dynamic boundary: the change preserves the static-only course path.
  Browser-only MathJax, backend rendering, personal study state, official study
  UI, and course-code execution remain out of scope.
