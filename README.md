# Raya Lucaria

Raya Lucaria is an open-source educational framework and commons for serious university-level courses. It is not a SaaS product. The framework must remain portable across static hosting, local machines, on-premise deployments, free tiers, and paid infrastructure.

This repository is being reset to a foundation-first starting point. Legacy code, examples, specs, and guides may still exist during cleanup, but they are historical material unless reintroduced through the current foundation.

## Truth Hierarchy

- Seed truth: `docs/foundation/`.
- Future specs: regenerated OpenSpec specs derived from the foundation.
- Operational guidance: `README.md`, `AGENTS.md`, and agent/editor adapters.
- Examples, packages, and deployment recipes: valid only after they are rebuilt against current contracts.
- Historical material: Git history, old branches, archived changes, and legacy code.

See `docs/foundation/13_truth_surfaces.md`.

## Foundation Map

- `docs/foundation/01_charter.md`: identity and non-negotiable principles.
- `docs/foundation/02_system_model.md`: source, artifacts, installations, and workflows.
- `docs/foundation/05_course_contract.md`: future course source contract.
- `docs/foundation/06_artifact_contract.md`: future static artifact contract.
- `docs/foundation/08_package_boundaries.md`: clean package map for rebuilding.
- `docs/foundation/11_iteration_roadmap.md`: order of work after the reset.

## Current State

No implementation stack is canonical yet. The next correct work is to regenerate specs and build the first contracts outward: schema, minimal fixture, CLI, static builder, then dynamic services.

Useful reset check:

```bash
find docs/foundation -maxdepth 1 -type f | sort
rg -n "Glintstone|Eleventy|Tailwind|Pagefind|clase" docs/foundation
```
