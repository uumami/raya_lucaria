## 1. Preconditions And Tests

- [x] 1.1 Confirm `define-reviewed-execution-output-baseline` has been archived/synced before changing reviewed-output display behavior, or explicitly limit reviewed-output work until that baseline is current.
- [x] 1.2 Add contract tests proving default rendered pages show authored content, navigation, generated indexes, compact resource/status labels, and deployment-neutral links.
- [x] 1.3 Add contract tests proving default rendered pages do not dump raw JSON, source hashes, cache keys, artifact storage paths, browser storage paths, or verbose runtime/execution internals into the main reading flow.
- [x] 1.4 Add contract tests proving manifest-declared artifact data remains complete when default pages hide verbose internals.
- [x] 1.5 Add or extend static-read-path/e2e tests for default pages, compact panels, inspection/gallery links, referenced files, reviewed files, and no backend assumptions.

## 2. Rendered Surface Implementation

- [x] 2.1 Define the minimal surface-tier vocabulary in the static builder or shared rendering helpers: student-default, support-panel, inspection, and machine-only.
- [x] 2.2 Update the default page shell so ordinary pages prioritize authored content, breadcrumbs, navigation, generated indexes, local assets, and compact support panels.
- [x] 2.3 Update code/notebook reference panels to show compact kind, label, no-execution status, and view/download links without raw artifact metadata in the main flow.
- [x] 2.4 Update runtime, execution, cache, and reviewed-output page summaries so only reader-relevant status appears by default and verbose internals stay in artifact data or inspection surfaces.
- [x] 2.5 Add static inspection output when needed to expose detailed metadata from manifest-declared data without scraping rendered HTML.
- [x] 2.6 Preserve no-execution guarantees for validation, build, artifact inspection, static serving, default pages, inspection pages, and copied file links.

## 3. Examples And Gallery

- [x] 3.1 Add a static examples/gallery surface or equivalent preview artifact that links to representative fixture `artifact/site/` entrypoints.
- [x] 3.2 Label each gallery entry as fixture material and name the behavior it demonstrates, such as minimal course, ordered navigation, rich rendering, references, runtime metadata, or reviewed outputs.
- [x] 3.3 Ensure gallery links use deployment-neutral static paths and work when served from a local static server rooted at the repository or gallery artifact.
- [x] 3.4 Adjust representative fixture rendered content only as needed to exercise compact panels and inspection surfaces without turning examples into canonical pedagogy.

## 4. Documentation And Guidance

- [x] 4.1 Update `docs/foundation/06_artifact_contract.md`, `docs/foundation/15_system_overview.md`, `docs/foundation/16_documentation_surfaces.md`, and `docs/foundation/17_rendering_execution_plan.md` as needed to describe rendered-surface discipline compactly.
- [x] 4.2 Update rendered documentation source under `docs/` so the accepted display model is available through the docs static read path.
- [x] 4.3 Update separate English and Spanish role guide pages for contributors/collaborators, professors, students, and agents.
- [x] 4.4 Update `AGENTS.md` with guidance that normal pages should stay focused and verbose internals belong in manifest data or inspection surfaces.
- [x] 4.5 Update `openspec/config.yaml` so future proposals inherit rendered-surface discipline and examples/gallery expectations.

## 5. Verification

- [x] 5.1 Run the full Python test suite through the available local or Docker workflow.
- [x] 5.2 Build representative fixtures, including minimal, ordered, render, reference, runtime, execution/reviewed-output, and the examples/gallery surface.
- [x] 5.3 Run artifact inspection for generated representative artifacts and confirm manifest-declared data remains complete.
- [x] 5.4 Run static-read-path/e2e coverage for default pages, compact panels, inspection/gallery pages, referenced files, reviewed files, and deployment-neutral links.
- [x] 5.5 Run `raya validate docs` and build or e2e-check rendered documentation if docs rendering is touched.
- [x] 5.6 Run `openspec validate define-rendered-surface-discipline --strict`, `openspec validate --specs --strict`, and `git diff --check`.
