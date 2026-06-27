# Graph Key Object Search Design

## Goal

Make the generated Graph workspace find a page when a learner searches for a public numbered object, proof, or key-object label that already appears on that page.

## Background

The current Graph payload already embeds public `key_objects` for each page so the selected-page inspector can show links such as `Definition 4.1 Orthogonal residual` and `Proof of Proposition 4.2 Orthogonal decomposition`. The Graph search haystack still ignores those objects, so a learner can inspect them after selecting a page but cannot reliably search by those public labels.

## Design

Extend the local Graph search text builder to include each node's generated public key-object fields: reference, kind, title, and anchor. This keeps Graph search page-level: it selects and reveals the owning page, not a new object node. Existing selected-page inspector links remain the object-level jump path.

The change is local static JavaScript over embedded public payload data. It does not add fetches, browser storage, graph data semantics, object nodes, ranking, recommendation, progress, mastery, private source paths, or URL state beyond the existing Graph query behavior.

## Scope

In scope:

- Add public `node.key_objects` fields to `nodeSearchText(node)`.
- Add browser coverage proving a key-object query selects the owning page and reveals the existing key-object links.
- Assert no storage writes, no external requests, and no overflow for that workflow.

Out of scope:

- Object-level graph nodes or edges.
- Object ranking or recommendation language.
- Search result snippets inside Graph list rows.
- Changes to `data/graph.json` shape.
- Changes to the static Search workspace.

## Testing

Use TDD:

1. Add an e2e test that searches Graph for a key-object-only label such as `Projection triangle`.
2. Verify the Graph selects `reader-ux`, displays `Projection Residuals`, and keeps the key-object inspector links visible.
3. Verify the workflow writes no browser storage, makes no external requests, and has no horizontal overflow.
4. Run the focused test, render-fixture build, and render-debug gate.
