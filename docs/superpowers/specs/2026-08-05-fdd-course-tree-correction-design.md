# FDD-Style Course Tree Correction Design

Date: 2026-08-05
Status: approved in visual brainstorming
Scope: the reader left rail's course tree and full-height structural geometry

## Relationship To Prior Work

This design corrects the course-tree interaction and outer rail geometry from
`2026-08-04-navigation-first-course-rail-design.md`. That design remains the
authority for the navigation-first information architecture, command grid,
filter, footer, responsive rail states, storage boundaries, and modal drawer.
When the two designs differ on tree appearance, accordion behavior, or the
outer rail's vertical geometry, this correction governs.

The visual and interaction references are:

- `/home/uumami/itam/fdd_p26` and its deployed course;
- `/home/uumami/itam/ia_p26`, which uses the same sidebar implementation with
  a deeper content tree.

Raya adopts the reference's branch-disclosure model, compact rhythm, simple
vertical guides, and full-height sidebar. It does not copy its global storage,
inaccessible hidden descendants, undersized touch targets, inline handlers,
magic animation height, incomplete keyboard model, or mobile modality.

## Problem

The implemented course tree has working state logic but communicates it poorly.
The only visible branch affordance is a muted ASCII `>` or `v`; the title is a
separate page link; blank row space does nothing; leaves correctly have no
disclosure but look indistinguishable from broken branches; and the current
sequence pill overlaps the label. The fixture shown during review has one root
branch and five leaves, so the single weak disclosure is easy to miss and
clicking the current root link appears inert because it reloads the same URL.

Hierarchy guides are only a tight one-pixel vertical border with no convincing
relationship to the disclosure. The outer course rail also renders like a
short card and can end before the viewport, unlike the full-height FDD/IA
navigation surface.

## Goals

1. Make every branch visibly and predictably expandable by a dedicated
   disclosure control.
2. Keep every title a navigation link, matching FDD/IA option A selected during
   visual brainstorming.
3. Use same-depth accordion behavior without allowing unrelated interactions
   to hide the current path.
4. Restore compact FDD/IA tree rhythm, plain structural numbers, and one clear
   vertical guide per nesting level.
5. Make the structural rail cover the viewport from top to bottom with one
   central native scroll owner.
6. Preserve Raya's static rendering, keyboard behavior, semantic hiding,
   course-scoped state, filtering, accessibility, and mobile drawer lifecycle.

## Non-Goals

- Redesigning the course action grid, content filter, footer commands, mini-rail
  contents, right learning rail, article, or discovery workspaces. The mini
  rail's outer height and edge alignment are in scope because the same course
  rail container owns expanded and collapsed structural states.
- Making phone presentation a new visual priority. Phone behavior must remain
  functional, accessible, and regression-free, but desktop and tablet are the
  primary design targets for this correction.
- Copying FDD/IA colors, fonts, routes, course-specific numbering, global
  `localStorage`, stored scroll position, or max-height animation.
- Making a branch title toggle expansion or adding a separate trailing
  open-page action.
- Adding horizontal connector elbows. The selected reference uses restrained
  vertical guides only.

## Interaction Contract

### Disclosure And Navigation Ownership

Every node with visible child pages renders one row with:

1. a dedicated disclosure button;
2. one navigation anchor containing an optional structural-number span and a
   title span.

The disclosure button is the only pointer control that changes branch display.
Clicking either the number or title inside the anchor navigates to the node's
generated page. Row whitespace has no hidden action. A leaf renders an
equal-size disclosure spacer but no button, `aria-expanded`, or false
affordance.

Fine-pointer rows use `30px minmax(0, 1fr)`. Coarse/no-hover rows use
`44px minmax(0, 1fr)`. Column one is exactly the disclosure button or its
equal-size leaf spacer. Column two is the single navigation anchor. Inside that
anchor, the structural-number span is nonshrinking and the title span owns all
remaining width with `min-width: 0`. The current marker decorates the anchor's
inline-start edge and never occupies the disclosure, number, or title gap.

The disclosure uses a real chevron icon from the established icon system. It
points right when collapsed and rotates 90 degrees when expanded. The visible
icon remains 12-14px. Its target is at least 30px on fine-pointer desktop and
tablet layouts and at least 44px when `any-pointer: coarse` or `hover: none`
matches. Hover, pressed, and focus-visible states expose the control boundary
without styling every row as a card.

Each branch disclosure has stable `aria-controls`, synchronized
`aria-expanded`, and a state-specific accessible name containing the full
branch title: `Expand <title>` or `Collapse <title>`. The chevron is decorative
and hidden from the accessibility tree. Focus-visible treatment is at least
3px, remains inside the target, and is not clipped by the scroll owner.

### Accordion

Expanding a branch collapses other expanded branches at the same depth under
the same parent. Two exceptions preserve orientation and direct intent:

- accordion side effects do not collapse an ancestor of the current page;
- an explicit disclosure action on a current-path ancestor may collapse it,
  and unrelated branch, filter-clear, or restoration activity must not
  immediately undo that direct choice during the page lifetime.

On initial page load and navigation, current-page ancestors are exposed even
when a stored collapsed preference exists. This exposure is temporary and must
not overwrite the stored preference. Existing page-local explicit-collapse
bookkeeping remains valid, but pointer and keyboard disclosure paths must use
the same accordion transition function.

A user disclosure action is one persistence transaction. It applies the direct
node change, collapses eligible same-parent siblings, and writes the final
collapsed-ID preference set once. Accordion side effects are therefore part of
the direct action and are persisted. Filter exposure, load-time current-path
exposure, and effective-state normalization never write storage.

If a non-empty local filter is active, any direct branch action first clears the
volatile query and empty state, restores preference, deterministic accordion,
current-path, and explicit-collapse effective state without writing, and only
then applies and persists the one user accordion transaction. This order is
identical for disclosure click, disclosure `Enter`/`Space`, and title-anchor
`ArrowLeft`/`ArrowRight`; temporary filter exposure can never immediately undo
the requested branch result.

### Keyboard

The existing tree-link keyboard model remains when a title anchor owns focus:

- `ArrowDown` and `ArrowUp` move through visible page links;
- `Home` and `End` move to visible boundaries;
- `ArrowRight` expands a collapsed branch, then moves to its first visible
  child when already expanded;
- `ArrowLeft` collapses an expanded branch, then moves to its parent when
  already collapsed.

Native `Enter` or `Space` on a focused disclosure invokes the centralized user
transition and keeps focus on that disclosure when it remains visible. Arrow
keys are owned by title anchors and are not intercepted while a disclosure
button owns focus. Pointer and keyboard activation must produce the same
accordion, storage, active-path, `aria-expanded`, `hidden`, and `aria-hidden`
results; they are not required to focus the same element. No direct, accordion,
filter, or restoration collapse may leave focus inside a hidden subtree. If a
collapse would do so, focus moves to the disclosure of the branch being hidden.

## Tree Appearance

Fine-pointer tree text uses a stable 14px interface size with 19-21px line
height. Ordinary title anchors target a compact 27-30px rhythm while the fine
disclosure/spacer column remains exactly 30px. Long titles
wrap in normal flow and may increase only their own row; no overlay, hover-only
text reveal, clipping, or label overlap is permitted.

Each expanded child group follows the FDD/IA spatial model:

- 16px inline-start margin;
- 8px inline-start padding;
- one subtle one-pixel vertical border;
- no horizontal elbows.

The number span is derived only from `ContentPage.display_label` already
generated by the content model. Appendix entries prepend their established
`hierarchy_label` to that generated display label. It must not use global page
position, `sequence_index`, CSS counters, raw filename-prefix parsing, or title
parsing to invent hierarchy. When the display label is empty, the span is
omitted without changing disclosure or title ownership.

The structural number and title live inside the same navigation anchor, so the
link's accessible name contains the number exactly once followed by the title.
The builder displays `nav_title` unchanged. For de-duplication only, when the
normalized `nav_title` already begins with the exact generated structural label
followed by whitespace or punctuation, the separate number span is omitted.
The renderer never removes text from `nav_title` and never derives hierarchy
from that comparison. Fixture coverage must include this already-numbered case
and prove there is one visual and spoken prefix. The current pill treatment is
removed from the tree because its minimum width plus padding overlaps labels in
the available column.

Current state uses `aria-current="page"`, stronger text, an accent color, and a
two- or three-pixel inline-start marker on the anchor. Ancestors receive
moderate weight or surface emphasis without competing with the current page.

Skins may supply colors, but geometry, contrast, disclosure recognition, and
current/ancestor distinction remain renderer contracts.

## Full-Height Rail Geometry

At every structural width (`640px+`), the course rail is a fixed,
viewport-pinned navigation surface in both expanded and collapsed states:

- `position: fixed` with logical block insets of zero and inline-start zero;
- ordered fallback declarations `height: 100vh; height: 100dvh` and
  `box-sizing: border-box`;
- no outer margin, rounded card corners, bottom gap, or floating-card shadow;
- a restrained inline-end divider separates navigation from the article;
- the shell continues to reserve the accepted 256px expanded width or 48px
  collapsed width even though the aside itself is fixed.

The expanded surface remains a three-row layout:

1. fixed 48px header;
2. `minmax(0, 1fr)` central navigation;
3. fixed 48px footer.

Only the central navigation owns `overflow-y: auto`. It contains the course
actions, filter, and tree. The outer aside clips layout overflow and must not
become a second vertical scroller. The article keeps normal document scrolling.
The collapsed state keeps the existing 48px mini contents inside the same
full-height, square-corner, edge-aligned outer rail. It does not retain the
short card, outer inset, radius, shadow, or max-height behavior.

Phone presentation remains the existing full-height modal drawer with safe-area
handling, scroll lock, focus trap/restore, inert background, overlay, and Close
control. This correction must not copy FDD/IA's incomplete mobile behavior.

## Markup And Runtime Boundaries

### Builder

The builder owns recursive tree structure and initial static state. It emits:

- branch-only disclosure buttons;
- one number span plus title span inside a single navigation anchor;
- child groups with stable IDs and semantic grouping;
- the current path expanded in initial HTML so static/no-script reading retains
  orientation.

The builder must not infer new hierarchy or progress. It consumes only current
generated navigation data. Branch controls render with an enhancement-pending
marker so no-script CSS can remove them from display and tab order rather than
advertise inert buttons.

### Shell

The shell owns volatile and session-scoped display behavior. It maintains two
explicit layers:

1. preference state in each branch's `data-raya-map-expanded`, derived from the
   validated collapsed-ID payload and changed only by user transactions;
2. effective state in `aria-expanded`, `hidden`, and `aria-hidden`, which may
   add temporary filter/current-path exposure without changing preference.

A centralized user branch transition applies:

- direct node expansion or collapse;
- same-parent/same-depth accordion collapse;
- current-path protection and explicit-current-path exceptions;
- one atomic storage write for the final direct/accordion preference set;
- equivalent pointer and keyboard state results with the focus rules above.

The retained v1 payload stores collapsed branch IDs and may encode several
expanded siblings from pre-accordion sessions. Initialization parses that
preference without rewriting it, then derives deterministic effective
accordion state per sibling group: preserve the protected current-path branch
and at most the first additional eligible expanded sibling in document order;
effectively collapse later eligible siblings. The first subsequent user
disclosure transaction persists the complete normalized final collapsed-ID set
once. No storage version change is required because the payload meaning remains
"collapsed branch IDs."

Filter matches may temporarily open ancestors. Clearing the filter applies this
precedence without writing: persisted preference, deterministic accordion
normalization, current-path exposure, then page-local explicit current-ancestor
collapses. Page-local explicit-collapse bookkeeping survives BFCache restoration
of the same document and resets on a new document load or page navigation.
Invalid or unavailable session storage is ignored without disabling disclosure
behavior.

The accepted storage key remains
`raya:course-map-branches:v1:<course_id>` in `sessionStorage`. Filter text,
focus, scroll position, drawer state, current page, and active path are not
stored.

### Renderer CSS

Renderer CSS owns viewport geometry, the single scroll owner, disclosure and
number columns, chevron rotation, guide lines, row density, long-label flow,
and active states. Breakpoint rules must not change semantic DOM or interaction
ownership.

### Static And No-Script Presentation

When enhancement does not run, branch disclosure buttons are hidden and removed
from keyboard traversal. No-script CSS also hides and removes from traversal all
other enhancement-only rail controls and their tooltips or empty states: the
local filter, Context, Hide/Close/Expand map controls, Text size, OpenDyslexic,
drawer opener, and drawer backdrop. Static Search, Graph, Practice, Tasks, and
Schedule links, course home, structural position, branch/title anchors, article,
and right-rail static content remain available. At every width, no-script CSS
exposes the course rail as an in-flow static navigation surface before the
article rather than leaving a closed drawer or mini opener that cannot run. The
builder-rendered current path remains expanded; navigating a branch title loads
that branch's page and exposes its current subtree, so every course page remains
reachable without an inert advertised control.

At `640px+`, no-script presentation may retain the 256px column only when the
complete current-path navigation is visible. Below `640px`, it must neutralize
drawer transform, inert-looking overlay chrome, and body scroll lock and render
the same current-path navigation inline. This fallback needs no accordion,
filter, rail-collapse, or drawer behavior because those require enhancement.

## Failure And Fallback Behavior

- Nodes without children remain ordinary links even when JavaScript fails.
- Branch children on the current path are visible in initial HTML.
- A branch whose controlled child container is missing or invalid must not be
  enhanced into an operable disclosure; its title link remains available and a
  generated contract reports the mismatch.
- Invalid storage data is discarded logically and never copied into markup.
- Filtering to zero results keeps the existing concise empty state in the one
  central navigation scroller.
- Reduced motion removes chevron/rail animation timing without changing final
  state or focus.

## Verification

The existing render fixture is insufficient by itself because it exposes only
one branch. Browser coverage must include or extend a fixture with:

- at least three sibling branches at one depth;
- at least three hierarchy levels;
- a current page below one branch;
- a long branch label and long leaf label;
- generated structural display labels `1`, `1.2`, and `12.10`, an appendix
  label, an unnumbered root, and an authored already-numbered nav label that is
  normalized to one visual/spoken number;
- enough direct leaves inside one valid accordion branch to overflow the
  central navigation at a short viewport without expanding sibling branches.

This verification supplements rather than replaces the responsive/static
matrix in the prior navigation-first design. Chromium checks cover 1440, 1024,
894, 893, 768, 640, 639, and 390px, normal and short heights, fine and
coarse/hybrid input, expanded/collapsed structural states, and open/closed
drawer states. They must verify:

1. expanded and collapsed structural rail rects have top zero and bottom equal
   to `innerHeight` before and after article scroll and dynamic viewport change;
2. header/footer remain fixed while only central navigation scrolls;
3. disclosure hit testing targets the button, not the link or blank row;
4. branch labels navigate and leaves expose no disclosure semantics;
5. disclosure accessible name, `aria-controls`, `aria-expanded`, decorative
   icon, focus indicator, `hidden`, and `aria-hidden` remain synchronized after
   pointer, Enter/Space, title-link arrows, filter, and storage restoration;
6. expanding a branch collapses eligible same-level siblings;
7. the current path is not collapsed as an accordion side effect;
8. direct current-ancestor collapse survives unrelated interaction during the
   page lifetime and load-time exposure does not overwrite stored preference;
9. filter expansion/restoration preserves accordion and current-path rules;
10. every expanded hierarchy level measures 16px logical margin, 8px logical
    padding, and a visible one-pixel vertical guide with no horizontal elbow;
11. in fine-pointer, hover-capable contexts at 1440, 893, 768, and 640px,
    computed tree text is 14px, line height is 19-21px, ordinary title anchors
    are 27-30px, disclosure/spacer columns are exactly 30px, and numbers,
    titles, chevrons, and markers never overlap;
12. long labels remain inside the rail without horizontal overflow;
13. in coarse or no-hover contexts at those widths and in the phone matrix,
    disclosure/spacer columns and title-link targets are at least 44px while
    wrapped rows may grow;
14. phone tests prove the same DOM plus Close, Escape, backdrop, focus trap,
    opener focus restoration, inert background, scroll lock, safe-area
    containment, branch semantics, and no hidden focusable descendants;
15. JS-disabled Chromium at 1440, 893, 640, 639, and 390px shows reachable
    current-path navigation; sequentially follows branch-title links through
    three levels to a deep leaf; and exposes no visible or focusable
    enhancement-only button, input, tooltip, empty state, backdrop, disclosure,
    or opener-only trap;
16. scroll/orientation tests use deterministic path expansion and a valid
    overflowing accordion state; the old expand-all helper is removed rather
    than allowed to loop against accordion behavior;
17. with a non-empty descendant-match filter, disclosure click, disclosure
    `Enter`/`Space`, and title-anchor arrows all clear the filter first and end
    with equivalent effective, preference, accordion, and stored branch state.

Capture expanded current-path, peer-expanded accordion, long-label,
full-height collapsed-rail, and phone-drawer screenshots. Visual comparison
asserts element bounds and interaction state, not color similarity alone.

Adversarial Chromium reviewers must compare the completed desktop/tablet tree
against both FDD and IA reference screenshots and independently exercise every
visible disclosure. The comparison should confirm the selected option A model,
not merely static visual similarity.

## Truth-Surface Changes

Implementation must update the smallest affected current truth surfaces:

- `docs/foundation/20_learning_renderer_contract.md` gains the full-height
  expanded/mini structural container, FDD-style separate disclosure/link,
  same-parent accordion with current-path/direct-intent rules, and no-script
  fallback;
- affected English and Spanish contributor, professor, student, and agent role
  guides describe the corrected branch action and full-height navigation only
  where they currently document the course rail;
- static builder, renderer, shell, storage, accessibility, and browser contracts
  replace assertions/comments for ASCII toggles, pills, tight indentation,
  short-card geometry, and expand-all behavior;
- render-debug captures and inspection checks add the valid accordion/full-height
  states without treating generated screenshots as source truth.

## Acceptance Criteria

The correction is complete when a reader can immediately distinguish branches
from leaves, expand a branch by its chevron, navigate by its title, understand
hierarchy from the reference-style vertical guides, and use the full rail from
viewport top to bottom without clipped navigation or nested scroll confusion.
The current path remains oriented unless the reader directly collapses it, and
all pointer, keyboard, storage, filter, static, tablet, and phone contracts stay
coherent.
