## ADDED Requirements

### Requirement: Known missing work documentation
Documentation surfaces SHALL include a current known-missing-work inventory for deferred capabilities and intentional gaps.

#### Scenario: Deferred work is documented
- **WHEN** a contributor, professor, student, or agent needs to understand whether a capability is current behavior
- **THEN** current documentation MUST identify major deferred capabilities and intentional gaps without requiring readers to infer them from archived changes or old plans

#### Scenario: Deferred work is not current behavior
- **WHEN** known missing work is listed in current documentation
- **THEN** the listing MUST state that deferred work becomes current only through an accepted OpenSpec change, implementation, tests, and documentation

#### Scenario: Preview proposal remains parked
- **WHEN** current guidance describes the repository hygiene baseline
- **THEN** it MUST keep the parked preview proposal separate from the hygiene implementation scope

### Requirement: Current guidance consistency
Current guidance surfaces SHALL agree on canonical verification commands and accepted source layout.

#### Scenario: Canonical commands are consistent
- **WHEN** `README.md`, `AGENTS.md`, role guides, foundation docs, rendered docs, or `openspec/config.yaml` describe repository verification
- **THEN** they MUST point to the canonical host and Docker check scripts or explicitly explain a narrower focused command

#### Scenario: Source layout guidance is consistent
- **WHEN** current guidance describes course source layout, local assets, official support, reviewed output, runtime metadata, or code and notebook references
- **THEN** it MUST match accepted foundation and OpenSpec contracts, including extension-based `.py` and `.ipynb` reference ownership rather than required `code/` or `notebooks/` roots

#### Scenario: Role guidance is aligned
- **WHEN** contributor or agent guidance changes for repository verification, generated output handling, deferred work, or source layout
- **THEN** the English and Spanish role directories MUST be updated together or the deferred language page MUST be tracked explicitly in OpenSpec tasks
