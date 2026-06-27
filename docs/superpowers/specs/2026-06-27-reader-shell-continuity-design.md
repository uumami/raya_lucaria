---
id: superpowers-reader-shell-continuity-design
title: Reader Shell Continuity
status: accepted
---
# Reader Shell Continuity

## Context

The reset renderer already has the right learning shell primitives: a sticky command bar, an expanded-by-default course map, an article-first reading surface, a collapsible right learning rail, mobile drawers, local comfort controls, and generated static workspace handoffs. The old `main` branch adds a useful UX lesson: collapsible chrome should feel like one continuous workspace, using width and transform transitions with compact tabs instead of abrupt page jumps.

The old implementation cannot be copied. It persists navigation state in `localStorage`, depends on Eleventy/Tailwind conventions, and includes external or legacy renderer assumptions. The current framework rules remain authoritative: no browser-side MathJax conversion, no CDN/external renderer requests, no runtime fetch for shell state, no stored navigation/progress state, and no learner-state semantics.

## Goal

Make desktop reader shell collapse, expand, and reader-focus changes feel continuous and intentional while preserving the current static renderer contract.

## Design

This slice keeps the existing generated HTML structure and shell script ownership:

- `packages/static/src/raya_static/rendering.py` owns the CSS and generated markup classes.
- `packages/static/src/raya_static/shell.py` owns volatile shell state and transition markers.
- `tests/e2e/test_preview_static_read_path.py` owns browser assertions against rendered behavior.

The visible behavior should be:

- Desktop map and context collapses animate as a coordinated workspace resize.
- The article grows without a blink or horizontal overflow when map and/or context collapse.
- Compact `Map` and `Context` tabs remain horizontal, operable, and visually stable.
- During collapse and expand transitions, the disappearing full panel bodies should not flash wrapped text, create keyboard traps, or expose inaccessible hidden controls.
- Reader focus should collapse both side regions through the same transition path, not through a visually different shortcut.
- Tablet and mobile keep the current drawer/body behavior and do not gain desktop collapsed rails.
- Reduced-motion users get the same final states with transitions disabled.

The implementation should prefer CSS motion and existing transition data attributes over new state. The shell may add a small transition marker when expanding as well as collapsing if tests prove it is needed. It must not persist map, rail, focus, or drawer state.

## Test Contract

Add browser tests that prove rendered behavior, not CSS strings alone:

- At a desktop viewport, sample article, map, and rail widths before transition, during the first animation frame after a command, and after transition cleanup.
- Assert the article width changes monotonically in the intended direction and never overflows the viewport.
- Assert transition markers are present only during the transition window and are cleaned up afterward.
- Assert compact tabs remain visible, horizontal, and at least 40px wide after collapse.
- Assert expanding from a compact tab restores the full panel without leaving hidden/inert state behind.
- Assert no `localStorage` or `sessionStorage` keys are written by shell map, rail, or reader-focus controls.
- Assert reduced-motion media disables shell transition durations while preserving the same final states.

## Non-Goals

- No new course data, graph schema, search index, or artifact schema.
- No persistent shell state beyond existing comfort preferences for text size and OpenDyslexic.
- No hover-triggered map expansion.
- No personal progress, mastery, recommendation, or adaptive language.
- No external resources, CDN scripts, browser-side MathJax conversion, or runtime data fetch.
- No replacement of the current renderer with old `main` architecture.

## Verification

Run focused browser tests for the reader shell and then `./scripts/check-render-debug.sh`. If CSS or shell script changes affect generated static resources, verify `artifact/site/_raya/render/shell.js` is local and that browser requests stay within the preview origin.
