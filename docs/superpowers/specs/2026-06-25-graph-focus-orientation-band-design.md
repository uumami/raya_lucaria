# Graph Focus Orientation Band Design

## Context

The current reset graph already has the important mechanics from the old
`main` branch rebuilt under Glintstone constraints: local SVG rendering,
embedded graph data, fuzzy search, layout modes, filters, collapsible panels,
inspection previews, selected-page details, relationship chips, walkthroughs,
URL state, fit/zoom/pan/reset, and no external graph library or runtime graph
fetch.

The remaining learner UX gap is orientation. A student can arrive at Graph from
`?page=<page-id>`, select a page, hide panels, change filters, or focus a
neighborhood, but the most visible summary of "what am I looking at?" is split
between terse status text, the inspector, and the closed debug state
disclosure. The old graph had a visible status count; this slice adapts that
value into a richer, reset-native orientation band.

## Decision

Add a compact graph focus orientation band near the graph controls/status area.
It is normal student-facing UI, not debug output. It summarizes the current
static graph view using only already embedded public graph data and transient
DOM state.

The band shows:

- visible page and relationship counts;
- current layout label;
- selected page title or `None`;
- URL page focus title when present;
- active search text when present;
- active hidden group and hidden relationship summaries;
- whether selected-neighborhood focus is on;
- structural actions for the selected page: `Open page`, `Focus neighborhood`
  or `Show full graph`, and `Clear selection`.

The actions reuse existing selected-page behavior. `Open page` follows the
selected page's local URL. `Focus neighborhood` toggles the existing
non-persistent neighborhood focus. `Clear selection` clears selected page state
without clearing search/layout/filter state.

## Relationship Detail Consistency

While adding the band, align the selected-page incoming/outgoing detail lists
with the relationship chips and walkthrough. The lists should be derived from
the same explicit generated edge set and include visible relationship kinds
such as `navigation`, `parent`, `content`, and `prerequisite`, not only the
legacy backlink subset. This avoids a student seeing relationship counts or
chips that do not match the visible connected-page lists.

Each relationship list item remains a normal local link plus an existing graph
focus control when useful. Relationship labels are structural, for example
`Navigation`, `Parent`, `Content`, and `Prerequisite`.

## Boundaries

- No new course source syntax, schema, artifact data file, or graph payload
  shape beyond optional rendering scaffolding.
- No external graph library, CDN, runtime `fetch`, XHR, worker, service worker,
  browser-side MathJax, or graph-state browser storage.
- No progress, mastery, recommendation, ranking, completion, importance,
  personalization, or adaptive wording.
- No replacement of the existing debug/share disclosure. The band is compact
  orientation; the disclosure remains the copyable state/debug surface.
- No new graph mode. Use current selection, search, layout, filters, focus mode,
  and neighborhood focus behavior.

## Implementation Shape

- `packages/static/src/raya_static/builder.py` renders orientation-band
  scaffolding in the graph surface with stable `data-raya-graph-orientation-*`
  attributes and action controls.
- `packages/static/src/raya_static/graph.py` gathers current graph state after
  each render and updates the orientation fields and action controls.
- `graph.py` changes selected-page incoming/outgoing rendering to use explicit
  generated edges grouped by direction and kind, matching relationship chips and
  walkthrough semantics.
- `packages/static/src/raya_static/rendering.py` styles the band as a compact,
  responsive, high-scan region that works with existing skins.
- `docs/foundation/20_learning_renderer_contract.md` records the compact graph
  orientation band and relationship-list consistency as static structural graph
  affordances.
- English and Spanish student and agent role docs mention the band as
  structural graph context and warn agents not to treat it as learner progress.

## Accessibility And UX

The band is a named region with concise text and normal links/buttons. It uses
existing graph controls and selected-page state rather than moving focus on
render. It must remain usable when one or both side panels are collapsed, and it
must not introduce mobile horizontal overflow.

Action controls are hidden or disabled when no selected page exists. The band
updates politely without rewriting long live text on every hover. It should
help students recover orientation after filtering or panel collapse, especially
on desktop where the graph workspace is dense.

## Testing

Focused tests should prove:

- generated graph HTML includes the orientation band scaffolding;
- local `graph.js` updates orientation fields without using storage, fetch, or
  external requests;
- browser graph view initially shows visible page and relationship counts;
- selecting a page updates the selected-page title and enables orientation
  actions;
- toggling selected-neighborhood focus changes the band and can return to the
  full graph;
- filtering relationship kinds or groups updates the hidden-filter summary;
- incoming/outgoing detail lists agree with relationship chips and walkthrough
  over explicit edge kinds;
- desktop and mobile checks do not show horizontal overflow.

Run focused graph tests first, then `./scripts/check-render-debug.sh`, then
`./scripts/check.sh`, then `./scripts/check-docker.sh` sequentially before
claiming the slice works.

## Self-Review

- Placeholder scan: no TBD/TODO placeholders remain.
- Scope check: one graph UX slice plus directly related relationship-list
  consistency; no schema or graph payload redesign.
- Ambiguity check: the band is structural graph context, not progress,
  recommendation, ranking, mastery, or personalization.
