---
id: docs-guides-en-students
title: Students
summary: Guidance for reading static artifacts, studying, keeping work portable, and reading authority labels.
status: ready
---
# Students

Students should be able to read static course artifacts, study with official learning objects, keep personal work portable, and understand whether material is official, personal, shared, generated, or accepted.

Static course pages are useful without accounts. Dynamic study state, review queues, and collaboration are future progressive enhancements.

Rendered courses hide source filename mechanics. Students should see clean page titles, hierarchy labels, summaries, breadcrumbs, previous/next links, generated section indexes, appendices, prerequisites, and official study-object counts when the course provides that metadata.

Generated section indexes appear as landing cards for child pages. They are a
map of course structure from the current artifact, not personal progress,
completion, mastery, or recommendations about what to study next.

Static pages may include pre-rendered math, highlighted code, copy buttons on fenced code blocks, tables, callouts, footnotes, heading anchors, and page contents. Math should already be typeset in the generated page and should not require a CDN, account, backend, or browser-side MathJax conversion. Displayed code is not run by the static page unless a future course explicitly adds an accepted execution workflow.

Some pages show a Page brief near the start. It summarizes public course
metadata such as summary, status, page position, estimated time, tags,
prerequisites, explicit page connections, and available official practice. Use
it to orient yourself quickly. It is not a progress tracker, recommendation,
grade, mastery estimate, or personalized next step.

Some courses use skins for visual presentation or to emphasize a unit, lab,
appendix, practice section, or review section. A skin does not change source
authority, labels, links, official/generated status, assignments, or what work
the course asks you to complete. If two sections look different, use the page
title, links, and labels as the source of course meaning; the skin is only
visual emphasis.

Rendered pages may include `Text size` and `OpenDyslexic` buttons in the top
chrome. They are local reading preferences stored by your browser for that
static site; they change text scale or page font for easier reading but do not
change course content, grading, links, skin identity, or authority labels.

You can print a generated page or save it as a PDF when you want a handout for
offline reading or annotation. Print mode removes the course chrome and keeps
the page content, math, code, tables, official practice, and support notes
readable. It does not submit work, save progress, estimate mastery, or contact
an external service.

The current course shell is a static reading aid. On desktop, the expanded course map
is rendered as an expanded hierarchical course map and may show structural
sequence numbers from the course order. It gives orientation by default, the top bar keeps the current course/page title and
structural page position visible, the main article remains the lesson, and the
learning rail provides page contents and nearby course context. You can collapse
the map to an operable compact map rail when you want more reading space; that
choice is non-persistent and does not store or show personal progress.
When a long map opens, the page can move the current page link into the visible
part of the map. That orientation is temporary reading context, not saved state.

Use the Course map button to collapse or expand navigation when you need a
different focus. Use the map filter to narrow visible page labels inside the
current static hierarchy. Use Previous and Next in the article, top reading
context, or end-of-page cards to move through the ordered material, and use Text
size or OpenDyslexic when those settings are more comfortable. End-of-page cards
are course-order links; they are not recommendations or progress markers.
The expanded course map may also show static links to Course Search, Course
Graph, Official Practice, Official Tasks, and Official Schedule. They are
shortcuts to generated workspaces, not progress, ranking, or personalized guidance. Some shortcut
cards include small structural badges such as course scope, explicit link
counts, accepted official-object counts, accepted task counts, or dated
official-task counts for the current
page. Those badges describe authored static course structure; they are not
completion, importance, grade, or recommendation signals.

Use the Course graph to inspect generated page relationships. Its search,
filters, selected-page details, Zoom in, Zoom out, Fit, Reset view, and expanded
graph workspace are local reading tools over current course structure. They do
not store progress, recommend what to study next, or change course authority.
Fit and Reset view only change the visual graph view; the list and selected-page
details stay available. Opening it from a course page may focus that page so you
can see its explicit links first. The learning rail may also show a Connections
panel with counts for links from the current page and links into it; those
counts describe authored static relationships, not recommendations or personal
progress.
Some pages may also end with a Page connections block inside the article. It
uses the same static relationship data to show pages linked from the lesson,
pages that link back to it, and an Open in course graph link. Connection items
can open native previews with the linked page summary, status, and explicit link
counts when the course has that metadata. Use them as a reading map after
finishing the page; they are not a progress tracker, ranking, or recommendation
engine.
Search, Graph, Practice, Tasks, and Schedule pages use the same static discovery bar so
you can return to the course, switch between those workspaces, and keep Text
size or OpenDyslexic available for the current page. Search, Practice, and
Tasks, and Schedule may also show controls, results, and a context panel on wider screens.
Those controls are for reading and scanning comfort; the workspaces do not
store your query, selected node, graph layout, practice filters, or task
filters as study state.
When a page is selected in the graph, connected pages may be highlighted and
summarized as outgoing links, incoming links, and connected pages. Those numbers
describe the current static graph, not how far you have progressed.
Graph colors group pages by current course structure, node size can show how
many explicit links touch a page, and hover or keyboard focus can temporarily
inspect a page and its connected pages. These are static readability cues, not
importance rankings, progress, mastery, recommendations, or grading signals.

Use Course Search when you remember a title, tag, status, summary phrase, or
stable ID. It searches generated metadata only, supports approximate matches and
keyboard, hover, and focus inspection of visible results, and does not search hidden source
paths or store your query. Opening it from a course page may preload that page
title as a temporary query. A result can also offer `View in graph`, which opens
the Course Graph focused on that same page so you can inspect its course
position and explicit links. The Search context panel summarizes public
metadata for the result you are inspecting; it is not a ranking or
recommendation. When a result has accepted official practice, it may also open
Official Practice focused on that page. That page focus is only URL context;
clearing Practice or pressing Escape returns to all visible official objects.

If math appears as raw TeX commands such as `\begin{bmatrix}` or an unknown macro on a published page, treat that as a rendering problem to report to the course team, not as a step you need to fix in your browser.

Rendered matrices, vectors, set notation, theorem-like notes, and proofs should appear as normal course text plus typeset math. If you see raw `\begin{bmatrix}`, an unknown macro, visible dollar-delimited math, or a page asking your browser to load browser-side MathJax, report it to the course team with the page URL or title.

Course pages may include numbered objects and static references. A result might appear as `Theorem 2.3.1`, an image as `Figure 2.3.1`, and practice work as a homework, problem, activity, or assignment reference. Numbered objects should appear as scannable course content where appropriate: theorem-like objects, examples, exercises, and assignments use the `scannable` reader style by default, while figures and tables keep `caption` presentation and equations keep `equation` presentation. These numbers, labels, anchors, and references are generated during build and published as static links; your browser should not need to calculate them or load a live reference service.

Numbered content appears as static labels and links, such as `Theorem 3.1`, `Figure 3.1`, or `Activity 3.3`. Proof headings such as `Proof of Activity 3.3` are generated during build; the browser does not calculate references.

Some course teams author internal links with `[[...]]` syntax. In the published
course, those should appear as normal page links before you see the page. If
raw `[[target]]` text appears in a published page, report the page title or URL
to the course team.

Rendered proof headings name the object being proved, and math inside the proof should already be typeset during build. The page should not need a browser-side MathJax request to display the proof. If you see raw source syntax or raw TeX instead of a rendered proof, report it to the course team with the page URL or title.

Proofs, solutions, hints, and answers should appear as static course content.
Proofs stay open when they are part of the explanation. Hints, solutions, and
answers may start collapsed so you can reveal them only when you want support.
Opening one does not submit an answer, save progress, contact a backend, or
ask your browser to render MathJax. When a block names a theorem, problem,
activity, homework, figure, table, or equation, that heading should already be
resolved before the page reaches your browser.

Some pages may include an `Official practice` section rendered from the page's
own `_official/` material. Cards, prompts, quizzes, and other official fields
are shown as static reading support on the owning page. Reveal controls are
local browser controls; opening one does not submit work, save answers, create
attempts, update progress, change mastery, contact a backend, fetch more data,
or ask your browser to render MathJax.

Some courses may also include an Official Practice workspace under
`_raya/practice/`. Use it to find accepted course cards, prompts, quizzes,
tasks, and other official objects across the course, then return to the owning
page for context. Practice items should link to page anchors such as
`#raya-official-<id>` and may offer `View in graph` links. You can inspect
visible Practice items with keyboard movement, hover, or focus on item links;
the context panel follows that temporary selection. The workspace is a
static discovery surface with filters, results, and public context summaries,
and Search or Graph may open it already filtered to one page through
`?page=<page-id>`. Clear or Escape removes that temporary page focus; it is not
saved as study state. It is not a recommendation engine, progress tracker,
submission system, grading system, scoring system, attempt log, mastery
estimate, stored practice state, external request workflow, private source-path
viewer, or personal review queue.

Some courses may also include an Official Tasks workspace under
`_raya/tasks/`. Use it to scan accepted assignments, projects, exams, and tasks
by text, type, course order, or due date, then open the owning page for full
context. It may show public planning fields such as title, page, due date,
points, status, and tags when the course team authored them. It is not a
personal progress tracker, submission system, gradebook, adaptive
recommendation page, calendar sync, or hidden answer surface.

Some courses may also include an Official Schedule workspace under
`_raya/schedule/`. Use it to scan accepted assignments, projects, exams, and
tasks that have authored due or available dates, then open the owning page for
full context. It is a static dated view over course metadata; it is not a
personal calendar, reminder system, progress tracker, recommendation page,
submission system, or gradebook.

Some pages may include linked scripts or notebooks. These are copied as readable files and may show source previews, but the static build labels them as not executed. Unlinked course source files are not part of the page artifact. Use course instructions when a class expects you to run code locally, in Docker, or through a future accepted execution workflow.

Fenced code examples may include a `Copy` button. Copying puts the displayed code text on your clipboard; it does not run the code, save progress, or contact a backend.

Some courses include runtime metadata for future local or Docker execution. In the current static artifact, that metadata only explains intended profiles, policies, and cache keys. It does not mean the web page has already run the code.

When a course asks you to run code, use the exact target named by the course team, such as `raya run . manual-script` from the course root or the Docker command they provide. `--dry-run` shows what would run before it runs. Cache-policy targets may reuse previous generated output unless the course asks for `--refresh`.

Some pages may show reviewed output panels. Reviewed output is course support that the course team has frozen into source review, so it can be shown statically without rerunning code. It is different from your personal work and from generated-only local logs. If reviewed output is stale or missing, the course artifact should fail before publishing it as current.

Static pages show a focused reading view. Internal hashes, cache keys, source paths, artifact paths, and runtime details are kept out of the normal page flow; they are for professors, contributors, agents, or tools inspecting the artifact.

If a professor shares a local preview URL, it is the same generated static site served from `artifact/site/`. Opening a preview page does not run course code or notebooks. Follow explicit course instructions when computation is part of the class.

Use role documentation as guidance. Use course pages and official learning objects as course material. If documentation and course material conflict, the course team and accepted OpenSpec specs or `docs/foundation/` authority decide what changes.

Rendered repository documentation may be browsed as static pages, but it remains guidance about the framework. It is not the same authority surface as a course team's official course artifact.
