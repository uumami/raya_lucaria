## 1. Test And Fixture Baseline

- [x] 1.1 Add CLI contract tests for `raya preview --help`, `raya preview <course> --dry-run`, invalid course diagnostics, explicit host/port reporting, and no hidden global state.
- [x] 1.2 Add no-execution regression tests proving preview does not call `raya run`, `raya outputs freeze`, Docker execution, kernels, package installers, cache refreshes, scripts, or notebooks.
- [x] 1.3 Add static-read-path/e2e coverage for preview-served default pages, local assets, referenced files, reviewed files, and `_raya/inspect/index.html`.
- [x] 1.4 Add screenshot, browser-driven, or equivalent visual/layout checks for representative default pages, examples/gallery, and inspection pages at desktop and mobile-sized viewports.
- [x] 1.5 Ensure representative fixtures remain labeled as fixture material and do not become canonical pedagogy or architecture examples.

## 2. Preview CLI Implementation

- [x] 2.1 Add `raya preview <course>` parser support with explicit `--host`, `--port`, and `--dry-run` options.
- [x] 2.2 Implement preview planning that resolves the explicit course path, validates/builds through the existing non-executing build path, and discovers the generated `artifact/site/` entrypoint.
- [x] 2.3 Implement local static serving for `artifact/site/` with deployment-neutral URLs and clear startup output for the entrypoint, artifact path, and inspection page when present.
- [x] 2.4 Implement actionable failure diagnostics for validation, build, missing artifact/site, missing entrypoint, and host/port conflicts.
- [x] 2.5 Keep preview behavior portable through local `uv` and Docker Compose workflows without adding a backend app, frontend framework, client-side router, or hosted dependency.

## 3. Rendered Surface And Gallery Polish

- [x] 3.1 Audit current default pages, support panels, inspection pages, and examples/gallery for visible clutter, overlap risk, confusing labels, and metadata leakage.
- [x] 3.2 Refine Glintstone page shell HTML/CSS so authored content, navigation, generated indexes, and compact support panels have clear hierarchy on desktop and mobile-sized viewports.
- [x] 3.3 Refine support-panel labels and links so runtime, execution, reference, and reviewed-output status stays compact without hiding required reader trust cues.
- [x] 3.4 Update examples/gallery with concise fixture descriptions, entrypoint links, inspection links, and an authority notice that points to foundation docs and accepted specs.
- [x] 3.5 Preserve complete manifest-declared data and static inspection output while keeping verbose internals out of student-default page flow.

## 4. Documentation And Guidance

- [x] 4.1 Update foundation docs, especially artifact/rendering/system guidance, to describe the preview workflow and visual review boundary compactly.
- [x] 4.2 Update rendered documentation source under `docs/` so preview guidance is available through the docs static read path.
- [x] 4.3 Update separate English and Spanish role guide pages for contributors/collaborators, professors, students, and agents where preview changes their workflow.
- [x] 4.4 Update `AGENTS.md` with preview, visual-check, and no-execution guidance for future rendered-surface changes.
- [x] 4.5 Update `openspec/config.yaml` so future proposals inherit preview workflow and visual/e2e expectations.

## 5. Verification

- [x] 5.1 Run focused CLI, static-builder, preview, and visual/e2e tests added by this change.
- [x] 5.2 Run the full local Python test suite.
- [x] 5.3 Run Docker Compose test coverage or explicitly document any Docker/browser setup gap discovered during implementation.
- [x] 5.4 Build representative fixtures and docs, then inspect generated artifacts.
- [x] 5.5 Run `raya validate docs` and `raya build docs` if rendered docs are touched.
- [x] 5.6 Run `openspec validate polish-rendered-preview-workflow --strict`, `openspec validate --specs --strict`, and `git diff --check`.
