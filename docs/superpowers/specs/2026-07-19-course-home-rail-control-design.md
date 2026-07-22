# Course-Home Control in the Left Rail Header — Design

Date: 2026-07-19
Status: Approved for planning

## Problem

There is no persistent, obvious way back to the course landing page from the
left course rail. A course-home link does exist, but only in the article
breadcrumbs (`_render_breadcrumbs`, `packages/static/src/raya_static/builder.py:3475`,
emitting `raya-breadcrumb-home`), which is easy to miss and renders nothing at
all when a page has no ancestors (`if not breadcrumbs: return ""`, `:3477`).

## Constraint that shapes the design

`docs/foundation/20_learning_renderer_contract.md` is seed truth and outranks
all other guidance. Two clauses bind this work:

- Line 25 and line 33 mandate the rail body contain **exactly eight** compact
  icon-labeled command tiles, two per row, for Search, Graph, Practice, Tasks,
  Schedule, Context, Text size, and OpenDyslexic.
- The same clauses state the rail header presents `Course map` and an explicit
  `Hide map` Map action.

A ninth tile is therefore not a code change but a contract amendment, and it
would additionally break the two-per-row grid into an uneven row. Placing the
control in the **header** leaves the eight-tile mandate completely untouched
and requires only that the header's description be amended. That is the
smallest possible change to seed truth, and it is why the header was chosen.

## Design

### Placement and behaviour

A course-home icon link inside `.raya-course-map-header`, alongside the
`Course map` title and the `Hide map` action, rendered through the existing
`_render_rail_chrome` helper (`builder.py:1930`) so the left rail keeps a
single chrome path. It appears on every reader page, including the course
root, and in the phone drawer, which reuses the same header.

**Collapsed state — a deliberate, accepted limitation.** When the rail is
collapsed it becomes a 2.75rem chip, and the contract requires that state to
expose a minimal floating opener with the accessible name
`Expand course map`. `tests/e2e/test_rail_collapse_contract.py::test_collapsed_rails_are_single_clean_chips`
asserts the collapsed rail has exactly one visible control. Because the header
is `display: none` when collapsed, a header home link disappears
automatically, which is both correct and consistent. **Home is reachable
whenever the rail is expanded or the drawer is open, and is not present on the
collapsed chip.** Adding a second persistent control to the collapsed chip
would re-break the single-chip invariant and is explicitly out of scope.

### Markup and accessibility

An `<a>` element, not a button, because it navigates. It contains an inline
SVG home glyph marked `aria-hidden="true"` and carries the accessible name
`Course home`. On the course root page itself the link still renders and
carries `aria-current="page"` so assistive technology announces that the
reader is already there.

The `href` is computed exactly as the existing breadcrumb home does —
`_relative_href(page.output_path, content_model.pages[0].output_path)` — so it
is a deployment-neutral static link that never exposes authored source paths,
as the contract requires of breadcrumb and navigation links.

### Contract amendment

`docs/foundation/20_learning_renderer_contract.md` lines 25 and 33 must be
amended so the header description includes the course-home action alongside
`Course map` and `Hide map`. **The eight-tile mandate is not modified.** No
other foundation clause changes.

## Testing

Test-driven, with each assertion failing first:

- The rail header contains a link with the accessible name `Course home` whose
  `href` resolves to the course root from a nested page.
- On the course root page, that link carries `aria-current="page"`.
- The collapsed rail still exposes exactly one visible control, so this feature
  cannot regress the single-clean-chip invariant.
- The emitted link is relative and contains no authored source path segment.

## Non-goals

- No change to the eight command tiles.
- No change to breadcrumbs, including the empty-breadcrumb case on pages
  without ancestors. That gap is real but separate; it is recorded below.
- No new persistent control on the collapsed chip.
- No change to discovery workspace chrome, which already links back to the
  course via its own `home_href` (`builder.py:1323,1333`).

## Follow-up recorded, not fixed here

`_render_breadcrumbs` returns an empty string when a page has no ancestors
(`builder.py:3477`), so those pages show no breadcrumb home link at all. Once
the rail header carries a persistent home control this matters less, but the
inconsistency remains and should be decided deliberately rather than left
implicit.
