## 1. Renderer Dependency Baseline

- [ ] 1.1 Add failing dependency and Docker contract tests for renderer-owned Node 22 and `@mathjax/src` v4 support.
- [ ] 1.2 Add root `package.json` and `package-lock.json` for the renderer-only `@mathjax/src` v4 dependency.
- [ ] 1.3 Ignore local Node install output such as `node_modules/` and npm cache directories.
- [ ] 1.4 Add Node 22/npm to the Docker reference image without changing Python 3.10 and `uv` ownership.
- [ ] 1.5 Update canonical verification scripts to install renderer dependencies with `npm ci --ignore-scripts --no-audit --no-fund`.
- [ ] 1.6 Update canonical verification scripts to run `npm run raya-render-math -- --self-test` before Python/Raya tests that need build-time math.

## 2. MathJax Adapter Implementation

- [ ] 2.1 Create `packages/static/scripts/render_math.mjs` with a self-test and JSON stdin/stdout conversion contract.
- [ ] 2.2 Add focused tests for the Python math-renderer adapter before implementing it.
- [ ] 2.3 Create `packages/static/src/raya_static/math_renderer.py` with `MathItem`, `MathRenderResult`, subprocess invocation, CSS collection, and diagnostic mapping.
- [ ] 2.4 Prove inline and display math render to MathJax output and broken math produces actionable diagnostics naming the source file and expression context.
- [ ] 2.5 Configure MathJax with `base`, `ams`, and `newcommand` only, and add coverage that unknown macros or control sequences fail unless defined by supported page-local TeX macro syntax.

## 3. Static Renderer Integration

- [ ] 3.1 Update rich renderer tests so raw TeX spans fail and MathJax output is required.
- [ ] 3.2 Collect inline and display math tokens with stable per-page IDs and source paths before rendering the Markdown token stream.
- [ ] 3.3 Replace math tokens with `MathRenderer.render_many()` HTML output while keeping any fallback path diagnostic-backed.
- [ ] 3.4 Stop `raya build` before writing successful page output when math rendering diagnostics make the report fail.
- [ ] 3.5 Preserve existing link, asset, code block, table, callout, footnote, heading-anchor, and page table of contents behavior.

## 4. Artifact Resources And Static Read Path

- [ ] 4.1 Write MathJax support CSS and any required local render assets under `artifact/site/_raya/render/math/`.
- [ ] 4.2 Link local math support resources from root and nested pages with deployment-neutral relative URLs.
- [ ] 4.3 Ensure `raya preview` serves the same pre-rendered math pages and local resources that static hosting serves.
- [ ] 4.4 Add static-read-path tests proving generated math resources resolve without backend routes, CDNs, configured hosts, or browser-only rendering.

## 5. Fixtures And Diagnostics

- [ ] 5.1 Expand the representative render fixture or add a math fixture covering inline math, display math, matrices, aligned equations, cases, calculus, probability, statistics, optimization, page-local macros, images, links, code, callouts, tables, footnotes, and nested pages.
- [ ] 5.2 Keep all fixture content labeled as fixture material and point authority back to `docs/foundation/`.
- [ ] 5.3 Add invalid fixture coverage for MathJax conversion errors, malformed delimiters, unknown macros or control sequences, unsupported delimiter nesting, and missing local math support assets.
- [ ] 5.4 Add authoring-contract fixture coverage for inline `$...$`, display `$$` blocks on their own lines, fenced-code non-math, escaped dollar signs, page-local `\newcommand` and `\renewcommand`, and rejection of full LaTeX documents.
- [ ] 5.5 Verify diagnostics identify files read, expressions or spans involved, outputs withheld, failure reasons, and concrete next actions.

## 6. Browser And Layout Verification

- [ ] 6.1 Add Chromium or Playwright checks proving math is visibly typeset rather than merely preserved as raw TeX text.
- [ ] 6.2 Assert that generated pages request no external renderer assets during browser checks.
- [ ] 6.3 Add desktop and mobile viewport checks for math, code, images, tables, callouts, footnotes, generated indexes, support panels, and inspection links.
- [ ] 6.4 Run browser coverage through the Docker Compose reference workflow or document any required Docker setup change before archive.

## 7. Documentation And Guidance

- [ ] 7.1 Update `docs/foundation/17_rendering_execution_plan.md` and related artifact or CLI foundation docs for the accepted build-time math boundary.
- [ ] 7.2 Update author-facing rendered docs or documentation fixtures with accepted math delimiters, supported subset, macro rules, escaping guidance, unsupported notation, and diagnostics.
- [ ] 7.3 Update separate English and Spanish role guide pages for contributors/collaborators, professors, students, and agents.
- [ ] 7.4 Update `AGENTS.md`, `README.md` if commands change, and `openspec/config.yaml` so future renderer proposals inherit math and browser verification requirements.

## 8. Verification And Archive Readiness

- [ ] 8.1 Run focused contract tests for the MathJax adapter, static builder, diagnostics, artifact resources, and static read path.
- [ ] 8.2 Run the full local Python/Raya verification path, including `./scripts/check.sh`.
- [ ] 8.3 Run Docker verification through `./scripts/check-docker.sh` or document an explicit Docker/browser setup gap.
- [ ] 8.4 Validate and build representative fixtures and rendered docs touched by this change.
- [ ] 8.5 Run `openspec validate harden-static-renderer --strict`, `openspec validate --specs --strict`, and `git diff --check` before archive.
