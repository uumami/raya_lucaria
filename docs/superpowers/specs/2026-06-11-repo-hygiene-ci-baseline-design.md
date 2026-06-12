# Repo Hygiene And CI Baseline Design

## Goal

Establish a cleanup and verification baseline that keeps the Raya Lucaria repository clean, ordered, verifiable, and hard to accidentally degrade before more rendered UX or pedagogy features are added.

## Context

The accepted foundation now includes course validation, static builds, rich rendering, code and notebook references, runtime metadata, explicit local execution, reviewed outputs, artifact inspection, rendered-surface discipline, Docker plus `uv` development, and English/Spanish role documentation.

The next useful step is not another feature. The repository needs a hygiene and CI pass that makes the current baseline easy for contributors and agents to verify. The pass should remove stale current guidance, prevent generated outputs and caches from polluting the worktree, unify commands, and document known gaps.

An active OpenSpec proposal named `polish-rendered-preview-workflow` exists, but it is parked for this cycle. It should not be implemented as part of hygiene work.

## Scope

This cycle should create an OpenSpec change, likely named `establish-repo-hygiene-and-ci-baseline`, and then implement it.

In scope:

- one canonical local verification command or script,
- one canonical Docker verification command or script,
- CI workflow that runs the accepted checks,
- cleanup of stale docs and stale references,
- cleanup or ignore handling for generated, cache, and local session files,
- consistency checks for OpenSpec, docs, examples, and config,
- a compact known-missing-work or deferred-work document,
- updated contributor and agent guidance that points to the same canonical commands.

Out of scope:

- `raya preview`,
- visual UX polish,
- rendered gallery redesign,
- student-facing card, quiz, prompt, or spaced repetition surfaces,
- new pedagogy features,
- broad package refactors unrelated to hygiene,
- changing accepted source-course or artifact contracts except to correct stale documentation.

## Truth Surfaces

The cleanup should keep four surfaces distinct.

Source truth:

- `docs/foundation/`,
- current OpenSpec specs,
- package source under `packages/`,
- explicitly labeled examples and fixtures.

Generated output:

- `artifact/`,
- `site/`,
- `__pycache__/`,
- `.pytest_cache/`,
- `.superpowers/`,
- build, test, and cache directories.

Historical archive:

- archived OpenSpec changes,
- Git history,
- old branches when intentionally consulted.

Deferred work:

- active but unapplied proposals,
- known missing features,
- intentional gaps.

Generated output must not become source truth. Archived changes and old branches may be mined for principles, but current docs/specs must not preserve stale behavior merely because it existed historically.

## Required Checks

The hygiene baseline should make these checks canonical:

- strict OpenSpec validation,
- local Python tests,
- Docker-based tests or smoke workflow,
- representative fixture validation/build/inspection,
- docs validation/build when docs are touched,
- stale current-doc guidance scan,
- OpenSpec placeholder scan,
- generated-output cleanliness scan,
- fixture labeling scan,
- README, `AGENTS.md`, and `openspec/config.yaml` command/source-layout consistency scan.

The exact command surface can be implemented as one `scripts/check.sh` with focused helper scripts if that keeps responsibilities clearer. CI should call the same script instead of duplicating the command list.

## Implementation Shape

Add a canonical local check script such as `scripts/check.sh`. It should be safe to run from the repository root and should fail fast with clear command names. If the full check is too expensive for every edit, add a clear quick/full split, but keep the full command canonical.

Add or document the Docker equivalent, preferably:

```bash
docker compose run --rm dev ./scripts/check.sh
```

Add a CI workflow that runs the canonical check through the repository's accepted Python, `uv`, and Docker assumptions where practical. If CI cannot run Docker-in-Docker, document that gap and run the local-equivalent check in CI.

Update `.gitignore` so local generated outputs, caches, and Superpowers brainstorming sessions do not appear as source changes.

Update README, `AGENTS.md`, role docs, and `openspec/config.yaml` so future contributors and agents share one command vocabulary and one cleanup standard.

Add a compact missing-work document in the docs tree. It should list intentional gaps such as preview workflow, visual e2e, student study surfaces, graph UI, identity, collaboration, and dynamic study state without turning them into current requirements.

## Success Criteria

This cycle is complete when:

- the hygiene/CI OpenSpec change is proposed, applied, and archived,
- `scripts/check.sh` or equivalent canonical command passes locally,
- the documented Docker verification path passes or has a documented unavoidable gap,
- CI configuration runs the canonical check set,
- stale current guidance is cleaned or explicitly marked historical,
- generated/cache/session files are ignored and not left as untracked source,
- known missing work is documented,
- `openspec validate --specs --strict` passes,
- the full test suite passes.

## Risks And Mitigations

Risk: the check script becomes too slow for everyday work.

Mitigation: provide a quick/full split only if needed, but keep the full check as the archive/CI gate.

Risk: cleanup accidentally rewrites historical archive content.

Mitigation: do not edit archived OpenSpec changes just to modernize wording; current guidance lives in active docs, specs, and config.

Risk: CI duplicates local logic and drifts.

Mitigation: CI should call scripts from the repo wherever possible.

Risk: the parked preview proposal creates ambiguity.

Mitigation: leave it active but clearly out of scope for hygiene, or explicitly decide to archive/delete it before implementation if the active-change state becomes operationally confusing.

Risk: "perfect" cleanup expands without bound.

Mitigation: focus on enforceable hygiene rules, current stale guidance, canonical checks, and documented deferred work. Do not refactor packages or implement future features unless a hygiene check proves a specific change is necessary.
