# Repository Guidelines

## Project Structure & Module Organization

Raya Lucaria is a foundation-first open educational framework and commons, not a product repo. The reset starts from contracts, specs, and package boundaries before implementation.

Current seed truth lives in `docs/foundation/`. Start with `docs/foundation/00_index.md` and `docs/foundation/15_system_overview.md`, then read `docs/foundation/13_truth_surfaces.md` for the authority map and the relevant foundation file for the task. Legacy code, examples, archived OpenSpec changes, and old guides may be mined for principles, but they are not canonical after the reset.

Role documentation lives under `docs/guides/en/` and `docs/guides/es/`. Keep English and Spanish role directories separate, with each role starting at an `index.md` page. Do not mix languages in one role page. Technical identifiers such as commands, paths, package names, schema fields, domain names, and stable IDs remain in English.

Future structure is defined in `docs/foundation/08_package_boundaries.md`: plain package names such as `cli`, `schema`, `static`, `graph`, `study`, `agents`, `collaboration`, `live`, `identity`, `core`, `web`, and `ui`. Domain names are defined in `docs/foundation/14_domain_language.md`; use them for conceptual ownership and user-facing language, not as default package directory names.

## Build, Test, and Development Commands

Docker Compose is the reference development workflow. Local `uv` execution remains supported.

- `./scripts/check.sh` is the canonical host archive gate.
- `./scripts/check-docker.sh` runs the Python/Raya verification path inside the reference container.
- `./scripts/smoke-test.sh` validates, builds, and inspects temporary external course copies locally and through Docker.
- `find docs/foundation -maxdepth 1 -type f | sort` lists the surviving foundation set.
- `rg -n "Eleventy|Tailwind|Pagefind" docs/foundation -g '!14_domain_language.md'` catches stale renderer assumptions outside the domain-language reset boundary.
- `openspec list --json` shows whether an active change already exists.
- `openspec validate --specs --strict` may be used only after specs are regenerated from the foundation.
- `docker compose run --rm dev uv run raya --help` runs the CLI through the reference container.
- `docker compose run --rm dev uv run raya doctor` reports detected context.
- `docker compose run --rm dev uv run raya course --help` shows course subcommands.
- `docker compose run --rm dev uv run raya validate examples/courses/minimal` validates the minimal fixture.
- `docker compose run --rm dev uv run raya build examples/courses/minimal` builds the minimal fixture artifact.
- `docker compose run --rm dev uv run raya validate examples/courses/reference-fixture` validates the code/notebook reference fixture.
- `docker compose run --rm dev uv run raya build examples/courses/reference-fixture` builds the code/notebook reference fixture.
- `docker compose run --rm dev uv run raya validate examples/courses/runtime-fixture` validates the runtime metadata fixture.
- `docker compose run --rm dev uv run raya build examples/courses/runtime-fixture` builds the runtime metadata fixture.
- `docker compose run --rm dev uv run raya validate examples/courses/execution-fixture` validates the explicit execution fixture without running targets.
- `docker compose run --rm dev uv run raya run examples/courses/execution-fixture manual-script --dry-run` checks the local execution plan without running code.
- `docker compose run --rm dev uv run raya outputs list examples/courses/execution-fixture` lists generated and reviewed output state without running code.
- `docker compose run --rm dev uv run raya artifacts inspect examples/courses/minimal/artifact` inspects the generated artifact through its manifest.
- `docker compose run --rm dev uv run pytest -q` runs tests through the reference container.
- `./scripts/smoke-test.sh` validates, builds, and inspects a temporary external course copy locally and through Docker without adding course output to the repository.
- `UV_PROJECT_ENVIRONMENT=.venv-local uv sync --python 3.10 --all-packages --dev` sets up the local non-Docker workflow.
- `UV_PROJECT_ENVIRONMENT=.venv-local uv run raya --help`, `UV_PROJECT_ENVIRONMENT=.venv-local uv run raya doctor`, `UV_PROJECT_ENVIRONMENT=.venv-local uv run raya course --help`, `UV_PROJECT_ENVIRONMENT=.venv-local uv run raya validate examples/courses/minimal`, `UV_PROJECT_ENVIRONMENT=.venv-local uv run raya build examples/courses/minimal`, `UV_PROJECT_ENVIRONMENT=.venv-local uv run raya run examples/courses/execution-fixture manual-script --dry-run`, `UV_PROJECT_ENVIRONMENT=.venv-local uv run raya artifacts inspect examples/courses/minimal/artifact`, and `UV_PROJECT_ENVIRONMENT=.venv-local uv run pytest -q` run the local workflow.

The current CLI baseline implements `raya --help`, `raya doctor`, `raya course init <path>`, `raya validate <course>`, `raya build <course>`, `raya run <course> <target>`, `raya outputs list <course>`, `raya outputs freeze <course> <target>`, and `raya artifacts inspect <artifact>`. Do not treat any legacy command as canonical unless current specs say so.

## Coding Style & Naming Conventions

Keep new files explicit, small, and easy for humans and coding agents to inspect. Prefer boring names over clever ones. Schemas and contracts sit below implementations; provider adapters belong at the edges.

Future course content uses `raya.yaml`, `source: course`, one ordered `course/` tree, colocated `_official/`, colocated `_assets/`, and ordered learning quanta as described in `docs/foundation/05_course_contract.md`. Do not add source `content:`, root `official/`, or root source `assets/` to new contracts, scaffolds, fixtures, or examples. Generated artifacts use the manifest-centered shape in `docs/foundation/06_artifact_contract.md`; generated data is rebuildable and must not become canonical course truth.

Artifact inspection is read-only and manifest-centered. It validates `manifest.json`, required artifact paths, and manifest-declared data indexes without rebuilding source course files.

Generated artifacts distinguish machine surfaces from browser-facing static resources. `manifest.json`, `data/*.json`, and artifact-level `assets/` remain artifact-root surfaces for inspection, agents, and future installations. Rendered browser pages under `site/` use `site/_raya/assets/` for local assets so the static read path can be served directly.

Course validation checks local Markdown source links and local asset references before build. Local `.md` links must point under the configured authored source root. Local asset references must point under the page's own `_assets/` directory or an ancestor `_assets/` directory inside the authored source tree; rendered pages must not link into private support paths such as `_official/`, `_drafts/`, or `_partials/`. External URLs, `mailto:`, `tel:`, and fragment-only links do not fail local validation in this baseline.

Local `.py` and `.ipynb` references are static source support, not rendered pages and not execution requests. Classify linked files by extension and keep them owned by the page's own learning quantum or an allowed ancestor; `code/`, `notebooks/`, `scripts/`, `helpers/`, and `labs/` are ordinary author folder names, not required support roots. Validation must reject missing files, malformed notebooks, private support paths, path escapes, and cross-quantum support references. Builds copy only validated linked files to `artifact/files/` and `artifact/site/_raya/files/`, and write manifest-declared `data/references.json` with `not-executed` status.

Runtime metadata is source support outside learning order. Keep `runtime/profiles.yaml`, root `pyproject.toml`, and `uv.lock` beside `course/`; do not put runtime profiles inside ordered pages. Runtime validation and build output may read metadata and write `data/runtime.json`, `data/execution.json`, and `data/cache.json`, but must not execute scripts, notebooks, `uv`, Docker, kernels, package installers, or cache refreshes.

Local execution is explicit and target-scoped. Use `raya run <course> <target>` only when the current task requires execution; prefer `--dry-run` when checking command shape. `raya run` may write generated logs, outputs, cache records, and `data/execution-results.json` under the artifact root. It must not promote generated outputs to source truth, and it must not become an implicit part of `validate`, `build`, artifact inspection, or static serving.

Reviewed execution output is source support, not generated artifact truth. Keep reviewed files under colocated `_reviewed/execution/<target>/`. Use `raya outputs list <course>` to inspect generated/reviewed/frozen state and `raya outputs freeze <course> <target>` only after a current successful generated result exists. Freeze copies files into `_reviewed/` and writes metadata for human source review; it must not execute. `policy: frozen` validates current reviewed output and fails if metadata or files are stale or missing.

Rendered pages are reader-facing views, not machine authority. Keep normal pages focused on authored content, navigation, indexes, local assets, compact resource/status panels, and deployment-neutral links. Put verbose internals such as source hashes, cache keys, source paths, artifact paths, runtime profile details, and reviewed-output freshness metadata in `manifest.json`, `data/*.json`, copied artifact files, or static `_raya/inspect/` pages.

Course initialization creates replaceable scaffold only. It must refuse non-empty target directories and must not define required pedagogy or official course canon by accident.

Use Raya Lucaria domain names consistently: Glintstone, Primeval Current, Glintstone Key, Rennala, Debate Parlor, Sellen, and Graven School are canonical concepts. Avoid carrying forward old source directory names, old generated JSON shapes, old renderer stacks, old theme systems, or old examples as architecture.

Use Python 3.10 for the current baseline. `packages/schema` owns schemas and validators; `packages/cli` owns the `raya` command; `packages/static` owns the Glintstone static builder. Renderer, TypeScript/web UI, backend, identity, dynamic study state, graph UI, backlinks, wikilinks, heading-anchor validation, and external link policy remain out of scope until later proposals.

When cleaning current guidance, update `README.md`, `AGENTS.md`, affected role docs, and `openspec/config.yaml` together so repository commands and source-layout rules do not drift across guidance surfaces.

## Testing Guidelines

Write tests against current contracts, not legacy behavior. Start with schema, validation, fixture, CLI, and artifact contract tests. Keep examples minimal and labeled; examples must not accidentally define pedagogy or architecture.

Use temporary directories for scenario tests that need throwaway courses. The external smoke test exists to prove `raya validate`, `raya build`, and `raya artifacts inspect` work on a course outside the framework checkout; do not add permanent course repos or generated course outputs for that purpose.

Test local source links and local asset references with throwaway courses, not permanent generated outputs. Broken local references should fail validation before build writes a successful artifact.

Changes to rendered HTML, browser-facing resources, deployment portability, or static site behavior should include e2e/static-read-path tests. Use representative fixture content such as `examples/courses/render-fixture`, label it as fixture material, and keep `docs/foundation/` as the authority surface.

Use `examples/courses/reference-fixture` for code/notebook reference behavior. It is fixture material for copied files, rewritten links, static previews, and `references.json`; it must not become hidden pedagogy or an execution contract.

Use `examples/courses/runtime-fixture` for runtime profile and cache metadata behavior. It is fixture material for metadata, policies, cache keys, and no-execution sentinels; it must not become an execution contract.

Use `examples/courses/execution-fixture` for explicit local execution behavior. It is fixture material for `raya run`, policy refusals, cache reuse, refresh behavior, generated logs/results, and notebook output handling; it must not become pedagogy or run during static build.

Use the same fixture for reviewed-output behavior. It is fixture material for `_reviewed/`, `raya outputs list`, `raya outputs freeze`, frozen validation, reviewed artifact files, static reviewed panels, and stale/missing diagnostics.

Use `examples/gallery/index.html` for quick manual preview of built fixtures. Keep it labeled as fixture material and make links deployment-neutral so it can be served from a local static server rooted at `examples/` or the repository.

Changes that affect contributors/collaborators, professors, students, or agents should include role-documentation impact. If role docs change, update both the English role directory under `docs/guides/en/` and the Spanish role directory under `docs/guides/es/`, or explicitly track the deferred language page in the OpenSpec tasks.

Validation and diagnostics should be actionable for both humans and coding agents: identify files read, outputs written, detected context, concrete next actions, and nonzero failures.

## Commit & Pull Request Guidelines

Use short, imperative commit subjects. Pull requests should describe the change, list validation commands run, link related issues, and include screenshots for visible site, theme, navigation, or content rendering changes.

## Agent-Specific Instructions

Treat `docs/foundation/13_truth_surfaces.md` as the authority map. If a lower surface conflicts with `docs/foundation/`, the lower surface is wrong until a new accepted decision updates the foundation.

For foundation work, update the smallest relevant foundation file and keep `docs/foundation/00_index.md` accurate. For implementation work, prefer creating or updating OpenSpec proposals/specs from foundation decisions before writing package code.

Do not preserve legacy docs in current guide paths merely because they exist; use Git history as the archive. Do not edit generated outputs, dependency folders, caches, or legacy code unless the current task explicitly includes reset cleanup. When salvaging legacy behavior, copy the principle intentionally into a proposal, define the new contract, rewrite the smallest useful idea, and add tests against the new contract.
