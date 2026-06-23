# Discovery Workspace Chrome Design

## Context

The current renderer has strong course-page chrome: a sticky command bar, local
reader comfort controls, course map, learning rail, local search, and local
graph. The standalone discovery pages under `_raya/search/` and `_raya/graph/`
work correctly, but they still feel less integrated than normal course pages.

Legacy `main` had a stronger app-like shell with top navigation and sidebar
tools, but it also depended on runtime theme state, external fonts/renderers,
Pagefind, service-worker behavior, and persisted navigation state. This design
adapts only the useful UX idea: discovery surfaces should look and behave like
first-class parts of the static course.

## Selected Approach

Add shared, static discovery chrome to `_raya/search/` and `_raya/graph/`.

Each standalone surface will render:

- a sticky discovery command bar using existing Raya command-button styling;
- course title and current workspace label;
- `Back to course`;
- cross-link from Search to Graph and Graph to Search;
- local `Text size` and `OpenDyslexic` controls using the existing local
  accessibility assets;
- no course-map toggle, because these pages do not render the course map;
- no persistent search/graph/page state.

The pages continue to use their embedded JSON payloads and local JavaScript.
The normal article shell script is not loaded on discovery pages.

## Alternatives Considered

### Full Article Shell Around Search And Graph

This would make Search and Graph visually identical to normal course pages, but
it would require rendering course map and learning rail on utility pages. That
adds layout weight and invites coupling to article-only shell behavior.

### Leave Standalone Pages As They Are

This preserves the current simpler implementation, but it leaves the strongest
remaining legacy UX gap: standalone tools still feel separate from the course.

### Shared Discovery Chrome

This gives the pages first-class course identity and common controls while
keeping them static, local, and decoupled from article page behavior. This is
the selected approach.

## Behavioral Requirements

- Discovery chrome must be generated during build.
- Links must be deployment-neutral relative static links.
- Search must link to Graph.
- Graph must link to Search.
- Both pages must keep `Back to course`.
- Both pages must include local `Text size` and `OpenDyslexic` controls.
- The controls must use existing local accessibility resources.
- The pages must not load `shell.js`, Pagefind, Cytoscape, external fonts, CDN
  assets, browser-side MathJax, service workers, or runtime renderer libraries.
- The pages must not store search state, graph state, page selection,
  recommendations, progress, answers, or mastery.
- Documentation must describe the chrome as static discovery tooling, not
  recommendations or personal state.

## Implementation Shape

Add a small helper in `packages/static/src/raya_static/builder.py` that renders
discovery command chrome for a named workspace. Use it from
`_render_search_surface` and `_render_graph_surface`.

Style the shared chrome in `packages/static/src/raya_static/rendering.py` by
reusing existing `.raya-top-command-bar`, `.raya-reading-context`, and
`.raya-command` patterns with a discovery-specific wrapper class.

Tests should assert generated markup, forbidden runtime tokens, no external
requests, comfort controls on both pages, cross-links, and no horizontal
overflow.

## Non-Goals

- No graph pan/zoom library.
- No full-text prose search.
- No Pagefind.
- No browser-side graph payload fetch.
- No persisted graph/search state.
- No course map or learning rail inside discovery pages in this slice.
- No runtime theme chooser; skins remain build-time course/section selections.

## Verification

Focused verification should include static builder contract tests, Playwright
checks for Search and Graph, and render-debug if layout or local resource
behavior changes. Full completion still requires `./scripts/check.sh` and
`./scripts/check-docker.sh`.
