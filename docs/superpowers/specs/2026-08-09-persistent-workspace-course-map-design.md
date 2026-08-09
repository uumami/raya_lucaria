---
id: persistent-workspace-course-map-design
title: Persistent Workspace Course Map Design
status: revised after adversarial review
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
- The active workspace tile is marked current on its own workspace; no
  course-tree link is current on a workspace, and the course tree remains
  visible.
- `Context` is a reader-only action and is omitted on workspaces, because a
  workspace has no learning rail for it to control. No artificial context rail
  is created to preserve that tile.
- A valid `?page=<page-id>` workspace focus may annotate and orient the
  matching tree node as focused, but it does not make that node current and it
  never replaces the map with the legacy rail focused-page panel.
- Workspace-specific controls, filters, results, and the already accepted
  main-content focused-page strip remain in the main workspace content.

The discovery-specific course rail, its focused-page panel, and the discovery
command bar's duplicate navigation controls are removed from workspace
layouts. The shared map supplies the mobile opener and all global course
navigation.

## Workspace Integration

This is a workspace rendering mode of the existing Course map, not a second
navigation abstraction. It receives:

- `from_output_path`, the workspace output path, separately from any optional
  focused course page; and
- an optional `current_workspace` value for the active workspace tile.

The renderer uses `from_output_path` for every generated map link. It does not
reuse a course page's output path merely because a workspace may be focused on
that page.

Each workspace also loads the map's existing local prepaint, shell, and
comfort resources and renders the map's required document attributes and
mobile drawer opener. `discovery.js` remains only for workspace-specific
filters, results, and the main-content focused-page strip. Focus parsing and
tree orientation move to shared map behavior, so removing the discovery rail
cannot silently remove `?page=` support.

## Link Contract

All Course-map destinations are generated through the renderer's existing
relative-path helper using the page currently being written as the origin.
This applies equally to course pages and `_raya/*/index.html` workspaces.

No root-relative URL is introduced. Generated links therefore work for a
course deployed at the domain root and for a course deployed beneath a path
such as `https://rayalucaria.org/ia_o26/`.

## Truth-Surface Changes

The current learning-renderer contract forbids course-shell behavior and the
Course map in discovery workspaces. This design intentionally supersedes that
rule. Implementation updates the smallest affected section of
`docs/foundation/20_learning_renderer_contract.md`, then updates the affected
English and Spanish role guidance and their indexes if they describe the old
separate workspace navigation.

Workspace map interactions remain presentation-only: they must not write
course source, artifacts, learner state, or unrelated preference state, and
must not fetch external resources. Any allowed volatile visual state follows
the accepted Course-map contract.

## Scope

The change is limited to the static renderer's shared navigation markup,
workspace call sites, supporting client behavior, the required local shell
resources and document state, removal of obsolete discovery navigation
markup/CSS/state, styling required to host the same map in workspaces,
foundation/role documentation, and focused tests.

It does not change course source schema, authored content, official-object
semantics, workspace data, deployment workflows, skins, storage policy, or
the visual design of the accepted Course map.

## Verification

Tests must prove, for the landing page and each of Search, Graph, Practice,
Tasks, and Schedule:

1. exactly one Course map is present and the discovery course rail is absent;
2. the discovery command bar does not retain duplicate course navigation;
3. the same applicable map controls and course-tree markup are present, with
   reader-only `Context` absent on workspaces;
4. the corresponding workspace control is current only on that workspace and
   no course-tree link is current;
5. the existing local map scripts, document attributes, drawer opener, filter,
   collapse behavior, and keyboard behavior work on workspaces;
6. course-home, tree, and workspace links resolve correctly from a normal
   course page and all five deep workspace output paths, including when served
   below a neutral path prefix;
7. a valid page-focus URL keeps the map and tree visible, the legacy rail focus
   panel absent, and the existing main-content focused-page strip available;
8. the map has no duplicate IDs, retains one expanded-map vertical scroller,
   and preserves drawer focus/inertness behavior at desktop and narrow widths;
9. interactions neither fetch nor write source, artifact, learner, or
   unrelated preference state.

The renderer build, static read-path/browser tests, and existing repository
checks remain the final gates. The course repository is updated only by
advancing its pinned framework revision after the framework change is merged.

## Self-Review

- The design has one navigation implementation and one link-generation path.
- It preserves the accepted Course-map interaction model instead of creating a
  third renderer abstraction.
- It explicitly retains workspace content and the main-content focused-page
  behavior while removing only duplicate navigation chrome.
- It defines the workspace-only omission of reader Context rather than leaving
  a visible dead control.
- It adds no runtime requests, account state, learner state, or deployment
  assumptions.
