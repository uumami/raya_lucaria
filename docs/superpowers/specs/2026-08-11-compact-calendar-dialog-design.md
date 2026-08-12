---
id: compact-calendar-dialog-design
title: Compact Calendar Dialog Design
status: approved
workflow: superpowers
created: 2026-08-11
---
# Compact Calendar Dialog Design

## Goal

Make the Calendar readable at a glance: compact month cells on wide screens,
an accessible day-detail dialog, and an agenda-first enhanced view on phones.

## Behavior

- Desktop and tablet open on Month. Each day shows at most two one-line event
  buttons, then a filtered `+N more` button.
- Phone opens on Agenda. Month remains available; phone cells show date plus
  compact textual/count indicators, never wrapped titles.
- A chip opens one reusable native `<dialog>` for its date and identifies the
  selected event. `+N more` opens the same dialog with all matching events.
- The dialog presents full titles, textual kind/type, times, summaries, tags,
  and real page/graph links. Unowned events have no dead action.
- Escape closes an open dialog first and restores exact opener focus. Only a
  later Escape clears Calendar filters/page focus. Clear preserves month/view.
- Filtering precedes compact limits and `+N` counts. It never changes the
  selected month. One visible summary plus one polite visually-hidden live
  region reports empty-month/filter results.

## Static And Accessibility Boundaries

- `data/calendar.json` remains the sole normalized public artifact data.
- Agenda is server-rendered and useful without JavaScript. JS hides it only
  after successfully mounting the selected enhanced view.
- Keep semantic month table/caption/Monday headers/full-date time labels and
  textual labels; colors are supplemental. Chips and overflow are buttons,
  never nested interactive elements.
- The dialog has labelled heading, close control, focus restoration, scrollable
  mobile-safe body, and `100dvh`/safe-area styling. It is one dialog, not one
  dialog per event.
- Calendar JS remains local and performs no fetch/XHR/storage. Existing shared
  Course-map shell persistence is separately scoped.

## Scope

Update Calendar renderer/JS/CSS, the smallest affected foundation/rendering
contract, and browser/static tests. Do not change calendar source schema,
artifact shape, DNS, or course-specific behavior.

## Acceptance

Test caps after filters, dialog keyboard/focus/Escape precedence, 320px and
zoom/large-text overflow, no-JS agenda, local-only requests, path-prefix
links, persistent Course map, and no duplicate visible status.
