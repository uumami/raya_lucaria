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

The current shell uses an expanded course map by default on desktop and browser load, keeps the article primary, and supports mobile article-first layout. The course map does not collapse on hover; readers can collapse it through an explicit click control, and keyboard users can close it with Escape. Collapsed mode becomes an operable compact map rail: visible rail items remain real navigation targets, not decorative markers. Course-map state is non-persistent UI state. The shell may show structural page position such as `Page N of M`; this is course structure, not personal progress.

## Static Renderer Status

| Capability | Status | Static renderer behavior |
| --- | --- | --- |
| Course map | `current` | Render from current navigation data, expanded by default when the shell script runs, non-persistent, not hover-triggered, and collapsible through an explicit click control or Escape into an operable compact map rail. |
| Main article | `current` | Render authored content, build-time MathJax, numbered objects, static environments, callouts, tables, code, and local assets. |
| Right learning rail | `current` | Render page contents, normalized summary/status, optional estimated time/tags, stable-ID prerequisites, and previous/next links from current artifact data. |
| Reader controls | `current` | Use local OpenDyslexic resources and keyboard-reachable controls. |
| Checkpoints and goals as metadata | `planned` | Require a future source-contract change; do not infer from prose. |
| Related practice index | `planned` | Requires accepted source/artifact data. |
| Personal progress, analytics, adaptive review, spaced queues | `future` | Requires dynamic study state outside the static renderer. |

## Current Responsibilities

The static renderer may present course map navigation, the main article, and the right learning rail as reader-facing regions. These regions should be stable across desktop and mobile layouts even when the visual skin changes.

The main article owns authored teaching content. It may include build-time MathJax, numbered objects, static environments, callouts, tables, code, local assets, and links rewritten through current Raya rules.

The right learning rail owns compact page context. It may show page contents, normalized `summary` and `status`, optional estimated time and tags when accepted data exists, stable-ID prerequisites when they resolve to current pages, and previous/next links from generated navigation.

Reader controls may use local `OpenDyslexic` resources and keyboard-reachable controls. They must work from static files and must not depend on accounts, a backend, CDN resources, or external font requests.

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
