# Public Article Search Design

## Context

The old `main` branch used Pagefind to give students full-text search with
subresults. The reset renderer currently has a stronger static discovery
workspace, but Course Search only matches page metadata. That leaves a real
learning UX gap: students often remember a phrase from the lesson, not the page
title, tag, or stable ID.

This design adapts the useful old-main capability without reviving Pagefind,
Eleventy, runtime indexing, CDN resources, or browser-side fetching.

## Goals

- Add build-time local search over public rendered article text.
- Keep Search fully static: embedded payload, local script, no `fetch`, no
  external search library, no storage for search state.
- Keep private and support surfaces out of the student search payload:
  `_official` answer/support content, `_reviewed`, source paths, artifact paths,
  cache keys, runtime metadata, and private course directories.
- Keep math safe by indexing nearby public prose and authored accessible labels,
  not MathJax CHTML internals or raw TeX.
- Preserve current Search behavior: metadata matching, fuzzy matching,
  keyboard movement, hover/focus inspection, `?q=`, `?page=`, Clear/Escape, and
  graph/practice/tasks/schedule handoffs.

## Non-Goals

- Do not add Pagefind, workers, IndexedDB, service workers, or external search
  packages.
- Do not infer recommendations, rankings, mastery, progress, related practice,
  or learning state from text matches.
- Do not search private source files or accepted official answer/support fields.
- Do not expose source Markdown paths or generated artifact internals.

## Design

The builder will generate a public search index from each page's rendered
article HTML after Markdown, static environments, numbered objects, and build-time
MathJax processing have completed. The extraction step will remove renderer
chrome and private panels, ignore MathJax CHTML/assistive internals, normalize
whitespace, and retain only public article prose that is already visible on the
rendered page.

The generated artifact will write `data/search-index.json` for inspection and
also embed the same public search text in the Search workspace payload. Each
page payload gets:

- `search_text`: normalized public article text plus current metadata fields.
- `search_snippet`: a short public excerpt used for context when a prose match
  is active.

The Search script will continue filtering already rendered result cards. Its
matching haystack will use `search_text`, while result cards still display only
public title, summary, metadata, counts, and actions. The context panel may show
`Match text: <snippet>` for the active result when a prose snippet exists. This
is descriptive context, not a score or recommendation.

## Data Flow

1. Build each page as today.
2. Extract public article text from the rendered article HTML.
3. Store a per-page public search record in generated artifact data.
4. Render Search with an embedded JSON payload containing the same public
   records.
5. Search JavaScript filters local DOM cards from the embedded payload only.

## Testing

Contract tests will prove:

- `data/search-index.json` is manifest-declared and contains public page records.
- A phrase that appears only in article prose is searchable.
- Private tokens such as `_official`, `_reviewed`, `_assets`, `artifact`,
  `source_path`, `cache_key`, and `course/` do not appear in the payload.
- Raw TeX, MathJax CHTML class names, and official answer/support text do not
  appear in the payload.
- The Search script still avoids storage, runtime fetches, workers, and external
  requests.

E2E checks will prove:

- Opening `_raya/search/index.html?q=<public-prose-phrase>` shows the expected
  page.
- Clear and Escape reset the results without writing browser storage.
- The search page makes no external requests and does not load Pagefind.

## Documentation

Update the foundation renderer contract and role docs in English and Spanish to
say Course Search now includes public rendered article prose in addition to
metadata, while excluding private/support/answer/state surfaces.
