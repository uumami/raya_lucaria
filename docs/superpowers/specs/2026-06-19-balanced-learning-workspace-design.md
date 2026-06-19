---
id: superpowers-balanced-learning-workspace-design
title: Balanced Learning Workspace Renderer Redesign
status: ready
created: 2026-06-19
---

# Balanced Learning Workspace Renderer Redesign

## Problem

The current renderer shell is technically functional but visually and ergonomically weak. The screenshot review showed these concrete failures:

- the collapsed course map becomes a narrow column with wrapped vertical text;
- the main article is boxed between two competing side panels and does not feel primary;
- the right rail dominates available space while showing little useful content;
- collapsible controls are visually unclear and feel like debug scaffolding;
- the default Eva-inspired skin overwhelms reading with broad saturated background color;
- the shell feels incremental rather than designed as one coherent learning workspace.

This is now a whole-shell redesign, not another small patch.

## Approved Direction

Use the **Balanced Learning Workspace** direction.

On desktop, the course map is expanded by default. This is the best UX because students need course orientation, and desktop viewports have enough room to show navigation without harming reading. The map remains collapsible, but collapse produces a usable icon/page rail, not squeezed text.

The main article is the primary surface. It should have the strongest visual hierarchy, a readable line length, and enough width for math, numbered objects, tables, and examples.

The right learning rail is a compact utility region. It supports scanning and orientation, but it must not compete with the article. Its accordion panels are useful for metadata, contents, prerequisites, sequence, and status.

Do not persist expanded/collapsed shell state in this loop. Predictable first paint is more important than remembering a local preference. Persistence may return later only if it can be applied without layout shift.

## Layout Contract

### Desktop

Desktop uses a three-region grid:

1. Course map: about `220px-260px`, expanded by default.
2. Article: centered, fluid, and visually primary, with a comfortable max readable width around `780px-860px`.
3. Learning rail: about `260px-300px`, compact and secondary.

The page max width may remain generous, but region widths must be intentional. The shell should use available computer screen space without stretching text lines into unreadable lengths.

The course map collapse state becomes an icon rail:

- width about `56px-72px`;
- no vertical wrapped words;
- active page remains visible through number/icon and accessible label;
- expanded/collapsed state uses a clear button with icon-like affordance;
- hidden links are removed from keyboard and screen-reader navigation while collapsed.

### Mobile

Mobile keeps article-first priority:

1. Top command bar;
2. article;
3. course map as a drawer or bounded section;
4. learning rail panels.

Mobile must not show three columns, clipped navigation, or horizontal overflow. Collapsed controls must remain large enough to tap.

## Visual Design

The default skin remains Eva Unit 02 inspired, but it must be readable first:

- use Eva red/orange/yellow as accent and identity, not full-page saturation;
- use neutral article surfaces and strong text contrast;
- use green accents sparingly for active/success state;
- avoid broad pale-yellow backgrounds around all regions;
- avoid oversized borders and nested card feeling;
- keep cards only for real content objects, right-rail panels, and bounded utilities.

The shell should feel like a modern learning workspace:

- dark or strong top command bar with restrained tool buttons;
- clean course map list with active-page highlighting;
- article surface that looks like the place to read and learn;
- right rail as compact accordions;
- consistent `8px` or smaller radii unless a local pattern requires otherwise;
- smooth transitions only for intentional user actions, not initial page load.

## Interaction Design

### Course Map

The map is expanded on desktop first paint. Collapse is explicit click/tap only. Hover must not expand or move layout.

Collapsed map behavior:

- show compact icon/page-number rail;
- keep current page visible;
- expose accessible labels for collapsed controls;
- hide full map text from visual layout and from focus order.

Expanded map behavior:

- show full course labels;
- current page is visually distinct;
- navigation links are keyboard reachable;
- no layout jump on page load.

### Learning Rail

Right rail panels are accordion panels:

- `On this page` open by default when available;
- `Summary` open by default when available;
- metadata panels such as `Status`, `Estimated time`, `Tags`, `Prerequisites`, and `Sequence` collapsed by default;
- panels with focusable children must use `aria-hidden`, `inert`, and correct tab behavior while collapsed;
- panel headers must be clear buttons, not plain headings with tiny symbols.

### Reader Controls

Top controls should be compact and understandable:

- course map toggle;
- OpenDyslexic toggle;
- later skin/appearance control when accepted;
- no visible instructional text describing how the controls work.

On desktop, the top course-map toggle and the map-region collapse control operate the same expanded/collapsed state. On mobile, the top course-map toggle controls the mobile map drawer/section state.

## Accessibility Requirements

The redesign must preserve:

- semantic regions for top tools, course map, article, and learning rail;
- keyboard operation for all toggles;
- visible focus rings;
- no focus leaks into hidden course-map or rail content;
- no screen-reader exposure of collapsed hidden content;
- no horizontal overflow at desktop or mobile breakpoints;
- no external CSS, font, script, renderer, or CDN requests;
- local OpenDyslexic resources;
- build-time MathJax only.

## Renderer And Code Boundaries

Implementation should remain in the static renderer package:

- `packages/static/src/raya_static/builder.py` owns generated shell markup.
- `packages/static/src/raya_static/rendering.py` owns rich renderer CSS.
- `packages/static/src/raya_static/shell.py` owns local shell interaction JavaScript.
- `packages/static/src/raya_static/skins.py` owns skin tokens; do not hard-code course-specific colors outside the token system unless the existing renderer already does so for shared structure.

Keep the change renderer-scoped. Do not add a frontend framework, runtime app, backend service, or browser-side MathJax.

## Documentation Impact

Update the foundation and role docs so they no longer describe the failed collapsed-by-default desktop shell as the intended current behavior.

Required documentation updates:

- `docs/foundation/20_learning_renderer_contract.md`;
- English role docs for professors, contributors, students, and agents;
- Spanish role docs for profesores, colaboradores, estudiantes, and agentes.

Documentation should describe:

- desktop course map expanded by default;
- collapse to compact rail when readers want more focus;
- right rail accordion behavior;
- article-first mobile behavior;
- no personal progress claims.

## Testing Strategy

Use TDD for implementation.

Required tests:

- static HTML contract for expanded desktop-first shell markup;
- browser test for course map collapse to compact rail without vertical text;
- browser test for re-expansion and accessible link restoration;
- browser test for right rail panel collapse/expand with focusable content;
- browser/mobile layout test for article-first order and no horizontal overflow;
- render-debug screenshot/report tests for desktop expanded and collapsed states;
- no external request and no browser-side MathJax regressions;
- docs coverage test for updated role/foundation language.

Verification should include:

- focused browser/static-read-path tests;
- focused contracts;
- `./scripts/check-render-debug.sh`;
- host `./scripts/check.sh` after implementation;
- Docker check if the implementation changes shared renderer behavior enough to affect the reference environment.

## Non-Goals

This redesign does not add:

- personal progress, completion, mastery, analytics, or adaptive review;
- inferred goals or related practice;
- a new framework or dynamic web app;
- browser-side MathJax;
- external assets or CDN requests;
- persisted shell layout state.

## Implementation Notes

The implementation plan should choose exact measurements and tokens after checking the current CSS and fixture screenshots. The target ranges are defined here, but pixel-perfect values should come from testable desktop and mobile behavior.
