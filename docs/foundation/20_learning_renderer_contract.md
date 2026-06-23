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

The current shell uses an expanded course map, rendered as an expanded hierarchical course map by default on desktop and browser load, keeps the article primary, and supports mobile article-first layout. The sticky command bar may show current reading context such as course title, page title, structural page position, and compact previous/next links. The course map is generated from current navigation data, can be filtered locally by rendered page labels, and may auto-orient the current page into the visible map region after load. It does not collapse on hover; readers can collapse it through an explicit click control, and keyboard users can close it with Escape. Collapsed mode becomes an operable compact map rail: visible rail items remain real navigation targets, not decorative markers. Course-map state, orientation, and filter text are non-persistent UI state. The shell may show structural page position such as `Page N of M`; this is course structure, not personal progress.

## Static Renderer Status

| Capability | Status | Static renderer behavior |
| --- | --- | --- |
| Course map and reading context | `current` | Render a hierarchical map from current navigation data, expanded by default when the shell script runs, locally filterable by page labels, able to auto-orient the current page into view, non-persistent, not hover-triggered, and collapsible through an explicit click control or Escape into an operable compact map rail. The sticky command bar may show static course/page title, structural page position, and compact previous/next links. |
| Main article | `current` | Render authored content, build-time MathJax, numbered objects, spoiler-safe static environments, callouts, tables, code, local assets, and optional Page connections from explicit content-link graph context. |
| Right learning rail | `current` | Render page contents, normalized summary/status, optional estimated time/tags, stable-ID prerequisites, static Connections summaries for explicit graph link context, graph-focus links, and previous/next links from current artifact data. |
| Reader controls | `current` | Use local OpenDyslexic resources, keyboard-reachable controls, copyable fenced code blocks, and previous/next page keyboard navigation from generated sequence links. |
| Local course search | `current` | Render a static search surface from generated page metadata only, using local JavaScript, approximate matching, keyboard result movement, and deployment-neutral page links. |
| Discovery workspace chrome | `current` | Render shared static course chrome on generated Search and Graph surfaces with a course link, cross-workspace links, local comfort controls, compact mobile layout, and no shell script dependency. |
| Checkpoints and goals as metadata | `planned` | Require a future source-contract change; do not infer from prose. |
| Related practice index | `planned` | Requires accepted source/artifact data. |
| Personal progress, analytics, adaptive review, spaced queues | `future` | Requires dynamic study state outside the static renderer. |

## Current Responsibilities

The static renderer may present command-bar reading context, course map navigation, the main article, and the right learning rail as reader-facing regions. These regions should be stable across desktop and mobile layouts even when the visual skin changes.

The main article owns authored teaching content. It may include build-time MathJax, numbered objects, static environments, callouts, tables, code, local assets, generated section landing cards, and links rewritten through current Raya rules. Generated section landing cards come from current child pages, page summaries, estimated time, and authored study-object counts; they are course structure, not recommendations, completion, mastery, or personal progress. Proof static environments remain expanded as part of the reasoning flow. Optional support environments such as hints, solutions, and answers render as native closed disclosures by default so learners can reveal support intentionally without the static page storing progress, submitting answers, or contacting a service. When explicit outgoing or incoming content-link graph context exists for the page, the article may end with a Page connections block that shows static counts, linked pages, and graph-focus links. This block is generated from current graph data only; it must not expose source paths, private support paths, external requests, storage calls, or inferred study guidance.

The right learning rail owns compact page context. It is expanded by default on desktop and may collapse through an explicit click control into an operable compact context tab. Collapsed rail content must be hidden from keyboard and screen-reader navigation. It may show page contents, normalized `summary` and `status`, optional estimated time and tags when accepted data exists, stable-ID prerequisites when they resolve to current pages, static Connections summaries for explicit incoming and outgoing content links from generated graph data, graph-focus links for those explicit relationships, and previous/next links from generated navigation.

Explicit graph link context means relationships already present in source links, stable IDs, or prerequisite metadata. It does not mean inferred recommendations, related practice, personal next steps, or mastery guidance.

The static graph page is a reader-facing view of generated artifact graph data.
It may provide local fuzzy search, deterministic layouts, group filters,
selected-page details, incoming/outgoing link lists, a static legend/help panel,
selected-page neighborhood summaries, connected-page visual states, transient
page focus from generated URL context, structural group color, bounded node
size derived from static link degree, hover/focus inspection text, keyboard
inspection parity, and a non-persistent expanded workspace mode. These visual
semantics are readability cues for current graph structure only; they are not
progress, authority, recommendation rank, importance rank, mastery, or
completion signals. It must not fetch graph data at runtime, load external graph
libraries, persist graph state, infer
recommendations, or present graph position as personal progress.

Generated Search and Graph pages may share discovery workspace chrome that shows the current course title, identifies the workspace, links back to the course, links between Search and Graph, and exposes local text-size and `OpenDyslexic` controls. This chrome is static page structure. It must not load the course shell script, show a course map control without a course map, store search or graph state, fetch external resources, or turn structural workspace labels into progress, ranking, or recommendation language.

Reader controls may use local `OpenDyslexic` resources, a local text-size comfort preference, keyboard-reachable controls, copyable fenced code blocks, and previous/next page keyboard navigation from generated sequence links. They must work from static files and must not depend on fetch/XHR requests, accounts, a backend, CDN resources, external font requests, personal progress, adaptive recommendations, or browser-side MathJax conversion. Local storage may be used only for reader comfort preferences such as font and text size; it must not store course progress, answers, mastery, recommendations, graph state, skin authority, or authored content.

Local course search may expose generated page titles, navigation titles, stable IDs, summaries, status, hierarchy labels, tags, and rendered page links. It may support approximate matching, clear controls, keyboard movement over visible results, and transient query context from generated page links. It must not scrape rendered prose, MathJax output, source paths, artifact paths, cache keys, personal progress, or inferred recommendations into the student search surface.

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
- no browser-side MathJax conversion;
- no external CSS, font, script, renderer, or CDN requests;
- no hidden schema change to distinguish raw `summary` or `status` presence in this loop.

These non-goals protect student trust. A static page may organize current data, but it must not pretend to know learner state or run a browser-only renderer.

## Verification

Changes to the course shell, right learning rail, reader controls, local assets, MathJax output, or visual layout should include static-read-path and render-debug checks. Use `scripts/check-render-debug.sh` for the focused render-fixture gate when browser-visible math, local resources, screenshots, external requests, or overflow can regress.
