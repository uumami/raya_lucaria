## Why

Raya Lucaria needs a compact authoring contract that lets professors and agents keep course content visibly ordered in source while Glintstone generates clean navigation, stable links, local indexes, and master indexes for students. This fills a foundation gap in `docs/foundation/05_course_contract.md`, `docs/foundation/06_artifact_contract.md`, and `docs/foundation/03_pedagogy.md`: directories and pages are learning quanta, but the reset has not yet defined the source-order, metadata, index, and stable-reference rules that make those quanta usable at scale.

## What Changes

- Define convention-first ordered content under `content/` using visible numeric prefixes, section landing pages, appendix prefixes, natural sorting, and strict validation.
- Define a small YAML frontmatter baseline for rendered pages and section indexes: stable `id`, title fields, summary, status, estimated time, tags, prerequisites, and aliases.
- Add stable `raya:<id>` links that resolve during validation/build independently of order prefixes or file moves.
- Require generated local indexes and master indexes in the rendered artifact while keeping generated sections out of source files.
- Add generated navigation/index data surfaces that Glintstone and future domains can read from artifact data rather than scraping rendered HTML.
- Keep explicit outline files, graph UI, search, glossary extraction, personal progress, and spaced repetition behavior out of this baseline; they remain future growth once source order and generated indexes are stable.
- Salvage the legacy principle that navigation can come from directory structure, while rejecting legacy renderer stacks, old generated JSON shapes, and hidden frontmatter `order` as the baseline ordering model.

## Capabilities

### New Capabilities
- `content-order-index-baseline`: Defines ordered source naming, index-page conventions, appendix ordering, page metadata, stable `raya:` references, generated index behavior, and validation expectations.

### Modified Capabilities
- `course-source-contract`: Adds source-level ordered content, section landing, frontmatter metadata, stable ID, and stable reference requirements.
- `artifact-contract-baseline`: Adds navigation and index data as generated artifact indexes that remain rebuildable from source truth.
- `minimal-static-builder`: Requires Glintstone to render generated local/master index sections and resolve stable `raya:` links in the static read path.
- `source-link-asset-validation`: Adds validation behavior for stable `raya:` content links alongside existing local Markdown and asset validation.
- `course-init-command`: Updates initialized source courses to scaffold the blessed ordered source/index shape without defining canonical pedagogy by accident.
- `dev-workflow-baseline`: Requires role documentation and focused tests when source-order, generated index, and static navigation contracts change.

## Impact

- Affected docs: `docs/foundation/05_course_contract.md`, `docs/foundation/06_artifact_contract.md`, `docs/foundation/15_system_overview.md`, role guides under `docs/guides/en/` and `docs/guides/es/`.
- Affected contracts: source schema/validation, artifact manifest/data indexes, static builder rendering, source link validation, course init fixtures, and e2e/static-read-path tests.
- Affected generated outputs: `site/` pages plus manifest-declared data such as `navigation.json`, `indices.json`, `pages.json`, `quanta.json`, and `links.json`.
- No new runtime backend, JavaScript framework, hosted service, or dynamic study state is introduced.
