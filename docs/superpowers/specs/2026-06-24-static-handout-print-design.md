# Static Handout Print Design

## Purpose

Generated Glintstone pages should be useful when printed or saved to PDF for review, annotation, and offline study. The browser reader shell can remain dense and interactive, but print output must become a clean handout that centers authored learning content and avoids wasting paper on navigation chrome.

## Scope

This loop adds print-specific rendering rules for reader pages and discovery workspaces. It does not add browser-side rendering, external assets, accounts, progress state, recommendation language, or new source-course syntax.

## Design

The static stylesheet will include a dedicated `@media print` section. In print, course command bars, course maps, learning rails, graph/search/practice controls, inspectors, filters, and transient workspace panels are hidden. Main article content, page brief, breadcrumbs, sequence links, official practice, numbered objects, static environments, callouts, tables, code, local images, and build-time MathJax remain printable.

Printed content uses white backgrounds, black text, no box shadows, normal page flow, full-width article layout, visible link URLs for external links, and page-break rules that avoid splitting figures, tables, code blocks, official objects, numbered objects, and static environments when possible. Native support disclosures such as hints, solutions, and answers are opened visually in print through CSS so a static handout can include the explanation without requiring interaction.

Discovery pages print as compact reference handouts. Search, Graph, and Practice keep their headings and result lists where useful, but hide interactive controls and graph canvases that do not translate well to paper. This preserves the static contract: print is another view of the already generated artifact, not a dynamic export feature.

## Documentation And Tests

The foundation renderer contract will name print/PDF handouts as a static reader view. Role docs in English and Spanish will explain that printed handouts are local artifact output, not canonical source truth and not learner state.

Tests will cover:

- generated CSS includes the print media rules and hides shell chrome only in print;
- browser print emulation keeps the article visible and hides command bars/maps/rails;
- MathJax, code, tables, official practice, and static environments remain present in print;
- no external requests, storage calls, browser-side MathJax conversion, or source/private paths are introduced.

## Self-Review

No placeholders remain. The design is intentionally limited to print/readability CSS and documentation. It does not change course contracts, source syntax, MathJax behavior, graph data, or learner-state policy.
