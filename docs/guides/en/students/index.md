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

Static pages may include math, highlighted code, tables, callouts, footnotes, heading anchors, and page contents. These are readable without accounts or a backend. Displayed code is not run by the static page unless a future course explicitly adds an accepted execution workflow.

Some pages may include referenced scripts or notebooks. These are copied as readable files and may show source previews, but the static build labels them as not executed. Use course instructions when a class expects you to run code locally, in Docker, or through a future accepted execution workflow.

Some courses include runtime metadata for future local or Docker execution. In the current static artifact, that metadata only explains intended profiles, policies, and cache keys. It does not mean the web page has already run the code.

When a course asks you to run code, use the exact target named by the course team, such as `raya run . manual-script` from the course root or the Docker command they provide. `--dry-run` shows what would run before it runs. Cache-policy targets may reuse previous generated output unless the course asks for `--refresh`.

Use role documentation as guidance. Use course pages and official learning objects as course material. If documentation and course material conflict, the course team and accepted OpenSpec specs or `docs/foundation/` authority decide what changes.

Rendered repository documentation may be browsed as static pages, but it remains guidance about the framework. It is not the same authority surface as a course team's official course artifact.
