# Reader Context Command Design

## Context

The reset renderer already supports a desktop course map, a right learning rail,
reader focus mode, and mobile drawer behavior. The right rail can collapse, but
the control lives inside the rail header. Students who want more article width
must either use full `Focus reading`, which collapses both side regions, or move
to the rail header and collapse it there.

The old `main` branch made sidebar and TOC collapse controls easy to find from
persistent navigation chrome. This design adapts that idea into the current
static renderer without restoring old Eleventy, Tailwind, CDN, or storage
patterns.

## Goals

- Add a top command-bar control for the right learning rail on desktop reader
  pages.
- Let students widen the article while keeping the course map available.
- Keep the existing right-rail collapse and expand controls working.
- Mirror state across all context controls with accessible labels and
  `aria-expanded`.
- Keep mobile and tablet article-first behavior unchanged; the right rail stays
  expanded there.
- Preserve reset constraints: no fetch, no external UI libraries, no browser
  storage for layout state, no progress/mastery/recommendation semantics.

## Non-Goals

- Do not persist layout state between page loads.
- Do not add a new theme, graph feature, search behavior, or source schema.
- Do not make right-rail collapse available on mobile, where the rail must
  remain visible and accessible after the article.
- Do not infer learning progress from whether the rail is shown or hidden.

## Design

The builder will add a `Context` command button to the reader top bar next to
`Focus reading`. The button uses `data-raya-learning-rail-toggle`,
`aria-controls="raya-learning-rail-body"`, and `aria-expanded="true"`. It is
hidden on non-desktop layouts by CSS, matching the current rail-collapse
contract.

The shell script will collect every `data-raya-learning-rail-toggle` button and
sync them whenever `setLearningRailExpanded()` runs. Clicking the top-bar
context command toggles the right rail on desktop only. The existing rail header
`Hide context` and collapsed `Context` tab continue to work; all three controls
reflect the same transient state.

When the rail is collapsed, the article uses the current wider grid state while
the course map can remain expanded. The collapsed rail remains an operable
desktop context tab. `Focus reading` remains the stronger mode that collapses
both course map and learning rail.

## Accessibility And UX

The new command is keyboard reachable in the same group as Search, Graph,
Practice, Tasks, Schedule, Course map, and Focus reading. Its accessible label
changes between `Hide learning context` and `Show learning context`. On mobile
and tablet the command is hidden and the shell forcibly restores the rail to an
expanded accessible state, preserving the existing article-first behavior.

The control is structural display state only. It does not store a learner
preference, track reading, or imply that hidden context is complete or
unimportant.

## Testing

Contract tests should prove the static reader top bar contains the context
command and the shell script contains the shared rail-toggle hook.

Browser tests should prove that on desktop:

- the top command collapses the right learning rail;
- `aria-expanded` mirrors across the top command, rail collapse button, and
  collapsed rail tab;
- article width increases while the course map stays expanded;
- clicking the command again restores the rail;
- no horizontal overflow is introduced.

Mobile tests should prove the top command is hidden and the right rail remains
expanded and reachable.

## Documentation

Update the learning renderer contract and English/Spanish student and agent
guides. The docs should describe this as a comfort/layout affordance for keeping
or hiding page context, not as progress, mastery, recommendation, or
personalization.

## Self-Review

- Placeholder scan: no TBD/TODO placeholders remain.
- Internal consistency: the command only affects the existing right rail state.
- Scope check: one reader-shell control and tests/docs only.
- Ambiguity check: desktop-only behavior and no-storage constraints are explicit.
