# Reader Rail Density — Design

Date: 2026-07-29
Status: proposed (revision 2 — rewritten after four adversarial reviews)
Scope: `packages/static` rendering and markup. Left course rail and right learning rail, at
structural reader widths only.

Revision 2 note: revision 1 asserted four things about shipped code that measurement
disproved, proposed a change that broke the invariant it claimed to protect, and set
verification gates that were tautological or unmeasurable. Those errors and their
corrections are recorded in "Corrections to revision 1" so the same ground is not
re-argued.

## Problem

Measured in Chrome against the deployed site
(`uumami.wiki/raya_lucaria/foundation/system-model/index.html`), 1440x900 unless noted.

### P1 — 41% of the rail swallows the scroll wheel

`rendering.py:4003-4010` gives `.raya-course-map` both `overflow: auto` and
`overscroll-behavior: contain`, while its `scrollHeight` equals its `clientHeight`.
Chrome still treats it as a scroll container, and `contain` blocks scroll chaining, so a
wheel event over the frame is captured and discarded.

Measured, wheel with the cursor over each region:

| Region | Height | Before | After removing `overscroll-behavior` from the frame |
| --- | --- | --- | --- |
| `.raya-course-map-header` | 63.0px | **dead** | page scrolls |
| `.raya-course-rail-tools` | 252.8px | **dead** | page scrolls |
| `.raya-course-map-filter` | 36.0px | **dead** | page scrolls |
| `.raya-course-map-list` | 385.4px | index scrolls | index scrolls |

351.8px of the 868px rail — **41%** — is dead to the wheel. This is the reported bug:
the pointer is over the rail, and nothing moves.

### P2 — 444.6px of fixed chrome above the index

| Block | Height |
| --- | --- |
| `.raya-course-map-header` | 63.0px |
| `.raya-course-rail-tools` (search form + eight command tiles) | 252.8px |
| `.raya-page-position` (`Page N of M`, incl. 32px margins) | 57.6px |
| `.raya-course-map-filter-label` | 24.8px |
| `.raya-course-map-filter` | 46.4px |
| **Fixed chrome total** | **444.6px** |
| `.raya-course-map-list` (the index) | 385.4px |

The index needs 2027px for the 23 currently expanded entries and receives 385.4px, so
the reader sees 4 of 33 pages. The chrome height is constant, so the index share falls
with viewport height: 385.4px at 900, 205.4px at 720, and the shipped `12rem` floor
(192px) from 600 down.

### P3 — the label column is 103.2px wide

Of the rail's 240px: 32px panel padding, a **15px reserved scrollbar gutter**, then per
nesting level **22.6px** (`padding-left: 10.4px` + `margin-left: 11.2px` + 1px guide
border), then a **42px** sequence badge (`min-width: 23.2px` + `margin-right: 7.2px` +
`5.6px` padding each side).

All 23 entries wrap. The worst render 5 line boxes. Average row height is 88.1px. Long
words break mid-word ("Security And Registratio / n") because the 103.2px column is
narrower than a single long word at the shipped 15px font, which triggers the anchor's
emergency `overflow-wrap: break-word`.

### P4 — the right rail ships 1358px of panels in a 767px window

| Panel | Builder call site | Height |
| --- | --- | --- |
| `raya-page-contents` ("On this page") | `builder.py:2765` | 419.3px |
| `raya-page-reading-flow` ("Reading flow") | `builder.py:2938` | 224.6px |
| `raya-page-context` ("Page context") | `builder.py:2882` | 473.2px |
| `raya-page-linked-pages` ("Connections") | `builder.py:2968` | 241.2px |
| **Total** | | **1358.3px** |

All four pass `expanded=True`. "On this page" is the only panel with live reading-position
tracking (`shell.py:1782-1828` writes `aria-current="location"` and an `aria-live` current
-section link), and it is displaced by three panels the reader consults rarely.

The right rail also has a nested scroller: `.raya-learning-rail` declares
`overflow: auto` (`rendering.py:4027`) and `.raya-learning-rail-body` declares it again
(`rendering.py:6721`).

## What is NOT the problem

Recorded so implementation does not "fix" working code.

1. **The index is already a correctly growing flex item.** Inside
   `@media (min-width: __RAYA_STRUCTURAL_PX__px)`, `rendering.py:6696-6699` makes
   `.raya-course-map` a flex column, `:6725-6728` gives `.raya-course-map-body`
   `flex: 1 1 auto; min-height: 0`, and `:6729-6739` gives `.raya-course-map-list`
   `flex: 1 1 auto; min-height: 12rem`. The comment at `:6731-6738` documents the
   squeeze-to-5px bug this already fixed, and names the frame's `overflow: auto` as the
   deliberate relief valve. **That floor and that valve are kept.**
   `tests/e2e/test_rail_collapse_contract.py:648` ratifies a >= 160px floor.
2. **The 0px index at 200% zoom is a different bug, and is out of scope.** 200% zoom of
   1440x900 is a 720x450 CSS viewport, which lands in the 640-893 medium band where
   `shell_geometry.py:54-63` collapses **both** rails by design and
   `rendering.py:6774-6778` sets `display: none` on the collapsed body. No `min-height`
   can act through `display: none`. The 44x40 chip expands on click, so nothing is
   unreachable. Owner decision on 2026-07-29: out of scope here, tracked separately.
3. **`overflow-wrap` must stay `break-word` on the anchor.** `anywhere` is on the list
   container; the anchor is `break-word` (`rendering.py:5121`), and
   `tests/e2e/test_preview_static_read_path.py:17554` pins it because it is what keeps a
   55-character unbroken identifier inside the 240px rail. Mid-word breaking is a
   *symptom* of the 103.2px column, not of this property.
4. **The right rail's collapse mechanism already exists and is contract-compliant.**
   `builder.py:2334-2375` emits `<section data-raya-rail-panel-state>` with
   `<h2><button data-raya-rail-toggle aria-expanded>` and `inert` + `aria-hidden` on
   collapsed bodies, driven by `shell.py:1134-1152`, animated at `rendering.py:4421-4456`
   with a reduced-motion opt-out. Its default is `expanded=False`. **No new markup.**
5. **Collapsing those three panels hides zero unique navigation paths.** Verified:
   reading flow's prev/next are duplicated by `raya-article-sequence-top`
   (`builder.py:3798-3805`), `raya-article-sequence-cards` (`:3808-3851`), the Page brief
   learning path (`:3613-3615`), and ArrowLeft/Right (`shell.py:1164-1172`); page
   context's only links are prerequisites, duplicated by the Page brief; connections'
   outgoing links and backlinks are duplicated by `.raya-article-connections`
   (`:3014-3063`) through the same renderer and the same emptiness guard.
6. **`data-raya-command-tooltip` renders nothing.** No CSS or JS reads it, and only the
   five `_render_compact_command_link` controls carry it at all. It cannot be relied on
   as a name-recovery mechanism. This is why command labels stay visible (Decision 2).

## Decisions

1. **Rail width stays 240px.** Owner decision. No article width is given up.
2. **Command labels stay visible.** Tiles go four-per-row with the label as a caption
   under the glyph. Icon-only was rejected: the tooltip attribute is inert, three of the
   eight controls never had it, and
   `tests/e2e/test_preview_static_read_path.py:9874`
   (`test_reader_comfort_labels_are_visible_on_desktop_only`) encodes visible desktop
   labels as a deliberate prior decision that this work will not silently reverse.
3. **The inline course-search form stays.** It is mandated twice by the contract and is
   functionally unique: `search.py:355` reads `?q=` and `:442` prefills the workspace, so
   the form is a type-and-go query handoff that the Search command control cannot
   replicate.
4. **The frame keeps `overflow: auto` and the index keeps `min-height: 12rem`.** No new
   `@media` rules are introduced, so no new geometry literal is added and the
   single-source geometry invariant (`20_learning_renderer_contract.md:232-237`) is not
   engaged.
5. **`scrollbar-gutter: stable` is dropped from BOTH rail frames**, symmetrically, and
   retained on the inner scrollers. This is the only horizontal change that needs no
   trade-off: +15px of content width per rail inside the locked 240px.
6. **The sequence badge shows on the current row only, always** — never on hover.
7. **The right rail keeps its existing disclosure mechanism**; three `expanded` flags flip.
8. **200% zoom / medium-band collapse is out of scope** (see "What is NOT the problem").

## Design

Every CSS change below lands inside the existing
`@media (min-width: __RAYA_STRUCTURAL_PX__px)` band alongside `rendering.py:6693-6760`,
except the two base-rule deletions in D1 and D5. The sub-640 drawer re-declares
`overflow`, `overscroll-behavior`, and `scrollbar-gutter` inside an `all: revert` block
(`rendering.py:6250-6270`), so base-layer deletions cannot leak into it. The drawer
deliberately uses the inverse architecture — frame scrolls, list capped by
`max-height: min(18rem, calc(100vh - 8rem))` (`:6344`) — and is **not** changed.

### D1 — free the wheel (fixes P1)

Delete `overscroll-behavior: contain` from `.raya-course-map` (`rendering.py:4008`).
Keep `overflow: auto` there. Keep `overscroll-behavior: contain` on
`.raya-course-map-list` (`:4207`) so index scrolling still does not chain into the page.

Verified: the four rail regions go from `dead / dead / dead / index` to
`page / page / page / index`.

### D2 — cut the chrome (fixes P2)

- `.raya-course-rail-command-list`: `grid-template-columns: repeat(2, minmax(0, 1fr))`
  becomes `repeat(4, minmax(0, 1fr))`. Eight controls render two rows of four.
- `.raya-course-rail-command`: keep the existing desktop `flex-direction: column;
  justify-content: center; text-align: center` (`rendering.py:6747-6756`). Set
  `min-height: 3.25rem` and caption `font-size: 0.625rem`; raise `.raya-command-icon`
  from `0.9375rem` to `1.25rem` so the glyph reads at four-up width.
  **Do not set `aspect-ratio: 1`** — with `repeat(4, minmax(0,1fr))` in a full-bleed
  238px track that yields 52-56px squares, not the intended tile.
- Per-command text colours collapse to one resting colour. The eight hues encode nothing;
  active state is carried by `[aria-current="page"]` / `[aria-pressed="true"]` background
  and border (`rendering.py:4247-4251`) plus the `aria-pressed` attribute and a live
  `aria-label`. Contrast was checked on the current hues (Search 5.18:1, Practice 5.11:1,
  Tasks 4.84:1) — flattening is neutral-to-positive, not a contrast fix.
- Fold in an adjacent defect: `accessibility.py:81-94` gives `.raya-font-toggle` the same
  `accent-soft` background that means `[aria-pressed="true"]` on its siblings, and wins on
  source order, so OpenDyslexic renders a permanently false "on" fill. Scope that
  background to the top-bar variant so `[aria-pressed]` is the only thing driving tile fill.
- `.raya-page-position` is removed from the rail body (`builder.py:2203`). Safe: the rail
  emitter and the Page brief `Position` fact (`builder.py:3610-3612`) are gated on the
  identical `_page_position()` predicate (`:1887-1891`), so whenever the rail would have
  shown it the brief does. The phone drawer keeps its own independent readout
  (`builder.py:2189`), which is **not** removed.
- `.raya-course-map-filter-label` stays visible; `font-size` 0.78rem -> 0.72rem and
  `margin-bottom` 0.3rem -> 0.15rem.
- `.raya-course-map-filter`: `min-height` 2.25rem -> 1.75rem, `margin-bottom` 0.65rem
  -> 0.25rem. The filter is **never hidden**. Revision 1 proposed hiding it at short
  heights on the false premise that it stays keyboard-reachable; there is no `/` hotkey
  and no `mapFilter.focus()` anywhere in `shell.py`, so hiding it removes the only route
  to filtering a 33-page map, failing WCAG 1.4.4 and 1.4.10.
- `.raya-course-rail-search .raya-command-search-input, ... -submit`: `min-height`
  2.25rem -> 2rem.

### D3 — widen the label column (fixes P3)

- `scrollbar-gutter: stable` is deleted from `.raya-course-map` (`rendering.py:4009`,
  `:6699`) and `.raya-learning-rail` (`:4029`), and retained on
  `.raya-course-map-list` (`:4209`) and `.raya-learning-rail-body`. Both rail content
  boxes go 191px -> 206px. Trade-off, accepted: in the rare degenerate state where the
  frame itself scrolls, its scrollbar now shifts content by 15px.
- Indentation: `.raya-course-map-list ol, ... ul` get `padding-left: 0;
  margin-left: 7px`, keeping the 1px guide border. Per level 22.6px -> 8px.
- Sequence badge: `.raya-course-map-list a::before` becomes `display: none` at rest.
  The current row only gets it back, always visible and out of flow:
  `[aria-current="page"]` gains `position: relative; padding-left: 1.625rem` and its
  `::before` becomes `position: absolute; left: 0`. One row of 33 pays 26px.
  No hover reveal: revision 1's hover variant grew rows 25px -> 48px, shifted every row
  below the cursor, pushed the label past its own clamp, failed WCAG 1.4.13 Dismissible,
  and was unreachable on touch. The badge is also **not** redundant with the label — it is
  the flat reading-order ordinal (`builder.py:2012-2014`), while the label prefix is the
  hierarchical address.
- `font-size: 0.8125rem; line-height: 1.3`, applied in both the >= 894 path and the
  640-893 band, whose `0.9375rem` override at `rendering.py:6571` must change too so the
  density fix is not silently desktop-only.
- Two-line clamp: `display: -webkit-box; -webkit-line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden`, released on interaction and on the
  current row: `a:hover, a:focus-visible, a[aria-current="page"] { -webkit-line-clamp:
  unset }`. This replaces revision 1's `title` attribute on all 33 links — `title` is not
  exposed to touch, is unreliable for keyboard-only users, and adds a redundant
  description announcement. The accessible name is unaffected either way:
  `-webkit-line-clamp` is a visual clip, the text nodes remain, so name-from-content
  yields the full string and WCAG 2.5.3 Label in Name holds.
- `overflow-wrap: break-word` is **kept** on the anchor. `hyphens` is left at its
  computed `manual` and `word-break` at its computed `normal`; neither is set.

### D4 — right rail (fixes P4)

- `expanded=True` becomes `expanded=False` at `builder.py:2882` (Page context), `:2938`
  (Reading flow), and `:2968` (Connections). `builder.py:2765` ("On this page") stays
  expanded — it owns the live reading-position region.
- `.raya-learning-rail` loses `overflow: auto` (`rendering.py:4027`) and becomes a flex
  column, leaving `.raya-learning-rail-body` (`:6721`) as the rail's single scroller.
- `rendering.py:4159-4163` re-declares `display: grid` on `.raya-learning-rail-body`
  during the 240ms expand transition; it becomes `flex` so settled and mid-transition
  layout modes cannot diverge.
- Nothing else. The body stays the scroller, so no panel needs `flex: 1 1 auto`, which
  avoids both the scroll-away-heading problem and the no-`raya-page-contents` case where
  no child would have carried the grow factor.
- Collapsed panels gain `content-visibility: hidden` on the collapsed body so
  find-in-page cannot scroll to invisible text — a pre-existing gap, since the shipped
  `0fr` + `opacity: 0` collapse (`rendering.py:4452-4456`) sets no `overflow: hidden`.

Three closed panels are 32px toggle + 0.75rem padding each way, about 56px apiece, so
panel content drops from 1358.3px to roughly 590px and fits the 767px window without
scrolling.

### Projected outcome

Chrome 444.6px -> about 275px. Index 385.4px -> about 555px on the deployed 33-page tree,
roughly 13 pages visible instead of 4. Label column 103.2px -> about 150px. These are
projections from component measurements and are gated empirically, not assumed.

## Contract amendment

`docs/foundation/20_learning_renderer_contract.md`. Smaller than revision 1's, because
labels, the search form, the page-position-in-brief claim, and the frame's `overflow` all
stay.

1. `:25` and `:33` — "rendered two per row" becomes "rendered four per row". "exactly
   eight", "icon-labeled", and the enumerated command identities are unchanged.
2. `:25` — delete "structural page position," from "followed by structural page position,
   the locally filterable hierarchical map". `:33` uses semicolons and needs its own edit:
   delete "structural page position;". Revision 1 quoted only the `:25` phrasing and would
   have left the table row still mandating it.
3. `:27` — state that at structural reader widths the right learning rail may render its
   non-contents panels collapsed by default through the existing inert disclosure
   mechanism, explicitly scoped so it does not conflict with the phone-parity sentence
   ("Phone layouts keep the rail body visually and accessibly available…").
4. `:35` — state that reading flow and page context may render collapsed by default, using
   the contract's own noun for the open panel ("current article section and page
   contents").
5. `## Verification` — add: each rail owns exactly one scrolling region under normal
   reader heights; a wheel gesture anywhere over a rail either scrolls that rail's single
   scroller or the page, never nothing; rail header parity covers width, height, top, and
   both insets; map labels clamp to at most two lines and release on interaction.

Not amended, and why: the "course search" clause stays satisfied (Decision 3); the "ten
reader actions" sentence is untouched and correct — the contract counts the header Map
action, the header course-home action, and eight body commands, and the search form is
not one of them; no new geometry literal is introduced (Decision 4), so
`:232-237` is not engaged; the `:210` no-hover-first-movement non-goal is satisfied by
Decision 6.

## Files to change

Named explicitly per `docs/foundation/13_truth_surfaces.md:23`,
`docs/foundation/16_documentation_surfaces.md:24`, and `AGENTS.md:7`.

**Implementation**
- `packages/static/src/raya_static/rendering.py` — D1, D2, D3, D4 CSS.
- `packages/static/src/raya_static/builder.py` — remove rail `.raya-page-position`
  (`:2203`); flip `expanded` at `:2882`, `:2938`, `:2968`.
- `packages/static/src/raya_static/accessibility.py:81-94` — scope the
  `.raya-font-toggle` background.

**Foundation** — `docs/foundation/20_learning_renderer_contract.md` at `:25`, `:27`,
`:33`, `:35`, and `## Verification`.

**Role documentation** — English and Spanish stay separate; control names, class names,
and paths stay in English. Only the two-per-row wording and the rail page position change;
the search-form mentions stay correct.
- `docs/guides/en/students/index.md:51`, `:74`
- `docs/guides/es/estudiantes/index.md:52`, `:75`
- `docs/guides/en/agents/index.md:144`, `:166`
- `docs/guides/es/agentes/index.md:155`, `:178-179`

No change needed, stated per `16_documentation_surfaces.md:24`:
`docs/guides/{en/professors,es/profesores,en/contributors,es/colaboradores}` — their
page-position mentions are Page-brief scoped. `docs/guides/en/students/index.md:94` and
`docs/guides/es/estudiantes/index.md:97` describe the drawer's own position readout, which
is retained.

**Contract-text gates that pin the sentences being amended**
- `tests/contracts/test_static_builder.py:4909` — pins the literal "course search, then
  exactly eight compact icon-labeled command tiles rendered two per row".
- `tests/contracts/test_documentation_surfaces.py:378-403` — binds the contract to exactly
  four role guides.

**Test assertions requiring update.** Roughly fifty sites, enumerated by category in the
plan with a one-line justification each. Categories, with the ones that **error** rather
than fail cleanly marked:
- Rail page position: `test_preview_static_read_path.py:12785`, `:19195-19199`,
  **`:19297` (unguarded `getBoundingClientRect` inside `page.evaluate` — the whole
  evaluate throws)**, `:19422-19428`; **`test_static_builder.py:5208-5213` (`.index()` ->
  ValueError)**, `:5680`.
- Command grid 2 -> 4 columns: `:10734-10735`, `:10761-10768`, `:11055-11057`, `:11559`,
  `:11738`, `:17888`, `:19207`, `:19467-19469`, `:21704-21708`, `:21060`;
  `test_static_builder.py:5950` (**already tautological** — the literal
  `grid-template-columns: repeat(2, minmax(0, 1fr))` also occurs at `rendering.py:1139`,
  `1144`, `3475`, `4470`, so it must be scoped inside the
  `.raya-course-rail-command-list {` block, not merely retargeted to `repeat(4`).
- Index rows: `:11060-11063`, `:19698-19701` (drop the `badgeClearance` derivation),
  `:19693-19695` (its "labels wrap" premise is removed by design), `:18906`
  (`linkFontSize == "15px"` in the 640-893 band).
- Right rail panels: `:14165`, `:14197-14203`, `:14228-14232`, `:14727-14733`,
  `:14768-14776`, `:14823-14826`, `:15120-15131`, `:15133-15135`, `:20069-20070`,
  `:20272-20301`, `:19889`; `test_static_builder.py:5155`, `:5162`, `:5361-5382`,
  `:5406-5414`, `:5505-5512`, `:5851-5886`. Note `test_static_builder.py:5506` is
  **already tautological** (the emitted class is `raya-page-contents
  raya-page-current-section`, so `raya-page-contents"` never matches).
- Two right-rail tests encode requirements this design appears to invert. Both are
  **re-pointed to the surface that now carries the intent**, which keeps them
  non-tautological. All three panels collapse; no panel is kept open to satisfy a test.
  - `test_render_fixture_reading_flow_panel_is_visible_in_first_viewport` (`:20183`)
    asserts the rail's prev/next are >40x32 in the first viewport. Its intent —
    prev/next reachable without scrolling — is satisfied by
    `_render_article_sequence_nav`, which `builder.py:1052` inserts as the **first child
    of `<article>`, above the breadcrumbs** (confirmed in the rendered page). Re-point the
    assertion at `.raya-article-sequence-top` and keep the >40x32 and first-viewport
    bounds, so it still fails if prev/next ever leaves the first screen.
  - `:15133-15135` asserts rail `innerText` contains reading position plus "previous" and
    "next". Reading position leaves the rail by design (D2) and lives in the Page brief
    `Position` fact (`builder.py:3610-3612`) under the identical predicate. Re-point the
    assertion at the Page brief and the article sequence nav.

**Tautology traps to fix, not inherit.** These pass today while asserting the opposite of
their intent and must be strengthened or deleted, never left green:
`test_preview_static_read_path.py:19210` / `:19442` (`filterLabelVisible is True` still
passes for a 1px clipped `.raya-visually-hidden` box), `:21654-21656` / `:21699`
(`positionVisible is False` on a selector that matches no emitted markup),
`:10738` (`formTop < firstCommandTop` with `formTop` defaulting to 0), `:20515-20526`
(asserting nonexistent elements are invisible), `:17480`, `:17553`.

## Non-goals

- Rail width, article width, and the shared rail-header rule.
- The sub-640 phone drawer's architecture, focus containment, Escape paths, or scroll lock.
- The 640-893 medium-band mutual-exclusion collapse (Decision 8), including its
  `shell_geometry.py` derivation and the byte-identical CSS/JS guarantee at `:36-43`.
- sessionStorage keys, persisted comfort keys, branch-collapse state.
- Generated map label text. Removing the redundant `1.10 ` prefix was considered and
  rejected; it changes generated navigation presentation and needs its own spec.
- Renderer, backend, identity, and study-state work.

## Invariants to protect

`tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_rails_share_outer_geometry`
(`:18341`) asserts the two rails share `top`, `width`, `height`, and both inset symmetries
within 1px at widths 640, 893, 894, 1279, 1280, and 1440, via one shared header rule at
`rendering.py:4074-4084`.

Revision 1 claimed "all changes are inside rail bodies, therefore safe" and proposed
gating only a header-**height** delta. Measurement refuted it: dropping
`scrollbar-gutter` from the map alone makes the headers 206px vs 191px, a 15px width and
inset failure that a height-only gate reports green. Decision 5 drops the gutter from
**both** rails, restoring symmetry, and the gate is the whole
`assert_expanded_header_parity` helper — width, height, top, and both insets.

Header height itself was independently confirmed safe: `min-height` is shared at
`rendering.py:4074-4084` and `:4117-4122`, header content is untouched, and rail width
cannot be widened by a wider tools row because the >= 894 track is a fixed
`var(--raya-map-col)` (`rendering.py:5322`, `:5340-5342`).

## Verification

Chromium via the existing `_browser_executable()` harness. **Every new check must fail
against `main` before it passes** — a red-then-green demonstration is required per check,
and the plan records the failure output. "Full suite green" is not evidence on its own,
because roughly fifty assertions are being edited.

**Fixture.** `examples/courses/render-fixture` has 6 pages; its index measures 217px and
its map never reaches the `max-height` clamp, so no density outcome is measurable on it.
Density checks run against a new large-tree fixture of at least 30 pages nested three
deep. Geometry and behaviour checks that do not depend on tree size stay on the existing
fixture.

1. **Wheel liveness (P1).** With the cursor over the header, the tools row, the filter,
   and the index in turn, assert the wheel moves *something*: the index's `scrollTop`
   strictly increases, or `window.scrollY` strictly increases. Assert no region reports
   "nothing moved". Red against `main` for the first three regions.
2. **One scroller per rail.** Exactly one scrollable ancestor of `.raya-course-map-list`,
   and exactly one of `.raya-page-contents`, at heights 900, 720, and 600 — with a
   positive anchor asserted first (the rail is expanded and the list has rendered at least
   one link), so the check cannot pass on a collapsed or empty rail.
3. **Nothing clipped.** `map.scrollHeight <= map.clientHeight + 1` at heights 900, 720,
   600, 520, and additionally with root `font-size` forced to 24px and 32px — the case
   that killed revision 1's `overflow: hidden`.
4. **Floor unchanged.** `.raya-course-map-list` computed `min-height` is `192px`, and its
   client height is >= 160px at heights 900, 720, 600, 520, keeping
   `test_rail_collapse_contract.py:648` meaningful rather than merely green.
5. **Header parity.** The full `assert_expanded_header_parity` at 640, 893, 894, 1279,
   1280, 1440 — width, height, top, both insets. Plus both rail content boxes measure the
   same width after the gutter change.
6. **Density (large-tree fixture).** Index client height >= 500px at 1440x900, and >= 11
   map links fully within the index viewport. Expressed against measured chrome, not as a
   bare magic number.
7. **Label column.** Deepest visible link's content width >= 140px. Zero links exceed two
   rendered lines, measured as `clientHeight / lineHeight` — not by
   `Range.getClientRects()`, which still reports the pre-clamp line count. At least one
   link in the fixture must exceed two lines unclamped, so the check has something to
   exercise.
8. **Clamp release.** A clamped link reports `scrollHeight > clientHeight` at rest and
   `scrollHeight <= clientHeight + 1` under `:focus-visible`, reachable by keyboard.
9. **Unbreakable token.** The 55-character identifier from `:17489` stays within the rail
   and remains visually truncated with `overflow-wrap: break-word` intact.
10. **Badge.** `::before` computed `display` is `none` on non-current rows and
    `inline-flex` on `[aria-current="page"]`, at rest, with no pointer involved. Hovering a
    non-current row changes neither its own height nor the list `scrollHeight`.
11. **Commands.** Eight controls, four grid columns, each >= 40px on both axes, each with
    a visible label whose `scrollWidth <= clientWidth`, each accessible name identical to
    its pre-change value. `.raya-font-toggle` background matches its siblings while
    `aria-pressed="false"`.
12. **Filter.** The filter input and its label are present, visible, and focusable at
    heights 900, 720, 600, 520, and 480 — no viewport height removes them.
13. **Right rail.** "On this page" open; the other three collapsed with
    `aria-expanded="false"`, `aria-hidden="true"`, `inert`, and no focusable descendants;
    each opens on toggle click; the `<h2>` headings remain in the heading outline;
    `content-visibility: hidden` prevents find-in-page reaching collapsed text.
14. **Drawer unchanged.** At 639px and 390px, assert the drawer's *actual* architecture is
    preserved: the frame scrolls, the list is `max-height`-capped, focus containment,
    Escape, and scroll lock behave as before, and the new flex/indent/font rules have not
    leaked below 640px.
15. **Contract and docs.** `test_static_builder.py:4909` and
    `test_documentation_surfaces.py:378-403` updated and green, with the four role guides
    consistent.
16. Full suite green, then live Chromium verification after deploy, repeating checks 1, 5,
    6, and 13 against the deployed 33-page tree.

## Corrections to revision 1

Kept so the same ground is not re-argued.

| Revision 1 claim | Measurement |
| --- | --- |
| The index is not a growing flex item | False — `rendering.py:6725-6739` already ships `flex: 1 1 auto` and `min-height: 12rem` |
| `min-height: 9rem` is the fix | A regression: 144px against a shipped 192px floor and a ratified 160px gate |
| `overflow: hidden` on the frame | Clips tree content at 24px/32px root font with no scroll path |
| Index is 0px at 200% zoom, and this is the reported bug | It is the medium-band collapse; the body is `display: none`, so no floor applies |
| Changes are body-local, so header parity is safe | Dropping the map's `scrollbar-gutter` breaks header **width** parity by 15px |
| `overflow-wrap: anywhere` causes mid-word breaks | The anchor is `break-word`; it is load-bearing and pinned at `:17554` |
| The right rail is architecturally sound | It has the same nested scroller: `rendering.py:4027` + `:6721` |
| `data-raya-command-tooltip` carries each name | Inert markup; unread, and absent on three of eight controls |
| The badge is redundant with the label prefix | Different facts: reading-order ordinal vs hierarchical address |
| Hover-revealing the badge is acceptable | Grows rows 25px -> 48px, re-clamps the label, fails WCAG 1.4.13 Dismissible, dead on touch |
| The filter stays reachable by typing when hidden | No `/` hotkey and no `mapFilter.focus()` exists; hiding it fails WCAG 1.4.4 and 1.4.10 |
| Native `<details>` for right-rail panels | Re-implements a shipped compliant mechanism and deletes three `<h2>` headings |
| The drawer uses the same three zones | It deliberately uses the inverse: frame scrolls, list `max-height`-capped |
| `title` recovers clamped text | Not exposed on touch, unreliable for keyboard; releasing the clamp on interaction is better |
| Index >= 600px at 1440x900 | Unmeasurable on the 6-page fixture (217px) and above what the design produces |
| 200% device scale factor tests zoom | `deviceScaleFactor` changes DPR only; layout is byte-identical |
