# Static Schedule Workspace Design

## Goal

Adapt the old `main` branch calendar affordance into the current static
renderer as a Schedule discovery workspace over accepted official task
metadata.

## Design

The current renderer already builds `data/tasks.json` and an Official Tasks
workspace from accepted `_official/` assignments, exams, projects, and tasks.
Schedule should be a peer generated surface at `_raya/schedule/index.html`
that reuses the same public task payload and includes only objects with
`content.due` or `content.available`.

The page presents date-bearing official work in a compact calendar-like view:

- a shared discovery command bar with Course, Search, Graph, Practice, Tasks,
  Schedule, text-size, and OpenDyslexic controls;
- a control panel with search, type filters, and an event-kind filter for due,
  available, or all dated items;
- a results panel with schedule cards ordered lexically by authored date, then
  course order;
- a context panel that follows the active card through keyboard movement,
  pointer hover, or focus.

The surface is a static planning view, not a calendar integration feed. It does
not create `data/schedule.json`, parse dates semantically, calculate overdue or
today state, sync with a calendar, store state, fetch data, or infer schedule
items from prose.

## Scope

Current scope:

- Generate `_raya/schedule/index.html`.
- Add a local `schedule.js` resource beside `tasks.js`.
- Add Schedule to reader command bars, discovery command bars, and course-map
  workspace shortcut cards.
- Show a Course-map Schedule badge as `<N> dated`, counting direct page-owned
  task-like official objects with `due` or `available`.
- Reuse `data/tasks.json` semantics and the existing task object extraction.
- Update foundation and role docs in English and Spanish.
- Add focused contract and browser checks for static resources, no storage, no
  fetch, no personal progress, and no external requests.

Out of scope:

- New course source fields or validation for dates.
- New manifest `data/schedule.json`.
- Calendar CSV ingestion from the old branch.
- Calendar sync, reminders, overdue labels, relative-date labels, personal
  progress, mastery, recommendations, submissions, grading, or adaptive study
  state.

## Main-Branch Adaptation

The old calendar table's useful idea is a scannable time-oriented view. The old
implementation details are not reused: no Eleventy/Nunjucks layout, no
`clase/calendario_temas.csv`, no generated `_data/calendar_topics.json`, and no
relative overdue logic. The current renderer adapts only the UX affordance and
grounds it in accepted official task metadata.

## Verification

Focused tests should prove that:

- Schedule is generated as a local static workspace.
- Schedule includes accepted task-family objects with `due` or `available`.
- Schedule excludes task-family objects without either field.
- The page uses local resources only and no browser storage.
- Reader and discovery command bars expose Schedule with deployment-neutral
  links.
- Course-map Schedule shortcut cards show structural badges.
- Schedule copy avoids progress, recommendation, overdue, reminder, sync,
  scoring, grading, and learner-state language.
