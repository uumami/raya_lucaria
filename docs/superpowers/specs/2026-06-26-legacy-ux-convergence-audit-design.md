---
id: superpowers-legacy-ux-convergence-audit-design
title: Legacy UX Convergence Audit Design
status: accepted
---
# Legacy UX Convergence Audit Design

## Context

The active Superpowers goal is to fuse the useful UX/UI capabilities from the
legacy `main` branch into `new_rayalucaria` without inheriting legacy
architecture. The current branch has rebuilt many of the valuable ideas:
collapsible reader rails, responsive course map, local search, graph workspace,
skins, OpenDyslexic, text size, static official workspaces, print handouts, and
graph relationship comprehension.

The remaining risk is duplicated or misaligned work. The old branch contains
features that are useful as UX references but not acceptable as implementation
models, including Eleventy templates, Tailwind build assumptions, CDN
Cytoscape, browser-side theme stylesheet switching, service worker behavior,
and localStorage for navigation state. The current branch also contains many
Superpowers specs and plans, so the next useful step is an explicit convergence
inventory that maps old features to current status and future subgoals.

## Goal

Create a source-backed legacy UX convergence inventory that tells future loops
what has already converged, what must not be ported, and what remains worth
building under the current static renderer contracts.

## Design

Add a single Superpowers audit document under `docs/superpowers/` rather than a
foundation contract. The document is a working project-management surface for
this active Superpowers goal; it does not outrank `docs/foundation/` and does
not create new renderer behavior by itself.

The audit will contain:

- legacy `main` evidence: files and feature families inspected;
- current branch evidence: foundation contracts, current specs/plans, and
  implemented renderer surfaces;
- a convergence table with each legacy capability classified as `converged`,
  `adapted`, `rejected`, or `candidate`;
- explicit rejection reasons for legacy behavior that violates current
  contracts, especially external graph libraries, arbitrary browser-side theme
  switching, service-worker/offline behavior, and localStorage shell state;
- a prioritized next-subgoal list for remaining useful UX work;
- verification guidance for future loops.

The document should use concise language and concrete file references so
agents can act from it without relying on conversation memory.

## Non-Goals

- No code changes in this slice.
- No renderer contract change.
- No OpenSpec change.
- No generated artifact edits.
- No importing legacy code, CSS, Eleventy templates, package files, or CDN
  dependencies.
- No claim that the full UX fusion goal is complete.

## Verification

Verification for this slice is source inspection:

- `git status --short --branch` confirms only intended audit/spec/plan files
  changed before commit.
- A literal placeholder scan over the new audit files confirms there are no
  unfinished-work markers or forbidden recommendations.
- Independent review should check whether the inventory is faithful to both
  `main` and current contracts, and whether the proposed next subgoals are
  actually aligned with the active objective.
