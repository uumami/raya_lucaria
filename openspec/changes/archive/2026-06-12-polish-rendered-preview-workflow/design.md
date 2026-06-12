## Context

Glintstone now builds rich static pages, compact support panels, inspection pages, copied reference/reviewed files, generated indexes, and an examples/gallery surface. The artifact contract is solid, but the human review loop is still awkward: contributors need to know what to open, professors need to trust the student page, and agents need deterministic checks that page polish did not regress.

The existing static-read-path tests prove links resolve and data remains complete. This design adds the next layer: a local static preview command and visual checks for the surfaces people actually inspect before accepting more pedagogy features.

Relevant foundation anchors:

- `docs/foundation/06_artifact_contract.md`: artifact data is authority; rendered HTML is a view.
- `docs/foundation/15_system_overview.md`: static course path is the baseline.
- `docs/foundation/17_rendering_execution_plan.md`: rendering and execution advance in phases; preview must not execute code.

Stakeholders:

- students need quiet default pages,
- professors need quick local review of a course artifact,
- contributors need repeatable fixture/gallery preview,
- agents need stable commands and visual/e2e assertions.

## Goals / Non-Goals

**Goals:**

- Add `raya preview <course>` as a local static preview workflow over generated `artifact/site/`.
- Keep preview validation/build behavior explicit and non-executing.
- Improve default rendered page polish without changing artifact authority.
- Improve examples/gallery as a fixture review surface with links to entrypoints and inspection pages.
- Add screenshot or visual e2e checks for representative default, gallery, and inspection pages.
- Keep Docker plus `uv` compatibility documented and testable.
- Update role docs and rendered docs where preview changes actual workflows.

**Non-Goals:**

- No backend app, account system, client-side router, frontend framework, or hosted preview service.
- No browser execution of Python, notebooks, kernels, runtime profiles, Docker services, cache refreshes, or output freezing.
- No new pedagogy feature such as cards-on-page, quizzes, spaced repetition, mastery maps, or study state.
- No redesign of the whole theme beyond compact page hierarchy, spacing, and fixture review ergonomics.
- No change to source-course layout or artifact data schemas unless implementation reveals a small missing field for preview discovery.

## Decisions

### 1. Preview is a CLI wrapper over static files

`raya preview <course>` will validate and build the course, then serve the generated `artifact/site/` directory using a local static HTTP server. It prints the local URL, the artifact path, and inspection URL when present.

Rationale: contributors and professors get one command, but the served content remains the same files that static hosting will serve. Alternatives considered were a frontend dev server or a dynamic preview app; both would blur the static contract too early.

### 2. Preview does not execute anything except validation/build

Preview may run `raya validate` and `raya build` because build is already non-executing. It must not call `raya run`, `raya outputs freeze`, Docker execution, kernels, package installers, or cache refresh. If the user wants execution, they must use explicit target-scoped commands before preview.

Rationale: the page review loop must be safe for heavy notebooks and long training runs. This preserves the execution phase boundaries in the rendering plan.

### 3. Visual checks are test-only and static-read-path based

Use pytest-driven e2e tests with a local static server and screenshot or layout assertions for representative pages. The test should check visible hierarchy, absence of metadata leakage, no obvious text overlap, fixture labels, and link availability across desktop and mobile-sized viewports.

Rationale: static-read-path checks already exist; visual assertions extend them without creating a product UI. If adding a browser automation dependency is necessary, keep it as a dev/test dependency and document Docker compatibility.

### 4. Polish is contract-level only where it protects readability

The contract should require readable hierarchy and compact panels, not lock the project into a permanent visual theme. Page shell changes should be conservative: clearer nav, tighter metadata labels, predictable panel spacing, useful page landmarks, and no instructional clutter in the reading flow.

Rationale: this is a foundation framework, not a marketing site. Future Rennala study components need a quiet course surface to grow into.

### 5. Gallery remains fixture review, not pedagogy

The examples/gallery page should list representative fixture artifacts, what behavior each demonstrates, and links to the page and inspection surface. It should not teach course content, define architecture, or replace foundation docs.

Rationale: fixtures are essential for test review, but they must not become accidental canon.

## Risks / Trade-offs

- [Risk] Visual tests become brittle after harmless CSS changes. -> Mitigation: prefer page-level screenshots and targeted layout assertions over pixel-perfect comparisons unless a specific regression requires a strict snapshot.
- [Risk] Preview command is mistaken for a dynamic app. -> Mitigation: print static artifact paths and document that preview serves generated files only.
- [Risk] Preview rebuild surprises users who expected to inspect an existing artifact. -> Mitigation: support an explicit no-build or artifact-preview mode if implementation shows a need, but keep the first contract simple.
- [Risk] Adding browser automation slows tests. -> Mitigation: keep browser checks focused on representative fixtures and run them in the e2e group.
- [Risk] Page polish hides useful professor details. -> Mitigation: keep compact status visible and link inspection surfaces for audit details.

## Migration Plan

- Existing `raya build` and `raya artifacts inspect` behavior remains unchanged.
- Add preview as an additional command; no existing command is removed.
- Existing gallery links may be refined in place.
- Existing tests continue to pass; new e2e/visual tests cover the preview surfaces.
- Rollback is straightforward: remove the preview command and gallery/page polish changes while keeping generated artifact data unchanged.

## Open Questions

- Should `raya preview` default to rebuilding every time, or should it accept `--no-build` in the first implementation?
- Should examples/gallery be hand-authored static HTML for now, or generated by a small repo command later?
- Which browser automation package best fits the Docker/uv workflow if screenshots require a real browser dependency?
