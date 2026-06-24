---
id: docs-learning-renderer-contract
title: Learning Renderer Contract
summary: Current, planned, and future renderer behavior derived from learning science.
status: ready
---
# Learning Renderer Contract

The learning renderer contract maps the principles in `19_learning_science_principles.md` to Glintstone static renderer behavior. It defines what the current course shell may show, what later static work may add, and what requires future dynamic study state.

## Course Shell

The course shell is the reader-facing static page structure for a built course. It should help students answer:

- where am I in the course;
- what should I read now;
- what does this page depend on;
- what can I do next;
- what official or authored practice is visible without pretending to know my personal state.

The shell uses current artifact data only. It must not infer learning goals, related practice, assignments, progress, mastery, or spacing from prose.

The current shell uses an expanded course map, rendered as an expanded hierarchical course map by default on desktop and browser load, keeps the article primary, and supports mobile article-first layout. The sticky command bar may show current reading context such as course title, page title, structural page position, and compact previous/next links. Article pages may show reader breadcrumbs with the course home, ancestor pages, and current page generated from navigation data. Breadcrumb links are deployment-neutral static links and must not expose authored source paths. The course map is generated from current navigation data, can be filtered locally by rendered page labels, may show generated structural sequence numbers, and may auto-orient the current page into the visible map region after load. It does not collapse on hover; readers can collapse it through an explicit click control, and keyboard users can close it with Escape. Collapsed mode becomes an operable compact map rail: visible rail items remain real navigation targets, not decorative markers. Course-map state, orientation, and filter text are non-persistent UI state. The shell may show structural page position such as `Page N of M`; this is course structure, not personal progress. The article may also end with larger Previous/Next sequence cards generated from the same ordered navigation data so students have a clear static reading path after finishing the page.

## Static Renderer Status

| Capability | Status | Static renderer behavior |
| --- | --- | --- |
| Course map and reading context | `current` | Render a hierarchical map from current navigation data, expanded by default when the shell script runs, locally filterable by page labels, able to show structural sequence numbers, able to auto-orient the current page into view, non-persistent, not hover-triggered, and collapsible through an explicit click control or Escape into an operable compact map rail. The sticky command bar may show static course/page title, structural page position, and compact previous/next links. Article breadcrumbs may show course home, ancestor pages, and the current page as accessible static location links. |
| Main article | `current` | Render authored content, build-time MathJax, numbered objects, spoiler-safe static environments, callouts, tables, code, local assets, optional Page connections from explicit content-link graph context with native page previews, and article-end Previous/Next sequence cards from generated course order. |
| Right learning rail | `current` | Render page contents, normalized summary/status, optional estimated time/tags, stable-ID prerequisites, static Connections summaries for explicit graph link context, native page previews, graph-focus links, and previous/next links from current artifact data. |
| Reader controls | `current` | Use local OpenDyslexic resources, keyboard-reachable controls, copyable fenced code blocks, and previous/next page keyboard navigation from generated sequence links. |
| Local course search | `current` | Render a static search workspace from generated page metadata only, using local JavaScript, approximate matching, keyboard, hover, and focus result inspection, control/results/context panels, deployment-neutral page links, and graph-focus links generated from stable page IDs. |
| Discovery workspace chrome | `current` | Render shared static course chrome on generated Search, Graph, and Practice surfaces with a course link, cross-workspace links, local comfort controls, compact mobile layout, workspace control/results/context regions where useful, and no shell script dependency. |
| Official practice section | `current` | Render page-level official cards, prompts, quizzes, and generic official object fields from colocated `_official/` data on the owning page as a static `Official practice` section, using escaped text and native reveal controls where appropriate. |
| Official Practice workspace | `current` | Render a generated static discovery workspace at `_raya/practice/index.html` over already accepted official objects from `data/official.json` and page-owned `_official/` source objects, with local filters, keyboard, hover, and focus object inspection, control/results/context panels, local links back to owning page anchors, and graph focus links. |
| Checkpoints and goals as metadata | `planned` | Require a future source-contract change; do not infer from prose. |
| Related practice index | `planned` | Requires accepted source/artifact data. |
| Personal progress, analytics, adaptive review, spaced queues | `future` | Requires dynamic study state outside the static renderer. |

## Current Responsibilities

The static renderer may present command-bar reading context, course map navigation, article breadcrumbs, the main article, and the right learning rail as reader-facing regions. These regions should be stable across desktop and mobile layouts even when the visual skin changes.

The main article owns authored teaching content. It may include build-time MathJax, numbered objects, static environments, callouts, tables, code, local assets, generated section landing cards, and links rewritten through current Raya rules. Generated section landing cards come from current child pages, page summaries, estimated time, and authored study-object counts; they are course structure, not recommendations, completion, mastery, or personal progress. Proof static environments remain expanded as part of the reasoning flow. Optional support environments such as hints, solutions, and answers render as native closed disclosures by default so learners can reveal support intentionally without the static page storing progress, submitting answers, or contacting a service. When explicit outgoing or incoming content-link graph context exists for the page, the article may end with a Page connections block that shows static counts, linked pages, graph-focus links, and native previews with public linked-page summary, status, and explicit relationship counts when that generated metadata exists. The article may also end with larger Previous/Next sequence cards from generated navigation so readers can move through the ordered material after finishing a page. These cards are static course-order links, not recommendations, completion signals, or personal next steps. Article-end generated blocks must not expose source paths, private support paths, external requests, storage calls, or inferred study guidance.

The official practice section is reader-facing convenience over accepted course source and artifact data, not canonical authority. Canonical official practice remains the authored course files under colocated `_official/`; machine-readable authority remains manifest-declared data such as `data/official.json` and `manifest.json`. Static pages may render the owning page's official cards, prompts, quizzes, and generic official object fields as escaped text inside an `Official practice` section. Prompts, answers, explanations, choices, and other revealable support may use native `<details>` controls so students can intentionally open them. This section must not render private source paths or support paths, must not scrape prose to invent practice, and must not turn official objects into scoring, grading, submissions, attempts, progress, mastery, recommendations, backend calls, browser-side fetching, localStorage/sessionStorage, external/CDN renderer requests, or browser-side MathJax conversion.

The Official Practice workspace is a generated static discovery surface for accepted official objects across the course. It reads manifest-declared `data/official.json` and page-owned `_official/` objects during build, then publishes `_raya/practice/index.html` with a local script and an embedded public payload for static filtering and navigation. It may list accepted cards, prompts, quizzes, tasks, and generic official objects with public page title, object type, stable ID, label, owning page link, owning page anchor such as `#raya-official-<id>`, graph focus link when generated graph context exists, and a context panel derived from the active or first visible accepted object. The active object may be selected transiently through keyboard movement, pointer hover, or focus on an existing object link. The workspace is not a second authority surface and must link students back to the owning page for context.

The Practice workspace must not expose private source paths, `_official/` paths, support paths, answer-only hidden duplicates, artifact internals, cache keys, or source hashes. It must not fetch data at runtime, load external scripts or renderers, persist state, score answers, collect attempts, submit work, grade, estimate progress or mastery, recommend what to do next, adapt to a learner, or store personal practice state. Revealed support remains ordinary static content or native disclosure behavior from accepted official objects, not a submission or tracking workflow.

The right learning rail owns compact page context. It is expanded by default on desktop and may collapse through an explicit click control into an operable compact context tab. Collapsed rail content must be hidden from keyboard and screen-reader navigation. It may show page contents, normalized `summary` and `status`, optional estimated time and tags when accepted data exists, stable-ID prerequisites when they resolve to current pages, static Connections summaries for explicit incoming and outgoing content links from generated graph data, native previews for linked pages using public generated metadata, graph-focus links for those explicit relationships, and previous/next links from generated navigation.

Explicit graph link context means relationships already present in source links, stable IDs, or prerequisite metadata. It does not mean inferred recommendations, related practice, personal next steps, or mastery guidance.

The static graph page is a reader-facing view of generated artifact graph data.
It may provide local fuzzy search, deterministic layouts, group filters,
selected-page details, incoming/outgoing link lists, a static legend/help panel,
selected-page neighborhood summaries, connected-page visual states, transient
page focus from generated URL context, structural group color, bounded node
size derived from static link degree, source-group edge colors,
transient search spotlighting over matched pages and directly connected
context, transient hover/focus spotlight dimming, hover/focus inspection text, keyboard
inspection parity, public selected-page discovery card metadata, non-persistent selected-neighborhood focus mode,
detail-list controls that select connected pages inside the graph workspace without replacing normal page links,
non-persistent SVG viewport controls such as Zoom in, Zoom
out, pan buttons, focused canvas Arrow-key panning, pointer drag panning, Fit,
and Reset view, and a non-persistent expanded workspace mode. These visual
semantics are readability cues for current graph structure only; they are not
progress, authority, recommendation rank, importance rank, mastery, or
completion signals. Pan, Zoom in, Zoom out, Fit, and Reset view change only the visual graph viewport;
they must not clear search, filters, selected-page details, or authored graph
data. The default `Connections` layout may arrange visible pages by normalized
explicit graph relationships and course order so students can read link flow,
while `Cluster` may group visible pages by generated course group, and `Map`,
`Radial`, and `List` remain alternate local views. Layout position is only a
readability cue over generated graph data, not recommendation rank, progress,
importance, mastery, or authority. Selected-neighborhood focus may narrow visible graph and list nodes to the selected page plus directly connected pages from explicit generated edges, but it remains transient UI state and must always allow return to the full graph. It must not fetch graph data at runtime, load external graph
libraries, persist graph state, infer
recommendations, or present graph position as personal progress.

Generated Search, Graph, and Practice pages may share discovery workspace chrome that shows the current course title, identifies the workspace, links back to the course, links between discovery workspaces, and exposes local text-size and `OpenDyslexic` controls. Search and Practice may also use static workspace regions for controls, results, and public context summaries so desktop readers can scan without leaving the page. Search result context and Practice object context may follow transient active cards selected by keyboard movement, pointer hover, or focus on existing links. This chrome and active context are static page structure. They must not load the course shell script, show a course map control without a course map, store search, graph, or practice state, fetch external resources, or turn structural workspace labels into progress, ranking, or recommendation language.

Generated Search and Graph cards/details may show public page metadata from generated artifact data: page title, navigation title, stable ID, hierarchy label, status, summary, tags, previous/next course-order links, explicit incoming/outgoing/connected graph counts, accepted official object counts, and local links to Search, Graph, Practice, and owning pages. These are structural discovery cues, not recommendations, progress, mastery, importance, ranking, or related-practice inference. Official object counts may be displayed only as counts of accepted source objects owned by the page or its generated structural scope. They must not imply recommended practice or expose answer/support content.

Reader controls may use local `OpenDyslexic` resources, a local text-size comfort preference, keyboard-reachable controls, copyable fenced code blocks, and previous/next page keyboard navigation from generated sequence links. They must work from static files and must not depend on fetch/XHR requests, accounts, a backend, CDN resources, external font requests, personal progress, adaptive recommendations, or browser-side MathJax conversion. Local storage may be used only for reader comfort preferences such as font and text size; it must not store course progress, answers, mastery, recommendations, graph state, skin authority, or authored content.

Local course search may expose generated page titles, navigation titles, stable IDs, summaries, status, hierarchy labels, tags, explicit link counts, official object counts, rendered page links, workspace handoff links, and graph-focus links generated from stable page IDs. It may support approximate matching, clear controls, keyboard movement over visible results, hover and focus inspection of visible results, transient query context from generated page links, public context summaries for visible results, and static handoff from a result to the graph page focused on the same page. It must not scrape rendered prose, MathJax output, source paths, artifact paths, cache keys, personal progress, answer/support content, related-practice inference, or recommendations into the student search surface.

## Planned Static Work

Checkpoints, goals, and related practice may become static metadata only after an accepted source-contract and artifact-contract change. Until then, authors may write checkpoint prompts and practice links as content, but the renderer must not treat prose as structured goals.

Related practice indexes need accepted source or artifact data. The renderer may not scrape headings, numbered objects, tags, or paragraph text to invent them.

## Future Dynamic Work

Personal progress, analytics, adaptive review, spaced queues, mastery estimates, dashboards, and per-student recommendations require dynamic study state outside the static renderer. Future packages such as `study`, `graph`, `web`, or `identity` may own those behaviors after accepted contracts define them.

## Non-Goals

The learning course shell has explicit non-goals in this loop:

- no personal progress claims in static HTML;
- no hover-first navigation expansion that moves the reading layout without intent;
- no wording that turns structural page position into personal progress;
- no inferred goals or related practice;
- no scoring, grading, submissions, attempts, progress, mastery, or recommendations from static official practice;
- no adaptive, recommended, personalized, stored, fetched, scored, submitted, or graded behavior in the Official Practice workspace;
- no backend calls, browser-side fetching, localStorage/sessionStorage for practice state, or browser-side official-object hydration;
- no browser-side MathJax conversion;
- no external CSS, font, script, renderer, or CDN requests;
- no hidden schema change to distinguish raw `summary` or `status` presence in this loop.

These non-goals protect student trust. A static page may organize current data, but it must not pretend to know learner state or run a browser-only renderer.

## Verification

Changes to the course shell, right learning rail, reader controls, official practice rendering, local assets, MathJax output, or visual layout should include static-read-path and render-debug checks. Breadcrumb checks should cover accessible navigation markup, course-home and ancestor links, current-page marking, deployment-neutral relative URLs, no source/private paths, no external requests, and desktop/mobile no-overflow behavior. Page-connection preview checks should cover public metadata only, escaped text, local page and graph links, native disclosure controls, no source/private paths, no storage/fetch calls, no recommendation/progress/mastery wording, and no external requests. Official practice checks should cover escaping, source path privacy, native reveal controls, no storage/fetch calls, no external renderer requests, and no browser-side MathJax conversion. Practice workspace checks should cover `_raya/practice/index.html`, local script only, links to owning page anchors, graph focus links, no private source paths, no answer-only hidden duplication, no storage/fetch calls, no external requests, and no learner-state language. Use `scripts/check-render-debug.sh` for the focused render-fixture gate when browser-visible math, local resources, screenshots, external requests, or overflow can regress.
