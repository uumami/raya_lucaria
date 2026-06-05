## ADDED Requirements

### Requirement: Runtime and execution metadata surfaces
Course artifacts SHALL expose runtime profiles, execution plans, and cache metadata through manifest-declared generated data surfaces without treating rendered HTML as authority.

#### Scenario: Runtime data declared
- **WHEN** a build generates runtime profile metadata
- **THEN** `manifest.json` MUST declare the runtime data path

#### Scenario: Execution plan data declared
- **WHEN** a build generates execution policy metadata for referenced code or notebooks
- **THEN** `manifest.json` MUST declare the execution plan data path

#### Scenario: Cache metadata declared
- **WHEN** a build generates cache-key metadata
- **THEN** `manifest.json` MUST declare the cache metadata path

#### Scenario: Metadata remains generated
- **WHEN** runtime, execution, or cache data is present in an artifact
- **THEN** it MUST be treated as rebuildable generated output derived from source files and accepted contracts

#### Scenario: Metadata does not imply execution
- **WHEN** runtime, execution, or cache data is present in an artifact
- **THEN** the artifact MUST distinguish planned or not-executed targets from executed outputs, trusted frozen outputs, logs, or refreshed cache entries
