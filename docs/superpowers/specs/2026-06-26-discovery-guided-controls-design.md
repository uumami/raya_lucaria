# Discovery Guided Controls Design

## Context

Search, Practice, Tasks, and Schedule already share the current discovery
workspace shell: command bar, overview, collapsible controls, results, context
panel, local volatile scripts, local accessibility controls, and no runtime data
fetching. Graph now has an explicit quick guide that makes the workspace easier
to enter without reading the whole UI. The non-graph discovery workspaces need
the same first-use guidance, adapted to their own controls.

The foundation contract allows generated discovery chrome and public structural
metadata. This design keeps guidance static and structural: it explains where
to type, filter, inspect, reset, and open owning pages or graph focus links. It
does not add progress, mastery, ranking, recommendation, personalization,
grading, submission, backend, external resource, or browser-side MathJax
behavior.

## Goal

Add a shared, compact guided-control strip to Search, Practice, Tasks, and
Schedule so students can quickly understand each workspace without leaving the
static site or expanding private implementation details.

## Approach

Add one shared builder helper, `_render_discovery_quick_guide`, that receives a
workspace kind, title, and a small list of cards. Each card has a short label
and structural text. The helper renders a semantic section with:

- `class="raya-discovery-quick-guide"`;
- `data-raya-discovery-guide="<kind>"`;
- one `h2` for the guide;
- card articles with `h3` headings and short paragraphs.

Each workspace inserts the guide immediately after the existing discovery
overview and before the three-column workspace. This keeps orientation close to
the controls while preserving the current panel layout and collapse behavior.

## Workspace Content

Search guide cards:

- `Find`: type public page, section, tag, or stable-ID text.
- `Inspect`: use pointer, focus, or keyboard movement to update context.
- `Open`: use result links for page, graph, practice, tasks, or schedule.
- `Reset`: clear or press Escape to return to all visible public pages.

Practice guide cards:

- `Find`: search accepted official objects and filter by type.
- `Inspect`: select visible objects to read public metadata.
- `Open`: return to the owning page or graph focus.
- `Reset`: clear or press Escape to show accepted objects again.

Tasks guide cards:

- `Find`: filter accepted task-family objects by text and type.
- `Sort`: switch course order, authored due date, or type.
- `Inspect`: select visible tasks to read public planning fields.
- `Open`: return to the owning page or graph focus.

Schedule guide cards:

- `Find`: filter dated official work by text, date kind, and type.
- `Scan dates`: read authored due and available dates as course metadata.
- `Inspect`: select visible dated items to read public planning fields.
- `Open`: return to the owning page or graph focus.

## Styling

Add shared CSS near the existing discovery overview styles. The guide is a
compact responsive grid with clear borders, subtle accent surface, readable
headings, and no decorative or animated dependency. It must work inside all skin
profiles and avoid horizontal overflow on desktop and mobile.

## Tests

Add contract assertions to existing builder tests for Search, Practice, Tasks,
and Schedule:

- the guide section exists with the correct `data-raya-discovery-guide`;
- expected card labels and structural text are present;
- forbidden learner-state words are absent from guide text;
- shared guide CSS selectors exist in `rich.css`;
- scripts remain local and do not fetch, store state, or call external
  renderers.

Add a browser/static-read-path check over the four workspace URLs:

- guide is visible at desktop and mobile;
- no horizontal overflow appears;
- guide cards stay within the viewport width.

## Non-Goals

- No new JavaScript.
- No persistent state.
- No runtime fetch/XHR.
- No external scripts, fonts, CSS, renderers, or CDN requests.
- No source-path, artifact-path, cache-key, private support, answer-only, or
  hidden solution exposure.
- No progress, mastery, ranking, recommendation, personalization, adaptive,
  submission, grading, scoring, attempt, calendar-sync, reminder, or due-state
  claims.
