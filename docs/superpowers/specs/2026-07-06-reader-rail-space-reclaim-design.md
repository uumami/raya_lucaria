---
id: reader-rail-space-reclaim-design
title: Reader Rail Space Reclaim Design
status: active
workflow: superpowers
created: 2026-07-06
---
# Reader Rail Space Reclaim Design

## Goal

Make the reader shell article-first when side rails are collapsed. Collapsing the
left course map or right learning context must reclaim the space for the
article instead of leaving gray reserved columns, while expanded rails remain
usable and keep current Raya capabilities.

## Problem

The current render fixture shows two user-visible failures:

- Collapsed rails still reserve grid tracks. A small arrow button appears, but
  the rest of the column remains empty gray space.
- Expanded left navigation is dominated by dense course tools and workspace
  badges before the course map. Labels truncate, badges overlap, and the course
  hierarchy starts too low to function as the primary navigation surface.

These are layout and information hierarchy failures, not only color or spacing
issues.

## Contract Change

Update `docs/foundation/20_learning_renderer_contract.md` so collapsed desktop
course-map mode may become a minimal operable edge opener instead of an
operable compact map rail with page targets. This change is intentional because
the article must reclaim collapsed rail space.

The new contract keeps these requirements:

- Collapse is explicit click/Escape state, not hover state.
- State is volatile and does not persist in browser storage.
- Expanded map and right rail remain normal structural desktop columns.
- Closed mobile course map remains a modal drawer surface.
- The right learning rail collapse remains desktop-only unless a later contract
  changes tablet behavior.

## Selected Design

Use the current static renderer and adapt the main-branch principle that
collapsing navigation returns width to the article. Do not port the old
Eleventy app, top bar, Tailwind assumptions, CDN resources, service worker, or
localStorage navigation persistence.

### Collapsed Left Map

On desktop, collapsing the course map removes the left grid column from the
shell layout. A small fixed edge opener remains at the left viewport edge. It
uses the existing course-map toggle button, has a useful accessible name, and
does not expose hidden full-map descendants to keyboard or assistive
navigation.

The opener must not cover readable article text or article controls. It may sit
in the outer page gutter or just outside the article content bounds. It is a
control, not a mini navigation rail.

### Collapsed Right Context

On desktop, collapsing the right learning rail removes the right grid column
from the shell layout. A small fixed edge opener remains at the right viewport
edge. The rail body stays `aria-hidden`, inert, and non-tabbable until restored.

### Expanded Left Map

The expanded map is reorganized so course navigation is primary:

1. Header and collapse control.
2. Current-page chip.
3. Filter and section actions.
4. Course map tree.
5. Compact course tools and workspace links.

The exact DOM may keep generated capabilities in the same region, but the
visual order must put the map before secondary tools. Visible command text must
not truncate to partial labels such as `Text si...` or `OpenD...`. Commands may
use compact icons with accessible names. Workspace details may be hidden or
reduced in narrow rails; they must not overlap.

### Responsive Boundaries

The desktop shell breakpoint remains `1280px` for this pass. Below that
breakpoint, the course map uses the drawer model and the right learning rail
body remains visible and accessible in normal reading order.

## Accessibility

- Hidden collapsed map contents and hidden collapsed right-rail body are inert,
  `aria-hidden`, and removed from tab order.
- Visible edge openers are keyboard reachable, have visible focus, and have
  accurate `aria-expanded`.
- Escape collapses desktop rails and closes mobile drawers without leaving
  focus inside hidden content.
- No shell state is written to `localStorage` or `sessionStorage`; accepted
  comfort preferences remain the only stored reader keys.

## Testing

Add behavior tests instead of CSS trivia:

- Contract tests assert the updated foundation language and generated shell
  surfaces.
- Browser tests assert that collapsed left/right rails no longer reserve grid
  columns and that article width increases materially.
- Browser tests assert hidden collapsed regions are not tabbable or exposed.
- Browser tests assert edge openers do not intersect the article content box at
  representative desktop widths.
- Existing mobile drawer and right-rail availability tests remain valid below
  `1280px`.

## Out Of Scope

- Rewriting discovery workspaces.
- Reintroducing the main-branch top bar or persisted sidebar state.
- Changing course source layout, artifact data contracts, graph internals, or
  execution behavior.
- Full tablet structural-collapse redesign below `1280px`.
