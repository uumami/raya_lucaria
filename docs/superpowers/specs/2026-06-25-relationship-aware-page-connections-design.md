# Relationship-Aware Page Connections Design

## Goal

Make reader-facing Page connections more useful as a static reading map by showing explicit relationship kind and direction in the article and right-rail previews.

## Context

The legacy `main` branch exposed inline backlinks after article content, which helped readers notice pages that referred to the current lesson. The current reset branch already has a stronger contract: generated graph context, article Page connections, rail Connections, graph-focus links, and native page previews. The current weakness is that the connection rows look generic. They show a linked page title and counts, but they do not tell the reader whether the preview is an outgoing explicit content link from the current page or an incoming explicit content link back to the current page.

The current builder already carries `kind` on graph-context items. This loop should expose that existing public metadata without changing schemas, adding runtime fetches, or copying old browser-side theme/sidebar behavior.

## Design

Add relationship-aware orientation to existing connection previews:

- each preview summary gets a compact relationship badge before the linked page title;
- outgoing article and rail previews label the direction as `From this page`;
- incoming article and rail previews label the direction as `Links here`;
- the badge includes the normalized relationship kind, currently `Content`, from existing graph context;
- the preview body adds one short structural sentence explaining the direction, for example `This page links to the target page through an explicit content link.`;
- the article section headings remain `From this page` and `Links here`, and graph-focus links stay unchanged.

This keeps the current native `<details>` preview interaction. The page remains useful without JavaScript, and opening previews must not write browser storage.

## Boundaries

- Use only `page_graph_context` generated from current graph edges.
- Do not infer related pages from prose, headings, tags, search text, math, or graph position.
- Do not introduce browser-side graph data fetches, CDN resources, persistent graph state, or browser-side MathJax.
- Do not expose source paths, artifact paths, private support paths, hashes, or cache keys.
- Do not use recommendation, ranking, importance, progress, completion, mastery, or personalization language.
- Do not change artifact graph schema in this slice.

## Documentation

Update the learning renderer contract and EN/ES role docs to say that article Page connections and rail Connections can show relationship kind and direction from explicit graph context. Students should understand this as a reading map. Professors should understand that authored content links feed the surface. Contributors and agents should verify that labels come from explicit generated graph context and remain static.

## Tests

Contract tests should verify:

- rail previews include relationship badge text and direction explanation;
- article previews include relationship badge text and direction explanation;
- graph-focus links and page links remain deployment-neutral;
- forbidden language and private/source paths remain absent.

Browser tests should verify:

- article preview summaries expose relationship labels on desktop and mobile;
- opening a preview shows the direction explanation;
- no local/session storage is written by the interaction.

## Self-Review

- No placeholders remain.
- Scope is a bounded UX polish over existing data.
- The design does not add schema, runtime data loading, external resources, or learner state.
- The design advances the main-branch UX fusion goal by keeping the useful backlink/read-map idea and adapting it to current static renderer contracts.
