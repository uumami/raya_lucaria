---
id: course-first-shell-hierarchy-plan
title: Course-First Shell Hierarchy Plan
status: active
workflow: superpowers
---
# Course-First Shell Hierarchy Plan

## Plan

1. Add contract assertions for nested command-bar hierarchy and current-map chip
   hierarchy using the minimal fixture.
2. Update the static builder helpers to render ancestor links between the course
   title and current page in the reading context.
3. Update the course-map current chip to include compact active-path text and an
   accessible current-path label.
4. Add or adjust CSS so the hierarchy wraps cleanly in command-bar and map chip
   layouts without changing shell persistence or workspace contracts.
5. Run focused contract tests, then the focused browser shell test. Use the full
   archive gates only after the slice is complete.

## Completion Evidence

Record focused tests, render-debug/browser evidence if visible behavior changes,
adversarial review outcome, and final host/Docker gates in
`docs/superpowers/course-first-ux-goal.md`.
