## MODIFIED Requirements

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

## ADDED Requirements

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
