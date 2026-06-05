## 1. Renderer Foundation

- [x] 1.1 Select parser, syntax highlighting, math, and sanitization libraries that keep Glintstone as the renderer boundary and do not make Quarto core.
- [x] 1.2 Add required renderer dependencies to the static package and Docker/uv lock workflow.
- [x] 1.3 Refactor the current ad hoc Markdown renderer into a parser-backed rendering module with clear entry points for page body rendering and inline/link rewriting.
- [x] 1.4 Preserve existing Raya link and asset resolution for local Markdown links, `raya:<id>` links, ignored external links, fragments, and colocated `_assets/`.

## 2. Rich Static Rendering Features

- [x] 2.1 Render common Markdown block and inline structures including headings, paragraphs, unordered/ordered lists, blockquotes, thematic breaks, emphasis, strong text, inline code, and pipe tables.
- [x] 2.2 Render fenced code blocks with escaped code, language metadata, and syntax highlighting when supported while never executing code.
- [x] 2.3 Render inline and display math with preserved TeX source and local browser-facing support resources when needed.
- [x] 2.4 Render accepted callout syntax for note, tip, warning, and caution-style blocks.
- [x] 2.5 Render footnotes and add actionable diagnostics for missing footnote definitions.
- [x] 2.6 Generate page-local heading anchors with duplicate-safe IDs and render a generated page table of contents without treating anchors as durable course identity.
- [x] 2.7 Escape or sanitize raw HTML and unsafe markup so scripts and event handlers do not execute by default.

## 3. Artifact And Static Resource Integration

- [x] 3.1 Copy any rich-render browser support resources under `artifact/site/_raya/` and reference them with deployment-neutral relative URLs.
- [x] 3.2 Preserve artifact-level generated outputs and artifact inspection behavior when rich rendering adds support resources or data.
- [x] 3.3 Update manifest or artifact schemas only if rich rendering introduces manifest-declared support data.
- [x] 3.4 Ensure rich-rendered pages remain usable when `artifact/site/` is served directly or opened from local files.

## 4. Fixtures And Examples

- [x] 4.1 Add or extend a representative rich rendering course fixture with root and nested pages that cover headings, lists, links, code blocks, math, tables, callouts, footnotes, anchors, TOC, and local assets.
- [x] 4.2 Keep rich rendering fixture text labeled as fixture material and point it to `docs/foundation/` as the authority surface.
- [x] 4.3 Add invalid fixture coverage for unsafe raw HTML or missing footnotes if those conditions fail validation/build.
- [x] 4.4 Update documentation fixture and live documentation render content to include a compact rich-rendering example where appropriate.

## 5. Documentation And Guidance

- [x] 5.1 Update the relevant foundation docs, including `docs/foundation/17_rendering_execution_plan.md`, with the accepted Phase 1 rich static rendering baseline.
- [x] 5.2 Update English role guides for contributors/collaborators, professors, students, and agents when authoring or rendered behavior changes.
- [x] 5.3 Update Spanish role guides for colaboradores, profesores, estudiantes, and agentes with separated Spanish pages and English technical identifiers.
- [x] 5.4 Update README, AGENTS, or OpenSpec config only if rich rendering changes operational commands or future proposal guidance.

## 6. Contract And E2E Tests

- [x] 6.1 Add contract tests for generated HTML covering rich Markdown structures, code block rendering, math, tables, callouts, footnotes, heading anchors, page TOC, and unsafe markup handling.
- [x] 6.2 Add contract tests that prove stable links, local Markdown links, fragments, external links, and local assets still rewrite correctly inside rich-rendered content.
- [x] 6.3 Add artifact validation tests for any new render support resources or manifest-declared support data.
- [x] 6.4 Add static-read-path e2e tests that build the representative rich rendering fixture and fetch root/nested pages plus any `_raya/` support resources.
- [x] 6.5 Add rendered documentation tests or fixture assertions that prove live docs stay renderable after rich rendering changes.

## 7. Verification

- [x] 7.1 Run host validation and tests for schema, static builder, artifact inspection, documentation surfaces, and e2e coverage.
- [x] 7.2 Run `raya validate docs` and render/build documentation coverage affected by this change.
- [x] 7.3 Run the Docker Compose reference workflow for representative rich rendering tests or document any Docker workflow gap.
- [x] 7.4 Run `openspec validate define-rich-static-rendering-baseline --strict`.
- [x] 7.5 Run `openspec validate --specs --strict` before archive.
