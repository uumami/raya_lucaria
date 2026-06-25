---
id: superpowers-continuous-reader-search
title: Continuous Reader Search Design
summary: Make the reader shell feel calmer and more immediately searchable without reintroducing old renderer dependencies.
status: ready
---

# Continuous Reader Search Design

## Context

The old `main` branch had two useful reader-facing ideas that still fit the
reset framework when rebuilt locally: search was reachable from ordinary pages,
and the article flow felt less boxed than the current three-panel fixture view.
The current branch already has a reset-native static Search workspace with
public article prose, snippets, keyboard inspection, and graph handoffs. This
slice should not add Pagefind, fetches, browser-side indexing, browser-side
MathJax, or stored search state.

## Design

Add a compact search form to the top command bar on rendered reader pages. The
form submits with `GET` to the existing `_raya/search/index.html` surface using
the existing `q` query parameter. It has one text field, a clear accessible
label, a short placeholder, and a submit button. Empty submissions simply open
the Search workspace. The form is local HTML only and uses the already generated
Search page for all filtering and result inspection.

Polish the default reader layout so the main article reads as a continuous
surface rather than another heavy card. The article keeps its background and
padding, but drops the prominent shadow and heavy border. The course map and
right rail remain framed support surfaces because they are secondary controls;
their borders stay visible but quieter. Desktop keeps the three-column layout,
while mobile/tablet behavior remains unchanged.

## Boundaries

- No Pagefind, Eleventy, CDN, external font, fetch, XHR, or runtime search index
  creation.
- No `localStorage` or `sessionStorage` for search or shell state.
- No change to generated `data/search-index.json` contents in this slice.
- No graph behavior change.
- No personal progress, recommendations, mastery, rankings, or inferred study
  guidance.

## Tests

Contract tests should assert that reader pages render the search form with a
deployment-neutral action URL, `name="q"`, no runtime fetch dependency, and no
stored search state. CSS contract tests should assert the article uses the new
continuous-reader class and that the main article no longer receives the heavy
box shadow/border treatment.

Browser tests should submit a query from a reader page and verify navigation to
the existing Search workspace with the encoded `q` value and visible matching
results. Existing render-debug and static-read-path gates should continue to
cover local resources, overflow, screenshots, and external request constraints.

