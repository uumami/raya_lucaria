# Course Map Orientation Design

## Goal

Adapt the useful legacy navigation auto-orientation behavior into the current static course shell: when a page loads with an expanded course map, the current page link should be brought into view inside the course-map scroll region without storing navigation state.

## Context

Legacy `main` used `nav-state.js` to auto-scroll the active navigation item into view after load. It also persisted expanded sections in `localStorage`; that part is not acceptable in the current reset because course-map state must remain non-persistent.

The current shell already renders active and ancestor map nodes, expands the current path, supports explicit node toggles, filters map labels locally, and avoids external requests. The missing affordance is orientation in long maps: the active page can exist outside the visible scroll region.

## Design

Add a small course-map orientation helper to the local shell script. It finds `#raya-course-map-list a[aria-current="page"]`, checks whether that link is fully visible inside the `.raya-course-map` scroll panel, and if not, scrolls that local map panel so the link is centered. It runs after initial expansion/filter setup and again after returning from compact-map expansion, because the map can become visible after being collapsed.

The `.raya-course-map` panel must be a real bounded scroll region on desktop and mobile. On desktop, the grid item must opt out of stretch sizing so the viewport-based `max-height` can take effect; otherwise orientation has no scroll container to move.

The helper is one-shot UI orientation. It must not write `localStorage`, `sessionStorage`, URL state, artifact data, or source files. It must not override explicit user node expansion choices, and it must not run while the map filter has a query because filtering intentionally changes the visible map.

## Boundaries

- Keep the course map generated from current navigation data.
- Keep map expansion and filtering non-persistent.
- Do not copy legacy accordion persistence.
- Do not add Pagefind, external search, external scripts, or browser-side rendering.
- Do not introduce progress, recommendation, ranking, or mastery language.
- Preserve keyboard access and mobile no-overflow behavior.

## Tests

Add browser coverage against the existing render fixture. The test should force the course-map panel into a small scroll region, reset its scroll position to the top, invoke the shell orientation helper, and assert the current page is visible inside the map-panel viewport. It should also assert automatic orientation does not run while a filter query is active, the helper does not create local/session storage state, and no network requests are made.

Contract tests should assert the shell script contains the explicit orientation helper and does not contain the legacy navigation storage key.

## Documentation

Update the learning renderer contract and EN/ES student/agent role docs to say the map may auto-orient the current page as non-persistent reading context, while map state and filter text remain non-persistent.
