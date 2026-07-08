---
id: superpowers-course-map-tiny-tray-design
status: approved-for-planning
workflow: superpowers
date: 2026-07-08
---

# Course Map Tiny Tray Design

## Purpose

The medium-width course map currently keeps the right height and compact map
width, but its tool strip still reads as an awkward row of unrelated icons at
the bottom of the panel. The row should become a small, intentional tray near
the top of the expanded map so the tools are visible without consuming the
bottom edge or looking like stray marks.

## User-Approved Direction

Use a **Tiny Tray under the header**:

1. Keep the `Course map` title and map collapse button in the panel header.
2. Place a compact pill-shaped tray directly below the header.
3. Keep `Page N of M` below the tray.
4. Keep the course tree below the page position.
5. Remove the bottom medium-width tool strip.

The user explicitly rejected bottom placement and approved the under-header
placement during the Superpowers brainstorming visual companion review.

## Scope

In scope:

- Medium expanded course map layout.
- Course-map tool placement and visual treatment.
- Existing command actions: Search, Graph, Practice, Tasks, Schedule, Text size,
  and OpenDyslexic.
- Browser-driven regression checks for geometry, width, placement, and visual
  artifacts.

Out of scope:

- Changing command destinations or behavior.
- Reworking the mobile drawer layout.
- Changing the right learning context rail.
- Replacing the existing icon set or adding new tools.

## Layout

The expanded medium course map should render in this order:

```text
Course map header row
Tiny tray command row
Page N of M
Course tree
```

The tray should sit near the left edge under the header, not centered in the
whole panel and not attached to the bottom. It should use the same full-height
map panel established by the previous rail work.

## Visual Rules

The tray should be visually quiet:

- pill-shaped container;
- light neutral surface and border;
- no blue underline or active-page bar;
- no visible text labels in the row;
- each command remains a small, stable icon target;
- hover and focus states may use subtle inset treatment without changing size;
- total tray width should be narrower than the current bottom row.

The row must look intentional as a control tray, not like loose icon strokes
floating across the panel.

## Accessibility and Behavior

The tray reuses existing command elements, labels, ARIA state, keyboard behavior,
and link/button targets. Text labels remain visually hidden but accessible.
Focus-visible treatment must remain clear enough for keyboard users.

The map collapse button remains in the header and keeps its existing expanded
state behavior.

## Testing

Add or update browser-driven e2e coverage to verify:

- the expanded medium map remains full-height and compact width;
- the tray appears under the header and above `Page N of M`;
- the bottom tool strip is absent in the medium expanded map;
- all seven expected command targets remain visible and icon-only;
- the tray width is narrower than the previous bottom strip;
- commands have no active blue bar, underline artifact, or unintended background;
- mobile drawer comfort chrome is not regressed.

The existing host and Docker gates remain the final verification path:

- `./scripts/check.sh`
- `./scripts/check-docker.sh`

## Implementation Notes

Prefer a CSS-only implementation in `packages/static/src/raya_static/rendering.py`
using the existing generated course-map tool markup. If markup order makes the
under-header placement fragile or impossible, the implementation plan should
call out the smallest renderer markup move needed and keep the same command
elements/actions.
