# Article Page Connections Design

## Goal

Make explicit graph context visible at the end of a lesson page by adapting the useful legacy inline backlinks affordance into the current static renderer.

## Context

Legacy `main` rendered a `Referenciado por` backlinks section directly after article content. That made incoming references visible when a learner finished reading, but it depended on the old Eleventy stack and legacy graph assumptions.

The current renderer already builds explicit graph context from current source links and stable page IDs. It shows that context in the right learning rail and in the generated Graph workspace. The weak point is discoverability: on mobile the rail appears after the article and map, and on desktop the `Connections` rail panel is compact context rather than part of the reading flow.

## Design

Add a static `Page connections` block inside `article.raya-main-article` after authored content and before the article closes. It renders only when the page has explicit outgoing or incoming content links in `page_graph_context`.

The block contains:

- a heading, `Page connections`;
- a compact count row for `From this page` and `Links here`;
- an `Open in course graph` link with `?page=<current-page-id>`;
- a `From this page` list for outgoing explicit content links;
- a `Links here` list for incoming explicit content links.

Each linked page row uses normal deployment-neutral page links plus a secondary graph-focus link for that target page. The existing right-rail `Connections` panel remains unchanged.

## Boundaries

- Use only existing `page_graph_context`; do not add source or artifact schema.
- Do not infer related pages from prose, headings, tags, math, or rendered text.
- Do not add fetch/XHR, external graph libraries, browser-side rendering, or storage.
- Do not use progress, mastery, recommended, completion, ranking, or importance language.
- Hide the block entirely when there are no explicit incoming or outgoing content links.
- Keep links deployment-neutral and do not expose source paths, artifact paths, hashes, or private support paths.

## Tests

Contract coverage should assert generated article HTML contains the block for a connected fixture page, includes outgoing and incoming sections, contains the graph-focus URL for the current page, and excludes forbidden learner-state language and private/source paths.

Browser coverage should open a connected render fixture page on desktop and mobile, verify the block is visible inside the article after authored content, verify links remain local and deployment-neutral, verify no horizontal overflow, and verify no external requests are made.

Documentation should update the learning renderer contract and EN/ES student/agent guidance to say explicit page connections may appear in the article as static graph context, not recommendations or progress.

## Self-Review

- No placeholders remain.
- The design uses existing graph context and does not add schema or runtime data loading.
- The block is scoped to explicit content links and hides when empty.
- The design preserves current rail and graph behavior instead of replacing them.
