---
id: persistent-workspace-course-map-design
title: Persistent Workspace Course Map Design
status: approved
workflow: superpowers
created: 2026-08-09
---
# Persistent Workspace Course Map Design

## Problem

Rendered course pages use the established `Course map`, while Search, Graph,
Practice, Tasks, and Schedule render a separate discovery course rail. The two
rails duplicate course identity, workspace links, page links, responsive
behavior, and focus handling. They are visibly inconsistent and their separate
relative-link generation can break from deep workspace paths.

Course navigation must remain stable while visitors move among a course page
and its generated workspaces. A workspace is a destination within the course,
not a reason to replace the course map.

## Chosen Design

Use the existing `Course map` as the only persistent course-navigation
component on every generated surface.

- Normal course pages retain the current Course map unchanged.
- Every generated workspace renders that same Course map in the same position,
  with the same hierarchy, filter, collapse/drawer behavior, comfort controls,
  and shared client behavior.
- The active workspace tile is marked current on its own workspace; the course
  tree remains visible.
- A valid `?page=<page-id>` workspace focus may highlight or orient the
  matching node, but it never replaces the map with a focused-page panel.
- Workspace-specific controls, filters, results, and the already accepted
  focused-page strip remain in the main workspace content.

The discovery-specific course rail and its duplicate page/workspace navigation
are removed from workspace layouts.

## Link Contract

All Course-map destinations are generated through the renderer's existing
relative-path helper using the page currently being written as the origin.
This applies equally to course pages and `_raya/*/index.html` workspaces.

No root-relative URL is introduced. Generated links therefore work for a
course deployed at the domain root and for a course deployed beneath a path
such as `https://rayalucaria.org/ia_o26/`.

## Scope

The change is limited to the static renderer's shared navigation markup,
workspace call sites, supporting client behavior, styling required to host the
same map in workspaces, and focused tests.

It does not change course source schema, authored content, official-object
semantics, workspace data, deployment workflows, skins, storage policy, or
the visual design of the accepted Course map.

## Verification

Tests must prove, for the landing page and each of Search, Graph, Practice,
Tasks, and Schedule:

1. exactly one Course map is present and the discovery course rail is absent;
2. the same map controls and course-tree markup are present;
3. the corresponding workspace control is current only on that workspace;
4. course-home, tree, and workspace links resolve correctly from the deep
   workspace output path;
5. a valid page-focus URL preserves the map and its tree rather than rendering
   a replacement focused-page panel; and
6. the map remains usable at desktop and narrow drawer widths.

The renderer build, static read-path/browser tests, and existing repository
checks remain the final gates. The course repository is updated only by
advancing its pinned framework revision after the framework change is merged.

## Self-Review

- The design has one navigation implementation and one link-generation path.
- It preserves the accepted Course-map interaction model instead of creating a
  third renderer abstraction.
- It explicitly retains workspace content and page-focus behavior while
  removing only duplicate navigation chrome.
- It adds no runtime requests, account state, learner state, or deployment
  assumptions.
