# Navigation-First Course Rail Design

Date: 2026-08-04
Status: approved in brainstorming
Scope: the reader's left course rail at all reader widths

## Relationship To Prior Work

This design supersedes the architectural direction in
`2026-07-29-reader-rail-density-design.md`. The density branch contains useful
tests and partial improvements, but it keeps the earlier rail structure and
does not solve the narrow drawer or scroll-ownership problem as one system.

Implementation must audit the existing `feature/reader-rail-density` commits.
It may retain changes that satisfy this design, but it must remove obsolete
compensations, comments, assertions, and contract wording rather than stacking
another CSS layer over them.

The reference is the navigation model in `/home/uumami/itam/fdd_p26` and the
deployed `https://www.sonder.art/fdd_p26/`. Raya adopts its navigation-first
information architecture, not its templates, JavaScript, storage rules, color
theme, or course-specific content.

## Problem

The left rail currently reads as a large control tray before it reads as the
course index. At narrow widths its controls use large text, repeated borders,
and tall rows. The course tree receives the remaining space and is difficult to
scan. Scroll ownership differs between structural and drawer layouts, so wheel
or touch gestures over parts of the map can be consumed without moving the
expected content.

The partial density work improves individual measurements but keeps different
scroll architectures across width bands. It therefore cannot guarantee the
same behavior in the narrow drawer where the reported problem remains visible.

The course index is the primary navigation surface. Course commands support it;
they must not visually displace it.

## Goals

1. Make the left rail a compact course-navigation surface rather than a grid of
   large controls.
2. Give the expanded rail one native scrolling region in every layout.
3. Use the same semantic content and order in structural and drawer modes.
4. Keep Raya's accepted Search, Graph, Practice, Tasks, Schedule, Context,
   comfort, hierarchy, filtering, and course-position capabilities.
5. Keep long labels readable without letting them dictate the density of every
   row.
6. Preserve Raya's static, foundation-first, accessibility, privacy, and
   non-inference principles.
7. Make collapsed navigation stable and predictable through a 48px mini rail.

## Non-Goals

- Redesigning the right learning rail. It may receive only changes required to
  prevent collisions or invalid paired states.
- Copying the FDD color palette, persistence model, generated hierarchy, or
  Eleventy templates.
- Adding progress, mastery, recommendations, analytics, or remote requests.
- Persisting filter text, scroll position, focus, or drawer state.
- Changing course source schema or authored navigation data.
- Localizing established generated control labels. Spanish text in the visual
  brainstorming mockups was illustrative; existing renderer language rules
  remain authoritative.

## Design Principles

- Navigation first: the tree is the rail's primary working surface.
- One scroll owner: no nested vertical scroll regions in the expanded rail.
- Native behavior: correct CSS structure replaces wheel-event forwarding.
- Stable geometry: the same controls do not jump between unrelated positions.
- Progressive disclosure: dense labels may clamp visually, but their complete
  accessible names and intentional reveal paths remain available.
- Capabilities need a clear home: extra Raya features remain only when their
  purpose and placement are explicit.
- Source truth stays static: runtime state controls display only.

## Information Architecture

The generated left rail uses this order:

```text
Course rail (256px expanded)
|-- Fixed header (48px)
|   |-- Course home
|   |-- Course name
|   `-- Hide map / Close drawer
|-- Central navigation (the only vertical scroller)
|   |-- Course actions
|   |   `-- Six flat links/controls in two columns
|   `-- Content
|       |-- Compact local filter
|       `-- Hierarchical course tree
`-- Fixed footer (48px)
    |-- Text size
    |-- OpenDyslexic
    `-- Structural position N / M
```

The header and footer remain visible while the central navigation scrolls. The
outer rail clips layout overflow and must not become a second vertical scroll
owner.

Structural and drawer layouts render the same header, central navigation,
footer, actions, filter, and tree DOM. Layout changes presentation and modal
semantics; it does not create a second mobile navigation tree.

## Header

The header is 48px high.

- The course-home icon is a deployment-neutral static link.
- The center displays the generated course name. The containing region retains
  the accessible name `Course map`. The visible name is one line with ellipsis;
  its full value remains the accessible name and is available through a tooltip.
- The trailing icon is `Hide course map` in structural expanded mode and
  `Close course map` in drawer mode.
- Header icon controls are 30-32px square, use the established icon library,
  expose accessible names, and provide hover tooltips.

The header does not contain a second Map tile or a full-width text button.

## Course Actions

The central navigation begins with a compact `Course` section. Its controls are
flat links or buttons, not individually bordered cards:

```text
Search        Graph
Practice      Tasks
Schedule      Context
```

The section uses two equal minmax-zero columns. Each action targets a 30px row
and may measure up to 32px after borders and platform rounding, uses a 14-16px
icon and a stable 12-13px interface label, and has a subtle hover, focus,
current, or pressed surface only when state requires it.

Semantics remain distinct:

- Search opens the existing Search workspace.
- Graph, Practice, Tasks, and Schedule retain their existing static workspace
  destinations.
- Context retains its existing control of the right learning rail where that
  control is available.
- The previous inline query form is removed from the rail. Search workspace
  querying remains owned by Search.
- Local tree filtering remains a separate Content control and never navigates.

The six course actions plus two footer comfort controls preserve the eight
accepted reader commands without treating comfort preferences as course
destinations.

## Content Filter And Tree

The `Content` section follows course actions in the same scrolling element.

The compact filter is always available while the Content section is in layout.
It filters rendered course labels locally. Empty results render a concise state
inside the same navigation region. Filter text is volatile and is not restored
after navigation or refresh.

Tree rows use:

- 12-13px stable interface type;
- compact 27-30px single-line row rhythm;
- small indentation and one subtle guide per hierarchy level;
- separate disclosure, sequence, and label geometry;
- a maximum of two visual label lines at rest;
- full visual release on hover, keyboard focus, and the current page;
- the complete authored label as the accessible name at all times.

The current path expands on load. The current row is oriented into the visible
scroll region only when needed. Once orientation completes, ordinary user
scroll is authoritative; observers and animations must not repeatedly pull the
tree back to the current row.

Branch display state may continue using the accepted course-scoped,
tab-isolated session key. It must not move to localStorage.

## Footer And Comfort Controls

The 48px footer contains Text size, OpenDyslexic, and compact `N / M`
structural position.

- Text size changes the authored article and learning content, not navigation
  chrome. The rail retains its stable interface density at every accepted text
  size setting.
- OpenDyslexic may apply to both reading content and navigation because it
  changes font family rather than magnification.
- Comfort controls use icon buttons with accessible names and tooltips.
- Position is course structure, not learner progress.

## Scroll Ownership

The central navigation is the only expanded-rail element with vertical
`overflow: auto`. The outer aside, header, footer, action grid, filter, and tree
must not independently create vertical scroll containers.

At structural widths:

- a wheel or touch gesture inside the central navigation moves it when it can
  scroll in that direction;
- at a central-navigation boundary, native scroll chaining may move the page;
- a gesture over the fixed header or footer may move the page;
- no outer `overscroll-behavior: contain` may swallow those gestures.

In modal drawer mode, background scroll is intentionally locked. A boundary
gesture cannot scroll the inert background; that modal boundary is not treated
as a dead-zone defect. Gestures inside the central navigation still move its
single scroller whenever overflow remains in the requested direction.

No JavaScript wheel forwarding is permitted.

## Geometry And Responsive States

### Expanded Structural: 894px And Wider

- Expanded rail width: 256px.
- Header and footer: 48px each.
- The rail reserves its width in the reader shell.
- The right rail keeps its current independent role and content.

### Structural Intermediate: 640px Through 893px

- The left rail is fixed to the viewport edge and the shell reserves its 256px
  width while it is expanded, matching the existing Raya intermediate family
  selected during brainstorming.
- Content and order are identical to the wider structural rail.
- Only one full rail may remain expanded. Activating Context from the left rail
  expands the right rail and collapses the left to its 48px mini state;
  expanding the left while Context is full performs the inverse handoff.
- Collapsing the left rail produces the same 48px mini rail.

### Drawer: Below 640px

- Structural and mini rails leave layout.
- The existing Course launcher opens the same rail content as a 256px modal
  drawer.
- Drawer behavior includes backdrop, visible close control, Escape closure,
  focus containment, focus restoration, background inertness, and temporary
  background scroll lock.
- The footer remains visible and the central navigation remains the single
  drawer scroller.

### Collapsed Structural Mini Rail

At 640px and wider, collapsed left navigation is a stable 48px rail rather than
a floating 40px opener.

The mini rail retains, in stable positions:

- course home;
- expand course map;
- Text size;
- OpenDyslexic.

The article recovers 208px when the 256px rail collapses. The mini rail remains
reserved in shell geometry. Full map content is hidden, inert, absent from the
tab order, and unavailable to assistive navigation until expanded.

## State Model

Accepted session state remains course-scoped and tab-isolated:

- structural left/right expanded pair;
- collapsed course-map branch identifiers.

The following remain volatile:

- drawer open state;
- filter text;
- central-navigation scroll position;
- current focus;
- active hover;
- orientation attempts and animation state.

Breakpoint reconciliation must update visual state, `hidden`, `inert`,
`aria-hidden`, `aria-expanded`, modal semantics, scroll lock, and focus before
controls become interactive in the new mode. The state machine must not leave a
hidden body focusable or an article inert after the drawer closes.

The FDD sidebar's durable scroll and expansion storage is explicitly not
copied.

## Accessibility

- Every icon-only control has an accessible name and hover tooltip.
- Expanded action targets are at least 30px in their compact layout.
- Mini-rail controls are at least 34px square.
- Focus indicators are at least 3px and do not change geometry.
- Full link text remains exposed despite visual line clamping.
- Disclosure state uses native button semantics and correct `aria-expanded`.
- The modal drawer has a dialog name and `aria-modal=true`.
- Reduced motion removes coordinated transition timing without changing final
  visibility, focus, or inertness.
- Print excludes course navigation.
- Article text magnification does not enlarge interface chrome, but browser
  zoom and user-agent accessibility behavior remain supported. Browser zoom
  may move the page into another responsive band and must receive that band's
  complete, accessible layout.

## Data Flow And Failure Handling

Build-time inputs provide the course name, validated destinations, ordered
hierarchy, current page, and structural position. Runtime code only filters,
discloses, or changes presentation state.

Required workspace destinations must fail existing validation/build gates
rather than render dead actions. Optional data is omitted without reserving an
empty row. An empty local filter result is represented in the navigation, not
as an exception or network fallback.

No rail interaction writes source data, generated artifact data, analytics,
answers, progress, mastery, recommendations, cookies, or network state.

## Implementation Boundaries

- `packages/static/src/raya_static/builder.py`: semantic rail regions, six
  course actions, footer position, and removal of the large inline search form.
- `packages/static/src/raya_static/rendering.py`: single-scroll layout, compact
  action grid, tree density, 256px/48px geometry, drawer parity, and print.
- `packages/static/src/raya_static/shell.py`: state reconciliation, drawer,
  focus, filtering, branch disclosure, and one-shot orientation. It must not
  own wheel routing.
- `packages/static/src/raya_static/accessibility.py`: article-only text-size
  scope and accepted OpenDyslexic scope.
- `packages/static/src/raya_static/shell_geometry.py`: single-source geometry
  values if that remains the established ownership point.

Existing public state attributes and selectors should remain when they express
stable behavior. Internal selectors tied only to the old tile layout may be
replaced. New helpers are justified only where they create a clear header,
navigation, tree, footer, or state-machine boundary.

## Truth-Surface Changes

Implementation requires a foundation amendment before package behavior is
claimed current.

At minimum, update:

- `docs/foundation/20_learning_renderer_contract.md` for six two-column course
  actions, two footer comfort controls, removal of the inline rail query form,
  article-only text scaling, one scroll owner, 256px expanded geometry, 48px
  mini geometry, and drawer parity;
- `docs/foundation/00_index.md` only when its existing renderer summary or file
  inventory would otherwise become inaccurate;
- English and Spanish student and agent guides that enumerate rail controls;
- contract tests binding foundation and role wording.

The new contract replaces the old requirements for eight body tiles, a
separate inline course-search form, and a collapsed floating Map opener.

## Migration From The Density Branch

Before implementation, classify every existing density-branch change as:

1. retained unchanged because it satisfies this design;
2. adapted to the new semantic structure;
3. removed because it compensates for the old architecture.

Likely reusable work includes long-label browser fixtures, current-row
orientation coverage, compact typography measurements, sequence-badge
containment, and right-rail disclosure tests. Four-column tile rules, old
frame-relief valves, duplicated structural/drawer sizing, and comments tied to
the former badge flow require re-evaluation.

No generated artifact, cache, screenshot report, or external-course fixture is
source truth.

## Verification

### Structural Matrix

Browser coverage includes at least:

- widths: 1440, 1024, 894, 893, 640, 639, and 390px;
- normal and short viewport heights;
- expanded, collapsed, drawer-closed, and drawer-open states;
- default, article-large-text, OpenDyslexic, reduced-motion, and print modes.

### Required Assertions

1. Expanded structural width is 256px within one CSS pixel.
2. Collapsed structural width is 48px within one CSS pixel.
3. Drawer width is 256px and remains inside the viewport.
4. Header and footer remain visible while central navigation scrolls.
5. Exactly one expanded-rail element owns vertical scrolling.
6. The outer rail, actions, filter, and tree do not create nested vertical
   scroll containers.
7. Gestures over actions, filter, and tree move the central navigation when
   overflow remains.
8. Structural boundary gestures may chain to the page and are not swallowed.
9. Six course actions render in two columns in the documented order.
10. Two comfort controls render in the footer and mini rail.
11. Article text-size changes do not change rail row, action, header, footer,
    or mini-control dimensions.
12. OpenDyslexic does not cause clipping, horizontal overflow, or vertical
    character-by-character text.
13. Long labels remain within row and scrollport bounds, clamp to at most two
    lines at rest, and reveal fully on hover, focus, and current state.
14. Current-page orientation runs when needed and stops controlling scroll
    after initial reconciliation.
15. Collapsed full content is hidden, inert, untabbable, and absent from
    assistive navigation while mini controls remain operable.
16. Drawer focus, backdrop, Escape, close, restoration, inert background, and
    scroll lock are correct.
17. Breakpoint transitions cannot leave stale inertness or hidden focus.
18. Right-rail behavior does not regress.
19. Document horizontal overflow is at most one CSS pixel in every viewport.

### Visual Evidence

Retain and inspect screenshots for:

- wide expanded and mini-rail states;
- 894px expanded and mini-rail states;
- 893px intermediate state;
- 640px intermediate state;
- 639px drawer closed and open;
- 390px drawer closed and open;
- long-label and OpenDyslexic cases.

No nested scroll, clipped control, dead destination, inaccessible hidden
content, incoherent overlap, or gesture consumed without an eligible scroll
response may pass acceptance.

### Repository Gates

Run focused TDD loops first, then render-debug coverage, host checks, smoke, and
Docker checks sequentially. Deployment is allowed only after adversarial code,
contract, accessibility, and live visual reviews are clean.
