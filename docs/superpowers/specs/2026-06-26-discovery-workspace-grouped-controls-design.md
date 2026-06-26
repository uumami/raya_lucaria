# Discovery Workspace Grouped Controls Design

## Goal

Make Search, Practice, Tasks, and Schedule control panels easier to scan by
borrowing Graph's grouped-control organization, while preserving the current
static renderer contracts and generated data flow.

## Authority

This design follows `docs/foundation/20_learning_renderer_contract.md` and the
legacy convergence audit in `docs/superpowers/legacy-ux-convergence-audit.md`.
Discovery workspaces may show controls, results, context panels, local comfort
controls, and compact page-focus notices. They must not depend on the course
shell script, runtime fetches, external resources, browser-side rendering,
stored graph/search state, or learner-progress language.

## Approach

Keep the existing page structure and JavaScript-owned behavior, but group
controls into explicit static sections inside each left control panel. The
markup uses shared `.raya-discovery-control-group` fieldsets with visible
legends. Existing IDs, data attributes, filter button containers, clear buttons,
and live-status nodes remain in place so Search, Practice, Tasks, and Schedule
scripts continue to work without data-flow changes.

The existing dynamic count and URL page-focus notice move into a shared
`.raya-discovery-control-state` region below the controls. This makes the
current static workspace context visually distinct from the controls without
turning it into learner state.

## Workspace Groups

- Search: `Query` and `Reset`.
- Practice: `Query`, `Object type`, and `Reset`.
- Tasks: `Query`, `Sort`, `Object type`, and `Reset`.
- Schedule: `Query`, `Date kind`, `Object type`, and `Reset`.

## Constraints

- No changes to embedded payload shape, generated JSON, scripts, URL query
  semantics, result cards, context panels, or graph handoff URLs.
- No `localStorage`, `sessionStorage`, fetch/XHR, external requests, service
  workers, progress, mastery, recommendation, ranking, grading, submission, or
  personalization language.
- Group styling must be compact on desktop side panels and must not create
  mobile horizontal overflow.
- Print rules must continue to hide workspace controls.

## Testing

Use TDD in `tests/contracts/test_static_builder.py` before production changes.
Focused tests assert each workspace emits grouped controls, visible legends,
the shared context-state wrapper, and the original IDs/data hooks required by
local scripts. Then run the focused four-workspace contract tests and
`./scripts/check.sh` before commit/push.
