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

The current shell uses an expanded course map, rendered as an expanded hierarchical course map by default when the approved `894px+` reader geometry is active, keeps the article primary as the continuous reading surface, and supports narrower article-first layout below that breakpoint. Reader pages have no command strip above the article. Reader commands live in the left course rail. Article pages may show reader breadcrumbs with the course home, ancestor pages, and current page generated from navigation data. Reader navigation links — breadcrumbs and the left-rail course-home control — are deployment-neutral static links and must not expose authored source paths.

At structural reader widths, the left course rail is `256px through 1311px` and `288px from 1312px` when expanded, with a fixed `48px` structural mini rail when collapsed. Phone-sized layouts use a `256px phone drawer`. Its fixed 48px header presents `Course map`, an explicit `Hide map` Map icon control, and a course-home action only when the course has an index root; all reader navigation links remain deployment-neutral static links and must not expose authored source paths. The central navigation is the one central native vertical scroll owner. It contains six two-column course actions for Search, Graph, Practice, Tasks, Calendar, and Context, followed by a locally filterable hierarchical map and its course tree. Course Search opens the generated Search workspace; the local Content filter narrows only rendered map labels. Its fixed footer contains structural page position and two fixed-footer comfort controls for Text size and OpenDyslexic. The rail renders no separate workspace section, no visible Current, All, Scan, or Less map action buttons, no inline course query, and no reader focus controls. The course map is generated from current navigation data, may show generated structural sequence numbers, may auto-orient the current page into the visible map region after load, and exposes per-branch disclosure controls for hierarchy scanning. Branch collapse is reader-local orientation state: course-scoped sessionStorage under `raya:course-map-branches:v1:<course_id>` may restore collapsed course-map branches across refresh and same-tab page navigation, but this state must not become durable progress, mastery, recommendations, analytics, source data, generated artifact data, localStorage, cookies, network state, or cross-tab memory. Workspace handoffs in the course-action rows may show static structural labels and may include page-focused Search, Graph, Practice, Tasks, or Calendar links when current artifact data supports those links. It does not collapse on hover; readers at the approved `894px+` geometry can collapse it through an explicit click control, and keyboard users can close it with Escape. From `640px` upward, collapsed structural mode reserves the 48px mini rail with course-home when available, an `Expand course map` control, and the two comfort controls; expanded content is inert, removed from keyboard navigation, and hidden from assistive navigation until restored.

Each branch row gives the chevron a separate disclosure control; its title remains the ordinary static link for navigation. Direct disclosure intent is distinct from current-path visibility: a protected same-parent accordion permits only one eligible expanded sibling while preserving the current path, and a reader may explicitly collapse a current-path ancestor without creating learner state. Filter and restoration visibility are temporary effective states and must not replace the saved branch preference. The tree uses the shared decorative chevron icon; generated structural numbers belong with the title link when they are needed for authored course order.

At every structural width, both the expanded rail and the reserved mini rail are pinned at full viewport height, with square structural geometry and the shell reserving `256px through 1311px` or `288px from 1312px` when expanded, or the fixed `48px` mini-rail width when collapsed. The fixed header and footer stay outside the central navigation scroller; the central navigation remains the only course-rail vertical scroll owner. With JavaScript unavailable, no-script navigation renders the rail in normal flow before the article, keeps static course links and the current path reachable, and hides disclosure, filter, drawer, comfort, and other enhancement-only controls.

Search, Graph, Practice, Tasks, and Calendar use one persistent Course map with the same local shell resources as reader pages. Every map link is a generated relative link from the workspace output path. The active workspace tile is the only current map link; no course-tree link is current, and reader-only Context is absent. Workspace filters and optional `?page=<page-id>` focus are volatile presentation state: focus may orient a non-current tree node while the workspace keeps its main-content focused-page strip. Workspace map interactions must not fetch external resources or write learner state, source, artifacts, browser preferences, or shell state.

The shell may use coordinated, reduced-motion-aware visual transitions for explicit map and context state changes so the reader perceives one continuous workspace; these transitions are display state only and must not infer progress or hide accessible content outside the documented collapsed desktop states. On phone-sized layouts, the course map may open as a non-persistent modal drawer with visible chrome, a close button, backdrop and Escape close paths, focus containment, background inertness, and temporary background scroll lock. The drawer chrome may include the course-home action ordered before the close button. The closed drawer is non-persistent, inert, hidden from assistive navigation, and must not hide the article or right learning rail from normal reading. Orientation, workspace links, drawer state, drawer scroll lock, filter text, focus, scroll position, and active content context are non-persistent UI state. Same-tab sessionStorage may restore only course-scoped collapsed course-map branch identifiers and the explicit left/right structural rail display pair. The versioned structural rail key is `raya:reader-shell:v1:<course_id>` and the branch key is `raya:course-map-branches:v1:<course_id>`; validated `course_id` isolates courses that share an origin. An opener-created or duplicated browsing context may receive the browser-provided initial sessionStorage copy, but later mutations remain tab-isolated, and an independently created tab starts with its own state. Drawer, filter, focus, scroll, active-context, progress, mastery, recommendation, and personalization state remains non-persistent. The accepted session state must not become analytics, answers, source data, generated artifact data, localStorage, cookies, network state, or cross-tab synchronization. Reader pages may persist only accepted comfort keys such as `raya:open-dyslexic` and `raya:text-size` in local storage. The right learning rail collapse is available only when explicit collapse controls are visible; hidden or collapsed rail content must be inert, removed from keyboard navigation, and hidden from assistive navigation until restored. Phone layouts keep the rail body visually and accessibly available when collapse controls are hidden, and Escape must not create an inert hidden rail state there. The shell may show structural page position such as `Page N of M`; this is course structure, not personal progress. The article may also end with larger Previous/Next sequence cards generated from the same ordered navigation data so students have a clear static reading path after finishing the page.

## Static Renderer Status

| Capability | Status | Static renderer behavior |
| --- | --- | --- |
| Course map and reading context | `current` | Render an expanded course rail of 256px through 1311px and 288px from 1312px, with a fixed 48px header, one central native vertical scroll owner, and a fixed 48px footer. The header presents `Course map`, an explicit `Hide map` icon control, and a course-home action only when an index root exists. The central navigation contains six two-column course actions for Search, Graph, Practice, Tasks, Calendar, and Context, then the locally filterable hierarchical map and scrollable course tree. The footer presents structural page position and two fixed-footer comfort controls for Text size and OpenDyslexic. Search is a static handoff to its generated workspace; the local Content filter only narrows rendered map labels. Render the hierarchical map from current navigation data, expanded by default when the approved `894px+` reader geometry is active and no same-tab shell state exists, able to show structural sequence numbers, auto-orient the current page into view, expose per-branch disclosure controls, and restore collapsed branch identifiers and explicit course-map expanded/collapsed state from course-scoped sessionStorage across refresh and same-tab page navigation. At `640px` and wider, collapse into a reserved 48px structural mini rail with course-home when available, `Expand course map`, Text size, and OpenDyslexic controls; narrower article-first layouts remain primary below that breakpoint. Phone-sized layouts use a 256px phone drawer. |
| Main article | `current` | Render the authored lesson as the primary continuous reading surface. When the article starts with an authored `h1`, that title is the lesson orientation anchor and the compact Page brief from public page metadata appears immediately after it. When there is no leading authored `h1`, the Page brief remains near the start before authored content. The article then continues with authored content, build-time MathJax, numbered objects, spoiler-safe static environments, callouts, tables, code, local assets, optional Page connections from explicit content-link graph context with native page previews, and article-end Previous/Next sequence cards from generated course order. |
| Right learning rail | `current` | Render current article section and page contents first when generated heading anchors exist, followed by reading flow, normalized summary/status, optional authored estimated time or computed estimated read time, tags, stable-ID prerequisites, static graph relationship summaries for explicit graph link context with compact direction and relationship-kind labels, native page previews, graph-focus links, and previous/next links from current artifact data. Desktop and medium-width reader shells may collapse the rail through explicit controls in the left course rail and may restore explicit expanded/collapsed state from same-tab sessionStorage; phone-sized layouts keep the rail body expanded for visual and accessibility parity. |
| Reader controls | `current` | Use local OpenDyslexic resources, keyboard-reachable footer and mini-rail controls, a static Search handoff, volatile active content context in the desktop and medium-width right rail, copyable fenced code blocks, and previous/next page keyboard navigation from generated sequence links. Text size applies only to the authored article. |
| Print/PDF handouts | `current` | Render print media as a static handout view that hides interactive chrome, keeps article content, math, code, tables, official practice, numbered objects, and support disclosures readable, and uses no external services or learner state. |
| Local course search | `current` | Render a static search workspace from generated page metadata, public rendered article prose, and generated public section/object anchors, using local JavaScript, approximate matching, optional URL-only exact page focus such as `?page=<page-id>`, keyboard, hover, and focus result inspection, control/results/context panels, deployment-neutral page links, section subresult links, and graph-focus links generated from stable page IDs. |
| Discovery workspace chrome | `current` | Render the persistent Course map and its local shell resources on generated Search, Graph, Practice, Tasks, and Calendar surfaces. Generate course-home, tree, and workspace links relative to the workspace output path; mark only the active workspace tile current; omit reader-only Context; preserve volatile workspace controls, filters, results, context regions, and focused-page strips; and do not fetch external resources or write learner, source, artifact, or preference state. |
| Official practice section | `current` | Render page-level official cards, prompts, quizzes, and generic official object fields from colocated `_official/` data on the owning page as a static `Official practice` section, using escaped text and native reveal controls where appropriate. Multiple-choice quiz objects may add page-local answer buttons, feedback, and reset controls over already rendered option data while preserving the native answer reveal as a no-JavaScript fallback. This is transient reader interaction only, not scoring, submission, attempts, progress, mastery, storage, network fetching, or browser-side rendering. |
| Official Practice workspace | `current` | Render a generated static discovery workspace at `_raya/practice/index.html` over already accepted official objects from `data/official.json` and page-owned `_official/` source objects, with local filters including approximate text matching over public fields, keyboard, hover, and focus object inspection, control/results/context panels, local links back to owning page anchors, graph focus links, and optional URL-only page focus such as `?page=<page-id>` from Search or Graph handoffs. |
| Official Tasks workspace | `current` | Render a generated static planning workspace at `_raya/tasks/index.html` over accepted official assignments, exams, projects, and tasks, with manifest-declared `data/tasks.json`, local filtering/sorting including approximate text matching over public fields, keyboard, hover, and focus task inspection, owning page anchors, and graph focus links. |
| Calendar | `current` | Render a generated static agenda and month surface from manifest-declared `data/calendar.json` inside the persistent Course map and its local shell resources, with local view, month, event-kind, and task-type controls, owning-page anchors, graph-focus links, optional URL-only page focus, and Clear/Escape reset. Agenda is the enhanced default on narrow screens. Month-day controls open an accessible day-detail dialog. Its visible name is `Calendar`; `/_raya/schedule/` is a compatibility URL only. |
| Checkpoints and goals as metadata | `planned` | Require a future source-contract change; do not infer from prose. |
| Related practice index | `planned` | Requires accepted source/artifact data. |
| Personal progress, analytics, adaptive review, spaced queues | `future` | Requires dynamic study state outside the static renderer. |

## Current Responsibilities

The static renderer may present left-rail reader commands, course map navigation, article breadcrumbs, the main article, and the right learning rail as reader-facing regions. These regions should be stable across desktop and mobile layouts even when the visual skin changes.

The main article owns authored teaching content. When the article starts with an authored `h1`, that title should appear before the compact Page brief so the lesson title remains the first primary article orientation anchor. Immediately after that title, the article may show a compact Page brief from public page metadata. When the article has no leading authored `h1`, the Page brief remains near the start before authored content as fallback orientation. The Page brief may include summary, normalized status, structural page position, optional authored estimated time or computed estimated read time, tags, resolved prerequisites, explicit graph-link counts, and accepted official-practice counts when those data exist. Authored `estimated_time` takes precedence; when it is absent, the renderer may compute an approximate `Estimated read time` from public rendered article text during build. The Page brief is first-screen scanning support over current artifact data; it is not a recommendation, progress marker, mastery signal, grading state, or personalized next step. The article may include build-time MathJax, numbered objects, static environments, callouts, tables, code, local assets, generated section landing cards, and links rewritten through current Raya rules. Generated section landing cards come from current child pages, page summaries, estimated time, and authored study-object counts; they are course structure, not recommendations, completion, mastery, or personal progress. Proof static environments remain expanded as part of the reasoning flow. Optional support environments such as hints, solutions, and answers render as native closed disclosures by default so learners can reveal support intentionally without the static page storing progress, submitting answers, or contacting a service. When explicit outgoing or incoming content-link graph context exists for the page, the article may end with a Page connections block that shows static counts, linked pages, graph-focus links, and native previews with public linked-page summary, status, explicit relationship kind and direction, and explicit relationship counts when that generated metadata exists. The article may also end with larger Previous/Next sequence cards from generated navigation so readers can move through the ordered material after finishing a page. These cards are static course-order links, not recommendations, completion signals, or personal next steps. Generated article blocks must not expose source paths, private support paths, external requests, storage calls, or inferred study guidance.

The official practice section is reader-facing convenience over accepted course source and artifact data, not canonical authority. Canonical official practice remains the authored course files under colocated `_official/`; machine-readable authority remains manifest-declared data such as `data/official.json` and `manifest.json`. Static pages may render the owning page's official cards, prompts, quizzes, and generic official object fields as escaped text inside an `Official practice` section. Prompts, answers, explanations, choices, and other revealable support may use native `<details>` controls so students can intentionally open them. This section must not render private source paths or support paths, must not scrape prose to invent practice, and must not turn official objects into scoring, grading, submissions, attempts, progress, mastery, recommendations, backend calls, browser-side fetching, localStorage/sessionStorage, external/CDN renderer requests, or browser-side MathJax conversion.

The Official Practice workspace is a generated static discovery surface for accepted official objects across the course. It reads manifest-declared `data/official.json` and page-owned `_official/` objects during build, then publishes `_raya/practice/index.html` with a local script and an embedded public payload for static filtering and navigation. It may list accepted cards, prompts, quizzes, tasks, and generic official objects with public page title, object type, stable ID, label, owning page link, owning page anchor such as `#raya-official-<id>`, graph focus link when generated graph context exists, and a context panel derived from the active or first visible accepted object. Its text filter may use approximate matching over that public payload and visible object text so small spelling mistakes still find likely public object fields; this is local matching, not ranking, personalization, or recommendation. Search and Graph handoff links may include a non-persistent `?page=<page-id>` query so the workspace initially shows accepted objects owned by that page. Clear and Escape must return the workspace to all visible accepted objects without writing browser storage. The active object may be selected transiently through keyboard movement, pointer hover, or focus on an existing object link. The workspace is not a second authority surface and must link students back to the owning page for context.

The Practice workspace must not expose private source paths, `_official/` paths, support paths, answer-only hidden duplicates, artifact internals, cache keys, or source hashes. It must not fetch data at runtime, load external scripts or renderers, persist state, score answers, collect attempts, submit work, grade, estimate progress or mastery, recommend what to do next, adapt to a learner, or store personal practice state. Revealed support remains ordinary static content or native disclosure behavior from accepted official objects, not a submission or tracking workflow.

The Official Tasks workspace is a generated static planning surface for accepted official objects whose type is `assignment`, `exam`, `project`, or `task`. It reads accepted `_official/` source objects during build, writes manifest-declared `data/tasks.json`, and publishes `_raya/tasks/index.html` with a local script and an embedded public payload. It may list stable object ID, type label, authority, owning page title, owning page anchor such as `#raya-official-<id>`, graph focus link, title, preview, and explicit public planning fields such as `content.due`, `content.available`, `content.points`, `content.weight`, `content.status`, and `content.tags`. It may filter by text and type, including approximate text matching over public task fields and visible task text, sort by course order, due date, or type, and update a transient context panel through keyboard movement, pointer hover, or focus on a visible task. Search and Graph handoff links may include a non-persistent `?page=<page-id>` query so the workspace initially shows accepted task-family objects owned by that page. Clear and Escape must return the workspace to all visible accepted task-family objects without writing browser storage. It is a planning view over accepted course source, not a submission, grading, calendar synchronization, recommendation, progress, or mastery surface.

The Tasks workspace and `data/tasks.json` must not expose private source paths, `_official/` paths, support paths, answer-only hidden duplicates, artifact internals, cache keys, source hashes, quiz correctness, solutions, reviewed-output state, personal due-state calculations, learner progress, or recommendation language. They must not fetch data at runtime, load external scripts or renderers, persist state, submit work, grade, score, collect attempts, infer completion, adapt to a learner, contact a backend, or store personal task state.

Calendar is a generated static agenda and month view over manifest-declared
`data/calendar.json`: explicit official sessions, holidays, cancellations, and
milestones plus due and available dates derived from valid official task-family
objects. It uses the one course IANA timezone to interpret civil dates. The
visible surface is always `Calendar`; `/_raya/schedule/` is a compatibility URL
only. Calendar uses the persistent Course map and the same local shell resources
as the other generated workspaces. It may filter locally by event kind and task
type, link to owning page anchors and graph focus, and accept non-persistent
`?page=<page-id>` focus. Agenda and month controls, filters, focus, and
Clear/Escape reset are temporary display state. Calendar is not source
authority, a machine calendar feed, a reminder,
synchronization, submission, grading, progress, mastery, recommendation, or
personal-state surface. It must not parse prose for dates, fetch data at
runtime, make network requests, load external resources, persist state, or
expose private paths or hidden answer/support content. It performs no network
requests. Agenda is the enhanced default on narrow screens. In the Month view,
up to two visible events per day appear as ordinary keyboard-reachable event-chip
buttons that open an accessible day-detail dialog; any additional visible events
are represented by one `+N` overflow button that opens the same dialog. At narrow
widths, month cells
suppress event-chip titles while retaining their kind labels and accessible
names. The dialog places focus on its close control when opened, supports
Escape dismissal, and restores focus to the invoking event-chip or overflow
button when closed. It presents only the events visible under the current local
filters and retains the same local owning-page and graph-focus links; it neither
fetches nor persists detail state.

The right learning rail owns compact page context. It is expanded by default when the approved `894px+` reader geometry is active and may collapse through an explicit rail control or the left course rail Context command into its explicit Context expansion control without reserving a shell grid column. Collapsed rail content must be hidden from keyboard and screen-reader navigation. When the layout is phone-sized and the collapse controls are not visible, the rail must remain visually expanded and screen-reader reachable; responsive changes from the expanded geometry back to a narrower layout must restore that accessible expanded state. When generated heading anchors exist, current-section context and page contents appear before general page metadata so the rail works as a dedicated section-orientation surface first. It may also show reading flow, normalized `summary` and `status`, optional authored estimated time or computed estimated read time, tags when accepted data exists, stable-ID prerequisites when they resolve to current pages, static Connections summaries for explicit incoming and outgoing content links from generated graph data, native previews for linked pages using public generated metadata and explicit relationship kind and direction, graph-focus links for those explicit relationships, and previous/next links from generated navigation. Current-section context, estimated read time, and right-rail Context behavior are structural reading orientation only; they must not become reading percentage, completion, mastery, recommendation, or personal progress state.

Explicit graph link context means relationships already present in source links,
resolved course-local wikilinks, stable IDs, or prerequisite metadata. It does
not mean inferred recommendations, related practice, personal next steps, or
mastery guidance.

The static graph page is a reader-facing view of generated artifact graph data.
It may provide grouped local controls for `Find pages`, `Relationship filters`,
`Canvas view`, `Move canvas`, and `Workspace`; local fuzzy search,
deterministic layouts, group filters,
selected-page details, incoming/outgoing link lists, a static legend/help panel,
selected-page neighborhood summaries, selected-page relationship walkthroughs
that group explicit edges by kind and direction with local page links and
transient graph-focus controls, connected-page visual states, transient
page focus from generated URL context, structural group color, bounded node
size derived from static link degree, source-group edge colors,
contextual SVG label reveal that keeps high-context labels visible and
declutters low-context labels without removing page links or accessibility
labels,
relationship-kind edge line patterns for generated `navigation`, `parent`,
`content`, and `prerequisite` edges,
transient search spotlighting over matched pages and directly connected
context, transient graph-search keyboard movement over visible page results
with Enter-to-open active result behavior, transient hover/focus spotlight
dimming, hover/focus inspection text, keyboard inspection parity,
an optional bounded graph preview bubble for SVG graph node hover/focus using
only already loaded public page metadata,
transient SVG relationship inspection through keyboard-focusable and
pointer-inspectable edge hit targets that name source page, target page,
relationship kind, and source-to-target direction using already loaded graph
data, with actions to select either endpoint or focus that relationship kind
through the existing graph detail relationship controls,
single-click selection/inspection for SVG graph page links, double-click
page opening for SVG graph page links, keyboard Enter-to-open behavior on
focused SVG graph page links,
public selected-page discovery card metadata, course-order
Previous/Selected/Next links inside the selected-page detail card, a primary
selected-page open link, local Tasks and Calendar handoff links when the
selected page owns accepted public task-family metadata,
non-persistent selected-neighborhood focus mode,
detail-list controls that select connected pages inside the graph workspace without replacing normal page links,
non-persistent SVG viewport controls such as Zoom in, Zoom
out, explicit direction-symbol pan buttons, focused canvas Arrow-key panning,
pointer drag panning, Fit,
Fit selection, Reset view, and a non-persistent graph focus mode that collapses
side panels into operable rails, and URL-addressable
static graph state for selected page, search query, layout, visible groups,
visible edge kinds, selected-neighborhood focus, expanded mode, and panel state.
The graph may show a compact student-facing orientation band with visible page
and relationship counts, layout, selected page, URL page focus, search, filters,
selected-neighborhood focus state, and local actions for the selected page. It
may also show a compact state readout and share URL for debugging and
orientation over the already loaded static artifact data inside an intentional
native disclosure. The graph may show compact first-viewport reading keys for
page nodes, arrows, selection, and filters as structural interpretation cues.
Selected-page incoming/outgoing detail lists must use the
same explicit generated edge kinds as relationship chips and walkthroughs, so
visible lists, counts, and walkthrough cards do not describe different graph
subsets. Desktop
page-focused graph handoffs such as `?page=<page-id>` must first-paint visible
selected graph content in the graph canvas when graph data exists; graph canvas
height should remain bounded relative to the viewport so side-panel height
cannot stretch the canvas and hide the graph below the first visible area. Label
visibility, graph color, node size, edge style, spotlighting, and layout
position are readability cues for current graph structure only; they are not
progress, authority, recommendation rank, importance rank, mastery, or
completion signals. The orientation band is structural graph context only and
must not become progress, mastery, ranking, recommendation, or personalization.
Pan, Zoom in, Zoom out, Fit, Fit selection, Reset view, and minimap activation
change only the visual graph viewport; they must not clear search, filters,
selected-page details, URL state, storage, or authored graph data. Fit selection may frame the
selected page and visible directly connected graph context, and may scroll the
graph canvas into view as a local viewport affordance, but it must not change
graph data, selection, filters, URL state, storage, progress, ranking,
recommendation, or mastery semantics. Desktop mouse users may temporarily reposition visible SVG graph nodes to untangle the current view; this updates
only local node and visible edge geometry, must stay within graph bounds, must
reset through `Reset graph` or layout changes, must not persist to browser
storage, must not mutate URL state, graph data, or authored relationships, and
must not imply recommendation, ranking, progress, mastery, or authority. The
default `Connections` layout may arrange visible pages by normalized
explicit graph relationships and course order so students can read link flow.
`Topology` may place visible pages by explicit generated graph relationships
using a deterministic local layout over the current visible edge set, while
`Cluster` may group visible pages by generated course group, and `Map`,
`Radial`, and `List` remain alternate local views. Layout position is only a
readability cue over generated graph data, not recommendation rank, progress,
importance, mastery, or authority. Selected-neighborhood focus may narrow visible graph and list nodes to the selected page plus directly connected pages from explicit generated edges, but it remains transient UI state and must always allow return to the full graph. Selected-page relationship chips may focus the already rendered relationship walkthrough, selected-page incoming/outgoing lists, and visible selected-page graph edges by explicit relationship kind and direction. Global Relationship filters may mark selected-page chip kinds as currently hidden. That focus remains local UI state and must not persist to browser storage, mutate URL/share state, fetch data, change authored graph data, or imply recommendation, ranking, mastery, progress, or authority. URL graph state is shareable page state, not browser storage or learner state. It must not fetch graph data at runtime, load external graph
libraries, persist graph state in browser storage, infer
recommendations, or present graph position as personal progress.
The graph preview bubble is transient spatial context only; it must not fetch
data, persist state, expose private source surfaces, or imply progress,
mastery, ranking, recommendation, personalization, or authority.

Course skin profiles may optionally define `tokens.graph.group_1` through
`tokens.graph.group_8` as validated six-digit hex colors. When present, those
tokens drive generated `--raya-graph-group-*` variables for graph group chips,
legend swatches, SVG nodes, SVG edges, and SVG arrow markers. When omitted, the
renderer keeps its semantic-color fallback palette. Graph palette tokens are
static course visual identity and readability cues only; they must not encode
progress, ranking, recommendation, mastery, authority, hidden graph data,
browser-side skin resolution, external CSS, external fonts, or arbitrary CSS.

Generated Search, Graph, Practice, Tasks, and Calendar pages use the persistent Course map and local shell resources to show the current course title, identify the active workspace, link back to the course, link between workspaces, and expose local volatile text-size and `OpenDyslexic` controls. Search, Practice, and Tasks may also use static workspace regions for controls, results, and public context summaries so desktop readers can scan without leaving the page; Calendar instead keeps its dedicated agenda, month grid, and filter controls. Search, Practice, and Tasks text filters may use local approximate matching over public payload fields and visible text to help find likely public results despite small spelling mistakes. Search result context, Practice object context, and Tasks object context may follow transient active cards selected by keyboard movement, pointer hover, or focus on existing links. Those context panels may expose static action links generated from the same public payload, such as the owning page, graph focus, and sibling workspace handoffs when the active public item supports them. When Search, Practice, Tasks, or Calendar opens from a valid `?page=<page-id>` handoff, the control region may show a compact visible notice naming the focused public page, the current visible count, and the Clear reset path. That notice is structural URL context only and must hide when no valid page focus exists or after Clear/Escape restores the full static workspace. The workspace shell, active contexts where implemented, context actions, page-focus notice, and approximate matching are static page structure. Workspace comfort controls are volatile and must not write `raya:open-dyslexic`, `raya:text-size`, shell state, search, graph, practice, task, or Calendar state. These workspaces must load only local shell resources, must not show a course map control without a course map, must not fetch external resources, and must not turn structural workspace labels into progress, ranking, or recommendation language.

Generated Search and Graph cards/details may show public page metadata from generated artifact data: page title, navigation title, stable ID, hierarchy label, status, summary, tags, previous/next course-order links, explicit incoming/outgoing/connected graph counts, accepted official object counts, and local links to Search, Graph, Practice, Tasks, Calendar, and owning pages. Graph selected-page details may include a relationship walkthrough that explains explicit generated relationship kinds and directions using structural language and existing local page/focus controls. Graph selected-page details may also show generated public section/object anchor jump links for the selected page, including numbered objects and proofs, when those anchors already exist in the rendered public article/search surface. Search handoff links may include `?page=<page-id>` to narrow visible Search results to the exact public page ID until Clear or Escape restores all visible results. Practice handoff links may include `?page=<page-id>` only when the page owns accepted official objects. Graph selected-page details may show Tasks handoff links only when the selected page owns accepted public task-family objects, and Calendar handoff links only when those accepted public task-family objects have authored `due` or `available` metadata. These are structural discovery cues, not recommendations, progress, mastery, importance, ranking, or related-practice inference. Official object counts may be displayed only as counts of accepted source objects owned by the page or its generated structural scope. They must not imply recommended practice or expose answer/support content.

Reader controls may use local `OpenDyslexic` resources, a local text-size comfort preference, keyboard-reachable controls in the left course rail, a static Search handoff, same-tab desktop and medium-width structural rail display preferences, volatile active content context, copyable fenced code blocks, and previous/next page keyboard navigation from generated sequence links. They must work from static files and must not depend on fetch/XHR requests, accounts, a backend, CDN resources, external font requests, personal progress, adaptive recommendations, or browser-side MathJax conversion. Local storage may be used only for reader comfort preferences such as `raya:open-dyslexic` and `raya:text-size`; sessionStorage may be used only for `raya:course-map-branches:v1:<course_id>` course-scoped collapsed course-map branch identifiers and the `raya:reader-shell:v1:<course_id>` explicit structural rail display pair. Browser storage must not store drawer, filter, focus, scroll, active-context, course progress, answers, mastery, recommendations, personalization, analytics, graph state, skin authority, authored content, or any other shell or learner state.

Generated reader pages may include print media rules for static handouts and browser PDF export. Print mode may hide command bars, course maps, learning rails, workspace controls, inspectors, filters, and graph canvases while keeping the already rendered article, page brief, breadcrumbs, sequence links, official practice, numbered objects, static environments, callouts, tables, code, local images, and build-time MathJax readable. The local shell may temporarily open native support disclosures for printing and restore them afterward without persistence. Print handouts are generated artifact views, not source truth, grading, progress, mastery, recommendations, submissions, external requests, storage workflows, or browser-side rendering.

Local course search may expose generated page titles, navigation titles, stable IDs, summaries, status, hierarchy labels, tags, explicit link counts, official object counts, public rendered article prose, rendered page links, workspace handoff links, generated public section/object anchors, and graph-focus links generated from stable page IDs. It may write `data/search-index.json` as generated artifact data and may embed the same public records in the Search workspace. It may support approximate matching, exact URL-only page focus from `?page=<page-id>`, a visible page-focus notice for valid page handoffs, clear controls, keyboard movement over visible results, hover and focus inspection of visible results, transient query context from generated page links, public context summaries for visible results, public match snippets, section subresult links under page results, and static handoff from a result to the graph page focused on the same page. Exact page focus is structural URL state only; it may narrow visible Search results to the matching public page ID and must reset through Clear or Escape without writing browser storage. Section subresults are generated public anchors and snippets for scanning within a page; they are not separate page authority, recommendations, or progress markers. Search must not index MathJax CHTML internals, raw TeX, source paths, private support paths, artifact paths, cache keys, personal progress, answer/support-only content, related-practice inference, or recommendations into the student search surface.

## Planned Static Work

Checkpoints, goals, and related practice may become static metadata only after an accepted source-contract and artifact-contract change. Until then, authors may write checkpoint prompts and practice links as content, but the renderer must not treat prose as structured goals.

Related practice indexes need accepted source or artifact data. Public article search text must not be reused to invent goals, recommendations, or related practice.

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

Changes to the course shell, right learning rail, reader controls, official practice rendering, local assets, MathJax output, print handout behavior, or visual layout should include static-read-path and render-debug checks. Breadcrumb checks should cover accessible navigation markup, course-home and ancestor links, current-page marking, deployment-neutral relative URLs, no source/private paths, no external requests, and desktop/mobile no-overflow behavior. Rail home-control checks should cover the same: an accessible course-home link resolving to the course root, deployment-neutral relative URLs, no source/private paths, no external requests, omission when the course has no index root, and left/right rail header height parity. Rail checks should additionally cover separate chevron/link ownership, protected same-parent accordion behavior, current-path visibility and direct-collapse intent, full-height expanded and mini geometry, one central scroller, and no-script navigation with only static links reachable. Course-map titles must remain fully readable and wrap naturally without truncation in expanded, drawer, and no-script layouts. Page brief checks should cover public metadata only, escaped summary/status/tags, resolved prerequisite links, page-focused graph links, official-practice anchors, no source/private paths, no storage/fetch calls, no recommendation/progress/mastery wording, no learner-state wording, and desktop/mobile no-overflow behavior. Print checks should cover print media hiding of interactive chrome, visible article content, readable MathJax/code/tables/static environments, temporary non-persistent opening of support disclosures, no source/private paths, no external requests, no storage calls, and no browser-side MathJax conversion. Page-connection preview checks should cover public metadata only, escaped text, local page and graph links, native disclosure controls, no source/private paths, no storage/fetch calls, no recommendation/progress/mastery wording, and no external requests. Graph checks should cover desktop page-focused handoffs such as `?page=<page-id>` by asserting that the selected SVG node and at least one edge intersect the visible graph canvas on first paint, not only that SVG nodes exist in the DOM. Search workspace checks should cover `_raya/search/index.html`, local script only, generated `data/search-index.json`, public prose queries, public section/object subresult links, exact URL-only `?page=<page-id>` filtering, visible page-focus notice for valid handoffs, hidden notice for missing/invalid page focus, Clear/Escape reset to all visible results, no private source paths, no MathJax internals or raw TeX leakage, no answer/support-only content leakage, no storage/fetch calls, no external requests, and no learner-state language. Official practice checks should cover escaping, source path privacy, native reveal controls, no storage/fetch calls, no external renderer requests, and no browser-side MathJax conversion. Practice workspace checks should cover `_raya/practice/index.html`, local script only, links to owning page anchors, graph focus links, URL-only `?page=<page-id>` filtering from Search or Graph handoffs, visible page-focus notice for valid handoffs, hidden notice for missing/invalid page focus, Clear/Escape reset to all accepted objects, no private source paths, no answer-only hidden duplication, no storage/fetch calls, no external requests, and no learner-state language. Tasks workspace checks should cover `_raya/tasks/index.html`, local script only, accepted task-family objects, links to owning page anchors and graph focus links, URL-only `?page=<page-id>` filtering from Search or Graph handoffs, visible page-focus notice for valid handoffs, hidden notice for missing/invalid page focus, Clear/Escape reset to all accepted task-family objects, no private source paths, no storage/fetch calls, no external requests, no personal due-state language, and no learner-state language. Calendar workspace checks should cover `_raya/schedule/index.html`, local script only, inclusion of accepted task-family objects with authored `due` or `available`, exclusion of undated task objects, links to owning page anchors and graph focus links, URL-only `?page=<page-id>` filtering from Search or Graph handoffs, visible page-focus notice for valid handoffs, hidden notice for missing/invalid page focus, Clear/Escape reset to all dated task-family objects, no private source paths, no storage/fetch calls, no external requests, no personal due-state language, and no learner-state language. Use `scripts/check-render-debug.sh` for the focused render-fixture gate when browser-visible math, local resources, screenshots, external requests, or overflow can regress.

## Calendar Verification

Calendar verification additionally covers manifest-declared
`data/calendar.json`, the course IANA timezone, explicit official sessions,
holidays, cancellations, and milestones, and valid due/available task-family
dates derived into the same index without duplicate Calendar source entries.
Check agenda and month views, local filtering and reset behavior, no runtime
fetch or network requests, no browser storage, and no reminder, synchronization,
or personal-state claims. `/_raya/schedule/` remains a compatibility URL, not a
visible surface name.

## Rail Collapse Invariants

These four rules exist because the collapsed rail broke repeatedly when one
visual state was expressible in many places. Each is enforced by a guardrail
in `tests/e2e/test_rail_collapse_contract.py`.

1. **Geometry is single-sourced.** Every rail breakpoint lives in
   `packages/static/src/raya_static/shell_geometry.py` and reaches CSS and JS
   only through `__RAYA_*__` tokens. A literal `px` boundary **outside**
   `shell_geometry.py` — in a rail `@media` rule or a `matchMedia` string — is
   a defect, not a shortcut. Inside `shell_geometry.py` the literals are the
   single source, built from the Python ints.

2. **JS and CSS derive band membership from the same source.** Both read
   `matchMedia` against identical boundary strings. Deriving band membership
   from `innerWidth` is forbidden: on engines where the media-query width
   excludes a classic scrollbar the two disagree **permanently**, producing a
   rail whose state says "collapsed" while its body stays visible.

   Two caveats, both deliberate. The **prepaint read is provisional**:
   `shell-prepaint.js` runs before any stylesheet and before `<body>`
   (`builder.py:1023` vs `:1024-1029`), so no scrollbar exists yet and the
   query returns the no-scrollbar answer. Agreement is reached once
   `shell.js` runs and the MQ `change` listeners fire — so the guarantee is
   *eventual consistency*, not structural impossibility. And `rayaRailBands()`
   **forces the widest band while printing**, because viewport media features
   resolve against the page box (~700-760px), which would otherwise collapse
   both rails in the printout.

3. **Collapse state lives only on the root element.** It is written to
   `document.documentElement.dataset.rayaCourseMap` / `.rayaLearningRail` and
   nowhere else. Never mirror it onto a rail element or `main`. CSS reads it
   only via `html[data-raya-...]`.

4. **Collapsed appearance is defined in one region.** The
   "rail collapse: appearance (single source)" region owns the collapsed
   header/body hiding and the chip. Band-scoped fragments elsewhere are how
   the original drift happened.

Note that the transition channel (`data-raya-*-transition`) is a genuine
element-level attribute and is not a state mirror. Its ancestor-rooted
selectors are live during the 240 ms animation window: they keep the expand
chip painted and the header hidden while the rail animates. Removing them
makes the rail render empty mid-animation.
