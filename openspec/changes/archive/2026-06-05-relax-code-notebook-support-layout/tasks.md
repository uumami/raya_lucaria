## 1. Contract Tests And Fixtures

- [x] 1.1 Add valid reference tests for a rendered page linking to `.py` and `.ipynb` files in ordinary colocated folders outside mandatory `code/` and `notebooks/` roots.
- [x] 1.2 Add valid reference tests proving `code/` and `notebooks/` still work as ordinary folder names when the ownership boundary is satisfied.
- [x] 1.3 Add ownership-boundary tests for own quantum, accepted ancestor quantum, sibling quantum rejection, unrelated quantum rejection, and path escape rejection.
- [x] 1.4 Add private-path tests rejecting `.py` and `.ipynb` links under `_official/`, `_reviewed/`, `_assets/`, `_drafts/`, `drafts/`, `_partials/`, and runtime support paths.
- [x] 1.5 Add missing-target and malformed-notebook diagnostics tests with source page and target path details.
- [x] 1.6 Add unlinked support-file tests proving unlinked `.py` and `.ipynb` files are not copied or listed in `data/references.json`.
- [x] 1.7 Update the representative reference fixture and static-read-path/e2e coverage to include at least one script and one notebook referenced through extension-based links.

## 2. Schema And Validation

- [x] 2.1 Remove `code` and `notebooks` from reserved/private source support directory handling while preserving `_official/`, `_reviewed/`, `_assets/`, `_drafts/`, `drafts/`, `_partials/`, and runtime privacy.
- [x] 2.2 Implement extension-based reference classification for linked `.py` and `.ipynb` targets.
- [x] 2.3 Implement quantum ownership resolution for source support targets, including support-only ordinary directories owned by the nearest ancestor quantum.
- [x] 2.4 Update code/notebook reference diagnostics so failures explain missing files, malformed notebooks, private paths, ownership boundaries, or path escapes.
- [x] 2.5 Preserve static no-execution guarantees in validation for scripts, notebooks, runtime profiles, cache metadata, reviewed output, and previews.

## 3. Builder, Artifacts, And CLI Compatibility

- [x] 3.1 Update Glintstone reference copying so only validated linked `.py` and `.ipynb` files are copied into `artifact/files/` and `artifact/site/_raya/files/`.
- [x] 3.2 Update `data/references.json` generation to record actual course-root-relative source paths without assuming `code/` or `notebooks/`.
- [x] 3.3 Update static reference panels and previews to render deployment-neutral links for extension-classified references.
- [x] 3.4 Update artifact inspection to validate reference metadata and copied files for ordinary source paths.
- [x] 3.5 Update `raya run`, runtime/cache metadata, `raya outputs list`, and `raya outputs freeze` compatibility where they resolve validated reference targets by source path.

## 4. Documentation, Config, And Agent Guidance

- [x] 4.1 Update `docs/foundation/17_rendering_execution_plan.md` and any smaller relevant foundation course/source guidance to describe extension-based linked support as the Phase 2 baseline.
- [x] 4.2 Update rendered documentation under `docs/` so examples show natural colocated scripts/notebooks and make clear that only linked files are exposed.
- [x] 4.3 Update separate English and Spanish role guide pages for contributors/collaborators, professors, students, and agents, or explicitly track any deferred role-language page.
- [x] 4.4 Update `AGENTS.md` to remove mandatory `code/` and `notebooks/` support-root guidance.
- [x] 4.5 Update `openspec/config.yaml` so future proposals inherit extension-based linked support guidance rather than the old required-folder baseline.

## 5. Verification

- [x] 5.1 Run the full Python test suite through the available local or Docker workflow.
- [x] 5.2 Run `raya validate` and `raya build` for the reference fixture and any runtime/execution fixture touched by the path change.
- [x] 5.3 Run artifact inspection for the generated reference fixture artifact.
- [x] 5.4 Run the static-read-path/e2e coverage for reference panels, copied files, and deployment-neutral links.
- [x] 5.5 Run `openspec validate relax-code-notebook-support-layout --strict`, `openspec validate --specs --strict`, and `git diff --check`.
