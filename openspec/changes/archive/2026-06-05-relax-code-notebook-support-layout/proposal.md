## Why

The current Phase 2 code/notebook contract is safe but too Raya-specific for authors: it forces `.py` files under `code/` and `.ipynb` files under `notebooks/`, even when colocating executable material beside a lesson would be clearer. This change keeps Glintstone static-first and ownership-bounded while making normal authoring easier: linked source files are classified by extension, not by mandatory support directory names.

## What Changes

- **BREAKING**: `code/` and `notebooks/` stop being required or reserved source support roots for `.py` and `.ipynb` references.
- Classify linked `.py` files as code references and linked `.ipynb` files as notebook references by extension, regardless of ordinary folder name.
- Preserve the ownership boundary: rendered pages may reference support files owned by their own learning quantum or an accepted ancestor, but not sibling or unrelated quanta.
- Keep `_official/`, `_reviewed/`, `_assets/`, `_drafts/`, `drafts/`, `_partials/`, runtime support, and path escapes private for code/notebook references unless a future accepted contract opens a specific path.
- Copy only validated, linked `.py` and `.ipynb` files into `artifact/files/` and `artifact/site/_raya/files/`; do not auto-publish every script or notebook found under `course/`.
- Preserve static no-execution behavior for validation, build, artifact inspection, static serving, reference previews, and rendered documentation.
- Update examples, fixtures, foundation docs, rendered docs, role guides, `AGENTS.md`, and OpenSpec config guidance so future proposals use extension-based linked support rather than special `code/` and `notebooks/` roots.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `course-source-contract`: remove `code/` and `notebooks/` as special private support directories and define `.py`/`.ipynb` source support by linked extension and learning-quantum ownership.
- `source-link-asset-validation`: validate code/notebook references by extension and ownership boundary instead of required support-root names.
- `code-notebook-references`: update the Phase 2 reference contract, artifact exposure, and static rendering examples to use extension-classified linked support files.
- `dev-workflow-baseline`: require representative fixture, invalid fixture, e2e/static-read-path, and documentation verification for the relaxed reference layout.

## Impact

- Affected code: `packages/schema` reference validation and source-tree classification, `packages/static` reference copying/rendering, `packages/cli` commands that report or execute validated reference targets, and tests/fixtures under `examples/courses/`.
- Affected docs: `docs/foundation/17_rendering_execution_plan.md`, relevant course/source foundation guidance, rendered docs under `docs/`, English and Spanish role guides, `AGENTS.md`, and `openspec/config.yaml`.
- Affected artifacts: `data/references.json`, `artifact/files/`, `artifact/site/_raya/files/`, and generated static reference panels keep their current purpose and shape while recording actual course-root-relative target paths.
- Non-goals: executing code or notebooks during build, introducing browser execution, defining shared cross-quantum support libraries, treating `.py` or `.ipynb` files as rendered pages, or changing runtime/cache/reviewed-output semantics beyond compatibility with the new source paths.
