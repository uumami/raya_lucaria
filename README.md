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

- `docs/foundation/15_system_overview.md`: newcomer map with core concepts and ASCII diagrams.
- `docs/foundation/01_charter.md`: identity and non-negotiable principles.
- `docs/foundation/02_system_model.md`: source, artifacts, installations, and workflows.
- `docs/foundation/05_course_contract.md`: future course source contract.
- `docs/foundation/06_artifact_contract.md`: future static artifact contract.
- `docs/foundation/08_package_boundaries.md`: clean package map for rebuilding.
- `docs/foundation/11_iteration_roadmap.md`: order of work after the reset.
- `docs/foundation/14_domain_language.md`: canonical Raya Lucaria domain names.

## Current State

The first implementation baseline is Docker/uv/Python:

- Docker Compose is the reference development workflow.
- `uv` is the Python environment and package tool.
- `raya` is the Python CLI entrypoint.
- `packages/schema` owns portable contracts and validation helpers.
- `packages/cli` owns the command surface.
- `packages/static` owns the first Glintstone static artifact builder.

Renderer, TypeScript/web UI, backend, identity, and dynamic study-state choices remain out of scope until later proposals.

## Development Commands

Reference Docker workflow:

```bash
docker compose run --rm dev uv run raya --help
docker compose run --rm dev uv run raya doctor
docker compose run --rm dev uv run raya course --help
docker compose run --rm dev uv run raya validate examples/courses/minimal
docker compose run --rm dev uv run raya build examples/courses/minimal
docker compose run --rm dev uv run raya artifacts inspect examples/courses/minimal/artifact
docker compose run --rm dev uv run pytest -q
```

Local non-Docker workflow:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv sync --python 3.10 --all-packages --dev
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya --help
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya doctor
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya course --help
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate examples/courses/minimal
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/minimal
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya artifacts inspect examples/courses/minimal/artifact
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q
```

External-course smoke test:

```bash
./scripts/smoke-test.sh
```

The smoke test copies the minimal fixture into a temporary directory outside the repository, validates, builds, and inspects it locally, validates, builds, and inspects it through Docker with an explicit temporary mount, and removes the temporary files afterward.

Artifact inspection is read-only and manifest-centered: it validates `manifest.json`, required artifact directories, and manifest-declared data indexes without rebuilding source.

Course initialization creates replaceable scaffold and refuses to overwrite non-empty directories:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya course init /tmp/raya-course-demo --course-id raya-course-demo --title "Raya Course Demo"
```

Useful reset check:

```bash
find docs/foundation -maxdepth 1 -type f | sort
rg -n "Eleventy|Tailwind|Pagefind" docs/foundation -g '!14_domain_language.md'
```
