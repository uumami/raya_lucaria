# Page-Local Quiz Interaction Design

## Context

The current reset renderer already renders official quiz objects from colocated
`_official/quizzes/*.yaml` files into reader pages. Those pages keep the static
contract: the answer is available through a local `<details>` reveal, nothing is
submitted, and no state is saved. The old `main` branch has a useful UX pattern
for immediate quiz checking and retry, but it is tied to legacy Eleventy
components and checkbox parsing.

This design adapts the useful interaction to the current renderer without
importing the old component model.

## Goal

Official multiple-choice quiz objects on reader pages should support immediate
local checking and retry while preserving the existing static answer reveal as a
no-JavaScript fallback.

## Requirements

- Render official quiz options as native buttons when option data is present.
- Mark the selected answer after a click and visually identify correct options.
- Show short local feedback in the quiz card: correct selections are confirmed;
  incorrect selections tell the learner to try again and leave the reveal
  available.
- Provide a reset button that clears only the current page-local quiz state.
- Preserve the existing `<details>` answer reveal so static and no-JavaScript
  readers still work.
- Do not use `localStorage`, `sessionStorage`, cookies, network requests,
  browser-side MathJax, or external resources.
- Keep the behavior local to reader pages through the existing static shell
  resource copied into `artifact/site/_raya/render/shell.js`.
- Keep keyboard access native: option controls and reset use `<button>`.
- Keep generated markup inspectable for agents through explicit `data-raya-*`
  attributes.

## Non-Goals

- No persistent progress, scoring, analytics, adaptive sequencing, or user
  identity.
- No change to the official quiz YAML schema.
- No change to the separate practice workspace in this slice.
- No browser-side conversion of TeX or Markdown.

## Rendering Model

The builder keeps using the existing official quiz object contract. For each
question with options, it emits:

- a `.raya-official-options` list;
- one native button per option with
  `data-raya-official-quiz-option` and
  `data-raya-official-quiz-correct`;
- a polite status node with `data-raya-official-quiz-feedback`;
- a reset button with `data-raya-official-quiz-reset`;
- the existing `.raya-official-reveal` answer details.

The shell script initializes these controls after load. It uses DOM attributes
only, so reloading the page returns every quiz to its initial state.

## Interaction States

Initial:

- quiz root has `data-raya-official-quiz-state="ready"`;
- options are enabled;
- feedback text is empty or neutral;
- reset is hidden.

Answered correctly:

- quiz root becomes `data-raya-official-quiz-state="answered"`;
- selected correct option gets `data-raya-official-quiz-selected="true"`;
- all correct options get `data-raya-official-quiz-result="correct"`;
- feedback says `Correct.`;
- reset is visible.

Answered incorrectly:

- quiz root becomes `data-raya-official-quiz-state="answered"`;
- selected wrong option gets `data-raya-official-quiz-result="incorrect"`;
- correct options get `data-raya-official-quiz-result="correct"`;
- feedback says `Try again. The correct option is available below.`;
- reset is visible.

Reset:

- clears quiz state and result attributes;
- reenables option buttons;
- hides reset;
- restores the neutral feedback label.

## Styling

The existing official quiz visual language remains. Option buttons should feel
like answer choices, not form-heavy controls: full width, left aligned, compact,
with strong focus outlines. Correct and incorrect states use existing semantic
skin tokens so they adapt to course skins.

## Testing

Tests should prove the behavior at three layers:

- rendered HTML contains native option/reset/status controls and keeps the
  answer reveal;
- browser interaction marks correct/incorrect answers, resets state, and does
  not write storage;
- focused static parity checks still reject external requests and browser-side
  renderer dependencies.

## Self-Review

- No placeholders remain.
- Scope is one renderer slice: article-local quiz interaction.
- The design preserves current source authority and static deployment rules.
- The separate practice workspace is intentionally out of scope to avoid mixing
  reader-page micropractice with workspace-level study flows.
