# Collapsed Reader Rails Polish Design

## Goal

Make the desktop collapsed course-map and learning-context rails feel intentional, readable, and fluid while preserving the reset renderer contract: static output, no persisted reader state, no external assets, and no browser-side renderer dependency.

## Context

The old `main` branch had a stronger shell affordance: clear sidebars, explicit collapse/expand controls, and smooth state changes. The reset branch already has the correct architecture and constraints, but its collapsed rails still read as cramped square labels (`Nav`, `Info`) and the panel bodies disappear abruptly. This slice adapts the old branch's affordance quality without importing Eleventy, Tailwind, localStorage persistence, CDN fonts, or legacy navigation data.

## Design

On desktop, a collapsed rail should become a narrow vertical tab rather than a small unlabeled box. The course-map collapsed toggle should show an icon-like marker plus the vertical label `Map`; the right context rail should show an icon-like marker plus the vertical label `Context`. Both remain real buttons with the existing accessible labels and `aria-expanded` state.

The article grid should keep the existing behavior: collapsing the map and/or right rail increases article space, and the current map remains keyboard navigable through visible compact links. The right rail remains inert and hidden from assistive navigation when collapsed, matching the current contract.

Transitions should be limited to layout, opacity, transform, and border/color polish. They must not animate on first paint before shell readiness, and they must respect `prefers-reduced-motion: reduce`.

## Non-Goals

- No persisted sidebar, TOC, or reader state.
- No legacy frontend framework, Tailwind, Eleventy templates, or CDN resources.
- No change to graph data, MathJax rendering, OpenDyslexic behavior, or numbered-object semantics.
- No mobile/tablet change beyond ensuring desktop-only collapsed affordances remain hidden there.

## Verification

Tests must prove:

- Desktop collapsed map renders a vertical `Map` tab with a non-horizontal writing mode.
- Desktop collapsed context rail renders a vertical `Context` tab with a non-horizontal writing mode.
- Collapsing map and context increases article width and preserves the expected `aria-expanded`, `aria-hidden`, and inert states.
- Mobile/tablet keep the desktop collapsed affordances hidden and do not create an inert right rail state.

