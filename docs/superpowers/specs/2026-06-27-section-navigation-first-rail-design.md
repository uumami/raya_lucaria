---
title: Section Navigation First Rail
date: 2026-06-27
status: accepted
---

# Section Navigation First Rail

## Problem

The current reader shell already generates a right-rail `Current section` panel,
an active `Page contents` table of contents, and shell JavaScript that updates
the active heading while the reader scrolls. On realistic pages those panels are
below first-viewport metadata panels, so the right rail feels less like the
dedicated old-main TOC and more like a general info stack.

## Design

Move section navigation to the top of the right learning rail when a page has
headings:

1. `Current section`
2. `Page contents`
3. `Reading flow`
4. Summary, status, time, tags, prerequisites, and other compact context

This keeps the old-main right-TOC benefit: students can see where they are
inside the page before scanning metadata. It also preserves the current reset
contract because all content still comes from generated heading anchors and
artifact metadata, with no storage, fetch, progress, mastery, or
recommendation semantics.

The `Current section` and `Page contents` panels remain ordinary rail panels.
They keep existing explicit collapse behavior, keyboard reachability, active
heading sync, and whole-rail `Context` collapse behavior. When a page has no
TOC, the rail keeps the existing fallback order.

## Boundaries

- No source schema, graph data, search data, or official object changes.
- No browser storage or persisted section state.
- No external scripts, CSS, fonts, renderers, or runtime fetches.
- No personal progress, reading percentage, mastery, recommendation, or
  inferred learning-goal language.

## Tests

- Contract test: generated reader HTML orders `Current section` and
  `Page contents` before `Reading flow` and summary when a TOC exists.
- Contract test: a page without enough headings for a generated TOC omits the
  section-navigation panels and keeps `Reading flow` before summary.
- Browser test: on `reader-ux/` desktop, the `Current section` and
  `Page contents` panels are visible in the first viewport and the active
  section link still updates from shell JavaScript.
- Existing rail collapse tests continue to prove collapsed panels are inert and
  the whole right rail can collapse into the `Context` tab.
