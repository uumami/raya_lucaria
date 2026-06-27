---
id: desktop-learning-workspace-breathing-room
title: Desktop Learning Workspace Breathing Room
status: ready
date: 2026-06-27
workflow: superpowers
---

# Desktop Learning Workspace Breathing Room

## Problem

The current course shell is functionally rich, but the desktop reader can still feel cramped because the shell preserves narrow fixed side columns and does not gain enough article space when the course map or learning context is collapsed. The visible result can feel like a mobile-first page stretched onto desktop instead of a continuous learning workspace.

## Design

Keep the existing static shell architecture, generated navigation, learning rail, comfort controls, and non-persistent state rules. Improve only the desktop layout proportions and collapse affordance quality:

- wider desktop shell at large viewports;
- existing side rail proportions preserved so map/context affordances stay stable;
- main article and command bar gain width through a larger desktop workspace cap;
- collapsed map/context rails remain operable, compact, and visible;
- collapsing one or both rails must materially increase available article width;
- mobile and tablet layouts stay article-first and drawer-based.

This is a renderer presentation change only. It must not add browser-side MathJax, external requests, backend behavior, progress state, recommendation language, or persistent layout state.

## Testing

Use browser-driven e2e coverage against the render fixture:

- assert large desktop shell width uses available viewport space without horizontal overflow;
- assert expanded desktop rails preserve a wide article region;
- assert collapsing map and context increases article width;
- assert collapsed rails remain visible, operable, and compact;
- keep existing no-overflow, accessibility, reduced-motion, and render-debug gates passing.

## Documentation

The existing learning renderer contract already permits coordinated shell transitions, explicit map/context collapse, and desktop-focused layout behavior. This slice does not change authoring contracts or role workflows, so no role-guide wording is required unless implementation changes visible labels.
