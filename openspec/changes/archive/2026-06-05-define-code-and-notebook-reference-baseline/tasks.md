## 1. Source Reference Model

- [x] 1.1 Add schema-layer reference data structures for code and notebook references.
- [x] 1.2 Classify local Markdown links to `.py` and `.ipynb` files separately from content links and assets.
- [x] 1.3 Treat `code/` and `notebooks/` as source support directories that do not render as pages or generated indexes.
- [x] 1.4 Enforce support-owner rules for `code/` and `notebooks/`, including normalized `0_index.md` owner pages.
- [x] 1.5 Decide and implement the Phase 2 boundary for own-only versus own-or-ancestor support references.

## 2. Validation And Diagnostics

- [x] 2.1 Validate existing `.py` references under accepted `code/` support roots.
- [x] 2.2 Validate existing readable `.ipynb` references under accepted `notebooks/` support roots.
- [x] 2.3 Add actionable diagnostics for missing code and notebook references.
- [x] 2.4 Add actionable diagnostics for unreadable or malformed notebooks.
- [x] 2.5 Block references to code or notebooks under private support paths or outside the authored source tree.
- [x] 2.6 Preserve external URL, `mailto:`, `tel:`, and fragment-only ignore behavior.

## 3. Artifact Contract And Data

- [x] 3.1 Define `references.json` schema or validator for code and notebook reference data.
- [x] 3.2 Add manifest declaration for reference data when references are generated.
- [x] 3.3 Add artifact-level `files/` output for copied code and notebook references.
- [x] 3.4 Add browser-facing `site/_raya/files/` output for copied code and notebook references.
- [x] 3.5 Record page ID, source path, kind, language or format, hash, artifact path, browser path, and no-execution status for each reference.
- [x] 3.6 Update artifact inspection to validate reference data and copied file existence.

## 4. Static Builder And Rendering

- [x] 4.1 Copy referenced code and notebook files to artifact-level and browser-facing generated file paths.
- [x] 4.2 Rewrite rendered Markdown links to referenced code and notebooks as deployment-neutral static URLs.
- [x] 4.3 Render a compact static reference panel or equivalent readable surface for pages with references.
- [x] 4.4 Render safe code source excerpts without executing scripts.
- [x] 4.5 Render safe notebook outlines or source-cell previews without executing cells or trusting outputs.
- [x] 4.6 Preserve existing page rendering, stable links, local content links, assets, generated indexes, and static read paths.

## 5. Fixtures And Examples

- [x] 5.1 Add a representative valid code/notebook reference fixture with root and nested pages.
- [x] 5.2 Include `.py`, `.ipynb`, and `_assets/` references in the valid fixture without defining pedagogy by accident.
- [x] 5.3 Add invalid fixture coverage for missing code references.
- [x] 5.4 Add invalid fixture coverage for missing or malformed notebook references.
- [x] 5.5 Add invalid fixture coverage for private, path-escaping, or cross-quantum support references according to the accepted boundary.
- [x] 5.6 Update live documentation render content with a compact Phase 2 reference example if needed.

## 6. Documentation And Guidance

- [x] 6.1 Update `docs/foundation/17_rendering_execution_plan.md` with the accepted Phase 2 baseline decisions.
- [x] 6.2 Update English role guides for contributors/collaborators, professors, students, and agents.
- [x] 6.3 Update Spanish role guides for colaboradores, profesores, estudiantes, and agentes with separated pages and English technical identifiers.
- [x] 6.4 Update README, AGENTS, or OpenSpec config only if operational commands or future proposal rules change.

## 7. Contract And E2E Tests

- [x] 7.1 Add contract tests for code reference validation and diagnostics.
- [x] 7.2 Add contract tests for notebook reference validation and diagnostics.
- [x] 7.3 Add contract tests for generated `references.json`, manifest declaration, and artifact inspection.
- [x] 7.4 Add contract tests for copied artifact files and browser-facing `_raya/files/` outputs.
- [x] 7.5 Add generated HTML tests for rewritten links, reference panels, previews, and no-execution messaging.
- [x] 7.6 Add e2e/static-read-path tests that serve pages and fetch copied code/notebook files from `artifact/site/`.
- [x] 7.7 Add rendered documentation tests or assertions that live docs stay renderable after the reference changes.

## 8. Verification

- [x] 8.1 Run host validation and tests for schema, static builder, artifact inspection, documentation surfaces, and e2e coverage.
- [x] 8.2 Run `raya validate docs` and build/render documentation coverage affected by this change.
- [x] 8.3 Run the Docker Compose reference workflow for representative code/notebook reference tests or document any Docker workflow gap.
- [x] 8.4 Run `openspec validate define-code-and-notebook-reference-baseline --strict`.
- [x] 8.5 Run `openspec validate --specs --strict` before archive.
