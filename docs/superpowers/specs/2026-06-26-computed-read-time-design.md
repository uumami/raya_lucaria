# Computed Read Time Design

## Context

The legacy `main` branch showed an automatic reading-time hint for pages. The
reset renderer already supports authored `estimated_time`, but pages without
that metadata had no comparable static orientation cue.

## Decision

When a page has authored `estimated_time`, render it unchanged as `Estimated
time`. When it is absent, compute a display-only `Estimated read time` during
build from public rendered article text and show it in the Page brief and right
learning rail.

The computed value is approximate structural orientation. It is not progress,
completion, mastery, recommendation, grading, personalization, analytics, or
runtime learner state.

## Design

The builder computes the fallback after rendering public article HTML and
extracting public article search text. This keeps the estimate aligned with the
student-visible article instead of private source/support paths or generated
artifact internals.

The fallback uses a simple words-per-minute estimate and displays `N min read`.
Authored `estimated_time` always takes precedence so course teams can override
the generic estimate with a deliberate course-specific value.

## Constraints

- No source schema change.
- No browser-side computation.
- No storage, fetch, external requests, analytics, progress, mastery, or
  recommendation language.
- No change to generated `estimated_time` metadata semantics.

## Testing

Contract tests cover a page without authored `estimated_time` and assert that
the Page brief and right rail show `Estimated read time` with the computed value.
Existing authored metadata tests continue to assert authored `estimated_time`
renders as `Estimated time`.

## Documentation

The foundation renderer contract and English/Spanish role guides describe the
authored-vs-computed distinction and the non-progress semantics.

