## ADDED Requirements

### Requirement: References as executable targets
Code and notebook references SHALL become executable targets only when selected through the accepted local execution command.

#### Scenario: Referenced script selected
- **WHEN** a user selects a validated `.py` reference with `raya run`
- **THEN** local execution MUST resolve the reference metadata and execute the source script according to its policy and profile

#### Scenario: Referenced notebook selected
- **WHEN** a user selects a validated `.ipynb` reference with `raya run`
- **THEN** local execution MUST resolve the reference metadata and execute a generated copy or output notebook without mutating the authored source notebook

#### Scenario: Static preview not execution
- **WHEN** a page renders a code or notebook preview
- **THEN** the preview MUST NOT be treated as evidence that the target has executed

#### Scenario: Missing reference target refuses execution
- **WHEN** a user selects a code or notebook target that does not match a validated reference or accepted source path
- **THEN** local execution MUST fail with an actionable diagnostic
