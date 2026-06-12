## ADDED Requirements

### Requirement: Reviewed output source support privacy
Course source SHALL allow colocated `_reviewed/` directories as private source support for reviewed execution outputs.

#### Scenario: Reviewed output support does not render
- **WHEN** `_reviewed/` appears under the configured `course/` tree
- **THEN** files under it MUST NOT become rendered pages, navigation entries, generated index entries, official objects, ordinary assets, or code/notebook source references

#### Scenario: Reviewed output support is colocated
- **WHEN** a reviewed output supports a target owned by a learning quantum
- **THEN** validation MUST require the reviewed output to live under that quantum's `_reviewed/` directory or an accepted ancestor ownership boundary

#### Scenario: Reviewed output paths stay inside course source
- **WHEN** reviewed output metadata declares files
- **THEN** validation MUST require those paths to remain under the owning `_reviewed/` support directory and fail for missing or escaping paths
