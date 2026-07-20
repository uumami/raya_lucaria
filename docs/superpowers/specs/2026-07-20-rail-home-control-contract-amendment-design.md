# Rail Home Control — Contract Amendment Design

Date: 2026-07-20
Status: Approved for planning
Supersedes: `2026-07-19-course-home-rail-control-design.md`,
`2026-07-20-course-home-affordance-design.md` (both rejected)

## Goal

An always-visible home control at the top of the left rail that returns the
reader to the course landing page.

## Why this needs a contract amendment

Two prior designs tried to avoid amending seed truth. Both were rejected by
independent review, and the reason is structural rather than incidental:

- **The rail header is enumeration-closed.** `docs/foundation/20_learning_renderer_contract.md:25`
  states the header "presents `Course map` and an explicit `Hide map` Map
  action" — indicative, not permissive, while the contract uses "may" freely
  elsewhere. The same line asserts the rail preserves "the existing nine reader
  actions". A header home control makes ten.
- **The rail body is enumeration-closed.** `:25` lists search, exactly eight
  tiles, page position, the map, and the tree. There is no slot for a
  persistent control.
- **The tree is non-persistent by contract.** Placing the affordance on the
  tree's root node fails because `orientCourseMapToCurrentPage`
  (`packages/static/src/raya_static/shell.py:793-846`) scrolls it out of view on
  load — measured `scrollTop` 98 at 1440×900 and 264 at 1440×700 on the render
  fixture, with the root row outside the scrollport in both. That auto-scroll is
  itself contract-granted at `:25` ("may auto-orient the current page into the
  visible map region after load").

Every location in the left rail is therefore either enumeration-closed or
non-persistent. An always-visible home control cannot be added without
amending the contract. This design amends it deliberately.

## Enabling change: `Hide map` becomes an icon control

The header does not currently have room. Measured at the rail's fixed 240px, the
header content box is **191.00px** and its contents already need **191.39px**, so
`Course map` **already wraps to two lines** at every desktop width today. Adding
anything crushes `.raya-region-title`, which has `min-width: 0` and silently
absorbs the squeeze — measured 18.76px of title text painting outside its own box
and overlapping the new control by 6.76px.

Converting the `Hide map` text button (92.39px) to an icon-only chevron
(32.38px) frees **60.01px**. Re-measured with that change:

| header contents | deficit | title box | title lines | spill |
|---|---|---|---|---|
| baseline today | +0.39 | 86.61 | **2** | 0 |
| `Hide map` as icon, no home | −52.62 | 93.53 | **1** | 0 |
| `Hide map` as icon + full home chip | **−1.84** | 93.53 | **1** | 0 |

So the amendment also **fixes a pre-existing defect**: the header title stops
wrapping for the first time. The home chip retains full padding (38.78 × 32.38),
clearing the WCAG 2.5.8 24×24 target minimum — a bare 16px icon would be 44% of
that minimum and is rejected.

## Contract amendment

All in `docs/foundation/20_learning_renderer_contract.md`:

1. **`:25` sentence 1** — the header presents `Course map`, a course-home
   action, and an explicit Map collapse action rendered as an icon control with
   an accessible name.
2. **`:25` sentence 3** — "the existing nine reader actions" becomes ten,
   decomposed as one header Map action, one header home action, and eight body
   commands. This sentence must change in the same edit; leaving it produces a
   self-contradictory foundation, which `docs/foundation/13_truth_surfaces.md:25`
   forbids.
3. **`:33` table row** — the same two changes, plus its "Keep the header Map
   action separate from the eight body commands" rule, which is phrased in terms
   of exactly one header action.
4. **`:27`** — the phone drawer enumeration, to grant the home control inside
   the drawer chrome (see Drawer below).
5. **`:224` Verification** — add rail home-control checks; course-home
   verification is currently scoped to breadcrumb checks only.
6. **Deployment-neutrality** — `:23` states the no-authored-source-path rule for
   *breadcrumb* links only. Extend it to cover rail navigation links, or the
   rail control relies on a rule that does not cover it.

**The eight-tile mandate is NOT changed.**

Per `13_truth_surfaces.md:23`, lower surfaces must be updated in the same
change: the eight role guides pinned by
`tests/contracts/test_static_builder.py:4881`
(`docs/guides/{en,es}/*/index.md`), plus the pinning assertions in
`tests/contracts/test_documentation_surfaces.py:378-399`.

## Implementation

### Home control

Add a keyword-only `header_home_html: str | None = None` parameter to
`_render_rail_chrome` (`packages/static/src/raya_static/builder.py:1930-1943`),
inserted into the item list **between** `header_prefix_html` and the
`raya-region-title` paragraph (`:1959-1960`). The existing
`if item is not None` filter (`:1972`) keeps output byte-identical when omitted.
`_render_learning_rail` (`:2251`) must **not** pass it — the helper is shared by
both rails and this is the leak vector. Do not overload `header_suffix_html`;
that slot is already the drawer close button and would place home after Close.

Reuse the existing `_command_icon("home")` glyph (`builder.py:3233`), marked
`aria-hidden="true"`. Its accessible name is **`Back to course`**, matching the
name the discovery command bar already uses for this exact destination
(`builder.py:1330-1337`), so no third name is invented.

The control carries **no `aria-current="page"`**. The map tree already marks the
current page (`builder.py:2019-2021`); a second such element inside the same
`<nav aria-label="Course map">` landmark is an accessibility defect, and six
e2e probes query `#raya-course-map a[aria-current="page"]` unscoped — one via a
Playwright strict-mode locator that would hard-fail on the course root page.

Both the home control and the collapse control get `flex: 0 0 auto`;
`.raya-course-map-collapse` currently has no `flex-shrink: 0`
(`rendering.py:4137-4151`) and is the first thing to collapse under pressure.

### Root resolution, and when to omit the control

Resolve the destination with `_course_home_page()`
(`builder.py`, added by the breadcrumb root-resolution fix): `content_model.root_id`
when present, else the first `children_by_parent[None]` entry. **Render the
control only when that resolves.**

A course of `course/1_alpha.md` + `course/2_beta.md` validates and builds with
two depth-0 roots and **no `site/index.html` at all** — there is no landing page
to go home to. In that shape the control must be omitted, not pointed at an
arbitrary top-level page.

### Drawer

**Decision: show it, ordered before Close.** Silence here produces the wrong
order. `rendering.py:6305-6309` hides a whitelist of header children when the
drawer is open; the home control is deliberately **not** added to that list, and
because `header_home_html` slots before the title it precedes
`.raya-course-map-close` in the DOM.

The focus trap (`shell.py:315-346`) filters on computed visibility, so the
control is counted correctly. Drawer-open focus still lands explicitly on Close
(`shell.py:955-961`), so initial focus is unchanged — but the control becomes
`focusable[0]`, changing the shift-Tab wrap target. That is acceptable and must
be pinned by a test.

### Collapsed state

The header is `display: none` when collapsed at ≥640 (`rendering.py:6785-6789`,
inside the `min-width: 640px` block opened at `:6704`), verified in Chrome at
768/894/1280 with `controlCount == 1`. Below 640 there is no collapsed state;
the closed drawer hides the map by clip-rect and the control's inertness rides
on the existing JS path (`shell.py:441-444`), not on CSS.

## Testing

Test-driven. Assertions that already pass are not TDD evidence and must not be
listed as such.

**Layout — these exist because the failure mode is invisible to normal checks.**
Page-level and container-level overflow both read **0** in every measured broken
case, because `.raya-region-title` absorbs the squeeze silently. Assert instead:

1. `.raya-region-title` has `scrollWidth - clientWidth === 0`.
2. No header child's painted text overlaps a sibling's box.
3. `Course map` renders on **one** line at 894/1000/1280/1440, with and without
   OpenDyslexic. This fails today and is fixed by the icon conversion.

**Behaviour and accessibility:**

4. The header contains a link named `Back to course` resolving to the course
   root from a nested page.
5. It is omitted entirely for the two-root, no-`index.html` course shape.
6. Exactly one `aria-current="page"` inside `#raya-course-map` on the root page.
7. Drawer header child order places home before Close.
8. The collapsed rail still exposes exactly one visible control.

**Tests requiring updates** (identified, not exhaustive — confirm during
implementation): `tests/e2e/test_preview_static_read_path.py:20942` asserts the
collapse button is 80–100px wide and will fail at 32px; `:18342` and `:20945`
assert `collapse.scrollWidth <= clientWidth + 1`; `:17246` selects the collapse
button as a direct header child; `tests/contracts/test_static_builder.py:5609-5620`
pins header markup and ordering.

## Non-goals

- No change to the eight command tiles.
- No change to breadcrumbs; their root-resolution defect is fixed separately.
- No home control on the collapsed chip.
- No change to discovery workspace chrome.

## Known residual risk

`_course_home_page()` returns the first top-level page when `root_id` is unset.
For the multi-root shape this design omits the control, so the residual risk is
confined to breadcrumbs, where the same fallback still guesses. Recorded rather
than silently accepted.
