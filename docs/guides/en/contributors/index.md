---
id: docs-guides-en-contributors
title: Contributors And Collaborators
nav_title: Contributors
summary: Workflow guidance for changing code, specs, docs, tests, and contracts safely.
status: ready
---
# Contributors And Collaborators

Start with `docs/foundation/15_system_overview.md`, then `docs/foundation/13_truth_surfaces.md`, then the accepted OpenSpec specs for the capability you are changing.

OpenSpec remains available for future contract changes. When a user explicitly selects a Superpowers workflow, committed Superpowers design and plan documents may drive that loop, but `docs/foundation/` remains the highest source of seed truth and implementation must update the affected foundation, role, test, and contract surfaces.

Use the Docker Compose and `uv` commands from `README.md` and `AGENTS.md` when changing code, contracts, docs, or tests. Run `./scripts/check.sh` before archive or commit, run `./scripts/check-docker.sh` when Docker behavior changes, and keep `./scripts/smoke-test.sh` for external-course smoke checks when command or course portability changes. Run `./scripts/check.sh` and `./scripts/check-docker.sh` sequentially. Both prepare local Node/MathJax dependencies through `scripts/check-python.sh`, so the scripts fail fast when another verification is already preparing dependencies. Wait for the active check to finish, then rerun the blocked command. Keep deferred capabilities in `docs/foundation/18_known_missing_work.md` until an accepted OpenSpec change makes them current. Keep package paths, commands, schema fields, and stable IDs in English.

When changing course validation or rendering, preserve the convention-first source model: `source: course` points at the ordered `course/` tree, ordered filenames define authoring order, frontmatter `id` defines stable identity, colocated `_official/` and `_assets/` stay private, and `navigation.json` plus `indices.json` are generated artifact data. Tests should cover source diagnostics, official object export, asset copying, artifact schemas, and static-read-path rendering.

Course-local wikilinks are build-time authoring syntax, not browser behavior.
Validation resolves `[[target]]` and `[[target|label]]` against the current
course pages, fails missing or ambiguous targets, and rendering emits ordinary
static local links plus explicit content graph edges. Do not add browser-side
wikilink resolution, external graph/search services, or source-path leakage.

Rich static rendering is Glintstone-owned. Keep parser, highlighter, and MathJax libraries behind the `packages/static` boundary; source contracts should describe supported authoring behavior, not library internals. Accepted math uses inline dollar math, display dollar-delimiter blocks, page-local macros, local `site/_raya/render/math/` support resources, strict diagnostics, and no browser-only renderer dependency. Renderer changes need representative fixtures, invalid diagnostics when applicable, contract tests, e2e/static-read-path tests, Chromium visible-math/no-external-request checks, desktop/mobile overflow checks, and role documentation updates.

Fenced code blocks render with local copy controls. Preserve exact copied `pre code` text, keyboard-reachable buttons, static HTML fallback, and the no-storage/no-fetch/no-external-script rule when changing this behavior.

Reader comfort controls live in local accessibility resources. `Text size`
applies only to the authored article, and `Text size` and `OpenDyslexic` may
persist local browser preferences, but they must not change
course skins, source data, graph data, numbered object identity, progress,
answers, mastery, or recommendations.

Print/PDF handouts are renderer behavior over generated `artifact/site/` pages.
Keep them print-media scoped: hide chrome and controls, preserve article
content, MathJax, code, tables, official practice, numbered objects, and support
disclosures, and avoid fetch, storage, external assets, learner-state language,
or source-path leakage.

Skin profile changes must preserve token validation and generated static output.
Course-local profiles under `skins/` define semantic tokens. Course
`render.skin` and section `_raya/skin.yaml` selectors choose one of those
profiles; they do not define tokens. Rendering emits `_raya/render/skin.css`
and marks pages with `data-raya-skin`. The generated CSS file is `skin.css`
under the renderer support path. The rule is no arbitrary CSS, no external
fonts, no CDN requests, and no browser-side skin resolution. Cover skin changes
with render-debug evidence when generated CSS, page attributes, local resources,
or visual layout can regress. When changing this contract, keep docs aligned
with `REQUIRED_COLOR_TOKENS`, `REQUIRED_GRAPH_TOKENS`,
`REQUIRED_FONT_TOKENS`, `ALLOWED_DENSITIES`, and `ALLOWED_FONT_STACKS` in
`packages/static/src/raya_static/skins.py`. Optional graph tokens must remain
validated categorical color cues for generated `--raya-graph-group-*`
variables; do not let them become arbitrary CSS, browser-side theme logic, graph
data authority, progress, ranking, or recommendations. Tests should cover
unknown selectors, duplicate IDs, filename/id mismatches, unsupported token
fields, malformed colors, malformed graph colors, low contrast, invalid
density, unsafe fonts, generated `skin.css`, graph palette CSS variables, and
nearest-section inheritance.
Density tokens may change generated workspace card and control spacing through
renderer-owned CSS variables. They must not become article typography controls
or browser-side skin override logic.

Use `examples/courses/render-fixture/course/2_math_authoring/0_index.md` when changing math rendering or authoring guidance. It is the fixture target for current valid examples: `\begin{bmatrix}`, vector macros, `\newcommand`, `\renewcommand`, set and logic notation, norms, inner products, aligned derivations, optimization notation, and numbered object Markdown. Keep invalid math examples in tests so professor and student docs remain copyable.

Use `examples/courses/render-fixture/course/5_authoring_matrix/0_index.md` as the compact fixture when a change crosses math, numbered objects, skins, static environments, local assets, and static read-path behavior.

Numbered object support is current renderer behavior. Preserve the `render.numbered_objects` config model for numbering plus course-level sequence and family overrides; validate fenced directives, stable object IDs, `@id` shorthand references, and `raya:ref/id` explicit references; and emit the manifest-declared `data/numbered-objects.json` index with object IDs, labels, numbers, source paths, page output paths, anchors, hrefs, and reference text. Preserve built-in `remark` support and the default reader presentation: theorem-like, example, exercise, and assignment sequences use `scannable`, figures and tables use `caption`, and equations use `equation`. Static pages must render labels and links without external renderer or CDN requests and with no browser-side MathJax or browser-side reference resolver. Fixture and debug checks should cover remark plus the reader-ux fixture when the numbered-content reader experience changes.

When changing numbered content behavior, keep CLI/build diagnostics and `data/numbered-objects.json` authoritative. Render-debug may summarize objects, references, proof headings, and screenshots, but it is evidence for inspection, not a replacement data contract.

Proof blocks are static render surfaces, not numbered-index records. They may resolve `of` against any numbered object family, render a proof heading and body, and remain absent from `data/numbered-objects.json`.

Build-time static environments are separate from numbered objects. Preserve
`proof`, `solution`, `hint`, and `answer` as rendered blocks whose optional `of`
target resolves against `data/numbered-objects.json`; do not add them to the
numbered index or require browser-side reference resolution. Keep proofs
expanded, and keep `hint`, `solution`, and `answer` as native closed
`details` disclosures by default. Do not add scoring, storage-backed progress,
fetch requests, external assets, or browser-side MathJax to those disclosures.

The learning renderer contract divides course shell behavior into `current`,
`planned`, and `future` categories. Current renderer work may use existing
navigation, authored content, local assets, build-time MathJax, page metadata,
and stable prerequisites. Planned work needs accepted source and artifact data.
Future work such as personal progress, analytics, adaptive review, and spaced
queues needs dynamic study state outside the static renderer. Preserve the
rules: no browser-side MathJax, no external assets, no inferred goals, and no
related practice invented from prose.

Same-tab sessionStorage may restore only course-scoped collapsed course-map
branch identifiers and the explicit left/right structural rail display pair.
Drawer, filter, focus, scroll, active-context, progress, mastery,
recommendation, and personalization state remains non-persistent.

The official practice section is a current static rendering surface for
page-level objects from colocated `_official/` data on their owning page.
Review it as reader-facing convenience over existing source and
artifact authority: `_official/` remains source truth, while `data/official.json`
and `manifest.json` remain machine surfaces. Verification should cover cards,
prompts, quizzes, generic official object fields, escaped text, native
`details` reveal controls where appropriate, deterministic ordering, and
source-path/privacy boundaries. Multiple-choice quiz controls should be native
page-local buttons over accepted option data, preserve the reveal fallback, and
reset without storage. Do not add scoring, grading, submissions, attempts,
progress, mastery, recommendations, backend calls, runtime `fetch`,
localStorage/sessionStorage, external/CDN renderer requests, or browser-side
MathJax. Changes to this surface should include static-read-path coverage,
focused escaping/privacy assertions, no-storage/no-fetch checks, and role-doc
impact for students, professors, contributors, and agents.

The Official Tasks workspace is also current static renderer behavior. Review
it as a generated planning surface over official `assignment`, `project`,
`exam`, and `task` objects, not as a calendar service or learner-state system.
Verification should cover `data/tasks.json`, manifest declaration,
`_raya/tasks/index.html`, the local `tasks.js` resource, public `content`
planning fields, owning page anchors, graph focus links, filtering, sorting,
keyboard inspection, desktop/mobile layout, no external requests, no runtime
fetch, no browser storage, and no grading, submission, progress, mastery, or
recommendation language.

Calendar is current static renderer behavior over manifest-declared
`data/calendar.json`: explicit official sessions, holidays, cancellations, and
milestones plus due and available dates derived automatically from valid
official task-family objects. Verify agenda and month views, local filters,
owning page anchors, graph focus links, no private paths, no runtime fetch, no
network requests, no browser storage, and no grading, submission, progress,
mastery, recommendation, reminder, synchronization, or learner-state language.
Its visible name is Calendar; `/_raya/schedule/` is a compatibility URL only.

Review shell controls as accessibility surfaces. The current reader uses an expanded course rail of 256px through 1311px and 288px from 1312px, with a fixed header, one central native vertical scroll
owner, and a fixed footer. Its six two-column actions are Search, Graph,
Practice, Tasks, Calendar, and Context; Search opens the generated workspace,
while the local Content filter narrows only rendered map labels. The footer
contains Text size and OpenDyslexic. At 640px and wider, explicit collapse uses
a reserved 48px structural mini rail. Phone-sized layouts may open the course
map as a 256px phone drawer. The phone drawer and other transient
shell state remain non-persistent; the explicit structural rail display pair may
persist in same-tab sessionStorage under the course-scoped contract above. The
course-map behavior is
explicit-click rather than hover-triggered, uses `aria-expanded`, and must be
served from local renderer resources rather than external scripts or styles.
Article-end Previous/Next cards are generated from the same course order as the
compact sequence links. Keep them static, keyboard reachable, responsive, and
free of progress, mastery, recommendation, or personal next-step wording.

Treat authored course navigation as the source of the tree title and structural
order. Each branch has a separate disclosure control: the chevron changes only
that branch, while the title is the deployment-neutral page link. The protected
same-parent accordion keeps the current path visible and records direct reader
collapse/expand intent without changing authored order or creating learner
state. At structural widths the expanded and mini rails use full viewport
height around their one central scroller. Verify no-script navigation keeps the
static links and current path usable in normal flow while enhancement controls
are absent.

Review the Page brief as first-screen static orientation over already accepted
metadata. It may show summary, status, structural page position, authored
estimated time or computed estimated read time, tags, resolved prerequisites,
explicit graph-link counts, and official-practice counts. It must use local
links and anchors only, stay responsive, and avoid source paths, private paths,
fetches, browser storage, progress, mastery, recommendations, grading, or
personalization.

Review the Course graph as a static artifact surface. Graph search, selected-page
details, group filters, SVG viewport controls, and expanded graph workspace mode
must use embedded artifact data and local renderer resources only. Zoom in, Zoom
out, Fit, and Reset view may change the visual SVG viewport, but must not persist
state, fetch graph data, or clear selected-page context. Graph shortcuts may
focus search, fit the SVG view, or reset graph filters and selection, but must
not intercept typing in form fields. Do not add CDN graph
engines, runtime fetches, persistent graph state, or recommendation/progress
wording. Selected-page relationship walkthroughs must be built from explicit
generated graph edges and local links only. Relationship chips may act as native
button filters for that walkthrough, with `aria-pressed`, no URL mutation, no
browser storage, and clear behavior when graph selection changes. Contextual label reveal may hide
low-context SVG labels visually, but page anchors and `aria-label` text must
remain available. Generated URL context may focus a page, but it must remain transient.
Connection previews may label relationship kind and direction, such as
`Content` and `From this page`, using explicit generated graph context only.
Graph state/debug readout and copy URL controls may be hidden behind a native
disclosure by default; keep the underlying state synchronized, local, and free
of graph storage.

Review Course Search as the matching companion to graph navigation. Approximate
matching, clear controls, and keyboard result movement are allowed over embedded
public page metadata and public rendered article prose. Do not index source
paths, artifact paths, private support paths, MathJax internals, raw TeX,
cache keys, answer/support-only content, or learner state. Generated query
context may preload the search box without becoming stored search state. Search
records may include generated public section/object anchors and snippets as
subresults, but those records must remain sanitized public scan aids rather
than recommendations or alternate authority. Search
result graph-focus links must be generated from stable page IDs and local graph
URLs only; keep their wording structural, such as `View in graph`. Search and
Practice discovery workspaces may use control, results, and context regions on
desktop. Search, Practice, Tasks, and Calendar may show a shared focused course
page strip for a valid `?page=<page-id>` handoff, with same-page links across
Search, Graph, Practice, Tasks, and Calendar. Search, Practice, Tasks, and
Calendar may also show compact page-focus notices in their control regions. The
strip and notices must hide for missing or invalid page focus and after
Clear/Escape restores the full workspace. Those regions must stay public,
responsive, and free of stored discovery state.

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

Before changing renderer behavior, run the focused parity gate with `scripts/check-render-debug.sh`. It builds and previews `examples/courses/render-fixture`, captures desktop/mobile render-debug artifacts, and fails on visible raw TeX, external renderer requests, missing screenshots, overflow, or browser-side MathJax runtime dependencies. The gate writes `report.json` and `index.html` beside the screenshots. When it fails, inspect `index.html` first, then use `report.json` for exact page, viewport, file path, and copied-site diagnostics. For an individual course regression, use `raya preview <course> --render-debug /tmp/raya-render-debug`. Treat those files as local evidence only; do not commit them and do not treat them as artifact authority.

Code and notebook references are static source support in the current baseline. Validate linked `.py` and `.ipynb` files by extension and own-or-ancestor quantum ownership, not by required folder names. Copy only validated linked files to manifest-declared `artifact/files/` and `artifact/site/_raya/files/`, keep `references.json` machine-readable, and preserve the `not-executed` status until an execution proposal accepts runtimes and caches.

Runtime profiles are metadata only. Keep `runtime/profiles.yaml`, `pyproject.toml`, and `uv.lock` outside the ordered `course/` tree; validate policies, profile paths, cache inputs, and generated `runtime.json`, `execution.json`, and `cache.json` without calling `uv`, Docker, kernels, or source files.

Local execution is explicit. `raya run <course> <target>` may run one validated script or notebook through the selected `uv` profile, with `--docker` only when requested and configured. Execution changes need CLI tests for dry-run, policies, cache reuse, refresh, logs, output files, notebook output preservation, Docker command shape, artifact inspection, and no-execution regressions for validate/build/inspect/static serving.

Reviewed execution output is the source-controlled frozen path. Keep reviewed files under colocated `_reviewed/execution/<target>/`, validate `reviewed.yaml` against current source/runtime/input/review/file hashes, and expose current reviewed output through `data/reviewed-outputs.json`, `artifact/reviewed/`, `site/_raya/reviewed/`, reference metadata, and static panels. Changes need tests for `raya outputs list`, `raya outputs freeze`, stale metadata, missing files, `policy: frozen`, artifact inspection, static read paths, and no-execution regressions.

Rendered pages use surface discipline. Keep normal pages focused on authored content, navigation, generated indexes, compact resource/status panels, and deployment-neutral links. Put verbose hashes, cache keys, source paths, artifact paths, and reviewed-output freshness internals in `manifest.json`, `data/*.json`, or static `_raya/inspect/` pages.

Generated section landing cards are part of the normal generated index surface.
They must be derived from child pages, summaries, estimated time, and authored
study-object counts only. Do not use them for recommendations, completion,
mastery, personal progress, or inferred next actions.

Use `raya preview <course>` for local review of generated static pages. Preview validates, builds, serves `artifact/site/`, and reports the student entrypoint plus `_raya/inspect/` URL when present. Preview changes need CLI tests, no-execution regressions, static-read-path coverage, and visual/layout assertions for representative desktop and mobile-sized viewports.

Current documentation is also a renderable docs course. Edit the readable pages under `docs/foundation/` and `docs/guides/`, keep `docs/render-content/` aligned for rendered order, and treat `docs/artifact/` as ignored generated output. Use `raya validate docs`, `raya build docs`, and static-read-path tests when changing documentation rendering behavior.

For substantial changes, state the documentation impact for contributors/collaborators, professors, students, and agents. If role documentation changes, keep the English and Spanish pages separate.

Search, Graph, Practice, Tasks, and Calendar use the persistent Course map with
generated relative links and local shell resources. Review the active workspace
tile, no current course-tree link, and absent reader-only Context alongside the
workspace-local filters, results, and focused-page strip. These interactions are
volatile: they must not fetch external resources or write learner, source,
artifact, or unrelated preference state.

## Publishing independent courses

Use [Publishing Independent Courses](raya:docs-guides-en-contributors-publishing-courses)
when a course team wants optional GitHub Pages delivery without making the
provider part of the course contract.
