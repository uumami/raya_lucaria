# Graph Orientation Fit Selection Design

## Context

The graph workspace already has a toolbar `Fit selection` control that frames the selected page and its visible connected context. The selected-page orientation band also exposes nearby selected-page actions such as `Open page`, `Details`, `Focus neighborhood`, and `Clear selection`.

Students currently need to look away from the selected-page context to find the toolbar action. This is unnecessary friction in the graph workspace, especially after a student has selected a page from search, a graph node, or a page-focused handoff.

## Decision

Add a `Fit selection` button to the graph orientation action band. The action reuses the existing `fitSelectedGraphContext()` behavior and does not create new graph semantics.

The button is visible only when a selected page can be framed in the SVG graph:

- a page is selected;
- the current layout is not `List`;
- a graph view box exists;
- the selected page has a rendered SVG position.

When available, activating the orientation action frames the selected page and visible directly connected graph context, then keeps the selected details, search text, filters, URL state, and graph data unchanged. It must not write `localStorage` or `sessionStorage`.

## User Experience

The orientation band remains the compact "where am I and what can I do with this selected page?" surface. `Fit selection` belongs there because it is selected-page specific, unlike global `Fit`, `Reset view`, or pan/zoom controls.

On unavailable states, including `List` layout, the orientation action is hidden and disabled so keyboard users are not sent to a control that cannot act.

## Constraints

- No browser-side MathJax.
- No external renderer, CDN, font, CSS, script, or graph library request.
- No runtime fetch/XHR for graph data.
- No graph state in browser storage.
- No progress, mastery, recommendation, ranking, or personalization language.
- No source-course or private artifact paths in student-facing graph HTML.

## Testing

Add tests before implementation:

- Contract test: generated graph HTML includes the orientation `Fit selection` button and local graph JS wires it to `fitSelectedGraphContext()`.
- Browser e2e test: with `?page=reader-ux`, pan/zoom away, activate orientation `Fit selection`, and assert the canvas `viewBox` changes back to selected context while selection, search text, URL, details, and storage remain stable.
- Existing graph focus and minimap tests continue to pass.

## Documentation Impact

Role documentation does not need a new conceptual section because the behavior is a placement improvement for an existing graph viewport action. The existing foundation renderer contract already permits selected-page orientation actions and states that `Fit selection` changes only the SVG viewport.
