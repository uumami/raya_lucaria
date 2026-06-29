---
id: reader-navigation-spine-design
title: Reader Navigation Spine Design
status: ready
date: 2026-06-29
workflow: superpowers
---

# Reader Navigation Spine Design

## Context

The active UX convergence goal is to adapt useful reader experience from the
legacy `main` branch into the reset static renderer without importing legacy
architecture. Legacy `main` made navigation feel continuous through a persistent
sidebar, top and bottom previous/next links, backlinks, and a page table of
contents. The current renderer already has stronger contract boundaries:
generated course map, sticky command bar, article breadcrumbs, article-end
sequence cards, Page connections, graph handoffs, and a collapsible right
learning rail.

The current issue is not missing data. The reader page has enough navigation
surfaces, but they do not yet read as one intentional learning path. This slice
will make the existing surfaces more coherent and scannable while keeping the
article primary.

## Goal

Make reader pages answer these questions quickly:

- where am I in the course;
- what section am I reading;
- what should I inspect around this page;
- what comes before and after in the authored course order;
- how do I collapse support chrome without losing the reading flow.

This is a static UX slice. It must not add progress, recommendations, learner
state, analytics, scoring, storage for shell state, runtime fetching, or legacy
Eleventy/Tailwind behavior.

## Design

### Article Continuation

Keep the article as the primary continuous reading surface. Improve the
article-end Previous/Next sequence cards so they act as the clearest
continuation point after the lesson:

- show stable structural labels such as `Previous page` and `Next page`;
- keep page titles prominent and course-order based;
- preserve deployment-neutral links;
- avoid wording such as `recommended`, `continue learning`, `completed`, or
  `progress`.

The compact top command-bar previous/next links remain quick navigation. The
article-end cards are the main end-of-reading affordance.

### Page Connections

Refine the existing Page connections block into a scannable graph context
summary, not a recommendation panel:

- keep explicit incoming/outgoing relationship counts;
- make each connected page row easier to scan with page title, relationship
  direction, relationship kind, and a graph-focus action;
- keep native previews for public page metadata where present;
- keep all links local and static;
- do not infer related practice or importance from prose.

This adapts the legacy backlink affordance but uses current generated graph
data and current relationship language.

### Learning Rail Coherence

Refine the right learning rail into a clearer support spine with stable
sections:

- `On this page` for generated heading anchors;
- `Reading flow` for current page position and previous/next course-order
  links;
- `Page context` for summary, status, estimated time, tags, and prerequisites;
- `Connections` for explicit graph relationship summaries and graph-focus
  links.

The rail collapse/expand behavior keeps the current volatile model:

- desktop collapse is explicit through the existing context controls;
- collapsed state removes rail body controls from keyboard navigation;
- mobile and tablet keep the support body available instead of creating hidden
  inert content;
- no rail, map, section, or focus state is written to browser storage.

### Visual Treatment

Use the current skin tokens and renderer CSS. Do not introduce arbitrary CSS,
external fonts, CDN resources, or legacy theme switching. Visual changes should
make structure clearer through spacing, section headers, relationship chips,
and stronger card hierarchy, while preserving readable density on desktop.

## Non-Goals

- No browser-side theme authority or saved shell state.
- No hover-first sidebar expansion.
- No progress, mastery, completion, personalization, recommendations, or
  inferred next steps.
- No graph library, external request, browser-side renderer, or CDN import.
- No source-contract or artifact-contract changes.
- No redesign of generated Search, Graph, Practice, Tasks, or Schedule
  workspaces in this slice.

## Implementation Scope

Expected implementation files:

- `packages/static/src/raya_static/builder.py` for generated HTML grouping and
  labels;
- `packages/static/src/raya_static/rendering.py` for CSS hierarchy and
  responsive behavior;
- `packages/static/src/raya_static/shell.py` only if existing collapse behavior
  needs small accessibility fixes;
- `tests/e2e/test_preview_static_read_path.py` for browser-facing assertions.

Role documentation is not required unless the implementation changes authoring
behavior. This slice changes generated reader presentation only.

## Testing

Add or update browser e2e coverage against `examples/courses/render-fixture`:

- desktop reader page shows article-end Previous/Next cards as the primary
  end-of-reading continuation without overflow;
- Page connections show explicit incoming/outgoing counts, connected page
  titles, relationship direction/kind, graph-focus links, and no recommendation
  language;
- learning rail exposes the expected section groups and remains keyboard
  reachable when expanded;
- desktop rail collapse removes rail body links from tab order and restores
  them on expand;
- mobile keeps the rail body available and does not create a hidden inert rail;
- rendering the page does not add browser storage keys, external renderer
  requests, browser-side MathJax conversion, or private/source path links.

Run focused e2e tests first, then `./scripts/check-render-debug.sh`. If the
implementation touches shared shell behavior, also run the broader shell and
static-read-path tests that cover map, rail, and command-bar interactions.

## Risks

The main risk is visual clutter from making every navigation surface louder.
The implementation should use hierarchy: article content first, end-of-article
sequence cards as the main continuation, Page connections as optional graph
context, and the learning rail as compact support. A second risk is accidentally
turning structural links into recommendations. Tests and review should check
visible text for recommendation, progress, and learner-state language.
