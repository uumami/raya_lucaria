# Graph Edge Readability Design

## Context

The current static graph already keeps the main UX gains from the old `main`
branch: compact controls, search spotlighting, group filters, neighborhood
focus, pan/zoom, local SVG rendering, and source-group edge colors. The old
branch also used directed arrows and hover neighborhood highlighting, but it
did not carry a current contract-safe relationship taxonomy into the visual
edge treatment.

The current artifact graph already has relationship kinds: `navigation`,
`parent`, `content`, and `prerequisite`. Students can see linked pages and edge
counts, but the canvas itself draws all relationship kinds as the same line.
That makes graph structure harder to scan, especially when course hierarchy,
authored content references, and prerequisite metadata coexist.

## Decision

Add structural edge-kind readability to the existing local graph surface.

1. Keep graph JSON and browser payload shape unchanged. Edge `kind` already
   exists and remains generated artifact data.
2. Add local SVG attributes/classes for each rendered edge:
   `data-raya-graph-kind="<kind>"` and `raya-graph-edge-kind-<kind>`.
3. Keep source-group color as the primary edge color. Use line pattern and
   weight for relationship kind:
   - `navigation`: solid course-order/course-structure line.
   - `content`: short dashed authored content-reference line.
   - `prerequisite`: longer dashed prerequisite-metadata line.
   - `parent`: dotted structural parent line with lighter emphasis.
4. Add legend entries for all four relationship kinds.
5. Update graph help text to explain that edge patterns show relationship
   kinds and remain structural readability cues only.

## Boundaries

- No schema change, no new artifact file, no graph JSON rewrite.
- No external graph library, CDN, runtime fetch, worker, service worker, or
  graph state persistence.
- No progress, recommendation, importance, mastery, completion, or personal
  next-step language.
- No color-only distinction for relationship kind. Source-group color stays
  intact; kind is expressed through stroke pattern/weight.
- No single-click navigation change from the old branch; current inspect-first
  behavior remains.

## Implementation Shape

- `packages/static/src/raya_static/graph.py` adds a tiny edge-kind sanitizer and
  applies kind data/class to rendered SVG `<line>` edges.
- `packages/static/src/raya_static/builder.py` adds graph legend entries and
  help copy for relationship patterns.
- `packages/static/src/raya_static/rendering.py` adds legend line variants and
  SVG edge-kind selectors.
- `docs/foundation/20_learning_renderer_contract.md` records that edge patterns
  may show generated relationship kinds as readability cues.
- Contract and browser tests assert the legend, script selectors, CSS selectors,
  and rendered SVG edge attributes/classes.

## Verification

Focused verification must prove:

- Graph HTML still uses local resources only.
- Legend entries exist for `navigation`, `content`, `prerequisite`, and
  `parent` relationship kinds.
- The local graph script emits `data-raya-graph-kind` and kind classes.
- Rendered SVG edges expose expected kind attributes/classes for known fixture
  relationships.
- Existing inspected/search edge states still work alongside kind classes.
- No learner-state or recommendation wording is introduced.
