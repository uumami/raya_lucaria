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

The current course shell is a static reading aid. On desktop, the expanded course map
is rendered as an expanded hierarchical course map and gives
orientation by default, the main article remains the lesson,
and the learning rail provides page contents and nearby course context. You can
collapse the map to an operable compact map rail when you want more reading space; that
choice is non-persistent and does not store or show personal progress.

Use the Course map button to collapse or expand navigation when you need a
different focus. Use the map filter to narrow visible page labels inside the
current static hierarchy. Use Previous and Next to move through the ordered
material, and use Text size or OpenDyslexic when those settings are more comfortable.

Use the Course graph to inspect generated page relationships. Its search,
filters, selected-page details, and expanded graph workspace are local reading
tools over current course structure. They do not store progress, recommend what
to study next, or change course authority.

If math appears as raw TeX commands such as `\begin{bmatrix}` or an unknown macro on a published page, treat that as a rendering problem to report to the course team, not as a step you need to fix in your browser.

Rendered matrices, vectors, set notation, theorem-like notes, and proofs should appear as normal course text plus typeset math. If you see raw `\begin{bmatrix}`, an unknown macro, visible dollar-delimited math, or a page asking your browser to load browser-side MathJax, report it to the course team with the page URL or title.

Course pages may include numbered objects and static references. A result might appear as `Theorem 2.3.1`, an image as `Figure 2.3.1`, and practice work as a homework, problem, activity, or assignment reference. Numbered objects should appear as scannable course content where appropriate: theorem-like objects, examples, exercises, and assignments use the `scannable` reader style by default, while figures and tables keep `caption` presentation and equations keep `equation` presentation. These numbers, labels, anchors, and references are generated during build and published as static links; your browser should not need to calculate them or load a live reference service.

Numbered content appears as static labels and links, such as `Theorem 3.1`, `Figure 3.1`, or `Activity 3.3`. Proof headings such as `Proof of Activity 3.3` are generated during build; the browser does not calculate references.

Rendered proof headings name the object being proved, and math inside the proof should already be typeset during build. The page should not need a browser-side MathJax request to display the proof. If you see raw source syntax or raw TeX instead of a rendered proof, report it to the course team with the page URL or title.

Proofs, solutions, hints, and answers should appear as static course content.
Proofs stay open when they are part of the explanation. Hints, solutions, and
answers may start collapsed so you can reveal them only when you want support.
Opening one does not submit an answer, save progress, contact a backend, or
ask your browser to render MathJax. When a block names a theorem, problem,
activity, homework, figure, table, or equation, that heading should already be
resolved before the page reaches your browser.

Some pages may include linked scripts or notebooks. These are copied as readable files and may show source previews, but the static build labels them as not executed. Unlinked course source files are not part of the page artifact. Use course instructions when a class expects you to run code locally, in Docker, or through a future accepted execution workflow.

Fenced code examples may include a `Copy` button. Copying puts the displayed code text on your clipboard; it does not run the code, save progress, or contact a backend.

Some courses include runtime metadata for future local or Docker execution. In the current static artifact, that metadata only explains intended profiles, policies, and cache keys. It does not mean the web page has already run the code.

When a course asks you to run code, use the exact target named by the course team, such as `raya run . manual-script` from the course root or the Docker command they provide. `--dry-run` shows what would run before it runs. Cache-policy targets may reuse previous generated output unless the course asks for `--refresh`.

Some pages may show reviewed output panels. Reviewed output is course support that the course team has frozen into source review, so it can be shown statically without rerunning code. It is different from your personal work and from generated-only local logs. If reviewed output is stale or missing, the course artifact should fail before publishing it as current.

Static pages show a focused reading view. Internal hashes, cache keys, source paths, artifact paths, and runtime details are kept out of the normal page flow; they are for professors, contributors, agents, or tools inspecting the artifact.

If a professor shares a local preview URL, it is the same generated static site served from `artifact/site/`. Opening a preview page does not run course code or notebooks. Follow explicit course instructions when computation is part of the class.

Use role documentation as guidance. Use course pages and official learning objects as course material. If documentation and course material conflict, the course team and accepted OpenSpec specs or `docs/foundation/` authority decide what changes.

Rendered repository documentation may be browsed as static pages, but it remains guidance about the framework. It is not the same authority surface as a course team's official course artifact.
