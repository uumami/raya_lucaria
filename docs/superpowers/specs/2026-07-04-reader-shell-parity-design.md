---
id: reader-shell-parity-design
title: Reader Shell Parity Design
status: draft
workflow: superpowers
created: 2026-07-04
---
# Reader Shell Parity Design

## Context

The current reset branch has the correct foundation-first architecture and
static renderer boundaries, but the reader shell still has authority drift from
earlier UX iterations and legacy-main comparisons. The user approved the current
reader direction: generated reader pages should have no reader top bar so the
article can use more vertical projection space. Course navigation and reader
tools belong in the left course rail; page-local support belongs in the right
learning rail.

Legacy `main` remains historical UX evidence only. The implementation must not
restore Eleventy, Tailwind, Pagefind, Cytoscape, CDN renderers, old source
layouts, old generated JSON shapes, persistent sidebar/theme state, or browser
skin authority.

An adversarial design review found three blockers to resolve in this slice:

- `docs/foundation/20_learning_renderer_contract.md` still authorizes reader
  top-bar behavior even though foundation is the highest authority.
- Render-debug still requires `header.raya-top-command-bar` as a reader-shell
  selector.
- The `main-like-reader-shell` bridge branch contains useful accessibility
  behavior but also persists shell state in `sessionStorage`, which conflicts
  with the current storage policy.

## Goal

Make the accepted reader shell model explicit and testable:

```text
left course rail | article | right learning rail
```

Reader pages have no reader top bar. Discovery workspaces may keep their own
`.raya-discovery-command-bar` because they are generated tool pages, not
continuous reading pages.

## Non-Goals

- No onboarding or first-course tutorial work.
- No manifest schema or discovery-data contract expansion.
- No new Graph, Search, Practice, Tasks, or Schedule capabilities.
- No runtime skin switching or browser-side skin authority.
- No legacy `main` architecture or old source-layout restoration.
- No persisted shell, rail, drawer, search, filter, focus, or navigation state.

## Accepted Reader Model

Generated reader pages use the left course rail as the command center. The rail
contains course navigation, static workspace links, search handoff, reader focus
controls, context controls, text-size control, and OpenDyslexic control. The
article remains the primary continuous reading surface. The right learning rail
contains page-local support such as headings, key objects, reading flow, and
explicit page connections.

The reader shell must not render `.raya-top-command-bar` or
`header.raya-top-command-bar` on reader pages. Stale helper code or CSS may be
removed or quarantined after the contract is aligned so future work does not
accidentally restore the old reader top bar.

Discovery workspaces keep their command bar. Tests must explicitly distinguish
reader pages from discovery workspaces so a no-top-bar assertion does not remove
valid workspace chrome.

## Course Rail Behavior

Desktop reader pages use a structural three-column layout:

1. Left course rail.
2. Main article.
3. Right learning rail.

Collapsing the left course rail must give width back to the article. Collapsed
desktop mode becomes compact support chrome, not a full keyboard-heavy miniature
course map. The collapsed rail must keep an intentional expand affordance and a
current-page signal. Verbose map controls, workspace shortcuts, filters, and
hidden map content must not remain tabbable while visually hidden. Any compact
target that remains visible and reachable must have a useful accessible name.

The current page should remain easy to find in the course map after page load,
desktop expand, and mobile drawer open. This is volatile orientation only and
must not persist scroll, section expansion, or shell state.

## Mobile Drawer Behavior

On mobile and below the desktop shell breakpoint, the course map opens as an
intentional modal drawer. The implementation should port only the accessibility
parts from the `main-like-reader-shell` bridge branch:

- the open drawer has dialog-like semantics, including `role="dialog"`,
  `aria-modal`, and an accessible label or labelled-by target;
- keyboard focus is contained inside the drawer while it is open;
- Escape, backdrop click, and the close button close the drawer;
- focus returns to the opener after close when possible;
- background regions are unavailable to pointer, keyboard, and assistive
  navigation while the drawer is open;
- closed drawer contents are inert, hidden from assistive navigation, and not
  tabbable;
- resizing across the desktop breakpoint cleans up drawer state, inertness,
  scroll lock, and focus.

The implementation must not port any bridge `sessionStorage` or `localStorage`
shell-state restore/write behavior. Storage remains allowed only for documented
reader comfort preferences such as text size and OpenDyslexic.

## Foundation And Documentation Updates

The foundation must be updated before lower surfaces are treated as accepted.
`docs/foundation/20_learning_renderer_contract.md` should state that reader
pages have no reader top bar, reader commands live in the left course rail, and
discovery workspaces may keep command bars.

Role docs in English and Spanish must be updated where they describe top-bar
reader behavior. Student-facing docs should describe the left course rail, the
article-first reading surface, the right learning rail, and the mobile course
map drawer. Agent/contributor docs should state that reader pages do not render
top bars and that discovery command bars are separate generated workspace
chrome.

## Render-Debug Contract

Render-debug should validate the accepted reader shell, not the stale top-bar
model. Reader shell checks should require the course map, article, right
learning rail, and left-rail course tools. They should not require
`header.raya-top-command-bar` on reader pages.

Render-debug tests should still verify discovery command bars on generated
Search, Graph, Practice, Tasks, and Schedule pages where appropriate.

## Testing

Focused tests should be written against behavior:

- Reader contract tests assert reader pages do not emit `.raya-top-command-bar`
  and do emit course-map tools inside the left rail.
- Discovery contract tests assert Search, Graph, Practice, Tasks, and Schedule
  still emit `.raya-discovery-command-bar`.
- Documentation tests or hygiene checks assert foundation and role docs do not
  describe reader-page top-bar behavior.
- Render-debug report tests update required reader selectors away from top-bar
  selectors.
- Desktop Playwright tests verify left rail, article, and right rail are ordered
  without overlap, rail collapse expands article width, and no horizontal
  overflow appears.
- Mobile Playwright tests verify closed drawer inertness, open drawer modal
  behavior, focus containment, Escape/backdrop/close behavior, focus
  restoration, and breakpoint cleanup.
- Storage guard tests verify no forbidden shell state is written to
  `localStorage`, `sessionStorage`, IndexedDB, cookies, or URL state.

## Verification

Focused verification should run first:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q \
  tests/contracts/test_static_builder.py \
  tests/e2e/test_render_debug_report.py \
  tests/e2e/test_render_debug_parity_gate.py \
  tests/e2e/test_preview_static_read_path.py
```

Final verification for implementation should run sequentially:

```bash
./scripts/check-render-debug.sh
./scripts/check.sh
./scripts/check-docker.sh
```

`./scripts/smoke-test.sh` should be run as a separate external-course evidence
gate if the implementation changes course initialization, external-course
builds, artifact inspection, or publishing-related behavior. This slice is not
expected to touch those surfaces.

## Adversarial Review Gate

Before implementation planning, this design must include the findings from the
adversarial design review. During implementation, request another adversarial
review after the main behavior/test patch and before claiming completion.

The reviewer should specifically check:

- no reader top bar applies only to reader pages;
- discovery command bars remain valid;
- no old-main architecture or CDN/browser renderer dependency was restored;
- mobile drawer behavior is actually modal/inert, not merely styled that way;
- collapsed rail hidden controls are not tabbable;
- no forbidden storage is added;
- render-debug validates real reader shell selectors;
- tests prove behavior rather than CSS trivia.

## Acceptance Criteria

- Foundation, role docs, render-debug, renderer code, and tests agree that
  reader pages have no top bar.
- Discovery workspace command bars still render and are tested as valid.
- Mobile drawer behavior is accessible and volatile.
- Collapsed desktop course rail gives article width back and does not expose
  hidden controls in the tab order.
- No forbidden storage or legacy architecture is introduced.
- Focused tests, render-debug, host check, and Docker check pass after
  implementation.

## Self-Review

- Placeholder scan: no TBD/TODO placeholders remain.
- Internal consistency: the design consistently treats no-top-bar as a
  reader-page-only contract and preserves discovery workspace command bars.
- Scope check: the work is limited to reader-shell authority, accessibility,
  render-debug, and focused tests; onboarding, data contracts, new capabilities,
  and skin switching remain out of scope.
- Ambiguity check: collapsed desktop map behavior is explicitly compact support
  chrome, not a full keyboard-heavy miniature map, and bridge storage behavior
  is explicitly rejected.
