# End-of-Page Sequence Cards Design

The current static reader already exposes generated course order in the command
bar, at the top of the article, and in the right rail. The remaining useful
legacy affordance is a larger previous/next navigation target at the end of the
article, after the student has finished reading the page.

## Goal

Add article-end Previous and Next cards generated from the existing ordered
course pages. The cards must help students move through the authored order
without becoming recommendations, progress tracking, or adaptive study state.

## Constraints

- Reuse `ContentModel.pages`; do not add a new schema, artifact index, or
  source-course contract.
- Keep compact top article sequence links and right-rail sequence links.
- Keep `rel="prev"`, `rel="next"`, `data-raya-prev-page`, and
  `data-raya-next-page` on generated sequence links so keyboard shortcuts
  continue to work.
- Do not add `fetch`, storage, browser-side rendering, external libraries, CDN
  assets, or recommendation logic.
- Use structural wording only: "Previous page", "Next page", page title, and
  structural page position. Avoid "recommended", "progress", "mastery", or
  "continue your learning".
- Omit unavailable directions instead of rendering disabled placeholders.

## Design

`packages/static/src/raya_static/builder.py` gains a small sequence-target
helper that calculates the current page index, previous target, next target,
relative hrefs, and total page count once. Existing compact sequence links keep
their current text. A new `_render_article_sequence_cards()` helper renders a
bottom `<nav class="raya-article-sequence-cards">` after authored content and
page connections.

Each card is a normal static anchor:

```html
<a class="raya-sequence-card raya-sequence-card-next"
   rel="next"
   data-raya-next-page
   href="topic/index.html">
  <span class="raya-sequence-card-kicker">Next page</span>
  <span class="raya-sequence-card-title">Topic title</span>
  <span class="raya-sequence-card-meta">Page 3 of 6</span>
</a>
```

CSS in `packages/static/src/raya_static/rendering.py` presents the cards as a
responsive grid: two columns when space allows, one column on narrow screens,
with clear focus states and no horizontal overflow.

## Tests

- Contract tests assert first, middle, and last pages render only available
  bottom cards with correct hrefs, labels, `rel`, and `data-raya-*` attributes.
- Contract tests assert the bottom cards appear after authored article content
  and after page connections when a page has them.
- Browser tests assert the cards are visible on desktop and mobile without
  horizontal overflow, use local links, and do not break existing sequence
  keyboard shortcuts.
- Documentation tests continue to guard role docs and renderer constraints.

## Documentation

Update the renderer contract and English/Spanish role docs to explain that
bottom Previous/Next cards are structural course-order navigation, not progress
or recommendation surfaces.
