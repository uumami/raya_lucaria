# Rail Graph Affordances Design

## Purpose

The right learning rail already exposes prerequisites and explicit linked-page context. This slice makes that context easier to orient in the graph by adding compact graph-focus links beside those rail entries.

## Scope

Add secondary `Graph` links in the learning rail:

- Prerequisite items link to the prerequisite page and include a graph-focus link for that prerequisite page.
- Linked-page items link to the related page and include a graph-focus link for that related page.
- Graph links use the existing static graph page with `?page=<target page id>`.
- The existing primary page links remain unchanged.

## UX Rules

- The primary action remains opening the page.
- The secondary action is visually compact and labeled `Graph`.
- The secondary action includes an accessible label such as `View <title> in course graph`.
- The rail remains collapsed by default where it is currently collapsed; hidden links remain inert through the existing shell behavior.

## Constraints

- Use only generated navigation and explicit graph context already available during build.
- Do not add browser storage, runtime fetches, external libraries, CDN requests, recommendations, personal progress wording, or inferred related practice.
- Keep links deployment-neutral and relative from the current rendered page.
- Do not add section-level graph behavior in this slice.

## Testing

Tests should prove:

- Rendered prerequisite and linked-page rail panels include graph-focus links.
- Graph-focus links encode the target page id and use relative static graph URLs.
- Browser interaction from a rail `Graph` link opens the graph with the target page selected.
- Collapsed rail content remains hidden/inert until expanded.
- Existing no learner-state wording and no external request checks remain green.
