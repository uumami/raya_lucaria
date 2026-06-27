# Graph Focus Fit Design

## Goal

Make Graph Focus mode feel like a real focused reading workspace by giving the graph canvas most of the desktop viewport and refitting the selected page context after the layout changes.

## Background

The legacy `main` branch expanded its graph and called fit after the size change. The current renderer has a stronger static SVG graph and better panel collapse semantics, but the Focus command mostly collapses the side panels while the graph canvas remains capped at `72vh` and does not explicitly refit after the expanded layout settles.

## Design

When a desktop reader activates Graph Focus, the Graph workspace keeps its existing volatile state model: no storage, no backend, no external graph library, and no new graph semantics. The focus button continues to collapse the list and inspector rails, but the expanded graph canvas becomes viewport-dominant. After toggling focus on, the local graph script schedules a selected-context fit after the DOM has applied the expanded layout so the selected node and nearby edges remain visible in the larger canvas.

This adapts the useful UX from `main` without bringing back Cytoscape, persisted sidebar state, external scripts, or personal progress semantics.

## Scope

In scope:

- Increase focused graph canvas height on desktop through static CSS.
- After entering Graph Focus, schedule `fitSelectedGraphContext()` when a page is selected.
- Keep panel collapse, URL state, and reset behavior unchanged.
- Add browser coverage for selected-page focus mode on the render fixture.

Out of scope:

- New graph layouts.
- Fullscreen browser APIs.
- Persisted graph focus state beyond the existing shareable URL parameter.
- External graph libraries, fetches, or CDN assets.
- Any ranking, recommendation, progress, mastery, or learner-state language.

## Testing

Use TDD:

1. Add an e2e test that opens Graph at `?page=reader-ux`, clicks `Focus`, and asserts the desktop canvas is at least 80% of viewport height.
2. Assert the selected `reader-ux` node and at least one graph edge intersect the visible canvas after focus.
3. Assert the list and inspector panels are collapsed, no horizontal overflow appears, and storage keys remain empty.
4. Run the focused test pair and render-debug gate.
