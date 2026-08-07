# Course Tree Title Wrapping Design

**Date:** 2026-08-07
**Status:** Approved

## Goal

Make every course-map title, including the root, readable at natural multiline
length without changing tree behavior or rail geometry.

## Design

Course-map rows retain their fixed chevron/spacer column. Within the title link,
the structural number and title become two grid columns: a compact intrinsic
number column and a flexible title column. Titles wrap at ordinary word
boundaries over as many lines as needed. Unbroken authored identifiers retain
emergency wrapping so they cannot create horizontal overflow.

The root remains a normal course-map row and uses the same link grid whenever
it has a structural number/title pair; it receives no special compact or
single-line treatment.

## Scope

- Update only course-map link/number/title CSS.
- Preserve the `256px`/`288px` responsive rail widths, nesting geometry,
  chevrons, disclosure/title ownership, focus, filtering, drawer, and static
  fallback.
- Add browser coverage for ordinary multiword wrapping, root-row parity, and
  unbroken-identifier containment at both 1280px and 1312px.

## Non-Goals

- No markup, runtime, storage, navigation, typography-size, or color changes.
- No line clamp, ellipsis, text truncation, or forced single-line labels.

## Verification

- Assert a number/title two-column link grid and that the title begins in a
  stable second column.
- Assert a representative multiword title grows to at least two lines when
  constrained, has no character-level word break, and remains fully visible.
- Assert the root link has the same layout contract and unbroken identifiers
  remain contained with no document horizontal overflow at 1280px and 1312px.
