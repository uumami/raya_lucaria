# Discovery First Viewport Design

## Goal

Search, Practice, Tasks, and Schedule should show usable controls and results
earlier in the first viewport while keeping their static orientation and quick
guide content available.

## Current Problem

The discovery workspaces currently render in this order:

1. command bar;
2. page header;
3. overview band;
4. quick guide card grid;
5. actual controls, results, and context panels.

That preserves useful learning guidance, but it makes the first viewport feel
like an introduction page instead of a work surface. The user has to scroll
past two orientation bands before reaching the tool.

## Design

Move the actual workspace directly after the compact page header. Render the
overview and quick guide after the workspace as support material. Keep the
overview compact and convert the quick guide into a native collapsed `details`
element. The summary remains visible as a small "Quick guide" row, and opening
it reveals the existing four guide cards.

This makes the page act like a tool first and a guide second. Students can start
searching, filtering, and scanning immediately, while professors and agents can
still inspect the explanatory support material on the same static page.

The workspace layout stays static and local:

- no persisted browser state;
- no `localStorage` or `sessionStorage`;
- no external requests;
- no JavaScript dependency for the guide collapse;
- no progress, mastery, ranking, recommendation, grading, or submission
  language.

## Implementation Boundaries

- `packages/static/src/raya_static/builder.py` owns the generated order and
  quick-guide markup.
- `packages/static/src/raya_static/rendering.py` owns density, spacing, and
  responsive styling.
- Contract tests protect the generated native collapsed guide markup.
- Browser tests prove the guide remains available, has no overflow, and the
  actual workspace begins inside the first viewport on desktop and mobile.

## Testing

Use TDD:

1. contract tests fail until the guide is generated as `details` with a
   visible summary and closed default;
2. browser tests fail until workspace top position is within the viewport and
   the workspace appears before support material;
3. implementation changes are the minimum markup/CSS required to pass.
