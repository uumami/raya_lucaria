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

For rich static rendering, preserve the Glintstone boundary: rewrite links through Raya rules, generate page-local anchors and tables of contents from source headings, keep support files under `site/_raya/`, escape raw HTML, and do not execute code blocks. Test generated HTML and static read paths instead of relying on a browser framework.

For code and notebook references, treat `code/` and `notebooks/` as private source support owned by the nearest learning quantum. Validate links before build, block private or cross-quantum references, copy referenced files to both artifact and browser-facing file surfaces, update `references.json`, and never infer execution from previews.

For runtime metadata, treat `runtime/profiles.yaml`, root `pyproject.toml`, and `uv.lock` as source support outside learning order. Validate and emit runtime, execution-plan, and cache metadata, but never call `uv`, Docker, kernels, package installers, notebooks, scripts, or cache refreshes unless a later accepted execution contract explicitly says to do so.

For repository documentation, `docs/raya.yaml` renders the live docs through `docs/render-content/`. Edit `docs/foundation/` and `docs/guides/` as the readable source, update the ordered render tree when a rendered docs page is added or reordered, and use `raya validate docs` plus `raya build docs` before relying on the static docs artifact.

When updating documentation, keep English and Spanish role pages separate. Preserve English technical identifiers such as `raya`, `raya.yaml`, `source`, `course/`, `_official/`, `_assets/`, `artifact/`, `packages/static`, and `OpenSpec`.
