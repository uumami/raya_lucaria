# Course Rail Readable Width Design

**Date:** 2026-08-07
**Status:** Approved

## Goal

Make the expanded desktop/tablet course rail easier to read in deeply nested
course maps without changing its interaction model.

## Chosen Approach

Use a fixed 288px expanded rail and a 12px indentation step for course-map
children. This is a small, controlled adjustment to the existing FDD-style
tree: it adds 32px of usable rail width and avoids consuming that gain through
deep nesting.

## Scope

- Change the expanded course-map column and course-map inline size from 256px
  to 288px at structural desktop/tablet widths (640px and above).
- Change each nested course-map child guide/indentation step from 16px to
  12px.
- Preserve the 48px collapsed rail, the 640px structural breakpoint, phone
  drawer behavior, controls, disclosure/title ownership, accessibility state,
  and static fallback.

## Non-Goals

- No typography, color, row-height, or navigation-content redesign.
- No change to the accordion, filtering, stored preferences, or focus rules.
- No mobile drawer-width change.

## Verification

- Update structural rail geometry coverage to expect a 288px expanded rail.
- Assert the nested guide/indentation step is 12px and that deep labels retain
  more usable title width without overlap or document horizontal overflow.
- Re-run the focused rail-density and browser geometry suites.

