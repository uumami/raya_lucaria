# Command Bar Iconography Design

## Context

The current reset renderer has a strong static learning shell: course map,
right learning rail, reader comfort controls, Search, Graph, Practice, Tasks,
and Schedule workspaces. Legacy `main` used recognizable SVG controls in its
sidebar and top bar. The current branch intentionally avoided that old stack,
but its command buttons still use letter badges such as `C`, `S`, `G`, `P`,
`T`, `D`, and `Aa`. Those badges are compact, but they are weaker visual
affordances than real symbols and make the interface feel less polished.

The portable legacy idea is not the Eleventy/Tailwind implementation. It is
the use of compact semantic controls that help students identify navigation,
map, graph, practice, schedule, text-size, and accessibility actions quickly.

## Goals

- Make reader and discovery command bars easier to scan by replacing letter
  badges with local semantic glyphs.
- Keep generated HTML deployment-neutral and static.
- Preserve existing labels, `aria-label`s, links, keyboard behavior, and
  OpenDyslexic/text-size controls.
- Keep mobile command bars compact and non-overflowing.
- Add tests that prevent regression back to raw letter badges.

## Non-Goals

- No OpenSpec work in this loop.
- No external icon package, CDN, remote font, runtime fetch, service worker, or
  browser-side renderer.
- No dynamic theme picker or persisted skin choice.
- No learner-state storage, progress, recommendation, scoring, or tracking.
- No port of the old Eleventy sidebar, Tailwind classes, or JavaScript modules.

## Design

The command bar keeps the existing HTML structure and classes. CSS changes the
small command badge pseudo-element from text letters to local semantic glyphs
using simple Unicode symbols:

- Course/Home: house symbol.
- Search: magnifying glass.
- Graph: connected-node symbol.
- Practice: check mark.
- Tasks: clipboard/checklist symbol.
- Schedule: calendar symbol.
- Course map: map symbol.
- Text size: `A+`.
- OpenDyslexic: `Aa`, kept as a readable two-letter font cue because the
  command is specifically about letterform changes.

The visible button label remains unchanged. Screen readers continue to use the
existing `aria-label` text, so the glyph is only a visual cue. The glyph badge
keeps stable dimensions, border, and contrast using current skin tokens. Mobile
layouts keep the command strip horizontally scrollable instead of wrapping into
a tall header.

Tests should inspect computed pseudo-element content on reader and discovery
surfaces. They should also verify the command labels and `aria-label`s remain
present, local links remain deployment-neutral, and no horizontal overflow is
introduced on representative desktop and mobile viewports.

## Acceptance Criteria

- Reader command bars no longer compute old single-letter command badges for
  Course, Search, Graph, Practice, Tasks, Schedule, Map, or Text size.
- OpenDyslexic keeps the explicit `Aa` font cue while preserving its existing
  text label and `aria-label`.
- Discovery command bars use the same semantic glyph vocabulary.
- Existing command text labels and `aria-label`s remain visible/available.
- The generated pages still make no external icon, font, script, CSS, or fetch
  requests.
- Focused browser tests and render-debug verification pass.

## Self-Review

- Placeholder scan: no `TBD` or incomplete requirement remains.
- Scope check: this is one focused visual/accessibility polish slice.
- Boundary check: the design changes only generated static CSS and tests; it
  does not add persistence, old stack dependencies, or learner-state behavior.
