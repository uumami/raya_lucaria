# Responsive Shell Hardening Design

## Context

The current renderer already adapts the old `main` branch's useful reader-shell
ideas: sticky command bar, collapsible course map, collapsible learning rail,
article-first mobile flow, local comfort controls, workspace shortcuts, graph
workspaces, and no external renderer dependencies. Independent review found the
next useful fusion slice is not another visual feature. It is making the
responsive shell states harder to break.

The concrete defect is that the shell script collapses the learning rail on
`Escape` whenever focus is inside the rail. Collapsed learning-rail controls and
compact styling are desktop-only. On mobile and tablet widths, those controls
are hidden and the shell is article-first, so `Escape` can make the rail body
`aria-hidden` and `inert` while the visual layout remains a normal stacked rail.

There is also redundant tablet CSS: one `@media (max-width: 1279px)` block sets
a three-column shell and the following block immediately overrides it to
article-first single column. The final behavior is acceptable, but the duplicate
rule makes the intended responsive contract harder to maintain.

## Goal

Harden the reader shell so desktop, tablet, and mobile have explicit, testable
state behavior:

- desktop keeps explicit collapsible map and rail behavior;
- tablet and mobile stay article-first and never enter a hidden collapsed rail
  accessibility state through `Escape`;
- the compact course-map rail remains a real keyboard-operable navigation
  surface on desktop;
- shell and workspace state remains non-persistent except existing comfort
  preferences.

## Design

Keep all existing generated HTML regions and current CSS class names. Change the
shell behavior by adding a desktop-only guard around right-rail collapse. The
same `desktopMapQuery` match media object already owns the desktop shell
threshold, so `Escape` should collapse the learning rail only when that query
matches. When the viewport leaves desktop width, the shell should force the
learning rail back to expanded accessibility state so the visible stacked rail
and `aria-hidden`/`inert` state cannot diverge.

Keep course-map collapse available through the existing command button on
mobile, because current tests and contract allow the map to collapse into a
short stacked region. Do not add persistent sidebar behavior from old `main`.

Clean the duplicate tablet CSS by removing the dead three-column shell rule from
the first `max-width: 1279px` block. The intended tablet/mobile behavior is the
article-first single-column block that follows. Graph and discovery workspace
single-column rules remain in the first block.

Strengthen browser tests around current behavior rather than adding new UI:

- mobile rail `Escape` keeps the rail expanded, visible, non-inert, and with
  collapse controls hidden;
- resizing from desktop collapsed rail to mobile restores the rail body to an
  expanded accessibility state;
- tablet viewport uses article-first shell ordering with no horizontal overflow;
- desktop collapsed course-map links remain focusable, visible enough to be
  operable, and deployment-neutral;
- map and rail collapse/expand cycles do not create storage keys.

## Non-Goals

- No new source or artifact contract.
- No persistent map, rail, graph, search, practice, tasks, or schedule state.
- No old-main `localStorage` navigation state, service worker, Pagefind,
  browser-side math renderer, external font, CDN graph library, or quiz scoring.
- No redesign of graph algorithms or discovery workspace data.
- No pixel-perfect snapshot contract.

## Verification

Focused verification should include the new browser test and the shell CSS
contract test. Completion requires render-debug, host, and Docker gates before
claiming the loop is done.
