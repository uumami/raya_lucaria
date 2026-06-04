---
id: docs-guides-en-agents
title: Agents
summary: Guidance for coding and learning agents working through explicit files, commands, specs, and diagnostics.
status: ready
---
# Agents

Agents operate through explicit files, commands, OpenSpec specs, diagnostics, and authority boundaries. Agents inherit user authority and do not receive special trust.

Use `docs/foundation/13_truth_surfaces.md` for the authority map, accepted OpenSpec specs for testable contracts, and `AGENTS.md` for repository workflow.

For course content, treat source files as canonical and generated artifacts as rebuildable. Preserve `source: course`, the ordered `course/` tree, frontmatter `id`, `raya:<id>` links, colocated `_official/` and `_assets/` privacy, generated index markers, and manifest-declared data surfaces. Do not edit generated `artifact/` output as source truth.

For repository documentation, `docs/raya.yaml` renders the live docs through `docs/render-content/`. Edit `docs/foundation/` and `docs/guides/` as the readable source, update the ordered render tree when a rendered docs page is added or reordered, and use `raya validate docs` plus `raya build docs` before relying on the static docs artifact.

When updating documentation, keep English and Spanish role pages separate. Preserve English technical identifiers such as `raya`, `raya.yaml`, `source`, `course/`, `_official/`, `_assets/`, `artifact/`, `packages/static`, and `OpenSpec`.
