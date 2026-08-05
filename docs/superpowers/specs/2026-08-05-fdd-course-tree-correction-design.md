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

- Redesigning the course action grid, content filter, footer commands, mini
  rail, right learning rail, article, or discovery workspaces.
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

Every node with visible child pages renders:

1. a dedicated disclosure button;
2. an optional structural number in its own inline area;
3. a title link.

The disclosure button is the only pointer control that changes branch display.
The title always navigates to the node's generated page. Row whitespace has no
hidden action. A leaf renders a stable disclosure spacer but no button,
`aria-expanded`, or false affordance.

The disclosure uses a real chevron icon from the established icon system. It
points right when collapsed and rotates 90 degrees when expanded. The visible
icon remains 12-14px. Its target is at least 30px on fine-pointer desktop and
tablet layouts and at least 44px when `any-pointer: coarse` or `hover: none`
matches. Hover, pressed, and focus-visible states expose the control boundary
without styling every row as a card.

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

### Keyboard

The existing tree-link keyboard model remains:

- `ArrowDown` and `ArrowUp` move through visible page links;
- `Home` and `End` move to visible boundaries;
- `ArrowRight` expands a collapsed branch, then moves to its first visible
  child when already expanded;
- `ArrowLeft` collapses an expanded branch, then moves to its parent when
  already collapsed.

Keyboard expansion and collapse produce the same accordion, storage, active
path, `aria-expanded`, `hidden`, `aria-hidden`, and focus results as pointer
activation.

## Tree Appearance

Fine-pointer tree text uses a stable 14px interface size with approximately
20px line height. Ordinary rows target a compact 27-30px rhythm. Long titles
wrap in normal flow and may increase only their own row; no overlay, hover-only
text reveal, clipping, or label overlap is permitted.

Each expanded child group follows the FDD/IA spatial model:

- 16px inline-start margin;
- 8px inline-start padding;
- one subtle one-pixel vertical border;
- no horizontal elbows.

Structural numbers are plain compact text in a dedicated flex/grid area before
the title. The current pill treatment is removed from the tree because its
minimum width plus padding overlaps labels in the available column. Current
state uses `aria-current="page"`, stronger text, an accent color, and a two- or
three-pixel inline-start marker. Ancestors receive moderate weight or surface
emphasis without competing with the current page.

Skins may supply colors, but geometry, contrast, disclosure recognition, and
current/ancestor distinction remain renderer contracts.

## Full-Height Rail Geometry

At structural desktop and tablet widths, the expanded course rail is a
viewport-pinned navigation surface rather than a short card:

- block size: `100dvh`, with a `100vh` compatibility fallback where needed;
- inset block start: zero;
- no outer margin, rounded card corners, bottom gap, or floating-card shadow;
- a restrained inline-end divider separates navigation from the article;
- the shell continues to reserve the accepted 256px expanded width.

The rail remains a three-row layout:

1. fixed 48px header;
2. `minmax(0, 1fr)` central navigation;
3. fixed 48px footer.

Only the central navigation owns `overflow-y: auto`. It contains the course
actions, filter, and tree. The outer aside clips layout overflow and must not
become a second vertical scroller. The article keeps normal document scrolling.
Desktop may use sticky positioning inside the reserving shell and intermediate
tablet geometry may use the existing fixed-edge implementation; both must keep
the rail aligned to the viewport's top and bottom during document scroll.

Phone presentation remains the existing full-height modal drawer with safe-area
handling, scroll lock, focus trap/restore, inert background, overlay, and Close
control. This correction must not copy FDD/IA's incomplete mobile behavior.

## Markup And Runtime Boundaries

### Builder

The builder owns recursive tree structure and initial static state. It emits:

- branch-only disclosure buttons;
- a separate number element when structural numbering exists;
- a separate title link;
- child groups with stable IDs and semantic grouping;
- the current path expanded in initial HTML so static/no-script reading retains
  orientation.

The builder must not infer new hierarchy or progress. It consumes only current
generated navigation data.

### Shell

The shell owns volatile and session-scoped display behavior. A centralized user
branch transition applies:

- direct node expansion or collapse;
- same-parent/same-depth accordion collapse;
- current-path protection and explicit-current-path exceptions;
- storage writes only for direct non-temporary preferences;
- identical pointer and keyboard results.

Filter matches may temporarily open ancestors. Clearing the filter restores
the stored accordion state, exposes the current path when no explicit page-local
collapse prevents it, and does not rewrite preferences. Invalid or unavailable
session storage is ignored without disabling disclosure behavior.

The accepted storage key remains
`raya:course-map-branches:v1:<course_id>` in `sessionStorage`. Filter text,
focus, scroll position, drawer state, current page, and active path are not
stored.

### Renderer CSS

Renderer CSS owns viewport geometry, the single scroll owner, disclosure and
number columns, chevron rotation, guide lines, row density, long-label flow,
and active states. Breakpoint rules must not change semantic DOM or interaction
ownership.

## Failure And Fallback Behavior

- Nodes without children remain ordinary links even when JavaScript fails.
- Branch children on the current path are visible in initial HTML.
- A missing child container makes its disclosure inert without affecting the
  title link; generated contracts should prevent this mismatch.
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
- structural numbering with multi-digit values;
- enough content to overflow the central navigation.

Chromium checks at 1440px and a representative tablet width must verify:

1. the rail touches viewport top and bottom before and after article scroll;
2. header/footer remain fixed while only central navigation scrolls;
3. disclosure hit testing targets the button, not the link or blank row;
4. branch labels navigate and leaves expose no disclosure semantics;
5. pointer and keyboard expansion change `aria-expanded`, `hidden`, and
   `aria-hidden` consistently;
6. expanding a branch collapses eligible same-level siblings;
7. the current path is not collapsed as an accordion side effect;
8. direct current-ancestor collapse survives unrelated interaction during the
   page lifetime and load-time exposure does not overwrite stored preference;
9. filter expansion/restoration preserves accordion and current-path rules;
10. every expanded hierarchy level has a visible vertical guide;
11. plain numbers, titles, chevrons, and current markers never overlap;
12. long labels remain inside the rail without horizontal overflow;
13. fine targets are at least 30px and coarse targets at least 44px;
14. the same DOM remains functional in the phone drawer without modal,
    overflow, or safe-area regressions.

Adversarial Chromium reviewers must compare the completed desktop/tablet tree
against both FDD and IA reference screenshots and independently exercise every
visible disclosure. The comparison should confirm the selected option A model,
not merely static visual similarity.

## Acceptance Criteria

The correction is complete when a reader can immediately distinguish branches
from leaves, expand a branch by its chevron, navigate by its title, understand
hierarchy from the reference-style vertical guides, and use the full rail from
viewport top to bottom without clipped navigation or nested scroll confusion.
The current path remains oriented unless the reader directly collapses it, and
all pointer, keyboard, storage, filter, static, tablet, and phone contracts stay
coherent.
