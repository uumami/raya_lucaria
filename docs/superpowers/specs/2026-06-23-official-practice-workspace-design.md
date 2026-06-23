---
id: superpowers-official-practice-workspace-design
title: Official Practice Workspace Design
summary: Static discovery workspace for accepted official learning objects.
status: draft
---
# Official Practice Workspace Design

## Goal

Add a generated static workspace where students can scan official cards,
prompts, quizzes, tasks, assignments, exams, projects, and generic official
objects across the current course artifact.

## Legacy UX To Salvage

The legacy `main` branch had useful task-list and calendar surfaces: compact
cards, type accents, metadata badges, grouped course work, and empty-state
messages. It also had interactive quiz feedback. The current framework should
salvage the scannable work-list pattern, not the old Eleventy architecture,
date-overdue logic, inferred metadata, or browser-side scoring.

## Current Authority

The workspace is generated from accepted official learning-object data only.
Canonical source remains colocated `_official/` YAML and the machine-readable
artifact authority remains `data/official.json` plus `manifest.json`. The
workspace is a reader-facing discovery view, not a new source contract.

## Behavior

Generate `artifact/site/_raya/practice/index.html` when a course builds. The
page should use the same discovery chrome as Search and Graph, with local links
back to the course and across discovery workspaces.

The workspace should show:

- a compact summary of official object counts by type;
- filter chips for object type;
- a local search input over object ID, type, owning page title, and visible
  prompt/front/title text;
- grouped cards by owning page, in course order;
- each card's type, authority, owning page, stable object ID, compact visible
  text, and an `Open page` link to the owning page anchor such as
  `../../unit/topic/index.html#raya-official-card-id`;
- a `View page in graph` link when the owning page has a generated graph focus
  URL.

Cards may show prompt/front/question/title text, but must not duplicate hidden
answers, quiz correctness, solutions, source paths, `_official/` paths, or raw
object YAML. If a type has no compact visible text, show a neutral fallback such
as the object ID and owning page.

## Non-Goals

- no scoring, attempts, grading, submissions, overdue labels, completion,
  progress, mastery, ranking, or recommendations;
- no inferred practice from prose, numbered objects, tags, headings, or links;
- no browser-side fetching or hydration from `data/official.json`;
- no external scripts, fonts, renderers, or CDN requests;
- no personal storage for query, filters, answers, graph state, or progress;
- no schema change for assignments, due dates, or calendars in this loop.

## Implementation Shape

Add a small local `practice.js` resource similar to `search.js`. The script may
filter pre-rendered list items and update an `aria-live` status message. It must
not fetch, store, submit, score, or infer anything.

Add builder helpers near the current Search and Graph surfaces:

- `STATIC_PRACTICE_PATH = _raya/practice/index.html`;
- `_write_practice_surface(...)`;
- `_render_practice_surface(...)`;
- `_browser_practice_payload(...)` if the local script needs embedded metadata.

Keep the payload public and minimal. Allowed fields are object ID, type,
authority, owning page ID/title/url/graph URL, source order, and compact visible
text derived from public official content. Do not include `source_path`, raw
scope paths, answer fields, solution fields, cache keys, artifact paths, or
private support paths.

## Documentation

Update the learning renderer foundation contract and English/Spanish student
and agent guides. The docs must explain that this is a static discovery view for
official course-provided practice, not a personal study dashboard or progress
surface.

## Verification

Contract tests should assert generated workspace HTML, embedded public payload,
relative page-anchor links, graph-focus links, escaped official text, type
counts, no private paths, no answers/correct options, no external URLs, and no
storage/fetch tokens.

Browser tests should load the workspace through `raya preview`, check desktop
and mobile no-overflow, use search and type filters, navigate to an owning page
anchor, navigate to a graph-focused page, and confirm no post-load external
requests.
