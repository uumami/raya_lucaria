---
title: Graph Relationship Inspection
date: 2026-06-27
status: accepted
---

# Graph Relationship Inspection

## Problem

The current static graph explains selected-page relationships in the inspector,
but the visible SVG edges themselves are not directly inspectable. A student can
see arrows, colors, and line patterns without an immediate answer to "what does
this relationship mean?"

Old `main` made the graph feel approachable through a compact graph workspace
and quick controls, but it depended on Cytoscape from a CDN. The current reset
must keep the local SVG graph and static artifact data.

## Design

Add relationship inspection to the graph canvas:

1. Render each visible SVG relationship with a wider transparent hit path in
   addition to the visual path.
2. Make each relationship keyboard-focusable and pointer-inspectable.
3. Show a compact relationship preview near the graph canvas when a relationship
   is hovered, focused, or tapped.
4. The preview names the source page, target page, relationship kind, and
   direction, then exposes local actions to select the source page, select the
   target page, and focus that relationship kind when the kind is visible.
5. Highlight the inspected edge and its endpoints without implying importance,
   progress, ranking, recommendation, or mastery.

Relationship inspection is transient viewport state. Selecting a source or
target page may use existing selected-page behavior and URL graph state, but
mere edge inspection must not write storage, mutate graph data, fetch resources,
or change authored relationships.

## Boundaries

- No source schema, artifact graph schema, or data-index changes.
- No external graph library, CDN, renderer, font, or runtime data request.
- No browser storage for inspected relationships.
- No inferred relatedness, importance, recommendation, progress, mastery, or
  learner-state wording.
- No replacement of existing selected-page inspector, relationship chips, or
  walkthroughs.

## Tests

- Contract test: generated graph HTML contains a relationship preview region and
  graph JavaScript contains relationship hit-target/inspection hooks without
  storage, fetch, or external requests.
- Browser test: focusing or hovering a visible SVG edge opens the relationship
  preview with source page, target page, relationship kind, and direction.
- Browser test: the preview actions select the source or target page through
  existing graph selection behavior.
- Browser test: inspected relationship styling remains visible on desktop and
  mobile without horizontal overflow.
- Render-debug gate: screenshots, external requests, overflow, raw TeX, local
  resource, and static parity checks continue to pass.
