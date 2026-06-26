# Graph Mobile First Viewport Design

## Goal

Make the mobile graph page show the actual SVG graph much earlier in the first viewport while preserving the current static, dependency-free graph controls and explanatory context.

## Context

Fresh measurements at `390x844` show the mobile graph canvas starts around `760px`. The main contributors before the canvas are:

- Graph reading keys: about `102px`
- Graph instructions: about `78px`
- Graph orientation: about `214px`

The old `main` branch had less pre-canvas density around its graph interaction. The current reset renderer already has the stronger static graph architecture, local resources, URL-backed state, no storage requirement, and no Cytoscape dependency. This slice adapts the old branch's lower-friction graph entry feel without importing its stack.

## Design

Use mobile-only CSS under the existing `max-width: 520px` breakpoint:

- Reading keys remain visible and in DOM, but become a single horizontal reference strip.
- Graph instructions remain in DOM, but are line-clamped to a compact two-line cue on mobile.
- Orientation remains above the canvas, but metadata and actions become compact horizontal strips.
- The toolbar keeps its existing internal horizontal scrolling and must not reintroduce document-level horizontal overflow.

No graph JavaScript, payload, URL, storage, layout algorithm, or dependency behavior changes.

## Acceptance Criteria

- At `390x844`, the graph canvas top is `<= 620px`.
- At `390x844`, reading keys height is `<= 48px`.
- At `390x844`, graph instructions height is `<= 40px`.
- At `390x844`, orientation height is `<= 100px`.
- The page has no document-level horizontal overflow.
- The mobile graph toolbar still has internal horizontal overflow.
- Existing reading-key articles, orientation metadata, and orientation actions remain in the DOM.
- Existing graph deep-link, toolbar, map-priority, and render-debug checks remain green.
