# Course Tree Title Wrapping Design

**Date:** 2026-08-07
**Status:** Approved

## Goal

Make every course-map title, including the root, readable at natural multiline
length without changing tree behavior or rail geometry.

## Design

Course-map rows retain their fixed chevron/spacer column and existing
number/title flex layout. Titles wrap at ordinary word boundaries over as many
lines as needed. Unbroken authored identifiers retain emergency wrapping so
they cannot create horizontal overflow. This avoids a conditional grid layout:
roots and authored titles that already contain their structural number have no
separate number span.

The root remains a normal course-map row and uses the same title wrapping rule;
it receives no special compact or single-line treatment.

## Scope

- Update only the winning course-map title wrapping CSS declaration.
- Preserve the `256px`/`288px` responsive rail widths, nesting geometry,
  chevrons, disclosure/title ownership, focus, filtering, drawer, and static
  fallback.
- Add browser coverage for ordinary multiword wrapping, root-row parity, and
  unbroken-identifier containment at both 1280px and 1312px.

## Non-Goals

- No markup, runtime, storage, navigation, typography-size, or color changes.
- No line clamp, ellipsis, text truncation, or forced single-line labels.

## Verification

- Assert ordinary titles use `word-break: normal` and `overflow-wrap:
  break-word`, while unbroken identifiers retain emergency containment.
- At real 256px and 288px rail geometry, assert the unnumbered root and the
  depth-three `Detailed Requirements And Registration Constraints` title wrap
  naturally when needed, remain fully visible, and never use a line clamp or
  ellipsis.
- Assert per-title Range rectangles and title/link/row/navigation bounds, not
  only document overflow, for containment.
- Assert the same behavior in a 390px coarse-pointer open drawer and in the
  JavaScript-disabled static fallback; wrapped links retain focus visibility,
  44px touch targets where required, and Arrow navigation to the next visible
  node.
