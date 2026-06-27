# Graph Minimap Control Design

## Purpose

Make the generated Course Graph minimap a direct viewport control. Students should be able to click or keyboard-activate the minimap to center the SVG graph view on that overview position.

## Constraints

- The minimap remains static-renderer UI over embedded graph data.
- It must not fetch data, import graph libraries, write browser storage, mutate graph data, mutate authored links, clear search, clear filters, clear selection, or change URL/share state.
- It must remain keyboard reachable and screen-reader named.
- It must hide in print with the rest of graph chrome.

## Design

The generated minimap `<svg>` becomes an operable control with `role="button"`, `tabindex="0"`, and an accessible label that says activation centers the graph view. The existing minimap renderer continues drawing node, edge, and viewport marks from the current visible graph state.

`graph.py` adds one helper that maps a pointer or keyboard event on the minimap back into graph coordinates through the already known `fullViewBox`. It preserves the current `graphViewBox.width` and `graphViewBox.height`, recenters the main canvas around the chosen minimap point, and clamps the result into graph bounds. `Enter` and Space center on the minimap midpoint. Pointer clicks center on the clicked position.

The behavior is intentionally viewport-only. Existing selection, detail panel state, filters, layout, search, URL state, manual node arrangements, and comfort storage are left alone.

## Tests

- Browser e2e extends the minimap viewport test: after zooming/panning, click the minimap and assert the main SVG `viewBox` and minimap viewport move while selection, storage, URL/request boundaries, and overflow remain safe.
- Contract test asserts the generated minimap has operable semantics and the graph script wires click and keyboard activation while preserving the no-storage/no-fetch runtime script invariant.

