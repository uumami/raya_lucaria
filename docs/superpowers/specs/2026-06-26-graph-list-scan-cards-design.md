# Graph List Scan Cards Design

## Purpose

The Graph workspace left page list should be readable as a navigation and
inspection surface, not a compressed run of link text and metadata. The current
graph already has strong canvas behavior, page focus, relationship filters, and
inspector panels, but the page list is hard to scan on desktop because the page
title, stable ID, status, explicit-link count, backlink count, and summary are
rendered as adjacent inline text.

This loop adapts the useful legacy sidebar idea of a clear page list into the
current static renderer by turning graph list rows into structured scan cards.
It keeps the current framework constraints: generated static HTML, local graph
script only, no fetch, no storage, no external graph dependency, no learner
state, and no new source of graph truth.

## Design

Each graph list item remains one `<li data-raya-graph-node="...">` so the
existing graph script can keep using the same selection, filtering, keyboard,
hover, and focus logic. Inside the item, the generated markup becomes:

- a title row with the existing page link and a compact status pill;
- a metadata row for stable ID and relationship counts;
- a summary row with public page summary text.

The visible order prioritizes learner scanning: title first, status second,
relationship counts third, summary last. Stable IDs remain visible because they
are useful for agents and debugging, but they are no longer glued to the title.

During browser verification, the longer graph interaction path showed that
stale canvas hover can race with focused list navigation. The graph script
therefore treats focus inside the list as the active inspection source and does
not let canvas hover overwrite it until focus leaves the list.

## Constraints

- Do not change the graph payload shape.
- Do not change graph selection, URL state, relationship filters, page focus,
  pan, zoom, or layout behavior.
- Do not add browser persistence.
- Do not add runtime data loading.
- Do not expose private source paths, artifact paths, cache keys, or source
  hashes.
- Do not introduce external scripts, graph libraries, fonts, renderers, or CDN
  requests.

## Testing

Add a contract test assertion to the existing graph surface test for the new
static classes and ordering. Add browser assertions to the existing visual graph
surface test to prove the list card has separated block rows, a visible status
pill, readable summary text, and no cramped title/metadata run-on.

Run the focused graph tests and the render-debug gate before review and commit.
