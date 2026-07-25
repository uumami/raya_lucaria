# Rail Home Control — Contract Amendment Design

Date: 2026-07-20 (revised 2026-07-24: re-measured, then corrected after a second
adversarial pass found the `flex-wrap` mechanism unworkable)
Status: Approved for planning
Supersedes: `2026-07-19-course-home-rail-control-design.md`,
`2026-07-20-course-home-affordance-design.md` (both rejected)

## Goal

An always-visible home control at the top of the left course rail that returns
the reader to the course landing page.

## Why the rail, not the breadcrumb

`docs/foundation/20_learning_renderer_contract.md:23` already grants a breadcrumb
"course home" link. It does not satisfy the requirement: breadcrumbs sit above
the article, scroll away with the article, and are absent on pages without an
ancestor chain. The requirement is an **always-present, in-rail** control. The
rail is the persistent reader-command surface, so the control belongs there —
which is why an amendment is warranted rather than reusing the breadcrumb.

## Why this needs a contract amendment

Two prior designs tried to avoid amending seed truth. Both were rejected by
independent review, and the reason is structural rather than incidental:

- **The rail header is enumeration-closed.** `:25` states the header "presents
  `Course map` and an explicit `Hide map` Map action" — indicative, not
  permissive, while the contract uses "may" freely elsewhere. The same line
  asserts the rail preserves "the existing nine reader actions". A header home
  control makes ten.
- **The rail body is enumeration-closed.** `:25` lists search, exactly eight
  tiles, page position, the map, and the tree. There is no slot for a
  persistent control.
- **The tree is non-persistent by contract.** Placing the affordance on the
  tree's root node fails because `orientCourseMapToCurrentPage`
  (`packages/static/src/raya_static/shell.py:793-846`) scrolls it out of view on
  load. That auto-scroll is itself contract-granted at `:25`.

Every location in the left rail is therefore either enumeration-closed or
non-persistent. An always-visible home control cannot be added without amending
the contract. This design amends it deliberately.

## Header layout: the measured reality

Measured in google-chrome against the `examples/courses/render-fixture` build
(via `raya_cli.preview.create_preview`, reader page `authoring-matrix/`), the
current desktop header has **exactly two visible children**: `.raya-region-title`
("Course map") and `.raya-course-map-collapse` ("Hide map" text button, ~92px).
The mobile-drawer Map toggle is `display:none` at desktop widths.

The header is a single non-wrapping flex row (`rendering.py:4074-4084`:
`display:flex; gap:0.75rem; justify-content:space-between; align-items:center;
min-height` 2.9375rem, 3.9375rem at ≥894) with the title at `min-width:0`
(`rendering.py:4109-4116`). Under pressure the **title text wraps** rather than
items reflowing. Measured line counts for `Course map`:

| font | density | title lines | overlap |
|---|---|---|---|
| default | comfortable (common case) | **2** | none |
| default | compact | 1 | none |
| OpenDyslexic | comfortable | 1 | none |
| OpenDyslexic | compact | 1 | none |

Two facts drive the design:

1. **Nothing overlaps in any cell.** An earlier draft claimed a 6.76px overlap;
   direct measurement (title text `Range` rect vs sibling border boxes, all 8
   cells) shows **zero overlap**. The failure mode is silent text-wrap, not
   overlap.
2. **The header height is pinned equal between the two rails.**
   `tests/e2e/test_preview_static_read_path.py:18349-18352` asserts
   `abs(mapHeader.height − railHeader.height) <= 1`, and
   `tests/contracts/test_documentation_surfaces.py` encodes the same left/right
   rail visual-parity truth. Both rail headers share one CSS rule
   (`rendering.py:4074-4084`, `.raya-course-map-header, .raya-learning-rail-header`)
   and one min-height, so today they are equal by construction, both governed by
   the min-height (the wrapped title, ~33.6px, stays under it).

**Parity is the load-bearing constraint.** Any header change that makes the
left header taller than the right — e.g. reflowing the controls onto a second
row (`flex-wrap`) — breaks `:18349`. A second-row layout was measured and
rejected for three independent reasons: it breaks height parity; because the
home control must be DOM-first for the drawer (see Drawer) a flat `flex-wrap`
renders a **three-row sandwich** (home / title / collapse), not "title row +
controls row"; and the header CSS selector is shared, so the wrap leaks into the
learning-rail header. The header must therefore stay **one row**.

## Enabling change: icon controls + a taller header at narrow widths

Adding a third element to a one-row header that is already full forces freeing
horizontal space, because the title needs at least one word's width (`Course` is
~50px and `word-break: normal` will overflow, not break, a narrower column). The
`Hide map` text button is ~92px — by far the largest consumer. Converting it to
an **icon control** frees enough room for the home icon plus a non-overflowing
title. (Measured: after conversion the header is one row with no overlap in
every font/density cell; the title still wraps to two lines in some cells, which
is fine — it stays under the header height and is the status quo today. The
earlier hope that icon-ification would give a *one-line* title does not
materialize because a real `.raya-command-icon` button is ~47px wide, not the
~32px first assumed, so the title column is ~81px — enough for one word per line,
not for `Course map` on one line. No one-line claim is made.)

**Parity fix (the load-bearing correction).** An icon button is ~40px **tall**
(24px glyph + shared vertical padding + border) versus the ~29px text button it
replaces. Below `RAIL_APPROVED_PX` (894) the shared header `min-height` is
`2.9375rem` = 47px (border-box), leaving only ~34px of content region — so the
icon button would push the **left** header to ~53px while the **right** header
stays at 47px, breaking the `abs(mapHeader.height − railHeader.height) <= 1`
assertion (`test_preview_static_read_path.py:18349`, run at 640 and 893). The
fix is to **raise the shared sub-894 header `min-height`** (both
`.raya-course-map-header` and `.raya-learning-rail-header`, `rendering.py:4082`)
to comfortably clear the icon button — target `min-height: 3.625rem` (58px).
This was empirically verified in google-chrome: at 3.5rem the parity delta is
0.00px at 640/893/894/1280 but the icon button's per-side slack is only ~1.3px;
3.625rem widens that margin against font/icon variation while keeping parity
exact. Because the rule is **shared**, both rail headers grow equally and parity
holds **by construction** at every width, with no per-breakpoint pixel tuning.
The 640/893 parity assertion is the guardrail if the icon size is later retuned. This is a deliberate,
user-visible ~9px increase to the right learning-rail header at narrow widths —
accepted as the cost of structural parity. The ≥894 min-height (`3.9375rem` =
63px, `rendering.py:4117-4121`) already clears the icon and is unchanged.

The `Hide map` conversion itself is **markup-only** and course-map-scoped: the
button's visible text becomes `_command_icon(...)` (`aria-hidden`) plus a
**visually-hidden `<span>Hide map</span>`** (reuse `.raya-visually-hidden`,
`rendering.py:638-646`). The button keeps its `aria-label="Hide course map"`, so
its **accessible name stays `Hide course map`** (aria-label wins over the span);
the span preserves `textContent === "Hide map"`. The shared CSS padding rule
(`rendering.py:4137-4152`) is untouched, so the learning-rail `Hide context`
button — a different element — stays a text button. No chevron/collapse glyph
exists in `_COMMAND_ICON_BODIES` (`builder.py:3232-3285`); a `collapse` glyph
must be added (or an existing collapse affordance reused — confirm during
implementation).

The home control is likewise an icon (`_command_icon("home")`), so the one-row
header reads: **`[home icon]` `Course map` `[collapse icon]`**.

## Contract amendment

All in `docs/foundation/20_learning_renderer_contract.md`:

1. **`:25` sentence 1** — the header presents `Course map`, a course-home
   action, and an explicit `Hide map` Map action **rendered as an icon control
   with the accessible name `Hide course map`** (the current button's aria-label,
   preserved).
2. **`:25` sentence 3** — "the existing nine reader actions" becomes **ten**,
   decomposed as one header Map action, one header course-home action, and eight
   body commands. This sentence must change in the same edit; leaving it produces
   a self-contradictory foundation, which `docs/foundation/13_truth_surfaces.md`
   forbids. (The body stays **eight** commands; only the header gains an action.)
3. **`:33` table row** — the same two additions and the icon-control phrasing.
   Its "Keep the header Map action separate from the eight body commands" rule
   stays valid (it forbids duplicating Map into the body; it does not cap header
   actions at one).
4. **`:27`** — the phone drawer enumeration, to grant the home control inside
   the drawer chrome (see Drawer).
5. **`## Verification`** — add rail home-control checks alongside the existing
   breadcrumb-check sentence ("course-home and ancestor links, current-page
   marking, deployment-neutral relative URLs, no source/private paths, no
   external requests, desktop/mobile no-overflow"). The rail home control needs
   the same coverage.
6. **`:23` deployment-neutrality** — currently scopes the "must not expose
   authored source paths" rule to *breadcrumb* links. Extend it so reader
   navigation links (breadcrumbs and the rail course-home control) are
   deployment-neutral.

**The eight-tile mandate is NOT changed.**

Per `13_truth_surfaces.md`, lower surfaces updated in the same change:

- **Role guides** (`docs/guides/{en,es}/*/index.md`, English and Spanish kept
  separate). These do **not** contain a "nine" count — `en/agents/index.md:144`
  and `es/agentes/index.md:155` say "**eight** reader commands" / "**ocho**
  comandos lectores" (header Map action held separate), which stays correct. The
  required edit is to **extend the header description** — currently "the rail
  header shows `Course map` with a `Hide map` Map action"
  (`en/students/index.md:51`, `es/estudiantes/index.md:52`, and the agents
  guides) — to include the course-home control and the icon rendering of
  `Hide map`. No count change in the guides.
- **`tests/contracts/test_documentation_surfaces.py`** — the reader-rail
  visual-parity truth surface (pins "Hide map", the tile enumeration, "header
  Map action") stays green through a visually-hidden label, but must gain the
  course-home-control assertion if it enumerates header actions.

## Implementation

### Home control

Add a keyword-only `header_home_html: str | None = None` parameter to
`_render_rail_chrome` (`builder.py:1930`), inserted into the item list
**between** `header_prefix_html` (`builder.py:1959`) and the `raya-region-title`
paragraph (`:1960`). The existing `"\n".join(item for item in items if item is
not None)` (`:1972`) keeps output byte-identical when omitted.
`_render_rail_chrome` is shared by the course map (`builder.py:2196`) and the
learning rail (`builder.py:2257`); the learning-rail call **must not** pass
`header_home_html` — the keyword-only default makes omission safe, and this is
the shared leak vector. Do not overload `header_suffix_html`; that slot is the
drawer close button and would place home after Close.

Reuse `_command_icon("home")` (glyph body at `builder.py:3233`, function at
`builder.py:3288`), marked `aria-hidden="true"`. Its accessible name is
**`Back to course`**, matching the discovery command bar's name for this exact
destination (`builder.py:1334`), so no third name is invented. Emit it with a
**home-specific class** (not in the drawer-hide whitelist below).

The control carries **no `aria-current="page"`**. The map tree already marks the
current page; a second such element inside `<nav aria-label="Course map">` is an
accessibility defect, and `test_preview_static_read_path.py:17495-17498` is a
Playwright **strict-mode** locator on `#raya-course-map a[aria-current="page"]`
that hard-fails on >1 match on the course root page.

### `Hide map` icon conversion

Course-map-scoped markup change only (no shared-CSS edit): the
`.raya-course-map-collapse` button's visible label becomes
`_command_icon("collapse")` (`aria-hidden`) plus a visually-hidden
`<span>Hide map</span>`. The button keeps its existing `aria-label="Hide course
map"` (`test_preview_static_read_path.py:17340`) and, via the visually-hidden
span, keeps `textContent === "Hide map"` (`.textContent.trim()` is what
`:17341`, `:18439`, `:18454`, and `:13861/:13965/:14025` read — verified — so
those stay green). Only the button **width** changes. Reuse an existing
visually-hidden utility class if one exists; otherwise add one.

### Root resolution, and when to omit the control

Resolve the destination with `_course_home_page()` (`builder.py:3475-3494`).
**Render the control only when `content_model.root_id is not None`** (and present
in `pages_by_id`). Do **not** gate on "`_course_home_page()` resolves": that
helper falls back to the first `children_by_parent[None]` entry
(`builder.py:3491-3493`), so a two-root `course/1_alpha.md` + `course/2_beta.md`
course (`root_id` unset, no `site/index.html`) would resolve to `1_alpha` and
wrongly render a home control at an arbitrary page. Gating on `root_id` omits it
for exactly that shape.

Caveat: `root_id` is set only for a depth-0 page whose source name starts with
`0_`/`00_` (`packages/schema/src/raya_schema/content.py:673-675`); a plain
`index.md` root gets `root_id=None` and no control. The `render-fixture` root is
`course/0_index.md`, so the fixture renders the control. The omit test (below)
needs a **separate** two-root fixture.

### Drawer

**Show it, ordered before Close.** `rendering.py:6296-6299` hides a whitelist of
header children when the drawer is open (`.raya-region-title`,
`.raya-page-position`, `.raya-course-map-toggle`, `.raya-course-map-collapse`);
the home control's class is deliberately **not** on that list, and because
`header_home_html` slots before the title it precedes `.raya-course-map-close`
in the DOM. `drawer_chrome_html` (`builder.py:2158-2167`) has no focusable
elements, so home is genuinely `focusable[0]`. The focus trap (`shell.py:314`)
filters on visibility, so it is counted. Initial focus stays forced on Close
(`shell.py:949`), unchanged — only the shift-Tab wrap target becomes home. Pin
this.

### Collapsed state

`rendering.py:6774-6778` sets `.raya-course-map-header` (and body) `display:none`
when `data-raya-course-map="collapsed"` at ≥640. The home child lives in the
header and disappears with it; only the expand chip remains, so "exactly one
visible control" holds. Below 640 there is no collapsed state; the closed drawer
hides the map by clip-rect and inertness rides on the JS path
(`shell.py:441-444`).

## Testing

Test-driven. Assertions that already pass are not TDD evidence. Aim browser
tests at `raya_cli.preview.create_preview` opening `authoring-matrix/index.html`
(mirror `_browser_executable` / `create_preview` in
`tests/e2e/test_rail_collapse_contract.py`).

**Layout — the failure mode is invisible to page-level overflow checks**
(`.raya-region-title` absorbs squeeze silently). Across the four font×density
cells (default/OpenDyslexic × comfortable/compact):

1. **Parity (the make-or-break invariant).** `mapHeader.height` equals the
   learning-rail `railHeader.height` within 1px — asserted at **640, 893, 894,
   and 1280** widths specifically (the sub-894 widths are where the taller icon
   button broke parity before the min-height fix; existing coverage runs 640/893).
2. The header is **one row** (all children share one row top ± centering slack),
   and in every cell no title character overflows its box (title box width ≥ its
   text `Range` width). The title may wrap to two lines; that is acceptable and
   is not asserted against.
3. No header child's painted text overlaps a sibling's border box; the header
   does not horizontally overflow the 240px rail.

**Behaviour and accessibility:**

4. The header contains a link named `Back to course` resolving to the course
   root from a nested page.
5. It is **omitted entirely** for a two-root, no-`index.html` course shape
   (`root_id` unset) — requires a dedicated fixture.
6. Exactly one `aria-current="page"` inside `#raya-course-map` on the root page.
7. `Hide map` collapse: accessible name stays `"Hide course map"` (aria-label)
   and `textContent` stays `"Hide map"` (visually-hidden span) after icon
   conversion; the button renders an icon, not visible text.
8. Drawer header child order places home before Close; shift-Tab wrap target is
   home.
9. The collapsed rail still exposes exactly one visible control.

**Pinning tests requiring updates** (confirm exact lines during implementation —
line numbers drift):

- `tests/e2e/test_preview_static_read_path.py:17338` **and `:20943`** — two
  copies of `assert 80 <= <collapse width> <= 100` both fail at the ~47px icon
  width; update both to the icon range. When updating, also **widen the height
  upper bound** at `:17339` and `:20944` (`28 <= height <= 40`): the icon button
  measures ~40.4px, which rounds to 40 only at the exact bound and is one
  sub-pixel from failing. `:17340` aria-label (`"Hide course map"`) stays valid;
  the `.textContent` probes (`:17341`, `:18439`, `:18454`, `:13861/:13965/:14025`)
  stay valid via the visually-hidden label.
- `tests/contracts/test_static_builder.py` — the exact-markup collapse-button
  pin at **`:5591-5597`** (literal `aria-label="Hide course map">Hide map</button>`)
  changes to the icon + visually-hidden-span markup; header child-order pins gain
  the home `<a>`. The `"Hide map" in text` pins (`:4946`, `:4970`) stay green via
  the visually-hidden span (textContent preserved).
- `tests/contracts/test_documentation_surfaces.py` — add the course-home-control
  assertion if it enumerates header actions; its parity/`Hide map` pins stay green.
- `tests/render/test_render_debug_report.py`,
  `tests/render/test_render_debug_parity_gate.py` — if they snapshot header
  markup, they gain the home + icon-collapse elements.
- Any test pinning the sub-894 header `min-height` / header height to `47px`
  (`2.9375rem`) will shift to the new `3.625rem`; grep and update during
  implementation. (Empirically, none currently exists — confirmed — but re-grep.)

## Non-goals

- No change to the eight command tiles.
- No `flex-wrap` / second header row; the header stays one row.
- No change to breadcrumbs; their root-resolution defect is fixed separately.
- No home control on the collapsed chip.
- No change to discovery workspace chrome. No home control or icon conversion in
  the learning-rail header — though its shared sub-894 `min-height` grows ~9px as
  a deliberate, accepted side effect of the parity fix.

## Known residual risk

`_course_home_page()` still returns the first top-level page when `root_id` is
unset. This design omits the rail control for that shape, so the residual risk
is confined to breadcrumbs, where the same fallback still guesses. Recorded
rather than silently accepted.
