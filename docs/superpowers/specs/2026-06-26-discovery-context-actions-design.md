---
id: superpowers-discovery-context-actions-design
title: Discovery Context Actions Design
status: accepted
---
# Discovery Context Actions Design

## Context

The legacy `main` interface kept useful actions close to the object being
inspected. The reset renderer already has stronger static Search, Practice,
Tasks, and Schedule workspaces, but their context panels currently update only
title and metadata for the active result. Graph's selected-page detail is more
useful because it pairs the active object with direct static handoff links.

## Goal

Add context-panel action links to Search, Practice, Tasks, and Schedule so a
student scanning results with keyboard, pointer, or focus can immediately open
the active item, view it in Graph, or move to the relevant neighboring
workspace without hunting through the result card.

## Design

Each discovery workspace gets one context action region inside its existing
context panel:

- Search shows `Open page`, `View graph`, and any generated `Open practice`,
  `Open tasks`, or `Open schedule` links for the active page.
- Practice shows `Open page` and `View graph` for the active official object.
- Tasks shows `Open page` and `View graph` for the active task-family object.
- Schedule shows `Open page` and `View graph` for the active dated item.

The action region is static markup generated at build time and updated by the
existing local workspace script from the already embedded public payload. It is
hidden when no visible result exists. Links must never be invented from prose,
must not add schema fields, and must not fetch at runtime.

## Constraints

- No browser storage for context action state.
- No external scripts, CSS, fonts, fetch, or XHR.
- No learner-state, recommendation, progress, mastery, ranking, or authority
  language.
- No source paths, private `_official/` paths, support paths, cache keys, or
  artifact internals.
- Existing Enter-to-open keyboard behavior stays unchanged.
- Collapsing the context panel must remove context action links from keyboard
  and assistive navigation through the existing discovery panel behavior.

## Verification

Contract tests should assert generated action-region markup and local script
tokens for all four workspaces. Browser tests should load Search, Practice,
Tasks, and Schedule, move the active result with keyboard or focus, verify the
context links point at the active public item, verify no-visible-result state
hides the actions, and confirm no localStorage/sessionStorage or external
requests are introduced.
