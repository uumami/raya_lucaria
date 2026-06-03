# CLAUDE.md

This repository is the Raya Lucaria framework reset workspace. Production courses and installations should eventually be separate repos generated from templates; current implementation material is historical unless rebuilt from the foundation.

Authority order: `docs/foundation/`, then future regenerated OpenSpec specs, then root operational guidance, then rebuilt package/example/deploy docs. See `docs/foundation/13_truth_surfaces.md`.

## Current State

The repository is intentionally starting over from durable principles. Glintstone and the other Raya Lucaria domain names are canonical concepts, but old Eleventy renderer assumptions, course examples, archived changes, and package names are not current architecture.

The surviving memory is:

- `docs/foundation/15_system_overview.md`
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
- `docs/foundation/14_domain_language.md`

## Reset Checks

```bash
find docs/foundation -maxdepth 1 -type f | sort
rg -n "Eleventy|Tailwind|Pagefind" docs/foundation -g '!14_domain_language.md'
```

## Development Commands

Docker Compose is the reference workflow:

```bash
docker compose run --rm dev uv run raya --help
docker compose run --rm dev uv run raya doctor
docker compose run --rm dev uv run raya course --help
docker compose run --rm dev uv run raya validate examples/courses/minimal
docker compose run --rm dev uv run raya build examples/courses/minimal
docker compose run --rm dev uv run raya artifacts inspect examples/courses/minimal/artifact
docker compose run --rm dev uv run pytest -q
./scripts/smoke-test.sh
```

Local `uv` workflow:

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

The current implementation baseline is Python 3.10, `packages/schema`, `packages/cli`, and `packages/static`. Renderer, TypeScript/web UI, backend, identity, and dynamic study state remain out of scope for this baseline.

Use temporary directories for throwaway course validation/build/inspection scenarios. The smoke test copies the minimal fixture outside the repository, validates, builds, and inspects that external course locally and through Docker, then cleans up the temporary files.

Artifact inspection is read-only and manifest-centered. It validates `manifest.json`, required artifact paths, and manifest-declared data indexes without rebuilding source course files.

Generated artifacts keep artifact-root machine surfaces separate from browser static resources. `manifest.json`, `data/*.json`, and artifact-level `assets/` are inspectable artifact surfaces; rendered pages under `site/` use `site/_raya/assets/` for browser-facing local assets.

Course validation catches broken local `.md` content links under configured `content/` and missing local asset references under configured/default `assets/` before build. External URLs, `mailto:`, `tel:`, and fragment-only links are ignored locally. Graph UI, backlinks, wikilinks, heading-anchor validation, and external link policy remain future work.

Course initialization creates replaceable scaffold only. It refuses non-empty target directories and must not be treated as required pedagogy or official course canon.

## Guidance Boundary

`.claude/`, `.codex/`, and `.cursor/` are tooling adapters. They do not define pedagogy, architecture, infrastructure, package boundaries, or implementation truth.

## Generated Files

Do not edit generated outputs:

- `_site/` or nested example `_site/`,
- `artifact/` or nested example `artifact/`,
- `node_modules/`,
- `.pytest_cache/`.
