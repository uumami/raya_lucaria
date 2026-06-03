## ADDED Requirements

### Requirement: Static render e2e workflow
The development workflow SHALL include real e2e or static-read-path tests when a change affects rendered HTML, browser-facing resources, deployment portability, or static site behavior.

#### Scenario: Rendered static site e2e
- **WHEN** a change modifies static rendering or browser-facing generated resources
- **THEN** the verification workflow MUST build a representative fixture and test the generated `artifact/site/` read path rather than only checking source validation or string-level unit behavior

#### Scenario: Docker e2e compatibility
- **WHEN** rendered static site e2e tests are added
- **THEN** they MUST run through the Docker Compose reference workflow or explicitly document any required Docker setup change

#### Scenario: Fixture content remains labeled
- **WHEN** e2e fixture content is created for renderer coverage
- **THEN** it MUST be labeled as fixture material and MUST NOT be treated as canonical pedagogy, architecture, or foundation truth
