# Navigation-First Course Rail Design

Date: 2026-08-04
Status: approved after adversarial review
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
  prevent collisions, invalid paired states, the mobile `Context` handoff, or
  the explicitly narrowed Text-size scope.
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

- The course-home icon is a deployment-neutral static link when the generated
  navigation has a root page. It is omitted, without a dead target or blank
  substitute, when no root page exists.
- The center displays the generated course name. The containing region retains
  the accessible name `Course map`. The visible name is one line with ellipsis;
  its full value remains the accessible name and is available through a tooltip.
- The trailing icon is `Hide course map` in structural expanded mode and
  `Close course map` in drawer mode.
- On fine-pointer layouts, header icon controls are 30-32px square, use the
  established icon library, expose accessible names, and provide tooltips.

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
  rail can collapse. In phone drawer mode, where the right rail remains
  expanded by contract, Context closes the course drawer, restores the
  background, scrolls the right learning landmark into view, and moves focus
  to that landmark without collapsing it.
- The previous inline query form is removed from the rail. Search workspace
  querying remains owned by Search.
- Local tree filtering remains a separate Content control and never navigates.

All six course actions are always operable. Search, Graph, Practice, Tasks, and
Schedule are renderer-owned links to workspaces generated by the same build;
Context is the mode-specific rail control or handoff described above. The six
course actions plus two footer comfort controls preserve the eight accepted
reader commands without treating comfort preferences as course destinations.

## Content Filter And Tree

The `Content` section follows course actions in the same scrolling element.

The compact filter is always available while the Content section is in layout.
It filters rendered course labels locally. Empty results render a concise state
inside the same navigation region. Filter text is volatile and is not restored
after navigation or refresh.

Tree rows use:

- 12-13px stable interface type;
- compact 27-30px single-line row rhythm on fine-pointer layouts;
- small indentation and one subtle guide per hierarchy level;
- separate disclosure, sequence, and label geometry;
- a maximum of two visual label lines at rest;
- full visual release on hover, keyboard focus, and the current page;
- the complete authored label as the accessible name at all times.

On hover-capable fine pointers, non-current labels clamp to two lines at rest
and release in normal document flow without overlays or horizontal overflow.
When `any-pointer: coarse` is true, including on a mouse-plus-touch hybrid, or
when the primary input cannot hover, labels render in full in normal flow so a
touch does not need to perform a reveal before navigation. Those layouts use a
minimum 44px tree-row rhythm. A reveal may grow only the affected row; it must
keep the focused/current row visible between the fixed header and footer.

The current path expands on load. The current row is oriented into the visible
scroll region only when needed. Once orientation completes, ordinary user
scroll is authoritative; observers and animations must not repeatedly pull the
tree back to the current row.

Branch display state may continue using the accepted course-scoped,
tab-isolated session key. It must not move to localStorage.

## Footer And Comfort Controls

The 48px footer contains Text size, OpenDyslexic, and compact `N / M`
structural position. Its visible compact position exposes the full accessible
name `Page N of M`.

- Text size changes only content inside `.raya-main-article`. It does not scale
  either rail or any shell header, action, filter, tree, footer, mini control,
  breadcrumb, or launcher. This intentionally narrows the current right-rail
  scaling behavior so both navigation surfaces retain stable interface density
  at every accepted text-size setting.
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
- With no saved shell state, the navigation-first default is left expanded and
  right collapsed. A saved pair with zero or one expanded rail is preserved.
  Prepaint and initial runtime reconciliation resolve any saved or legacy
  `expanded/expanded` pair to left expanded/right collapsed; prepaint never
  guesses future restored focus. During an explicit runtime resize, zoom, or
  BFCache reconciliation, the rail that already contains focus may instead win.
  If neither rail contains focus, the left course rail wins. Reconciliation
  moves focus to the winning rail's corresponding control when the losing
  rail's focused content becomes inert.

### Drawer: Below 640px

- Structural and mini rails leave layout.
- The existing Course launcher opens the same rail content as a 256px modal
  drawer. Its used width is `min(256px, 100vw)` after safe-area accommodation,
  so zoom and unusually narrow viewports cannot create horizontal overflow.
- Drawer behavior includes backdrop, visible close control, Escape closure,
  focus containment, focus restoration, background inertness, and temporary
  background scroll lock.
- The footer remains visible and the central navigation remains the single
  drawer scroller.
- The drawer uses dynamic viewport height (`100dvh`) with a compatible
  fallback and accounts for relevant `safe-area-inset-*` values so its header,
  scroller, and footer remain operable through mobile chrome and orientation
  changes.

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

An opener-created browsing context may receive the browser-provided initial
sessionStorage copy and then diverges. A separately created tab starts with its
own state. The accepted comfort preferences `raya:text-size` and
`raya:open-dyslexic` remain the only durable localStorage written by reader
pages.

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
- Tooltips are real hover-and-keyboard-focus content associated with their
  controls; a `title` or inert data attribute alone does not satisfy the
  tooltip requirement. They remain visible while their trigger or tooltip is
  hovered or the trigger retains focus, are pointer-hoverable when their content
  permits it, and can be dismissed without moving focus. Tooltips supplement
  rather than replace accessible names. Touch operation does not depend on a
  tooltip.
- Expanded action targets are at least 30px in their compact fine-pointer
  layout. When `any-pointer: coarse` is true, every operable rail control uses a
  non-overlapping target of at least 44px, including course home, expand/hide/
  close, action links, filter input, tree links and disclosures, comfort
  controls, and mini controls, while preserving semantic content and order.
- Mini-rail controls are at least 34px square on fine pointers and 44px square
  on coarse pointers within the 48px rail.
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

Build-time inputs provide the course name, ordered hierarchy, current page, and
structural position. The renderer generates Search, Graph, Practice, Tasks, and
Schedule workspaces and their relative links as one artifact operation. Runtime
code only filters, discloses, or changes presentation state.

Artifact tests must prove that all five renderer-owned workspace hrefs resolve
to files produced by the same build. A missing generated workspace is a build
defect and must never render as a dead action; it is not a course-schema option.
The root-page course-home action is the only optional header destination and is
omitted when the navigation has no root. Optional page-focus query data changes
only a generated href and never removes or reserves an action row. An empty
local filter result is represented in the navigation, not as an exception or
network fallback.

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
- `packages/static/src/raya_static/shell_prepaint.py`: apply the same default,
  persisted-pair reconciliation, and breakpoint derivation before first paint.
  Its deterministic no-focus fallback is left expanded/right collapsed for an
  invalid intermediate `expanded/expanded` pair; focus-aware arbitration is a
  runtime-only transition rule.

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
- all eight English and Spanish role indexes under `docs/guides/` where rail,
  drawer, comfort, or session behavior is described: contributors/
  colaboradores, professors/profesores, students/estudiantes, and
  agents/agentes;
- `tests/contracts/test_documentation_surfaces.py`,
  `tests/contracts/test_static_builder.py`, and any renderer-dependency binding
  that asserts the replaced contract wording;
- `docs/foundation/00_index.md` only if its renderer summary or inventory would
  otherwise become inaccurate. The current summary does not require a geometry
  edit.

The new contract replaces the old requirements for eight body tiles, a
separate inline course-search form, and a collapsed floating Map opener.

## Migration From The Density Branch

Before implementation, classify every existing density-branch change as:

1. retained unchanged because it satisfies this design;
2. adapted to the new semantic structure;
3. removed because it compensates for the old architecture.

The implementation plan must record an executable commit/file matrix before
the first production edit. At minimum it must classify the four-column/`Plan`
builder wording, accessibility overrides scoped to old rail tiles, every outer
or list scroll-owner rule, four-column card CSS, legacy scroll tests that allow
any of several elements to move, and assertions for the inline query, eight
body tiles, Page-brief-only position, and floating opener.

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
3. Drawer width is 256px when the viewport can contain it; otherwise it uses
   the available safe-area-adjusted viewport width and never overflows it.
4. Header and footer remain visible while central navigation scrolls.
5. Exactly one left expanded-rail element declares vertical scrolling. Tests
   distinguish that CSS owner from whether a particular fixture currently
   overflows.
6. The outer rail, actions, filter, and tree do not create nested vertical
   scroll containers.
7. Gestures over actions, filter, and tree move the central navigation when
   overflow remains.
8. Structural boundary gestures may chain to the page and are not swallowed.
9. Six course actions render in two columns in the documented order.
10. Two comfort controls render in the footer and mini rail, and compact `N / M`
    exposes `Page N of M` to assistive technology.
11. Article text-size changes affect `.raya-main-article` and do not change
    typography or dimensions in either rail, any shell chrome, action, filter,
    tree, footer, or mini control.
12. OpenDyslexic does not cause clipping, horizontal overflow, or vertical
    character-by-character text.
13. Long labels remain within row and scrollport bounds. Fine-pointer labels
    clamp to at most two lines at rest and reveal fully on hover, focus, and
    current state; coarse-pointer/no-hover labels render fully without a
    pre-navigation gesture. Reveal remains in flow and keeps the active row
    visible.
14. Current-page orientation runs when needed and stops controlling scroll
    after initial reconciliation.
15. Collapsed full content is hidden, inert, untabbable, and absent from
    assistive navigation while mini controls remain operable.
16. Drawer focus, backdrop, Escape, close, restoration, inert background, and
    scroll lock are correct.
17. Breakpoint transitions cannot leave stale inertness or hidden focus.
18. Right-rail content and structural behavior do not regress except for the
    explicit article-only Text-size scope, intermediate handoff, and mobile
    Context focus handoff.
19. Document horizontal overflow is at most one CSS pixel in every viewport.
20. The same single course-map and tree DOM instances survive
    `640 -> 639 -> 640` resize, drawer open/close, and state reconciliation;
    there are no duplicate IDs or parallel mobile trees.
21. The session keys retain course isolation and opener-copy/tab-divergence
    semantics. Filter, drawer, scroll, focus, and active context remain absent
    from storage, and no new localStorage key is written.
22. Intermediate defaults and `expanded/expanded` reconciliation share the
    documented deterministic fallback in prepaint and runtime. Focus-aware
    priority is used only during explicit runtime resize, zoom/reflow, or
    BFCache reconciliation, including focus transfer when a losing rail becomes
    inert.
23. The five generated workspace hrefs resolve inside the artifact, Context is
    operable in every band, and rootless navigation omits only course home.
24. Header tests cover generated course name, one-line ellipsis, full accessible
    name and tooltip, deployment-neutral course home when present, omission when
    rootless, and `Hide course map`/`Close course map` mode labels.
25. Coarse-pointer targets are at least 44px, do not overlap, and remain inside
    the drawer or mini rail at short heights and safe-area insets.
26. Shell/runtime code registers no `wheel` or `touchmove` routing listener and
    never assigns scroll deltas to simulate native propagation.

Behavioral scroll tests identify the declared central owner, use an actually
overflowing fixture, and compare its `scrollTop` before and after wheel gestures
over actions, filter, and tree. Boundary chaining starts that owner exactly at
an edge on a scrollable document. Header/footer stability is verified from
bounding rectangles before and after central scrolling. One-shot orientation
is verified by manually moving the owner and triggering resize/observer work,
not by relying on an arbitrary timeout. Hidden-content checks include an
accessibility-tree snapshot in addition to `inert`, `aria-hidden`, and tab order.
At least one structural coarse-pointer case and one open-drawer case use a real
touchscreen swipe over actions, filter, and tree in an overflowing fixture and
verify the central owner's delta. Static/runtime guardrails also reject event
listeners or handlers that forward `wheel` or `touchmove` deltas.

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
