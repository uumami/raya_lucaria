---
id: mobile-reader-chrome-compaction
title: Mobile Reader Chrome Compaction
status: ready
date: 2026-06-27
workflow: superpowers
---

# Mobile Reader Chrome Compaction

## Problem

Current render-fixture evidence shows the mobile reader command bar consumes
about `220px` of vertical space on a `390px` wide viewport. The lesson title
then starts around `380px` to `420px` from the top of the viewport, so the
first screen reads as tool chrome before learning content.

The legacy branch kept reader controls reachable, but the current reset shell
must keep the article primary, avoid persisted shell state, and avoid copying
legacy runtime architecture.

## Design

Keep all current mobile commands reachable, but make the small-screen command
bar more compact:

- keep the reading context, search handoff, workspace links, course-map button,
  text-size control, OpenDyslexic control, and skin control available;
- keep the course map as an explicit drawer opened by the map command;
- keep mobile command labels visually clipped where icons and accessible labels
  already name the controls;
- reduce vertical gaps, padding, and row height in the mobile command bar so
  the first lesson title appears substantially earlier;
- preserve touch targets at or above the existing `36px` command minimum;
- do not add browser storage, external assets, runtime fetches, or new shell
  state.

This slice is presentation-only. It does not change generated navigation data,
graph/search/practice/task/schedule URLs, mobile drawer behavior, comfort
preference semantics, skin authority, MathJax rendering, or artifact data.

## Testing

Use TDD against the render fixture:

- add a browser assertion at `390px` that the top command bar height stays below
  a compact threshold and the first `h1` appears earlier in the first viewport;
- assert visible command touch targets remain at least `36px` tall;
- assert the search form, map command, OpenDyslexic command, text-size command,
  and workspace links remain reachable;
- keep existing no-overflow, drawer, comfort-toggle, and shell layout coverage.

Finish with the focused reader-shell e2e tests, render-fixture build,
`git diff --check`, and `./scripts/check-render-debug.sh`.
