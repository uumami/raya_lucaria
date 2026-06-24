---
id: superpowers-discovery-workspace-polish
title: Discovery Workspace Polish Design
status: draft
date: 2026-06-23
workflow: superpowers
---
# Discovery Workspace Polish Design

## Problem

The Graph workspace now uses a three-region desktop layout with collapsible context panels and clear handoffs. Search and Practice still render as flat generated pages: a header, a controls block, and one long results region. They are contract-correct, but they do not yet feel like part of the same reader workflow or make good use of desktop space.

## Goals

- Make Search and Practice read as static discovery workspaces that match the Graph page's visual model.
- Improve desktop space usage with left controls, central results, and right context panels.
- Keep mobile layout article-first and single-column.
- Keep Search metadata-only and Practice accepted-object-only.
- Keep all discovery state transient except existing reader comfort preferences.
- Preserve local-only static deployment parity: no fetch/XHR, external requests, CDN resources, browser-side MathJax, or shell-script dependency.

## Non-Goals

- No Pagefind, rendered-prose indexing, source-path indexing, answer/support indexing, or MathJax-output indexing.
- No inferred related practice, recommendations, personal next steps, progress, mastery, confidence, scoring, attempts, submissions, or grading.
- No new source or artifact schema.
- No copied legacy Eleventy, Tailwind, Cytoscape, persistent sidebar state, service worker, or quiz behavior.

## Design

Search and Practice get a shared discovery workspace structure:

- a left control panel for search, filters, and status;
- a central results panel for page or official-object cards;
- a right context panel for public metadata and safe handoff links.

The markup is generated at build time. Search continues to embed public page metadata in `raya-search-data`; Practice continues to embed public official-object metadata in `raya-practice-data`. JavaScript may filter existing DOM nodes and update status text, but must not fetch data or persist search/practice state.

Practice should use the shared accessibility script like Search and Graph instead of duplicating comfort-control logic in practice filtering JavaScript.

## Test Strategy

- Contract tests assert the new workspace regions, panel labels, filter/status controls, and local resource links exist.
- Contract tests assert forbidden runtime behavior and learner-state wording remain absent.
- Browser tests check desktop and mobile no-overflow layout, Search result filtering, Practice type filtering, workspace context panels, and OpenDyslexic/text-size behavior through the shared accessibility path.
- `scripts/check-render-debug.sh` remains the focused parity gate for visible renderer changes.
