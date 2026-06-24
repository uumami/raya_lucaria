# Graph Orientation Controls Design

## Context

The old `main` branch graph UX had a dense toolbar, layout switcher, fit/reset, expansion, fuzzy search, group chips, hover neighborhoods, and click navigation. The current `new_rayalucaria` renderer already rebuilt the important graph behavior under current contracts: local SVG rendering, embedded public graph payload, deterministic layouts, group filters, search spotlight, selected-neighborhood focus, collapsible panels, pan/zoom, keyboard inspection, and no runtime fetch, CDN, browser-side MathJax, or persistent graph state.

The remaining issue is scanability. The graph controls are text-heavy, and the selected-page inspector underuses public metadata that already exists in the graph payload. A student can inspect a node, but the page does not yet present a compact orientation card with course-order neighbors and local workspace handoffs.

## Decision

Build a narrow graph orientation pass:

1. Add a compact graph toolbar grouped into search/layout, viewport controls, pan controls, and reset/expand controls. Keep existing element IDs and accessible names so behavior and tests remain stable.
2. Add a selected-page sequence strip to the graph inspector using existing `previous_url` and `next_url` payload fields. It shows `Previous`, `Selected`, and `Next` as course-order structure, not a recommendation or progress cue.
3. Add graph detail handoffs to Tasks and Schedule when the selected page has accepted public task-family metadata. These are static workspace links derived at build time and hidden when no relevant accepted objects exist.
4. Keep selected-page metadata structural and compact while adding clearer sequence and workspace action sections without exposing private paths or learner-state language.

## Boundaries

- No new source contract or artifact data file.
- No external graph library, CDN, runtime fetch, XHR, worker, service worker, browser-side MathJax, or graph-state persistence.
- No personal progress, recommendation, importance rank, mastery, completion, reminder, overdue, or adaptive wording.
- The graph remains a reader-facing static view over generated artifact data. `data/graph.json` and generated embedded payload remain derived surfaces, not source truth.

## Implementation Shape

- Extend `_public_discovery_page_payload(...)` or graph-only payload composition to include optional `tasks_url` and `schedule_url` for pages that own accepted public task-family objects and accepted dated task-family objects.
- Update `_render_graph_surface(...)` to group controls with stable CSS classes and add detail scaffolding for sequence and task/schedule actions.
- Update `graph.py` `renderDetail()` to populate sequence links and optional Tasks/Schedule links from the selected node.
- Update `rendering.py` graph selectors for compact toolbar groups and richer detail card layout.
- Update foundation and role docs only where needed to record that graph selected-page details may show course-order neighbors and local workspace handoffs as structural discovery cues.

## Verification

Focused tests should prove:

- Graph HTML still uses local resources only and no storage/fetch APIs.
- Graph payload includes only public fields, including optional task/schedule handoff URLs.
- Selected detail panel renders Previous/Selected/Next and static workspace handoffs.
- Handoffs hide when no accepted relevant object exists.
- The compact toolbar remains keyboard-reachable, does not overflow desktop/mobile widths, and keeps existing graph behavior.
