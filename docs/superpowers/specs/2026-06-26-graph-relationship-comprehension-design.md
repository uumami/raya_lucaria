---
id: superpowers-graph-relationship-comprehension-design
title: Graph Relationship Comprehension Design
status: accepted
---
# Graph Relationship Comprehension Design

## Context

The reset renderer already has a local SVG Graph workspace with search, layout,
group filters, relationship-kind filters, selected-page details, relationship
chips, and a relationship walkthrough. The legacy `main` branch showed why a
graph should feel like an explorable learning surface instead of a diagnostic
diagram, but its implementation model is not reusable because it depended on
legacy routes, external graph libraries, and runtime assumptions outside the
current framework.

The current Graph workspace now has clearer toolbar control groups. The next
student-facing gap is relationship comprehension after selecting a page:
students can see chips and walkthrough cards, but it is not obvious how those
chips relate to the global relationship filters, visible graph edges, and the
selected-page link lists.

## Goal

Make the selected-page Graph detail explain and focus explicit relationships
more clearly, while preserving current static graph data, URL rules, local-only
resources, and no learner-state storage.

## Design

When a page is selected, the selected-page detail keeps showing relationship
chips such as `Content out 3` and `Navigation in 1`. Each chip remains a local
toggle for one relationship kind and direction. The change adds a compact
relationship focus bar inside the selected-page relationship area:

- a status message that names the active focus or says all selected-page
  relationships are visible;
- a visible `Show all relationships` reset button that appears only while one
  chip is active;
- explicit text saying disabled or globally hidden relationship kinds come from
  the Graph toolbar relationship filters.

Relationship chip focus remains local UI state only. It must not change URL
state, graph data, edge-kind filter state, group filter state, selected page,
or browser storage.

The visible graph should reinforce the selected-page relationship focus. When a
relationship chip is active, graph marks for matching selected-page edges get a
focused class and nonmatching selected-page edges get a muted class. The
walkthrough cards and outgoing/incoming detail lists narrow to the active
relationship focus. The edge-kind toolbar still controls global visibility; if
a kind is hidden globally, the selected-page chip for that kind stays visible
but shows that it is currently hidden by the relationship filter.

The implementation uses the existing embedded graph payload and existing
`relationshipFocus` object. It adds no new generated graph schema, no external
libraries, no runtime fetches, and no storage.

## Non-Goals

- No recommendation, importance, ranking, mastery, progress, or personalization
  language.
- No new graph data fields or artifact schema changes.
- No browser-side data fetch or graph library.
- No localStorage/sessionStorage for graph relationship focus.
- No persistent URL parameter for relationship-chip focus.
- No scoring, assignment, or learner-state behavior.

## Verification

Contract tests should assert the generated Graph HTML includes the relationship
focus bar and reset control, while preserving existing local-only graph script
and data attributes.

Browser tests should assert:

- selecting a page shows all relationship chips and all walkthrough cards;
- activating a chip shows the reset button, narrows walkthrough cards, narrows
  the matching outgoing/incoming detail list, and does not mutate URL or browser
  storage;
- hiding the matching global relationship kind through the toolbar marks the
  selected-page chip as globally hidden;
- pressing `Show all relationships` restores all selected-page relationship
  cards and lists without changing global relationship filters.

Render-debug verification remains required because the change affects the
browser-visible Graph workspace.
