# Hierarchical Course Map Design

## Context

The old `main` branch used an always-available left sidebar with nested course navigation, explicit expand/collapse controls, active-page ancestry, inline search, and compact visual affordances. The reset renderer already has a static course shell with a collapsible course map, a top command bar, local search and graph pages, and local reader controls. The current course map is still flat, so multi-unit courses lose the structural affordance that made the older UI easier to scan.

## Decision

Adapt the old sidebar's useful navigation behavior into the reset course shell by rendering the course map as a static hierarchy from `ContentModel.children_by_parent`. Keep the reset architecture:

- no Eleventy, Tailwind, Pagefind, Cytoscape, CDN, external font, fetch, or XHR dependency;
- no persistent course-map state;
- no inferred learning progress or recommendations;
- source-authored page order, page IDs, hierarchy labels, and generated artifact data remain authoritative.

## Behavior

The rendered course map will:

- show a local filter field inside the expanded course map;
- render nested `<ol>` lists that follow the existing content hierarchy;
- mark current-page ancestors with `data-raya-map-active="ancestor"`;
- render child groups expanded by default so the structure is visible before any interaction;
- allow readers to toggle child groups with buttons that update `aria-expanded`;
- filter visible links by page label/title and automatically reveal matching ancestor groups while a filter is active;
- keep collapsed compact-map mode operable through existing numbered link markers.

Filtering is local DOM behavior over already-rendered navigation labels. It does not read artifact JSON, scrape prose, fetch search indexes, or persist query state.

## Out Of Scope

This slice does not change the separate `_raya/search/` page, graph page layouts, graph tooltips, page recommendations, personal progress, or course skin configuration. Those remain separate UX fusion slices.

## Testing

Add contract tests for hierarchical HTML structure, filter controls, active ancestor metadata, and local shell resource tokens. Add browser tests that:

- collapse and expand a nested map group;
- filter the course map and verify matching pages remain visible;
- clear the filter and verify the full map returns;
- prove no network requests occur during map toggles/filtering;
- verify no horizontal overflow on representative desktop/mobile viewports.

Update foundation and role docs in English and Spanish so professors, students, contributors, and agents understand that course-map hierarchy is static structure, not personal progress.
