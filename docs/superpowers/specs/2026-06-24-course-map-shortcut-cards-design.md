# Course Map Shortcut Cards Design

## Goal

Make the reader shell's Course workspaces block feel like a useful course
destination panel instead of four plain links, adapting the stronger `main`
branch sidebar affordance to the current static renderer contract.

## Design

The current course map already links to Search, Graph, Practice, and Tasks.
Those links should become compact shortcut cards with a short label and one
structural badge. The badges are generated during build from public artifact
data already available to the page renderer:

- Search: `Course`
- Graph: `<N> links`, where `N` is incoming plus outgoing explicit page links
  for the current page
- Practice: `<N> official` when the current page directly owns accepted
  official objects, otherwise `Course`
- Tasks: `<N> tasks` when the current page directly owns accepted task-like
  official objects, otherwise `Course`

Practice should also use a page-focused href when direct official objects exist,
matching the existing Search/Graph handoff behavior:
`_raya/practice/index.html?page=<page-id>`. Otherwise it remains the generic
Practice workspace. Tasks stays generic in this loop because Tasks does not yet
have page URL focus.

## Scope

Current scope:

- Render the Course workspaces links as compact shortcut cards inside the
  course map.
- Add structural badges without adding source schema or artifact data.
- Preserve collapsed course-map behavior by hiding the workspace card panel when
  the map is collapsed.
- Keep the top command bar unchanged except where it already shares the
  generated Practice href.

Out of scope:

- Calendar/schedule source or artifact contracts.
- Runtime storage, progress, recommendations, ranking, or learner state.
- Graph layout or graph algorithm changes.
- Task page focus.
- New external assets, icon libraries, fetches, or browser-side hydration.

## Verification

Focused browser tests should prove that:

- the Course workspaces block renders four shortcut cards;
- shortcut cards include structural badge text;
- direct-owner pages get page-focused Practice hrefs;
- pages without direct official objects keep generic Practice hrefs;
- badges and hrefs do not require storage, fetch, or external requests; and
- desktop and mobile layouts have no horizontal overflow.
