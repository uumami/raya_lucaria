---
title: Collapsible Learning Shell Design
date: 2026-06-18
status: approved-for-plan
---

# Collapsible Learning Shell Design

> **Supersession note, current as of the balanced learning workspace update:**
> this historical design's collapsed-by-default and stored-preference decisions
> are superseded. Current shell behavior is expanded by default, non-persistent,
> and collapsible by explicit click to a compact map rail. Do not implement
> course-map `localStorage` persistence from this document.

## Goal

Improve rendered course comfort, learning orientation, and desktop usability by
adding an intentional collapsible learning shell to the Glintstone static
renderer.

The selected scope is **Collapsible Shell + Page Tracking + Desktop Polish**.
This loop should make every rendered course page easier to read and navigate
without adding personal progress, dynamic study state, backend dependencies, or
external renderer resources.

## Current Context

The current renderer already has a learning shell:

- a top command bar with local OpenDyslexic toggle;
- a left course map;
- a central article;
- a right learning rail with summary, status, page contents, prerequisites, and
  sequence links when source/artifact data exists;
- build-time MathJax and local static resources;
- render-debug checks for screenshots, overflow, external requests, raw TeX,
  and shell region structure.

This is a solid static baseline, but the default desktop layout still keeps both
rails fully expanded. That consumes reading space, makes the page feel busier
than necessary, and leaves the student with less article width than a learning
surface should have. On mobile, the course map is visible before the article,
which is useful for structure but not ideal for immediate reading comfort.

The user compared this against a previous course page that used a persistent
collapsible course sidebar, section toggles, top previous/next navigation, and
strong visual hierarchy. That reference is useful for interaction patterns, but
Raya must not copy its external CDN/font dependencies, mobile overflow, or any
dynamic-state implication.

## Learning Rationale

The renderer should reduce extraneous cognitive load and preserve attention.
Navigation is important, but it should not compete with the lesson. The best
default for study is therefore intentional disclosure:

- article reading space is stable by default;
- course navigation is available through an explicit click;
- no hover-triggered layout movement interrupts reading;
- the current course position remains visible even when the full map is
  collapsed;
- previous/next movement is available without hunting through a sidebar;
- page and section tracking expose structure without pretending to know personal
  progress.

This follows the existing learning-science foundation: support orientation,
signaling, segmenting, readability, and accessibility while keeping static HTML
honest.

## Requirements

1. Superseded: the desktop left course map no longer defaults to a slim
   collapsed rail. Current behavior is expanded by default and may collapse by
   explicit click to a compact map rail.
2. The full course map expands only by intentional user action, not by hover.
3. The course-map toggle is a real button with `aria-expanded`,
   `aria-controls`, keyboard focus, and an accessible label.
4. Clicking the toggle opens or closes the full map.
5. Pressing `Escape` while the full map is open closes it.
6. Selecting a course-map link must never block navigation. Historical stored
   reader preference behavior is superseded and must not be implemented.
7. Superseded: the open/closed preference is not stored in `localStorage`.
   Current course-map state is non-persistent UI state only.
8. The current page remains visible in the collapsed rail through a compact
   marker, number, or label.
9. The central article gets wider and clearer desktop priority when the map is
   collapsed.
10. Previous/next navigation appears near the top of the article and remains
    available near the bottom or in the learning rail.
11. The right learning rail remains compact, sticky on desktop, and lower
    priority than the article.
12. Mobile pages put the article before large navigation surfaces.
13. Mobile course navigation opens through a top control, drawer, or compact
    disclosure rather than appearing as a large block before the article.
14. Mobile layout must not introduce horizontal overflow.
15. Page contents should highlight the active heading when this can be done with
    local static JavaScript and current heading anchors.
16. Any page-position label must describe course structure only, such as
    `Page 3 of 18` or a section/page number. It must not claim completion,
    mastery, score, or personal progress.
17. Shell controls must use local static resources only.
18. No external CSS, fonts, scripts, renderer requests, or CDN dependencies may
    be introduced.
19. Preview and copied static deployment must serve the same shell resources.

## Non-Goals

- No personal progress, completion, mastery, analytics, or adaptive
  recommendations.
- No browser-side MathJax conversion.
- No backend, account, identity, or study-state package work.
- No inferred goals, inferred assignments, or inferred related practice from
  prose.
- No arbitrary JavaScript injection from course authors.
- No hover-first expansion as the default behavior.
- No redesign of numbered objects, math authoring, proofs, static environments,
  or skin token contracts in this loop.

## Approach

### Shell Markup

Keep the semantic region order:

1. top command bar;
2. main learning shell;
3. course map navigation;
4. article;
5. learning rail.

Add a course-map toggle in the top command bar or at the start of the left rail.
The toggle should control the full course map with `aria-controls` and
`aria-expanded`. The target region should have a stable ID so render-debug can
inspect it.

The collapsed rail should still expose enough structure for orientation:

- course identity or compact course mark;
- current page marker;
- current unit/page number when available;
- a clear expand button.

Do not hide the article behind navigation on initial render.

### Shell Behavior

Add a small local shell script under the renderer static resources, for example
`artifact/site/_raya/render/shell.js`. It should:

- initialize from the expanded static default;
- apply a class or data attribute to the document when the map is expanded;
- update `aria-expanded`;
- support `Escape` to close;
- keep course-map state non-persistent; do not read or write `localStorage`;
- degrade cleanly when JavaScript is disabled by showing usable static
  navigation.

The script must not fetch data, call external origins, infer learning state, or
depend on a framework.

### Desktop Layout

Use CSS grid states instead of DOM mutation:

- collapsed state: slim left rail, wide article, compact right rail;
- expanded state: wider left course map, article remains readable, right rail
  may narrow or stack if needed at intermediate widths;
- large desktop: make meaningful use of horizontal space without overlong line
  lengths;
- medium desktop/tablet: prefer article stability over keeping both rails
  visible.

The page should feel intentionally designed, but article text, math, code, and
tables remain the highest-contrast, least-decorative surfaces.

### Mobile Layout

Mobile should prioritize reading:

- top command bar includes the course-map control;
- article appears before the full course map in the visual reading path;
- full course navigation opens as a drawer, overlay, or compact disclosure;
- learning rail content appears after the article or behind a clear context
  control;
- no horizontal overflow at common mobile widths.

The exact mobile implementation can be chosen during the implementation plan,
but it must preserve semantic accessibility and static-file behavior.

### Page Tracking

Use current artifact/navigation data and current heading anchors only. The
renderer may show:

- current page in course map;
- current page number or position;
- previous/next links near the article top;
- active heading in the page contents through local intersection-observer
  behavior when available.

The renderer must not label personal progress. Wording such as `Page 3 of 18`
is acceptable. Wording such as `30% complete`, `completed`, or `mastered` is
not acceptable in this static shell.

### Render Debugging

Extend render-debug inspection to cover the new shell:

- required shell controls exist;
- required controlled region IDs exist;
- collapsed and expanded screenshots can be produced;
- no horizontal overflow in desktop or mobile states;
- no external requests are introduced;
- copied static-site parity still serves the same shell resources.

Debug artifacts remain local evidence and must not be committed.

## Documentation

Update role docs in English and Spanish when implementation changes behavior:

- professors: how students will experience course navigation, what structural
  metadata is safe to rely on, and why static pages do not claim progress;
- contributors/collaborators: how to review shell behavior, accessibility, and
  local-resource boundaries;
- students: how to use the expanded-by-default course map, compact collapsed
  rail, page contents, previous/next
  controls, and OpenDyslexic toggle;
- agents: how to verify shell behavior, render-debug artifacts, no external
  requests, and local/deployed static parity.

Update foundation renderer guidance where needed, especially
`docs/foundation/20_learning_renderer_contract.md`, so the shell contract names
expanded-by-default navigation, compact collapsed rail behavior, and static
page tracking explicitly.

## Testing

Use TDD before production edits.

Expected coverage:

- contract tests for generated shell markup, toggle attributes, controlled IDs,
  and shell resource links;
- static builder tests for course map, article, and learning rail order;
- browser/e2e tests for expanded desktop default, explicit collapsed click state,
  `Escape` close behavior, no hover requirement, and mobile article priority;
- render-debug tests for shell inspection fields and screenshots;
- static-read-path tests proving copied `artifact/site/` serves the same local
  shell CSS/JS resources;
- no-external-request checks;
- focused fixture build and artifact inspection for
  `examples/courses/render-fixture`.

## Acceptance Criteria

- Desktop rendered pages default to an expanded course map.
- A click-only toggle expands and collapses the full course map.
- The toggle uses accessible button semantics and updates `aria-expanded`.
- The current page remains visible while the left rail is collapsed.
- Article width and visual priority improve on desktop.
- Previous/next navigation is visible near the article top.
- Mobile pages do not put a large course map before the article.
- Mobile pages have no horizontal overflow.
- Active section tracking is implemented if it can be done from current heading
  anchors with local static JavaScript; otherwise the implementation plan must
  explicitly defer it.
- No external CSS, font, script, renderer, or CDN requests are introduced.
- Preview and copied static deployment use the same local shell resources.
- English and Spanish role docs describe the new shell behavior.
- Focused tests, render-debug checks, fixture build, artifact inspection, and
  the normal archive gates pass before merge or push.
