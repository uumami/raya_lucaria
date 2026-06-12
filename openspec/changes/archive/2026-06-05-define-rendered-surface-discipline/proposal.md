## Why

Glintstone now produces rich pages, generated indexes, code/notebook references, runtime metadata, local execution metadata, and reviewed-output surfaces, but normal rendered pages are starting to show too much internal machinery. We need a display contract before adding more pedagogical features so student reading stays focused while artifact data remains complete for professors, contributors, and agents.

## What Changes

- Define a rendered-surface discipline that separates student-default page content, compact support panels, optional inspection surfaces, and machine-only artifact data.
- Keep `manifest.json` and `data/*.json` complete as the authority for tools, agents, future dynamic services, and artifact inspection; rendered HTML remains a readable view, not the canonical data surface.
- Make normal static course pages show only the learning content, navigation, generated indexes, selected study cues, and compact resource/status summaries needed by students.
- Move verbose reference metadata, runtime/execution/cache details, reviewed-output freshness internals, raw hashes, copied-file paths, and diagnostic details out of default page flow unless they are explicitly useful as compact labels or links.
- Allow Glintstone to generate optional static inspection pages or developer surfaces from the same artifact data so professors, contributors, and agents can audit what was built without scraping normal student pages.
- Add an examples/gallery preview surface for repository fixtures so contributors can open rendered examples quickly and see what each fixture is meant to test.
- Preserve static-first behavior: no backend, accounts, client-side router, execution, kernels, Docker, `uv`, cache refresh, or hosted service is required to render or inspect these surfaces.
- Add contract and e2e checks proving static pages remain readable, internal machine data is not dumped into normal pages, inspection/gallery paths work through the static read path, and manifest-declared data remains complete.

## Capabilities

### New Capabilities

- `rendered-surface-discipline`: Defines student-default, support-panel, inspection, and machine-only rendered surface rules for Glintstone artifacts.

### Modified Capabilities

- `artifact-contract-baseline`: Clarify that artifact data may be complete while default rendered pages expose only the appropriate view of that data.
- `minimal-static-builder`: Require the builder to apply rendered-surface discipline to generated page shells, support panels, and optional inspection/gallery pages.
- `code-notebook-references`: Clarify that code/notebook reference data remains complete in artifact data while default rendered pages use compact resource summaries and links.
- `dev-workflow-baseline`: Require representative fixture/gallery and static-read-path verification when rendered-surface behavior changes.

## Impact

- Affected packages: `packages/static`, `packages/schema` if artifact data or validation labels need small schema support, and `packages/cli` only if a preview command is accepted during implementation.
- Affected artifacts: `artifact/site/`, optional static inspection/gallery pages under the static read path, `manifest.json`, and manifest-declared `data/*.json`.
- Affected examples: repository fixtures under `examples/courses/` should get a preview/gallery path and clearer fixture labels.
- Affected documentation: foundation rendering/artifact docs, rendered docs, `AGENTS.md`, `openspec/config.yaml`, and separate English/Spanish role guidance for contributors/collaborators, professors, students, and agents.
- Static/dynamic boundary: this change does not introduce dynamic services, authentication, browser execution, notebook execution, cache refresh, or personal study state.
- Legacy assumptions rejected: rendered HTML must not become the authority surface for agents or future services, and examples must not rely on raw internal metadata being visible in normal student pages.
