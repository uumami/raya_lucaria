## ADDED Requirements

### Requirement: Reference execution metadata hooks
Code and notebook references SHALL expose execution policy and runtime profile metadata hooks while preserving static Phase 2 behavior.

#### Scenario: Reference default policy
- **WHEN** a referenced code or notebook file has no explicit execution metadata
- **THEN** generated reference or execution metadata MUST record policy `never` and status `not-executed`

#### Scenario: Reference profile binding
- **WHEN** a referenced code or notebook file declares a runtime profile binding through accepted metadata
- **THEN** validation MUST require the named runtime profile to exist and MUST NOT execute the referenced file

#### Scenario: Reference cache metadata
- **WHEN** a referenced code or notebook file declares policy `cache`
- **THEN** generated cache metadata MUST include a cache key for the reference without executing the target or refreshing cached output

#### Scenario: Reference always policy
- **WHEN** a referenced code or notebook file declares policy `always`
- **THEN** validation MUST require the declaration to be target-specific and generated metadata MUST still record status `not-executed` in Phase 3
