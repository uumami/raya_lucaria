# Graph Inspection Preview Design

## Context

The current graph workspace already supports local SVG rendering, graph search,
hover and focus spotlighting, single-click selection, double-click page opening,
keyboard page opening, relationship chips, and static selected-page details.
The remaining UX gap is that hover and keyboard focus only update terse status
text plus visual dimming. Students can see that a node is related, but they do
not get enough immediate page context before deciding whether to select or open
it.

This loop adapts the useful legacy graph-preview affordance without copying the
legacy implementation. The current framework remains authoritative: no external
graph library, no runtime fetch, no browser storage for graph state, no
browser-side MathJax, and no inferred recommendations or learner-state wording.

## Design

Add a compact graph inspection preview card inside the graph map panel, below
the SVG canvas so hover/focus updates never move the graph under the pointer.
The card is static markup filled
by local `graph.js` from the already embedded graph payload. It is hidden when
no graph node is being inspected and becomes visible when hover, focus, or graph
search active-result inspection sets `inspectedId`.

The preview shows:

- page title;
- group or hierarchy label;
- normalized status when present;
- summary when present;
- outgoing, incoming, and connected page counts from generated graph data;
- an `Inspect page` button that selects the node in the graph inspector without
  navigating;
- an `Open page` link that uses the node's deployment-neutral page URL.

The preview is not floating and does not follow the pointer. Keeping it in the
map panel avoids overlap, mobile jitter, and pointer-tracking complexity. It is
a stable orientation aid, not a tooltip, recommendation, progress signal, or
personalized next step.

## Behavior

Hovering or focusing an SVG node or list item updates the preview card and the
existing hover status. Clearing inspection hides the card unless another focused
graph node or active search result still owns inspection state. Clicking
`Inspect page` calls the same selected-page path as clicking a graph node once.
Clicking `Open page` follows the normal static page link.

The preview must not change selected graph state just because a node is hovered
or focused. It must not persist anything. Existing graph click, double-click,
keyboard Enter, search, reset, filters, layout, pan, zoom, focus mode, and
selected-page detail behavior must remain unchanged.

## Accessibility

The preview card is a named region with polite updates. Its controls are normal
button and link elements. Hidden state uses the `hidden` attribute so the card is
not focusable or announced when no node is inspected. Text stays concise so the
card improves orientation without replacing the selected-page inspector.

## Testing

Add contract assertions that the graph HTML, local graph script, and stylesheet
contain the preview container, render function hooks, and CSS class. Add a
browser test in the existing graph static-read-path coverage that:

- starts with the preview hidden;
- focuses `authoring-matrix` and sees the preview title, summary, status, and
  relationship counts;
- confirms focus inspection does not select the node;
- clicks `Inspect page` and sees the selected-page detail panel;
- verifies `Open page` points to the same local page URL as the node;
- clears/reset graph state and sees the preview hidden again;
- confirms no runtime requests are made.

Run focused graph tests first, then the render-debug gate, then the full host
and Docker gates sequentially before committing.
