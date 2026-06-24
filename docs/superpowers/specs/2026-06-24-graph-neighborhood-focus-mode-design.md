# Graph Neighborhood Focus Mode Design

## Context

The current static Course graph already uses the reset renderer architecture:
embedded graph data, local JavaScript, local CSS, SVG rendering, fuzzy search,
group filters, map/radial/list layouts, collapsible list and inspector panels,
selected-page details, URL page focus, and selected-neighborhood highlighting.

Legacy `main` used Cytoscape and a CDN, which are not acceptable in the reset
renderer, but it had a useful interaction pattern: when a reader inspected a
node, the local neighborhood became visually dominant and the rest of the graph
receded. The current branch highlights neighbors but still keeps every visible
page equally present. For larger courses, that makes the graph harder to use
when a student is trying to answer one concrete question: "what is directly
connected to this page?"

## Goal

Add explicit, transient neighborhood focus controls to the static Course graph
so readers can narrow the visible graph and list to the selected page plus
directly connected pages, move focus between connected pages from the detail
panel, then return to the full graph without changing source data, fetching
data, storing graph state, or adding external graph libraries.

## Approach Options

### Option A: Passive dimming only

Keep the current full graph visible and make non-neighbor nodes dim more
strongly when a page is selected. This is low risk, but it does not solve scan
load on large graphs because the list and SVG still contain every visible page.

### Option B: Search-like automatic expansion

Automatically show only a selected node and its neighbors whenever a page is
selected. This creates a strong focus state, but it can surprise readers because
clicking a page changes the whole graph without a named mode.

### Option C: Explicit focus mode

Add a `Focus neighborhood` control inside the selected-page detail panel. The
control is enabled only when a page is selected. When active, the graph and list
show the selected page and directly connected pages that also pass current group
filters. Detail-panel incoming/outgoing lists also get an in-place `Focus`
button for each connected page so a reader can move the selected-page context
without finding the page again in the graph. Search matches can still choose the
candidate set before focus, but focus mode is not persistent and can be cleared
with the same control, detail clear, or reset.

Option C is the best fit. It gives students a deliberate way to reduce visual
noise while preserving current graph controls and reset-renderer boundaries.

## User Experience

When no page is selected, the detail panel keeps the current empty state and the
focus control is not visible. When a page is selected, the detail panel shows:

- the selected page title, metadata, counts, and links;
- the existing selected-neighborhood summary;
- a `Focus neighborhood` button;
- incoming and outgoing linked-page lists where each item keeps its normal page
  link and adds a separate `Focus` button for graph-only selection.

Activating the button switches the graph page into focus mode:

- the status text names that focus mode is active;
- the SVG and list show only the selected page plus its directly connected
  pages, after applying hidden group filters;
- selected and neighbor visual states remain visible;
- outgoing and incoming detail lists remain complete for the selected page;
- the button changes to `Show full graph`.

Deactivating focus mode restores the full graph view under the current search,
layout, and group-filter controls. Clearing the selected page or pressing Reset
also leaves focus mode.

Clicking a connected item `Focus` button selects that page inside the graph
workspace, refreshes the detail panel, and preserves static page links as normal
navigation targets. It does not mutate the URL.

## Architecture

No graph schema changes are needed. The local graph script already has
`connectedNodeIds()`, `relationshipCountsFor()`, `visibleNodes()`, `render()`,
`renderList()`, `renderDetail()`, and `renderDetailList()`. The new behavior
adds one local boolean state, a detail-panel button, item-level focus buttons in
the existing detail lists, and a small filter step in `visibleNodes()`.

The builder emits a static button placeholder in the graph detail panel:

```html
<button type="button" data-raya-graph-focus-neighborhood hidden>
  Focus neighborhood
</button>
```

The script keeps `neighborhoodFocus` in memory only. It must not write URL
state, `localStorage`, `sessionStorage`, cookies, or generated files. It must
not fetch graph data at runtime. It must keep URL page focus as a one-time
initial selected page, not as a persistent state channel.

Detail-list focus buttons use public node IDs already present in the embedded
payload. They call the existing selection path and must not replace or hijack
the normal page links.

## Boundaries

Focus mode is a structural reading aid over explicit graph edges. It is not a
recommendation, progress signal, mastery estimate, prerequisite inference, or
importance ranking. It does not hide graph authority; all machine authority
remains in manifest-declared graph data and the full graph can be restored.

Focus mode applies only to the generated graph workspace. It does not change
article page connections, the right learning rail, Search, Practice, or course
source contracts.

## Testing

Contract tests should assert that the graph surface includes the static focus
button placeholder and that `graph.js` includes the focus-state functions without
adding fetch, storage, workers, external library imports, or Cytoscape.

Browser tests should open the render fixture graph with
`?page=authoring-matrix`, activate focus mode, and verify:

- the focus control is visible after page selection;
- status text names focus mode;
- the list contains only the selected page and directly connected pages;
- a non-neighbor page is hidden;
- selected and neighbor classes remain correct;
- `Show full graph` restores the full list;
- a connected item `Focus` button changes the selected-page detail panel without
  navigation or network requests;
- Reset clears focus mode;
- desktop and mobile viewports have no horizontal overflow and no external
  requests after page load.

## Documentation

Update the learning renderer contract and English/Spanish agent guides. The
docs should frame focus mode as a transient graph-reading aid, not a stored
learner state or recommendation system.
