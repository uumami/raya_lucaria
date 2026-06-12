## ADDED Requirements

### Requirement: Math renderer hardening verification
Changes that add or modify build-time math rendering SHALL include contract,
fixture, static-read-path, browser, Docker, local, and documentation
verification.

#### Scenario: Adapter and build contracts tested
- **WHEN** build-time math rendering changes
- **THEN** verification MUST include focused contract tests for MathJax conversion, Python adapter diagnostics, generated HTML, local support CSS/assets, artifact validation, and static read-path behavior

#### Scenario: Chromium proves visible math
- **WHEN** browser verification runs against a representative generated page with math
- **THEN** it MUST prove the page shows visibly typeset math rather than only raw TeX text

#### Scenario: External renderer requests rejected
- **WHEN** browser verification runs against a representative generated page with math
- **THEN** it MUST fail if the page requests external MathJax, font, CSS, script, CDN, configured host, backend, or renderer-service assets

#### Scenario: Docker reference workflow covers renderer dependencies
- **WHEN** MathJax or Node renderer dependencies are introduced or changed
- **THEN** verification MUST run through the Docker Compose reference workflow or explicitly document a Docker setup change before archive

#### Scenario: Local uv workflow covers renderer dependencies
- **WHEN** the local host verification path runs
- **THEN** it MUST install or check renderer dependencies before running Python/Raya tests that require build-time math rendering

#### Scenario: Renderer documentation updated
- **WHEN** build-time math rendering changes author-facing syntax, student-facing rendered behavior, workflow commands, or proposal guidance
- **THEN** foundation docs, rendered docs or documentation fixtures, separate English and Spanish role guides, `AGENTS.md`, and `openspec/config.yaml` MUST be updated or explicitly marked as deferred
