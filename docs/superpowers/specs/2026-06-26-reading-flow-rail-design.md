# Reading Flow Rail Design

## Context

The reset reader has a strong shell, but orientation is still split across the
top sequence links, bottom sequence cards, the collapsed rail `Sequence` panel,
and the collapsed rail `Connections` panel. Old `main` made navigation feel
closer at hand through a persistent sidebar. The reset branch should adapt that
idea without carrying over old Eleventy/Pagefind state or progress language.

## Goal

Add a compact, expanded-by-default `Reading flow` panel near the top of the
learning rail. It should combine previous/next sequence and page graph context so
students can answer "where am I, what comes next, and how is this page connected?"
without leaving the first viewport.

## Approach

Generate one static rail panel from existing data:

- previous and next targets from `_sequence_targets`;
- outgoing and incoming graph context from `page_graph_context`;
- graph workspace link from the current page's graph URL.

The panel replaces the rail's separate `Connections` and `Sequence` panels when
it has content. The article-level sequence nav, end-of-page cards, and
article-level connection section remain unchanged because they serve different
reading positions.

## UI

The panel uses the existing rail disclosure component with:

- class `raya-page-reading-flow`;
- title `Reading flow`;
- expanded initial state;
- compact sequence chips for `Previous` and `Next`;
- a graph summary line with counts for `from this page` and `links here`;
- an `Open in course graph` link;
- up to a small number of connection chips, split by direction when available.

It must stay readable in the first viewport on desktop and inside the mobile
context drawer.

## Constraints

- No learner progress, recommendation, scoring, mastery, analytics, or completion
  claims.
- No localStorage/sessionStorage/fetch.
- No graph data mutation.
- No schema or authoring syntax changes.
- Preserve generated article sequence and graph context surfaces.
- Preserve existing rail panel keyboard and collapsed-state behavior.

## Test Strategy

- Contract test proves generated reader fixture HTML contains the expanded
  `raya-page-reading-flow` panel, previous/next links, graph counts/link, and no
  forbidden progress/personalization/runtime terms.
- Browser test proves the panel is visible in the first desktop viewport, link
  chips have usable boxes, graph link is visible, and no external requests occur.
- Existing rail collapse and mobile context drawer tests continue to cover
  disclosure mechanics.

## Acceptance

- `/reader-ux/index.html` includes one expanded `Reading flow` rail panel.
- The panel contains previous/next links and graph connection counts when data
  exists.
- The old rail `Sequence` and `Connections` panels do not duplicate that same
  rail content on pages where `Reading flow` is rendered.
- Focused contracts, focused e2e, and render-debug pass.
