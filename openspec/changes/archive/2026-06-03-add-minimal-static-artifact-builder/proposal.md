## Why

The baseline can validate source courses, but it cannot yet produce the portable course artifact promised by the foundation. Raya Lucaria needs the first Glintstone build loop now so `raya validate` can lead to a concrete `artifact/` with static pages, manifest data, and study seeds without choosing a rich renderer or web stack.

## What Changes

- Add a minimal Glintstone static builder under `packages/static`.
- Add `raya build <course>` as the first artifact-producing CLI command.
- Build `examples/courses/minimal` into the configured artifact output directory.
- Generate the required artifact shape: `site/`, `manifest.json`, `data/pages.json`, `data/quanta.json`, `data/links.json`, `data/official.json`, and `assets/`.
- Render readable, accessible, static HTML pages from Markdown content with simple navigation and internal links.
- Copy local course assets when present.
- Index official learning objects as static study seed data with official authority labels and learning-quantum scope.
- Validate the generated artifact contract in tests and development commands.
- Keep renderer, TypeScript/web UI, search, graph UI, backend services, identity, and personal study state out of scope.

Minimum requirement: `raya build examples/courses/minimal` creates a valid, backend-readable, static-useful artifact.

Growth path: future proposals can enrich Glintstone rendering, Primeval Current graph behavior, Rennala study queues, themes, search, and browser UI after the artifact surface is stable.

## Capabilities

### New Capabilities

- `minimal-static-builder`: Glintstone builder behavior for producing the first portable static artifact from a validated source course.

### Modified Capabilities

- `cli-contract-baseline`: add `raya build <course>` with stable diagnostics, output reporting, and nonzero failure behavior.
- `artifact-contract-baseline`: require the first builder output to satisfy the existing artifact shape with generated static pages, manifest, data indexes, and copied assets.

## Impact

- Adds `packages/static` and wires it into the `uv` workspace.
- Updates `packages/cli` to expose `raya build <course>`.
- Adds artifact generation tests and CLI build tests.
- Updates README, AGENTS, and CLAUDE command guidance.
- Does not introduce a JavaScript renderer, CSS framework, backend, database, auth provider, personal study state, or hosted service dependency.
