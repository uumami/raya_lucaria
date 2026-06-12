## ADDED Requirements

### Requirement: Surface-aware artifact contract
Course artifacts SHALL distinguish complete machine-readable generated data from the smaller set of data exposed on default rendered pages.

#### Scenario: Complete artifact data preserved
- **WHEN** a builder hides verbose metadata from normal rendered pages
- **THEN** `manifest.json` and manifest-declared `data/*.json` MUST still expose the accepted complete generated data for artifact inspection, agents, future services, graph tools, launchers, and execution tools

#### Scenario: Default HTML is a view
- **WHEN** generated HTML summarizes navigation, references, runtime state, execution state, cache state, reviewed output, official objects, or copied files
- **THEN** that HTML MUST be treated as a reader-facing view derived from artifact data rather than the authority surface

#### Scenario: Inspection data discovers through manifest
- **WHEN** a static inspection surface needs detailed generated metadata
- **THEN** it MUST read or be generated from manifest-declared artifact data rather than relying on hidden assumptions in the rendered page shell

#### Scenario: Static usefulness preserved
- **WHEN** rendered pages apply student-default surface discipline
- **THEN** course pages, navigation, internal links, accessible HTML, local assets, referenced files, and reviewed files MUST remain usable without accounts, network services, backend routes, or client-side routing
