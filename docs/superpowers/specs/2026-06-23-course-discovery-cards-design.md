---
title: Course Discovery Cards Design
status: draft
date: 2026-06-23
workflow: superpowers
---

# Course Discovery Cards Design

## Goal

Improve the generated Search and Graph workspaces so they feel like one course discovery system, using denser public page cards inspired by the legacy `main` branch task/list UX while preserving the reset framework's static, manifest-centered contracts.

The feature should help readers answer:

- what page is this;
- where does it sit in the course;
- what explicit course links connect it to other pages;
- what accepted official practice objects are under it;
- how do I open the page, focus it in the graph, or inspect accepted practice.

It must not infer related practice, goals, priorities, importance, progress, mastery, recommendations, or workload from prose.

## Legacy UX To Salvage

The legacy task-list and calendar layouts used dense cards, compact metadata rows, type badges, and scannable status/count fields. That pattern is useful here, but the data source and meaning must change.

Salvage:

- compact cards with a title, short summary, metadata row, and action links;
- pill/badge counts for object types and explicit links;
- stable rows that are easy to scan at desktop width and still fit on mobile;
- empty states that are plain and useful.

Reject:

- date-relative overdue labels;
- inferred task discovery from prose;
- scoring or quiz checking;
- Pagefind or any runtime search index;
- storage-backed discovery state;
- any language that frames static structure as a recommendation.

## Current Authority

The static renderer may already expose generated page titles, nav titles, stable IDs, summaries, status, hierarchy labels, tags, rendered page links, graph-focus links, and explicit graph relationship counts. It already computes official object counts for generated section indexes.

This feature should reuse current in-memory build data:

- `ContentModel.pages` and generated navigation order;
- `graph_index` nodes, edges, groups, and backlinks;
- accepted official object counts from `_official_counts`;
- existing relative URL helpers;
- existing Search, Graph, and Practice workspace chrome.

No source contract or artifact schema change is required in this slice. Generated browser payloads may add public fields because they are views over already accepted artifact data.

## Search Workspace Behavior

Search results should become richer discovery cards.

Each result card may show:

- page title and summary;
- status, hierarchy label, tags, and stable ID;
- official object counts by type when non-empty, such as `Cards: 1` or `Quizzes: 2`;
- explicit link metrics, such as outgoing, incoming, and connected page counts;
- action links:
  - `Open page`;
  - `View in graph`;
  - `Open practice` when the page has accepted official objects.

Search filtering remains local and metadata-only. The searchable text may include the new public fields, but it must not include source paths, raw official object answers, hidden support fields, artifact internals, or rendered prose scraping.

Keyboard behavior must remain: ArrowUp/ArrowDown moves the active visible result, Enter opens the page result, Escape or Clear resets the query.

## Graph Workspace Behavior

Graph selected-page details should become a compact page card rather than only title/meta/link lists.

The selected-page card may show:

- page title;
- summary when present;
- status, hierarchy label, tags, and stable ID;
- official object counts by type when non-empty;
- explicit neighborhood counts: outgoing, incoming, connected;
- links:
  - `Open page`;
  - `Find in search`;
  - `Open practice` when accepted official objects exist for that page.

The Graph list should also expose a compact version of the same public metadata so the list mode stays useful without the SVG map.

Graph visuals remain structural. Counts, colors, node size, and neighborhoods are readability cues only. They must not become rankings, recommendations, progress, mastery, or importance scores.

## Payload Shape

Search browser payload page entries may add public keys:

- `practice_url`: local Practice URL focused by page or empty when not useful;
- `search_url`: local Search URL when used by Graph payload;
- `study_counts`: object-type counts;
- `link_counts`: `{ "outgoing": int, "incoming": int, "connected": int }`;
- `stable_id`: same as page ID if useful for card text.

Graph browser payload nodes may add the same public fields, with URLs rewritten relative to `_raya/graph/index.html`.

Private fields remain forbidden:

- `_official`, `_assets`, `_reviewed`;
- `source_path`, `artifact_path`, `browser_path`;
- source hashes, cache keys, runtime profiles;
- official answers, solutions, correctness, card backs, hidden support fields.

## Documentation Impact

Update `docs/foundation/20_learning_renderer_contract.md` to state that Search and Graph discovery cards may show public official-object counts, explicit link counts, stable IDs, generated previous/next or workspace handoff links when they are derived from current artifact data.

Update agent role docs in English and Spanish so reviewers know to verify:

- metadata-only payloads;
- no private paths;
- no learner-state wording;
- no storage/fetch/external requests;
- Search Enter-to-open behavior;
- Graph selected-page detail card behavior.

Student docs may get a brief note if the UI labels change materially.

## Tests

Contract tests should verify:

- Search HTML contains richer card regions, object counts, explicit link metrics, Practice action links, and Graph action links.
- Search JSON payload contains only allowed public keys.
- Graph HTML contains selected-page detail fields for summary, stable ID, study counts, search link, and practice link placeholders.
- Graph JSON payload nodes contain only allowed public keys and deployment-neutral URLs.
- Generated visible text does not contain progress, mastery, recommendations, related practice, ranking, or source path language.

Browser tests should verify:

- Search still filters and Enter opens the active page.
- New Search card action links go to Graph and Practice.
- Graph selected-page detail renders the summary/counts and can open Search/Practice without external requests or overflow.
- Mobile and desktop layouts have no horizontal overflow.

## Non-Goals

- No calendar or due-date model.
- No scoring, attempts, submissions, grading, saved answers, progress, mastery, recommendations, review queues, or adaptive behavior.
- No prose scraping to infer related pages or related practice.
- No Pagefind, backend, CDN, fetch/XHR, worker, indexedDB, or browser-side graph/search data loading.
- No artifact schema change unless a test exposes that the current in-memory data is insufficient.

## Self-Review

The scope is one renderer UX slice: richer static discovery cards for current Search and Graph. It does not add a new course data model, does not alter source contracts, and does not introduce dynamic learner state. The requirements name concrete files, payload constraints, and tests without placeholders.
