# Desktop Command Bar Continuity Design

## Context

The current reset renderer has adapted much of the useful old-main UX: local skins,
reader comfort controls, collapsible course map, collapsible learning rail,
discovery workspaces, and the generated graph surface. A fresh desktop probe of
the render fixture showed the normal reader command bar occupying about 254px at
1600px wide. That makes the first viewport feel like chrome first and learning
second, even though the page shell and side rails work correctly.

## Goal

Make normal reader pages feel more continuous on desktop by keeping the top
command bar compact, stable, and app-like while preserving every existing static
contract.

## Recommended Approach

Use the existing generated header and CSS tokens. Do not redesign the whole
reader shell in this slice. Compact the normal reader command bar at desktop
widths by:

- giving the reading context and tool groups explicit flex bounds;
- hiding nonessential text labels earlier on normal reader pages while keeping
  accessible labels;
- reducing the desktop search form footprint without removing search;
- preventing the top bar from wrapping into many rows at 1280px and wider;
- keeping mobile and discovery workspace command bars on their current rules.

This is preferable to replacing the shell because the current renderer already
has tests for course-map collapse, learning-rail collapse, OpenDyslexic, graph
links, no external requests, and static parity. The issue is density and
continuity, not missing architecture.

## Constraints

- No browser-side MathJax, external renderer, CDN, backend, or fetch dependency.
- No persisted shell state beyond the existing local accessibility preference
  resources.
- No learner progress, mastery, scoring, or personalization claims.
- Preserve all existing command semantics, keyboard focus, `aria-label`,
  `aria-expanded`, and `aria-pressed` behavior.
- Use skin tokens rather than hard-coded visual palettes.
- Keep discovery workspace command bars out of scope unless a shared rule must be
  protected.

## Test Strategy

Add a browser-driven render-fixture test before implementation. At a desktop
viewport, the test should prove:

- the normal reader top bar height stays compact;
- the article starts in the first viewport below the command bar;
- command groups remain visible and reachable;
- the search input remains usable;
- there is no horizontal overflow;
- mobile/tablet behavior remains covered by existing drawer and collapse tests.

## Documentation Impact

This slice is implementation-focused and follows existing reader shell and
learning science docs. It should not change authoring syntax or role
documentation. If later slices expose new controls or authoring options, update
English and Spanish role docs then.

## Acceptance

- A failing e2e test captures the current desktop command-bar height problem.
- CSS changes make the test pass without changing generated HTML contracts.
- Existing focused reader shell, graph, accessibility, and render-debug checks
  still pass.
- Local preview at the render fixture shows the compact command bar at the same
  static URL.
