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

The reset implementation does not need those exact class names or pixel values, but it must preserve the same interaction model.

## Architecture

Use the existing reset reader shell:

- `packages/static/src/raya_static/builder.py` owns generated reader markup.
- `packages/static/src/raya_static/rendering.py` owns shell layout CSS.
- `packages/static/src/raya_static/shell.py` owns collapse, drawer, focus, and map-orientation behavior.

Do not reintroduce the old Eleventy app, Tailwind, Pagefind assumptions, or legacy source layout. The implementation should adapt the old behavior to the current artifact-first static builder.

## Desktop Layout

For viewports at the desktop breakpoint, the shell is a three-column structural layout:

1. Left course map rail.
2. Main article.
3. Right learning context rail.

The left rail must use real grid width. It must not be `position: fixed`, transformed over the article, or otherwise overlay the article on desktop.

Expanded state:

- Left rail shows course tools, workspace links, map controls, filter, and map list.
- Article occupies the remaining center column.
- Course-map scrolling is contained within the left rail.

Collapsed state:

- Left rail shrinks to a compact strip comparable to `main`'s collapsed sidebar.
- Article column expands immediately through the shell grid definition.
- Collapsed rail keeps a clear expand affordance and compact page/index markers.
- Course tools, workspace links, filters, and verbose map controls are hidden while collapsed.
- The current-page marker remains visible.

Right-rail collapse should continue to reallocate width to the article independently from the left rail.

## Mobile Layout

Below the desktop breakpoint:

- The article is the primary page flow.
- The left course map is an off-canvas drawer opened by a compact button.
- Opening the drawer overlays the article and locks background scroll.
- Closing the drawer restores focus to the opener.
- Drawer contents can include course tools and map controls, but closed drawer contents must not leak into the viewport or tab order.

Mobile behavior should not drive desktop behavior. Any CSS or JavaScript for drawer state must be scoped so desktop remains structural.

## Course Tools Placement

The reader top bar remains removed. Course tools move into the left rail, but they must not dominate the navigation.

Desktop expanded rail order:

1. Compact tool area.
2. Course workspace links if present.
3. Current-page/map controls.
4. Course map list.

The tool area should be compact and predictable:

- Search input and submit remain available.
- Graph, practice, tasks, schedule links remain available.
- Map, focus, context, text size, and OpenDyslexic controls remain available.
- The tool area must not create a sticky child that escapes a closed mobile drawer.
- The map list must remain scrollable and orientable after the current page is auto-scrolled into view.

If available height is tight, the whole rail may scroll as one container. Avoid nested scroll regions unless a test proves they behave correctly.

## Scrolling And Orientation

Course-map orientation should follow `main`'s intent:

- On load, auto-scroll the current page into view.
- Preserve useful map scroll state during navigation where the current contract already supports it.
- Re-orient after expanding the desktop rail or opening the mobile drawer.
- Do not let sticky tools change the scroll target such that the current page is hidden under the tool area.

The preferred design is a single scroll container for the rail. If the implementation keeps sticky tools, orientation must account for the sticky tool height and visible content area.

## Accessibility

- Desktop collapsed rail must remain keyboard reachable.
- Mobile drawer must trap focus while open and restore focus on close.
- Closed mobile drawer contents must be inert and removed from tab order.
- `aria-expanded`, `aria-hidden`, and `inert` must reflect desktop structural state separately from mobile drawer state.
- The collapsed rail must expose useful labels through accessible names even when visual text is hidden.

## Testing

Add or update tests around behavior, not legacy implementation details:

- Contract tests verify reader pages do not render the old reader top bar and do render left-rail tools.
- Desktop e2e tests verify expanded and collapsed left rail widths, article width growth on collapse, and no article overlay.
- Mobile e2e tests verify drawer closed contents do not intersect viewport or tab order, drawer open works, and focus trapping remains intact.
- Scrolling tests verify current page/link orientation after load, after expanding the desktop map, and after opening the mobile drawer.
- Regression tests verify right-rail collapse still reallocates width independently.

Visual checks should include representative desktop and mobile viewports from the render fixture.

## Out Of Scope

- Reintroducing the old Eleventy renderer.
- Restoring the old top navigation bar.
- Changing course contracts, generated artifact contracts, or source layout.
- Redesigning graph, practice, tasks, or schedule internals beyond their entry links and control placement.
- Persisting new user preferences unless needed to match existing shell state behavior.
