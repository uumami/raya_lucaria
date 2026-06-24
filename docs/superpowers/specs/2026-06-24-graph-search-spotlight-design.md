# Graph Search Spotlight Design

## Context

The graph workspace already supports local fuzzy search, match expansion to one-hop neighbors, group filters, selected-page detail, source-group edge colors, hover/focus inspection, and transient dimming. The next renderer quality slice is to make search state visually legible inside the SVG graph itself: exact search matches should read as the foreground, their one-hop context should remain visible, and unrelated visible nodes and edges should recede.

This adapts the useful legacy graph behavior of search highlighting and fading, but keeps the current reset architecture: no Cytoscape, no CDN, no browser-side data fetch, no storage, no schema change, and no learner-state language.

## Goals

- While graph search has a non-empty query, matched nodes keep the existing match styling and become the visual spotlight.
- One-hop neighbors of matched nodes stay visible as structural context.
- Visible nodes outside the match-plus-context set are dimmed.
- Visible edges incident to a matched node are emphasized as search context.
- Visible edges not incident to a matched node are dimmed while search is active.
- Hover/focus inspection remains stronger than search spotlight for the inspected node and its incident edges.
- Reset clears search spotlight because it clears graph search.
- Layout, filters, selected-page details, and neighborhood focus continue to use current static behavior.

## Non-Goals

- No graph data schema change.
- No search ranking, recommendation, mastery, progress, or importance language.
- No browser-side fetch, external graph library, CDN, worker, cache API, or persistent graph state.
- No prose scraping or search over rendered article body text.
- No change to Search workspace behavior in this slice.

## Architecture

The graph script already computes `matchIds` and expands visible nodes to include one-hop neighbors when `query` is non-empty. Add a small derived helper in `packages/static/src/raya_static/graph.py` that returns the current search spotlight set:

- empty set when no query is active;
- all matched node IDs;
- direct neighbors of matched nodes that survive current group filters.

During render and inspection DOM updates, apply classes to SVG nodes and edges from that derived set. The graph list should keep its current match and selected/neighbor classes; dimming is primarily a visual graph cue so list navigation remains readable.

CSS in `packages/static/src/raya_static/rendering.py` should define separate search-context classes instead of reusing inspection classes. This keeps hover/focus inspection and search spotlight understandable and testable:

- `is-search-context` for one-hop search context nodes and incident edges;
- `is-search-dimmed` for visible nodes/edges outside the search spotlight.

The graph help text and foundation/agent docs should call the behavior a structural search spotlight, not a relevance ranking or recommendation.

## Testing

Use TDD against existing graph tests.

Contract coverage:

- generated graph HTML mentions search spotlight as a structural cue;
- generated graph JS contains the helper and class names;
- graph CSS contains the search context and search dimming classes;
- no forbidden runtime APIs or external renderer dependencies are introduced.

Browser coverage:

- searching `matrix` shows the exact match and at least one connected page;
- the matched SVG node has `is-match`;
- a directly connected visible node has `is-search-context`;
- an unrelated visible node has `is-search-dimmed`;
- an edge incident to the match has `is-search-context`;
- a non-incident visible edge has `is-search-dimmed`;
- clearing/resetting search removes search dimming classes.

## Documentation

Update the learning renderer contract and EN/ES agent guide wording for graph checks. The docs should describe the feature as a non-persistent readability cue over generated graph data.

## Self-Review

- No placeholders remain.
- Scope is limited to graph search spotlighting.
- The design does not change source or artifact contracts.
- The design preserves current renderer constraints and avoids learner-state wording.
