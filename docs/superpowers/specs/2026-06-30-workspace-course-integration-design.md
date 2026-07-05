---
id: workspace-course-integration-design
title: Workspace Course Integration Design
status: draft
workflow: superpowers
created: 2026-06-30
---
# Workspace Course Integration Design

## Context

The Course-first UX goal now points to **Workspace course integration**. The
static renderer already publishes Search, Graph, Practice, Tasks, and Schedule
workspaces with shared discovery chrome, local scripts, cross-workspace links,
course-rail navigation, and URL-only `?page=<page-id>` handoffs. The remaining
course-first gap is first-viewport orientation: a reader who lands on a
workspace from a page handoff sees the page focus in tool-specific controls or
the course rail, but the main workspace body still starts as a tool page rather
than a course-owned page handoff.

This loop keeps the work scoped to the current Glintstone static renderer. It
does not add schema fields, dynamic study state, browser storage, external
requests, recommendation language, graph data changes, or new workspace
features.

## Chosen Approach

Add a shared **focused course page strip** near the top of every generated
discovery workspace. It appears only for a valid URL handoff such as
`?page=reader-ux`, names the focused public page, links back to that page, links
to the same page focus across Search, Graph, Practice, Tasks, and Schedule, and
offers a plain clear link back to the current workspace without the query.

The strip is generated as static HTML with no public page data beyond existing
course-rail links and existing relative workspace paths. The existing
`discovery.js` script reads URL state, validates it against already rendered
public course-page links, fills the strip, and keeps it hidden for missing or
invalid page IDs. This mirrors the existing rail page-focus behavior and keeps
page focus as structural URL state only.

## Alternatives Considered

1. **Shared focus strip in every workspace.** Recommended. It makes the
   course-to-tool-to-page relationship visible in the first viewport, reuses
   existing public page IDs and links, and can be tested with one browser loop
   across all workspaces.
2. **Only improve each tool-specific page-focus notice.** Lower risk but too
   buried. Search, Practice, Tasks, and Schedule notices live inside control
   panels, and Graph has separate orientation readouts, so the course handoff
   remains inconsistent.
3. **Expand the course rail into the primary workspace orientation surface.**
   Too broad for this loop. The rail already works and has collapse behavior;
   making it visually primary risks letting chrome outrank the workspace result
   surface.

## Surface, Fixture, Assertion, Command

- **Surface:** shared discovery workspace chrome for generated Search, Graph,
  Practice, Tasks, and Schedule pages.
- **Fixture/page:** `examples/courses/render-fixture`, starting from
  `_raya/search/index.html?page=reader-ux`,
  `_raya/graph/index.html?page=reader-ux`,
  `_raya/practice/index.html?page=reader-ux`,
  `_raya/tasks/index.html?page=reader-ux`, and
  `_raya/schedule/index.html?page=reader-ux`.
- **Measurable UX assertion:** a valid page handoff shows one visible
  first-viewport focused course page strip before the workspace shell on all
  five workspaces; the strip names `Projection Residuals`, links back to
  `reader-ux/index.html`, provides same-page-focus handoffs to all five
  workspaces, provides a clear link to the current workspace, remains hidden for
  missing or invalid page focus, does not write storage, and does not overflow
  desktop or mobile viewports.
- **First verification command:**

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q tests/e2e/test_preview_static_read_path.py::test_discovery_workspaces_show_shared_page_focus_strip
```

Expected RED before implementation: the new browser assertion fails because
`[data-raya-discovery-focus-strip]` does not exist or remains hidden.

## Behavior

For a valid `?page=<page-id>`:

- the strip appears below the workspace header and before the workspace shell;
- the visible heading is `Focused course page`;
- the page title text comes from the existing rendered course-page link for
  that public page ID;
- `Open page` returns to the rendered page using the existing relative page
  link;
- `Search`, `Graph`, `Practice`, `Tasks`, and `Schedule` links preserve the
  same page ID as URL query state;
- `Clear focus` links to the current workspace `index.html` without `?page`;
- no localStorage or sessionStorage key is written.

For missing or invalid page focus:

- the strip stays hidden;
- action links keep inert `href="#"` placeholders while hidden;
- no storage, fetch, external request, or learner-state wording appears.

## Implementation Notes

- Add one helper in `packages/static/src/raya_static/builder.py`, likely near
  `_render_discovery_course_rail`, to render the shared hidden focus strip.
- Insert the helper after each discovery workspace header and before
  `.raya-discovery-workspace-shell` in Search, Graph, Practice, Tasks, and
  Schedule.
- Extend `packages/static/src/raya_static/discovery.py` so the same validated
  `activeRailPage` path that currently updates the course rail also updates the
  shared strip.
- Add compact CSS in `packages/static/src/raya_static/rendering.py` for the
  strip, its actions, mobile wrapping, hidden state, focus-visible outlines,
  and no-overflow behavior.
- Keep all text structural: page focus, course page, workspace, clear. Do not
  use progress, mastery, recommended, personalized, score, grade, submit, due
  state, or learner-state wording.

## Testing

The first failing test is a Playwright static-read-path test across desktop and
mobile viewports. It should:

- load each workspace with `?page=reader-ux`;
- assert the strip is visible and appears before the workspace shell;
- assert the title is `Projection Residuals`;
- assert action links are relative, preserve `page=reader-ux`, and do not point
  to private/source paths;
- assert `Clear focus` targets the current workspace without a query;
- assert no localStorage/sessionStorage keys are written;
- assert no horizontal overflow;
- load one invalid page focus and assert the strip remains hidden.

Focused GREEN should run that new test plus the existing discovery command bar,
course rail, and page-focus tests. Final visible-renderer gates remain
`./scripts/check-render-debug.sh`, `./scripts/check.sh`, and
`./scripts/check-docker.sh` sequentially after review and role-doc impact
checks.

## Role And Tutorial Impact

This is visible learner, professor, contributor, and agent behavior because the
generated workspaces now expose page handoff context more prominently. Update
the English and Spanish role docs if they do not already describe page-focused
workspace handoffs in a way that matches the new strip. If existing pages are
already current, record exact checked paths and no-impact rationale in the
plan and goal ledger.

## Self-Review

- No placeholder requirements remain.
- The design is scoped to one shared renderer affordance.
- The strip is generated from existing public page/workspace links and URL
  state, so it does not change source or artifact authority.
- The design preserves static-only behavior, avoids storage and external
  requests, and does not introduce learner-state semantics.
