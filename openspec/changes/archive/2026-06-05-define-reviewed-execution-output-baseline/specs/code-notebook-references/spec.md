## ADDED Requirements

### Requirement: References expose reviewed output status
Code and notebook reference surfaces SHALL expose reviewed output status when current reviewed output exists for a referenced target.

#### Scenario: Referenced script has reviewed output
- **WHEN** a rendered page references a script target with current reviewed output
- **THEN** generated reference metadata MUST associate that reference with reviewed output status and reviewed output artifact paths

#### Scenario: Referenced notebook has reviewed output
- **WHEN** a rendered page references a notebook target with current reviewed output
- **THEN** generated reference metadata MUST associate that reference with reviewed output status and reviewed output artifact paths without mutating the authored source notebook

#### Scenario: Reference preview remains non-executing
- **WHEN** reference metadata includes reviewed output status
- **THEN** validation, build, preview generation, and artifact inspection MUST NOT execute the referenced target
