# Repository Guidelines

## Project Structure & Module Organization

Raya Lucaria is a foundation-first educational framework. Treat `docs/foundation/` as the highest source of truth; read `00_index.md`, `15_system_overview.md`, and `13_truth_surfaces.md` before changing contracts or behavior.

OpenSpec remains available for future contract changes. When a user explicitly selects a Superpowers workflow, committed Superpowers design and plan documents may drive that loop, but `docs/foundation/` remains the highest source of seed truth and implementation must update the affected foundation, role, test, and contract surfaces.

Implementation packages live in `packages/`: `cli` owns the `raya` command, `schema` owns schemas and validators, and `static` owns the Glintstone builder. Tests live in `tests/`. Fixture courses and gallery material live under `examples/`; they are test material. Role docs live in `docs/guides/en/` and `docs/guides/es/`.

## Build, Test, and Development Commands

Docker Compose is the reference; local `uv` is supported.

- `./scripts/check.sh`: canonical host archive gate.
- `./scripts/check-docker.sh`: runs the Python/Raya checks in the reference container.
- `./scripts/smoke-test.sh`: validates, builds, and inspects temporary external courses.
- `./scripts/check-render-debug.sh`: focused browser/static parity checks for rendered fixtures; it writes `report.json` and `index.html` beside screenshots for local evidence only.
- `docker compose run --rm dev uv run pytest -q`: run Docker tests.
- `UV_PROJECT_ENVIRONMENT=.venv-local uv sync --python 3.10 --all-packages --dev`: prepare local development.
- `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q`: run local tests.
- `docker compose run --rm dev uv run raya validate examples/courses/minimal`: validate the minimal fixture.
- `docker compose run --rm dev uv run raya build examples/courses/minimal`: build the minimal fixture artifact.

Run host and Docker checks sequentially.

## Coding Style & Naming Conventions

Use Python 3.10. Keep files small and explicit. Prefer boring names and package boundaries from `docs/foundation/08_package_boundaries.md`. Course source uses `raya.yaml`, `source: course`, an ordered `course/` tree, and colocated `_official/`, `_assets/`, and `_reviewed/` support. Do not introduce legacy `content:`, root `official/`, or root source `assets/` layouts.

Generated artifacts are rebuildable and must not become source truth. Do not edit dependencies, caches, generated outputs, or legacy material unless explicitly required.

## Testing Guidelines

Write tests against current foundation contracts, not legacy behavior. Use temporary directories for throwaway courses. Use fixtures such as `examples/courses/reference-fixture`, `runtime-fixture`, `execution-fixture`, and `render-fixture` for focused behavior. Rendered HTML, browser resources, preview, and layout changes need static-read-path or browser-driven coverage.

## Commit & Pull Request Guidelines

Use short, imperative commit subjects, matching history such as `Compact course map controls`. Pull requests should describe the change, list validation commands run, link related issues, and include screenshots for visible rendering, navigation, or layout changes.

## Agent-Specific Instructions

If lower surfaces conflict with `docs/foundation/`, update the lower surface or propose a foundation change. For foundation work, update the smallest relevant foundation file and keep `docs/foundation/00_index.md` accurate. For implementation work, prefer OpenSpec proposals/specs from accepted foundation decisions before package code.
