---
id: graph-skin-palette-design
title: Graph Skin Palette Design
summary: Adapt old-main theme category colors into current validated skin tokens for the static graph.
status: approved
---
# Graph Skin Palette Design

## Context

The old `main` branch used theme variables such as `--color-homework`,
`--color-exercise`, `--color-exam`, `--color-project`, `--color-prompt`, and
accent colors to seed graph/category color. The reset branch already has a
static graph workspace, course-level and section-level skins, local
OpenDyslexic controls, and no external renderer dependency. The remaining gap
is that graph group colors are still renderer defaults derived from a small
fixed set of semantic colors.

This slice adapts the useful old-main idea without importing the old theme
stack, Cytoscape, arbitrary CSS, external assets, or browser-side fetching.

## Design

Skin profiles may define an optional `tokens.graph` group with eight validated
hex colors:

- `group_1`
- `group_2`
- `group_3`
- `group_4`
- `group_5`
- `group_6`
- `group_7`
- `group_8`

When omitted, the renderer keeps the current graph palette fallback derived
from semantic skin colors. When present, `render_skin_css()` emits
`--raya-graph-group-1` through `--raya-graph-group-8` inside the skin selector.
The static graph page, group chips, legend swatches, SVG nodes, SVG edge lines,
and SVG arrow markers already consume these variables, so a course can change
graph identity by changing skin YAML and rebuilding.

The token group is intentionally small. It is a course visual profile, not a
new graph ontology or author-facing CSS escape hatch.

## Validation

`tokens.graph` accepts only the eight group keys listed above. Values must be
six-digit hex colors. Unknown keys fail validation with actionable diagnostics.
The existing text/background contrast rules remain scoped to reading tokens,
because graph group colors are categorical visualization cues, not body text
colors.

## Documentation

Update the learning renderer contract and role guides to explain that graph
colors are skin-driven, local, static readability cues. Keep the English and
Spanish role docs separate.

## Testing

Add contract tests that prove:

- skin CSS includes graph group variables for a profile with `tokens.graph`;
- invalid graph token keys or colors fail validation;
- the graph page and graph script continue to use `--raya-graph-group-*`
  variables for chips, nodes, edges, and arrow markers.

Run focused static-builder tests, render-debug, host checks, and Docker checks
before claiming completion.

## Non-Goals

- No arbitrary CSS in skin files.
- No old Eleventy theme import.
- No Cytoscape or external graph renderer.
- No runtime fetch, CDN, localStorage, progress, ranking, recommendations, or
  browser-side MathJax.
- No section-specific graph data changes in this slice.
