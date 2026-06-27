---
title: Reader Title-First Orientation
date: 2026-06-26
status: accepted
---

# Reader Title-First Orientation

## Problem

Desktop reader pages currently show sequence navigation, breadcrumbs, and the
generated Page brief before the authored lesson heading. On dense fixture pages
this pushes the `h1` far below the first viewport, so the page feels like chrome
before lesson.

## Design

Render the first authored `h1` as the article's primary orientation anchor
before the generated Page brief. Keep article sequence navigation and
breadcrumbs above it because they are compact location controls. Keep the Page
brief immediately after the `h1` so students still get summary, structural
position, read time, tags, prerequisites, graph links, and practice handoffs
before the long lesson body.

The renderer should preserve exactly one visible `h1` per page. If an article
does not start with a generated first `h1`, the renderer leaves the article HTML
unchanged and keeps the current Page brief position.

## Boundaries

- No source schema change.
- No inferred goals, progress, mastery, recommendations, or personal state.
- No browser-side fetch, storage, external resources, or MathJax conversion.
- No change to graph, search, practice, tasks, or schedule data contracts.

## Tests

- Contract HTML order test: sequence and breadcrumbs may precede the title, but
  the first visible `h1` must precede `.raya-page-brief`, and only one page `h1`
  is emitted.
- Browser layout test: at desktop width, the `h1` must appear before the Page
  brief and near the first viewport instead of below the brief.
