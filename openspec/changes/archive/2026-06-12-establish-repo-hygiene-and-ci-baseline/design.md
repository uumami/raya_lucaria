## Context

Raya Lucaria now has accepted foundation contracts for the static course path, rendered surfaces, explicit local execution, reviewed outputs, artifact inspection, Docker plus `uv`, and role documentation. The remaining workflow gap is operational: contributors and agents still have to copy long command lists, and stale current guidance can survive after source-layout or workflow specs move.

The existing Superpowers hygiene design identified the right boundary: make repository verification canonical and enforceable before reopening preview or pedagogy implementation. The active `polish-rendered-preview-workflow` proposal is parked and remains outside this implementation cycle.

## Goals / Non-Goals

**Goals:**

- Provide one canonical host verification entrypoint: `./scripts/check.sh`.
- Provide one canonical Docker verification entrypoint: `./scripts/check-docker.sh`.
- Keep Python/Raya validation, builds, tests, and artifact inspection in `./scripts/check-python.sh`.
- Keep repository cleanliness scans in `./scripts/check-hygiene.sh`.
- Make CI call repository scripts instead of duplicating command lists.
- Keep current docs, role guides, and OpenSpec config aligned on command and source-layout guidance.
- Document known missing work without turning deferred features into current requirements.

**Non-Goals:**

- Do not implement `raya preview` or the parked preview proposal.
- Do not add visual e2e, rendered UX polish, cards, quizzes, spaced repetition, graph UI, identity, or dynamic services.
- Do not rewrite archived OpenSpec changes for wording cleanup; they remain historical records.

## Decisions

### Canonical Check Scripts

The host full check is `./scripts/check.sh`. It should compose whitespace checks, hygiene scans, strict OpenSpec validation, and the Python/Raya verification path so humans and agents have one archive-ready command.

The Docker check is `./scripts/check-docker.sh`. It should exercise the Python/Raya verification path inside the reference `dev` service while keeping host-only checks in the host script where tools such as OpenSpec and Git state are already available.

Python/Raya work lives in `./scripts/check-python.sh`. That script owns dependency sync, tests, fixture validation/build/inspection, and docs validation/build/inspection. Keeping this separate allows both host and Docker workflows to share the expensive project verification without duplicating command lists.

Repository cleanliness scans live in `./scripts/check-hygiene.sh`. That script owns stale current-guidance scans, generated-output pollution checks, incomplete-marker checks, fixture labeling checks, and command/source-layout drift checks. These are repository policy checks, not package runtime behavior.

### CI Uses Repository Scripts

CI should install the accepted tools and call scripts from the repository. It should not expand the same long verification sequence inline in workflow YAML, because duplicated command lists are the drift problem this change is meant to solve.

### Historical And Parked Work

Archived OpenSpec changes are history and are not rewritten for wording cleanup. Hygiene scans and cleanup should target current docs, current specs, active proposal expectations, package source, scripts, fixtures, and config.

The parked `polish-rendered-preview-workflow` proposal remains active but out of implementation scope for this change. Any preview-specific work waits for a later task or proposal application.

## Risks / Trade-offs

- Full verification may become slow -> keep responsibilities split across scripts while preserving `./scripts/check.sh` as the canonical full gate.
- CI may drift if workflow YAML duplicates commands -> require CI to call repository scripts.
- Hygiene cleanup may expand into feature work -> keep known missing work as documentation only and leave deferred capabilities behind accepted proposals.
- Archive wording may look stale after cleanup -> preserve archives as historical truth and scan only current guidance surfaces.
