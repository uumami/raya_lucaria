# Course-Home Affordance in the Left Rail — Design

Date: 2026-07-20
Status: Approved for planning
Supersedes: `2026-07-19-course-home-rail-control-design.md` (rejected — see below)

## Goal

Give the reader an obvious, always-visible home affordance at the top of the
left rail: a home icon that returns to the course landing page.

## Why the previous design was rejected

The superseded spec put a new home link in `.raya-course-map-header`. Three
independent reviews rejected it on separate grounds, and its problem statement
was factually wrong.

**Its premise was false.** The rail already contains a persistent course-home
link: the course tree's first node *is* the course root, rendered as an anchor
that already carries `aria-current="page"` when active
(`packages/static/src/raya_static/builder.py:2080-2090`, `:2019-2021`).

**It violated seed truth.** `docs/foundation/20_learning_renderer_contract.md:25`
states "The header Map action and eight body commands preserve the existing
nine reader actions"; a header home control makes ten. The same line's header
enumeration is closed and indicative ("presents `Course map` and an explicit
`Hide map` Map action"), while the contract uses "may" elsewhere when granting
optionality. The one extra header control that exists — the drawer close
button — is separately granted at `:27`. The amendment would have touched at
least six foundation clauses, four role docs, and three pinning tests, not the
two claimed.

**It did not fit.** Measured: the header content box is 191.00px and its
current contents need 191.39px, so `Course map` *already* wraps to two lines at
every desktop width. Adding an icon crushed the title to 35.83px with its text
painting 18.76px outside its box and overlapping the new control by 6.76px; an
icon-plus-label crushed the title to 0px and clipped `Hide map` by 11.16px.
Page overflow and rail overflow both read **0** in every broken case, because
`.raya-region-title` has `min-width: 0` and absorbs the squeeze silently — so
container-level and page-level overflow assertions provably cannot catch it.

## Design

### Placement

Add a home icon to the **course tree's root node** — the topmost item in the
rail body, rendered by `render_node` at `builder.py:2000-2090`.

This placement is free of every problem above:

- **No contract amendment.** The tree and its nodes are already granted by
  `20_learning_renderer_contract.md:25` ("the locally filterable hierarchical
  map, and its scrollable course tree"). No new reader action is created, so
  the nine-action budget is untouched.
- **No new tab stop.** The link already exists; it gains an icon, not a
  sibling.
- **No `aria-current` conflict.** The node already carries `aria-current="page"`
  on the course root (`builder.py:2019-2021`), and it remains the only such
  element in the `<nav aria-label="Course map">` landmark.
- **No header capacity problem.** It lives in the body, not the 191px header.
- **Correct root resolution already.** `render_node` is driven by
  `content_model.root_id` with a `children_by_parent[None]` fallback
  (`builder.py:2080-2083`) — not the `pages[0]` formula that is being fixed
  separately.

### Markup

Inside the root node's existing `<a>`, prepend the shared home glyph via the
existing `_command_icon("home")` helper (`builder.py:3233`), marked
`aria-hidden="true"`. Do **not** hand-roll an SVG; the discovery command bar
already uses this glyph for the same destination (`builder.py:1331-1338`).

The link's **accessible name is unchanged** — it stays the course's navigation
title, which is correct for a tree node and avoids inventing a third name for
this destination (the discovery bar already uses "Back to course"/"Course").

The icon is added **only** to the root node, not to every tree node.

### Styling

Give the root node a distinct treatment so it reads as "home" rather than as
just the first tree row. Scope the rule to the root node only. The icon must
be sized so the row does not grow or wrap at the rail's 240px width.

### Interaction with existing subsystems

- **Map filtering** reads `data-raya-map-label` (`shell.py:516`, `:849`), an
  attribute, not link text — and an SVG contributes no text content — so
  filtering is unaffected. This must still be asserted, not assumed.
- **Compact preview**, sequence numbers, and branch disclosure all key off
  existing attributes and are not expected to change. Also to be asserted.

## Testing

Test-driven. Each assertion must fail before the change; assertions that
already pass are not evidence and must not be listed as TDD.

1. The root tree node contains the home glyph, marked `aria-hidden="true"`,
   and no other tree node does.
2. The root node's accessible name is still the course navigation title.
3. Exactly one `aria-current="page"` exists inside `#raya-course-map` on the
   course root page.
4. Map filtering still matches the root node by its label.
5. **Layout, measured, not reasoned** — at 894/1000/1280/1440 and in the phone
   drawer at 390/375/320, with and without OpenDyslexic: the root row does not
   wrap, its height does not grow relative to sibling rows, and no descendant's
   painted text escapes its own box.

Requirement 5 exists because the previous design's failure was invisible to
container-level and page-level overflow checks. Assert on the element's own
`scrollWidth - clientWidth` and on painted-text-versus-sibling overlap.

## Non-goals

- No change to the rail header, the eight command tiles, or any foundation
  clause.
- No new control anywhere, including on the collapsed chip.
- No change to breadcrumbs. The `pages[0]` root-resolution defect they carry is
  a real shipped bug being fixed as its own separate change, not here.

## Open risks to validate before implementation

- Whether any test asserts the exact markup of map link inner HTML, which an
  added `<svg>` would break.
- Whether the icon measurably changes tree row height, which would reduce how
  many rows fit in the tree window — the tree is already sitting on its 12rem
  floor with content hidden at a 700px-tall viewport.
