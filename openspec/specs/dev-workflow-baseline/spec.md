# dev-workflow-baseline Specification

## Purpose
Defines the Docker Compose and `uv` development workflow, local escape hatch, smoke checks, e2e expectations, and provider-neutral baseline.
## Requirements
### Requirement: Docker Compose reference workflow
The repository SHALL provide Docker Compose as the documented reference development workflow for the first contract and CLI implementation.

#### Scenario: Run CLI through Docker
- **WHEN** a contributor follows the documented Docker workflow from the repository root
- **THEN** the workflow MUST run the `raya` CLI without requiring a host Python virtual environment

#### Scenario: Docker workflow is canonical for setup
- **WHEN** Docker and Docker Compose are available
- **THEN** the documented setup MUST prefer Docker Compose over ad hoc host-machine setup

### Requirement: uv Python environment
The first Python packages SHALL use `uv` for dependency resolution, environment creation, and local non-Docker execution.

#### Scenario: Sync Python dependencies
- **WHEN** a contributor runs the documented `uv` setup command
- **THEN** the command MUST create or update a Python environment that can run the `raya` CLI

#### Scenario: Container uses uv
- **WHEN** the Docker development workflow installs Python dependencies
- **THEN** it MUST use `uv` instead of unmanaged `pip install` commands

### Requirement: Local non-Docker escape hatch
The repository SHALL document a local non-Docker workflow for contributors who need to run the first CLI and tests directly on the host.

#### Scenario: Run CLI locally
- **WHEN** a contributor has Python and `uv` installed locally
- **THEN** the documented local workflow MUST run `raya --help` without Docker

### Requirement: External course smoke test
The repository SHALL provide a focused smoke-test workflow for validating a source course outside the framework checkout without creating a permanent second repository.

#### Scenario: Validate temporary external course
- **WHEN** the smoke-test workflow runs from the repository root
- **THEN** it MUST copy the minimal fixture course into a temporary directory outside the repository, validate that external course locally, validate it through Docker Compose with an explicit temporary mount, and clean up the temporary files

### Requirement: Baseline development commands
The development workflow SHALL define commands for checking the foundation docs, syncing dependencies, running the CLI, and running baseline tests.

#### Scenario: Execute baseline checks
- **WHEN** a contributor runs the documented baseline check command set
- **THEN** it MUST include the foundation file listing check, stale renderer assumption check, CLI help, contract tests, and external-course smoke test once implemented

### Requirement: Canonical repository verification
The development workflow SHALL provide canonical repository verification scripts for host and Docker workflows.

#### Scenario: Host full check runs canonical gate
- **WHEN** a contributor or agent runs `./scripts/check.sh` from the repository root
- **THEN** the command MUST run the repository's full host verification gate, including whitespace checks, hygiene scans, strict OpenSpec validation, and Python/Raya verification through `./scripts/check-python.sh`

#### Scenario: Docker check uses reference container
- **WHEN** a contributor or agent runs `./scripts/check-docker.sh` from the repository root
- **THEN** the command MUST run the accepted Python/Raya verification path through the Docker Compose `dev` service without requiring the caller to copy the underlying command list

#### Scenario: Python verification is centralized
- **WHEN** host, Docker, or CI workflows need Python/Raya validation
- **THEN** they MUST call `./scripts/check-python.sh` or an equivalent repository-owned script rather than maintaining separate duplicated lists of `uv`, `pytest`, `raya validate`, `raya build`, and artifact inspection commands

#### Scenario: Verification output is actionable
- **WHEN** a canonical verification script runs
- **THEN** it MUST print the major command or check being run so failures identify the concrete workflow step that needs attention

### Requirement: Repository hygiene verification
The development workflow SHALL include repository hygiene checks that protect current guidance, source truth, and generated-output boundaries.

#### Scenario: Stale current guidance is scanned
- **WHEN** repository hygiene verification runs
- **THEN** it MUST scan current guidance surfaces for stale renderer assumptions, stale source-layout requirements, command drift, or other current wording that conflicts with accepted foundation or specs

#### Scenario: Generated output pollution is scanned
- **WHEN** repository hygiene verification runs
- **THEN** it MUST fail if generated artifacts, static site output, caches, dependency folders, or local session output appear as tracked source or untracked source that should be ignored

#### Scenario: OpenSpec incomplete markers are scanned
- **WHEN** repository hygiene verification runs
- **THEN** it MUST fail on incomplete markers in current specs or current documentation surfaces that are expected to be accepted guidance

#### Scenario: Fixture labeling is scanned
- **WHEN** repository hygiene verification runs
- **THEN** it MUST verify that repository examples, galleries, rendered documentation fixtures, or similar preview surfaces remain labeled as fixture or documentation material rather than hidden authority

### Requirement: CI verification
The development workflow SHALL provide CI that runs the canonical repository verification scripts.

#### Scenario: CI installs accepted tools
- **WHEN** CI runs for the repository
- **THEN** it MUST install the accepted Python, `uv`, OpenSpec, and Docker Compose tooling needed by the canonical checks or document any platform limitation

#### Scenario: CI calls repository scripts
- **WHEN** CI verifies the repository
- **THEN** it MUST call repository-owned scripts such as `./scripts/check.sh` and `./scripts/check-docker.sh` instead of duplicating their command lists in workflow configuration

#### Scenario: CI documents Docker limits
- **WHEN** CI cannot run the accepted Docker verification path
- **THEN** the workflow or current repository guidance MUST document the limitation and identify the local Docker command contributors should run before archive or merge

### Requirement: Provider and renderer neutrality
The development workflow SHALL NOT require a hosted service, identity provider, JavaScript framework, or static-site renderer for the baseline contract work.

#### Scenario: No backend needed
- **WHEN** the baseline workflow validates the minimal fixture course
- **THEN** it MUST complete without network services, auth providers, databases, or a frontend build pipeline

### Requirement: Static render e2e workflow
The development workflow SHALL include real e2e, visual, or static-read-path tests when a change affects rendered HTML, browser-facing resources, deployment portability, preview behavior, or static site behavior.

#### Scenario: Rendered static site e2e
- **WHEN** a change modifies static rendering or browser-facing generated resources
- **THEN** the verification workflow MUST build a representative fixture and test the generated `artifact/site/` read path rather than only checking source validation or string-level unit behavior

#### Scenario: Visual rendered surface checks
- **WHEN** a change modifies default page layout, examples/gallery layout, inspection layout, support-panel display, or preview workflow
- **THEN** verification MUST include screenshot, browser-driven, or equivalent visual/layout checks across representative desktop and mobile-sized viewports

#### Scenario: Docker e2e compatibility
- **WHEN** rendered static site e2e tests are added
- **THEN** they MUST run through the Docker Compose reference workflow or explicitly document any required Docker setup change

#### Scenario: Fixture content remains labeled
- **WHEN** e2e fixture content is created for renderer coverage
- **THEN** it MUST be labeled as fixture material and MUST NOT be treated as canonical pedagogy, architecture, or foundation truth

### Requirement: Documentation impact in change workflow
The development workflow SHALL require documentation impact to be considered for every substantial change.

#### Scenario: Proposal documents documentation impact
- **WHEN** a proposal is created for a change that affects behavior, contracts, commands, rendering, deployment, pedagogy, authority boundaries, or user-facing workflows
- **THEN** the proposal MUST identify affected documentation audiences or explicitly state that no documentation update is needed

#### Scenario: Tasks include documentation work
- **WHEN** a proposal identifies documentation impact
- **THEN** the task list MUST include the smallest appropriate documentation updates and any required documentation checks

### Requirement: Documentation hygiene checks
The development workflow SHALL include focused documentation hygiene checks when a change creates or updates documentation, specs, or rendered documentation fixtures.

#### Scenario: Specs are updated
- **WHEN** a change creates or updates current OpenSpec specs
- **THEN** verification MUST check that current specs do not retain `Purpose: TBD` placeholders

#### Scenario: Documentation fixtures are added
- **WHEN** a change adds rendered documentation or documentation fixtures
- **THEN** verification MUST check that the fixture is labeled as documentation or fixture material and remains separate from class/course examples

#### Scenario: Role documentation is updated
- **WHEN** a change creates or updates documentation for contributors/collaborators, professors, students, or agents
- **THEN** verification MUST check that separate English and Spanish role directories with index pages are present or that any deferred language version is tracked

### Requirement: Ordered content verification
Changes that affect ordered content, generated indexes, stable references, or static navigation SHALL include focused contract and e2e verification.

#### Scenario: Ordered content contracts changed
- **WHEN** a change modifies ordered source conventions, page metadata, generated index behavior, stable `raya:` links, or navigation artifact data
- **THEN** verification MUST include contract tests for source validation, metadata parsing, stable reference resolution, generated navigation data, and generated index data

#### Scenario: Rendered index behavior changed
- **WHEN** a change modifies generated local indexes, master indexes, breadcrumbs, previous/next links, or stable rendered links
- **THEN** verification MUST include a representative static-read-path e2e fixture that renders those behaviors from source content

### Requirement: Ordered content documentation
Changes that introduce or modify the ordered authoring model SHALL update role documentation for affected audiences.

#### Scenario: Role docs updated
- **WHEN** ordered content, generated indexes, stable IDs, or authoring metadata change
- **THEN** documentation tasks MUST update separate English and Spanish role documentation for contributors/collaborators, professors, students, and agents or explicitly track any deferred role-language page

#### Scenario: Documentation includes source and rendered views
- **WHEN** role documentation explains ordered content behavior
- **THEN** it MUST show both the source-tree authoring model and the rendered student-facing result so readers do not confuse filename mechanics with student navigation labels

### Requirement: Unified source tree verification
Changes that affect the authored source root, support-directory conventions, official learning-object colocation, or colocated assets SHALL include focused contract and e2e verification.

#### Scenario: Unified source contract changed
- **WHEN** a change modifies `source: course`, unsupported source-root fields, `_official/`, `_assets/`, support path classification, or source-root behavior
- **THEN** verification MUST include contract tests for configuration resolution, source validation, support directory privacy, official object discovery, asset validation, and representative artifact generation

#### Scenario: Unified source static behavior changed
- **WHEN** a change modifies how unified source content renders, exports study seed data, copies assets, or creates browser-facing links
- **THEN** verification MUST include a representative static-read-path e2e fixture that exercises rendered pages, generated indexes, official object export, and colocated asset URLs

### Requirement: Unified source documentation
Changes that introduce or modify the unified authored source tree SHALL update the documentation surfaces that authors, learners, contributors, and agents use to understand course structure.

#### Scenario: Unified source role docs updated
- **WHEN** `source: course`, colocated `_official/`, colocated `_assets/`, or support-directory privacy changes
- **THEN** documentation tasks MUST update separate English and Spanish role documentation for contributors/collaborators, professors, students, and agents or explicitly track any deferred role-language page

#### Scenario: Unified source foundation docs updated
- **WHEN** the canonical source-course tree changes
- **THEN** documentation tasks MUST update the foundation course contract, system overview, documentation surface map, and OpenSpec config guidance as needed

### Requirement: Rich rendering verification
Changes that affect rich static rendering SHALL include representative contract and e2e verification.

#### Scenario: Rich rendering contracts changed
- **WHEN** a change modifies Markdown rendering, math rendering, code block rendering, callouts, footnotes, heading anchors, page table of contents, or rich render support resources
- **THEN** verification MUST include contract tests for generated HTML, link/asset rewriting, artifact validation, and static read-path behavior

#### Scenario: Rich rendering e2e fixture
- **WHEN** rich static rendering behavior changes
- **THEN** verification MUST include a representative fixture that renders at least one root page and one nested page through `artifact/site/`

#### Scenario: Rich rendering Docker coverage
- **WHEN** rich static rendering introduces parser, highlighter, math, or renderer dependencies
- **THEN** verification MUST include the Docker Compose reference workflow or explicitly document any Docker workflow gap

### Requirement: Rich rendering documentation
Changes that introduce or modify rich static rendering SHALL update the documentation surfaces authors, learners, contributors, and agents use.

#### Scenario: Rich rendering role docs updated
- **WHEN** rich rendering changes author-facing syntax or student-facing rendered behavior
- **THEN** documentation tasks MUST update separate English and Spanish role documentation for contributors/collaborators, professors, students, and agents or explicitly track any deferred role-language page

#### Scenario: Rich rendering foundation and rendered docs updated
- **WHEN** the accepted rich rendering baseline changes
- **THEN** documentation tasks MUST update the rendering execution plan or other relevant foundation docs and keep the live rendered docs tree aligned

### Requirement: Code and notebook reference verification
Changes that affect code or notebook reference behavior SHALL include representative contract and e2e verification.

#### Scenario: Reference behavior changed
- **WHEN** a change modifies code reference validation, notebook reference validation, reference copying, reference data, reference rendering, or static file paths
- **THEN** verification MUST include contract tests for validation, generated HTML, artifact data, artifact inspection, and static-read-path behavior

#### Scenario: Representative reference fixture
- **WHEN** code or notebook reference behavior changes
- **THEN** verification MUST include a representative fixture with at least one root or nested page referencing a script and a notebook through extension-based links that do not depend on mandatory `code/` or `notebooks/` support roots

#### Scenario: Optional folder compatibility fixture
- **WHEN** code or notebook reference behavior changes
- **THEN** verification MUST prove that existing `code/` or `notebooks/` folder names still work as ordinary author organization choices when linked references satisfy the ownership boundary

#### Scenario: Invalid reference fixtures
- **WHEN** code or notebook reference validation changes
- **THEN** verification MUST include invalid fixtures or equivalent tests for missing targets, malformed notebooks, private support paths, cross-quantum references, and path-escaping references

#### Scenario: Unlinked support fixture
- **WHEN** code or notebook reference copying behavior changes
- **THEN** verification MUST prove that unlinked `.py` and `.ipynb` files are not copied into generated reference artifact storage

### Requirement: Code and notebook reference documentation
Changes that introduce or modify code and notebook references SHALL update relevant foundation, rendered documentation, role guidance, and agent guidance.

#### Scenario: Role docs updated
- **WHEN** code or notebook reference behavior changes author-facing or student-facing workflows
- **THEN** separate English and Spanish role pages for contributors/collaborators, professors, students, and agents MUST be updated or explicitly marked as deferred

#### Scenario: Phase plan updated
- **WHEN** the accepted code and notebook reference baseline changes
- **THEN** `docs/foundation/17_rendering_execution_plan.md` or a more specific foundation document MUST be updated and kept aligned with rendered documentation

#### Scenario: Agent and proposal guidance updated
- **WHEN** code or notebook reference source-layout guidance changes
- **THEN** `AGENTS.md` and `openspec/config.yaml` MUST stop requiring special `code/` and `notebooks/` support roots and MUST describe extension-based linked support compactly

### Requirement: Rendered surface verification
Changes that affect rendered surface discipline SHALL include contract and static-read-path verification for both visible reader content and hidden machine-only internals.

#### Scenario: Default page visibility tested
- **WHEN** rendered-surface behavior changes
- **THEN** verification MUST prove representative default pages show authored content, navigation, generated indexes, compact resource/status labels, and deployment-neutral links

#### Scenario: Metadata leakage tested
- **WHEN** rendered-surface behavior changes
- **THEN** verification MUST prove representative default pages do not dump raw JSON, source hashes, cache keys, artifact storage paths, browser storage paths, or verbose runtime/execution internals into the main reading flow

#### Scenario: Machine data preservation tested
- **WHEN** rendered-surface behavior changes
- **THEN** verification MUST prove manifest-declared artifact data and artifact inspection still expose the complete accepted metadata

#### Scenario: Static inspection tested
- **WHEN** inspection surfaces are generated or changed
- **THEN** verification MUST prove those surfaces work from the static read path without executing targets or requiring a backend

### Requirement: Examples gallery verification
Changes that add or modify repository example preview surfaces SHALL include fixture labeling, build, and static-read-path checks.

#### Scenario: Gallery builds with fixtures
- **WHEN** the examples/gallery surface changes
- **THEN** verification MUST build the representative fixtures and prove the gallery links to their generated static entrypoints

#### Scenario: Gallery labels examples as fixtures
- **WHEN** the examples/gallery surface is rendered
- **THEN** verification MUST prove it labels entries as fixture material and points to foundation docs or accepted specs for authority

#### Scenario: Gallery static links work
- **WHEN** the gallery is served through local static hosting or static-read-path tests
- **THEN** links to fixture pages, support resources, referenced files, and reviewed files MUST resolve without backend routes or absolute deployment-root assumptions

### Requirement: Rendered surface documentation
Changes that introduce or modify rendered-surface discipline SHALL update foundation, rendered documentation, role guidance, and agent/proposal guidance.

#### Scenario: Role docs updated
- **WHEN** rendered-surface behavior changes author-facing, student-facing, contributor-facing, professor-facing, or agent-facing workflows
- **THEN** separate English and Spanish role pages for contributors/collaborators, professors, students, and agents MUST be updated or explicitly marked as deferred

#### Scenario: Foundation docs updated
- **WHEN** rendered-surface discipline changes the relationship between artifact data and rendered pages
- **THEN** `docs/foundation/06_artifact_contract.md`, `docs/foundation/15_system_overview.md`, `docs/foundation/16_documentation_surfaces.md`, or `docs/foundation/17_rendering_execution_plan.md` MUST be updated as appropriate

#### Scenario: Agent and proposal guidance updated
- **WHEN** rendered-surface discipline becomes an accepted baseline
- **THEN** `AGENTS.md` and `openspec/config.yaml` MUST tell future agents and proposals to keep normal pages focused and use manifest-declared data or inspection surfaces for verbose internals

### Requirement: Runtime metadata verification
Changes that affect runtime profile, execution policy, or cache metadata behavior SHALL include contract and fixture verification without running executable course code.

#### Scenario: Runtime metadata behavior changed
- **WHEN** a change modifies runtime profile parsing, policy validation, cache-key generation, runtime artifact data, execution-plan artifact data, or cache metadata artifact data
- **THEN** verification MUST include contract tests for valid fixtures, invalid diagnostics, generated data schemas, artifact inspection, and static build preservation

#### Scenario: Docker plus uv metadata fixture
- **WHEN** runtime profile behavior changes
- **THEN** verification MUST include a representative fixture that declares a `uv` profile and Docker Compose service metadata without requiring test code to execute the profile

#### Scenario: Invalid runtime fixtures
- **WHEN** runtime profile validation changes
- **THEN** verification MUST include invalid fixtures or equivalent tests for unsupported managers, missing project files, missing or stale lockfile signals, path escapes, and unsafe execution defaults

### Requirement: Runtime metadata documentation
Changes that introduce or modify runtime profiles, execution policies, or cache metadata SHALL update foundation, rendered documentation, and role guidance.

#### Scenario: Role docs updated
- **WHEN** runtime profile, execution policy, or cache metadata behavior changes author-facing, student-facing, contributor-facing, or agent-facing workflows
- **THEN** separate English and Spanish role pages for contributors/collaborators, professors, students, and agents MUST be updated or explicitly marked as deferred

#### Scenario: Phase plan updated
- **WHEN** the accepted runtime profile or cache metadata baseline changes
- **THEN** `docs/foundation/17_rendering_execution_plan.md` or a more specific foundation document MUST be updated and kept aligned with rendered documentation

### Requirement: Local execution verification
Changes that affect local execution SHALL include host, Docker, cache, notebook, and no-execution regression verification.

#### Scenario: Script execution behavior changed
- **WHEN** local script execution behavior changes
- **THEN** verification MUST include contract or CLI tests proving explicit target execution, logs, outputs, exit codes, and nonzero failure diagnostics

#### Scenario: Notebook execution behavior changed
- **WHEN** local notebook execution behavior changes
- **THEN** verification MUST include tests proving generated output notebooks are produced without mutating authored source notebooks

#### Scenario: Cache behavior changed
- **WHEN** cache reuse or refresh behavior changes
- **THEN** verification MUST include tests for cache hit reuse, refresh rerun, stale cache diagnostics, and hidden no-execution paths

#### Scenario: Docker execution behavior changed
- **WHEN** Docker execution behavior changes
- **THEN** verification MUST include a representative Docker Compose plus `uv` workflow or document the exact environment gap

#### Scenario: Static no-execution regression
- **WHEN** local execution support changes
- **THEN** verification MUST prove `raya validate`, `raya build`, `raya artifacts inspect`, and static serving do not execute targets

### Requirement: Local execution documentation
Changes that introduce or modify local execution SHALL update foundation, rendered documentation, operational docs, and role guidance.

#### Scenario: Role docs updated
- **WHEN** local execution behavior changes author-facing, student-facing, contributor-facing, or agent-facing workflows
- **THEN** separate English and Spanish role pages for contributors/collaborators, professors, students, and agents MUST be updated or explicitly marked as deferred

#### Scenario: Phase plan updated
- **WHEN** the accepted local execution baseline changes
- **THEN** `docs/foundation/17_rendering_execution_plan.md` or a more specific foundation document MUST be updated and kept aligned with rendered documentation

### Requirement: Reviewed output verification
Changes that affect reviewed or frozen execution output SHALL include source, artifact, static-read-path, command, and no-execution verification.

#### Scenario: Reviewed output behavior changed
- **WHEN** reviewed output source, validation, artifact data, freezing, or rendering behavior changes
- **THEN** verification MUST include contract tests for current reviewed output, stale reviewed output, missing reviewed files, generated-to-reviewed freezing, and artifact inspection

#### Scenario: Frozen policy changed
- **WHEN** frozen policy behavior changes
- **THEN** verification MUST include tests proving frozen targets validate reviewed output without executing and fail when reviewed output is missing or stale

#### Scenario: Static reviewed output changed
- **WHEN** reviewed output rendering changes
- **THEN** verification MUST include e2e/static-read-path tests proving reviewed panels and linked reviewed files work from `artifact/site/`

#### Scenario: No-execution regression
- **WHEN** reviewed/frozen output support changes
- **THEN** verification MUST prove `raya validate`, `raya build`, `raya artifacts inspect`, `raya outputs list`, `raya outputs freeze`, and static serving do not execute targets

### Requirement: Reviewed output documentation
Changes that introduce or modify reviewed/frozen execution output SHALL update foundation, rendered documentation, operational docs, and role guidance.

#### Scenario: Role docs updated
- **WHEN** reviewed output behavior changes author-facing, student-facing, contributor-facing, or agent-facing workflows
- **THEN** separate English and Spanish role pages for contributors/collaborators, professors, students, and agents MUST be updated or explicitly marked as deferred

#### Scenario: Phase plan updated
- **WHEN** the accepted reviewed output baseline changes
- **THEN** `docs/foundation/17_rendering_execution_plan.md` or a more specific foundation document MUST be updated and kept aligned with rendered documentation

### Requirement: Preview workflow verification
Changes that add or modify `raya preview`, examples/gallery preview behavior, or rendered surface polish SHALL include CLI, static serving, and no-execution verification.

#### Scenario: Preview command tested
- **WHEN** preview command behavior changes
- **THEN** verification MUST prove the command resolves an explicit course path, validates/builds or reports its dry-run plan, and prints the student-default entrypoint URL

#### Scenario: Preview static server tested
- **WHEN** preview serving behavior changes
- **THEN** verification MUST prove the served URL resolves generated static pages, local assets, referenced files, reviewed files, and inspection pages without backend routes or deployment-root assumptions

#### Scenario: Preview no-execution tested
- **WHEN** preview command behavior changes
- **THEN** verification MUST prove preview does not execute scripts, notebooks, kernels, Docker execution, package installers, cache refreshes, `raya run`, or `raya outputs freeze`

#### Scenario: Preview documentation updated
- **WHEN** preview workflow changes contributor, professor, student, or agent behavior
- **THEN** foundation docs, rendered docs, role guides in separate English and Spanish directories, `AGENTS.md`, and `openspec/config.yaml` MUST be updated or explicitly marked as deferred
