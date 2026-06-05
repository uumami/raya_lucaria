## ADDED Requirements

### Requirement: Generated execution result surfaces
Course artifacts SHALL expose local execution results as generated, inspectable artifact surfaces without making them authored course truth.

#### Scenario: Execution result data declared
- **WHEN** local execution writes result metadata
- **THEN** `manifest.json` or an equivalent artifact entrypoint MUST declare the execution result data path

#### Scenario: Generated output directories
- **WHEN** local execution writes outputs, logs, or cache result records
- **THEN** those files MUST live under generated artifact output directories such as `execution/`, `logs/`, or `cache/`

#### Scenario: Source course remains canonical
- **WHEN** generated execution outputs differ from source files
- **THEN** authored source files and accepted specs MUST remain the authority unless a future frozen-output contract explicitly promotes output

#### Scenario: Static read path unaffected
- **WHEN** local execution writes generated outputs
- **THEN** the existing static `site/` read path MUST remain usable without execution services
