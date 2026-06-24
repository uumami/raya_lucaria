---
id: superpowers-reader-page-brief-design
title: Reader Page Brief Design
summary: Add a compact static first-screen orientation block to reader pages.
status: ready
---
# Reader Page Brief Design

## Problem

The current reader shell has strong orientation surfaces, but their useful
metadata is scattered: summary and status live in the right rail, page position
and tools live in the command bar, prerequisites and connections live in
collapsed rail panels or article-end blocks, and official practice appears
later in the article.

Students need a quick first-screen answer to "what is this page and what can I
use here?" without opening several panels. Agents need a stable surface for
debugging rendered reader context.

## Selected Approach

Render a compact **Page brief** immediately after article sequence navigation
and breadcrumbs, before authored content.

The brief uses only current generated page and artifact data:

- page summary;
- normalized page status;
- structural page position such as `Page N of M`;
- estimated time and tags when authored metadata exists;
- resolved prerequisites;
- explicit incoming/outgoing graph-link counts;
- accepted official practice count for the page scope.

The brief is static HTML. It does not fetch data, store state, infer learning
goals, infer related practice, personalize recommendations, or claim progress.

## Behavior

The brief renders only when it has useful metadata beyond the page title. It
contains a concise summary paragraph when `summary` exists and a set of small
facts. Facts may link to existing static anchors or generated workspaces:

- prerequisites link to resolved prerequisite pages;
- connections link to the page-focused graph workspace;
- official practice links to `#raya-official-practice` only when the page has
  accepted official objects.

The layout should fit in the article column on desktop and mobile, wrap facts
without horizontal overflow, and visually support scanning without becoming a
second navigation rail.

## Static Boundary

The page brief is generated at build time from the same data already used by
the course shell, right learning rail, graph/search workspaces, and official
practice section. It must not expose source paths, private support paths,
artifact internals, source hashes, cache keys, external links, browser-side
MathJax conversion, or learner-state language.

## Alternatives Considered

1. **Leave metadata in existing rails only**: low implementation cost, but
   first-screen orientation remains weak when the rail is collapsed or visually
   distant.
2. **Add a static Page brief**: selected. It reuses current data, improves
   orientation, and is easy to test.
3. **Add personalized next steps or recommended practice**: rejected. Static
   pages have no learner state and must not infer study guidance.

## Documentation Impact

Update the learning renderer contract to make the Page brief part of the
current shell. Update English and Spanish role docs for professors, students,
contributors, and agents so they know what metadata appears and what it does
not mean.

## Test Strategy

Use TDD.

- Contract tests assert the brief renders public summary/status/position,
  metadata facts, prerequisite links, graph-focus links, and official-practice
  anchors when data exists.
- Contract tests assert no recommendation/progress/mastery wording, source
  paths, private paths, runtime fetches, storage calls, or external requests are
  introduced.
- Browser tests assert the brief is visible on desktop and mobile, does not
  overflow, and uses only same-origin static requests.

## Self-Review

- No source schema change is required.
- The brief is a synthesis of already accepted metadata, not a new authority.
- The design preserves static deployment parity and no-CDN renderer rules.
