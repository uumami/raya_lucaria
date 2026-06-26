---
id: superpowers-learning-rail-first-viewport-polish-design
title: Learning Rail First-Viewport Polish Design
status: accepted
---
# Learning Rail First-Viewport Polish Design

## Context

The current reset renderer already adapts many useful legacy-main UX ideas:
an explicit course map rail, collapsible learning context, command bar,
reader controls, course graph, fuzzy discovery workspaces, local skins, and
OpenDyslexic support. The live render fixture shows a more serious desktop UX
problem: the right learning rail is visible as an empty-looking panel in the
first viewport even though its generated content exists.

Root-cause inspection shows the rail content is stretched by CSS grid sizing.
The parent learning shell stretches the rail to match the long article, and
the rail's own grid rows stretch across that height. The generated header and
panel body are pushed far below the visible viewport, so students lose the
context surface that should help orientation.

## Goal

Keep the right learning rail useful in the first desktop viewport and make the
course shell feel like a coherent workspace rather than three disconnected
document columns. This slice should be a focused reset-safe polish pass, not a
legacy-stack port.

## Design

Add a CSS layout invariant for the learning rail:

- the rail remains sticky and aligned to the top of the shell;
- the rail does not stretch its internal grid rows to article height;
- the rail body starts directly under the rail header in the first viewport;
- collapsed rail behavior still turns into the compact `Context` tab on
  desktop;
- mobile/tablet behavior remains article-first with the rail content available
  below the article.

Add a browser regression test against the render fixture that proves the rail
is not merely present in the DOM but visible in the first viewport. The test
should verify that the rail header and first panel body appear near the rail
top and above the desktop viewport fold.

After the bugfix, lightly tune the shared shell CSS so the rails and article
feel more intentional under EVA-style skins:

- keep readable high contrast;
- preserve the current local skin token system;
- avoid external fonts, images, CDN requests, runtime fetches, storage, or
  browser-side renderer dependencies;
- avoid changing generated course data or graph payloads.

## Expected Behavior

- On `reader-ux/` at desktop width, the learning rail shows `Learning context`
  and the first rail panel content in the first viewport.
- The first rail panel body is positioned close to the top of the rail, not
  thousands of pixels below it.
- Collapsing the rail still creates the compact `Context` tab and makes the
  rail body inert.
- The course map and main article keep their current responsive behavior and
  no horizontal overflow is introduced.

## Non-Goals

- No redesign of graph interactions in this slice.
- No new JavaScript state model.
- No imported legacy dependencies such as Cytoscape, Pagefind, Eleventy,
  Tailwind, KaTeX runtime, Mermaid runtime, service workers, or CDN fonts.
- No course schema changes.

## Verification

Use TDD. First add a focused Playwright regression that fails because the first
learning rail panel is below the first viewport. Then implement the minimal CSS
fix and run the focused browser test. Finish with the affected static/read-path
tests and render-debug gate before committing.
