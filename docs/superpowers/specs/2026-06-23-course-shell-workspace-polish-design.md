# Course Shell Workspace Polish Design

## Goal

Make the static course shell feel like a cohesive learning workspace on desktop while preserving an article-first mobile flow. The shell must use only current artifact data and local static resources.

## Design

The reading shell keeps the existing three-region model: sticky command bar, left course map, main article, and right learning rail. Desktop should prioritize a wide article column with compact but useful map and context rails. The command bar should act as persistent course chrome with Search, Graph, Practice, map, text-size, and OpenDyslexic controls.

Mobile should keep the article before the course map and learning rail, but the command bar must not consume excessive vertical space. Main reading pages should use the same compact mobile command treatment already used by generated discovery pages: wrap the reading context predictably, keep tools reachable, hide text labels for small command buttons, and prevent horizontal overflow.

## Behavior

- Course map and learning rail remain expanded by default when the shell script loads.
- Course map collapse is explicit click or Escape, not hover.
- Right rail collapse hides its body from keyboard and screen-reader navigation.
- Map, rail, filter, and graph states remain transient. No `localStorage` or `sessionStorage` for shell state.
- Reader comfort controls may continue using local preferences.
- No browser-side MathJax, external renderers, CDN CSS, CDN fonts, or runtime fetches.

## Scope

This loop may change shell markup, `shell.js`, rich renderer CSS, render-fixture expectations, and foundation/role docs when needed. It must not add assignment, progress, recommendation, scored practice, offline app, or inferred learning-goal behavior.

## Testing

Use focused contract and browser tests for:

- desktop article/map/rail proportions;
- mobile article-first layout;
- command-bar compactness on narrow screens;
- no horizontal overflow;
- explicit collapse/expand state and accessibility attributes;
- no external requests, browser-side renderer dependencies, or persisted shell state.
