# Discovery Workspace Switcher Design

## Context

The generated discovery pages already share a command bar with course,
workspace, text-size, and OpenDyslexic controls. The current page title appears
in the reading context, but the workspace command row omits the current
workspace. That makes Search, Graph, Practice, Tasks, and Schedule feel like a
set of links away from the current page rather than a stable workspace switcher.

Legacy `main` treated navigation surfaces as persistent places in the interface.
The current renderer should adapt that affordance without restoring legacy
state persistence, external libraries, or browser-side theme behavior.

## Goal

Render Search, Graph, Practice, Tasks, and Schedule as a stable switcher on
every discovery page, with the current workspace visibly marked and exposed to
assistive technology through `aria-current="page"`.

## Design

Add `current_workspace` to `_render_discovery_command_bar`. The command bar will
always render the five discovery workspace commands when their hrefs are
provided. The current workspace will use a self-link, just like many static
sites mark the current navigation item. It will receive:

- `aria-current="page"`;
- `data-raya-current-workspace="<kind>"`;
- the existing command icon and label;
- an active visual style scoped to `.raya-discovery-command-bar`.

The course command remains separate and never receives workspace current state.
Text-size and OpenDyslexic controls remain unchanged.

## Workspace Hrefs

Each generated discovery page will pass hrefs for all five workspaces:

- Search: `search_href="index.html"`, `current_workspace="search"`;
- Graph: `graph_href="index.html"`, `current_workspace="graph"`;
- Practice: `practice_href="index.html"`, `current_workspace="practice"`;
- Tasks: `tasks_href="index.html"`, `current_workspace="tasks"`;
- Schedule: `schedule_href="index.html"`, `current_workspace="schedule"`.

Cross-workspace hrefs keep their existing relative paths.

## Styling

Add active styles scoped to discovery command bars:

- stronger surface fill;
- accent border;
- small inset highlight;
- high contrast label/icon color;
- focus style remains visible.

The style must work with all skin profiles and must not force horizontal
overflow on desktop or mobile.

## Tests

Contract tests should prove:

- Search, Graph, Practice, Tasks, and Schedule command labels appear on each
  discovery page;
- exactly one discovery workspace command has `aria-current="page"`;
- the current command has the expected `data-raya-current-workspace`;
- self-links are local relative links, not external URLs;
- shared active CSS exists.

Browser tests should prove:

- the active command is visible on Search, Graph, Practice, Tasks, and Schedule;
- the visible active label matches the page;
- the command bar does not horizontally overflow at desktop or mobile widths;
- no new browser storage or runtime fetch behavior is required.

## Non-Goals

- No JavaScript changes.
- No stored workspace state.
- No browser-side theme switching.
- No backend, fetch, XHR, CDN, external renderer, or external font request.
- No progress, mastery, ranking, recommendation, personalization, grading,
  scoring, attempts, submissions, reminders, or calendar sync.
