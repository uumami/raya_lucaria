---
id: docs-guides-en-agents
title: Agents
summary: Guidance for coding and learning agents working through explicit files, commands, specs, and diagnostics.
status: ready
---
# Agents

Agents operate through explicit files, commands, OpenSpec specs, diagnostics, and authority boundaries. Agents inherit user authority and do not receive special trust.

Use `docs/foundation/13_truth_surfaces.md` for the authority map, accepted OpenSpec specs for testable contracts, and `AGENTS.md` for repository workflow.

OpenSpec remains available for future contract changes. When a user explicitly selects a Superpowers workflow, committed Superpowers design and plan documents may drive that loop, but `docs/foundation/` remains the highest source of seed truth and implementation must update the affected foundation, role, test, and contract surfaces.

Use the canonical check scripts from `README.md` and `AGENTS.md`: `./scripts/check.sh` for the host gate, `./scripts/check-docker.sh` for reference-container Python/Raya verification, and `./scripts/smoke-test.sh` for external-course portability checks. Run `./scripts/check.sh` and `./scripts/check-docker.sh` sequentially, not in parallel. Both prepare local Node/MathJax dependencies through `scripts/check-python.sh`, so the fail-fast repository lock reports when another Raya verification is already preparing dependencies. Wait for the active process to finish and rerun the blocked command. Avoid editing generated outputs, dependency folders, caches, or local session output. Keep deferred capabilities in `docs/foundation/18_known_missing_work.md` until an accepted OpenSpec change makes them current.

For course content, treat source files as canonical and generated artifacts as rebuildable. Preserve `source: course`, the ordered `course/` tree, frontmatter `id`, `raya:<id>` links, colocated `_official/` and `_assets/` privacy, generated index markers, and manifest-declared data surfaces. Do not edit generated `artifact/` output as source truth.

For rich static rendering, preserve the Glintstone boundary: rewrite links through Raya rules, generate page-local anchors and tables of contents from source headings, pre-render accepted MathJax math at build time, keep support files under `site/_raya/`, escape raw HTML, and do not execute code blocks. Test generated HTML, static read paths, browser-visible math, local math assets, no external renderer requests, and desktop/mobile overflow.

For copyable code blocks, inspect the rendered `.raya-code-block` markup, the local `shell.js` handler, and the copied `pre code` text. The copy control may use the Clipboard API or local fallback behavior, but it must not execute code, persist reader state, fetch data, or load external scripts.

For skin debugging, inspect surfaces in order: the selector in `raya.yaml` or
`_raya/skin.yaml`, the selected skin file, build diagnostics, generated
`_raya/render/skin.css`, the `skin.css` file name, the rendered
`data-raya-skin` page attribute, and the render-debug report. Do not infer
source authority from visual presentation or scraped HTML. When a skin issue
appears, first classify whether the source is a selector problem, a
profile-token problem, generated CSS output, or a rendered-page activation
problem. Do not infer skin state from screenshots alone; compare the source
selector, loaded profile, diagnostics, `skin.css`, `data-raya-skin`, and
render-debug report.

For the `OpenDyslexic` reader toggle, verify the generated static assets under
`_raya/render/accessibility/`, the local font file, the local toggle script,
and static parity between preview and copied deployment. Treat any external font
request as a regression; the toggle may use a local script, but it must not
introduce browser-side MathJax or an external renderer.

For the `Text size` reader toggle, verify the same local accessibility resource
path, `data-raya-text-size` on the document root, command-bar labels, computed
article text size, and reload persistence. Treat it as a local comfort
preference only; it must not change `data-raya-skin`, source content, graph
data, progress, answers, mastery, or recommendations.

For math authoring checks, use `examples/courses/render-fixture/course/2_math_authoring/0_index.md` as the focused source fixture. Verify source pages rather than generated `artifact/` files, and use render-debug evidence to confirm there is no raw visible TeX, no browser-side MathJax conversion, and no external renderer request. Numbered object support is current behavior: inspect fenced directives, stable IDs, rendered anchors, `@id` shorthand references, `raya:ref/id` explicit references, and the manifest-declared `data/numbered-objects.json` index instead of looking for LaTeX `\label` or `\ref` support.

When a rendering issue crosses math, numbered objects, skins, references, static environments, and local assets, inspect `examples/courses/render-fixture/course/5_authoring_matrix/0_index.md` first, then move to the specialized fixture page for the failing surface.

For the learning-science course shell, preserve source constraints and current
artifact authority. The right learning rail may render only current page
contents, normalized metadata, stable-ID prerequisites, and previous/next links.
Keep the boundary explicit: no inferred goals, no fake related practice, no
personal progress, and no browser-side MathJax. Use render-debug checks when
course shell layout, local resources, screenshots, overflow, or visible math can
regress.

When changing the shell, verify the expanded course map default, including the
expanded hierarchical course map structure,
map filter behavior, compact rail metadata, render-debug output, mobile
no-overflow behavior, and no external requests. The course map state and filter
text are non-persistent UI state.

For renderer debugging, use `scripts/check-render-debug.sh` when you need the focused fixture parity gate that also runs in host/Docker verification. The gate writes `report.json` and `index.html` beside the screenshots. When it fails, inspect `index.html` first, then use `report.json` for exact page, viewport, file path, and copied-site diagnostics. Use `raya preview <course> --render-debug /tmp/raya-render-debug` when diagnosing a specific course. Both paths inspect generated static pages; neither path executes course code or relies on browser-side MathJax conversion. Use debug output as evidence for layout/math failures, raw TeX leakage, external requests, and overflow, but keep authority in source files, `manifest.json`, and manifest-declared `data/*.json`. Treat render-debug files as local evidence only; do not commit them.

For numbered object diagnostics, compare the source directive, `data/numbered-objects.json` entry, rendered page anchor, static href, visible reference text, and render-debug screenshot/report evidence. Include the reader-ux fixture and theorem-family cases such as built-in `remark` when labels, shared sequences, or presentation regress. Note whether objects use the expected `scannable`, `caption`, or `equation` style. Use the render-debug route to capture screenshots and inspection output, but keep the machine contract in manifest-declared data rather than scraped HTML.

For numbered-content failures, compare five surfaces in order: the source directive, the build diagnostic, `data/numbered-objects.json`, the rendered anchor/link text, and render-debug screenshots/report details.

For proof blocks, validate `of` targets against `data/numbered-objects.json`; do not introduce LaTeX `\label`, `\ref`, `\begin{proof}`, or browser-side MathJax. Proofs render as expanded static environments and should not appear as numbered-index records.

For static-environment failures, inspect the source directive, the build
diagnostic, the target record in `data/numbered-objects.json` when `of` is present,
the rendered heading/anchor, and render-debug evidence from the `reader-ux`
fixture. `hint`, `solution`, and `answer` should be native closed `details`
disclosures by default; they must not require storage, fetch, scoring, external
assets, or browser-side MathJax.

```markdown
::: theorem {#main-theorem title="Fixture theorem"}
For every vector $\vect{v}$, the identity map returns $\vect{v}$.
:::

::: proof {#proof-main of="main-theorem" title="Identity"}
The equality follows component by component:
$$
I\vect{v}=\vect{v}.
$$
:::
```

For code and notebook references, classify linked `.py` and `.ipynb` files by extension and own-or-ancestor quantum ownership. Treat folder names such as `scripts/`, `labs/`, `code/`, and `notebooks/` as ordinary author choices, block private or cross-quantum references, copy only validated linked files to artifact and browser-facing file surfaces, update `references.json`, and never infer execution from previews.

For runtime metadata, treat `runtime/profiles.yaml`, root `pyproject.toml`, and `uv.lock` as source support outside learning order. Validate and emit runtime, execution-plan, and cache metadata, but never call `uv`, Docker, kernels, package installers, notebooks, scripts, or cache refreshes unless a later accepted execution contract explicitly says to do so.

For local execution, use `raya run <course> <target>` only when the task explicitly requires running a target. Prefer `--dry-run` to inspect the plan first. Treat `artifact/data/execution-results.json`, `artifact/logs/`, `artifact/execution/`, and `artifact/cache/results/` as generated output; do not edit or promote them as source truth.

For reviewed execution output, treat `_reviewed/execution/<target>/` as source-controlled support that requires human review. Use `raya outputs list <course>` to inspect generated and reviewed state without execution. Use `raya outputs freeze <course> <target>` only to copy a current successful generated result into `_reviewed/`; do not treat freeze itself as institutional approval. `policy: frozen` validates reviewed metadata and files, and must not call `uv`, Docker, kernels, scripts, notebooks, package installers, or cache refreshes.

For rendered surfaces, do not scrape normal HTML as authority and do not put verbose internals into default pages. Use `manifest.json`, `data/*.json`, copied files, and static `_raya/inspect/` pages for hashes, cache keys, source paths, artifact paths, runtime details, and reviewed-output freshness metadata.

For rendered preview, use `raya preview <course> --dry-run` to inspect the plan or `raya preview <course>` to serve the generated static site. Preview is non-executing: it may validate, build, and serve `artifact/site/`, but it must not call `raya run`, `raya outputs freeze`, Docker execution, kernels, package installers, scripts, notebooks, runtime profiles, or cache refreshes. Rendered-surface changes need static-read-path and visual/layout checks.

For repository documentation, `docs/raya.yaml` renders the live docs through `docs/render-content/`. Edit `docs/foundation/` and `docs/guides/` as the readable source, update the ordered render tree when a rendered docs page is added or reordered, and use `raya validate docs` plus `raya build docs` before relying on the static docs artifact.

When updating documentation, keep English and Spanish role pages separate. Preserve English technical identifiers such as `raya`, `raya.yaml`, `source`, `course/`, `_official/`, `_assets/`, `artifact/`, `packages/static`, and `OpenSpec`.
