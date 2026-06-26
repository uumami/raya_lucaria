---
id: reader-path-affordance-design
title: Reader Path Affordance Design
status: implemented
---
# Reader Path Affordance Design

## Context

The active UX convergence goal uses the old `main` branch as historical UX
evidence while preserving the reset renderer contracts. The old branch kept
reader controls and previous/next movement lightweight and visible. The current
renderer already has the correct data and behavior: a sticky reading context,
comfort controls, article-top previous/next links, end-of-page sequence cards,
page-brief graph context, and page connections.

The remaining gap is visual discoverability. The richest orientation affordances
are split across the command bar and below-the-fold sections. The first-viewport
`Page brief` is where students already pause for orientation, so it should carry
compact path actions from the same generated static data.

## Goal

Make reader path controls easier to see in the first viewport without adding new
data, storage, runtime dependencies, or browser-side authority.

## Design

Add compact static path actions to the existing page brief:

- reuse the existing course-order sequence data from `ContentModel`;
- render previous/next links as a `Learning path` fact when either target
  exists;
- keep links deployment-neutral and marked with the same `rel`,
  `data-raya-prev-page`, `data-raya-next-page`, and keyboard shortcut metadata
  used elsewhere;
- style page-brief link values as compact action chips with borders,
  background, hover, and focus states;
- keep the existing graph-context fact in the page brief;
- retain the existing command-bar reading context, article-top sequence, comfort
  controls, and end-of-page sequence cards.

No new source fields, artifact fields, persistence, fetches, external scripts,
or learner-state wording are introduced.

## Testing

Tests should prove that:

- page-brief markup includes a visible `Learning path` fact when previous or
  next pages exist;
- previous and next links retain generated `rel`, stable data attributes,
  keyboard shortcut metadata, and deployment-neutral relative URLs;
- page-brief path and graph links render as bordered chip-like affordances on
  desktop;
- the page brief remains responsive and avoids horizontal overflow on mobile;
- wording avoids progress, recommendation, completion, mastery, and other
  learner-state language.

## Risks

The main risk is duplicating previous/next links across command bar, article
top, rail, page brief, and bottom cards. Keep the page-brief version compact and
orientation-focused. Another risk is treating sequence as personal progress;
wording must remain structural and static.
