# Main-Like Reader Shell Design

## Goal

Port the reader-shell behavior from the `main` branch into the reset static framework without restoring the old Eleventy implementation. The reset shell should keep its generated artifact structure, Raya workspace links, graph/practice/tasks/schedule surfaces, MathJax pipeline, and current course contracts, but the reader layout must behave like `main`:

- Desktop course navigation is a structural left rail, not an overlay.
- Collapsing the left rail shrinks it to an icon/index strip and gives the width back to the article.
- Expanding the left rail reallocates article width rather than covering the article.
- Mobile keeps an overlay drawer for the course map.
- The reader top bar stays removed.
- Course tools live in the left rail without breaking map scrolling or obscuring article text.

## Main-Branch Behavior To Preserve

The old `main` UI used a fixed-width sidebar and content offset:

- Expanded desktop sidebar: `16rem`.
- Collapsed desktop sidebar: `3rem`.
- Main content margin follows the sidebar width, so text reflows when the sidebar collapses or expands.
- Mobile sidebar is fixed and translated off-canvas when closed.
- Sidebar navigation preserves scroll position and auto-scrolls the current page into view.

The reset implementation does not need those exact class names or pixel values, but it must preserve the same interaction model for layout reallocation. It must not copy `main`'s persisted sidebar state when that conflicts with reset foundation contracts.

## Architecture

Use the existing reset reader shell:

- `packages/static/src/raya_static/builder.py` owns generated reader markup.
- `packages/static/src/raya_static/rendering.py` owns shell layout CSS.
- `packages/static/src/raya_static/shell.py` owns collapse, drawer, focus, and map-orientation behavior.

Do not reintroduce the old Eleventy app, Tailwind, Pagefind assumptions, or legacy source layout. The implementation should adapt the old behavior to the current artifact-first static builder.

## Foundation Impact

This design intentionally removes the reader top bar as a reader-page surface and moves reader commands into the structural left rail. That is a contract change because `docs/foundation/20_learning_renderer_contract.md` currently describes a sticky command bar and command-bar reader controls. Implementation must update the affected foundation and role-documentation surfaces alongside code and tests:

- `docs/foundation/20_learning_renderer_contract.md` must describe left-rail reader commands instead of a reader top bar.
- Student-facing role docs in English and Spanish must describe the left course rail, collapsed Map tab, and mobile map drawer.
- Agent/contributor guidance must avoid stale top-bar instructions.
- Discovery workspace chrome may keep its own command bar; the reader top bar removal applies to generated reader pages.

## Desktop Layout

Use the current reset shell desktop breakpoint, `min-width: 1280px`, unless this change also updates foundation docs and tests to a different breakpoint. For desktop viewports, the shell is a three-column structural layout:

1. Left course map rail.
2. Main article.
3. Right learning context rail.

The left rail must use real grid width. It must not be `position: fixed`, transformed over the article, or otherwise overlay the article on desktop.

At `1280`, `1366`, `1440`, and `1920` pixel viewport widths, the left rail, article, and right rail bounding boxes must be ordered left-to-right without intersection and without document-level horizontal overflow. These checks must also pass with large reader text size and OpenDyslexic enabled.

Expanded state:

- Left rail shows course tools, workspace links, map controls, filter, and map list.
- Article occupies the remaining center column.
- Course-map scrolling is contained within the left rail.
- Expanded left-rail width should stay in a compact navigation range, approximately `13rem` to `17rem`, unless tests prove a different range is required by content.

Collapsed state:

- Left rail shrinks to a compact strip comparable to `main`'s collapsed sidebar.
- Article column expands immediately through the shell grid definition.
- Collapsed rail keeps a clear expand affordance and compact page/index markers.
- Course tools, workspace links, filters, and verbose map controls are hidden while collapsed.
- The current-page marker remains visible.
- Collapsed left-rail width must be at most `5.5rem`, and collapsing the left rail must increase article width by at least `6rem` at representative desktop widths.
- Collapsed tab order must be bounded: the expand affordance and current/visible compact navigation targets may be reachable, but hidden verbose controls must not be tabbable. Compact targets require visible focus and useful accessible names.

Right-rail collapse should continue to reallocate width to the article independently from the left rail.

## Mobile Layout

Below the desktop breakpoint:

- The article is the primary page flow.
- The left course map is an off-canvas drawer opened by a compact button.
- Opening the drawer overlays the article and locks background scroll.
- Closing the drawer restores focus to the opener.
- Drawer contents can include course tools and map controls, but closed drawer contents must not leak into the viewport or tab order.
- While open, the drawer behaves as a modal surface: Tab and Shift+Tab stay inside the drawer, Escape/backdrop/close close it, and article/right-rail links or controls cannot be focused or activated behind it.
- While closed, the drawer and descendants are inert, `aria-hidden="true"`, non-tabbable, non-hit-testable, and have no meaningful viewport intersection.

Mobile behavior should not drive desktop behavior. Opening or closing the mobile drawer must not mutate the prior desktop expanded/collapsed state. Resizing across the desktop breakpoint in either direction must normalize `aria-hidden`, `inert`, `tabindex`, `aria-expanded`, scroll-lock, and focus so focus lands on a visible enabled control or the article.

## Course Tools Placement

The reader top bar remains removed. Course tools move into the left rail, but they must not dominate the navigation.

Desktop expanded rail order:

1. Compact tool area.
2. Course workspace links if present.
3. Current-page/map controls.
4. Course map list.

The compact tool area and course workspace links must not duplicate the same workspace affordance twice at the same prominence. The implementation should use one compact command surface for Search, Graph, Practice, Tasks, and Schedule, with badges/details only where they remain compact and do not dominate the navigation.

The tool area should be compact and predictable:

- Search input and submit remain available.
- Graph, practice, tasks, schedule links remain available.
- Map, focus, context, text size, and OpenDyslexic controls remain available.
- The tool area must not create a sticky child that escapes a closed mobile drawer.
- The map list must remain scrollable and orientable after the current page is auto-scrolled into view.
- The tool area must fit within `35%` of the visible left-rail height at desktop sizes and must not create horizontal overflow.

The left rail should use one vertical scroll owner for tools, workspace links, controls, and map list. Avoid nested scroll regions unless tests prove keyboard, pointer, and current-page orientation behavior at desktop and mobile drawer sizes.

## Scrolling And Orientation

Course-map orientation should follow `main`'s intent while respecting reset volatility:

- On load, auto-scroll the current page into view.
- Do not use `localStorage` or `sessionStorage` for course-map state, drawer state, map scroll, section expansion, reader focus, right-rail state, command search text, or filter text. Local storage remains limited to foundation-approved comfort preferences such as text size and OpenDyslexic.
- Re-orient after expanding the desktop rail or opening the mobile drawer.
- Do not let sticky tools change the scroll target such that the current page is hidden under the tool area.
- If restoring browser-native scroll within the same document lifecycle, restore first and then orient only when the current page link is not fully visible.

The preferred design is a single scroll container for the rail. If the implementation keeps sticky tools, orientation must account for the sticky tool height and visible content area. After load, desktop expand, mobile drawer open, text-size change, and map current/filter actions, the current page link must be fully visible within the actual scrollport, below any sticky tool or header bottom.

## Accessibility

- Desktop collapsed rail must remain keyboard reachable.
- Mobile drawer must trap focus while open and restore focus on close.
- Closed mobile drawer contents must be inert and removed from tab order.
- `aria-expanded`, `aria-hidden`, and `inert` must reflect desktop structural state separately from mobile drawer state.
- The collapsed rail must expose useful labels through accessible names even when visual text is hidden.
- Reduced-motion mode must not depend on transition timers for correct focusability, geometry, or state.

## Testing

Add or update tests around behavior, not legacy implementation details:

- Contract tests verify reader pages do not render the old reader top bar, do render left-rail tools as descendants of the course-map region, and expose required controls with accessible names and deployment-neutral local links. Avoid string assertions against CSS or JavaScript internals when a semantic HTML or browser behavior check is available.
- Desktop e2e tests verify expanded and collapsed left rail widths, article width growth on collapse, independent right-rail width reallocation, no article overlay, and no document horizontal overflow at `1280`, `1366`, `1440`, and wide desktop widths.
- Mobile e2e tests verify closed drawer geometry, inertness, `aria-hidden`, tab order, hit testing, open drawer backdrop/scroll lock, focus trapping, Escape/backdrop/close behavior, and focus restoration at `390x844` and a below-desktop tablet width.
- Resize e2e tests cross the desktop breakpoint in both directions from open/closed/collapsed states and verify no stale inertness, hidden focus, scroll lock, or incorrect `aria-expanded` remains.
- Scrolling tests use a fixture where the current page starts outside the initial map viewport and verify current page/link orientation after load, after expanding the desktop map, after opening the mobile drawer, after text-size changes, and after current/filter actions.
- Regression tests verify right-rail collapse still reallocates width independently.

Visual checks should include representative desktop and mobile viewports from the render fixture. The focused render-debug gate, `./scripts/check-render-debug.sh`, or equivalent browser evidence must cover screenshots, raw TeX leakage, overflow, local MathJax resources, and external renderer requests for normal, collapsed, and mobile shell states.

## Out Of Scope

- Reintroducing the old Eleventy renderer.
- Restoring the old top navigation bar.
- Changing course contracts, generated artifact contracts, or source layout.
- Redesigning graph, practice, tasks, or schedule internals beyond their entry links and control placement.
- Persisting course-map, drawer, map scroll, section expansion, reader focus, right-rail, command search, or filter state in browser storage.
