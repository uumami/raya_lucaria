# Page-Aware Discovery Design

## Purpose

Rendered course pages should open the local search and graph surfaces with the current page already in context. This adapts the stronger discovery UX from the legacy site while keeping the reset renderer static, metadata-only, and deployment-neutral.

## Scope

This slice adds page-context deep links:

- Page command bar `Search` opens `_raya/search/index.html?q=<current page title>`.
- Page command bar `Graph` opens `_raya/graph/index.html?page=<current page id>`.
- Linked-pages rail items may offer graph focus links for explicit incoming/outgoing page relationships.
- Search consumes only `q` from `window.location.search`, preloads the input, filters locally, and never persists the query.
- Graph consumes only `page` from `window.location.search`, selects the matching generated node, opens its detail panel, and keeps all graph data embedded in the page.

## Constraints

- No runtime `fetch`, XHR, workers, service workers, external graph libraries, CDN requests, or browser-side MathJax conversion.
- No local storage for search/graph state.
- No inferred recommendations, related practice, mastery, progress, analytics, or learner-state wording.
- Query parameters are transient UI state and must not become source truth.
- Links remain deployment-neutral relative URLs.

## UX Behavior

Search should feel like a learner starts from the page they were reading: the query box is already populated with the page title, the result list is filtered, and keyboard navigation remains unchanged. Clear or Escape returns to the unfiltered list.

Graph should feel like orientation, not personalization: the current page node is selected, the detail panel opens, neighboring explicit links are highlighted through existing selection behavior, and Reset clears the focus.

## Testing

Tests should prove:

- Generated page HTML includes encoded search and graph context links.
- Search and graph scripts parse URL parameters without storage or network APIs.
- Browser preview deep links preload search and select graph detail on desktop and mobile.
- Existing no-CDN/no-fetch/no-learner-state assertions remain green.
