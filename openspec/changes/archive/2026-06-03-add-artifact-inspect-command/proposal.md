## Why

The builder now produces portable artifacts, but there is no standalone command to inspect an artifact after it has been copied, served, or handed to a future service. Raya Lucaria needs a manifest-centered inspection command so humans, coding agents, and later dynamic domains can verify artifact integrity without rebuilding from source.

## What Changes

- Add `raya artifacts inspect <artifact>` as the first artifact inspection command.
- Inspect artifact directories through `manifest.json` rather than scraping rendered HTML.
- Validate required artifact directories, manifest fields, and manifest-declared data indexes.
- Report concrete files read, diagnostics, and next actions with stable zero/nonzero exits.
- Update smoke testing so temporary external course artifacts are built and inspected locally and through Docker.
- Keep artifact inspection read-only and independent of renderer, backend, identity, and deployment providers.

Minimum requirement: after `raya build <course>`, `raya artifacts inspect <artifact>` validates the generated artifact contract.

Growth path: future proposals can add machine-readable output, artifact summaries, graph checks, static link checks, search indexes, package export checks, and installation registration checks.

## Capabilities

### New Capabilities

- `artifact-inspection-command`: artifact inspection workflow for validating portable course artifacts from their manifest and generated data indexes.

### Modified Capabilities

- `cli-contract-baseline`: add `raya artifacts inspect <artifact>` as a nested CLI command with stable diagnostics and exits.
- `artifact-contract-baseline`: require artifact inspection to validate required paths and manifest-declared data indexes.

## Impact

- Updates `packages/schema` artifact helpers.
- Updates `packages/cli` command parsing and diagnostics.
- Adds tests for direct artifact inspection and CLI artifact inspection.
- Updates README, AGENTS, CLAUDE, and the external smoke test.
- Does not add a backend, deployment registry, renderer dependency, JavaScript UI, identity provider, or personal study state.
