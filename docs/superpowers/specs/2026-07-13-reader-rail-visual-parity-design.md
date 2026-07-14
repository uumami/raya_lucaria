# Reader Rail Visual Parity Design

Date: 2026-07-13

## Status And Authority

This Superpowers design restores collapsed behavior already required by
`docs/foundation/20_learning_renderer_contract.md` and adds two user-approved
visual decisions: the expanded left and right rails use equal outer widths,
and the left header mirrors the right header with an explicit `Hide map`
action. The foundation contract remains authoritative, so implementation must
update its left-rail command sentence before changing package behavior.

The contract requires the expanded course map to remain usable, the collapsed
course-map column to return its space to the article, and only a minimal edge
opener to remain. Hidden map content must be inert, removed from keyboard
navigation, and hidden from assistive navigation. The phone course map remains
a modal drawer.

This design supersedes the statement in
`2026-07-08-reader-rail-rebuild-design.md` that the right rail remains narrower.
It also supersedes that design's compact course-title rail header: the
structural rail header is the stable region label `Course map`, while the
authored course title remains available through the page title, course home,
and reader navigation. It preserves the rebuild's remaining information
architecture and article-primary rule.
It also supersedes the single-row, seven-command layout in
`2026-07-08-course-map-tiny-tray-design.md`: seven `32px` targets plus required
gaps and padding cannot fit inside the newly equal medium rail without either
overflowing or taking space needed by the article. The structural map instead
uses the full eight-command, two-column body described below. No other earlier
rail decision is superseded.

## Context

The production reader can render the left course rail in an invalid hybrid
state. Its outer panel becomes a narrow collapsed strip while expanded search,
command, and map content remains visible. Labels then wrap one character at a
time, controls overflow across the article, and the article does not receive a
coherent left boundary. The expanded state can also clip tree labels and make
commands visually inconsistent with the right learning rail.

The right learning rail is the accepted visual reference. Its expanded panel
has a clear header and explicit hide action, its content wraps normally inside
the panel, and its collapsed state removes the full panel in favor of one
small edge opener. The left course rail should use that same state model and
outer visual grammar while retaining its own map-specific content.

## Goal

Make the left course rail a left-side counterpart of the right learning rail:

- matching expanded width, panel treatment, header geometry, and hide control;
- matching collapsed edge-opener size, placement, surface, and shadow;
- matching column reclamation and transition behavior;
- no expanded content inside collapsed geometry under any initialization or
  script-failure condition; and
- no change to the distinct information each rail owns.

## Selected Design

Use shared mirrored rail geometry and state styling. Keep separate semantic
markup and body styles for the course map and learning context because their
contents and interactions differ. Do not copy the right rail into another
independent left-only CSS implementation, and do not refactor both bodies into
one renderer component.

### Expanded Rails

At structural reader widths where the rail controls are available, the outer
course-map and learning-context panels use the same computed width within one
CSS pixel, border, surface, radius, shadow, viewport relationship, and header
alignment. At `1280px` and wider, both grid tracks are `15rem`. At `894px`
through `1279px`, both fixed edge panels are `15rem`. At `640px` through
`893px`, the one permitted expanded fixed edge panel is `15.75rem`.

The left header visibly presents:

- `Course map`; and
- an explicit `Hide map` action in the same position and treatment as the
  right header's `Hide context` action.

At every structural width from `640px` upward, the map body uses one content and
focus order: course search; compact two-per-row icon-and-label command tiles for
Search, Graph, Practice, Tasks, Schedule, Context, Text size, and
OpenDyslexic; structural page position; map filter; and course tree. The
header's `Hide map` action is the visible Map command. Together these remain
the same nine foundation actions; their behavior and destinations do not
change. Stable two-column tracks replace the incompatible single-row medium
tray and prevent labels from collapsing into vertical text.

Map-specific controls use stable tracks and normal word wrapping. No label may
be squeezed into vertical character-by-character text, overlap the article, or
escape the panel. Long course-tree labels wrap within their row without
obscuring generated numbers or disclosure controls.

The right rail keeps its existing learning-context contents and behavior. This
change uses it as the visual reference rather than redesigning it.

### Collapsed Rails

At `1280px` and wider, collapsing the left rail removes the course-map track
from the reader grid so the article reclaims the space. At `640px` through
`1279px`, collapsing it removes the fixed panel and its reserved shell padding.
In both structural geometries the map header collapse action, body, search,
commands, filter, tree, and drawer-only chrome are absent from layout.

The visible remainder is one dedicated fixed left-edge opener that mirrors the
collapsed right-side Context opener in dimensions, vertical placement,
surface, border, shadow, focus treatment, and motion. Its accessible name is
`Expand course map`; its visible treatment follows the matching right opener
rather than becoming a miniature navigation rail.

The two rail openers remain separate controls and operate only their
corresponding rail. Expanding the map restores the full course rail and the
prior course-local branch state.

The generated `#raya-course-map` outer region owns three explicit children: a
header with the expanded `Hide map` control, a `.raya-course-map-body` wrapper,
and a collapsed `.raya-course-map-expand` opener. The body wrapper contains all
search, command, position, filter, tree, and drawer-only content and is the
unit that becomes hidden and inert. The edge opener is a separate sibling, is
never inside the inert body, and is visible only in collapsed structural state.
Both controls use the existing `data-raya-course-map-toggle` state path; they
are not one element repositioned between unrelated layouts. The right rail
keeps the corresponding existing collapse-control/body/expand-control shape.

### Shared Styling Boundary

Shared rail-shell rules own:

- expanded outer width and panel appearance;
- header layout and explicit hide-control geometry;
- collapsed fixed positioning and opener geometry;
- reader-grid track removal and article space reclamation;
- reduced-motion-aware state transitions; and
- shared visible focus treatment.

Course-map rules continue to own search, command tiles, filtering, hierarchy,
branch disclosure, and map scrolling. Learning-rail rules continue to own
reading flow, page context, connections, and section orientation. Shared rules
must not depend on the internal height or content of either body.

## State And Interaction

The existing state contract remains authoritative:

- `data-raya-course-map="expanded|collapsed"` controls the effective left-rail
  state;
- `data-raya-learning-rail="expanded|collapsed"` controls the effective
  right-rail state;
- the versioned course-scoped `sessionStorage` record restores explicit
  structural rail choices; and
- phone drawers, filters, focus, and scroll position remain non-persistent.

The deferred shell continues to synchronize `aria-expanded`, `aria-hidden`,
`inert`, and descendant tab order. `Hide map`, the left edge opener, Escape,
responsive reconciliation, and restored session state all converge through
the existing course-map state path rather than applying independent visual
classes. At `640px` through `893px`, explicitly opening one rail must collapse
the other rail and write the coordinated resulting pair once, as required by
the accepted session-persistence contract.

CSS must enforce the collapsed body boundary from the effective root state
alone. If prepaint has applied a collapsed state while the deferred shell is
delayed, unavailable, stale, or stopped by an exception, the body has
`display: none`, so expanded controls are neither rendered nor keyboard
reachable. Once the deferred shell is ready, it additionally synchronizes the
body's `aria-hidden`, `inert`, and descendant tabindex state. CSS is not
expected to create DOM accessibility attributes, and a failed shell leaves the
static article readable even though rail controls cannot be enhanced.

## Responsive Behavior

At `1280px` and wider, expanded rails occupy equal `15rem` grid tracks with the
article between them. Collapsing a rail removes its track. With both rails
expanded at `1280px`, the article content box remains at least `42rem` wide.

At `894px` through `1279px`, expanded rails are fixed `15rem` edge panels and
the shell reserves the corresponding side padding so neither panel intersects
the article. Valid stored left and right states apply directly and both rails
may be expanded. With both expanded at `894px`, the article content box remains
at least `23.75rem` wide.

At `640px` through `893px`, the existing article-first structural overlay rule
continues to permit at most one expanded `15.75rem` fixed edge panel. The left
and right panels use matching overlay geometry and matching collapsed edge
controls. Explicitly opening one collapses the other before expansion and
writes the coordinated pair once. A saved both-expanded pair becomes
effectively both-collapsed without a write until the next explicit rail action,
as already defined by the persistence design.

Below `640px`, the course map remains a modal drawer and the right learning
context remains available under the existing phone contract. Desktop hide
actions and structural edge openers are not shown. Crossing a breakpoint must
not leave stale fixed positioning, hidden reachable content, or an edge opener
over the phone article.

## Accessibility And Failure Behavior

- Expanded headers expose clear region names and explicit hide actions.
- A collapsed map body is `aria-hidden`, inert, untabbable, and absent from
  visual layout.
- The visible left opener remains keyboard reachable with an accurate
  accessible name, visible focus, and `aria-expanded="false"`.
- Clicking `Hide map` or pressing Escape while focus is within the expanded
  structural map collapses it and focuses the left edge opener.
- Clicking `Hide context` or pressing Escape while focus is within expanded
  learning context collapses it and focuses the right edge opener.
- When responsive reconciliation hides focused map content, focus moves to the
  structural left edge opener, the phone Map launcher, or the article, in that
  preference order according to which target is visible. The right rail uses
  its structural edge opener and otherwise the article.
- Storage read or write failures leave both rails operable and do not expose a
  hybrid collapsed/expanded state.
- Reduced-motion preferences suppress coordinated rail movement without
  changing final geometry or accessibility state.

## Implementation Boundary

Expected implementation surfaces are intentionally narrow:

- `docs/foundation/20_learning_renderer_contract.md`
  - define the structural left header's Map hide action followed by search and
    the eight two-per-row body commands, replacing the incompatible wording
    that describes all nine actions as body tiles;
- `docs/guides/en/students/index.md` and
  `docs/guides/es/estudiantes/index.md`
  - describe the visible Map header action and exact structural body-command
    order in student-facing language;
- `docs/guides/en/agents/index.md` and `docs/guides/es/agentes/index.md`
  - align renderer verification guidance with the header action, body wrapper,
    eight-command body, and collapsed opener ownership;
- `packages/static/src/raya_static/builder.py`
  - expose the visible `Hide map` header action, dedicated map-body wrapper,
    and separate collapsed opener using existing map-toggle semantics;
- `packages/static/src/raya_static/rendering.py`
  - consolidate shared outer rail, header, collapsed opener, and grid-reclaim
    rules;
  - keep body-specific course-map and learning-context rules separate;
  - remove or override conflicting left-only collapsed rules that permit the
    hybrid state; and
- `packages/static/src/raya_static/shell.py`
  - change only if required to keep labels, focus ownership, or state
    synchronization consistent with the shared controls.
- `tests/contracts/test_documentation_surfaces.py`,
  `tests/contracts/test_static_builder.py`, and
  `tests/e2e/test_preview_static_read_path.py`
  - update affected truth-surface assertions and add the specified structural,
    browser-geometry, failure-state, responsive, and accessibility coverage.

Stable public selectors and state attributes remain in place. No source course
schema, artifact payload, discovery workspace, graph, practice, tasks,
schedule, or storage format changes are part of this design.

## Verification

Test-driven implementation will first add a browser reproduction that fails on
the current hybrid state. Verification covers:

- expanded desktop left and right panels have matching outer widths and header
  geometry within one CSS pixel;
- `Course map` / `Hide map` mirrors `Learning context` / `Hide context`;
- expanded map commands and tree labels remain inside the panel, use normal
  horizontal writing, and cause no horizontal page overflow;
- every structural width renders exactly the eight body commands in the
  specified order after course search, while `Hide map` provides the ninth Map
  action in the header;
- the English and Spanish student and agent guides state the same header/body
  command boundary as foundation and generated markup;
- collapsing the map gives its grid track to the article and leaves only one
  visible left edge opener;
- the collapsed map body has zero layout area, is inert, is `aria-hidden`, and
  has no tabbable descendants;
- before shell readiness, a prepaint-collapsed map body is `display: none` and
  unreachable; after readiness, the same body also has synchronized
  `aria-hidden`, `inert`, and descendant tabindex state;
- the left and right collapsed openers match in dimensions and corresponding
  edge placement without intersecting article content;
- valid saved collapsed state is correct before and after deferred shell
  readiness;
- delayed or failed shell initialization cannot expose expanded map content in
  collapsed geometry;
- `639/640`, `893/894`, and `1279/1280` transitions do not overlap the article,
  lose focus, retain stale inertness, or show structural openers on phones;
- at `640px` through `893px`, opening one rail collapses the other and writes
  exactly one coordinated stored pair;
- the explicit and responsive focus paths land on the deterministic targets
  defined above;
- at `894px`, both expanded fixed panels leave at least a `23.75rem` article
  content box, and at `1280px` both expanded grid rails leave at least `42rem`;
- long fixture labels, the largest text-size setting, OpenDyslexic, and every
  supported reader skin preserve horizontal writing, panel containment, and
  the minimum article widths at `894px`, `1279px`, and `1280px`;
- `prefers-reduced-motion: reduce` reaches the same final geometry without an
  active rail transition or focus delay; and
- the phone course-map drawer retains backdrop, focus containment, Escape,
  background inertness, and close behavior.

Chromium screenshots at representative desktop, medium, and phone widths are
required alongside geometry and accessibility assertions. Final validation
uses the focused browser tests, `./scripts/check-render-debug.sh`,
`./scripts/check.sh`, `./scripts/smoke-test.sh`, and
`./scripts/check-docker.sh` sequentially.

## Non-Goals

- No new command behavior, destination, or command set; only command placement
  changes.
- No redesign of the accepted right learning rail body.
- No new breakpoint, transition duration, or state value.
- No new browser-storage key or persistence scope.
- No phone learning-context drawer.
- No discovery-workspace or course-source changes.
- No migration to a new frontend framework or external UI dependency.
