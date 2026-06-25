# Reading Focus And Graph Debug Design

The old `main` branch made navigation and graph tools feel more intentional than the early reset renderer, but it relied on persisted sidebar state, Cytoscape, and other stack choices that do not belong in the current static contract. The next reset-native UX slice should improve attention and graph readability without changing course data, artifact data, or reader-state rules.

## Goal

Add a volatile desktop `Focus reading` control that collapses the course map and right learning rail together, and move graph debug/state readout behind a native disclosure by default.

## Reader Focus Mode

The current shell already has separate desktop controls for the course map and right learning rail. Focus mode is a convenience command over those existing states:

- It appears as a keyboard-reachable command-bar button on reader pages.
- On desktop, activating it collapses the course map and the learning rail at the same time.
- Activating it again restores both regions to expanded reading layout.
- It is volatile DOM state only. It must not use `localStorage`, `sessionStorage`, URL state, cookies, fetch, or a backend.
- It does not replace individual map and rail controls.
- Escape should still leave the reader in an accessible state and should not create inert hidden panels on tablet or mobile.
- On tablet and mobile, the control should not hide article content or create a separate persistent mode. The existing course-map drawer behavior remains the mobile navigation affordance.

This is a comfort affordance, not progress, mastery, ranking, recommendation, or personalization.

## Right Rail Duplication

When a page brief is present in the article, the rail summary can add redundant first-screen weight. The rail may keep page contents visible while summary/status details are less visually dominant. Any collapse must use native accessible behavior or existing rail controls and must not hide required navigation from keyboard or screen readers on mobile.

## Graph Debug Disclosure

The graph workspace has useful state/debug readout, but it reads like developer instrumentation when shown as primary content. The graph should keep search, layout controls, canvas, list, selected-page detail, relationship walkthroughs, and normal page links visible. Debug state and copyable URL status should sit inside a native disclosure collapsed by default.

The disclosure is local HTML behavior. Opening it must not persist state, fetch data, load external code, or change graph selection. Existing copy URL behavior remains available inside the disclosure.

## Files

- `packages/static/src/raya_static/builder.py` renders the reader command-bar control and graph debug disclosure markup.
- `packages/static/src/raya_static/shell.py` wires volatile focus mode using the existing course-map and rail state helpers.
- `packages/static/src/raya_static/rendering.py` styles the focus command and graph disclosure.
- `tests/e2e/test_preview_static_read_path.py` proves focus mode behavior, graph disclosure default state, no storage for focus/graph state, and no mobile inert hidden rail regression.
- `docs/foundation/20_learning_renderer_contract.md` and role docs record the behavior.

## Tests

Focused browser tests should prove:

- `Focus reading` is visible and keyboard reachable on desktop reader pages.
- Clicking it collapses both course map and rail using existing DOM state.
- Clicking again restores both regions.
- It writes no storage keys and does not change URL.
- Mobile does not enter an inert hidden rail state.
- Graph debug/state readout is inside a collapsed native disclosure by default.
- Copy URL remains reachable when the disclosure is opened.

Verification should include the focused e2e tests, `git diff --check`, `./scripts/check-render-debug.sh`, `./scripts/check.sh`, and `./scripts/check-docker.sh`.
