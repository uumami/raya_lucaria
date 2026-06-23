# Static Official Practice Design

Date: 2026-06-23

## Purpose

The current reset validates `_official/` cards, prompts, quizzes, assignments,
exams, projects, examples, and tasks, writes them to `data/official.json`, and
uses counts in section cards. Students still cannot use those official objects
from the rendered course page. Legacy `main` had visible learning components
and quiz/task affordances, but depended on the old Eleventy/Tailwind component
stack and stateful JavaScript patterns.

This slice renders official learning objects on their owning page as static
practice material, adapted to the current Glintstone renderer.

## Scope

In scope:

- Render a page-end `Official practice` article section for official objects
  whose `scope.quantum` matches the current page.
- Support current object types with type-specific static rendering:
  - `card`: front text plus a closed native `details` answer reveal.
  - `prompt`: prompt text as a reflection/retrieval prompt.
  - `quiz`: question prompts, options, and a closed native `details` answer
    reveal listing correct options.
  - `assignment`, `exam`, `project`, `task`, and `example`: render common
    content fields such as `title`, `summary`, `prompt`, `instructions`, and
    optional closed `answer`/`solution` support when present.
- Preserve source order from ordered official filenames.
- Keep all behavior static, local, keyboard reachable, and non-persistent.
- Update foundation and EN/ES role docs.
- Add contract and browser coverage for visible practice content, reveal
  controls, no source/private paths, no learner-state wording, and no external
  requests.

Out of scope:

- Scoring, grading, submissions, attempts, progress, mastery, recommendations,
  adaptive queues, spaced repetition, analytics, accounts, or backend calls.
- Browser-side Markdown/MathJax conversion for official object text.
- Runtime fetching of `data/official.json`.
- A course-level practice index. That can follow after page-level rendering is
  stable.

## Behavior

Each rendered page may include one `Official practice` section after authored
article content and page connections, before end-of-page sequence cards. The
section contains one article per official object with a stable DOM id
`raya-official-<object-id>`, an authority label, the object type, and the
object's visible content.

Cards and quizzes use native `details` elements for revealable answers. Opening
or closing a reveal does not save state, calculate a score, submit an answer, or
contact a service. Quiz options are presented as plain static options. Correct
answers are available only inside the reveal block.

The renderer treats official object content as text unless a future accepted
contract defines richer typed content. It escapes official object strings and
does not render raw HTML from official YAML.

## Static Contract

The official practice section is reader-facing static HTML generated at build
time from already-validated official objects. It must not expose source paths,
private support paths, artifact paths, cache keys, runtime profile internals, or
generated hash details. It must not add external CSS, scripts, fonts, fetch/XHR,
workers, service workers, or browser-side MathJax conversion.

Official practice is official course material, not a personal study state. The
surface may say `official`, `practice`, `prompt`, `answer`, or `correct option`;
it must not say progress, completion, mastery, recommended, grade, score, or
next step as renderer-generated language.

## Testing

Contract tests should verify that rendered pages include official practice
objects from the minimal fixture, preserve object IDs and type labels, include
native reveal controls for card backs and quiz answers, and omit `_official`,
`source_path`, private paths, fetch/storage APIs, and learner-state wording from
the student-facing HTML.

Browser tests should verify that a student page can open the card answer and
quiz answer reveals, that no external requests happen after page load, and that
practice cards do not overflow on representative desktop and mobile viewports.

## Documentation

Update `docs/foundation/20_learning_renderer_contract.md` to define official
practice as current static rendering. Update English and Spanish student,
professor, contributor, and agent docs to explain authoring, reading, and
verification expectations.
