---
id: course-first-shell-hierarchy-design
title: Course-First Shell Hierarchy Design
status: active
workflow: superpowers
---
# Course-First Shell Hierarchy Design

## Goal

Make the first-screen course shell state the ordered course hierarchy before
optional workspace context:

```text
course -> ancestor unit/section -> current page -> ordered neighbors
```

## Scope

This loop touches the current static course shell only:

- top command-bar reading context;
- course-map current-page chip;
- supporting CSS/tests for those surfaces.

It preserves the current Search, Graph, Practice, Tasks, Schedule, right-rail,
MathJax, skin, and artifact contracts.

## UX Assertions

- On a nested page, the command bar renders the course title, each ancestor page,
  the current page, structural page position, and compact Previous/Next links in
  that order.
- Ancestor labels in the command bar are links to deployment-neutral rendered
  page paths.
- The course-map current chip includes the active ancestor path and current page,
  not only the current page title.
- The hierarchy text remains structural course position. It must not use
  progress, mastery, recommendation, ranking, completion, or personalization
  language.

## Test Surface

Use `examples/courses/minimal` because it has the smallest stable nested
hierarchy:

```text
Minimal Course Fixture -> First Unit -> First Topic
```

Primary verification starts with
`tests/contracts/test_static_builder.py::test_render_fixture_uses_static_learning_shell`
and the existing minimal-shell assertions around course map, breadcrumbs, and
sequence links.
