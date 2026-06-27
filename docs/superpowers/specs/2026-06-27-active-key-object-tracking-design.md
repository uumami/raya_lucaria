# Active Key Object Tracking Design

## Goal

Improve reader orientation on math-heavy pages by highlighting the key object currently in view inside the right rail `Key objects` list.

## Background

The legacy `main` branch used scroll tracking to keep its table of contents visually connected to the reader's current location. The reset renderer already tracks current headings for the command bar and right rail, and recent work added key-object lists for numbered objects and proofs. A learner reading a long theorem/proof/equation page still benefits from a lightweight signal showing which key object is currently in view.

## Design

The shell script will observe public numbered-object and proof sections that already have rendered article IDs such as `raya-object-...` and `raya-proof-...`. When one of those elements is active in the viewport, the matching link in `.raya-page-toc-objects` gets `aria-current="location"` and a visual active style. When no object is active, object links remain ordinary links.

This is local, transient reading orientation only. It does not persist state, infer progress, change the current heading context, mutate URLs, fetch data, or create object-level graph semantics. The existing heading current-section behavior remains unchanged.

## Scope

In scope:

- Add stable object-link attributes while rendering the right rail key-object list.
- Observe `.raya-numbered-object[id]` and `.raya-proof[id]` in `shell.js`.
- Toggle `aria-current="location"` only within `.raya-page-toc-objects`.
- Style active key-object links with current skin tokens.
- Add focused browser coverage on `reader-ux`.

Out of scope:

- Browser storage or saved reading position.
- Updating command-bar current section to object anchors.
- Object-level graph nodes or edges.
- New artifact schema or `data/graph.json` changes.
- Recommendation, progress, mastery, ranking, or completion language.

## Testing

Use TDD:

1. Add an e2e test that scrolls to a rendered object and expects the matching key-object link to receive `aria-current="location"`.
2. Assert the heading current-section link still points to the surrounding heading, not the object.
3. Assert no horizontal overflow and no storage keys are written.
4. Add contract assertions for stable object-link attributes and active-link CSS.
5. Run focused tests, render-fixture build, and render-debug gate.
