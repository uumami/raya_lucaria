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

For wikilink issues, inspect source `[[target]]` or `[[target|label]]` tokens,
course page IDs, aliases, titles, nav titles, source paths, validation
diagnostics, rendered HTML, `data/links.json`, and `data/graph.json`. The
resolver is build-time and course-local; raw wikilink text in rendered HTML,
missing graph content edges, browser-side resolution, or external graph/search
requests are regressions.

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
Skin `tokens.density` may compact generated workspace cards, chips, controls,
and action links after rebuild. It must not shrink authored article text or
create browser-side skin switching, `localStorage`, `sessionStorage`, or
`data-raya-skin-override`.
For graph palette issues, inspect optional `tokens.graph.group_1` through
`group_8` in the selected skin, generated `--raya-graph-group-*` variables in
`skin.css`, graph group chip inline variables, SVG node and edge custom
properties, and arrow marker paths. Treat graph colors as visual readability
cues only, never as progress, ranking, recommendation, or graph authority.

For the `OpenDyslexic` reader toggle, verify the generated static assets under
`_raya/render/accessibility/`, the local font file, the local toggle script,
and static parity between preview and copied deployment. Treat any external font
request as a regression; the toggle may use a local script, but it must not
introduce browser-side MathJax or an external renderer.

For the `Text size` reader toggle, verify the same local accessibility resource
path, `data-raya-text-size` on the document root, labels in the left course
rail, computed article text size, and reload persistence. Treat it as a local comfort
preference only; it must not change `data-raya-skin`, source content, graph
data, progress, answers, mastery, or recommendations.

For print/PDF handout changes, emulate print media in a browser test. Verify
that left course rail commands, course maps, learning rails, workspace controls,
inspectors, filters, and graph canvases hide only in print, while article content, Page
briefs, MathJax, code, tables, official practice, numbered objects, and support
disclosures remain readable. Temporary disclosure opening for print must restore
after screen media returns and must not use storage, fetch, external assets, or
browser-side MathJax conversion.

For math authoring checks, use `examples/courses/render-fixture/course/2_math_authoring/0_index.md` as the focused source fixture. Verify source pages rather than generated `artifact/` files, and use render-debug evidence to confirm there is no raw visible TeX, no browser-side MathJax conversion, and no external renderer request. Numbered object support is current behavior: inspect fenced directives, stable IDs, rendered anchors, `@id` shorthand references, `raya:ref/id` explicit references, and the manifest-declared `data/numbered-objects.json` index instead of looking for LaTeX `\label` or `\ref` support.

When a rendering issue crosses math, numbered objects, skins, references, static environments, and local assets, inspect `examples/courses/render-fixture/course/5_authoring_matrix/0_index.md` first, then move to the specialized fixture page for the failing surface.

For the learning-science course shell, preserve source constraints and current
artifact authority. The main article may end with a Page connections block
generated from explicit incoming/outgoing content-link graph context. The
right learning rail may render current page contents, normalized metadata, stable-ID
prerequisites, previous/next links, current-section context derived from active
heading anchors, static Connections summaries for explicit
incoming/outgoing graph context, and graph-focus links for those explicit
relationships. Keep the boundary explicit: no inferred goals, no fake related
practice, no personal progress, and no browser-side MathJax. Use render-debug
checks when course shell layout, local resources, screenshots, overflow, or
visible math can regress.

For official practice rendering, inspect the source `_official/` object,
the generated `data/official.json` entry, the owning rendered page, and
`manifest.json` instead of treating normal HTML as authority. Verify that cards,
prompts, quizzes, and generic fields render only on the owning page as escaped
text, with native `details` reveal controls where appropriate and no private
source paths. For multiple-choice quizzes, verify native page-local option
buttons expose `data-raya-official-quiz-*` attributes, mark correct/incorrect
answers transiently, reset without persistence, and preserve the native answer
reveal for no-JavaScript reading. Confirm the page does not add scoring,
grading, submissions, attempts, progress, mastery, recommendations, backend
calls, runtime `fetch`, localStorage/sessionStorage, external/CDN renderer
requests, or browser-side MathJax. When this surface changes, include
static-read-path checks, escaping/privacy checks, no-storage/no-fetch
inspection, and role-doc impact.

For the Official Practice workspace, inspect the same source
`_official/` objects, `data/official.json`, `manifest.json`,
`_raya/practice/index.html`, and the local workspace script. Verify that the
workspace lists only accepted official objects, links each item back to its
owning page anchor such as `#raya-official-<id>`, and uses generated graph focus
links only when graph context exists. Verify the control, results, and context
workspace regions on desktop and mobile. Confirm there are no private source
paths, support paths, hidden answer duplicates, external requests, runtime
`fetch`, practice-state localStorage/sessionStorage, scoring, submissions,
attempts, grading, progress, mastery, recommendation, adaptive, or learner-state
language. Shared Text size and `OpenDyslexic` comfort preferences may use the
local accessibility resource only.
When this workspace changes, also verify active-object inspection parity:
visible objects expose `data-raya-practice-active`, hover and focus on existing
item links update the context panel, keyboard movement from the search input
selects one visible object, Enter opens that object's `.raya-practice-open`
link, `?page=<page-id>` handoffs from Search or Graph initially show only
objects owned by that page, and Clear/Escape reset transient active and page
focus state. Do not make object cards extra tab stops just to support
inspection.

For the Official Tasks workspace, inspect accepted `_official/assignments/`,
`_official/projects/`, `_official/exams/`, and `_official/tasks/` objects,
then compare `data/tasks.json`, `manifest.json`, `_raya/tasks/index.html`, and
the local `tasks.js` script. Public planning metadata should come from object
`content` fields such as `due`, `available`, `points`, `weight`, `status`, and
`tags`. Verify page anchors, graph focus links, filtering, sorting, keyboard
Enter-to-open behavior, responsive panels, no private paths, no runtime fetch,
no external requests, no browser storage, and no grading, submission, progress,
mastery, recommendation, or learner-state language.

For the Official Schedule workspace, inspect the same accepted task-family
objects and verify that only objects with public `content.due` or
`content.available` appear in `_raya/schedule/index.html`. Compare the embedded
payload with `data/tasks.json` semantics and the local `schedule.js` script.
Verify event-kind and type filters, search, keyboard Enter-to-open behavior,
owning page anchors, graph focus links, responsive panels, no private paths, no
runtime fetch, no external requests, no browser storage, and no calendar sync,
reminder, grading, submission, progress, mastery, recommendation, or
learner-state language.

When changing the shell, verify reader pages render no `.raya-top-command-bar`,
reader commands render under `[data-raya-course-map-tools]` in the left course
rail, and discovery workspaces still render `.raya-discovery-command-bar` as a
discovery command bar.
Also verify the expanded course map default, including the expanded hierarchical
course map structure, generated structural map numbers, current-page map
orientation, map filter behavior, reader breadcrumbs, compact previous/next
links, article-end Previous/Next sequence cards, compact rail metadata,
render-debug output, mobile no-overflow behavior, and no external requests.
Breadcrumbs should show course home,
ancestor pages, and the current page with accessible navigation markup,
deployment-neutral static links, current-page marking, no source paths, and no
private support paths. Course map shell collapse, filter text, current-page map
orientation, drawer state, and right-rail context are non-persistent UI state.
Course-map branch collapse is the only same-tab storage exception: it may store
course-scoped collapsed branch identifiers in `sessionStorage` across refresh
and same-tab page navigation, and must not become durable, cross-tab, progress,
recommendation, or personalization state. Current-page map orientation must also
remain non-persistent and must not restore legacy navigation storage. Treat
structural page position and sequence cards as course orientation, not learner
progress.
If the shell exposes current-section context, verify it is generated from the
page contents and heading anchors, updates with the active heading in browser
tests, remains a normal local anchor link, writes no browser storage, and does
not use reading percentage, completion, mastery, recommendation, or progress
language.
Reader pages use the left course rail as a single Course Tools area plus the course map. The map supports collapsible course-map branches for nested structure, and the same tab may remember which branches are collapsed after refresh or page navigation. That memory is orientation only, not progress or personalization.
If a page lacks authored `estimated_time`, verify any `Estimated read time`
shown in the Page brief or right rail is computed during build from public
article text, uses no browser storage or runtime fetch, and remains approximate
orientation rather than progress, mastery, recommendation, or personalization.
When authored `estimated_time` exists, it takes precedence as `Estimated time`.
If the shell exposes a left course rail `Context` command, verify it toggles
only the right learning rail where the context control is visible, keeps the
course map available, mirrors `aria-expanded` and labels with the rail controls,
uses small floating edge openers without reserving shell columns, and writes no
browser storage or progress/recommendation state.
For responsive shell changes, check desktop, tablet, and mobile viewports
together. Inline desktop may use three shell columns, medium-width reader pages
should keep the article as the only shell grid column and use overlay panels,
and phone-sized layouts must keep the rail body visible and reachable by
assistive technology when collapse controls are hidden. Pressing Escape inside
the rail on mobile must not leave `aria-hidden`, `inert`, or hidden focusable
content behind. Shell collapse/orientation state must not write localStorage.
Only course-scoped collapsed course-map branch identifiers may use same-tab
`sessionStorage`; drawer state, right-rail context, progress, recommendations,
and personalization must not be stored. Only explicit comfort preferences such
as text size or `OpenDyslexic` may persist durably.
When the phone-sized Course map drawer changes, verify visible drawer chrome,
the structural page position when present, the close button, backdrop close,
Escape close, focus restore to the opener, focus containment while open,
`aria-hidden`/`inert` closed state, background scroll lock only while open,
scroll-lock cleanup after close or desktop resize, no storage writes, no
external requests, and article/right-rail availability after close.
When collapsed reader rails change, verify the desktop Map and Context edge
openers remain keyboard-operable through their existing controls, increase
article width without reserved grid columns, become small floating overlays at
medium widths, stay hidden on phone-sized layouts when their controls are hidden,
and do not add storage, fetch, progress,
recommendation, or learner-state behavior. When shell comfort controls change,
verify that reduced-motion disables nonessential transitions and that collapsed
desktop regions are removed from keyboard and assistive navigation as specified.
When changing Course workspace shortcut cards, verify labels, structural badges,
deployment-neutral hrefs, page-focused Practice hrefs only for direct official
ownership, Schedule hrefs and dated-task badges only from direct dated official
tasks, collapsed-map hiding, desktop/mobile no-overflow behavior, and no
storage, fetch, progress, ranking, recommendation, or learner-state language.

The Page brief is part of the reader shell. Verify it appears before authored
content when public metadata exists, uses escaped summary/status/tags, resolved
prerequisite links, page-focused graph links, and official-practice anchors, and
does not expose source paths, private paths, runtime `fetch`, browser storage,
progress, mastery, recommendations, grading, personalization, or learner-state
language.

When changing generated section indexes, verify section landing card markup,
normal local link navigation, desktop/mobile no-overflow behavior, and absence
of recommendation/progress/mastery wording inside the generated index surface.

When changing the Course graph, verify fuzzy search, selected-page details,
selected-page neighborhood summaries, connected-page visual states, group
filters, group color semantics, source-group edge colors, transient hover/focus
spotlight dimming, transient search spotlighting over matching pages and
directly connected context, bounded degree-based node sizing, hover/focus inspection
status, keyboard inspection parity, selected-neighborhood focus mode,
connected-page detail controls that change graph selection without replacing
normal page links, selected-page relationship walkthrough cards that explain
explicit edge kind and direction without recommendation language, relationship
chip buttons that transiently focus those walkthrough cards by kind and
direction with `aria-pressed` and without URL or storage writes, contextual
SVG label reveal for selected, inspected, neighboring, search, active-result,
dragging, and high-degree pages, SVG graph node single-click selection without page
navigation, SVG graph node double-click page opening, focused SVG graph node
Enter-to-open behavior, the primary selected-page open link, the default deterministic `Connections` layout, alternate
`Topology`, `Cluster`, `Map`, `Radial`, and `List` layouts, expanded graph workspace state,
SVG viewport controls including pan buttons, focused graph Arrow-key panning,
graph-level `/` search-focus, `F` fit, and `R` reset shortcuts that do not
intercept typing in fields,
pointer drag panning, shared discovery chrome, compact mobile discovery
chrome, mobile no-overflow behavior, and no external requests after page load. Graph UI
state is non-persistent and must
come from embedded artifact graph data, not scraped HTML or browser storage.
Graph URL state may encode selected page, search query, layout, visible groups,
visible edge kinds, selected-neighborhood focus, expanded mode, and panel state.
Verify the compact graph-state readout and browser URL stay synchronized after
control changes, use only public structural state, can live inside a closed
native disclosure by default, and do not write `localStorage` or
`sessionStorage`.
Also verify the student-facing graph orientation band when Graph changes. Its
visible counts, layout, selected page, page focus, search, filters,
neighborhood focus, and selected-page actions must be derived from embedded
graph data and transient DOM state. The band must not use storage, fetch
runtime graph data, or introduce progress, mastery, ranking, recommendation, or
personalization language. Selected-page incoming/outgoing lists, relationship
chips, and relationship walkthrough cards must agree on explicit generated edge
kinds.
For desktop page-focused graph handoffs such as `?page=<page-id>`, verify that
the selected SVG node and at least one graph edge are actually visible inside
the first-paint graph canvas. Do not accept DOM-only checks that pass while the
canvas is stretched so tall that the graph appears below the visible area.
Graph layout positions are readability cues over explicit generated graph data.
`Topology` is a static readability view over explicit generated graph
relationships and the current visible edge set;
they must not come from external graph libraries or imply recommendation,
progress, ranking, importance, mastery, or authority.
Pan, Zoom in, Zoom out, Fit, Fit selection, Reset view, and minimap activation may change the SVG
`viewBox`; they must not fetch graph data, persist graph state, clear
selected-page details, or remain enabled when the SVG graph is hidden by list
layout. When minimap activation changes, verify click and keyboard activation
move the main canvas viewport without clearing selection, filters, URL state, or
storage. For selected-page fit behavior, verify that `Fit selection` is disabled
without a selected page and in list layout, becomes enabled after page
selection, keeps selected-page details/search/filter/URL state intact, frames
the selected page plus at least one visible connected edge when such an edge
exists, and brings the graph canvas into the visible browser viewport when the
canvas has been pushed below the fold.
Generated URL context may select a page only when it resolves to an embedded
graph node. Neighborhood counts must be derived from generated graph edges, and
connected-page highlights must exclude the selected node itself.
Selected-neighborhood focus may narrow the visible graph and list to the selected
page plus directly connected pages, but it must remain transient, reversible, and
free of graph-state storage, fetch calls, external graph libraries,
recommendation language, progress language, ranking, and mastery claims. Connections
rail counts must come from explicit graph context only. Rail graph-focus links
must point only to explicit prerequisites or incoming/outgoing graph context.
Article Page connections counts and links must also come from explicit
incoming/outgoing content-link graph context only, stay inside the article, and
avoid source paths, private support paths, external URLs, fetch requests,
storage calls, progress, mastery, recommendations, and ranking language.
Page-connection previews in the rail and article must use generated public page
metadata only: title, summary, status, local page URL, graph-focus URL, and
explicit relationship kind, direction, and incoming/outgoing counts. Connection
previews may label relationship kind and direction, such as `Content` and
`From this page`, using explicit generated graph context only. Verify native
disclosure behavior, escaped text, no private paths, no browser storage, no
fetch, no external requests, and no recommendation/progress/mastery wording.
Treat graph color, source-group edge color, size, search spotlighting,
spotlight dimming, and inspection text as structural readability cues; do
not introduce progress, mastery, recommendation, ranking, persistent graph
state, external graph libraries, fetch requests, or runtime graph payloads.
When changing Graph, verify graph-search keyboard movement over visible page
results, active-result inspection, Enter-to-open behavior, graph viewport
panning, single-click graph-node selection without page navigation,
double-click graph-node page opening, focused graph node Enter-to-open
behavior, and selected-page details as transient local navigation aids only.

When changing Course Search, verify approximate matching, keyboard result
movement, hover/focus active-result inspection, Enter-to-open behavior, clear
controls, shared discovery chrome, control/results/context workspace regions,
compact mobile discovery chrome, no
external requests, and no persistent search state. Search payloads stay
public: generated page metadata plus public rendered article prose. They must
exclude source paths, private support paths, artifact paths, MathJax internals,
raw TeX, cache keys, answer/support-only content, and learner state. Generated
query context and context-panel summaries must remain transient. Exact Search
page focus from `?page=<page-id>` may initially narrow visible results to one
public page ID; Clear and Escape must restore all visible results without
writing browser storage or changing source authority, including when focus is
on a visible result link or context action instead of the query input.
Search result graph-focus links must come from stable page IDs and generated
local graph URLs, preserve Enter-to-open-page behavior, and avoid recommendation
or progress language. Search, Graph, Practice, and Tasks discovery pages may load
local accessibility resources for Text size and `OpenDyslexic`, but must not
load `shell.js`, a course-map toggle, external workspace assets, or persisted
graph/search/practice/tasks state.

When changing Tasks or Schedule, verify URL-only `?page=<page-id>` handoffs from
Search or Graph. The destination workspace may initially narrow visible public
task-family objects to the requested page, but Clear and Escape must restore the
full static workspace without writing browser storage or changing source
authority. Escape must work from focused result links or context actions, not
only from the query input. Treat the page query as transient navigation context,
not progress, recommendation, mastery, grading, or personal due state.

When changing Search or Graph discovery cards, verify that embedded payloads and
visible cards use only public generated data: page title, nav title, stable ID,
hierarchy label, status, summary, tags, public rendered article prose for
Search, generated public section/object anchors and snippets for Search
subresults, previous/next course-order links, explicit graph link counts, accepted
official object counts, and relative links to owning pages or generated
workspaces. Confirm there are no source paths, `_official/`, `_assets/`,
`_reviewed/`, artifact internals, cache keys, MathJax internals, raw TeX,
answer/support content, runtime `fetch`, search/graph storage, external
requests, recommendation, progress, mastery, completion, ranking, or fake
related-practice language. Search Enter must still open the page result, while
Graph selected-page details may offer separate Search and Practice handoff
links. Search handoff links should include `?page=<page-id>` for exact public
page focus. Practice handoff links should include `?page=<page-id>` only when
the page owns accepted official objects, and that page focus must remain
URL-only state.

When Course Search changes, verify section subresults as well as page results.
Generated section records may point to public rendered heading or numbered-object
anchors, but must not include raw TeX, MathJax CHTML, private paths, support-only
answer text, artifact internals, or learner-state language.

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

For discovery workspace page-focus failures, open Search, Practice, Tasks, and
Schedule with a valid `?page=<page-id>` handoff and verify the first-viewport
focused course page strip names the public page, links back to the page, links
to the same page focus across Search, Graph, Practice, Tasks, and Schedule, and
offers `Clear focus`. Also verify the control region shows a compact page-focus
notice with the public page title and visible count where that workspace has one.
Then verify Clear and Escape hide the notice and restore all visible results or
objects. Missing or invalid page focus must keep the strip and notice hidden.
Do not add storage, fetch, external resources, learner-state wording, or
recommendation language to make page focus work.

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
