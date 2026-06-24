---
id: superpowers-discovery-active-context-design
title: Discovery Active Context Design
summary: Make Search and Practice discovery surfaces inspectable through hover, focus, and keyboard without adding learner state.
status: ready
---
# Discovery Active Context Design

## Problem

The graph workspace already behaves like an inspectable learning surface: a reader can focus a page, inspect its public metadata, and hand off to the article or adjacent discovery surfaces. Search and Practice are less consistent. Search supports keyboard movement in the input, but hover and tab focus do not activate result context. Practice filters objects and updates the context panel from the first visible object, but it has no selected/active object state, no keyboard object movement, and no visible active-card state.

This creates unnecessary friction for students who scan with a mouse, tab through links, or compare practice objects before opening the owning page.

## Selected Approach

Use **Search and Practice active context parity**.

- Search keeps its existing local query, fuzzy matching, keyboard movement, and graph/page handoffs. Add pointer and focus activation for visible result cards so the context panel follows the item the reader is inspecting.
- Practice gets the same transient active-object model: visible object cards can become active by hover, focus, or keyboard movement. The context panel follows the active object when one exists, otherwise it falls back to the first visible object.
- Active state remains transient page UI state. It is not persisted, scored, recommended, adaptive, or personalized.

## Alternatives Considered

1. **Practice-only active object**: smaller and directly addresses the largest gap, but leaves Search and Practice feeling inconsistent.
2. **Search and Practice active context parity**: recommended and selected. It gives all discovery surfaces the same inspection pattern while staying static and bounded.
3. **Graph keyboard/pan/deep-link expansion**: useful later, but the graph already has stronger inspection behavior than Practice. Doing it now would delay a more immediate student-facing fix.

## Behavior

### Search

Search result cards remain generated from public page metadata. Existing input keyboard behavior continues:

- `ArrowDown` and `ArrowUp` move through visible results.
- `Enter` opens the active result.
- `Escape` clears the query and active result.

New behavior:

- Pointer entering a visible result makes that result active.
- Focus moving into a visible result makes that result active.
- The active result keeps `data-raya-search-active="true"`.
- The context panel uses the active result when present and falls back to the existing best visible result behavior when no result is active.

### Practice

Practice object cards remain generated from accepted official objects and link back to owning page anchors.

New behavior:

- Every object card exposes `data-raya-practice-active="false"` initially.
- Pointer entering a visible object makes that object active.
- Focus moving into a visible object makes that object active.
- `ArrowDown` and `ArrowUp` on the practice search input move through visible objects.
- `Enter` opens the active object's owning page link when an object is active.
- `Escape` and Clear reset query, type filter, and active object.
- Filtering or typing clears the active object; context falls back to the first visible object until the reader actively inspects one.
- Active object styling is visible and keyboard-friendly.

## Static Boundary

This design does not introduce runtime fetches, browser-side data hydration, storage, analytics, scoring, attempts, recommendations, mastery, progress, or adaptive behavior. It uses only the embedded static payload and DOM already published with the generated Search and Practice pages.

Reader comfort preferences remain the only accepted local storage use in the renderer; Search and Practice active context must not write to `localStorage` or `sessionStorage`.

## Documentation Impact

Update the learning renderer contract to state that generated Search and Practice workspaces support transient active context by hover, focus, and keyboard. Update student and agent role docs in English and Spanish so humans and coding agents know how to inspect and verify these surfaces.

## Test Strategy

Use TDD.

- Contract tests assert the generated Practice object markup includes inactive active-state hooks, the Practice script contains keyboard and pointer/focus active-object behavior, active styling exists, and forbidden runtime/storage tokens remain absent.
- Browser tests assert Search hover/focus updates the active result and context, Practice hover/focus updates the active object and context, keyboard movement activates visible Practice objects, Enter opens the active object, and Clear/Escape reset active state.
- Existing graph/search/practice static-read-path tests continue to guard no external requests, local resources, and deployment-neutral links.

## Self-Review

- No placeholders or deferred requirements remain.
- The design stays inside current static renderer authority and does not infer learning relationships.
- The behavior is bounded to Search and Practice and does not require schema changes.
- The selected approach is small enough for one implementation plan and one verification pass.
