---
id: numbered-object-learning-rail
title: Numbered Object Learning Rail
status: ready
date: 2026-06-27
workflow: superpowers
---

# Numbered Object Learning Rail

## Problem

Math-heavy pages already render numbered objects, proofs, equations, figures,
tables, problems, homework, assignments, and activities as public anchors. The
right learning rail currently exposes heading-based page contents, but a student
reading a dense page cannot jump directly to the key mathematical objects from
the rail. The generated Search workspace can see many of these anchors, so the
reader shell should make the same public structure usable in-place.

## Design

Extend the right rail Page contents panel with a compact `Key objects` group
derived from already rendered public article anchors. The group should include
numbered objects and proofs that the existing public article section parser can
identify. Each item links to the in-page anchor with the visible public label
that already appears in the rendered object, such as `Theorem 3.1 Fixture
theorem`, `Equation 3.1`, `Problem 4.1`, or `Proof of Proposition 4.1`.

This is structural navigation only. It must not introduce course progress,
recommendations, mastery, ranking, hidden learner state, browser storage,
runtime fetches, external requests, or new source-contract fields. It must not
expose source paths, private support directories, artifact internals, raw TeX,
or MathJax implementation text. It should keep headings first, then key objects,
so ordinary section scanning remains familiar while math objects become easy to
reach.

## Implementation

The renderer already computes public article sections during build with
`_public_article_search_sections`. Reuse that public output for the learning
rail instead of reparsing in browser JavaScript or reading generated JSON at
runtime. Pass the public section list from `_render_page` into
`_render_learning_rail`, then into `_render_page_contents_rail`. Render a
separate nested list when those sections point at object/proof anchors.

## Testing

Use TDD:

- Add a contract assertion that a render-fixture page containing numbered
  objects renders a `Key objects` subsection in the right rail with links to
  definitions, propositions, equations, figures, tables, problems, activities,
  homework/assignments, and proofs.
- Add a browser assertion that the desktop right rail exposes those links in the
  first-page context without horizontal overflow and without storage/fetch
  calls.
- Keep existing current-section, heading contents, mobile drawer, rail collapse,
  static-path, MathJax, and render-debug tests as regression coverage.

Finish with focused builder/e2e tests, `git diff --check`, a render-fixture
build, and `./scripts/check-render-debug.sh`.
