# Search Result Graph Focus Design

Date: 2026-06-23

## Purpose

Course Search already helps readers find pages by generated metadata. Course Graph already accepts `?page=<stable_id>` and focuses the selected page. This change connects those two static discovery surfaces: every search result gets a secondary graph-focus action that opens the graph workspace centered on that exact page.

The action is structural navigation only. It must not imply recommendation, related practice, progress, mastery, ranking, or personal state.

## Scope

In scope:

- Add a generated graph-focus URL to each search payload page entry.
- Render a secondary `View in graph` action inside each search result.
- Preserve the existing primary page link and Enter-key behavior from the search input.
- Keep Search and Graph static, deployment-neutral, fetch-free, CDN-free, and storage-free.
- Update the renderer contract and English/Spanish role guides.
- Add contract and browser checks proving the action works and remains static.

Out of scope:

- New graph algorithms, inferred related-page ranking, personalized recommendations, progress state, or saved search state.
- Prose indexing or scraping rendered HTML.
- Runtime fetching of `graph.json` or `pages.json`.
- Browser-side MathJax changes.

## Behavior

Each search result keeps its page title as the primary link to the rendered page. A compact secondary action appears after the result metadata:

`View in graph`

The link target is generated from the search surface to the graph surface:

`../graph/index.html?page=<stable_page_id>`

The graph page already reads the `page` query parameter and selects the matching node. If the page ID does not exist, the graph keeps its normal empty-detail state.

Keyboard movement from the search input continues to activate the primary page link with Enter. The graph action remains an ordinary focusable link for Tab and screen readers.

## Data Contract

The search payload stays metadata-only. Page entries may include:

- `id`
- `title`
- `nav_title`
- `summary`
- `status`
- `tags`
- `hierarchy_label`
- `url`
- `graph_url`

`graph_url` is a deployment-neutral link to the generated local graph page with a stable page ID query. It must not point into `data/`, private source folders, artifact paths, external URLs, or runtime services.

## Testing

Contract tests should verify:

- Search HTML includes the secondary graph action.
- Search payload entries include only the accepted keys, including `graph_url`.
- `graph_url` uses `../graph/index.html?page=<id>`.
- No fetch, storage, external URL, private source path, artifact path, or Pagefind dependency is introduced.

Browser tests should verify:

- Searching for `matrix` shows `Authoring Matrix Fixture`.
- That result has a graph-focus link to `_raya/graph/index.html?page=authoring-matrix`.
- Opening that link focuses the graph detail panel on `Authoring Matrix Fixture`.
- No horizontal overflow or external requests are introduced.

## Documentation

Update the learning renderer contract and role guides to state that Course Search may expose graph-focus links generated from stable page IDs. Students should understand this as a way to inspect where a found page sits in the course graph. Agents and contributors should verify it as static metadata navigation, not as recommendations or learner state.
