# Course Map Scan Mode Design

## Context

The current learning shell already has a generated course map, workspace shortcuts, local filter, desktop collapse, mobile drawer, and current/all/less section controls. The foundation contract allows volatile section controls for current path, all sections, and reduced current-path scanning. The legacy `main` branch has useful accordion behavior in its sidebar, but it persists expansion in `localStorage`, which does not fit the current static renderer contract.

## Decision

Add an explicit `Scan` control to the generated course map. `Scan` is a non-persistent accordion mode for large maps: it keeps the current page path open, and when a reader opens one branch, sibling branches at the same level collapse. This gives readers a focused, one-branch-at-a-time map without hiding the article, changing routes, storing state, or depending on external code.

The existing controls keep their meanings:

- `Current` opens the current page path and orients the current link.
- `All` expands every generated map section.
- `Less` collapses back to the current path.
- `Scan` enables focused sibling-collapse behavior and returns the map to the current path as its starting view.

Manual node toggles remain available. In scan mode, opening a branch collapses expanded sibling branches under the same parent. Closing an already-open branch only closes that branch. `Current`, `All`, `Less`, filtering, and course-map collapse/drawer state exit scan mode so the reader never gets stuck in a special hidden state.

## Architecture

The builder adds a fourth action button with `data-raya-course-map-action="scan"` and an `aria-pressed` state. The shell script tracks scan mode only in the current DOM runtime with `map.dataset.rayaCourseMapScan`. It reuses the existing `setMapNodeExpanded` function so ARIA, `hidden`, and stored DOM expansion state stay consistent.

The implementation intentionally avoids `localStorage`, `sessionStorage`, fetch/XHR, CDN dependencies, browser-side rendering, or learner-state language.

## Styling

The active scan button gets a clearer pressed state using existing skin variables. The map remains readable in all current skins and still respects reduced-motion behavior already present in the shell.

## Tests

Static contract tests prove the generated action and script tokens exist. Browser tests prove scan mode:

- starts from the current path,
- marks the `Scan` button pressed,
- collapses an expanded sibling when another sibling is opened,
- exits on `All`,
- does not write storage keys or issue network requests,
- keeps the current link visible.

## Self-Review

No placeholders remain. The scope is one shell behavior and its rendering/tests. The design follows the current renderer contract and only borrows the legacy accordion interaction, not legacy persistence or framework assumptions.
