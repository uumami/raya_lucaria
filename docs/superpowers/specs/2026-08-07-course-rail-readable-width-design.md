# Course Rail Readable Width Design

**Date:** 2026-08-07
**Status:** Approved

## Goal

Make the expanded desktop/tablet course rail easier to read in deeply nested
course maps without changing its interaction model.

## Chosen Approach

Use a fixed 288px expanded rail only from 1312px upward and a 12px effective
content indentation step for course-map children. Below 1312px, retain the
existing 256px structural rail. This is a small, controlled adjustment to the
existing FDD-style tree: it adds 32px of usable rail width where the reading
surface can absorb it and avoids consuming that gain through deep nesting.

## Scope

- Introduce a structural-only expanded-width value of 288px from 1312px
  upward. Keep the 256px structural rail from 640px through 1311px.
- Keep the separately sourced phone drawer width at 256px at every phone
  width; the structural width must not change drawer geometry.
- Change each nested course-map child to a 12px total title offset from its
  parent guide (8px guide margin plus 4px child padding).
- Update the affected foundation renderer contract, English and Spanish role
  guidance, and their documentation contracts from the previous unconditional
  256px statement to the responsive structural rule.
- Preserve the 48px collapsed rail, the 640px structural breakpoint, phone
  drawer behavior and 256px width, controls, disclosure/title ownership,
  accessibility state, and static fallback.

## Non-Goals

- No typography, color, row-height, or navigation-content redesign.
- No change to the accordion, filtering, stored preferences, or focus rules.
- No mobile drawer-width change.

## Verification

- Assert 256px expanded structural geometry at 640px, 894px, 1280px, and
  1311px, and 288px geometry at 1312px and wide desktop widths. Keep the
  established reader-width floors at 894px and 1280px.
- Assert a 256px phone drawer at 639px and 390px, including coarse-pointer
  target and focus behavior.
- Assert the 8px guide margin, 4px child padding, and 12px total nested title
  offset, with contained deep long labels and no document horizontal overflow.
- Cover expanded and collapsed rails, the JS-disabled fallback, and the
  639/640, 893/894, 1279/1280, and 1311/1312 boundaries in focused
  rail-density and browser geometry suites.
