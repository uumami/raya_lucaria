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

Adversarial review tightened this direction: the tray must not be the existing
bottom strip moved upward. It must be a small, intentional control tray with
real placement, stable accessibility order, and measurable visual constraints.

## Scope

In scope:

- Medium expanded course map layout, where medium means
  `640px <= viewport width < 1280px`.
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

This order is both visual order and DOM/focus order. A CSS-only implementation
is acceptable only if browser measurements prove this order and keyboard order
remain coherent. If the existing markup prevents that, the implementation should
make the smallest renderer markup move needed to produce:

```text
header row
tools tray
page position
map list
```

The tray should sit near the left edge under the header, aligned close to the
title edge, not centered in the whole panel and not attached to the bottom. It
should use the same full-height map panel established by the previous rail work.
`Page N of M` should be visually muted and kept close to the course tree so the
map still reads as navigation, not as a tool palette first.

## Visual Rules

The tray should be visually quiet:

- pill-shaped container;
- light neutral surface and border;
- intrinsic/content-sized width, not full-width;
- left-aligned placement under the header;
- no shadow;
- no blue underline or active-page bar;
- no visible text labels in the row;
- each command remains a small, stable icon target of at least `32px` square on
  medium widths;
- one tray with two internal clusters: five discovery commands, then a subtle
  separator or larger gap, then two reading-comfort commands;
- hover and focus states may use subtle inset treatment without changing size;
- total tray width should be narrower than the current bottom row.

The row must look intentional as a control tray, not like loose icon strokes
floating across the panel.

Pressed/current state must remain visible without using the old blue underline
or active-page bar. Text size and OpenDyslexic need a quiet but detectable
`aria-pressed="true"` visual state.

## Accessibility and Behavior

The tray reuses existing command elements, labels, ARIA state, keyboard behavior,
and link/button targets. Text labels remain visually hidden but accessible.
Focus-visible treatment must remain clear enough for keyboard users.

The map collapse button remains in the header and keeps its existing expanded
state behavior.

Sighted pointer and keyboard users should be able to identify icon-only controls
without guessing. The implementation should provide hover and keyboard-focus
tooltips or an equivalent visible-on-focus label treatment. Hidden text alone is
not enough for this tray.

The tray container must not clip focus indication. Focusing a command must not
change its measured width or height.

## Testing

Add or update browser-driven e2e coverage to verify:

- the expanded medium map remains full-height and compact width;
- the tray appears under the header and above `Page N of M`, with measured box
  order `header <= tray <= page position <= map list`;
- the bottom tool strip is absent in the medium expanded map;
- all seven expected command targets remain visible and icon-only, with exact
  accessible names: Search, Graph, Practice, Tasks, Schedule, Text size, and
  OpenDyslexic;
- visible command count is exactly seven, with no duplicate old strip;
- the tray is left-aligned near the title edge, not centered;
- the tray width is narrower than the previous bottom strip and less than 90%
  of the map width;
- the tray is not placed at the bottom of the map;
- the tray has a non-transparent neutral background, a visible border, no top
  border artifact, no shadow, and pill-like radius;
- commands have no active blue bar, underline artifact, or unintended background;
- command focus is visible and does not resize the command;
- Text size and OpenDyslexic pressed/current states are visible without a blue
  underline/bar;
- mobile drawer comfort chrome is not regressed.

Breakpoint coverage should include:

- `639px`: mobile drawer still opens as a modal with existing comfort chrome.
- `640px` and `767px`: narrow-medium tray remains under the header and is not
  reset by later narrow-medium CSS.
- `768px`, `912px`, and `1279px`: medium tray geometry remains stable.
- `1280px`: desktop behavior is unchanged or explicitly verified if touched.

The existing host and Docker gates remain the final verification path:

- `./scripts/check.sh`
- `./scripts/check-docker.sh`

## Implementation Notes

Prefer a small renderer markup move over fragile CSS visual reordering when
needed to make DOM order match visual order. Current generated markup places
`Page N of M` inside the course-map header and tools after the map list; the
implementation plan should inspect that shape and choose the smallest stable
change.

Shared selectors for `.raya-course-map-tools` and `.raya-course-map-tool-grid`
also affect mobile drawer chrome. Medium tray styling must be scoped so it does
not shrink or restyle the mobile drawer tool area.
