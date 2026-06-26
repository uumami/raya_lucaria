# Graph Return To Reading Design

## Goal

Make a page-focused Graph workspace feel like a continuation of reading by
surfacing the selected page's return link, course-order neighbors, and explicit
relationship actions as a coherent reading path.

## Context

The current graph is already static, local, URL-addressable, and rich. It can
open from reader pages with `?page=<page-id>`, select the focused page, show
relationships, and open the selected lesson. The remaining UX gap is that the
selected-page detail panel still feels like a tool inspector. Students need a
clear path back to reading and compact context for where the selected page sits
in the course.

The historical `main` branch graph had strong graph-navigation affordances, but
its Cytoscape/CDN implementation is incompatible with the reset. This design
salvages the interaction idea, not the dependency stack.

## Design

Add a static selected-page "Reading path" treatment inside the Graph inspector:

- a compact eyebrow naming the area as `Reading path`;
- a primary action group with `Open selected page` emphasized as the return to
  the lesson;
- the existing Search, Practice, Tasks, Schedule, and Focus neighborhood actions
  grouped as secondary static workspace actions;
- the existing Previous / Selected / Next course-order links styled as reading
  path cards with labels and titles;
- the existing incoming/outgoing relationship lists kept below the relationship
  overview and walkthrough, with their `Focus` controls preserved.

The selected-page detail remains generated from already loaded public graph
payload data. No browser storage, fetch, external graph library, personalization,
recommendation, progress, or mastery language is introduced.

## UX Requirements

- A page-focused graph URL such as `_raya/graph/index.html?page=authoring-matrix`
  first-paints with the selected detail visible on desktop. On mobile, the
  existing compact inspector default remains; opening the inspector shows the
  same reading path.
- The selected detail includes visible text `Reading path`.
- `Open selected page` is visually primary and appears before secondary actions.
- Previous, selected, and next course-order links are visible when the selected
  page has neighbors, and their labels include the linked page titles.
- The reading path block does not use recommendation, progress, mastery, or
  personalized-next-step language.
- The block fits desktop and mobile graph layouts without document-level
  horizontal overflow.

## Non-Goals

- No graph data contract change.
- No new selected-page state model.
- No persistence of reading path state.
- No inferred recommendations or ranking.
- No external graph renderer, CDN, fetch, or browser-side MathJax.

## Testing

- Contract test: generated graph HTML exposes the reading path structural
  wrappers and no forbidden static-only tokens.
- Browser test: page-focused graph URL shows the reading path, primary open
  action, previous/current/next links, static-only language, and no overflow on
  desktop and mobile.
