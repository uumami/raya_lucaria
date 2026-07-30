# Reader Rail Density — Design

Date: 2026-07-29
Status: proposed
Scope: `packages/static` rendering only. Left course rail and right learning rail bodies.

## Problem

Both reader rails are unreadable at their shipped density. Measured in Chrome against
the deployed site (`uumami.wiki/raya_lucaria/foundation/system-model/index.html`) at
1440x900 unless noted.

### Left course rail

The rail is 868px tall. Fixed chrome above the index consumes a constant **444.6px**:

| Block | Height |
| --- | --- |
| `.raya-course-map-header` | 63.0px |
| `.raya-course-rail-tools` (search form + eight command tiles) | 252.8px |
| `.raya-page-position` (`Page N of M`, incl. 32px margins) | 57.6px |
| `.raya-course-map-filter-label` | 24.8px |
| `.raya-course-map-filter` | 46.4px |
| **Fixed chrome total** | **444.6px** |
| `.raya-course-map-list` (the index) | 385.4px |

The index needs **2027px** to lay out the 23 currently expanded entries. It receives
385.4px — **44% of the rail** — so the reader sees **4 of 33 pages** at a time.

Because the chrome height is constant and the index takes only the remainder, the
index shrinks as the viewport shortens and eventually disappears:

| Viewport | Rail | Index | Index share | Outer map also scrolls |
| --- | --- | --- | --- | --- |
| 1440x900 | 868px | 385.4px | 44% | no |
| 1440x720 | 688px | 205.4px | 30% | no |
| 1440x600 | 568px | 192.0px | 34% | **yes** |
| 200% zoom | 40px | **0px** | **0%** | no |

At 200% zoom the index is **0px tall**, so a wheel gesture over the rail has no
scrollable element under the cursor and nothing scrolls. This is the reported bug.

Three further defects:

1. **Nested scrollers.** `.raya-course-map` (`rendering.py:4003`) and
   `.raya-course-map-list` (`rendering.py:4202`) both declare `overflow: auto`.
   Below 600px viewport height both become scrollable, so the whole menu scrolls
   rather than only its content. Both also inherit `overflow-x: auto`.
2. **The index is not a growing flex item.** `.raya-course-map-body`
   (`rendering.py:4085`) is `display: flex; flex-direction: column` but sets no
   `min-height: 0`, and `.raya-course-map-list` sets `min-height: 0` without
   `flex: 1 1 auto`. The list is therefore sized by content and clamped, never by
   leftover space.
3. **The text column is 103.2px wide.** Of the 191px list width, each nesting level
   costs **22.6px** (`padding-left: 10.4px` + `margin-left: 11.2px` + 1px guide
   border) and the sequence badge costs **42px** (`min-width: 23.2px` +
   `margin-right: 7.2px` + `padding: 5.6px` each side). All 23 entries wrap; the
   worst reach **5 line boxes**; average row height is **88.1px**. `overflow-wrap:
   anywhere` is inherited across the list chain, so words break mid-word
   ("Security And Registratio / n").

### Right learning rail

Architecturally sound — exactly one scroller (`.raya-learning-rail-body`). The
defect is content volume: four panels are permanently expanded.

| Panel | Height |
| --- | --- |
| `.raya-page-contents` (table of contents) | 419.3px |
| `.raya-page-reading-flow` | 224.6px |
| `.raya-page-context` | 473.2px |
| `.raya-page-linked-pages` | 241.2px |
| **Total** | **1358.3px** in a 767px window |

The table of contents — the only panel that tracks reading position — is displaced
by three panels the reader consults rarely.

## Decisions

Locked with the repository owner before design:

1. **Rail width stays 240px.** No article width is given up and the pinned
   equal-width invariant is untouched. The fix is vertical and horizontal-within-rail
   only.
2. **Moderate chrome cut.** Command tiles become icon controls; the duplicated rail
   page position is removed; the filter label becomes a placeholder.
3. **No Display popover.** A four-per-row grid fits all eight controls, so every
   control stays one click away and no new popover interaction is introduced.
4. **Long titles clamp to two lines with an ellipsis**, full text exposed on
   hover and focus. Not full wrapping, not label rewriting.
5. **Both rails in this spec**, one contract amendment, one plan, one deploy.

## Design

### Left rail: three-zone frame, one scroller

`.raya-course-map` becomes the fixed frame and never scrolls.

```
.raya-course-map          overflow: hidden        (was: overflow: auto)
                          display: flex; flex-direction: column
.raya-course-map-header   flex: 0 0 auto          zone 1, fixed, 63px, unchanged
.raya-course-map-body     flex: 1 1 auto; min-height: 0
  .raya-course-rail-tools flex: 0 0 auto          zone 2, fixed
  .raya-course-map-list   flex: 1 1 auto; min-height: 9rem
                          overflow-y: auto; overflow-x: hidden
                          overscroll-behavior: contain
                          scrollbar-gutter: stable                zone 3, scrolls
```

`.raya-course-map` keeps `max-height: calc(100vh - 2rem)`. It loses
`overflow: auto`, `overscroll-behavior`, and `scrollbar-gutter`; those move to the
index, which becomes the single scroller in the rail.

**The frame stays content-sized and bounded, not stretched.** `height: 100%` must not
be added to `.raya-course-map`. The rail is sized by its content up to
`max-height: calc(100vh - 2rem)`; flex distribution then happens *within* that bound,
so the index absorbs the leftover only when the rail is actually clamped at
max-height. A short course whose whole tree fits renders a short rail with no
scrollbar, which is correct. Adding `height: 100%` would stretch every short rail to
full viewport height and is explicitly out of scope.

**The drawer path uses the same three zones.** Below the structural breakpoint the
map is `position: fixed` with the same header/tools/list structure, so the same
rules apply unchanged. The two height guards apply there as well and are verified at
640px and 390px widths.

The `min-height: 9rem` floor on the index is the fix for the zero-height failure. It
guarantees roughly four rows of index regardless of viewport height.

**Degenerate-height guard.** When the viewport is too short for header + tools +
floor, something must yield. In priority order:

- `@media (max-height: 640px)`: `.raya-course-map-filter` is hidden. The filter is
  reachable by typing into it after focusing the rail; the index is not reachable at
  all if it has no height, so the index wins.
- `@media (max-height: 480px)`: `.raya-course-map` regains `overflow-y: auto` as a
  last resort so no rail content becomes unreachable. This is the only state in
  which the frame scrolls, and it is preferable to hidden content.

### Left rail: zone 2 chrome

- `.raya-course-rail-search` — removed from the rail body. The `Search` icon control
  already links to the search workspace, so the inline form is redundant. This
  reclaims 46px plus its grid gap.
- `.raya-course-rail-command-list` — `grid-template-columns: repeat(2, ...)` becomes
  `repeat(4, ...)`. Eight controls render as **two rows of four**.
- `.raya-course-rail-command` — becomes a square icon control:
  `min-height: 2.5rem`, `aspect-ratio: 1`, `justify-content: center`,
  `padding: 0`. 40px targets satisfy WCAG 2.5.8 Target Size (Minimum). Four
  40px controls plus three 5px gaps is 175px, inside the 191px column.
  A single row of six or more controls does **not** fit and must not be attempted.
- Command labels move to `.raya-visually-hidden`. The existing `aria-label` and
  `data-raya-command-tooltip` already carry each control's name, so no accessible
  name changes. This reuses the exact icon-control pattern shipped for
  `Hide course map`.
- Per-command text colours are replaced by one resting colour
  (`var(--raya-color-text)`) with accent treatment reserved for hover, focus, and
  active state. Eight distinct hues in a 191px column carry no information.
- `.raya-page-position` — removed from the rail body. The article Page brief already
  renders `POSITION Page N of M`, so the rail copy is duplication.
- `.raya-course-map-filter-label` — becomes `.raya-visually-hidden`; the input gains
  `placeholder="Filter map"`. The label element and its `for` association stay in the
  DOM for assistive technology.

Projected zone 2 after the change: 86px strip + 42px filter = 128px, against 381.6px
today.

### Left rail: index rows

- Per-level indent 22.6px becomes **8px**: `padding-left: 0`, `margin-left: 7px`,
  1px guide border retained.
- The sequence badge leaves the text column. `.raya-course-map-list a::before` is
  `display: none` at rest and `display: inline-flex` on `:hover` and
  `:focus-visible`. The badge is permissive in the contract ("may show generated
  structural sequence numbers"), so hiding it at rest needs no amendment.
- `overflow-wrap: normal`, `word-break: normal`, `hyphens: none` applied across
  `.raya-course-map-list` and its `ol`, `li`, and `a` descendants. This removes
  mid-word breaking.
- `font-size: 0.8125rem`, `line-height: 1.3`, `padding: 4px 2px 4px 4px`.
- Two-line clamp: `display: -webkit-box`, `-webkit-line-clamp: 2`,
  `-webkit-box-orient: vertical`, `overflow: hidden`. The builder adds
  `title="<full label>"` to each map link so clamped text stays available on hover,
  and the accessible name remains the full link text.

Active and ancestor styling (`border-left` accent, weight, colour) is preserved
unchanged.

### Right rail: collapse what is not consulted

- `.raya-learning-rail-body` becomes `display: flex; flex-direction: column;
  min-height: 0` and keeps its single `overflow-y: auto`.
- `.raya-page-contents` stays open and becomes `flex: 1 1 auto; min-height: 6rem;
  overflow-y: auto`.
- `.raya-page-reading-flow`, `.raya-page-context`, and `.raya-page-linked-pages` are
  emitted as native `<details>` elements, closed by default, each with a `<summary>`
  carrying the existing panel heading text. `flex: 0 0 auto`.
- No JavaScript. Native disclosure only, matching the pattern the contract already
  accepts for hints, solutions, and answers.

Projected: three closed summaries at ~44px each is 132px, so the table of contents
receives roughly 640px instead of 419.3px, and the rail no longer scrolls two
screens on a page of this size.

## Contract amendment

`docs/foundation/20_learning_renderer_contract.md`, sentences at lines 25 and 33.
Both currently mandate the exact composition that causes the defect.

1. "exactly eight compact icon-labeled command tiles rendered two per row" becomes
   "exactly eight compact command controls rendered as icon controls with accessible
   names, four per row". The count of eight and the enumerated command identities are
   unchanged.
2. "followed by structural page position, the locally filterable hierarchical map"
   becomes "followed by the locally filterable hierarchical map". A permissive
   sentence is added: the rail may omit structural page position when the article
   Page brief already renders it.
3. The left course rail is stated to own exactly one scrolling region, its course
   tree, with the rail frame itself fixed.
4. The right learning rail is stated to keep its reading-context table of contents
   open as its scrolling region and may render its remaining panels as native closed
   disclosures.
5. `## Verification` gains checks for: one scroll container per rail; a course-tree
   minimum height that survives short viewports and 200% zoom; no mid-word breaking
   in map labels; map labels clamped to at most two lines with full text available on
   hover and as the accessible name.

The ten reader actions are unchanged in count, identity, and reachability. No
accessible name changes. Deployment neutrality of rail links is unaffected.

## Non-goals

- Rail width, article width, and the shared rail-header rule are untouched.
- No change to the drawer's open/close mechanics, focus containment, scroll lock, or
  Escape paths below the structural breakpoint.
- No change to sessionStorage keys, persisted comfort keys, or branch-collapse state.
- No renderer, backend, identity, or study-state work.
- No change to generated map label text. Removing the redundant `1.10 ` numeric
  prefix from labels was considered and rejected; it changes generated navigation
  data presentation and belongs in a separate spec if wanted.

## Invariants to protect

`tests/e2e/test_preview_static_read_path.py::test_render_fixture_reader_rails_share_outer_geometry`
(`:18341`) asserts the two rails share `top`, `width`, `height`, and inset symmetry
within 1px at widths 640, 893, 894, 1279, 1280, and 1440, and that both rail headers
have equal height. Both headers are styled by one shared rule at
`rendering.py:4074-4084`.

Every change in this spec lives inside a rail **body**. The shared header rule and
the rail width are not touched. The plan asserts a 0px header-height delta after the
change as an explicit regression gate.

## Verification

Browser end-to-end, Chromium via the existing `_browser_executable()` harness.

Left rail:

1. Exactly one scrollable ancestor of `.raya-course-map-list` — the list itself —
   at viewport heights 900, 720, 600, and 480, and at 200% device scale factor.
2. `.raya-course-map-list` client height is at least the 9rem floor at every height
   above, and strictly greater than zero at 200% zoom.
3. A wheel gesture positioned over the index scrolls the index and leaves
   `window.scrollY` unchanged.
4. `.raya-course-map` reports `overflow-y: hidden` above the 480px height guard.
5. Zero map links render three or more line boxes. Computed `overflow-wrap` and
   `word-break` are `normal` and `hyphens` is `none` on `.raya-course-map-list` and on
   a sampled deep map link, so no word can break mid-word.
   A link whose label is longer than two lines reports
   `scrollHeight > clientHeight` (clamped) and carries a `title` equal to its full
   label text.
6. Eight command controls render, in a grid of four columns, each at least 40px on
   both axes, each with a non-empty accessible name matching its pre-change name.
7. No horizontal scrollbar on the rail or the index.
8. Index client height is at least 600px at 1440x900 — the density outcome.

Right rail:

9. `.raya-page-contents` is open and is the only scrolling region inside the rail.
10. The three remaining panels are `<details>` elements, closed on load, and open on
    click without script.

Shared:

11. Header parity delta remains 0px at 640, 893, 894, and 1280, and the existing
    outer-geometry test passes unchanged.
12. Drawer path at 640px and 390px: the opened drawer still has exactly one scroller,
    the index still meets its floor, and existing focus containment, Escape close, and
    scroll-lock behaviour are unchanged.
13. Full suite green before merge, plus a live Chromium verification after deploy.

## Risks

- **`-webkit-line-clamp`** is the only non-standard property used. It is supported in
  all current Chromium, WebKit, and Gecko engines. If clamping fails, the row wraps
  instead of truncating, which degrades to the rejected option rather than breaking
  layout. Acceptable.
- **Hover-only badge** hides sequence numbers from touch readers at rest. The
  contract makes the badge permissive, the number is not required for navigation, and
  the hierarchy plus the label's own numeric prefix still convey position.
- **Right rail disclosures** change what is visible on load. Panel content is
  unchanged and reachable in one click, and the contract already accepts native
  closed disclosures as a reader-controlled reveal pattern.
- **The 480px height guard** reintroduces a scrolling frame in one narrow case. This
  is deliberate: unreachable content is worse than a scrolling menu, and the guard is
  covered by verification item 1.
