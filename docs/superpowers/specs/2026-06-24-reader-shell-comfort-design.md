# Reader Shell Comfort Design

## Context

The static renderer already has a modern course shell, course map, learning rail,
reader controls, skins, OpenDyslexic resources, official practice, search, graph,
tasks, and schedule workspaces. The remaining issue is visible comfort: the
desktop shell can still feel like three competing panels, and the render fixture
still speaks like a renderer test instead of a small learning example.

The old `main` branch remains historical reference only. This loop adapts the
useful UX idea from that branch -- stronger orientation and more inviting visual
surface -- without adopting Eleventy, Tailwind, CDN graph libraries, browser-side
renderers, or old data contracts.

## Goals

- Make the article the primary desktop reading surface.
- Keep course map and learning rail useful, but visually quieter than authored
  content.
- Make collapsed map and rail states feel intentional and scan-friendly.
- Rework the render fixture's `reader-ux` page into a credible mini-lesson while
  preserving renderer coverage for math, numbered objects, callouts, static
  environments, local assets, and references.
- Add browser-visible tests for desktop shell comfort and fixture pedagogy.

## Non-Goals

- No new source contract.
- No persistent map, rail, graph, search, practice, task, or schedule state.
- No inferred progress, recommendations, mastery, related practice, or learner
  analytics.
- No external CSS, fonts, scripts, graph libraries, renderer requests, or CDN
  assets.
- No page-level skin override implementation in this loop.

## Design

The renderer keeps the current three-region shell: course map, main article, and
learning rail. Desktop CSS gives the article a wider, calmer canvas; side panels
retain sticky utility but lose visual dominance through softer backgrounds,
lighter borders, and reduced shadow. Collapsed side surfaces remain operable
buttons and links, but their labels become compact symbols/text with stable
dimensions and accessible names.

The first screen remains statically oriented through top sequence links,
breadcrumbs, and Page brief, but CSS treats those blocks as compact orientation
chrome rather than competing content panels. The authored article should appear
quickly below them on desktop and mobile.

The render fixture remains explicitly fixture material in source prose, but
student-visible titles, summaries, headings, callouts, and images on `reader-ux`
become a coherent projection-residual mini-lesson. Fixture-only wording moves
out of high-visibility metadata. A real local projection/residual SVG replaces
the generic static-path image so local asset rendering also supports the lesson.

## Testing

Tests should prove behavior rather than screenshots alone:

- Browser test at wide desktop verifies article width, side-panel width, side
  visual quietness, stable collapsed controls, and no horizontal overflow.
- Browser/static test verifies the `reader-ux` page title, summary, early
  learner-facing prompt, meaningful callouts, official practice anchor, local
  projection diagram, and absence of high-visibility fixture/test language.
- Existing render-debug and static-read-path gates continue to prove raw TeX,
  local MathJax resources, no external renderer requests, static environments,
  screenshots, and local/deployed parity.

## Review Notes

This design intentionally improves what a student sees without pretending the
static renderer knows anything about the student's state. All new labels and
copy must be structural or instructional content authored in the fixture, not
generated recommendation language.
