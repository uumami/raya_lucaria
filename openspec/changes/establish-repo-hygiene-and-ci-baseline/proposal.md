## Why

The foundation, static renderer, explicit execution, reviewed outputs, and rendered-surface discipline now work, but the repository still lacks a single accepted hygiene and CI gate. Current contributors and agents must copy long command lists, and stale current guidance can survive after specs change.

This change makes cleanliness enforceable before more preview or pedagogy work: canonical checks, CI, generated-output ignore rules, stale-reference scans, and a known-missing-work inventory.

## What Changes

- Add canonical host and Docker verification scripts.
- Add CI that calls repository scripts instead of duplicating command lists.
- Add hygiene scans for stale current guidance, generated-output pollution, OpenSpec incomplete markers, fixture labeling, and command/source-layout drift.
- Clean current README, AGENTS, foundation docs, role guides, and OpenSpec config so they agree on commands and source layout.
- Add a known-missing-work document for deferred features and intentional gaps.
- Keep archived OpenSpec changes as history and leave the parked preview proposal out of implementation scope.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `dev-workflow-baseline`: Add canonical hygiene, local, Docker, and CI verification requirements.
- `documentation-surface-baseline`: Add known-missing-work and current-doc consistency requirements.

## Impact

- Affected scripts: `scripts/check.sh`, `scripts/check-python.sh`, `scripts/check-hygiene.sh`, `scripts/check-docker.sh`.
- Affected CI: `.github/workflows/check.yml`.
- Affected docs: `README.md`, `AGENTS.md`, foundation docs, rendered docs, English/Spanish contributor and agent guides, and `openspec/config.yaml`.
- Affected tests: contract tests for the new scripts and hygiene behavior.
- Out of scope: `raya preview`, visual e2e, rendered UX polish, cards, quizzes, spaced repetition, graph UI, identity, and dynamic services.
