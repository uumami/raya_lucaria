---
id: native-course-calendar-design
title: Native Course Calendar Design
status: approved
workflow: superpowers
created: 2026-08-10
---
# Native Course Calendar Design

## Problem

Raya's current Schedule workspace is a dated view of official assignment,
exam, project, and task metadata. It cannot represent ordinary class sessions,
holidays, cancelled meetings, or course milestones without misclassifying them
as tasks. That makes a course calendar incomplete and creates false task
semantics.

The legacy FDD and IA course templates demonstrate a useful student experience:
one calendar combines scheduled class topics, holidays, homework, projects, and
exams in month and agenda views. Their CSV, preprocessing scripts, and
Eleventy templates are historical material only; this design adopts the
behavior through Raya's source and artifact contracts.

## Goals

1. Give every Raya course one official, static, student-facing Calendar.
2. Let authors enter only sessions, holidays, and milestones that cannot be
   inferred from existing official learning objects.
3. Automatically derive assignment, exam, project, and task dates from their
   validated official metadata without duplicate authoring.
4. Preserve a portable static artifact with deployment-neutral links, no
   external fetches, no personal state, and no calendar synchronization.
5. Keep `/_raya/schedule/` valid while evolving its student-facing experience
   into Calendar.

## Non-Goals

- Importing legacy CSV files, depending on a spreadsheet, or retaining legacy
  preprocessing/Eleventy code.
- Inferring dates from unstructured prose.
- iCalendar feeds, external calendar synchronization, reminders, notifications,
  subscriptions, grades, submissions, personal completion state, or analytics.
- A recurrence language in version one. Explicit session entries are safer for
  changed topics, closures, make-up classes, and review.

## Source Contract

Each academic term has one authored official calendar document:

```text
course/_official/calendar/2026-o26.yaml
```

It is a term schedule rather than an individual learning object. It contains
one course-level `id`, `authority: official`, `scope.quantum: course-root`, an
IANA timezone, and an ordered `events` list. Every event has a stable `id`.

```yaml
id: ia-o26-calendar
type: calendar
authority: official
scope:
  quantum: course-root
timezone: America/Mexico_City
events:
  - id: session-01
    kind: session
    date: "2026-08-10"
    start_time: "16:00"
    end_time: "18:00"
    title: Introducción a la Inteligencia Artificial
    page: introduccion

  - id: independence-day
    kind: holiday
    date: "2026-09-16"
    title: Descanso obligatorio
    summary: No hay clase.
```

Version-one event kinds are `session`, `holiday`, and `milestone`. `page` is
optional and, when present, must resolve to a course page stable ID. Events use
date-only ISO values; time is optional and has `HH:MM` local-clock format.

The calendar's `timezone` is an IANA identifier such as
`America/Mexico_City`, never a fixed GMT offset. It determines current-day
highlighting, timed-event ordering, and display. Date-only source values remain
civil dates and must not shift through UTC browser parsing.

## Automatic Derived Entries

Existing accepted official objects remain the only source for graded or
date-bound work. During build, the Calendar derives records from:

| Official object | Authored field | Derived calendar record |
| --- | --- | --- |
| assignment | `content.due` | Assignment deadline |
| exam | `content.due` | Exam |
| project | `content.due` | Project deadline |
| task | `content.due` | Task deadline |
| task-family object | `content.available` | Availability event |

Each derived record retains the official object ID, type, title, public
preview, tags, owning page/anchor, graph link, and authored date. Raya does not
guess dates from titles, instructions, Markdown, or any other prose. An
authored calendar event and a derived work record remain separate even if they
share a date; there is no fuzzy deduplication.

## Artifact Contract

The builder emits manifest-declared `data/calendar.json`. It combines authored
term events and derived dated official work into a normalized, chronological
static data product. Each record exposes a stable ID, kind/type, title,
date/time, public summary, optional owning page, and deployment-neutral link.

`data/tasks.json` remains the existing task-family planning index. The calendar
index is an additional generated artifact surface, not a new canonical source,
calendar feed, reminder system, or learner-state record.

## Rendered Calendar Workspace

`/_raya/schedule/` remains a supported URL and becomes the Calendar workspace.
Its primary heading and navigation label are `Calendar`; compatibility labels
may retain Schedule where necessary for stable existing controls or links.

The workspace provides:

- agenda view, chronological and grouped by month;
- month view, with all events displayed on their civil date;
- filters for All, Sessions, Holidays, Milestones, Assignments, Exams,
  Projects, Tasks, and Availability;
- clear type badges/colors and links to the owning page or official anchor;
- `?page=<page-id>` focus behavior consistent with other workspaces; and
- a timezone-correct today highlight.

View choice is URL-only or volatile DOM state; it is not written to browser
storage. The workspace uses only generated local JSON/embedded data and local
resources. It makes no network request and does not expose private source,
calendar synchronization, grade, due-state, progress, mastery, or
recommendation behavior.

## Validation

Validation rejects calendar documents with:

- an invalid or duplicate document/event ID;
- invalid IANA timezone, event kind, ISO date, or local time;
- `end_time` not later than `start_time` on the same event;
- missing title; or
- an unresolved `page` stable ID.

Validation also keeps the existing official-object date checks. Derived records
are built only from accepted public official objects with valid authored dates.

## IA O26 Adoption

IA O26 is the first reference adoption after the framework change merges.

1. Add one `2026-o26.yaml` term calendar with every Monday/Wednesday session,
   its topic, ITAM holidays, and course milestones.
2. Replace the current calendar-only fake task objects with real calendar
   events.
3. Add future homework, projects, and exams as normal official Raya objects;
   they will appear automatically in Calendar.
4. Build, inspect, deploy, and verify the Calendar under `/ia_o26/`.

## Truth-Surface And Test Changes

Implementation updates the smallest relevant parts of the course, artifact,
and learning-renderer foundation contracts; schema/docs for authors and role
guides; artifact validators; fixtures; static builder tests; browser calendar
tests; and manifest/index assertions. Tests cover validation, timezone-safe
date handling, automatic derived records, absence of duplicated authoring,
month/agenda rendering, filters, accessible links, URL focus, local-only
resources, no storage/fetch, desktop/mobile overflow, and deployment below a
path prefix.

## Self-Review

- The calendar document owns only non-inferable academic schedule information.
- Official work remains authored once and is automatically derived.
- The design introduces one new source document type and one generated index,
  not a legacy import pipeline or dynamic calendar product.
- IA O26 is a downstream reference adoption, not a framework exception.
