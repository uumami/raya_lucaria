# Reader-rail collapse: single source of truth

- **Date:** 2026-07-17
- **Status:** Design (approved to write; pending user review of this spec)
- **Authority note:** This is a Superpowers design doc. It does **not** outrank
  `docs/foundation/20_learning_renderer_contract.md` (seed truth). Where this
  design and the foundation contract appear to differ, the contract wins.
- **Validation:** Root cause established by code exploration, then the design and
  this written spec were each put through an independent adversarial review pass
  (foundation compliance, architectural robustness, feasibility/regression,
  internal consistency, implementation soundness, completeness). All material
  findings are folded in. See "Provenance."

## Problem

The two reader side-rails — the left **course map** (`#raya-course-map`) and the
right **learning rail** (`#raya-learning-rail`) — break repeatedly in their
**collapsed** state. Photographed symptom: the collapsed rail renders as a narrow
strip that still contains the full command body, so labels wrap one glyph per
line ("C-o-n-t-e-x-t"), the search box and tree show through, and **two** map
buttons appear ("Hide map" top, "Map" bottom). The right rail's opener similarly
shows the raw word "Context" instead of a clean chevron chip.

This has been re-fixed many times and never stays clean.

## Root cause (why it keeps breaking)

No single source of truth for "collapsed." One visual state is smeared across
three concerns that each have multiple, drifting sources:

1. **State** is written to **three DOM mirrors** — `html`, `main`, and the rail
   element (`nav`/`aside`) — at different times (SSR in `builder.py`, runtime in
   `shell.py:492-494` / `1086-1088`, prepaint in `shell_prepaint.py`). CSS
   matches both the `html[...]` and element forms, so the two families can
   transiently disagree.
2. **Appearance** is defined in ~18 CSS rulesets across ~9 locations. The two
   halves of the contract — "hide the rail body" (`rendering.py:~4081`) and
   "narrow the strip + show the chip" (`rendering.py:~6765`) — live in **two
   different** `@media (min-width: 640px)` blocks **~2,680 lines apart**.
3. **The threshold** is hardcoded independently: JS pivots at **894**
   (`shell_prepaint.py`, `shell.py:54`), the in-flow grid CSS pivots at **1280**
   (`rendering.py:5306`), and there are further CSS `894`/`893` literals
   (`rendering.py:4110`, `6848`). In the **894–1279** band, default-expanded
   rails overlay the article with no reserved column — a live layout bug.

Every past fix patched one location; the next change drifted another. The
architecture guarantees drift.

## Goal

- Collapsed rail = one clean chevron chip (mirroring the right rail's good
  state) at every width ≥640, no body/header leak, no duplicate control.
- **Single source of truth per concern** so it stops drifting.
- **Every surrounding subsystem preserved** (see "Entangled subsystems"), each
  pinned by an invariant test.

Non-goals: removing the Context tile (foundation-required); changing the
eight-tile set; touching discovery/graph/search rails (isolated) or skins.

## Scope: surgical consolidation, not blind rebuild

Adversarial review established that the collapse mechanism is entangled with five
additional live, tested subsystems (below). "Erase the scattered CSS wholesale
and rebuild" would orphan them and regress currently-green behavior — i.e. it
would be *less* correct. Therefore the work is **surgical consolidation**: rewrite
exactly the three drift sources into one source each, while leaving every
surrounding subsystem intact (or explicitly, deliberately re-homed), with
invariant tests that prevent re-drift. The three-concerns/one-source
architecture below is the target; nothing outside those three concerns is erased
without an explicit line item here.

## Design: three concerns, one source each

### 1. STATE — single source

- **Effective collapse state** lives only as `data-raya-course-map` /
  `data-raya-learning-rail` on `<html>`. The `main` and rail-element mirror
  **writes** are deleted (`shell.py:492-494`, `1086-1088`, SSR).
- **Preference is a separate, retained channel.** The existing
  `data-raya-course-map-preference` / `-learning-rail-preference` attributes on
  `<html>` (`shell.py:190-191, 237-238, 1531-1535`) are **kept** — they store the
  user's intent so that after a width excursion (phone forces expanded) the
  runtime restores it (contract line 82). So "single source" means: one
  **effective** attribute per rail drives all CSS/appearance; preference is a
  distinct, clearly-named input to the derivation, not a competing appearance
  source. (The earlier "only one attribute" phrasing was wrong; there are
  effective + preference attributes, with distinct roles.)
- **The full effective-state derivation is the single source, code-generated
  once** and shared by both scripts — not merely the `894` literal. The
  derivation has two boundaries and a pairwise rule, all of which must stay in
  lockstep between prepaint and runtime:
  - `< 640`: both rails **expanded** effective (left is then presented as a
    drawer — see phone regime; right stays inline-expanded).
  - `≥ 894`: both rails may be expanded (default expanded).
  - `640–893`: at most **one** rail expanded; if both preferences are expanded,
    force the pair to the coordinated state (expanding one collapses the other —
    see REFLOW / medium-band coordination).
- **Accessibility (inert) is a derived effect of `(effective-state, width-regime,
  side)`, applied by JS** — not CSS, and not a single unconditional flag:
  - Own-state inert = `isStructuralRailShell() && collapsed`, applied to **both**
    rail bodies. This converges both rails onto the map's width-gated form
    (`shell.py:108-112`) and **fixes the latent bug** where the learning rail
    applies inert with no width gate (`shell.py:1090`).
  - At phone width the right rail's effective state is forced expanded, so its
    own-state inert is never set there (contract line 82).
  - Inert must be **re-derived on width-driven state changes** (resize /
    reconciliation), not only in the toggle handler.
- The 1280 `isDesktopShell` query (`shell.py:49`) survives for concerns outside
  collapse (tooltip enable, tab-order); it is documented as a separate,
  non-collapse breakpoint so "single 894 boundary" is understood to govern the
  collapse/reflow pivot only.

### 2. APPEARANCE — width-invariant, one co-located block

- The collapsed **chip** is defined in one contiguous, commented CSS region:
  narrow strip (`width: 2.75rem`), and **everything except the chip is hidden** —
  both the rail **body and the header chrome** (`Course map` label + `Hide map`
  button) go `display: none`. (Hiding only the body while the header lives in
  chrome would leave the header rendering in the strip → the photographed bug.
  The rule must mirror today's `rendering.py:4081-4084`, which hides header
  **and** body.) `display: none` also guarantees the a11y removal.
- The single visible collapsed control is the chevron chip (`2.5rem`) via the
  expand control's `::after` (`>` left / `<` right), with the mandated opener
  names (`Expand course map` left; Context opener right).
- This collapsed appearance is **per-side, width-invariant** at every width ≥640
  (contract groups Desktop + medium-width for collapse). "Per-side" because the
  two sides deliberately differ in chevron direction and opener name; they are
  not cross-side identical (the symmetry test asserts equal *size/geometry*, not
  equal content).
- **Compact-preview tooltip interoperation:** the collapsed map's tree links must
  remain hoverable/focusable so the tooltip still fires, yet the body must be
  a11y-hidden. Resolve explicitly: the collapsed body is visually hidden and
  removed from normal a11y/tab flow, but the tooltip's hover/focus sources
  (`#raya-course-map-list a[href]`) must retain a usable hit-box and non-zero
  `getBoundingClientRect()` for `positionCourseMapCompactPreview`
  (`shell.py:864-873`). The implementation must therefore NOT achieve the hide
  purely via `display:none` on the tree if that kills the tooltip — it must
  reproduce today's working interplay (`updateMapLinkTabOrder` /
  `setFocusableDescendantsEnabled`) OR the design must consciously drop the
  tooltip (not silently). Tooltip horizontal anchor is `map.right`
  (`shell.py:865,870`), which still resolves for the fixed chip; the tooltip's
  vertical anchor references the chip, which is now width-invariant — restate the
  anchor as the chip box, not the old per-band `top` offsets.

### 3. REFLOW — width-conditional, minimal, token-driven

- A **single 894 boundary** governs reflow, matching the auto-collapse threshold
  (closes the 894-vs-1280 dead zone).
- **In-flow grid track math (must fit 894px = 55.875rem):** today's in-flow grid
  (`rendering.py:5306-5333`) uses `15rem minmax(42rem,1fr) 15rem` (dual-expanded)
  and `minmax(48rem,1fr)` for single-rail cases — floors of **72rem/1152px** and
  **63rem+**, which overflow 894 by ~300px. Therefore, when moving the in-flow
  grid down to 894:
  - In **894–1279**, the article track floor is **`minmax(0, 1fr)`** (not
    42/48rem); rail tracks are token-driven (`0` collapsed / `15rem` expanded).
    Dual-expanded article ≈ 22.9rem/366px at exactly 894 — narrow but
    non-overflowing — widening with the viewport.
  - The **42rem/48rem "comfortable article" floors are reintroduced only ≥1280**
    as a separate layout layer (the surviving legitimate use of 1280).
  - On a collapsed side, zero the adjacent **column-gap** (not just the track) so
    the article fully reclaims the ~1.5rem; a `0` track with a live gap leaves
    phantom spacing.
- **Medium-band (640–893) coordination is a first-class reflow rule:** at most one
  rail expanded; expanding one auto-collapses the other
  (`shell.py:1691-1693,1711-1712`; derived in `effectiveReaderShellState`
  `shell.py:220-226` and prepaint `shell_prepaint.py:21-24`). An expanded rail
  here **overlays** the article (does not reserve a column). Without this rule the
  token reflow would let both rails overlay from both edges at once — a
  regression the current code prevents (asserted at test
  `test_reader_shell_open_actions_coordinate_only_below_approved_geometry`).
- Media-query edges: 639/640 and 893/894 are integer-complementary. Drive both
  the JS threshold and the CSS `@media` boundaries from the one code-generated
  value; accept the sub-pixel `893.x` fractional line as pre-existing (or use a
  `.98` upper bound) — do not let JS and CSS disagree on the number.

### Structure — shared chrome, separate bodies, explicit focus handoff

- A shared `_render_rail_chrome(...)` helper emits only the recurring collapse
  chrome: landmark wrapper, header + collapse button, expand chip/edge opener,
  backdrop, inert wiring — parameterized by `side`, labels, opener name. It must
  **not** inject a second Map/collapse control into the left body (contract line
  25: no Map duplicated in body). Exactly two controls exist: the header
  `Hide map`/`Hide context` and the floating edge opener.
- Each rail keeps its **own body builder** (contract-mandated asymmetry): left =
  search · eight tiles (incl. Context) two-per-row · filter · tree ·
  compact-preview; right = section-context-first panels · context-chip. Rails are
  **chrome-symmetric, body-asymmetric**.
- **Focus-handoff contract (design, not just a test):** collapse → focus moves to
  the expand chip (`shell.py:1763`, `1779-1780`); expand → after the transition,
  focus moves from the chip to the collapse control (`focusAfterExpansion`,
  `shell.py:1062-1080,1105-1111`); breakpoint reconciliation maps the active
  element to a target (`readerShellReconciliationFocusTarget`,
  `shell.py:1408-1456`). The chrome refactor re-emits exactly these buttons, so
  their identities/wiring must be preserved and re-pointed.

### Phone regime (< 640) — asymmetric by contract

- **Left course map = modal drawer** (JS state machine: chrome, backdrop, focus
  trap, background inertness, scroll lock). Escape closes the drawer.
- **Right learning rail = inline-expanded by its own state**, unconditionally,
  regardless of any stored "collapsed" preference — restored on entry to phone
  width even from a previously-collapsed chip (contract lines 27, 35, 82). Escape
  never sets the right rail inert **via its own collapse mechanism**.
- **Modal-background exception:** while the **map drawer is open** at phone width,
  the right rail IS `aria-hidden` + `inert` as modal background
  (`syncCourseMapModalBackground`, `shell.py:286-290,441`), restored on close.
  The invariant distinguishes *own-state inert* (never at phone) from
  *modal-background inert* (yes, while the drawer is open).

## Entangled subsystems — preserved (explicitly not erased)

Each of these is live and tested; the consolidation must keep them working and
re-assert them against the new model, not delete them:

1. **Reduced-motion transition animator.** `data-raya-*-transition`
   (`expanding`/`collapsing`) on the rail element, gated by `reducedMotionQuery`
   (`shell.py:466-503,1057-1112`); CSS keeps the body `visibility:hidden` during
   the animation (`rendering.py:4149-4192,5349-5360,6571-6574`). The
   `-transition` attribute is a **distinct animation channel on the element**,
   explicitly exempt from the "html-only state" rule. Resolve the collision
   between the transient `.raya-learning-rail-expand::after { content:"Context" }`
   (`rendering.py:4187`) and the new chevron `::after` — one must win by state,
   documented.
2. **Medium-band (640–893) mutual-exclusion coordinator** (see REFLOW).
3. **Map-drawer modal background-inerting** + right-rail modal-background
   exception (see phone regime).
4. **Learning-rail drawer subsystem** — `data-raya-learning-rail-drawer`,
   opener, `trapLearningRailDrawerFocus` (`shell.py:349-368`), scroll-lock,
   backdrop (`builder.py:2232-2233`), Escape (`shell.py:1746-1748`). **Default:
   preserve as-is** (out of scope for the consolidation). It may be removed only
   if the plan's investigation proves the path unreachable, and only as a
   separate, explicit line item that also removes its backdrop — never orphan the
   backdrop element.
5. **Focus-handoff / reconciliation engine**, including bfcache `pageshow`
   (`shell.py:1458-1505`) and `focusout`-deferred reconciliation
   (`shell.py:1506-1519`) — both re-derive and re-apply rail state and must be
   re-expressed against the html-only effective model.
6. **Compact-preview tooltip** (see APPEARANCE) — preserve interactivity.
7. **Print + breadcrumbs** — print hides the rails and forces
   `.raya-learning-shell { display:block !important }` (`rendering.py:7210-7323`);
   the token-driven grid must not fight this override. Re-assert
   `test_preview_reader_print_view_is_static_handout`.
8. **Per-branch disclosure** (`raya:course-map-branches`) — assert branch state
   survives a collapse→expand cycle (collapse calls `clearCourseMapFilter`, body
   hides; branch storage must persist).

## Foundation invariants (asserted by tests)

Eight tiles two-per-row expanded incl. Context; header `Course map` + `Hide map`
with no Map duplicated in body; opener names `Expand course map` / Context;
collapsed content inert + removed from keyboard/assistive nav; **phone right rail
inline-expanded and reachable, restored even from a collapsed state, never
own-state-inert — but modal-background-inert while the map drawer is open**;
collapsed rails reserve no grid column ≥894; medium-band at most one rail
expanded; sessionStorage keys `raya:reader-shell:v1:<course_id>` and
`raya:course-map-branches:v1:<course_id>` and comfort keys unchanged; no new
storage/network/cross-tab state; discovery/graph/search untouched.

## Code-generation and guardrail tests

- **Threshold + derivation codegen.** Define the boundaries (640, 894) and the
  effective-state derivation once in Python. The two scripts are emitted verbatim
  from raw triple-quoted strings (`shell.py`, `shell_prepaint.py`), which are
  brace-dense, so use **placeholder tokens + `str.replace`** from the shared
  constant (NOT f-strings/`.format`). The CSS is also emitted from Python
  (`rendering.py`); interpolate the **same** boundary literals into the emitted
  CSS `@media` values so CSS cannot drift from JS.
- **Guardrail tests (prevent re-drift):**
  - Both emitted scripts **and** the emitted CSS contain the same boundary
    literals (grep parity across all three).
  - No collapse-relevant CSS selector references the **element mirror**
    (`.raya-course-map[data-...]`, `.raya-learning-rail[data-...]`) or the
    `.raya-learning-shell` (`main`) mirror form — only `html[...]` (audits the
    ~20+ read sites at `rendering.py:4083-4084,5321-5350,6529-6547`, not just the
    write sites).
  - No `#id` selector references collapse state outside the prepaint skeleton;
    this requires class-ifying **all** such selectors, including the
    **non-skeleton** hover rules at `rendering.py:6557-6558` (else the test
    self-fails on existing code) plus the skeleton set
    (`6661,6662,6686,6687,6689,6690`).

## Files touched

- `builder.py` — `_render_rail_chrome`; rails call chrome + own body; remove SSR
  state mirrors; emit codegen'd boundaries/derivation into both scripts.
- `rendering.py` — one collapsed-appearance region (hide header+body except chip);
  token-driven reflow with 894-band article floor `minmax(0,1fr)` and ≥1280
  comfort floors; codegen'd `@media` boundaries; class-ify `#id` collapse
  selectors (skeleton + `6557-6558`); preserve transition/print CSS.
- `shell.py` — single `<html>` effective write; keep `-preference`; inert =
  `f(state,width,side)` re-derived on resize; width/side-scoped Escape; re-point
  focus-handoff to re-emitted chrome buttons.
- `shell_prepaint.py` — read the same codegen'd boundaries/derivation.
- Tests — see below.

## Testing and verification

- **TDD first**: single-contract acceptance test at 640/768/894/1280/1440 — each
  rail collapsed = exactly one control, ~40px width-invariant chevron chip, body
  **and header** hidden + absent from a11y tree, left/right chip size identical,
  no horizontal overflow, no leak.
- **Re-assert every preserved subsystem** in the new model (named tests):
  transitions (`..._expansion_hides_full_list_until_transition_end`,
  `..._learning_rail_expansion_keeps_body_accessible_during_transition`),
  reduced-motion (`test_render_fixture_shell_respects_reduced_motion`),
  medium-band coordination
  (`test_reader_shell_open_actions_coordinate_only_below_approved_geometry`,
  `test_reader_shell_medium_actions_store_coordinated_pair`), modal background
  (`test_mobile_course_map_drawer_is_modal_and_volatile`), reconciliation
  (`test_reader_shell_bfcache_pageshow_reconciles_saved_state`,
  `test_reader_shell_null_focus_loss_does_not_reconcile_without_media_change`),
  overlay/edge-opener geometry
  (`test_render_fixture_collapsed_reader_rails_use_mirrored_edge_openers`,
  `test_render_fixture_medium_reader_rails_are_overlay_controls`), context toggle
  (`test_render_fixture_top_context_command_toggles_right_rail_only`), print
  (`test_preview_reader_print_view_is_static_handout`), tooltip
  (`test_render_fixture_course_map_collapses_and_expands_on_click_only`).
- **Guardrail tests** above (threshold parity, mirror-read, `#id`).
- **Foundation invariants** as assertions (list above).
- **Real-browser validation** at each breakpoint via Chromium + an independent
  adversarial visual-validation subagent that must *see* clean symmetric chips.
- **Gates:** `./scripts/check.sh` + `./scripts/check-render-debug.sh`;
  screenshots per convention.
- **Blast radius is a floor, not a ceiling.** The named tests above extend the
  original four categories (mirrors, per-width offsets, doubled selectors,
  four-breakpoint geometry); the risk is **un-enumerated behaviors deleted
  instead of re-asserted** — the implementation plan must convert, never drop.

## Risks and mitigations

- **Entanglement**: five surrounding subsystems can be silently orphaned.
  Mitigation: the "Entangled subsystems" section enumerates them; each is a
  named re-assert test; TDD-first so a dropped behavior fails before merge.
- **894 in-flow overflow**: article floor must drop to `minmax(0,1fr)` in
  894–1279 (comfort floors only ≥1280); acceptance test asserts no overflow at
  894/1000/1152.
- **Tooltip vs a11y-hide conflict**: explicit interactivity mechanism or a
  conscious, documented drop — not a silent regression.
- **JS-disabled**: prepaint absent → collapsed chips that cannot expand
  (pre-existing; documented).
- **Stash collision**: `test_rail_symmetry.py` sits in `stash@{0}`
  (`stale-local-rail-session-2026-07-17`), not on disk — reconcile/drop before
  starting.

## Process

- Work on branch `rail-collapse-single-source-of-truth` (already created off
  `new_rayalucaria`); fully revertible. Deployment (GitHub Pages via
  `raya build docs`) is structurally unaffected.

## Provenance

Two adversarial rounds. Round 1 (design): compact-preview is live (preserve);
shared chrome not shared rail; asymmetric phone regime; width/side-scoped Escape;
JS-applied inert as derived effect; build-time codegen; unify 894/1280. Round 2
(this written spec): collapsed must hide header not just body; the 894 in-flow
grid overflows unless the article floor drops to `minmax(0,1fr)` below 1280;
codegen must cover CSS and the full 640/894 derivation (not just the 894
literal); an invariant test must audit mirror-**read** sites; retain the
preference↔effective split; inert = `f(state,width,side)` and fix the latent
learning-rail inert bug; phone re-expansion from a collapsed state; and five
entangled subsystems (transition animator, medium-band coordinator, map-drawer
modal inerting, learning-rail drawer, focus/reconciliation engine) must be
preserved and re-asserted, not erased.
