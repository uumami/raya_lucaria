## MODIFIED Requirements

### Requirement: Execution policy metadata
Raya Lucaria SHALL model executable intent with explicit policies before any execution engine exists and SHALL bind `frozen` policy to reviewed output validation once the reviewed-output contract is accepted.

#### Scenario: Allowed policy values
- **WHEN** source metadata declares an execution policy
- **THEN** validation MUST accept only `never`, `manual`, `cache`, `always`, and `frozen`

#### Scenario: Default policy is never
- **WHEN** executable source support has no explicit policy
- **THEN** generated execution metadata MUST record policy `never` and status `not-executed`

#### Scenario: Unsafe always policy is explicit
- **WHEN** source metadata declares policy `always`
- **THEN** validation MUST require an explicit target-level declaration and MUST NOT infer `always` from a profile default

#### Scenario: Frozen output validates reviewed support
- **WHEN** source metadata declares policy `frozen`
- **THEN** validation MUST require current reviewed output metadata for the target and MUST NOT execute, refresh, or trust generated-only output content

### Requirement: Runtime policies drive local execution
Runtime profile and cache metadata SHALL determine whether local execution runs, reuses, refuses, or validates an explicitly selected target.

#### Scenario: Manual policy executes explicit target
- **WHEN** a target policy is `manual` and the user explicitly selects that target with `raya run`
- **THEN** local execution MUST run the target through the selected profile

#### Scenario: Cache policy uses current cache key
- **WHEN** a target policy is `cache`
- **THEN** local execution MUST compare the current cache key with generated cache result metadata before deciding to reuse or run

#### Scenario: Always policy remains explicit
- **WHEN** a target policy is `always`
- **THEN** local execution MUST run only when the target is explicitly selected

#### Scenario: Never policy blocks local execution
- **WHEN** a target policy is `never`
- **THEN** local execution MUST refuse to run the target

#### Scenario: Frozen policy validates reviewed output
- **WHEN** a target policy is `frozen`
- **THEN** local execution MUST validate current reviewed output for the target and MUST NOT run or trust generated-only output
