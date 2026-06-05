# Raya Lucaria

Raya Lucaria is an open-source educational framework and commons for serious university-level courses. It is not a SaaS product. The framework must remain portable across static hosting, local machines, on-premise deployments, free tiers, and paid infrastructure.

This repository is being reset to a foundation-first starting point. Legacy code, examples, specs, and guides may still exist during cleanup, but they are historical material unless reintroduced through the current foundation.

## Truth Hierarchy

- Seed truth: `docs/foundation/`.
- Future specs: regenerated OpenSpec specs derived from the foundation.
- Role documentation: `docs/guides/en/` and `docs/guides/es/`, below foundation/spec authority.
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
- `docs/foundation/16_documentation_surfaces.md`: role documentation and rendered-doc boundaries.

Role guides are split by language: English under `docs/guides/en/` and Spanish under `docs/guides/es/`. Technical identifiers such as commands, paths, package names, schema fields, and domain names remain in English.

## Current State

The first implementation baseline is Docker/uv/Python:

- Docker Compose is the reference development workflow.
- `uv` is the Python environment and package tool.
- `raya` is the Python CLI entrypoint.
- `packages/schema` owns portable contracts and validation helpers.
- `packages/cli` owns the command surface.
- `packages/static` owns the first Glintstone static artifact builder.

Course validation catches broken local Markdown content links and missing local asset references before build. The minimal builder exports navigation, parent, and valid source content links into `data/links.json`.

The generated artifact keeps machine-readable surfaces at the artifact root while making the browser static read path self-contained:

- `artifact/manifest.json` and `artifact/data/*.json` are for artifact inspection, agents, and future installations.
- `artifact/assets/` preserves copied source assets as artifact-level generated output.
- `artifact/site/` is the static read path.
- `artifact/site/_raya/assets/` contains browser-facing local assets referenced by rendered pages.
- `artifact/site/_raya/render/` contains generated rich-render support resources.

Glintstone now owns the first rich static rendering baseline: common Markdown, pipe tables, displayed code with highlighting, static math, callouts, footnotes, page-local heading anchors, and page tables of contents. Code blocks are display-only; execution, notebook execution, runtime profiles, TypeScript/web UI, backend, identity, dynamic study state, graph UI, backlinks, wikilinks, and expanded external link policy remain out of scope until later proposals.

The current code/notebook reference baseline is static and non-executing. Course pages may link to `.py` files under `code/` and `.ipynb` files under `notebooks/` owned by the page's learning quantum or an ancestor. Validation checks those references before build, copied files are written to `artifact/files/` and `artifact/site/_raya/files/`, and `artifact/data/references.json` records hash, paths, kind, format, and `not-executed` status.

The current runtime/cache baseline is also non-executing. Courses may declare root `pyproject.toml`, `uv.lock`, and `runtime/profiles.yaml` metadata for future local or Docker execution. Builds emit `data/runtime.json`, `data/execution.json`, and `data/cache.json` with profiles, policies, cache keys, and `not-executed` status; validation, build, artifact inspection, and static serving do not call `uv`, Docker, kernels, scripts, notebooks, or cache refreshes.

The current local execution baseline is explicit and target-scoped. `raya run <course> <target>` can run one validated script or notebook reference through the selected `uv` profile, optionally wrapped by Docker Compose with `--docker`. `--dry-run` prints the command shape without executing, `--refresh` reruns cache-policy targets, and generated logs, outputs, cache records, and `data/execution-results.json` stay under the artifact root. `raya validate`, `raya build`, `raya artifacts inspect`, and static serving remain non-executing.

## Development Commands

Reference Docker workflow:

```bash
docker compose run --rm dev uv run raya --help
docker compose run --rm dev uv run raya doctor
docker compose run --rm dev uv run raya course --help
docker compose run --rm dev uv run raya validate examples/courses/minimal
docker compose run --rm dev uv run raya build examples/courses/minimal
docker compose run --rm dev uv run raya validate examples/courses/reference-fixture
docker compose run --rm dev uv run raya build examples/courses/reference-fixture
docker compose run --rm dev uv run raya validate examples/courses/runtime-fixture
docker compose run --rm dev uv run raya build examples/courses/runtime-fixture
docker compose run --rm dev uv run raya validate examples/courses/execution-fixture
docker compose run --rm dev uv run raya run examples/courses/execution-fixture manual-script --dry-run
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
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate examples/courses/reference-fixture
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/reference-fixture
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate examples/courses/runtime-fixture
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/runtime-fixture
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate examples/courses/execution-fixture
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya run examples/courses/execution-fixture manual-script --dry-run
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya artifacts inspect examples/courses/minimal/artifact
UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q
```

External-course smoke test:

```bash
./scripts/smoke-test.sh
```

The smoke test copies the minimal fixture into a temporary directory outside the repository, validates, builds, and inspects it locally, validates, builds, and inspects it through Docker with an explicit temporary mount, and removes the temporary files afterward.

Rendered static-site behavior also has e2e/static-read-path coverage through `pytest -q tests/e2e`, using `examples/courses/render-fixture` as labeled fixture content.

Code/notebook reference behavior uses `examples/courses/reference-fixture` as labeled fixture content. The fixture proves static links, copied `_raya/files/` browser paths, artifact-level `files/`, and `references.json`; it does not define a pedagogy pattern or execute code.

Runtime metadata behavior uses `examples/courses/runtime-fixture` as labeled fixture content. The fixture proves `uv` profile metadata, Docker Compose service metadata, execution policy records, cache-key records, and no-execution sentinels; it does not define execution pedagogy or run code.

Local execution behavior uses `examples/courses/execution-fixture` as labeled fixture content. The fixture proves explicit `raya run` target selection, dry-run plans, policy refusals, cache reuse, refresh behavior, generated logs/results, and notebook output handling; it does not define pedagogy or run during static build.

Artifact inspection is read-only and manifest-centered: it validates `manifest.json`, required artifact directories, and manifest-declared data indexes without rebuilding source.

Source-course validation is local and source-oriented: local `.md` links must resolve under the configured authored source root, new courses use `source: course`, local asset references must resolve under the page's own `_assets/` directory or an ancestor `_assets/` directory inside the authored source tree, and rendered pages must not link into private support paths such as `_official/`. External URLs, `mailto:`, `tel:`, and fragment-only links are ignored by this baseline.

Local `.py` and `.ipynb` references are source support links, not page links. They must resolve under accepted `code/` or `notebooks/` support roots, and cross-quantum references fail until a future shared-code contract exists.

Local execution is a separate command, not a build side effect:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya run examples/courses/execution-fixture manual-script --dry-run
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya run examples/courses/execution-fixture cache-script
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya run examples/courses/execution-fixture cache-script --refresh
```

Course initialization creates replaceable scaffold and refuses to overwrite non-empty directories:

```bash
UV_PROJECT_ENVIRONMENT=.venv-local uv run raya course init /tmp/raya-course-demo --course-id raya-course-demo --title "Raya Course Demo"
```

Useful reset check:

```bash
find docs/foundation -maxdepth 1 -type f | sort
rg -n "Eleventy|Tailwind|Pagefind" docs/foundation -g '!14_domain_language.md'
```
