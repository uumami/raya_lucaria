---
id: native-course-calendar-design
title: Native Course Calendar Design
status: revised after adversarial review
workflow: superpowers
created: 2026-08-10
---
# Native Course Calendar Design

## Problem

Raya's Schedule is currently a dated view of official task-family metadata. It
cannot represent ordinary class sessions, holidays, cancelled meetings, or
course milestones without misclassifying them as tasks. Legacy FDD and IA
templates combine those dates successfully, but their CSV, scripts, and
Eleventy templates are historical material, not framework dependencies.

## Goals And Boundaries

Every course gets one static student-facing Calendar. Authors enter only
non-inferable sessions, holidays, cancellations, and milestones; Raya derives
all dated assignments, exams, projects, and tasks from their validated official
metadata. The Calendar is not a feed, reminder system, sync adapter, gradebook,
personal state, analytics surface, or prose-date extractor. Version one has no
recurrence language: explicit sessions are safer for changed topics and
closures.

## Source Contract

`raya.yaml` owns the single effective timezone for the whole course:

```yaml
calendar:
  timezone: America/Mexico_City
```

Each term has one separately discovered official calendar document:

```text
course/_official/calendar/1_2026-o26.yaml
```

This is a calendar-document family, not an official learning-object family. It
is excluded from generic official-object discovery and `data/official.json`,
but uses the ordinary ordered filename rule. It has `authority: official`,
`scope.quantum: course-root`, one stable document ID, and ordered events:

```yaml
id: ia-o26-calendar
type: calendar
authority: official
scope:
  quantum: course-root
events:
  - id: session-01
    kind: session
    date: "2026-08-10"
    start_time: "16:00"
    end_time: "18:00"
    title: Introducción a la Inteligencia Artificial
    page: course-root

  - id: independence-day
    kind: holiday
    date: "2026-09-16"
    title: Descanso obligatorio
    summary: No hay clase.
```

Version-one kinds are `session`, `holiday`, `milestone`, and `cancellation`.
`page` is optional but must resolve to a course page stable ID. Dates are ISO
civil dates; optional times are real 24-hour `HH:MM` local times. `end_time`
requires `start_time` and must be later on that event.

Document IDs, event IDs, and derived occurrences occupy one course-global
namespace. Calendar occurrence IDs are `calendar:<document-id>:<event-id>`;
derived occurrence IDs are `official:<object-id>:due` and
`official:<object-id>:available`. Validation rejects collisions.

## Automatic Derived Entries

Every validated official assignment, exam, project, or task contributes one
occurrence for each populated structured date field:

| Object | Field | Calendar occurrence |
| --- | --- | --- |
| assignment | `content.due` | Assignment deadline |
| exam | `content.due` | Exam |
| project | `content.due` | Project deadline |
| task | `content.due` | Task deadline |
| task-family object | `content.available` | Availability |

An object with both `available` and `due` therefore produces two occurrences.
Each preserves its source object ID, public allow-listed metadata, owning
page/anchor, graph target, tags, type, and date role. `content.due` remains the
canonical dated exam field in v1; legacy `exam.date` is not silently imported.
Raya never extracts dates from prose and never fuzzy-deduplicates a derived
record with an authored calendar event.

Validation adds strict `YYYY-MM-DD` checks for every populated `due` or
`available` field on task-family objects. Invalid values fail validation;
`status` remains display metadata and does not hide valid official work.

## Artifact Contract

The builder always emits manifest-declared `data/calendar.json` and
`/_raya/schedule/`, including for courses with no events:

```json
{"version": 1, "timezone": "America/Mexico_City", "events": [], "kinds": []}
```

Each normalized record has only allow-listed public fields: occurrence ID,
origin (`calendar` or `official`), source IDs, kind/type, date, optional times,
title, summary, tags, optional page ID, and optional output/anchor target.
The index never copies arbitrary object content. It is a generated artifact
surface; `data/tasks.json` remains the task planning index and neither is a
calendar integration or learner-state contract.

At render time, links are derived with `_relative_href` from the current output
path. This keeps `/ia_o26/` deployments correct. Calendar events without a
page render no dead action.

## Calendar Workspace

The compatibility URL remains `/_raya/schedule/`, but all visible UI says
**Calendar**. It retains the persistent Course map, marks Calendar active,
omits reader-only Context, and restores neither the legacy command bar nor the
legacy course rail.

The server renders a chronological, month-grouped agenda as the useful no-JS
baseline. Local progressive enhancement adds a month view, filters for all
event kinds/types, and Previous, Next, and Today controls. The initial month
is the course-timezone current month if it has events, otherwise the nearest
upcoming event month, then latest past event month, with a stable empty fallback.
Weeks start Monday; same-day records order all-day first, then start time,
source order, and occurrence ID.

The browser receives an escaped embedded copy of the normalized payload and
does not fetch `data/calendar.json`. Today uses timezone-aware `Intl` parts,
never `new Date("YYYY-MM-DD")` or a UTC round trip. View state is URL-only or
volatile DOM state, never browser storage.

Month markup is semantic and keyboard-operable: caption, weekday headers,
accessible view state, textual event badges, real links, and `aria-current`
plus text for today. It does not copy clickable divs, dot-only events,
tooltip-only details, or the legacy modal. Agenda remains available on narrow
screens. `?page=<id>` matches derived records owned by that page and authored
events whose `page` matches; unlinked course-wide holidays/milestones remain
visible, while Clear/Escape restores all records.

## Validation And Testing

Validation rejects invalid timezone, document/event IDs, kinds, dates, times,
time ordering, missing titles, unresolved pages, and global occurrence
collisions. Tests cover empty artifacts, due-plus-available derivation,
timezone boundaries, escaping including embedded `</script>` safety, source
privacy, no-JS agenda, keyboard navigation, focus/filters, no storage/fetch,
path-prefix links, persistent map behavior, desktop/mobile overflow, and
current-day highlighting.

## IA O26 Adoption

After framework merge, IA O26 adds `1_2026-o26.yaml` with each Monday/Wednesday
session, ITAM closures, and course milestones. It replaces only the five
calendar-only fake task objects with equivalent events, retains real work
objects, and adds future homework/projects/exams through normal official Raya
objects so they appear automatically. It then builds, inspects, deploys, and
verifies Calendar under `/ia_o26/` without DNS or course-specific renderer code.

## Truth Surfaces

Implementation updates the smallest relevant course, artifact, and
learning-renderer foundation contracts; schemas and validators; author/role
guides; artifact manifest validators; fixtures; static/browser tests; and the
Calendar workspace. IA O26 is a downstream reference adoption, not a framework
exception.

## Self-Review

- Calendar documents own only non-inferable academic schedule information.
- Official work is authored once and always derived from structured fields.
- The design adds one validated source family and one generated index, not a
  legacy import pipeline or dynamic calendar product.
