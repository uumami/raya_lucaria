---
title: Course Map Navigator Polish Design
date: 2026-06-25
status: accepted
workflow: superpowers
---

# Course Map Navigator Polish Design

## Context

The current static renderer already rebuilt the core shell, course map, learning
rail, discovery workspaces, graph page, comfort controls, and graph focus mode.
The old `main` branch still has a useful navigation pattern: a persistent
sidebar with compact workspace links, explicit section expand/collapse, mobile
overlay behavior, and clear controls close to the reading surface. Its
implementation relies on old Eleventy/Tailwind/Pagefind/CDN/browser-storage
patterns that are not current authority, but the interaction model is worth
adapting.

Independent audits selected shell navigation as the next highest-value UX
fusion slice. The work should improve the reader's ability to scan and move
through course structure without adding learner state, runtime data loading, or
external resources.

## Goals

- Make the current course map feel like a real learning navigator on desktop:
  dense, scannable, and controllable without hiding the article.
- Add course-map section controls inspired by the old sidebar: expand current
  path, expand all, collapse other sections, and keep filtering predictable.
- Add mobile drawer parity for the course map and workspace shortcuts while
  preserving the current article-first mobile layout.
- Keep all state volatile and local to the current page session. Do not use
  `localStorage`, `sessionStorage`, cookies, fetch, XHR, backend calls, or
  external scripts.
- Preserve the compact collapsed map rail as operable navigation, not
  decoration.

## Non-Goals

- No artifact schema or generated graph data changes.
- No Pagefind, Tailwind, Eleventy templates, service worker, Google fonts,
  external renderer, external graph library, CDN, or browser-side MathJax.
- No progress, mastery, recommendation, adaptive next-step, grading,
  submission, attempt, personal due-state, or analytics language.
- No persistent sidebar state from the old branch.
- No changes to Search, Graph, Practice, Tasks, or Schedule runtime scripts
  unless a shared shell link target needs a static href update.

## Design

### Desktop Course Map Controls

The course map header will gain a compact control row:

- `Current`: expands the ancestor chain for the current page and scrolls it into
  view.
- `All`: expands every map section.
- `Less`: collapses non-current top-level branches while preserving the current
  ancestor chain.

These controls operate only on already-rendered navigation data. They update
`aria-expanded`, child `hidden`, `aria-hidden`, and existing
`data-raya-map-expanded` values through `shell.js`. They do not persist across
pages.

Filtering remains local and temporary. While a filter is active, matching
descendant branches may open temporarily. Clearing the filter restores the last
volatile map expansion state.

### Mobile Map Drawer

On tablet/mobile widths, the command bar's existing course-map button becomes
an explicit drawer opener rather than a desktop-width layout toggle. The course
map appears as a fixed sheet with a lightweight backdrop and close control. The
sheet contains the existing course map, workspace shortcuts, filter, and section
controls.

The normal document order remains article-first. The drawer is an intentional
overlay opened by a button; when closed, map internals are hidden from keyboard
navigation and screen readers. Escape closes the drawer and returns focus to
the opener. The drawer must not affect the right learning rail's mobile
accessibility rule: the rail body remains visible and reachable when rail
collapse controls are hidden.

### Desktop Collapsed Rail

The existing compact map rail remains available on desktop. The polish should
keep visible rail items as real anchors with stable accessible names. Section
controls and filter inputs are hidden in compact rail mode, but the current-page
marker remains visible.

### Visual Treatment

The course map should use less vertical space and clearer hierarchy:

- smaller row gaps and stronger active/ancestor contrast;
- tighter workspace shortcut badges;
- section controls styled as small static shell buttons;
- no one-off decorative gradients or marketing panels;
- skin variables continue to control colors.

The result should feel closer to the old sidebar's density and immediacy while
remaining a current Glintstone shell surface.

## Implementation Surfaces

- `packages/static/src/raya_static/builder.py`: render static control buttons,
  drawer close affordance, and any needed attributes.
- `packages/static/src/raya_static/shell.py`: implement volatile section
  control actions, mobile drawer open/close/focus behavior, and responsive
  safety.
- `packages/static/src/raya_static/rendering.py`: add drawer/backdrop,
  compact-control, and density CSS using existing skin variables.
- `docs/foundation/20_learning_renderer_contract.md`: update the course shell
  contract because this adds mobile drawer and explicit section-control
  semantics.
- Focused tests in `tests/contracts/test_static_builder.py` and
  `tests/e2e/test_preview_static_read_path.py`.

## Accessibility And Safety

- All controls use buttons with accessible names and `aria-expanded` or
  `aria-controls` where appropriate.
- Closed mobile drawer content is not focusable and is hidden from assistive
  technology.
- Escape closes the drawer first, then follows existing desktop map/rail
  collapse behavior.
- Focus returns to the opener after drawer close.
- Responsive transitions cannot leave the drawer or rail in an inert hidden
  state on tablet/mobile.
- The shell script must not contain storage or fetch APIs.

## Testing

Use TDD for implementation. Add failing tests before production changes:

- Contract test asserts new static course-map controls and mobile drawer
  affordances are rendered, and that shell HTML does not include forbidden
  external/storage/fetch surfaces.
- E2E desktop test verifies `Current`, `All`, and `Less` update map expansion
  without losing the current page or compact rail navigation.
- E2E mobile test verifies the map button opens a drawer, Escape/close closes
  it, focus returns to the opener, no horizontal overflow occurs, and the
  learning rail remains accessible.
- Existing shell, graph, render-debug, host, and Docker gates remain the final
  verification path.

## Self-Review

- No placeholders remain.
- The design does not require schema, artifact data, backend, storage, fetch,
  external resources, or learner-state semantics.
- The scope is one implementation loop: course-map navigator polish.
- Foundation update is required because mobile drawer and map section controls
  refine current shell behavior.
