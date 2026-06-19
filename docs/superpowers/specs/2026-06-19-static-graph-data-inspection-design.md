---
id: superpowers-static-graph-data-inspection-design
title: Static Graph Data And Inspection Design
status: ready
created: 2026-06-19
---

# Static Graph Data And Inspection Design

## Problem

The old `main` branch had a useful graph experience: searchable nodes, multiple layouts, legend filters, status text, fit/reset controls, and click-to-page navigation. It also depended on an Eleventy/Nunjucks/Tailwind stack and a Cytoscape CDN script. Those implementation choices do not match the reset renderer.

The current branch already has better source and artifact contracts. It writes `pages.json`, `links.json`, and `navigation.json`, and it serves local static pages with no browser-side MathJax or external renderer requests. The missing piece is a graph-oriented artifact surface that agents and future UI code can trust.

## Design Direction

Build the graph feature data-first.

The first slice creates a manifest-declared `data/graph.json` index and surfaces it in static inspection HTML. This adapts the valuable capability from `main` without importing the old runtime stack. A later slice can build a visual graph page on top of the stable data index using local JavaScript only.

This is the best order because graph data belongs to the artifact contract, while graph visualization is a reader/debug presentation. Data-first also makes regressions testable without relying on a particular canvas or force-layout engine.

## Graph Index Contract

`data/graph.json` is generated during `raya build`.

It contains:

- `version`: graph index version, initially `1`;
- `course_id`: course ID;
- `nodes`: one node per rendered page;
- `edges`: graph edges derived from generated links;
- `groups`: top-level navigation groups for filtering and future layout color;
- `backlinks`: inbound non-navigation relationships by target page.

Nodes use current page authority:

- `id`: page stable ID / quantum ID;
- `title`;
- `nav_title`;
- `url`;
- `group`;
- `order`;
- `status`;
- `tags`.

Edges use current link authority:

- `from`;
- `to`;
- `kind`;
- `source`: current generated data source, initially `links`.

Backlinks include inbound `content` and `prerequisite` relationships. Plain navigation and parent edges are graph edges but not backlink recommendations in the reader surface, because they would duplicate the course map.

## Inspection Surface

The existing `_raya/inspect/index.html` surface gains a compact graph section:

- total node count;
- total edge count;
- edge-kind counts;
- top-level groups;
- a link to the raw `data/graph.json` file.

This page is for professors, contributors, and agents. It is not the student default view and must not imply personal progress or adaptive recommendations.

## Future Visual Graph Page

A later slice may add `_raya/inspect/graph/index.html` or a student-visible graph page if accepted. It should use only local static JavaScript and local CSS. It may adapt old-main behaviors such as search, legend filters, fit/reset, hover neighborhood highlighting, and click-to-page navigation.

Do not add Cytoscape from a CDN. If a graph library is used later, it must be vendored or generated as a local artifact resource, or the renderer must use a small local SVG/HTML implementation.

## Code Boundaries

- `packages/static/src/raya_static/builder.py` generates the graph index and inspection markup.
- `packages/schema/src/raya_schema/schemas/graph-index.schema.json` validates `data/graph.json`.
- `packages/schema/src/raya_schema/artifacts.py` exposes `validate_graph_index` and includes graph validation in artifact inspection when declared by the manifest.
- `packages/schema/src/raya_schema/__init__.py` exports the validator.
- `tests/contracts/test_static_builder.py` owns graph data and inspection contract tests.
- `tests/e2e/test_preview_static_read_path.py` may add static-read-path checks once an HTML graph surface exists.

Avoid changes to MathJax, source validation, runtime execution, reviewed outputs, OpenSpec, generated artifact outputs, or legacy Eleventy files.

## Testing Strategy

Use TDD.

First failing test:

- Build the render fixture.
- Assert `artifact/data/graph.json` exists.
- Assert `manifest.json` declares `"graph": "data/graph.json"`.
- Validate the graph index with `validate_graph_index`.
- Assert graph nodes include `render-root` and `authoring-matrix`.
- Assert graph edges include generated content relationships.
- Assert the inspection page mentions graph node/edge counts and links to `../../data/graph.json`.

Regression tests should also prove:

- `inspect_artifact()` validates declared graph data;
- malformed graph indexes fail schema validation;
- the student pages do not load external graph scripts;
- render-debug/static-read-path gates still pass after graph data generation.

## Non-Goals

This slice does not add:

- a force-directed visual graph canvas;
- CDN Cytoscape or any external script;
- browser-side MathJax;
- search indexing;
- personal progress, mastery, recommendations, or analytics;
- inferred related practice;
- object-level graph nodes for theorems, equations, figures, or homework.

Those can be future slices after the page-level graph data contract is stable.
