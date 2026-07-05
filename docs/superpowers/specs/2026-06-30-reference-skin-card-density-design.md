# Reference Skin And Card Density Design

## Context

The course-first UX goal names EVA Unit 02 as a reference skin direction and
calls for dense scannable cards. Current skin profiles already validate
`tokens.density` as `comfortable`, `compact`, or `spacious`, and `skin.css`
emits `--raya-density` plus broad spacing variables. Repeated discovery cards
for Search, Practice, Tasks, and Schedule still use mostly hard-coded padding,
gaps, and action heights, so compact skin profiles do not visibly make repeated
cards denser.

## Chosen Slice

This loop makes density tokens affect repeated discovery cards and workspace
controls while preserving article readability. The first measurable target is a
compact EVA Unit 02-derived skin on the render fixture: Practice, Tasks, and
Schedule result cards should use smaller padding/gaps/action heights than the
comfortable baseline, while body text remains readable and no workspace stores
state, fetches external resources, exposes private paths, or introduces
learner-state language.

## Approaches Considered

1. **Global compact typography.** Reduce font sizes and line heights for compact
   skins everywhere. Rejected because it risks making article reading less calm
   and conflicts with the learning-science guidance to keep reading surfaces
   stable.
2. **Card-local density variables.** Extend emitted skin CSS with semantic
   density variables for card padding, card gaps, chip padding, and action
   heights, then apply those variables to repeated workspace cards and controls.
   Chosen because it gives visible card density without changing schemas or
   article text.
3. **Per-skin special CSS.** Add selectors for `eva-unit-02` only. Rejected
   because skin profiles should remain data-driven and not require hard-coded
   skin IDs in the shared renderer.

## Design

`packages/static/src/raya_static/skins.py` remains the skin authority. It will
emit additional density-derived CSS variables for every profile:

- `--raya-space-card-padding`
- `--raya-space-card-gap`
- `--raya-space-card-action-min-height`
- `--raya-space-chip-padding-block`
- `--raya-space-chip-padding-inline`

`packages/static/src/raya_static/rendering.py` will consume those variables on
repeated discovery cards and panels: Search results, Search section subresults,
Practice object cards, Tasks object cards, Schedule item cards, chips, and
result action links. The article body, main headings, MathJax, and authored
content font scale will not be changed.

Because this loop touches skin code, it also removes the legacy browser-side
skin override path: generated student pages keep their source-selected
`data-raya-skin`, but no longer write `skin-prepaint.js`, `skin-toggle.js`,
`raya:skin-override`, `data-raya-skin-override`, or a Skin toolbar command.
Reading comfort controls remain separate reader preferences.

## Test Strategy

Add a Playwright e2e regression that copies `examples/courses/render-fixture`,
adds an EVA Unit 02 compact skin profile, selects it in `raya.yaml`, previews
the course, and inspects `_raya/practice/index.html`, `_raya/tasks/index.html`,
and `_raya/schedule/index.html` at desktop and mobile widths. The RED test must
fail before implementation because current repeated cards use hard-coded
`1rem` padding and `2.25rem` action min-height.

The test will verify:

- compact skin is active through `data-raya-skin`;
- repeated cards have compact padding and action heights;
- body text remains at a normal readable size;
- no horizontal overflow;
- no browser storage;
- no external requests;
- no progress, mastery, recommendation, scoring, submission, or grading
  language appears in inspected workspace text.

Add or update contract/browser coverage proving default rendered student pages
do not expose browser-side skin override selectors, scripts, toolbar commands,
or storage keys.

Focused tests will run before the broader gates. Because this is browser-visible
renderer work, completion also requires render-debug, host and Docker gates,
role-doc impact review, adversarial review, and a goal ledger update.

## Role Documentation Impact

This changes how existing `tokens.density` affects visible workspaces. English
and Spanish role docs that describe skin debugging or visible renderer behavior
should mention that density controls compact workspace cards and controls, while
reading comfort controls remain separate and do not change source-selected skin
authority.

## Non-Goals

- No schema change to skin profiles.
- No new default global skin identity.
- No browser-side skin authority expansion; remove the previous browser skin
  override path from default rendered student pages.
- No stored workspace, graph, search, practice, task, or schedule state.
- No learner progress, mastery, ranking, recommendation, scoring, submission,
  grading, or personalization language.
- No article typography shrink for compact skins.
