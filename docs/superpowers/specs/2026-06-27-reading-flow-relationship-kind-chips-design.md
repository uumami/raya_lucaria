# Reading Flow Relationship Kind Chips Design

## Context

The Graph workspace now explains explicit relationship kinds and lets readers
inspect SVG relationship lines directly. The reader-facing right rail still
compresses connected pages in the `Reading flow` panel to direction plus title.
That keeps the rail compact, but it hides the relationship kind cue that the
graph already uses.

## Decision

Add compact relationship-kind chips to existing `Reading flow` connected-page
links. Each connected-page chip shows:

- direction: `From this page` or `Links here`;
- kind: the existing generated relationship kind label such as `Content`;
- linked page title.

The rail continues to use current `page_graph_context` data only. This slice
does not broaden the graph context beyond the explicit content links already
provided to the reader rail.

## Behavior

The generated link keeps its existing destination. The link gains
`data-raya-reading-flow-kind="<kind>"` for testing and inspection, and a compact
visible `.raya-reading-flow-connection-kind` label beside the existing direction
label. The panel remains expanded and compact in the first viewport.

## Constraints

- No new source fields, artifact data, schema, or browser fetches.
- No storage, progress, mastery, recommendation, ranking, or related-practice
  language.
- No duplicate `Connections` or `Sequence` rail panels.
- No graph payload or Graph workspace behavior changes.

## Tests

Focused tests cover:

- generated reader rail HTML includes direction, relationship kind, title, and
  `data-raya-reading-flow-kind`;
- the rail keeps graph handoff links and avoids learner-state/storage/fetch
  language;
- browser layout keeps the Reading Flow panel visible and compact in the first
  desktop viewport with visible kind, direction, and title elements.

## Self-Review

The design is scoped to one user-visible rail affordance and uses existing
static graph context. It aligns the reader rail with graph relationship
comprehension without changing data authority or adding dynamic state.
