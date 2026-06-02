# Repository Guidelines

## Project Structure & Module Organization

Raya Lucaria is a foundation-first open educational framework and commons, not a product repo. Current seed truth lives in `docs/foundation/`. Legacy code, examples, and archived OpenSpec changes may be mined for principles, but they are not canonical after the reset. Future structure is defined in `docs/foundation/08_package_boundaries.md`.

## Build, Test, and Development Commands

No implementation command is canonical yet. Use documentation and spec checks during the reset:

- `find docs/foundation -maxdepth 1 -type f | sort` lists the surviving foundation set.
- `rg -n "Glintstone|Eleventy|Tailwind|Pagefind|clase" docs/foundation` catches stale implementation assumptions.
- `openspec validate --specs --strict` may be used only after specs are regenerated from the foundation.

## Coding Style & Naming Conventions

Keep new files explicit, small, and easy for humans and coding agents to inspect. Prefer plain package names (`cli`, `schema`, `static`, `core`, `web`, `ui`) and reserve lore names for concepts or UI labels when they improve clarity. Future course content uses `raya.yaml`, `content/`, and ordered learning quanta.

## Testing Guidelines

Write tests against current contracts, not legacy behavior. Start with schema, validation, fixture, CLI, and artifact contract tests. Keep examples minimal and labeled; examples must not accidentally define pedagogy or architecture.

## Commit & Pull Request Guidelines

Use short, imperative commit subjects. Pull requests should describe the change, list validation commands run, link related issues, and include screenshots for visible site, theme, navigation, or content rendering changes.

## Agent-Specific Instructions

Treat `docs/foundation/13_truth_surfaces.md` as the authority map. Do not preserve legacy docs in current guide paths merely because they exist; use Git history as the archive. Do not edit generated outputs, dependency folders, caches, or legacy code unless the current task explicitly includes the reset cleanup.
