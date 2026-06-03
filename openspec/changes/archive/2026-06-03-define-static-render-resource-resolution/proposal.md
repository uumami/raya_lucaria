## Why

Raya Lucaria's static path must work when a course artifact is opened locally, served from static hosting, copied away from its source course, or later registered with a dynamic installation. The current builder validates and copies local assets, but rendered HTML does not yet normalize asset URLs into a deployment-neutral browser path, leaving `artifact/site/` less self-contained than the foundation requires.

## What Changes

- Define a browser-facing static resource layout under `site/_raya/`.
- Rewrite valid local asset references in rendered HTML to relative URLs that target `site/_raya/assets/`.
- Copy source assets used by the static site into `site/_raya/assets/` while preserving the existing artifact-level `assets/` contract.
- Keep page-to-page links relative and deployment-neutral.
- Preserve `manifest.json` and artifact-level `data/*.json` as machine-readable and installation-readable artifact surfaces.
- Add a representative render/e2e fixture course with a framework overview page, nested pages, local assets, and link examples that are labeled as fixture material.
- Add contract tests and real e2e/static-read-path tests for nested pages, local asset href rewriting, copied static-site assets, artifact inspection, and browser/static portability.
- Explicitly leave math rendering, graph UI, backlinks, wikilinks, heading-anchor validation, external link policy, and interactive components for later proposals.

Minimum requirement: generated pages and local assets remain usable when `artifact/site/` is served as the static read path, without a backend, root URL, CDN, or client-side router.

Growth path: future Glintstone render capabilities such as math, syntax highlighting, component assets, public browser data, and optional graph UI can use the same `site/_raya/` resource boundary without changing course source or provider assumptions.

Testing path: this change should introduce a real e2e fixture and test surface, not only unit assertions. The fixture should exercise a course-like page about the Raya Lucaria framework itself so future renderer changes have stable content to build, serve, and inspect.

## Capabilities

### New Capabilities

- `static-render-resource-resolution`: browser-facing resource layout and deployment-neutral URL rules for generated static artifacts.

### Modified Capabilities

- `artifact-contract-baseline`: require the static read path to be self-contained for browser-facing local assets.
- `dev-workflow-baseline`: require rendered static-site changes to include representative e2e/static-read-path verification.
- `minimal-static-builder`: require the minimal Glintstone builder to copy and rewrite local asset references into the static read path.

## Impact

- Updates `packages/static` static builder rendering and asset-copy behavior.
- Adds or adjusts contract and e2e tests around asset href rewriting, nested page paths, generated artifact paths, browser/static serving, and artifact inspection.
- Adds a representative fixture course/page for renderer e2e tests, kept separate from the minimal fixture and labeled as fixture material.
- May update artifact contract documentation and root guidance to distinguish artifact-level machine data from browser-facing static resources.
- Updates OpenSpec guidance so future rendered-output changes include e2e/static-read-path tests.
- No new backend, JavaScript framework, CSS framework, hosted service, CDN, or dynamic study state is introduced.
