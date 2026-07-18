# Reader-rail collapse: single source of truth

- **Date:** 2026-07-17
- **Status:** Design (approved to write; pending user review of this spec)
- **Authority note:** This is a Superpowers design doc. It does **not** outrank
  `docs/foundation/20_learning_renderer_contract.md` (seed truth). Where this
  design and the foundation contract appear to differ, the contract wins and
  this doc must be corrected. Every requirement below was checked against that
  contract by an adversarial review pass.

## Problem

The two reader side-rails — the left **course map** (`#raya-course-map`) and the
right **learning rail** (`#raya-learning-rail`) — break repeatedly in their
**collapsed** state. The visible symptom (photographed by the user): the
collapsed rail renders as a narrow strip that still contains the full command
body, so labels wrap one glyph per line ("C-o-n-t-e-x-t"), the search box and
tree show through, and **two** map buttons appear ("Hide map" at top, "Map" at
bottom). The right rail's collapsed opener similarly shows the raw word
"Context" instead of a clean chevron chip.

This has been re-fixed many times (`Contain reader rail commands`,
`Fix reader rail control fit`, `Restore dedicated map control geometry`,
`Mirror reader rail geometry`, …) and never stays clean.

## Root cause (why it keeps breaking)

There is **no single source of truth for "collapsed."** One visual state is
smeared across three concerns that each have multiple, drifting sources:

1. **State** is written to **three DOM mirrors** — `html`, `main`, and the rail
   element (`nav`/`aside`) — at different times (SSR in `builder.py`, runtime in
   `shell.py:492-494` / `1086-1088`, prepaint in `shell_prepaint.py`). CSS
   selectors match both the `html[...]` form and the element form, so the two
   families can transiently disagree.
2. **Appearance** is defined in ~18 CSS rulesets across ~9 locations in the
   ~8000-line `rich_render_css`. The two halves of the collapse contract —
   "hide the rail body" (`rendering.py:~4081`) and "narrow the strip + show the
   chip" (`rendering.py:~6765`) — live in **two different**
   `@media (min-width: 640px)` blocks **~2,680 lines apart**. Edit one, forget
   the other, and the strip narrows without the body hiding → the broken frame.
3. **The auto-collapse threshold** is hardcoded independently in
   `shell_prepaint.py` (numeric `innerWidth < 894`), `shell.py`
   (`matchMedia("(min-width: 894px)")`), and referenced again in CSS at
   different widths. JS pivots at **894**; the in-flow grid CSS pivots at
   **1280**. In the **894–1279** band, default-expanded rails therefore overlay
   the article with no reserved column — a live layout bug.

Every past fix patched one of these locations; the next change drifted a
different one out of sync. The architecture *guarantees* drift. Patching cannot
win; the concerns must be separated and each given one source.

## Goal

Rebuild the collapse mechanism so that:

- The collapsed rail is always a clean, single chevron chip (mirroring the right
  rail's good state), at every width ≥640, with no body leak and no duplicate
  controls.
- The mechanism has a **single source of truth per concern**, so it stops
  drifting.
- All foundation-contract behavior is preserved exactly (see "Foundation
  invariants").

Non-goals: removing the Context tile (foundation-required; see below), changing
the eight-tile command set, changing discovery/graph/search rails (fully
isolated), or restyling skins.

## Design: three concerns, one source each

The core idea: **separate State, Appearance, and Reflow, and give each exactly
one source.**

### 1. STATE — single source

- Collapse state lives **only** as `data-raya-course-map` /
  `data-raya-learning-rail` on `<html>`. The `main` and `nav`/`aside` mirror
  writes are deleted. Every collapse-relevant CSS selector keys off `html[...]`
  (verified compliant: nothing in the contract mandates element-level state
  mirrors; persistence and prepaint already read/write the `html` root).
- The **auto-collapse threshold (894px) and the effective-state derivation are
  code-generated once in Python** and interpolated as the **same literal string**
  into both emitted scripts (prepaint + runtime shell). Because the site is
  bundler-free and the two scripts are separate non-module files, a "shared
  constant" is only enforceable via a single emission source. A contract test
  greps both emitted scripts and asserts the identical threshold literal.
- **Accessibility is a derived effect of the single flag, applied by JS** (not a
  competing source): when the flag is `collapsed`, JS sets `inert` +
  `aria-hidden` on the rail body and disables focusable descendants / map link
  tab order. CSS cannot set these attributes, so JS remains responsible — but it
  reads the one `html` flag rather than computing state independently.

### 2. APPEARANCE — width-invariant, one co-located block

- The collapsed **chip** is defined in **one contiguous, commented CSS region**:
  narrow strip (`width: 2.75rem`), body `display: none` (guarantees the a11y
  hide), and the `2.5rem` chevron chip via the expand control's `::after`
  (`>` left / `<` right), with the mandated accessible opener names
  (`Expand course map` left; Context opener right).
- This collapsed appearance is **identical at every width ≥640** (contract
  groups "Desktop and medium-width" together for collapse and mandates no
  distinct collapsed look between them). This is where the two historically
  split rules finally live together.

### 3. REFLOW — width-conditional, minimal, token-driven

- A **single 894 boundary** governs layout, matching the auto-collapse threshold
  (closes the 894-vs-1280 dead zone):
  - **≥894 (approved geometry):** rails default expanded and are **in-flow grid
    columns**; collapsing a rail drops its column and the article reclaims the
    space.
  - **640–893 (article-first):** rails default collapsed to chips; an expanded
    rail here **overlays** the article (does not reserve a column), per the
    contract's "narrower article-first layout below that breakpoint."
- Grid columns are expressed with **tokens** (`0` / `15rem`) driven by the state
  attribute, so a state or column change touches one declaration rather than a
  per-combination table.
- Any width tuning that must remain (e.g. a wider article max-width at ≥1280) is
  layout-only and never re-encodes collapse state or the collapse threshold.

### Structure — shared chrome, separate bodies

- A shared `_render_rail_chrome(...)` helper emits the parts that actually
  recur and that kept breaking: the landmark wrapper, the header + collapse
  button, the expand chip/edge opener, the drawer backdrop, and the inert
  wiring — parameterized by `side`, labels, and opener name.
- Each rail keeps its **own body builder**, because the contract mandates
  asymmetric bodies:
  - **Left:** course search; exactly **eight** compact command tiles
    (Search, Graph, Practice, Tasks, Schedule, Context, Text size, OpenDyslexic)
    two-per-row when expanded; structural page position; locally filterable
    hierarchical map; scrollable tree; the **compact-preview hover/focus
    tooltip** (preserved).
  - **Right:** current-section context and page contents first (when heading
    anchors exist), then reading flow, summary/status, estimated time, tags,
    prerequisites, connections, prev/next; the context-chip.
- The rails are **chrome-symmetric, body-asymmetric.** The "mirror images by
  construction" framing is dropped as inaccurate; the opener names alone must
  differ.

### Phone regime (< 640) — asymmetric by contract

- **Left course map = modal drawer:** JS drawer state machine with visible
  chrome, backdrop, focus containment, background inertness, and scroll lock;
  Escape closes the drawer.
- **Right learning rail = always inline-expanded:** never drawered, chipped, or
  inert at phone width; remains visually and screen-reader available.
- **Escape is scoped by width/side:** at < 640 it only closes the map drawer or
  acts on visible collapse controls, and must **never** transition the right
  rail to an inert/hidden state (contract line 82).

## Foundation invariants (must remain true; asserted by tests)

- Left rail: exactly eight command tiles two-per-row when expanded, including
  Context; header presents `Course map` + `Hide map`, with **no Map control
  duplicated in the body**; edge opener named exactly `Expand course map`.
- Right rail: section-context-first ordering; Context edge opener; collapse only
  via explicit controls (its own header control **or** the left-rail Context
  command, `data-raya-learning-rail-toggle`).
- Collapsed content is inert, removed from keyboard navigation, and hidden from
  assistive navigation until restored.
- Phone: right rail stays inline-expanded and reachable; responsive change back
  from expanded geometry restores the accessible expanded state; Escape never
  creates an inert hidden right rail.
- Collapsed rails reserve no grid column (article reclaims space) at ≥894.
- SessionStorage keys unchanged: `raya:reader-shell:v1:<course_id>` (structural
  rail display pair) and `raya:course-map-branches:v1:<course_id>` (collapsed
  branch identifiers). Comfort keys `raya:open-dyslexic` / `raya:text-size`
  unchanged. No new storage, network, or cross-tab state.
- Discovery/graph/search rails untouched (separate `data-raya-discovery-*`
  system; zero coupling confirmed).

## What is erased vs preserved

**Erased:**

- The scattered collapsed-state CSS across the multiple breakpoint blocks in
  `rendering.py`, replaced by the single appearance region + token-driven reflow.
- The `main` and `nav`/`aside` state mirrors (`shell.py:492-494`, `1086-1088`;
  SSR attributes) — state on `<html>` only.
- Independent hardcoded 894 thresholds — replaced by one Python-emitted literal.

**Preserved (explicitly not dead):**

- `.raya-course-map-compact-preview` and its shell.py hover/focus **tooltip
  subsystem** (~30 lines; runtime-populated; test-asserted). Kept as-is or ported
  faithfully.
- The map drawer state machine (focus trap, scroll lock, backdrop).
- Per-branch disclosure, filter, tree, structural page position.

**Cascade guardrail:** the prepaint pre-hydration skeleton currently uses `#id`
selectors that outrank `html[data-...]` rules; they are contained only by the
`shell-prepaint="pending"` guard. Convert the skeleton's `#raya-course-map` /
`#raya-learning-rail` selectors to class selectors to remove the specificity
cliff, and add a test invariant: no `#id` selector may reference collapse state
outside the prepaint skeleton.

## Files touched

- `packages/static/src/raya_static/builder.py` — `_render_rail_chrome` helper;
  `_render_course_map` / `_render_learning_rail` become chrome caller + own body;
  remove `main`/rail SSR state mirrors; emit codegen'd threshold into scripts.
- `packages/static/src/raya_static/rendering.py` — replace scattered collapse CSS
  with the single appearance region + token-driven reflow; class-ify skeleton.
- `packages/static/src/raya_static/shell.py` — single `<html>` state write; read
  codegen'd threshold; derived inert/aria-hidden; width/side-scoped Escape.
- `packages/static/src/raya_static/shell_prepaint.py` — read the same codegen'd
  threshold; already `html`-only.
- Tests (see below).

## Testing and verification

- **TDD first.** Write the single-contract acceptance test before implementing:
  at 640 / 768 / 894 / 1280 / 1440px, each collapsible rail collapsed = exactly
  one control, a ~40px chevron chip, body `display:none` + absent from the a11y
  tree, left/right chip geometry identical, no horizontal overflow, no body leak.
  Watch it fail, then build to green.
- **Foundation invariants as assertions** (the list above), plus: eight tiles
  two-per-row expanded; accessible opener names; no reserved column when
  collapsed at ≥894; phone right rail inline-expanded and reachable; Escape does
  not inert the phone right rail; sessionStorage keys intact.
- **Preserve tested behaviors explicitly:** compact-preview tooltip
  (hidden/empty when expanded and when collapsed-without-focus; populated on
  hover/focus); 894-boundary reflow (in-flow ≥894 vs overlay 640–893);
  focus/inert sequencing across transitions.
- **Codegen invariant test:** both emitted scripts contain the identical
  threshold literal.
- **Real-browser validation** at each breakpoint via Chromium, plus an
  independent adversarial visual-validation subagent that must *see* clean
  symmetric chips before "done."
- **Test blast radius is real:** ~35–50 existing e2e / contract assertions
  encode the old fragmented behavior (element mirrors, per-width chip offsets,
  doubled selectors, four-breakpoint geometry). These are rewritten to the new
  contract deliberately, not deleted, so protected behaviors are re-asserted in
  their new form.
- **Gates:** `./scripts/check.sh` and `./scripts/check-render-debug.sh`;
  screenshots attached per repo convention.

## Risks and mitigations

- **Large change to a heavily-tested visual system.** Mitigation: TDD +
  per-breakpoint browser validation + adversarial visual check + the canonical
  gates; keep protected behaviors as explicit assertions.
- **Silently dropping a tested behavior during test rewrite** (the tooltip, the
  894 reflow split, inert sequencing). Mitigation: enumerate them up front (done
  above) and re-assert each in the new contract before deleting the old test.
- **JS-disabled degradation:** with no JS, prepaint never runs and the skeleton
  renders both rails as collapsed chips that cannot expand. This is pre-existing
  behavior, documented here, not introduced by this design.
- **Uncommitted stash collision:** `test_rail_symmetry.py` from an earlier
  session lives in `stash@{0}` (`stale-local-rail-session-2026-07-17`), not on
  disk. Reconcile/drop it before starting so it does not collide.

## Process

- Work on a feature branch off `new_rayalucaria` (do not commit to the default
  branch directly). The change is fully revertible.
- Deployment is unaffected structurally (GitHub Pages via `raya build docs`);
  the docs course re-renders from the same builder.

## Provenance

Root cause and scope were established by a code-exploration pass and validated by
three independent adversarial reviews (foundation compliance, architectural
robustness, feasibility/regression). Their material findings are folded into this
design: compact-preview is live (preserve); shared chrome not shared rail;
asymmetric phone regime; width/side-scoped Escape; JS-applied inert as a derived
effect; build-time codegen for the threshold; and unification of the 894/1280
boundary.
