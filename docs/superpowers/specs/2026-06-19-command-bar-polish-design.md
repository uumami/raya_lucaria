# Command Bar Polish Design

## Context

The reset renderer now has the essential learning shell: top command bar, expanded/collapsible course map, main article, right learning rail, local `OpenDyslexic`, graph page, and graph context rail. The old `main` branch still has one useful UX pattern that has not been fully adapted: the page feels like a compact application shell because the sidebar and top bar use dense controls, icon-like affordances, and clear navigation actions.

The old implementation used Eleventy, Tailwind, localStorage, external Google Fonts, and CDN math resources. Those choices do not match the current renderer contract. This slice adapts only the useful shell affordance pattern.

## Goal

Make the static course command bar feel like a modern learning tool while preserving current Raya constraints:

- no external CSS, fonts, scripts, icons, or CDN requests;
- no persisted UI state;
- no new dynamic study state;
- no browser-side MathJax;
- no change to artifact data authority.

## Design

The top command bar becomes a compact command surface with three explicit controls:

- `Graph`: a local static link to `_raya/graph/index.html`;
- `Course map`: the existing map toggle;
- `OpenDyslexic`: the existing local font toggle.

Each command gets:

- a visible compact symbol generated in CSS, not an external icon;
- a stable text label for readability and translation later;
- an `aria-label` that names the action;
- uniform dimensions, borders, focus states, and hover states.

On desktop, the bar remains sticky and uses a single row. The course title may truncate, while controls remain reachable and do not wrap into the article. On narrow mobile screens, the bar may wrap into a compact grid, but controls keep stable tap targets and do not overlap.

The course map toggle remains non-persistent and click-only. The shell script continues to synchronize all map toggles. The existing course-map button inside the map remains hidden on mobile as today; the top command bar is the primary mobile map control.

## Non-Goals

- No runtime theme picker in this slice.
- No imported SVG icon set.
- No persistent sidebar state or localStorage map state.
- No graph mini-map inside normal article pages.
- No new source schema fields.

## Files

- `packages/static/src/raya_static/builder.py`: add command-specific classes and action labels to the existing top command bar markup.
- `packages/static/src/raya_static/rendering.py`: polish command bar layout and command button/link CSS using existing skin tokens.
- `packages/static/src/raya_static/shell.py`: preserve synchronized map toggle labels for the new command classes.
- `tests/contracts/test_static_builder.py`: assert command markup, local links, labels, and no external resources.
- `tests/e2e/test_preview_static_read_path.py`: assert desktop/mobile command bar layout, no overflow, command tap targets, map toggle behavior, and OpenDyslexic toggle behavior.

## Testing

Focused tests should prove:

- rendered pages include the three command controls with action-specific classes;
- graph link remains deployment-neutral and local;
- command CSS defines stable sizing/focus behavior without external assets;
- desktop command bar stays one-row and does not overlap the content shell;
- mobile command controls remain visible and tappable;
- map toggle still collapses/expands through the command bar;
- `OpenDyslexic` still changes the computed body font.

Broader verification should run the static builder suite, static-read-path e2e suite, and render-debug gate.
