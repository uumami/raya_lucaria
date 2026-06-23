# Connections Rail Design

## Context

The current Glintstone renderer already generates explicit graph data from authored
course order, source links, stable IDs, and prerequisites. The learning rail can
show prerequisites and linked pages, but the linked-pages panel is low-signal:
readers must expand it before they know how many relationships exist or what type
they are.

Legacy `main` used a more visible graph-oriented UX: compact controls, grouped
graph context, counts, and quick jumps into a graph surface. The useful idea is
not the old Eleventy/Cytoscape/CDN stack. The useful idea is making local
connections scannable while preserving the reset renderer's static artifact model.

## Goal

Replace the low-signal `Linked pages` rail affordance with a static
`Connections` panel that summarizes explicit page relationships, separates
outgoing and incoming links, shows counts, and keeps graph-focus actions one click
away.

## Requirements

- Use only current build-time `ContentModel` and generated graph context.
- Show a compact count summary before relationship lists.
- Separate outgoing source links from incoming backlinks.
- Preserve relative deployment-neutral links for page links and graph-focus links.
- Preserve existing rail collapse behavior, `aria-expanded`, `aria-hidden`, and
  inert/tabindex focus protection.
- Use static HTML/CSS only. Do not add runtime fetches, CDN resources, browser-side
  graph data loading, learner progress, recommendations, mastery state, or
  localStorage for graph/connection state.
- Keep the old prerequisite panel separate for now. Prerequisites are a distinct
  authored relationship and already have a dedicated panel.

## Design

The builder keeps using `_graph_context_by_page()` as the authoritative source for
incoming and outgoing explicit content edges. `_render_linked_pages_rail()` becomes
the public renderer for a `Connections` panel, preserving its call sites and test
coverage while changing the user-facing title and body structure.

The panel body starts with a small summary row:

```html
<p class="raya-rail-connection-summary">
  <span><strong>3</strong> from this page</span>
  <span><strong>2</strong> links here</span>
</p>
```

Each section uses a labelled header with a count chip:

```html
<div class="raya-rail-connection-heading">
  <h3>From this page</h3>
  <span class="raya-rail-count">3</span>
</div>
```

Each linked item keeps the existing page link plus a graph-focus pill. The graph
pill remains an ordinary relative link into `_raya/graph/index.html?page=<id>`.

## Accessibility And UX

The panel remains collapsed by default, so it does not crowd the rail. The
collapsed title changes from `Linked pages` to `Connections`, and the summary
inside the body gives readers immediate structure after expansion. Existing shell
JavaScript continues to manage collapse state and focus exclusion. No hidden links
are keyboard-reachable while the panel is collapsed.

The panel is intentionally not personalized. Counts describe authored static
relationships, not learner progress or recommendations.

## Testing

Contract tests must assert:

- the linked-pages rail is now titled `Connections`;
- the panel includes a static summary with outgoing and incoming counts;
- section headers expose count chips;
- existing page and graph-focus links remain relative;
- no learner-state wording appears.

Browser tests must assert:

- the panel is collapsed by default with focus protection intact;
- after expansion the summary and count chips are visible;
- the graph-focus link still opens the static graph detail for the selected page;
- no horizontal overflow is introduced on desktop.

## Out Of Scope

- Merging prerequisites into the same panel.
- Graph hover previews inside the rail.
- Personalized progress, recommendations, or adaptive next-step labels.
- Runtime graph fetching or external graph libraries.
