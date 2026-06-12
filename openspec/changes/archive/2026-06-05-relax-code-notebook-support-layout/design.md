## Context

Phase 2 currently treats referenced scripts and notebooks as source support only when they live under `code/` or `notebooks/` directories owned by a learning quantum or accepted ancestor. That was conservative and testable, but it makes authors learn a Raya-specific file layout before they can write ordinary lessons that link to nearby scripts or notebooks.

The implementation already separates rendered Markdown pages, private support paths, generated artifacts, runtime metadata, local execution, and reviewed output. This design keeps those boundaries and changes only how Glintstone discovers valid code/notebook references: from directory-name classification to linked-extension classification.

## Goals / Non-Goals

**Goals:**

- Allow rendered Markdown pages to link to `.py` and `.ipynb` files anywhere under the authored `course/` tree when the target is owned by the page's learning quantum or an accepted ancestor.
- Make `code/` and `notebooks/` ordinary optional author folder names instead of reserved or required support roots.
- Preserve private support boundaries for `_official/`, `_reviewed/`, `_assets/`, `_drafts/`, `drafts/`, `_partials/`, runtime paths, and path escapes.
- Preserve static-first behavior: validation, build, artifact inspection, static serving, and rendered previews never execute code, notebooks, kernels, `uv`, Docker, package installers, or cache refreshes.
- Keep generated artifact surfaces stable: reference metadata remains machine authority, copied files remain deployment-neutral, and execution/reviewed-output code reads validated reference records.

**Non-Goals:**

- Auto-discovering or publishing every `.py` or `.ipynb` file in a course.
- Turning `.py` or `.ipynb` files into navigation pages or generated index entries.
- Defining shared cross-quantum libraries or cross-course source reuse.
- Adding browser execution, Pyodide, JupyterLite, marimo, remote runners, or backend services.
- Changing runtime profile, cache, local execution, or reviewed-output policies except to accept the actual validated source paths.

## Decisions

### 1. Classify references by linked extension

Glintstone SHALL inspect local Markdown links and classify existing `.py` targets as code references and existing `.ipynb` targets as notebook references. The folder name does not decide the kind.

Alternatives considered:

- Keep mandatory `code/` and `notebooks/`: safest but too framework-specific and less natural for course authors.
- Add a new frontmatter list of executable files: explicit but more work for authors and easy to let drift from Markdown.
- Auto-scan all scripts/notebooks: convenient but publishes accidental files and weakens future execution trust.

### 2. Public exposure requires a validated Markdown link

A `.py` or `.ipynb` file under `course/` is source support, not a public artifact, until a rendered Markdown page links to it and validation accepts the link. Unlinked files remain source files and MUST NOT be copied into `artifact/files/`, `artifact/site/_raya/files/`, or `data/references.json`.

This preserves author privacy, avoids accidental publication, and keeps the Markdown page as the human-readable explanation for why the file matters.

### 3. Ownership is path-based and quantum-bounded

Reference ownership is resolved from the ordered source tree:

- A directory quantum is represented by its normalized zero index page, such as `0_index.md`.
- A rendered page may reference `.py` or `.ipynb` files under its own quantum directory or under an accepted ancestor quantum directory.
- A target under a sibling or descendant quantum owned by another rendered page is invalid unless a future shared-support contract accepts that boundary.
- A plain support subdirectory that contains no rendered Markdown is owned by the nearest ancestor quantum.

This gives authors natural folders such as `helpers/`, `scripts/`, `labs/`, `notebooks/`, or `code/` without making any folder name special. If authors need page-private support without ambiguity, they should use a directory quantum with its own `0_index.md`.

### 4. Private support paths remain blocked for code/notebook references

The reference resolver MUST reject `.py` and `.ipynb` targets under private source paths: `_official/`, `_reviewed/`, `_assets/`, `_drafts/`, `drafts/`, `_partials/`, runtime support paths, and any path outside the authored source root. `_assets/` remains for opaque assets; `_official/` remains for pedagogical objects; `_reviewed/` remains reviewed output support.

### 5. Artifact and execution contracts read the same reference metadata

The generated `data/references.json` record keeps the current fields and records the actual course-root-relative source path. `raya run`, runtime/cache metadata, reviewed output validation, artifact inspection, and static reference panels continue to read manifest-declared reference data instead of scraping HTML or assuming folder names.

### 6. Documentation and fixtures change with the contract

The foundation plan, rendered docs, role guides, `AGENTS.md`, and `openspec/config.yaml` need compact updates because this is author-facing behavior. Fixtures should show colocated/natural folder examples and keep `code/` or `notebooks/` only as optional examples, not required structure.

## Risks / Trade-offs

- Ambiguous same-directory ownership when many file pages share a parent → Use the nearest directory quantum as the support owner and recommend directory quanta for page-private support.
- Authors may assume unlinked scripts are published → Tests and docs must state that only validated Markdown links expose support files.
- Removing `code/` and `notebooks/` privacy may allow authored Markdown under those folders to render if ordered correctly → This is intentional; folder names are ordinary. Validation still blocks unordered published Markdown according to the ordered content contract.
- More flexible paths increase path-boundary complexity → Keep invalid fixture coverage for private paths, sibling quanta, malformed notebooks, missing targets, and path escapes.
- Existing fixture paths change → This is acceptable before external adoption; migration is to keep existing links or move files naturally while preserving Markdown links and runtime target paths.

## Migration Plan

1. Update specs and foundation docs to state extension-based linked support as the current Phase 2 baseline.
2. Update schema/source validation to remove `code` and `notebooks` from private directory sets and from required support-root checks.
3. Update reference resolution, static build copying, reference panels, CLI target resolution, and runtime/reviewed-output compatibility tests to use actual validated source paths.
4. Update fixtures and examples so at least one valid script and one valid notebook live outside mandatory `code/` and `notebooks` roots.
5. Keep backward-compatible examples where existing `code/` and `notebooks/` links still validate as ordinary folders.

Rollback is to restore support-root validation and fixture paths. No artifact migration is required because generated artifacts are rebuildable.

## Open Questions

- Shared support libraries across quanta remain intentionally deferred. A future proposal should decide whether that belongs in a named shared source area, runtime package, or explicit reference-export contract.
