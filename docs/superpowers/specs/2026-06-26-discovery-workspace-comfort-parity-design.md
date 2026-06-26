# Discovery Workspace Comfort Parity Design

## Goal

Bring Search, Practice, Tasks, and Schedule closer to the Graph workspace's
orientation quality without changing their static contracts. Each discovery
workspace should show an immediate structural overview, stable reset language,
and current static scope before the three-column controls/results/context grid.

## Authority

This design follows `docs/foundation/20_learning_renderer_contract.md` and the
legacy convergence audit in `docs/superpowers/legacy-ux-convergence-audit.md`.
It does not copy legacy Eleventy, Tailwind, browser storage, CDN graph/runtime
libraries, scoring, learner progress, or browser-side rendering behavior.

## Approach

Add a shared generated orientation band to the four discovery workspaces. The
band is static HTML rendered by `packages/static/src/raya_static/builder.py` and
styled by `packages/static/src/raya_static/rendering.py`. It will use the same
visual grammar as the Graph orientation band: compact summary text, metadata
cells, and action links. Workspace JavaScript continues to own transient filter
state and updates the existing per-workspace summary and page-focus notice.

The band is intentionally not a dynamic dashboard. It shows generated course
structure only: total records, primary record family, source scope, reset path,
and links to related local workspaces. Dynamic visible-count updates remain in
the existing control panel `data-raya-*-summary-count` elements.

## Workspace Content

- Search shows total public pages, searchable section anchors, source scope
  `public page metadata and public article text`, reset path `Clear or Escape`,
  and local handoffs to Graph, Practice, Tasks, and Schedule.
- Practice shows total accepted official objects, object type count, source
  scope `accepted official objects`, reset path `Clear or Escape`, and local
  handoffs to Search, Graph, Tasks, and Schedule.
- Tasks shows total accepted task-family objects, object type count, source
  scope `accepted assignments, exams, projects, and tasks`, reset path `Clear or
  Escape`, and local handoffs to Search, Graph, Practice, and Schedule.
- Schedule shows total dated task-family objects, dated event type count, source
  scope `authored due and available dates`, reset path `Clear or Escape`, and
  local handoffs to Search, Graph, Practice, and Tasks.

## Constraints

- No `localStorage`, `sessionStorage`, fetch/XHR, external requests, service
  workers, or runtime data loading.
- No progress, mastery, recommendation, ranking, personalization, grading, or
  submission language.
- The overview must fit desktop and mobile without horizontal overflow.
- The overview must not duplicate hidden answer/support content.
- Existing keyboard behavior, filters, URL-only page focus, and result/context
  panels must remain intact.

## Testing

Use TDD in `tests/contracts/test_static_builder.py` before changing production
code. Focused tests assert the four generated pages include the shared overview
classes, structural metadata, local action links, and forbidden runtime/state
tokens remain absent. Then run focused contract tests and `./scripts/check.sh`
before commit/push.
