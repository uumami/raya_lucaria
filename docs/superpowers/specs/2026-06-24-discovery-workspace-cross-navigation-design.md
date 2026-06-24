# Discovery Workspace Cross-Navigation Design

## Goal

Generated discovery workspaces must behave like one static tool family. Search, Graph, Practice, and Tasks should each expose local links to the other generated workspaces from the shared discovery command bar.

## Design

The existing `_render_discovery_command_bar()` remains the single renderer for discovery workspace chrome. It gains an optional `tasks_href` parameter, matching the existing optional `search_href`, `graph_href`, and `practice_href` parameters. Each workspace passes `None` for its own current surface and local relative links for the other surfaces.

Generated discovery workspace pages use the volatile OpenDyslexic toggle script. Reader pages may persist comfort preferences, but generated discovery workspaces should not depend on `localStorage` or `sessionStorage`.

## Scope

In scope:

- Add Tasks to Search, Graph, and Practice command bars.
- Keep Tasks linked back to Search, Graph, and Practice.
- Use local relative URLs only.
- Use volatile accessibility controls for generated discovery workspaces.
- Add focused contract coverage.

Out of scope:

- New learner state.
- New recommendations.
- Any external renderer, CDN, fetch, or browser-side MathJax dependency.
