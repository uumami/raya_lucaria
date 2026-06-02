# CLAUDE.md

This repository is the Raya Lucaria framework reset workspace. Production courses and installations should eventually be separate repos generated from templates; current implementation material is historical unless rebuilt from the foundation.

Authority order: `docs/foundation/`, then future regenerated OpenSpec specs, then root operational guidance, then rebuilt package/example/deploy docs. See `docs/foundation/13_truth_surfaces.md`.

## Current State

The repository is intentionally starting over from durable principles. Do not treat old Glintstone, Eleventy, course examples, archived changes, or package names as current architecture.

The surviving memory is:

- `docs/foundation/01_charter.md`
- `docs/foundation/02_system_model.md`
- `docs/foundation/03_pedagogy.md`
- `docs/foundation/04_ownership_permissions.md`
- `docs/foundation/05_course_contract.md`
- `docs/foundation/06_artifact_contract.md`
- `docs/foundation/07_cli_contract.md`
- `docs/foundation/08_package_boundaries.md`
- `docs/foundation/09_deployment_model.md`
- `docs/foundation/10_security_registration.md`
- `docs/foundation/11_iteration_roadmap.md`
- `docs/foundation/12_legacy_salvage.md`
- `docs/foundation/13_truth_surfaces.md`

## Reset Checks

```bash
find docs/foundation -maxdepth 1 -type f | sort
rg -n "Glintstone|Eleventy|Tailwind|Pagefind|clase" docs/foundation
```

## Guidance Boundary

`.claude/`, `.codex/`, and `.cursor/` are tooling adapters. They do not define pedagogy, architecture, infrastructure, package boundaries, or implementation truth.

## Generated Files

Do not edit generated outputs:

- `_site/` or nested example `_site/`,
- `node_modules/`,
- `.pytest_cache/`.
