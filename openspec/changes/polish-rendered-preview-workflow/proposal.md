## Why

The static renderer now has enough capability that manual review is harder than it should be: generated pages, fixture artifacts, inspection pages, and docs can be opened, but there is no accepted preview workflow or visual-quality contract for deciding whether the student-default page is actually readable.

This change makes the next layer explicit before adding more Rennala pedagogy: Glintstone should provide a quiet, static-first preview path and screenshot/e2e checks so future cards, quizzes, prompts, and reviewed outputs grow into a stable reading experience instead of a noisy fixture dump.

## What Changes

- Add a `raya preview <course>` workflow that validates/builds a course and serves its `artifact/site/` directory through local static hosting without executing code, notebooks, kernels, Docker services, cache refreshes, or output freezing.
- Make the preview command optionally open or print deployment-neutral links for the default entrypoint, `_raya/inspect/`, and repository examples/gallery where applicable.
- Polish default Glintstone pages so the first view emphasizes authored content, navigation, local indexes, compact support panels, and clear resource/status labels without instructional clutter.
- Improve examples/gallery into a useful fixture review surface with concise fixture labels, links to entrypoints and inspection pages, and no claim that fixture content is canonical pedagogy.
- Add screenshot or visual e2e checks for representative default pages, gallery pages, and inspection pages across desktop and mobile-sized viewports.
- Preserve complete artifact data in `manifest.json`, `data/*.json`, copied files, and inspection pages; do not make rendered HTML the machine authority.
- Update foundation docs, rendered docs, role guides, `AGENTS.md`, and `openspec/config.yaml` only where the preview/review workflow changes contributor, professor, student, or agent behavior.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `cli-contract-baseline`: Add the static `raya preview` command contract and no-execution guarantees.
- `minimal-static-builder`: Tighten student-default page polish and examples/gallery output expectations.
- `rendered-surface-discipline`: Clarify visual/readability expectations for student-default, support-panel, inspection, and machine-only surfaces.
- `dev-workflow-baseline`: Require screenshot/visual e2e coverage and documented preview verification when rendered UX changes.

## Impact

- Affected packages: `packages/cli` for the preview command, `packages/static` for page/gallery polish, and tests under `tests/contracts` and `tests/e2e`.
- Affected artifacts: generated `artifact/site/` pages, `_raya/inspect/`, examples/gallery, and static preview URLs.
- Affected documentation: foundation rendering/artifact/system docs, rendered docs, role guides in English and Spanish, `AGENTS.md`, and OpenSpec config guidance.
- Static/dynamic boundary: preview remains a local static server over generated files. It must not introduce a backend app, account system, client-side router, runtime execution, Docker execution, notebook execution, cache refresh, or hosted dependency.
- Growth path: the preview workflow becomes the review gate for later Rennala study surfaces, richer visual components, and optional web deployment checks without changing the artifact authority model.
- Legacy assumptions rejected: preview is not a dynamic dev app, fixture pages are not course canon, and visual review must not depend on scraping hidden metadata from normal rendered HTML.
